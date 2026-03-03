"""
Unit tests for UATP 7.2 Hardware Attestation

Tests:
- Challenge generation
- Attestation verification
- Capsule schema validation
- UATP envelope integration
"""

from datetime import datetime, timezone

from src.capsule_schema import (
    CapsuleStatus,
    CapsuleType,
    HardwareAttestationCapsule,
    HardwareAttestationPayload,
    Verification,
)
from src.security.attestation import (
    AttestationResult,
    AttestationType,
    HardwareAttestationService,
)
from src.utils.uatp_envelope import (
    create_hardware_attestation_context,
    detect_capsule_version,
    wrap_in_uatp_envelope,
)


class TestHardwareAttestationPayload:
    """Test HardwareAttestationPayload validation."""

    def test_valid_apple_attestation(self):
        """Test creating Apple Secure Enclave attestation payload."""
        payload = HardwareAttestationPayload(
            attestation_type="apple_secure_enclave",
            device_id_hash="sha256:" + "a" * 64,
            attestation_timestamp=datetime.now(timezone.utc),
            attestation_data="base64encodeddata",
            certificate_chain=[
                "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----"
            ],
            nonce="abc123def456",
            measurements={"secure_boot": "enabled"},
            verified=True,
        )
        assert payload.attestation_type == "apple_secure_enclave"
        assert payload.verified is True

    def test_valid_android_tee_attestation(self):
        """Test creating Android TEE attestation payload."""
        payload = HardwareAttestationPayload(
            attestation_type="android_tee",
            device_id_hash="sha256:" + "b" * 64,
            attestation_timestamp=datetime.now(timezone.utc),
            attestation_data="base64encodeddata",
            certificate_chain=[],
            nonce="xyz789",
            measurements={
                "security_level": "strong_box",
                "verified_boot": "green",
            },
            verified=True,
        )
        assert payload.attestation_type == "android_tee"
        assert payload.measurements["security_level"] == "strong_box"

    def test_valid_nvidia_cc_attestation(self):
        """Test creating NVIDIA Confidential Computing attestation payload."""
        payload = HardwareAttestationPayload(
            attestation_type="nvidia_cc",
            device_id_hash="sha256:" + "c" * 64,
            attestation_timestamp=datetime.now(timezone.utc),
            attestation_data="gpuattestationblob",
            certificate_chain=[],
            nonce="gpu_nonce_123",
            measurements={
                "gpu_model": "H100",
                "confidential_mode": "enabled",
                "driver_version": "535.104.05",
            },
            verified=True,
        )
        assert payload.attestation_type == "nvidia_cc"
        assert payload.measurements["gpu_model"] == "H100"


class TestHardwareAttestationCapsule:
    """Test HardwareAttestationCapsule creation."""

    def test_create_attestation_capsule(self):
        """Test creating a complete hardware attestation capsule."""
        capsule = HardwareAttestationCapsule(
            capsule_id="caps_2026_03_02_a1b2c3d4e5f6a7b8",
            version="7.2",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signature="ed25519:" + "0" * 128,
                merkle_root="sha256:" + "0" * 64,
            ),
            hardware_attestation=HardwareAttestationPayload(
                attestation_type="simulated",
                device_id_hash="sha256:" + "d" * 64,
                attestation_timestamp=datetime.now(timezone.utc),
                attestation_data="testdata",
                certificate_chain=[],
                nonce="test_nonce",
                measurements={"simulated": "true"},
                verified=True,
            ),
        )
        assert capsule.capsule_type == CapsuleType.HARDWARE_ATTESTATION
        assert capsule.version == "7.2"


