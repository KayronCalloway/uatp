"""
Unit tests for UATP 7.2 Edge-Native Capsules

Tests:
- Compact capsule encoding/decoding
- Edge-cloud sync protocol
- Offline signing
- CBOR serialization
"""

import struct
import time
from datetime import datetime, timezone

import pytest

# Skip if cbor2 or pynacl not available
pytest.importorskip("cbor2")
nacl = pytest.importorskip("nacl")

from src.edge.compact_capsule import (
    COMPACT_CAPSULE_MAGIC,
    COMPACT_CAPSULE_VERSION,
    FIXED_OVERHEAD,
    CompactCapsule,
    CompactCapsuleDecoder,
    CompactCapsuleEncoder,
    CompactCapsuleFlags,
    estimate_capsule_size,
)
from src.edge.offline_signer import (
    OfflineSigner,
    OfflineSignerRegistry,
    SignatureStatus,
)
from src.edge.sync_protocol import (
    ConflictResolution,
    EdgeSyncService,
    SyncBatch,
    SyncCheckpoint,
    SyncDirection,
    SyncStatus,
)


class TestCompactCapsule:
    """Test CompactCapsule dataclass."""

    def test_create_compact_capsule(self):
        """Test creating a compact capsule."""
        capsule = CompactCapsule(
            capsule_id=bytes.fromhex("a" * 64),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes.fromhex("b" * 64),
            payload={"type": "inference", "model": "gpt-4"},
            signature=bytes(64),
            flags=CompactCapsuleFlags.NONE,
        )

        assert len(capsule.capsule_id) == 32
        assert len(capsule.model_hash) == 32
        assert len(capsule.signature) == 64
        assert capsule.capsule_id_hex == "a" * 64

    def test_capsule_timestamp_conversion(self):
        """Test timestamp conversion to datetime."""
        now_ms = int(time.time() * 1000)
        capsule = CompactCapsule(
            capsule_id=bytes(32),
            timestamp_ms=now_ms,
            model_hash=bytes(32),
            payload={},
            signature=bytes(64),
        )

        dt = capsule.timestamp
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc

    def test_capsule_flags(self):
        """Test capsule flags."""
        flags = CompactCapsuleFlags.COMPRESSED | CompactCapsuleFlags.HAS_ATTESTATION
        assert flags & CompactCapsuleFlags.COMPRESSED
        assert flags & CompactCapsuleFlags.HAS_ATTESTATION
        assert not (flags & CompactCapsuleFlags.ENCRYPTED)


class TestCompactCapsuleEncoder:
    """Test CompactCapsuleEncoder."""

    def test_encode_capsule(self):
        """Test encoding a capsule to binary."""
        encoder = CompactCapsuleEncoder()

        capsule = CompactCapsule(
            capsule_id=bytes.fromhex("a" * 64),
            timestamp_ms=1709424000000,  # Fixed timestamp
            model_hash=bytes.fromhex("b" * 64),
            payload={"t": "inference", "m": "gpt-4"},
            signature=bytes(64),
        )

        binary = encoder.encode(capsule)

        # Check magic and version
        assert binary[:4] == COMPACT_CAPSULE_MAGIC
        version = struct.unpack(">H", binary[4:6])[0]
        assert version == COMPACT_CAPSULE_VERSION

    def test_encode_minimal_capsule(self):
        """Test encoding a minimal capsule."""
        encoder = CompactCapsuleEncoder()

        binary = encoder.encode_minimal(
            capsule_type="inference",
            model_id="gpt-4-turbo",
            content_hash="c" * 64,
            signature=bytes(64),
        )

        # Should be under 1KB target
        assert len(binary) < 1024

    def test_encode_minimal_with_metadata(self):
        """Test encoding minimal capsule with metadata."""
        encoder = CompactCapsuleEncoder()

        binary = encoder.encode_minimal(
            capsule_type="reasoning",
            model_id="claude-3",
            content_hash="d" * 64,
            signature=bytes(64),
            metadata={"tokens": 150, "latency_ms": 234},
        )

        assert len(binary) < 1024


