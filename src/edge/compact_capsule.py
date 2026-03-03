"""
Compact Capsule Format for UATP 7.2 Edge-Native Capsules

Provides a binary-efficient capsule format for edge devices with
limited bandwidth and storage. Target size: <1KB per capsule.

Binary Format:
  Header (16 bytes):
    MAGIC: "UATP" (4 bytes)
    VERSION: 0x72 (2 bytes)
    FLAGS: (2 bytes)
    PAYLOAD_LEN: (4 bytes, big-endian)
    RESERVED: (4 bytes)
  CAPSULE_ID (32 bytes): SHA-256
  TIMESTAMP (8 bytes): Unix milliseconds
  MODEL_HASH (32 bytes): SHA-256
  PAYLOAD (variable): CBOR-encoded
  SIGNATURE (64 bytes): Ed25519
"""

import hashlib
import secrets
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntFlag
from typing import Any, Dict, Optional, Tuple

# Try to import cbor2 for efficient encoding
try:
    import cbor2

    CBOR_AVAILABLE = True
except ImportError:
    CBOR_AVAILABLE = False

# Compact capsule constants
COMPACT_CAPSULE_MAGIC = b"UATP"
COMPACT_CAPSULE_VERSION = 0x0072  # UATP 7.2

# Fixed sizes
HEADER_SIZE = 16
CAPSULE_ID_SIZE = 32
TIMESTAMP_SIZE = 8
MODEL_HASH_SIZE = 32
SIGNATURE_SIZE = 64

# Total fixed overhead
FIXED_OVERHEAD = (
    HEADER_SIZE + CAPSULE_ID_SIZE + TIMESTAMP_SIZE + MODEL_HASH_SIZE + SIGNATURE_SIZE
)


def _generate_timestamp_ms() -> int:
    """
    Generate a timestamp with microsecond precision and random jitter.

    SECURITY: Adding random microsecond jitter prevents timing analysis attacks
    where an attacker could correlate capsules based on exact timestamp patterns.
    The jitter is small enough (0-999 microseconds) to not affect ordering
    semantics while preventing exact timing correlation.

    Returns:
        Unix timestamp in milliseconds with sub-millisecond jitter
    """
    # Get current time with microsecond precision
    now = time.time()
    base_ms = int(now * 1000)

    # Add cryptographically random jitter (0-999 microseconds = 0.0-0.999 ms)
    # The jitter affects rounding of the sub-millisecond portion
    jitter_us = secrets.randbelow(1000)  # 0-999 microseconds

    # Apply jitter to influence millisecond rounding
    # This randomizes whether we round up or down at the ms boundary
    return base_ms + (1 if jitter_us > 500 else 0)


def _generate_timestamp_ms_precise() -> int:
    """
    Generate a timestamp with true microsecond precision and random sub-microsecond jitter.

    SECURITY: The jitter introduces randomness to prevent timing correlation attacks.
    Even though the output is in milliseconds, the jitter affects rounding decisions,
    making it harder to predict exact capsule creation times.

    Returns:
        Unix timestamp in milliseconds (with microsecond-level jitter applied)
    """
    # Use time.time_ns() if available (Python 3.7+) for better precision
    try:
        now_ns = time.time_ns()
        base_ms = now_ns // 1_000_000  # Convert to milliseconds

        # Add random jitter that affects whether we include the next millisecond
        # This randomizes the exact timing boundary used
        jitter_ns = secrets.randbelow(1_000_000)  # 0-999999 nanoseconds (0-999.999 us)

        # Apply jitter: if jitter pushes us past half a millisecond, round up
        sub_ms_ns = now_ns % 1_000_000  # Current sub-millisecond portion
        if sub_ms_ns + jitter_ns >= 1_000_000:
            return base_ms + 1
        return base_ms
    except AttributeError:
        # Fallback for older Python versions
        return int(time.time() * 1000)


class CompactCapsuleFlags(IntFlag):
    """Flags for compact capsule header."""

    NONE = 0x0000
    COMPRESSED = 0x0001  # Payload is compressed
    ENCRYPTED = 0x0002  # Payload is encrypted
    HAS_ATTESTATION = 0x0004  # Contains hardware attestation
    OFFLINE_SIGNED = 0x0008  # Signed offline (pending sync)
    WORKFLOW_STEP = 0x0010  # Part of a workflow


