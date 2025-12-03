import secrets

import pytest
from capsule_schema import Capsule
from crud import capsule as capsule_crud
from engine.capsule_engine import CapsuleEngine
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# A strategy for generating capsule data suitable for creation
# We only generate fields that are passed to the create_capsule method
capsule_creation_strategy = st.fixed_dictionaries(
    {
        "capsule_type": st.sampled_from(
            ["Introspective", "Refusal", "Joint", "Perspective", "Embodied"]
        ),
        "input_data": st.text(
            min_size=1,
            max_size=256,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
        "output": st.text(
            min_size=1,
            max_size=256,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
        "reasoning": st.text(
            min_size=1,
            max_size=512,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
        "model_version": st.text(
            min_size=1,
            max_size=32,
            alphabet=st.characters(blacklist_categories=("Cs",)),
        ),
    }
)


@pytest.fixture(scope="function")
def property_test_engine(setup_database, monkeypatch):
    """
    Provides a CapsuleEngine instance specifically for property-based tests,
    with a unique signing key for each test function invocation.
    """
    signing_key = secrets.token_hex(32)
    monkeypatch.setenv("UATP_SIGNING_KEY", signing_key)
    monkeypatch.setenv("UATP_AGENT_ID", "property-test-agent")
    return CapsuleEngine(db=setup_database)


@pytest.mark.asyncio
@given(capsule_data=capsule_creation_strategy)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
async def test_create_log_and_verify_capsule(
    property_test_engine: CapsuleEngine, capsule_data: dict
):
    """
    Tests the full lifecycle of a capsule using property-based testing:
    1. Creates a capsule with generated data.
    2. Logs the capsule to the database.
    3. Retrieves the capsule from the database.
    4. Verifies the integrity and signature of the retrieved capsule.
    """
    engine = property_test_engine

    # 1. Create and persist the capsule using the generated data
    created_capsule = await engine.create_capsule_async(
        parent_capsule=None, **capsule_data
    )

    # 2. Retrieve the capsule directly from the database to ensure it was persisted
    db_capsule_model = await capsule_crud.get_capsule_async(
        engine.db, created_capsule.capsule_id
    )
    assert (
        db_capsule_model is not None
    ), "Capsule was not found in the database after logging."
    assert db_capsule_model.capsule_id == created_capsule.capsule_id
    assert db_capsule_model.input_data == created_capsule.input_data

    # 4. Convert the retrieved SQLAlchemy model to a Pydantic schema for verification
    retrieved_pydantic_capsule = Capsule.model_validate(db_capsule_model)

    # 5. Verify the capsule's cryptographic integrity
    is_valid, reason = await engine.verify_capsule_async(retrieved_pydantic_capsule)
    assert is_valid, f"Capsule signature verification failed: {reason}"

    # 6. Verify that the engine's load_chain method retrieves the capsule
    chain = await engine.load_chain_async(limit=1)
    assert len(chain) == 1, "load_chain did not return the expected number of capsules."
    assert (
        chain[0].capsule_id == created_capsule.capsule_id
    ), "The capsule ID from load_chain does not match."


# A strategy for generating a wide variety of unicode text.
# This includes control characters, non-printable characters, emojis, etc.
# to test for robustness against unexpected inputs.
fuzz_text_strategy = st.text()


@pytest.mark.asyncio
@given(
    input_text=fuzz_text_strategy,
    output_text=fuzz_text_strategy,
    reasoning_text=fuzz_text_strategy,
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
async def test_input_fuzzing_does_not_crash_creation(
    property_test_engine: CapsuleEngine,
    input_text: str,
    output_text: str,
    reasoning_text: str,
):
    """
    Tests that creating a capsule with a wide range of 'fuzzed' text inputs
    does not cause the engine to crash. The goal is to ensure robustness against
    unexpected unicode characters, control characters, and other edge cases.
    """
    engine = property_test_engine
    try:
        await engine.create_capsule_async(
            capsule_type="fuzz_test",
            input_data=input_text,
            output=output_text,
            reasoning=reasoning_text,
            model_version="fuzz-v1",
        )
    except Exception as e:
        # We expect some inputs to be invalid (e.g., violate database constraints
        # if they were ever to be implemented), but we should not have unexpected crashes.
        # For now, we'll just fail on any exception to see what Hypothesis finds.
        pytest.fail(f"Capsule creation crashed with unexpected exception: {e!r}")
