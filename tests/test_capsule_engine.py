import uuid
from datetime import datetime, timezone

import pytest

from src.capsule_schema import (
    CapsuleStatus,
    CapsuleType,
    EconomicTransactionCapsule,
    EthicsTriggerCapsule,
    GovernanceVoteCapsule,
    PostQuantumSignatureCapsule,
    ReasoningTraceCapsule,
    Verification,
)
from src.crypto.post_quantum import pq_crypto
from src.engine.capsule_engine import CapsuleEngine


@pytest.fixture(scope="module")
def sample_payloads():
    """Provides a dictionary of sample payloads for each capsule type, aligned with UATP 7.0 schema."""
    return {
        CapsuleType.REASONING_TRACE: {
            "reasoning_steps": [
                {
                    "step_id": 1,
                    "operation": "observation",
                    "reasoning": "Initial data analysis",
                    "confidence": 0.9,
                },
                {
                    "step_id": 2,
                    "operation": "conclusion",
                    "reasoning": "Final outcome derived",
                    "confidence": 0.95,
                },
            ],
            "total_confidence": 0.92,
        },
        CapsuleType.ECONOMIC_TRANSACTION: {
            "transaction_type": "value_transfer",
            "amount": 100.0,
            "currency": "USD",
            "sender": "test-sender",
            "recipient": "test-recipient",
        },
        CapsuleType.GOVERNANCE_VOTE: {
            "proposal_id": "e18500e1-68f1-48a8-a283-8a474671e3a1",
            "vote": "approve",
            "stake_amount": 50.0,
        },
        CapsuleType.ETHICS_TRIGGER: {
            "triggering_event": "unsafe_content_detected",
            "severity_level": 4,
            "details": {"reason": "Generated content violated safety policy X."},
        },
        CapsuleType.POST_QUANTUM_SIGNATURE: {
            "original_signature": "ed25519:deadbeef",
            "pq_signature_data": "dilithium2:cafebabe",
        },
    }


@pytest.mark.asyncio
async def test_capsule_creation_and_logging(engine_with_signed_capsules):
    """Test that a created capsule can be loaded back from the database."""
    engine, created_capsules = engine_with_signed_capsules

    # Test loading the first capsule created in the fixture
    first_capsule = created_capsules[0]
    loaded_capsule = await engine.load_capsule_async(first_capsule.capsule_id)

    assert loaded_capsule is not None
    assert loaded_capsule.capsule_id == first_capsule.capsule_id
    assert loaded_capsule.capsule_type == first_capsule.capsule_type
    assert loaded_capsule.verification.signature == first_capsule.verification.signature
    assert loaded_capsule.verification.signer == "test-agent"


@pytest.mark.asyncio
async def test_chain_loading(engine_with_signed_capsules):
    """Test loading a chain of capsules from the database."""
    engine, created_capsules = engine_with_signed_capsules

    chain = await engine.load_chain_async(limit=10)
    assert len(chain) == len(created_capsules)
    assert chain[0].capsule_id == created_capsules[0].capsule_id
    assert chain[1].capsule_id == created_capsules[1].capsule_id


@pytest.mark.asyncio
async def test_signature_verification(engine, sample_payloads):
    """Test the signature verification of a capsule, including failure on tampering."""
    # 1. Create a valid capsule using the engine
    payload = sample_payloads[CapsuleType.ECONOMIC_TRANSACTION]
    unsigned_capsule = EconomicTransactionCapsule(
        capsule_id=f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.DRAFT,
        verification=Verification(
            signature=f"ed25519:{'0'*128}", merkle_root=f"sha256:{'0'*64}"
        ),
        economic_transaction=payload,
    )
    created_capsule = await engine.create_capsule_async(unsigned_capsule)

    # 2. Verify the valid capsule
    is_valid, reason = await engine.verify_capsule_async(created_capsule)
    assert is_valid, f"Verification failed unexpectedly: {reason}"

    # 3. Tamper with the payload and verify that the signature check fails
    tampered_capsule = created_capsule.model_copy(deep=True)
    tampered_capsule.economic_transaction.amount = 999.99
    is_valid, reason = await engine.verify_capsule_async(tampered_capsule)
    assert not is_valid, "Verification succeeded unexpectedly for tampered data"
    assert "mismatch" in reason  # Could be "Hash mismatch" or "Signature mismatch"


@pytest.mark.asyncio
async def test_missing_agent_id_env(async_session_factory, monkeypatch):
    """Test that CapsuleEngine works without UATP_AGENT_ID set."""
    monkeypatch.delenv("UATP_AGENT_ID", raising=False)
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "d6f0f8e9c9a2a5b3d8d1f4e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
    )
    # CapsuleEngine should initialize without UATP_AGENT_ID
    engine = CapsuleEngine(db_manager=async_session_factory)
    assert engine is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("capsule_type_enum", list(CapsuleType))
async def test_all_capsule_types_e2e(engine, sample_payloads, capsule_type_enum):
    """End-to-end test for creating, saving, loading, and verifying all capsule types."""
    capsule_map = {
        CapsuleType.REASONING_TRACE: ReasoningTraceCapsule,
        CapsuleType.ECONOMIC_TRANSACTION: EconomicTransactionCapsule,
        CapsuleType.GOVERNANCE_VOTE: GovernanceVoteCapsule,
        CapsuleType.ETHICS_TRIGGER: EthicsTriggerCapsule,
        CapsuleType.POST_QUANTUM_SIGNATURE: PostQuantumSignatureCapsule,
    }

    # Skip capsule types that don't have sample payloads
    if capsule_type_enum not in sample_payloads:
        pytest.skip(f"No sample payload for {capsule_type_enum}")

    # Skip post-quantum tests when library is not available
    if (
        capsule_type_enum == CapsuleType.POST_QUANTUM_SIGNATURE
        and not pq_crypto.dilithium_available
    ):
        pytest.skip("Post-quantum cryptography library (liboqs) not installed")

    payload = sample_payloads[capsule_type_enum]
    capsule_model = capsule_map[capsule_type_enum]

    # 1. Create and sign the capsule using the engine
    # The payload needs to be passed to the specific field name, which is the capsule_type's value
    unsigned_capsule = capsule_model(
        capsule_id=f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.DRAFT,
        verification=Verification(
            signature=f"ed25519:{'0'*128}", merkle_root=f"sha256:{'0'*64}"
        ),
        **{capsule_type_enum.value: payload},
    )
    created_capsule = await engine.create_capsule_async(unsigned_capsule)

    # 2. Verify the signature of the created capsule
    is_valid, reason = await engine.verify_capsule_async(created_capsule)
    assert is_valid, f"Verification failed for new {capsule_type_enum.name}: {reason}"

    # 3. Load the capsule from the database
    loaded_capsule = await engine.load_capsule_async(created_capsule.capsule_id)
    assert loaded_capsule is not None
    assert loaded_capsule.capsule_id == created_capsule.capsule_id
    assert loaded_capsule.capsule_type == capsule_type_enum
    # The payload is nested inside the specific capsule type field
    assert getattr(loaded_capsule, capsule_type_enum.value) == getattr(
        created_capsule, capsule_type_enum.value
    )

    # 4. Verify the signature of the loaded capsule
    is_valid_loaded, reason_loaded = await engine.verify_capsule_async(loaded_capsule)
    assert (
        is_valid_loaded
    ), f"Verification failed for loaded {capsule_type_enum.name}: {reason_loaded}"
