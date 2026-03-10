"""
Tests for the Zero-Knowledge Proof System.
"""

from datetime import datetime, timezone

import pytest

from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)
from src.crypto.zero_knowledge import ProofType, ZKCircuit, zk_system
from src.privacy.capsule_privacy import (
    DEFAULT_PRIVACY_POLICIES,
    PrivacyLevel,
    PrivacyPolicy,
    privacy_engine,
)


def test_zk_circuit_registration():
    """Test registering ZK circuits."""
    circuit = ZKCircuit(
        circuit_id="test_circuit",
        circuit_type="test",
        constraints=["x > 0", "y < 100"],
        public_inputs=["x", "y"],
        private_inputs=["secret"],
    )

    circuit_hash = zk_system.register_circuit(circuit)

    assert len(circuit_hash) == 64  # SHA256 hash
    assert circuit.circuit_id in zk_system.circuits
    assert circuit.circuit_id in zk_system.proving_keys
    assert circuit.circuit_id in zk_system.verification_keys


def test_capsule_privacy_proof():
    """Test generating privacy proof for capsule."""
    capsule_data = {
        "capsule_id": "test_capsule_001",
        "capsule_type": "reasoning_trace",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reasoning_trace": {
            "steps": [
                {"content": "sensitive data", "step_type": "observation"},
                {"content": "private reasoning", "step_type": "conclusion"},
            ]
        },
        "metadata": {"internal_state": "confidential"},
    }

    private_witness = {
        "private_content": capsule_data["reasoning_trace"]["steps"],
        "agent_internal_state": capsule_data["metadata"],
        "nonce": "test_nonce_123",
    }

    proof = zk_system.prove_capsule_privacy(capsule_data, private_witness)

    assert proof.proof_type == ProofType.SNARK
    assert len(proof.proof_data) > 0
    assert proof.public_inputs["capsule_id"] == "test_capsule_001"
    assert "public_hash" in proof.public_inputs

    # Verify the proof
    is_valid = zk_system.verify_proof(proof)
    assert is_valid


def test_capsule_integrity_proof():
    """Test generating integrity proof for capsule."""
    capsule_hash = "abcdef1234567890" * 4  # Mock hash

    proof = zk_system.prove_capsule_integrity(capsule_hash, signature_valid=True)

    assert proof.proof_type == ProofType.SNARK
    assert len(proof.proof_data) > 0
    assert proof.public_inputs["capsule_hash"] == capsule_hash

    # Verify the proof
    is_valid = zk_system.verify_proof(proof)
    assert is_valid


def test_range_proof():
    """Test generating range proof."""
    value = 50
    min_value = 0
    max_value = 100

    proof = zk_system.prove_range(value, min_value, max_value)

    assert proof.proof_type in [ProofType.SNARK, ProofType.BULLETPROOF]
    assert len(proof.proof_data) > 0
    assert proof.public_inputs["min_value"] == min_value
    assert proof.public_inputs["max_value"] == max_value
    assert "commitment" in proof.public_inputs

    # Verify the proof
    is_valid = zk_system.verify_proof(proof)
    assert is_valid


def test_privacy_policy_creation():
    """Test creating privacy policies."""
    policy = PrivacyPolicy(
        privacy_level=PrivacyLevel.SELECTIVE,
        disclosed_fields={"capsule_id", "timestamp"},
        redacted_fields={"reasoning_trace"},
        proof_required=True,
        authorized_viewers=["user1", "user2"],
    )

    assert policy.privacy_level == PrivacyLevel.SELECTIVE
    assert policy.allows_field("capsule_id")
    assert policy.allows_field("timestamp")
    assert not policy.allows_field("reasoning_trace")


def test_capsule_privatization():
    """Test converting capsule to private capsule."""
    # Create a test capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(
            signature="test_signature",
            merkle_root="sha256:" + "0" * 64,
            hash="test_hash",
            signer="test_agent",
        ),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="Sensitive reasoning step",
                    step_type="observation",
                    metadata={"confidence": 0.8},
                )
            ]
        ),
    )

    # Use selective privacy policy
    privacy_policy = DEFAULT_PRIVACY_POLICIES["selective"]

    # Privatize the capsule
    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    assert private_capsule.capsule_id == capsule.capsule_id
    assert private_capsule.privacy_policy.privacy_level == PrivacyLevel.SELECTIVE
    assert private_capsule.integrity_proof is not None
    assert private_capsule.privacy_proof is not None
    assert len(private_capsule.original_capsule_hash) == 64

    # Verify the private capsule
    is_valid = privacy_engine.verify_private_capsule(private_capsule)
    assert is_valid