class TestCompactCapsuleDecoder:
    """Test CompactCapsuleDecoder."""

    def test_decode_capsule(self):
        """Test decoding a binary capsule."""
        encoder = CompactCapsuleEncoder()
        decoder = CompactCapsuleDecoder()

        original = CompactCapsule(
            capsule_id=bytes.fromhex("e" * 64),
            timestamp_ms=1709424000000,
            model_hash=bytes.fromhex("f" * 64),
            payload={"t": "inference", "result": "test"},
            signature=bytes(64),
        )

        binary = encoder.encode(original)
        decoded = decoder.decode(binary)

        assert decoded.capsule_id == original.capsule_id
        assert decoded.timestamp_ms == original.timestamp_ms
        assert decoded.model_hash == original.model_hash
        assert decoded.payload == original.payload

    def test_decode_invalid_magic(self):
        """Test decoding with invalid magic bytes."""
        decoder = CompactCapsuleDecoder()

        # Create invalid data
        invalid_data = b"XXXX" + bytes(FIXED_OVERHEAD - 4)

        with pytest.raises(ValueError, match="Invalid magic"):
            decoder.decode(invalid_data)

    def test_decode_unsupported_version(self):
        """Test decoding with unsupported version."""
        decoder = CompactCapsuleDecoder()

        # Create data with wrong version
        data = bytearray(FIXED_OVERHEAD + 10)
        data[0:4] = COMPACT_CAPSULE_MAGIC
        struct.pack_into(">H", data, 4, 0x0099)  # Wrong version
        struct.pack_into(">I", data, 8, 10)  # Payload length

        with pytest.raises(ValueError, match="Unsupported version"):
            decoder.decode(bytes(data))

    def test_decode_truncated_data(self):
        """Test decoding with truncated data."""
        decoder = CompactCapsuleDecoder()

        # Too short
        with pytest.raises(ValueError, match="too short"):
            decoder.decode(bytes(10))

    def test_roundtrip_with_flags(self):
        """Test encode/decode roundtrip with flags."""
        encoder = CompactCapsuleEncoder()
        decoder = CompactCapsuleDecoder()

        original = CompactCapsule(
            capsule_id=bytes.fromhex("01" * 32),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes.fromhex("02" * 32),
            payload={"test": True},
            signature=bytes(64),
            flags=CompactCapsuleFlags.OFFLINE_SIGNED
            | CompactCapsuleFlags.WORKFLOW_STEP,
        )

        binary = encoder.encode(original)
        decoded = decoder.decode(binary)

        assert decoded.flags == original.flags
        assert decoded.flags & CompactCapsuleFlags.OFFLINE_SIGNED
        assert decoded.flags & CompactCapsuleFlags.WORKFLOW_STEP


