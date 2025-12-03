import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from api.server import create_app
from capsule_schema import Capsule
from crud import capsule as capsule_crud
from engine.capsule_engine import CapsuleEngine

from tests.mock_openai_client import MockOpenAIClient

# Mark all tests in this file as async and as integration tests
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_generate_reasoning_end_to_end(setup_database, monkeypatch):
    """Test the full end-to-end flow of generating and persisting a reasoning capsule."""
    # 1. Setup
    api_keys = {
        "full-access-key": {
            "roles": ["read", "write", "admin", "ai"],
            "agent_id": "test-agent-full-access",
        }
    }
    monkeypatch.setenv("UATP_API_KEYS", json.dumps(api_keys))
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    monkeypatch.setenv("UATP_SIGNING_KEY", "deadbeef" * 8)  # 32-byte hex key
    mock_openai_client = MockOpenAIClient()
    engine = CapsuleEngine(db=setup_database, openai_client=mock_openai_client)
    app = create_app(engine_override=engine)
    client = app.test_client()

    # 2. Make the request
    headers = {"X-API-Key": "full-access-key"}
    payload = {
        "prompt": "Explain the theory of relativity.",
        "model": "gpt-4-test",
        "agent_id": "test-agent-e2e",
        "capsule_type": "reasoning-e2e-test",
    }
    response = await client.post("/reasoning/generate", headers=headers, json=payload)

    # 3. Assert the HTTP response
    assert response.status_code == 201
    data = await response.get_json()
    assert data["output"] == "This is a mock AI response."

    # 4. Verify persistence
    capsule_id = data["capsule_id"]
    db_capsule = await capsule_crud.get_capsule_async(
        setup_database, capsule_id=capsule_id
    )
    assert db_capsule is not None
    assert db_capsule.output == "This is a mock AI response."


async def test_configurable_ai_model(setup_database, monkeypatch):
    """Test that the AI model can be configured via environment variables and overridden by API calls."""
    # 1. Setup
    api_keys = {
        "full-access-key": {
            "roles": ["read", "write", "admin", "ai"],
            "agent_id": "test-agent-full-access",
        }
    }
    monkeypatch.setenv("UATP_API_KEYS", json.dumps(api_keys))
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    monkeypatch.setenv("UATP_SIGNING_KEY", "deadbeef" * 8)  # 32-byte hex key

    engine = CapsuleEngine(db=setup_database, openai_client=MockOpenAIClient())

    # In the real engine, create_capsule_from_prompt_async returns a full Capsule object.
    # We mock that behavior here to ensure the endpoint receives a valid, complete object.
    mock_capsule_default = Capsule(
        capsule_id="mock-capsule-default",
        agent_id="test-agent",
        capsule_type="reasoning-test",
        timestamp=datetime.now(),
        input_data="mock prompt",
        output="Default model response.",
        reasoning="mock reasoning",
        model_version="gpt-4-from-env",
        signature="sig",
        hash="hash",
    )
    mock_capsule_override = Capsule(
        capsule_id="mock-capsule-override",
        agent_id="test-agent",
        capsule_type="reasoning-test",
        timestamp=datetime.now(),
        input_data="mock prompt",
        output="Override model response.",
        reasoning="mock reasoning",
        model_version="gpt-4-override",
        signature="sig",
        hash="hash",
    )
    engine.create_capsule_from_prompt_async = AsyncMock(
        side_effect=[mock_capsule_default, mock_capsule_override]
    )

    app = create_app(engine_override=engine)
    client = app.test_client()

    # 2. Test default model from environment variable
    default_model = "gpt-4-from-env"
    monkeypatch.setenv("UATP_DEFAULT_AI_MODEL", default_model)
    headers = {"X-API-Key": "full-access-key"}
    payload_default = {
        "prompt": "Use the default model.",
        "agent_id": "test-agent-full-access",
        "capsule_type": "reasoning",
    }
    response_default = await client.post(
        "/reasoning/generate", headers=headers, json=payload_default
    )
    assert response_default.status_code == 201
    data_default = await response_default.get_json()
    assert data_default["model_version"] == default_model
    engine.create_capsule_from_prompt_async.assert_any_call(
        prompt="Use the default model.",
        capsule_type="reasoning",
        agent_id="test-agent-full-access",
        parent_capsule=None,
        model=None,
    )

    # 3. Test override model from API call
    override_model = "gpt-4-override"
    payload_override = {
        "prompt": "Use the override model.",
        "model": override_model,
        "agent_id": "test-agent-full-access",
        "capsule_type": "reasoning",
    }
    response_override = await client.post(
        "/reasoning/generate", headers=headers, json=payload_override
    )
    assert response_override.status_code == 201
    data_override = await response_override.get_json()
    assert data_override["model_version"] == override_model
    engine.create_capsule_from_prompt_async.assert_any_call(
        prompt="Use the override model.",
        capsule_type="reasoning",
        agent_id="test-agent-full-access",
        parent_capsule=None,
        model=override_model,
    )