class TestHardwareAttestationService:
    """Test HardwareAttestationService functionality."""

    def test_generate_challenge(self):
        """Test challenge generation."""
        service = HardwareAttestationService()
        challenge = service.generate_challenge(
            attestation_type=AttestationType.SIMULATED,
            device_id_hint="test_device",
        )

        assert challenge.challenge_id.startswith("attest_")
        assert len(challenge.nonce) == 64  # 32 bytes = 64 hex chars
        assert challenge.attestation_type == AttestationType.SIMULATED
        assert challenge.device_id_hint == "test_device"

    def test_verify_simulated_attestation_success(self):
        """Test successful simulated attestation verification."""
        service = HardwareAttestationService()

        # Generate challenge
        challenge = service.generate_challenge(AttestationType.SIMULATED)

        # Create attestation data that includes the nonce
        attestation_data = f"attestation_blob_{challenge.nonce}".encode()

        # Verify
        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
            measurements={"test": "value"},
        )

        assert result.verified is True
        assert result.attestation_type == AttestationType.SIMULATED
        assert len(result.device_id_hash) == 64  # SHA-256 hex

    def test_verify_simulated_attestation_failure(self):
        """Test failed simulated attestation (wrong nonce)."""
        service = HardwareAttestationService()

        # Generate challenge
        challenge = service.generate_challenge(AttestationType.SIMULATED)

        # Create attestation data WITHOUT the nonce
        attestation_data = b"attestation_blob_wrong_nonce"

        # Verify
        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
        )

        assert result.verified is False

    def test_challenge_not_found(self):
        """Test verification with invalid challenge ID."""
        service = HardwareAttestationService()

        result = service.verify_attestation(
            challenge_id="invalid_challenge_id",
            attestation_data=b"data",
            certificate_chain=[],
        )

        assert result.verified is False
        assert "not found" in result.error.lower()

    def test_challenge_single_use(self):
        """Test that challenges can only be used once."""
        service = HardwareAttestationService()

        # Generate challenge
        challenge = service.generate_challenge(AttestationType.SIMULATED)
        attestation_data = f"blob_{challenge.nonce}".encode()

        # First verification should succeed
        result1 = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
        )
        assert result1.verified is True

        # Second verification with same challenge should fail
        result2 = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
        )
        assert result2.verified is False
        assert "not found" in result2.error.lower()

    def test_apple_attestation_stub(self):
        """Test Apple Secure Enclave attestation (stubbed).

        SECURITY: Stub attestations now correctly fail unless nonce is present.
        This prevents accepting arbitrary data as valid attestation.
        """
        service = HardwareAttestationService()
        challenge = service.generate_challenge(AttestationType.APPLE_SECURE_ENCLAVE)

        # Test without nonce - should fail (stub no longer accepts arbitrary data)
        attestation_data = b"apple_attestation_blob" * 5

        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[
                "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            ],
        )

        assert result.attestation_type == AttestationType.APPLE_SECURE_ENCLAVE
        # SECURITY: Stub now correctly rejects data without proper nonce verification
        assert result.verified is False
        assert result.error is not None

    def test_apple_attestation_stub_with_nonce(self):
        """Test Apple Secure Enclave attestation with nonce present."""
        service = HardwareAttestationService()
        challenge = service.generate_challenge(AttestationType.APPLE_SECURE_ENCLAVE)

        # Include nonce in attestation data - should pass stub verification
        attestation_data = b"apple_attestation_blob_" + challenge.nonce.encode()

        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[
                "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
            ],
        )

        assert result.attestation_type == AttestationType.APPLE_SECURE_ENCLAVE
        assert result.verified is True  # Passes when nonce is present

    def test_android_attestation_stub(self):
        """Test Android TEE attestation (stubbed).

        SECURITY: Stub attestations now correctly fail because real
        Play Integrity/Key Attestation integration is required.
        """
        service = HardwareAttestationService()
        challenge = service.generate_challenge(AttestationType.ANDROID_TEE)

        attestation_data = b"android_attestation_blob" * 2

        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
        )

        assert result.attestation_type == AttestationType.ANDROID_TEE
        # SECURITY: Stub now correctly rejects - requires real implementation
        assert result.verified is False
        assert result.error is not None

    def test_nvidia_attestation_stub(self):
        """Test NVIDIA CC attestation (stubbed).

        SECURITY: Stub attestations now correctly fail because real
        NVIDIA Attestation SDK integration is required.
        """
        service = HardwareAttestationService()
        challenge = service.generate_challenge(AttestationType.NVIDIA_CC)

        attestation_data = b"nvidia_cc_attestation_blob" * 2

        result = service.verify_attestation(
            challenge_id=challenge.challenge_id,
            attestation_data=attestation_data,
            certificate_chain=[],
            measurements={"gpu_model": "H100"},
        )

        assert result.attestation_type == AttestationType.NVIDIA_CC
        # SECURITY: Stub now correctly rejects - requires real implementation
        assert result.verified is False
        assert result.error is not None

    def test_create_attestation_payload(self):
        """Test creating attestation payload from result."""
        service = HardwareAttestationService()

        result = AttestationResult(
            verified=True,
            attestation_type=AttestationType.SIMULATED,
            device_id_hash="abc123",
            timestamp=datetime.now(timezone.utc),
            measurements={"test": "value"},
            certificate_chain=["cert1"],
            attestation_data="base64data",
        )

        payload = service.create_attestation_payload(result)

        assert payload["verified"] is True
        assert payload["attestation_type"] == "simulated"
        assert payload["device_id_hash"] == "abc123"
        assert payload["measurements"]["test"] == "value"


class TestAttestationContext:
    """Test hardware attestation context in UATP envelope."""

    def test_create_hardware_attestation_context(self):
        """Test creating hardware attestation context."""
        ctx = create_hardware_attestation_context(
            attestation_type="apple_secure_enclave",
            device_id_hash="sha256:" + "a" * 64,
            verified=True,
            measurements={"secure_boot": "enabled"},
        )

        assert ctx["attestation_type"] == "apple_secure_enclave"
        assert ctx["verified"] is True
        assert "timestamp" in ctx
        assert ctx["measurements"]["secure_boot"] == "enabled"

    def test_attestation_context_in_envelope(self):
        """Test hardware attestation context in UATP envelope."""
        ctx = create_hardware_attestation_context(
            attestation_type="nvidia_cc",
            device_id_hash="sha256:" + "b" * 64,
            verified=True,
        )

        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="hardware_attestation",
            hardware_attestation=ctx,
        )

        assert "hardware_attestation" in envelope
        assert envelope["_envelope"]["version"] == "7.2"
        assert detect_capsule_version(envelope) == "7.2"

    def test_envelope_without_attestation_is_71(self):
        """Test that envelope without attestation is version 7.1."""
        envelope = wrap_in_uatp_envelope(
            payload_data={"test": "data"},
            capsule_id="caps_test",
            capsule_type="reasoning_trace",
        )

        assert "hardware_attestation" not in envelope
        assert envelope["_envelope"]["version"] == "7.1"
        assert detect_capsule_version(envelope) == "7.1"