def test_selective_disclosure():
    """Test selective disclosure of capsule fields."""
    # Create and privatize a capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(
            signature="test_signature",
            merkle_root="sha256:" + "0" * 64,
            hash="test_hash",
            signer="test_agent",
        ),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="Public reasoning step",
                    step_type="observation",
                    metadata={"public": True},
                )
            ]
        ),
    )

    privacy_policy = PrivacyPolicy(
        privacy_level=PrivacyLevel.SELECTIVE,
        disclosed_fields={"capsule_id", "timestamp", "status"},
        redacted_fields={"reasoning_trace"},
        proof_required=True,
        authorized_viewers=["authorized_user"],
    )

    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    # Request selective disclosure
    requested_fields = {"capsule_id", "timestamp", "reasoning_trace"}
    disclosure = privacy_engine.selective_disclosure(
        private_capsule.capsule_id, requested_fields, "authorized_user"
    )

    assert disclosure["capsule_id"] == private_capsule.capsule_id
    assert "disclosed_fields" in disclosure
    assert "capsule_id" in disclosure["disclosed_fields"]
    assert "timestamp" in disclosure["disclosed_fields"]
    assert "reasoning_trace" not in disclosure["disclosed_fields"]  # Should be redacted
    assert "disclosure_proof" in disclosure


def test_capsule_property_proofs():
    """Test proving capsule properties without revealing content."""
    # Create and privatize a capsule
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(steps=[]),
    )

    privacy_policy = DEFAULT_PRIVACY_POLICIES["private"]
    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    # Prove timestamp is within a range
    current_time = int(datetime.now(timezone.utc).timestamp())
    timestamp_proof = privacy_engine.prove_capsule_property(
        private_capsule.capsule_id,
        "timestamp_range",
        (current_time - 3600, current_time + 3600),  # Within last hour
    )

    assert timestamp_proof.proof_type in [ProofType.SNARK, ProofType.BULLETPROOF]
    assert zk_system.verify_proof(timestamp_proof)

    # Prove capsule type
    type_proof = privacy_engine.prove_capsule_property(
        private_capsule.capsule_id, "capsule_type", "reasoning_trace"
    )

    assert zk_system.verify_proof(type_proof)


def test_privacy_report():
    """Test generating privacy report."""
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(steps=[]),
    )

    privacy_policy = DEFAULT_PRIVACY_POLICIES["confidential"]
    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    report = privacy_engine.create_privacy_report(private_capsule.capsule_id)

    assert report["capsule_id"] == private_capsule.capsule_id
    assert report["privacy_level"] == "confidential"
    assert "proofs_verified" in report
    assert report["proofs_verified"]["integrity"] is True
    assert report["proofs_verified"]["privacy"] is True
    assert "disclosed_fields" in report
    assert "redacted_fields" in report


def test_unauthorized_access():
    """Test that unauthorized users cannot access private capsules."""
    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2024_01_01_0123456789abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(steps=[]),
    )

    privacy_policy = PrivacyPolicy(
        privacy_level=PrivacyLevel.PRIVATE,
        disclosed_fields={"capsule_id"},
        redacted_fields={"reasoning_trace", "timestamp"},
        proof_required=True,
        authorized_viewers=["authorized_user"],
    )

    private_capsule = privacy_engine.privatize_capsule(capsule, privacy_policy)

    # Try to access with unauthorized user
    with pytest.raises(PermissionError):
        privacy_engine.selective_disclosure(
            private_capsule.capsule_id, {"capsule_id", "timestamp"}, "unauthorized_user"
        )


def test_proof_serialization():
    """Test that proofs can be serialized and deserialized."""
    proof = zk_system.prove_range(42, 0, 100)

    # Serialize to dict
    proof_dict = proof.to_dict()

    assert "proof_type" in proof_dict
    assert "proof_data" in proof_dict
    assert "public_inputs" in proof_dict
    assert "verification_key" in proof_dict
    assert "circuit_hash" in proof_dict

    # Check that proof data is hex-encoded
    assert isinstance(proof_dict["proof_data"], str)
    assert isinstance(proof_dict["verification_key"], str)


if __name__ == "__main__":
    test_zk_circuit_registration()
    test_capsule_privacy_proof()
    test_capsule_integrity_proof()
    test_range_proof()
    test_privacy_policy_creation()
    test_capsule_privatization()
    test_selective_disclosure()
    test_capsule_property_proofs()
    test_privacy_report()
    test_unauthorized_access()
    test_proof_serialization()
    print("[OK] All ZK-proof tests passed!")
