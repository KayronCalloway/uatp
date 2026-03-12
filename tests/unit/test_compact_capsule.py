"""
Unit tests for Compact Capsule.
"""

import hashlib
import struct
from datetime import timezone

import pytest

from src.edge.compact_capsule import (
    CAPSULE_ID_SIZE,
    COMPACT_CAPSULE_MAGIC,
    COMPACT_CAPSULE_VERSION,
    FIXED_OVERHEAD,
    HEADER_SIZE,
    MODEL_HASH_SIZE,
    SIGNATURE_SIZE,
    TIMESTAMP_SIZE,
    CompactCapsule,
    CompactCapsuleDecoder,
    CompactCapsuleEncoder,
    CompactCapsuleFlags,
    build_signed_data,
    estimate_capsule_size,
)


class TestConstants:
    """Tests for module constants."""

    def test_magic_bytes(self):
        """Test magic bytes value."""
        assert COMPACT_CAPSULE_MAGIC == b"UATP"
        assert len(COMPACT_CAPSULE_MAGIC) == 4

    def test_version(self):
        """Test version value."""
        assert COMPACT_CAPSULE_VERSION == 0x0072

    def test_size_constants(self):
        """Test size constants."""
        assert HEADER_SIZE == 16
        assert CAPSULE_ID_SIZE == 32
        assert TIMESTAMP_SIZE == 8
        assert MODEL_HASH_SIZE == 32
        assert SIGNATURE_SIZE == 64

    def test_fixed_overhead(self):
        """Test fixed overhead calculation."""
        expected = (
            HEADER_SIZE
            + CAPSULE_ID_SIZE
            + TIMESTAMP_SIZE
            + MODEL_HASH_SIZE
            + SIGNATURE_SIZE
        )
        assert FIXED_OVERHEAD == expected
        assert FIXED_OVERHEAD == 152


class TestCompactCapsuleFlags:
    """Tests for CompactCapsuleFlags enum."""

    def test_none_flag(self):
        """Test NONE flag value."""
        assert CompactCapsuleFlags.NONE == 0x0000

    def test_compressed_flag(self):
        """Test COMPRESSED flag value."""
        assert CompactCapsuleFlags.COMPRESSED == 0x0001

    def test_encrypted_flag(self):
        """Test ENCRYPTED flag value."""
        assert CompactCapsuleFlags.ENCRYPTED == 0x0002

    def test_flag_combination(self):
        """Test combining flags."""
        combined = CompactCapsuleFlags.COMPRESSED | CompactCapsuleFlags.ENCRYPTED
        assert combined == 0x0003

    def test_flag_check(self):
        """Test checking flags."""
        flags = CompactCapsuleFlags.COMPRESSED | CompactCapsuleFlags.WORKFLOW_STEP
        assert CompactCapsuleFlags.COMPRESSED in flags
        assert CompactCapsuleFlags.WORKFLOW_STEP in flags
        assert CompactCapsuleFlags.ENCRYPTED not in flags


class TestCompactCapsule:
    """Tests for CompactCapsule dataclass."""

    @pytest.fixture
    def sample_capsule(self):
        """Create a sample compact capsule."""
        return CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,  # 2026-03-12 12:00:00 UTC
            model_hash=hashlib.sha256(b"test_model").digest(),
            payload={"type": "test", "data": "hello"},
            signature=b"\x00" * 64,
        )

    def test_create_capsule(self, sample_capsule):
        """Test creating a compact capsule."""
        assert len(sample_capsule.capsule_id) == 32
        assert len(sample_capsule.model_hash) == 32
        assert len(sample_capsule.signature) == 64
        assert sample_capsule.flags == CompactCapsuleFlags.NONE

    def test_capsule_id_hex(self, sample_capsule):
        """Test capsule_id_hex property."""
        hex_id = sample_capsule.capsule_id_hex

        assert len(hex_id) == 64
        assert hex_id == "0" * 64

    def test_timestamp_property(self, sample_capsule):
        """Test timestamp property."""
        ts = sample_capsule.timestamp

        assert ts.tzinfo == timezone.utc
        assert ts.year == 2024  # Based on the timestamp value

    def test_model_hash_hex(self, sample_capsule):
        """Test model_hash_hex property."""
        hex_hash = sample_capsule.model_hash_hex

        assert len(hex_hash) == 64

    def test_capsule_with_flags(self):
        """Test capsule with custom flags."""
        capsule = CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x00" * 32,
            payload={"t": "test"},
            signature=b"\x00" * 64,
            flags=CompactCapsuleFlags.COMPRESSED | CompactCapsuleFlags.ENCRYPTED,
        )

        assert CompactCapsuleFlags.COMPRESSED in capsule.flags
        assert CompactCapsuleFlags.ENCRYPTED in capsule.flags


