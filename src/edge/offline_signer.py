"""
Offline Signer for UATP 7.2 Edge-Native Capsules

Provides offline signing capabilities for edge devices:
- Local key management
- Deferred signature validation
- Signature queuing for batch verification
"""

import hashlib
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# Try to import cryptography libraries
try:
    from nacl.exceptions import BadSignatureError as BadSignature
    from nacl.signing import SigningKey, VerifyKey

    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False

try:
    import cbor2

    CBOR_AVAILABLE = True
except ImportError:
    CBOR_AVAILABLE = False


class SignatureStatus(str, Enum):
    """Status of offline signature."""

    PENDING = "pending"  # Signed offline, not yet verified
    VERIFIED = "verified"  # Verified by cloud
    REJECTED = "rejected"  # Signature invalid
    EXPIRED = "expired"  # Signature expired before verification


@dataclass
class OfflineSignature:
    """Offline signature record."""

    signature_id: str
    capsule_id: bytes
    signature: bytes
    public_key: bytes
    signed_at: datetime
    status: SignatureStatus = SignatureStatus.PENDING
    verified_at: Optional[datetime] = None
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signature_id": self.signature_id,
            "capsule_id": self.capsule_id.hex(),
            "signature": self.signature.hex(),
            "public_key": self.public_key.hex(),
            "signed_at": self.signed_at.isoformat(),
            "status": self.status.value,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "device_id": self.device_id,
        }


@dataclass
class SigningResult:
    """Result of signing operation."""

    success: bool
    signature: Optional[bytes]
    signature_id: Optional[str]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "signature": self.signature.hex() if self.signature else None,
            "signature_id": self.signature_id,
            "error": self.error,
        }


@dataclass
class VerificationResult:
    """Result of signature verification."""

    valid: bool
    signature_id: Optional[str]
    verified_at: Optional[datetime]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "signature_id": self.signature_id,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "error": self.error,
        }


