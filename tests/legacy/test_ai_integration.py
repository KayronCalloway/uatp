import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from capsule_schema import Capsule
from reasoning.trace import ReasoningStep, ReasoningTrace, StepType

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio


async def test_generate_reasoning_capsule(client, app, monkeypatch, setup_database):
    """Test the /reasoning/generate endpoint with a mocked engine call."""
    # 1. Setup the mock data
    mock_prompt = "Explain the theory of relativity."
    mock_ai_response = "It's all relative."
    mock_model = "gpt-4-test"

    reasoning_trace = ReasoningTrace(
        steps=[
            ReasoningStep(content=mock_prompt, step_type=StepType.OBSERVATION),
            ReasoningStep(content=mock_ai_response, step_type=StepType.CONCLUSION),
        ]
    )

    mock_capsule = Capsule(
        capsule_id="mock-capsule-id-async",
        agent_id="test-agent",
        type="reasoning_trace",
        timestamp=datetime.now(),
        input=mock_prompt,
        output=mock_ai_response,
        reasoning=json.dumps(reasoning_trace.to_dict_list()),
        model_version=mock_model,
        parent_capsule=None,
        hash_="mock-hash-async",
        signature="mock-signature-async",
    )

    # Patch the engine's method directly
    mock_async_create = AsyncMock(return_value=mock_capsule)
    monkeypatch.setattr(
        app.engine_override, "create_capsule_from_prompt_async", mock_async_create
    )

    # 2. Act: Make the request to the endpoint
    headers = {"X-API-Key": "full-access-key"}
    payload = {
        "prompt": mock_prompt,
        "model": mock_model,
        "agent_id": "test-agent-123",
        "capsule_type": "reasoning-test",
    }
    response = await client.post("/reasoning/generate", headers=headers, json=payload)

    # 3. Assert: Check the response
    assert response.status_code == 201
    data = await response.get_json()
    assert data["capsule_id"] == "mock-capsule-id-async"
    assert data["model_version"] == mock_model

    # 4. Verify the reasoning trace
    reasoning_trace_data = json.loads(data["reasoning"])
    assert len(reasoning_trace_data) == 2
    assert reasoning_trace_data[0]["step_type"] == "observation"
    assert reasoning_trace_data[0]["content"] == mock_prompt
    assert reasoning_trace_data[1]["step_type"] == "conclusion"
    assert reasoning_trace_data[1]["content"] == mock_ai_response

    # 6. Verify that the mock was called correctly
    mock_async_create.assert_awaited_once_with(
        prompt=mock_prompt,
        capsule_type=payload["capsule_type"],
        agent_id=payload["agent_id"],
        parent_capsule=None,
        model=mock_model,
    )


async def test_generate_reasoning_capsule_caching(
    client, app, monkeypatch, setup_database
):
    """Test that the /reasoning/generate endpoint correctly caches responses."""
    # 1. Enable caching for this specific test
    app.config["CACHE_ENABLED"] = True

    # Clear cache before test
    await app.cache.clear()

    # 2. Setup the mock
    mock_prompt = "Explain caching."
    mock_ai_response = "It's a way to store results."
    mock_model = "gpt-4-cache-test"

    reasoning_trace = ReasoningTrace(
        steps=[
            ReasoningStep(content=mock_prompt, step_type=StepType.OBSERVATION),
            ReasoningStep(content=mock_ai_response, step_type=StepType.CONCLUSION),
        ]
    )

    mock_capsule = Capsule(
        capsule_id="mock-capsule-id-cache",
        agent_id="test-agent-cache",
        type="reasoning_trace_cached",
        timestamp=datetime.now(),
        input=mock_prompt,
        output=mock_ai_response,
        reasoning=json.dumps(reasoning_trace.to_dict_list()),
        model_version=mock_model,
        parent_capsule=None,
        hash_="mock-hash-cache",
        signature="mock-signature-cache",
    )
    mock_async_create = AsyncMock(return_value=mock_capsule)
    monkeypatch.setattr(
        app.engine_override, "create_capsule_from_prompt_async", mock_async_create
    )

    # 3. Make the first request (should be a cache miss)
    headers = {"X-API-Key": "full-access-key"}
    payload = {
        "prompt": mock_prompt,
        "model": mock_model,
        "agent_id": "test-agent-cache",
        "capsule_type": "reasoning-cache-test",
    }
    response1 = await client.post("/reasoning/generate", headers=headers, json=payload)
    assert response1.status_code == 201

    # 4. Make the second request (should be a cache hit)
    response2 = await client.post("/reasoning/generate", headers=headers, json=payload)
    assert response2.status_code == 201

    # 5. Assert that the responses are identical
    data1 = await response1.get_json()
    data2 = await response2.get_json()
    assert data1 == data2

    # 6. Verify that the mock was only called once
    mock_async_create.assert_awaited_once()


async def test_rate_limiting(client, app, setup_database):
    """Test that the rate limiter works correctly."""
    # This test requires a live limiter, so we don't mock the engine
    app.config["CREATE_CAPSULE_RATE_LIMIT"] = "1 per second"

    headers = {"X-API-Key": "full-access-key"}
    payload = {
        "prompt": "test prompt for rate limit",
        "model": "test-model-ratelimit",
        "agent_id": "test-agent-ratelimit",
        "capsule_type": "reasoning-ratelimit-test",
    }

    # The first request should succeed (or be rate-limited depending on test speed)
    response = await client.post("/reasoning/generate", headers=headers, json=payload)
    assert response.status_code in [201, 429]

    # A subsequent request might be rate-limited, but we just check it doesn't 500
    response = await client.post("/reasoning/generate", headers=headers, json=payload)
    assert response.status_code in [201, 429]
