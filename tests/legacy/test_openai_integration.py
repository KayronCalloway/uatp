import json
from unittest.mock import AsyncMock

import pytest
from api.server import create_app


@pytest.mark.asyncio
async def test_generate_ai_text_endpoint(setup_database, monkeypatch):
    """Test the /ai/generate endpoint using an isolated app instance."""
    # 1. Setup
    from engine.capsule_engine import CapsuleEngine

    from tests.mock_openai_client import MockOpenAIClient

    api_keys = {
        "full-access-key": {
            "roles": ["read", "write", "admin", "ai"],
            "agent_id": "test-agent-full-access",
        }
    }
    monkeypatch.setenv("UATP_API_KEYS", json.dumps(api_keys))
    monkeypatch.setenv("UATP_AGENT_ID", "test-agent")
    monkeypatch.setenv("UATP_SIGNING_KEY", "deadbeef" * 8)  # 32-byte hex key

    mock_openai_client = MockOpenAIClient(response_text="This is a mock AI response.")
    # Spy on the method to track calls
    mock_openai_client.get_completion_async = AsyncMock(
        return_value="This is a mock AI response."
    )
    mock_engine = CapsuleEngine(db=setup_database, openai_client=mock_openai_client)
    app = create_app(engine_override=mock_engine)

    # 3. Call the endpoint
    client = app.test_client()
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "full-access-key",
    }
    response = await client.post(
        "/ai/generate", headers=headers, json={"prompt": "test prompt"}
    )

    # 4. Assert the response
    assert response.status_code == 200
    json_data = await response.get_json()
    assert json_data["status"] == "success"
    assert json_data["generated_text"] == "This is a mock AI response."

    # 5. Verify that the underlying client method was called
    # 5. Verify that the underlying client method was called
    mock_openai_client.get_completion_async.assert_called_once()
    call_args, call_kwargs = mock_openai_client.get_completion_async.call_args
    assert call_kwargs.get("prompt") == "test prompt"
    assert call_kwargs.get("model") == "gpt-3.5-turbo"