class TestCompactCapsuleEncoder:
    """Tests for CompactCapsuleEncoder class."""

    @pytest.fixture
    def encoder(self):
        """Create an encoder instance."""
        return CompactCapsuleEncoder()

    @pytest.fixture
    def sample_capsule(self):
        """Create a sample compact capsule."""
        return CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x00" * 32,
            payload={"type": "test"},
            signature=b"\x00" * 64,
        )

    def test_encode_capsule(self, encoder, sample_capsule):
        """Test encoding a capsule."""
        encoded = encoder.encode(sample_capsule)

        assert isinstance(encoded, bytes)
        assert len(encoded) >= FIXED_OVERHEAD

    def test_encoded_starts_with_magic(self, encoder, sample_capsule):
        """Test encoded capsule starts with magic bytes."""
        encoded = encoder.encode(sample_capsule)

        assert encoded[:4] == COMPACT_CAPSULE_MAGIC

    def test_encoded_contains_version(self, encoder, sample_capsule):
        """Test encoded capsule contains version."""
        encoded = encoder.encode(sample_capsule)

        version = struct.unpack(">H", encoded[4:6])[0]
        assert version == COMPACT_CAPSULE_VERSION

    def test_build_header(self, encoder):
        """Test building header."""
        header = encoder._build_header(CompactCapsuleFlags.NONE, 100)

        assert len(header) == HEADER_SIZE
        assert header[:4] == COMPACT_CAPSULE_MAGIC

        # Check payload length
        payload_len = struct.unpack(">I", header[8:12])[0]
        assert payload_len == 100

    def test_build_header_with_flags(self, encoder):
        """Test building header with flags."""
        flags = CompactCapsuleFlags.COMPRESSED | CompactCapsuleFlags.ENCRYPTED
        header = encoder._build_header(flags, 50)

        flag_bytes = struct.unpack(">H", header[6:8])[0]
        assert flag_bytes == 0x0003

    def test_encode_minimal(self, encoder):
        """Test encoding minimal capsule."""
        signature = b"\x00" * 64
        encoded = encoder.encode_minimal(
            capsule_type="inference",
            model_id="gpt-4",
            content_hash="a" * 64,
            signature=signature,
        )

        assert isinstance(encoded, bytes)
        assert len(encoded) >= FIXED_OVERHEAD
        assert encoded[:4] == COMPACT_CAPSULE_MAGIC

    def test_encode_minimal_with_metadata(self, encoder):
        """Test encoding minimal capsule with metadata."""
        signature = b"\x00" * 64
        encoded = encoder.encode_minimal(
            capsule_type="inference",
            model_id="gpt-4",
            content_hash="a" * 64,
            signature=signature,
            metadata={"key": "value"},
        )

        assert len(encoded) >= FIXED_OVERHEAD

    def test_encode_minimal_invalid_signature_length(self, encoder):
        """Test encoding with invalid signature length."""
        with pytest.raises(ValueError, match="Invalid signature length"):
            encoder.encode_minimal(
                capsule_type="test",
                model_id="model",
                content_hash="a" * 64,
                signature=b"\x00" * 32,  # Wrong length
            )