class TestEdgeSyncService:
    """Test EdgeSyncService."""

    def test_queue_capsule(self):
        """Test queuing capsules for sync."""
        service = EdgeSyncService()
        encoder = CompactCapsuleEncoder()

        capsule_data = encoder.encode_minimal(
            capsule_type="inference",
            model_id="test-model",
            content_hash="aa" * 32,
            signature=bytes(64),
        )

        result = service.queue_capsule("device_001", capsule_data, skip_auth=True)
        assert result is True
        assert service.get_pending_count("device_001") == 1

    def test_create_sync_batch(self):
        """Test creating sync batch."""
        service = EdgeSyncService()
        encoder = CompactCapsuleEncoder()

        # Queue multiple capsules
        for i in range(5):
            capsule_data = encoder.encode_minimal(
                capsule_type="inference",
                model_id=f"model-{i}",
                content_hash=f"{i:02x}" * 32,
                signature=bytes(64),
            )
            service.queue_capsule("device_002", capsule_data, skip_auth=True)

        batch = service.create_sync_batch("device_002")
        assert batch is not None
        assert batch.count == 5
        assert batch.device_id == "device_002"

    def test_process_sync_batch(self):
        """Test processing sync batch."""
        service = EdgeSyncService()
        encoder = CompactCapsuleEncoder()

        # Queue capsule
        capsule_data = encoder.encode_minimal(
            capsule_type="inference",
            model_id="test-model",
            content_hash="bb" * 32,
            signature=bytes(64),
        )
        service.queue_capsule("device_003", capsule_data, skip_auth=True)

        # Create and process batch
        batch = service.create_sync_batch("device_003")
        result = service.process_sync_batch(batch)

        assert result.status == SyncStatus.COMPLETED
        assert result.synced_count == 1
        assert result.failed_count == 0
        assert service.get_pending_count("device_003") == 0

    def test_sync_with_conflicts(self):
        """Test sync with conflicting capsule IDs."""
        service = EdgeSyncService(conflict_resolution=ConflictResolution.MANUAL)
        encoder = CompactCapsuleEncoder()
        decoder = CompactCapsuleDecoder()

        # Queue capsule
        capsule_data = encoder.encode_minimal(
            capsule_type="inference",
            model_id="test-model",
            content_hash="cc" * 32,
            signature=bytes(64),
        )
        service.queue_capsule("device_004", capsule_data, skip_auth=True)

        # Get capsule ID to create conflict
        capsule = decoder.decode(capsule_data)
        existing_ids = [capsule.capsule_id_hex]

        # Process with conflict
        batch = service.create_sync_batch("device_004")
        result = service.process_sync_batch(batch, cloud_capsule_ids=existing_ids)

        assert result.conflict_count == 1
        assert result.status == SyncStatus.CONFLICT

    def test_sync_device_full(self):
        """Test full device sync."""
        service = EdgeSyncService(max_batch_size=3)
        encoder = CompactCapsuleEncoder()

        # Queue more capsules than batch size
        for i in range(7):
            capsule_data = encoder.encode_minimal(
                capsule_type="inference",
                model_id=f"model-{i}",
                content_hash=f"{i:02x}" * 32,
                signature=bytes(64),
            )
            service.queue_capsule("device_005", capsule_data, skip_auth=True)

        # Sync all
        result = service.sync_device("device_005")

        assert result.synced_count == 7
        assert result.status == SyncStatus.COMPLETED
        assert service.get_pending_count("device_005") == 0

    def test_checkpoint_management(self):
        """Test checkpoint creation and retrieval."""
        service = EdgeSyncService()
        encoder = CompactCapsuleEncoder()

        capsule_data = encoder.encode_minimal(
            capsule_type="inference",
            model_id="test-model",
            content_hash="dd" * 32,
            signature=bytes(64),
        )
        service.queue_capsule("device_006", capsule_data, skip_auth=True)

        batch = service.create_sync_batch("device_006")
        result = service.process_sync_batch(batch)

        checkpoint = service.get_checkpoint("device_006")
        assert checkpoint is not None
        assert checkpoint.device_id == "device_006"
        assert checkpoint.sync_sequence == 1


