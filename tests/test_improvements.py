"""
Test the major improvements implemented based on the audit feedback.
"""

from datetime import datetime, timezone

import pytest

from src.audit.events import AuditEventType, audit_emitter
from src.capsule_schema import (
    CapsuleStatus,
    CapsuleType,
    ConsentCapsule,
    ConsentPayload,
    ManipulationAttemptCapsule,
    ManipulationAttemptPayload,
    UncertaintyCapsule,
    UncertaintyPayload,
    Verification,
)
from src.crypto.post_quantum import pq_crypto
from src.crypto_utils import (
    generate_post_quantum_keypair,
    hash_capsule_dict,
    hybrid_sign_capsule,
)


def test_all_21_capsule_types():
    """Test that UATP 7.0 capsule types are implemented (system now has 29 types)."""
    # System has evolved beyond original 21 types - now has 29
    assert len(CapsuleType) >= 21, f"Expected at least 21 types, got {len(CapsuleType)}"

    # Test that we can access all the new types
    assert CapsuleType.UNCERTAINTY == "uncertainty"
    assert CapsuleType.CONSENT == "consent"
    assert CapsuleType.MANIPULATION_ATTEMPT == "manipulation_attempt"
    assert CapsuleType.RETIREMENT == "retirement"


def test_new_capsule_creation():
    """Test creating capsules with the new UATP 7.0 types."""
    verification = Verification(
        signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        merkle_root="sha256:" + "0" * 64,
    )

    # Test uncertainty capsule
    uncertainty_capsule = UncertaintyCapsule(
        capsule_id="caps_2025_07_09_abcdef1234567890",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.DRAFT,
        verification=verification,
        uncertainty=UncertaintyPayload(
            confidence_score=0.7,
            missing_facts=["fact1", "fact2"],
            uncertainty_sources=["source1"],
            recommendation="Need more data",
        ),
    )

    assert uncertainty_capsule.capsule_type == CapsuleType.UNCERTAINTY
    assert uncertainty_capsule.uncertainty.confidence_score == 0.7

    # Test consent capsule
    consent_capsule = ConsentCapsule(
        capsule_id="caps_2025_07_09_fedcba0987654321",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.DRAFT,
        verification=verification,
        consent=ConsentPayload(
            consent_scope=["read", "write"],
            grantor="user123",
            granted_to="agent456",
            revocable=True,
        ),
    )

    assert consent_capsule.capsule_type == CapsuleType.CONSENT
    assert consent_capsule.consent.grantor == "user123"


def test_canonical_json_hashing():
    """Test that JSON hashing is stable and canonical."""
    test_data_1 = {"c": 3, "a": 1, "b": 2}
    test_data_2 = {"a": 1, "b": 2, "c": 3}  # Different order

    hash1 = hash_capsule_dict(test_data_1)
    hash2 = hash_capsule_dict(test_data_2)

    # Should be the same despite different key order
    assert hash1 == hash2

    # Should be consistent across multiple calls
    hash3 = hash_capsule_dict(test_data_1)
    assert hash1 == hash3


@pytest.mark.skipif(
    not pq_crypto.dilithium_available,
    reason="Post-quantum cryptography library (liboqs) not installed",
)
def test_post_quantum_crypto():
    """Test post-quantum cryptography functions."""
    # Test key generation
    pq_private, pq_public = generate_post_quantum_keypair()
    assert len(pq_private) > 0
    assert len(pq_public) > 0

    # Test hybrid signing
    ed25519_key = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    test_hash = "test_hash_string"

    hybrid_sig = hybrid_sign_capsule(test_hash, ed25519_key, pq_private)

    assert "ed25519" in hybrid_sig
    assert "post_quantum" in hybrid_sig
    assert hybrid_sig["ed25519"].startswith("ed25519:")
    assert hybrid_sig["post_quantum"].startswith("dilithium3:")


def test_audit_event_system():
    """Test the audit event system."""
    events_captured = []

    class TestAuditHandler:
        def handle(self, event):
            events_captured.append(event)

    # Add test handler
    test_handler = TestAuditHandler()
    audit_emitter.add_handler(test_handler)

    # Emit test events
    audit_emitter.emit_capsule_created(
        "test-capsule-001", "test-agent", "reasoning_trace"
    )
    audit_emitter.emit_capsule_verified(
        "test-capsule-001", "test-agent", True, "Valid signature"
    )

    # Check events were captured
    assert len(events_captured) == 2
    assert events_captured[0].event_type == AuditEventType.CAPSULE_CREATED
    assert events_captured[1].event_type == AuditEventType.CAPSULE_VERIFIED

    # Check event structure
    event_dict = events_captured[0].to_dict()
    assert "event_id" in event_dict
    assert "timestamp" in event_dict
    assert event_dict["capsule_id"] == "test-capsule-001"
    assert event_dict["agent_id"] == "test-agent"


def test_manipulation_attempt_capsule():
    """Test the manipulation attempt capsule for AI safety."""
    verification = Verification(
        signature="ed25519:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        merkle_root="sha256:" + "0" * 64,
    )

    manipulation_capsule = ManipulationAttemptCapsule(
        capsule_id="caps_2025_07_09_1234567890abcdef",
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.SEALED,
        verification=verification,
        manipulation_attempt=ManipulationAttemptPayload(
            attempt_type="jailbreak",
            severity=8,
            successful=False,
            countermeasures=["rate_limiting", "content_filtering"],
        ),
    )

    assert manipulation_capsule.capsule_type == CapsuleType.MANIPULATION_ATTEMPT
    assert manipulation_capsule.manipulation_attempt.severity == 8
    assert not manipulation_capsule.manipulation_attempt.successful


def test_capsule_schema_completeness():
    """Test that we have all the key capsule types from the AI suggestions."""
    # Test that the AI-suggested capsule types are implemented
    ai_suggested_types = [
        "uncertainty",
        "conflict_resolution",
        "perspective",
        "feedback_assimilation",
        "knowledge_expiry",
        "emotional_load",
        "manipulation_attempt",
        "compute_footprint",
        "hand_off",
        "retirement",
    ]

    for suggested_type in ai_suggested_types:
        assert any(ct.value == suggested_type for ct in CapsuleType)
        print(f"[OK] {suggested_type} capsule type implemented")


if __name__ == "__main__":
    test_all_21_capsule_types()
    test_new_capsule_creation()
    test_canonical_json_hashing()
    test_post_quantum_crypto()
    test_audit_event_system()
    test_manipulation_attempt_capsule()
    test_capsule_schema_completeness()
    print("[OK] All improvement tests passed!")