class OfflineSigner:
    """
    Offline signing service for edge devices.

    Manages local signing keys and deferred verification.
    """

    def __init__(
        self,
        device_id: str,
        signing_key: Optional[bytes] = None,
        signature_ttl_seconds: int = 86400 * 7,  # 7 days default
    ):
        """
        Initialize offline signer.

        Args:
            device_id: Unique device identifier
            signing_key: 32-byte Ed25519 seed (generates new if None)
            signature_ttl_seconds: How long signatures remain valid
        """
        if not NACL_AVAILABLE:
            raise ImportError(
                "PyNaCl required for offline signing. "
                "Install with: pip install pynacl"
            )

        self.device_id = device_id
        self.signature_ttl_seconds = signature_ttl_seconds

        # Initialize or generate signing key
        if signing_key:
            self._signing_key = SigningKey(signing_key)
        else:
            self._signing_key = SigningKey.generate()

        self._verify_key = self._signing_key.verify_key

        # Pending signatures queue
        self._pending_signatures: Dict[str, OfflineSignature] = {}

    @property
    def public_key(self) -> bytes:
        """Get public verification key."""
        return bytes(self._verify_key)

    @property
    def public_key_hex(self) -> str:
        """Get public key as hex string."""
        return self.public_key.hex()

    def sign_capsule_data(
        self,
        capsule_id: bytes,
        timestamp_ms: int,
        model_hash: bytes,
        payload: Dict[str, Any],
    ) -> SigningResult:
        """
        Sign capsule data offline.

        Args:
            capsule_id: 32-byte capsule ID
            timestamp_ms: Timestamp in milliseconds
            model_hash: 32-byte model hash
            payload: CBOR-encodable payload

        Returns:
            SigningResult with signature
        """
        try:
            if not CBOR_AVAILABLE:
                raise ImportError("cbor2 required for payload encoding")

            # Build data to sign (same as compact capsule format)
            signed_data = (
                capsule_id
                + struct.pack(">Q", timestamp_ms)
                + model_hash
                + cbor2.dumps(payload)
            )

            # Sign
            signed = self._signing_key.sign(signed_data)
            signature = signed.signature

            # Generate signature ID
            sig_id = self._generate_signature_id(capsule_id, signature)

            # Record pending signature
            offline_sig = OfflineSignature(
                signature_id=sig_id,
                capsule_id=capsule_id,
                signature=signature,
                public_key=self.public_key,
                signed_at=datetime.now(timezone.utc),
                device_id=self.device_id,
            )
            self._pending_signatures[sig_id] = offline_sig

            return SigningResult(
                success=True,
                signature=signature,
                signature_id=sig_id,
            )

        except Exception as e:
            return SigningResult(
                success=False,
                signature=None,
                signature_id=None,
                error=str(e),
            )

    def sign_raw(self, data: bytes) -> SigningResult:
        """
        Sign arbitrary data.

        Args:
            data: Raw bytes to sign

        Returns:
            SigningResult with signature
        """
        try:
            signed = self._signing_key.sign(data)
            signature = signed.signature

            sig_id = self._generate_signature_id(data[:32], signature)

            return SigningResult(
                success=True,
                signature=signature,
                signature_id=sig_id,
            )

        except Exception as e:
            return SigningResult(
                success=False,
                signature=None,
                signature_id=None,
                error=str(e),
            )

    def verify_signature(
        self,
        data: bytes,
        signature: bytes,
        public_key: Optional[bytes] = None,
    ) -> VerificationResult:
        """
        Verify a signature.

        Args:
            data: Original data that was signed
            signature: 64-byte Ed25519 signature
            public_key: Public key to verify against (uses own if None)

        Returns:
            VerificationResult
        """
        try:
            if public_key:
                verify_key = VerifyKey(public_key)
            else:
                verify_key = self._verify_key

            verify_key.verify(data, signature)

            return VerificationResult(
                valid=True,
                signature_id=None,
                verified_at=datetime.now(timezone.utc),
            )

        except BadSignature:
            return VerificationResult(
                valid=False,
                signature_id=None,
                verified_at=None,
                error="Invalid signature",
            )
        except Exception as e:
            return VerificationResult(
                valid=False,
                signature_id=None,
                verified_at=None,
                error=str(e),
            )

    def get_pending_signatures(self) -> List[OfflineSignature]:
        """Get all pending (unverified) signatures."""
        now = datetime.now(timezone.utc)
        pending = []

        for sig in self._pending_signatures.values():
            if sig.status == SignatureStatus.PENDING:
                # Check expiration
                age_seconds = (now - sig.signed_at).total_seconds()
                if age_seconds > self.signature_ttl_seconds:
                    sig.status = SignatureStatus.EXPIRED
                else:
                    pending.append(sig)

        return pending

    def mark_verified(self, signature_id: str) -> bool:
        """
        Mark a signature as verified by cloud.

        Args:
            signature_id: Signature ID to mark

        Returns:
            True if found and marked
        """
        if signature_id in self._pending_signatures:
            sig = self._pending_signatures[signature_id]
            sig.status = SignatureStatus.VERIFIED
            sig.verified_at = datetime.now(timezone.utc)
            return True
        return False

    def mark_rejected(self, signature_id: str, reason: str = "") -> bool:
        """
        Mark a signature as rejected.

        Args:
            signature_id: Signature ID to mark
            reason: Rejection reason

        Returns:
            True if found and marked
        """
        if signature_id in self._pending_signatures:
            sig = self._pending_signatures[signature_id]
            sig.status = SignatureStatus.REJECTED
            return True
        return False

    def export_public_key_info(self) -> Dict[str, Any]:
        """Export public key information for cloud registration."""
        return {
            "device_id": self.device_id,
            "public_key": self.public_key_hex,
            "key_type": "ed25519",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_signature_id(self, capsule_id: bytes, signature: bytes) -> str:
        """Generate unique signature ID.

        Uses 128 bits (32 hex chars) to prevent collision attacks.
        Previous 96-bit IDs were collision-prone.
        """
        combined = capsule_id + signature + str(time.time()).encode()
        # SECURITY: Use 32 hex chars (128 bits) instead of 24 (96 bits)
        return f"sig_{hashlib.sha256(combined).hexdigest()[:32]}"


class OfflineSignerRegistry:
    """
    Registry of offline signers for multiple devices.

    Used by cloud to manage device keys.
    """

    def __init__(self):
        """Initialize registry."""
        self._devices: Dict[str, Dict[str, Any]] = {}

    def register_device(
        self,
        device_id: str,
        public_key: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a device's public key.

        Args:
            device_id: Device identifier
            public_key: Device's Ed25519 public key
            metadata: Optional device metadata

        Returns:
            True if registered
        """
        self._devices[device_id] = {
            "public_key": public_key,
            "registered_at": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }
        return True

    def get_public_key(self, device_id: str) -> Optional[bytes]:
        """Get public key for a device."""
        device = self._devices.get(device_id)
        return device["public_key"] if device else None

    def verify_device_signature(
        self,
        device_id: str,
        data: bytes,
        signature: bytes,
    ) -> VerificationResult:
        """
        Verify signature from a registered device.

        Args:
            device_id: Device identifier
            data: Signed data
            signature: Signature to verify

        Returns:
            VerificationResult
        """
        public_key = self.get_public_key(device_id)
        if not public_key:
            return VerificationResult(
                valid=False,
                signature_id=None,
                verified_at=None,
                error=f"Device {device_id} not registered",
            )

        try:
            verify_key = VerifyKey(public_key)
            verify_key.verify(data, signature)

            return VerificationResult(
                valid=True,
                signature_id=None,
                verified_at=datetime.now(timezone.utc),
            )

        except BadSignature:
            return VerificationResult(
                valid=False,
                signature_id=None,
                verified_at=None,
                error="Invalid signature",
            )
        except Exception as e:
            return VerificationResult(
                valid=False,
                signature_id=None,
                verified_at=None,
                error=str(e),
            )

    def list_devices(self) -> List[Dict[str, Any]]:
        """List all registered devices."""
        return [
            {
                "device_id": device_id,
                "public_key": info["public_key"].hex(),
                "registered_at": info["registered_at"].isoformat(),
                "metadata": info["metadata"],
            }
            for device_id, info in self._devices.items()
        ]


# Singleton registry
offline_signer_registry = OfflineSignerRegistry()