class TestOfflineSigner:
    """Test OfflineSigner."""

    def test_create_signer(self):
        """Test creating offline signer."""
        signer = OfflineSigner(device_id="test_device")

        assert signer.device_id == "test_device"
        assert len(signer.public_key) == 32

    def test_sign_capsule_data(self):
        """Test signing capsule data."""
        signer = OfflineSigner(device_id="test_device")

        result = signer.sign_capsule_data(
            capsule_id=bytes(32),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes(32),
            payload={"test": "data"},
        )

        assert result.success is True
        assert result.signature is not None
        assert len(result.signature) == 64

    def test_verify_own_signature(self):
        """Test verifying own signature."""
        signer = OfflineSigner(device_id="test_device")

        data = b"test data to sign"
        sign_result = signer.sign_raw(data)
        assert sign_result.success

        verify_result = signer.verify_signature(data, sign_result.signature)
        assert verify_result.valid is True

    def test_verify_with_wrong_data(self):
        """Test verification with wrong data fails."""
        signer = OfflineSigner(device_id="test_device")

        data = b"original data"
        sign_result = signer.sign_raw(data)

        # Verify with different data
        verify_result = signer.verify_signature(b"wrong data", sign_result.signature)
        assert verify_result.valid is False

    def test_pending_signatures(self):
        """Test pending signature tracking."""
        signer = OfflineSigner(device_id="test_device")

        # Sign some data
        signer.sign_capsule_data(
            capsule_id=bytes.fromhex("01" * 32),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes(32),
            payload={"n": 1},
        )
        signer.sign_capsule_data(
            capsule_id=bytes.fromhex("02" * 32),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes(32),
            payload={"n": 2},
        )

        pending = signer.get_pending_signatures()
        assert len(pending) == 2
        assert all(sig.status == SignatureStatus.PENDING for sig in pending)

    def test_mark_signature_verified(self):
        """Test marking signature as verified."""
        signer = OfflineSigner(device_id="test_device")

        result = signer.sign_capsule_data(
            capsule_id=bytes(32),
            timestamp_ms=int(time.time() * 1000),
            model_hash=bytes(32),
            payload={},
        )

        assert signer.mark_verified(result.signature_id)

        pending = signer.get_pending_signatures()
        assert len(pending) == 0

    def test_export_public_key_info(self):
        """Test exporting public key info."""
        signer = OfflineSigner(device_id="my_device")

        info = signer.export_public_key_info()

        assert info["device_id"] == "my_device"
        assert info["key_type"] == "ed25519"
        assert len(info["public_key"]) == 64  # Hex encoded


class TestOfflineSignerRegistry:
    """Test OfflineSignerRegistry."""

    def test_register_device(self):
        """Test registering a device."""
        registry = OfflineSignerRegistry()
        signer = OfflineSigner(device_id="device_001")

        result = registry.register_device(
            device_id="device_001",
            public_key=signer.public_key,
            metadata={"type": "edge"},
        )

        assert result is True
        assert registry.get_public_key("device_001") == signer.public_key

    def test_verify_device_signature(self):
        """Test verifying signature from registered device."""
        registry = OfflineSignerRegistry()
        signer = OfflineSigner(device_id="device_002")

        # Register device
        registry.register_device("device_002", signer.public_key)

        # Sign data
        data = b"test data"
        sign_result = signer.sign_raw(data)

        # Verify through registry
        verify_result = registry.verify_device_signature(
            device_id="device_002",
            data=data,
            signature=sign_result.signature,
        )

        assert verify_result.valid is True

    def test_verify_unregistered_device(self):
        """Test verifying from unregistered device fails."""
        registry = OfflineSignerRegistry()

        result = registry.verify_device_signature(
            device_id="unknown",
            data=b"data",
            signature=bytes(64),
        )

        assert result.valid is False
        assert "not registered" in result.error

    def test_list_devices(self):
        """Test listing registered devices."""
        registry = OfflineSignerRegistry()

        for i in range(3):
            signer = OfflineSigner(device_id=f"device_{i}")
            registry.register_device(f"device_{i}", signer.public_key)

        devices = registry.list_devices()
        assert len(devices) == 3


class TestEstimateCapsuleSize:
    """Test capsule size estimation."""

    def test_estimate_minimal_payload(self):
        """Test size estimation for minimal payload."""
        payload = {"t": "inf"}
        size = estimate_capsule_size(payload)

        assert size >= FIXED_OVERHEAD
        assert size < 200

    def test_estimate_larger_payload(self):
        """Test size estimation for larger payload."""
        payload = {
            "type": "reasoning_trace",
            "model": "claude-3-opus",
            "tokens": {"input": 1500, "output": 2000},
            "reasoning_steps": ["step1", "step2", "step3"],
        }
        size = estimate_capsule_size(payload)

        assert size > FIXED_OVERHEAD
        assert size < 500
