import pytest
from capsule_schema import Capsule
from crud import capsule as capsule_crud
from engine.capsule_engine import CapsuleEngine, UATPEngineError

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_capsule_lifecycle_with_verification(setup_database, monkeypatch):
    """Tests the complete lifecycle of a capsule: creation, signing, logging, loading, and verification."""
    # 1. Setup
    monkeypatch.setenv("UATP_AGENT_ID", "fixture-agent")
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    engine = CapsuleEngine(db=setup_database)

    # 2. Creation: Create a new capsule
    created_capsule = await engine.create_capsule_async(
        capsule_type="test_lifecycle",
        input_data="Test input data",
        output="Test output data",
        reasoning="Testing the full lifecycle",
        model_version="1.0.0",
    )
    assert created_capsule is not None
    assert created_capsule.agent_id == engine.agent_id
    assert created_capsule.signature is not None

    # 3. Storage: Verify the capsule was persisted
    db_capsule = await capsule_crud.get_capsule_async(
        setup_database, created_capsule.capsule_id
    )
    assert db_capsule is not None

    # 4. Retrieval: Load the capsule from the chain
    loaded_capsules = await engine.load_chain_async()
    assert len(loaded_capsules) == 1
    loaded_capsule = loaded_capsules[0]

    assert loaded_capsule.capsule_id == created_capsule.capsule_id
    assert loaded_capsule.output == "Test output data"

    # 5. Verification: Verify the loaded capsule's integrity and signature
    is_valid, reason = await engine.verify_capsule_async(loaded_capsule)
    assert (
        is_valid
    ), f"The loaded capsule should have a valid signature, but failed with: {reason}"


@pytest.mark.asyncio
async def test_malformed_signature_handling(setup_database, monkeypatch):
    """
    Tests that the engine correctly identifies a capsule with a tampered signature.
    """
    # 1. Setup
    monkeypatch.setenv("UATP_AGENT_ID", "fixture-agent")
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    engine = CapsuleEngine(db=setup_database)

    # 2. Setup: Create and log a valid capsule
    capsule = await engine.create_capsule_async(
        capsule_type="test_malformed",
        input_data="Original input",
        output="Legit output",
        reasoning="Testing malformed signature detection",
        model_version="2.0.0",
    )

    # 3. Manually tamper with the signature in the database
    db_capsule = await capsule_crud.get_capsule_async(
        setup_database, capsule.capsule_id
    )
    await capsule_crud.update_capsule_signature_async(
        setup_database, db_capsule.capsule_id, "clearlyinvalidsignature"
    )

    # 4. Reload the chain and attempt to verify the tampered capsule
    loaded_capsules = await engine.load_chain_async()
    tampered_capsule = loaded_capsules[0]

    is_valid, reason = await engine.verify_capsule_async(tampered_capsule)

    # 5. Assert that verification fails
    assert not is_valid, "Engine should have detected the malformed signature."
    assert "non-hexadecimal number found" in reason


@pytest.mark.asyncio
async def test_signature_forgery_prevention(setup_database, monkeypatch):
    """
    Tests that the engine rejects a capsule whose payload has been tampered with
    after signing, preventing signature forgery.
    """
    # 1. Setup
    monkeypatch.setenv("UATP_AGENT_ID", "fixture-agent")
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    engine = CapsuleEngine(db=setup_database)

    # 2. Create a valid capsule
    original_capsule = await engine.create_capsule_async(
        capsule_type="test_forgery",
        input_data="Original, legitimate input.",
        output="Valid output.",
        reasoning="Testing signature integrity.",
        model_version="4.0.0",
    )

    # 3. Create a tampered version of the capsule
    # This simulates an attacker intercepting the capsule data and altering it.
    tampered_capsule_data = original_capsule.model_dump()
    tampered_capsule_data["output"] = "Malicious, tampered output."

    # Re-create the capsule object from the tampered data. The signature is still the original one.
    tampered_capsule = Capsule(**tampered_capsule_data)

    # 4. Attempt to verify the tampered capsule
    # The engine should re-calculate the hash of the tampered payload and find
    # it doesn't match the signature.
    is_valid, _ = await engine.verify_capsule_async(tampered_capsule)

    # 5. Assert that verification fails
    assert (
        not is_valid
    ), "Engine should have rejected the capsule with a forged signature."

    # 6. As a control, verify the original capsule to ensure it's still valid
    is_original_valid, reason = await engine.verify_capsule_async(original_capsule)
    assert (
        is_original_valid
    ), f"The original, untampered capsule should still be valid, but failed with {reason}."


@pytest.mark.security
@pytest.mark.asyncio
async def test_replay_attack_prevention(setup_database, monkeypatch):
    """
    Tests that the engine prevents replay attacks by rejecting capsules that have
    already been logged.
    """
    # 1. Setup
    monkeypatch.setenv("UATP_AGENT_ID", "fixture-agent")
    monkeypatch.setenv(
        "UATP_SIGNING_KEY",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    engine = CapsuleEngine(db=setup_database)

    # 2. Create and log a capsule for the first time.
    capsule_to_replay = await engine.create_capsule_async(
        capsule_type="test_replay",
        input_data="Original transaction.",
        output="Action performed once.",
        reasoning="Initial valid operation.",
        model_version="5.0.0",
    )

    # 3. Attempt to create the exact same capsule again.
    # This should be rejected by the engine's persistence layer due to duplicate primary key.
    with pytest.raises(UATPEngineError) as excinfo:
        await engine.create_capsule_async(
            capsule_type="test_replay",
            input_data="Original transaction.",
            output="Action performed once.",
            reasoning="Initial valid operation.",
            model_version="5.0.0",
            # Re-using the same data will generate the same ID
            capsule_id=capsule_to_replay.capsule_id,
            timestamp=capsule_to_replay.timestamp,
            signature=capsule_to_replay.signature,
        )

    # 4. Assert that the error message indicates a persistence conflict.
    assert "already exists" in str(excinfo.value)

    # 5. Verify that the database only contains the first instance.
    all_capsules = await capsule_crud.get_capsules_async(setup_database, limit=-1)
    assert len(all_capsules) == 1, "The replayed capsule should not have been logged."
    assert all_capsules[0].capsule_id == capsule_to_replay.capsule_id