@dataclass
class CompactCapsule:
    """
    Compact binary capsule for edge devices.

    All fields are designed for minimal size while maintaining
    cryptographic integrity.
    """

    capsule_id: bytes  # 32-byte SHA-256 hash
    timestamp_ms: int  # Unix timestamp in milliseconds
    model_hash: bytes  # 32-byte SHA-256 of model weights
    payload: Dict[str, Any]  # CBOR-encodable payload
    signature: bytes  # 64-byte Ed25519 signature
    flags: CompactCapsuleFlags = CompactCapsuleFlags.NONE

    @property
    def capsule_id_hex(self) -> str:
        """Get capsule ID as hex string."""
        return self.capsule_id.hex()

    @property
    def timestamp(self) -> datetime:
        """Get timestamp as datetime."""
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=timezone.utc)

    @property
    def model_hash_hex(self) -> str:
        """Get model hash as hex string."""
        return self.model_hash.hex()


class CompactCapsuleEncoder:
    """
    Encodes capsules into compact binary format.

    Target: <1KB for typical inference capsules.
    """

    def __init__(self):
        """Initialize the encoder."""
        if not CBOR_AVAILABLE:
            raise ImportError(
                "cbor2 package required for compact capsule encoding. "
                "Install with: pip install cbor2"
            )

    def encode(self, capsule: CompactCapsule) -> bytes:
        """
        Encode a compact capsule to binary format.

        Args:
            capsule: CompactCapsule to encode

        Returns:
            Binary-encoded capsule
        """
        # Encode payload with CBOR
        payload_bytes = cbor2.dumps(capsule.payload)
        payload_len = len(payload_bytes)

        # Build header
        header = self._build_header(capsule.flags, payload_len)

        # Assemble binary capsule
        binary = bytearray()
        binary.extend(header)
        binary.extend(capsule.capsule_id)
        binary.extend(struct.pack(">Q", capsule.timestamp_ms))
        binary.extend(capsule.model_hash)
        binary.extend(payload_bytes)
        binary.extend(capsule.signature)

        return bytes(binary)

    def _build_header(self, flags: CompactCapsuleFlags, payload_len: int) -> bytes:
        """Build the 16-byte header."""
        header = bytearray(HEADER_SIZE)
        header[0:4] = COMPACT_CAPSULE_MAGIC
        struct.pack_into(">H", header, 4, COMPACT_CAPSULE_VERSION)
        struct.pack_into(">H", header, 6, int(flags))
        struct.pack_into(">I", header, 8, payload_len)
        # Reserved bytes 12-15 remain zero
        return bytes(header)

    def encode_minimal(
        self,
        capsule_type: str,
        model_id: str,
        content_hash: str,
        signature: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Encode a minimal capsule with just essential fields.

        Args:
            capsule_type: Type of capsule
            model_id: Model identifier
            content_hash: Hash of content being attested
            signature: Ed25519 signature
            metadata: Optional additional metadata

        Returns:
            Binary-encoded minimal capsule
        """
        # Generate capsule ID from content hash
        if isinstance(content_hash, str):
            capsule_id = bytes.fromhex(content_hash[:64].ljust(64, "0"))
        else:
            capsule_id = hashlib.sha256(content_hash).digest()

        # Generate model hash
        model_hash = hashlib.sha256(model_id.encode()).digest()

        # Build minimal payload
        payload = {
            "t": capsule_type,  # Short key for type
            "m": model_id[:32],  # Truncated model ID
        }
        if metadata:
            payload["d"] = metadata  # Short key for data

        # SECURITY: Reject signatures that are not exactly 64 bytes (Ed25519 signature size)
        # Never pad or truncate signatures as this creates invalid but "accepted" signatures
        if len(signature) != SIGNATURE_SIZE:
            raise ValueError(
                f"Invalid signature length: expected {SIGNATURE_SIZE} bytes, got {len(signature)}. "
                "Ed25519 signatures must be exactly 64 bytes."
            )

        # SECURITY: Use timestamp generation with jitter to prevent timing analysis
        # This makes it harder for attackers to correlate capsules based on timestamps
        timestamp_ms = _generate_timestamp_ms_precise()

        capsule = CompactCapsule(
            capsule_id=capsule_id,
            timestamp_ms=timestamp_ms,
            model_hash=model_hash,
            payload=payload,
            signature=signature,
        )

        return self.encode(capsule)


class CompactCapsuleDecoder:
    """
    Decodes compact binary capsules.
    """

    def __init__(self):
        """Initialize the decoder."""
        if not CBOR_AVAILABLE:
            raise ImportError(
                "cbor2 package required for compact capsule decoding. "
                "Install with: pip install cbor2"
            )

    def decode(self, data: bytes) -> CompactCapsule:
        """
        Decode a binary capsule.

        Args:
            data: Binary capsule data

        Returns:
            Decoded CompactCapsule

        Raises:
            ValueError: If data is invalid
        """
        if len(data) < FIXED_OVERHEAD:
            raise ValueError(
                f"Data too short: {len(data)} bytes, minimum {FIXED_OVERHEAD}"
            )

        # Parse header
        magic, version, flags, payload_len = self._parse_header(data[:HEADER_SIZE])

        if magic != COMPACT_CAPSULE_MAGIC:
            raise ValueError(f"Invalid magic: {magic}")

        if version != COMPACT_CAPSULE_VERSION:
            raise ValueError(f"Unsupported version: {hex(version)}")

        # Calculate expected total size
        expected_size = FIXED_OVERHEAD + payload_len
        if len(data) < expected_size:
            raise ValueError(
                f"Data truncated: {len(data)} bytes, expected {expected_size}"
            )

        # Parse fixed fields
        offset = HEADER_SIZE
        capsule_id = data[offset : offset + CAPSULE_ID_SIZE]
        offset += CAPSULE_ID_SIZE

        timestamp_ms = struct.unpack(">Q", data[offset : offset + TIMESTAMP_SIZE])[0]
        offset += TIMESTAMP_SIZE

        model_hash = data[offset : offset + MODEL_HASH_SIZE]
        offset += MODEL_HASH_SIZE

        # Parse variable payload
        payload_bytes = data[offset : offset + payload_len]
        offset += payload_len

        # Parse signature
        signature = data[offset : offset + SIGNATURE_SIZE]

        # Decode CBOR payload
        payload = cbor2.loads(payload_bytes)

        return CompactCapsule(
            capsule_id=capsule_id,
            timestamp_ms=timestamp_ms,
            model_hash=model_hash,
            payload=payload,
            signature=signature,
            flags=CompactCapsuleFlags(flags),
        )

    def _parse_header(self, header: bytes) -> Tuple[bytes, int, int, int]:
        """Parse the 16-byte header."""
        magic = header[0:4]
        version = struct.unpack(">H", header[4:6])[0]
        flags = struct.unpack(">H", header[6:8])[0]
        payload_len = struct.unpack(">I", header[8:12])[0]
        return magic, version, flags, payload_len

    def verify_signature(
        self,
        capsule: CompactCapsule,
        verify_key: bytes,
    ) -> bool:
        """
        Verify the signature on a compact capsule.

        Args:
            capsule: Decoded compact capsule
            verify_key: Ed25519 public key (32 bytes)

        Returns:
            True if signature is valid
        """
        try:
            from nacl.exceptions import BadSignatureError as BadSignature
            from nacl.signing import VerifyKey

            # Build signed data (everything except signature)
            # SECURITY: Include header (version, flags) in signed data to prevent tampering
            header = struct.pack(
                ">4sHHI4x",  # magic(4) + version(2) + flags(2) + payload_len(4) + reserved(4)
                COMPACT_CAPSULE_MAGIC,
                COMPACT_CAPSULE_VERSION,
                int(capsule.flags),
                len(cbor2.dumps(capsule.payload)),
            )
            signed_data = (
                header
                + capsule.capsule_id
                + struct.pack(">Q", capsule.timestamp_ms)
                + capsule.model_hash
                + cbor2.dumps(capsule.payload)
            )

            key = VerifyKey(verify_key)
            key.verify(signed_data, capsule.signature)
            return True

        except ImportError:
            raise ImportError(
                "PyNaCl required for signature verification. "
                "Install with: pip install pynacl"
            )
        except BadSignature:
            return False
        except Exception:
            return False


def build_signed_data(capsule: CompactCapsule) -> bytes:
    """
    Build the data that should be signed for a compact capsule.

    This includes the header (magic, version, flags, payload_len) to prevent
    tampering with capsule metadata.

    Args:
        capsule: The compact capsule to build signed data for

    Returns:
        Bytes that should be signed with Ed25519
    """
    if not CBOR_AVAILABLE:
        raise ImportError("cbor2 required for building signed data")

    payload_bytes = cbor2.dumps(capsule.payload)

    # Header must be included in signed data to prevent tampering
    header = struct.pack(
        ">4sHHI4x",  # magic(4) + version(2) + flags(2) + payload_len(4) + reserved(4)
        COMPACT_CAPSULE_MAGIC,
        COMPACT_CAPSULE_VERSION,
        int(capsule.flags),
        len(payload_bytes),
    )

    return (
        header
        + capsule.capsule_id
        + struct.pack(">Q", capsule.timestamp_ms)
        + capsule.model_hash
        + payload_bytes
    )


def estimate_capsule_size(payload: Dict[str, Any]) -> int:
    """
    Estimate the encoded size of a capsule.

    Args:
        payload: Payload to encode

    Returns:
        Estimated size in bytes
    """
    if not CBOR_AVAILABLE:
        # Rough estimate without CBOR
        import json

        json_size = len(json.dumps(payload).encode())
        return FIXED_OVERHEAD + int(json_size * 0.7)  # CBOR is ~30% smaller

    payload_size = len(cbor2.dumps(payload))
    return FIXED_OVERHEAD + payload_size