class TestCompactCapsuleDecoder:
    """Tests for CompactCapsuleDecoder class."""

    @pytest.fixture
    def encoder(self):
        """Create an encoder instance."""
        return CompactCapsuleEncoder()

    @pytest.fixture
    def decoder(self):
        """Create a decoder instance."""
        return CompactCapsuleDecoder()

    @pytest.fixture
    def sample_capsule(self):
        """Create a sample compact capsule."""
        return CompactCapsule(
            capsule_id=b"\x12" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x34" * 32,
            payload={"type": "test", "value": 42},
            signature=b"\x56" * 64,
        )

    def test_decode_roundtrip(self, encoder, decoder, sample_capsule):
        """Test encode/decode roundtrip."""
        encoded = encoder.encode(sample_capsule)
        decoded = decoder.decode(encoded)

        assert decoded.capsule_id == sample_capsule.capsule_id
        assert decoded.timestamp_ms == sample_capsule.timestamp_ms
        assert decoded.model_hash == sample_capsule.model_hash
        assert decoded.payload == sample_capsule.payload
        assert decoded.signature == sample_capsule.signature

    def test_decode_too_short(self, decoder):
        """Test decoding data that's too short."""
        with pytest.raises(ValueError, match="too short"):
            decoder.decode(b"\x00" * 50)

    def test_decode_invalid_magic(self, decoder):
        """Test decoding data with invalid magic."""
        # Create invalid data with wrong magic
        data = b"XXXX" + b"\x00" * (FIXED_OVERHEAD + 10)

        with pytest.raises(ValueError, match="Invalid magic"):
            decoder.decode(data)

    def test_decode_invalid_version(self, decoder):
        """Test decoding data with invalid version."""
        # Create data with wrong version
        header = bytearray(HEADER_SIZE)
        header[0:4] = COMPACT_CAPSULE_MAGIC
        struct.pack_into(">H", header, 4, 0x9999)  # Wrong version
        struct.pack_into(">I", header, 8, 0)  # Zero payload length

        data = bytes(header) + b"\x00" * (FIXED_OVERHEAD - HEADER_SIZE)

        with pytest.raises(ValueError, match="Unsupported version"):
            decoder.decode(data)

    def test_decode_truncated_data(self, decoder, encoder, sample_capsule):
        """Test decoding truncated data."""
        encoded = encoder.encode(sample_capsule)

        # Truncate the data significantly
        truncated = encoded[: len(encoded) - 50]

        with pytest.raises(ValueError, match="(too short|truncated)"):
            decoder.decode(truncated)

    def test_parse_header(self, decoder):
        """Test parsing header."""
        header = bytearray(HEADER_SIZE)
        header[0:4] = COMPACT_CAPSULE_MAGIC
        struct.pack_into(">H", header, 4, COMPACT_CAPSULE_VERSION)
        struct.pack_into(">H", header, 6, 0x0003)  # Flags
        struct.pack_into(">I", header, 8, 1234)  # Payload length

        magic, version, flags, payload_len = decoder._parse_header(bytes(header))

        assert magic == COMPACT_CAPSULE_MAGIC
        assert version == COMPACT_CAPSULE_VERSION
        assert flags == 0x0003
        assert payload_len == 1234

    def test_decode_with_flags(self, encoder, decoder):
        """Test decoding capsule with flags."""
        capsule = CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x00" * 32,
            payload={"t": "test"},
            signature=b"\x00" * 64,
            flags=CompactCapsuleFlags.COMPRESSED,
        )

        encoded = encoder.encode(capsule)
        decoded = decoder.decode(encoded)

        assert decoded.flags == CompactCapsuleFlags.COMPRESSED


class TestBuildSignedData:
    """Tests for build_signed_data function."""

    def test_build_signed_data(self):
        """Test building signed data."""
        capsule = CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x00" * 32,
            payload={"t": "test"},
            signature=b"\x00" * 64,
        )

        signed_data = build_signed_data(capsule)

        assert isinstance(signed_data, bytes)
        # Should include header + all fields except signature
        assert len(signed_data) > HEADER_SIZE + CAPSULE_ID_SIZE

    def test_build_signed_data_includes_header(self):
        """Test signed data includes header."""
        capsule = CompactCapsule(
            capsule_id=b"\x00" * 32,
            timestamp_ms=1710259200000,
            model_hash=b"\x00" * 32,
            payload={"t": "test"},
            signature=b"\x00" * 64,
        )

        signed_data = build_signed_data(capsule)

        # Should start with magic
        assert signed_data[:4] == COMPACT_CAPSULE_MAGIC


class TestEstimateCapsuleSize:
    """Tests for estimate_capsule_size function."""

    def test_estimate_simple_payload(self):
        """Test estimating size for simple payload."""
        payload = {"t": "test"}

        size = estimate_capsule_size(payload)

        assert size >= FIXED_OVERHEAD
        assert size < FIXED_OVERHEAD + 100  # Should be small

    def test_estimate_larger_payload(self):
        """Test estimating size for larger payload."""
        payload = {
            "type": "inference",
            "model": "gpt-4-turbo",
            "data": "x" * 500,
        }

        size = estimate_capsule_size(payload)

        assert size > FIXED_OVERHEAD + 500

    def test_estimate_nested_payload(self):
        """Test estimating size for nested payload."""
        payload = {
            "outer": {
                "inner": {
                    "value": 42,
                    "list": [1, 2, 3, 4, 5],
                }
            }
        }

        size = estimate_capsule_size(payload)

        assert size >= FIXED_OVERHEAD
