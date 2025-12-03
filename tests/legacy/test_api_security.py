import pytest


@pytest.mark.asyncio
async def test_api_key_privilege_escalation(client, setup_database):
    """
    Tests that a read-only API key cannot be used for write operations.
    """
    headers = {"X-API-Key": "read-only-key-for-testing"}
    payload = {
        "capsule_type": "reasoning_trace",
        "payload": {
            "input": "Attempting to write with a read-only key.",
            "output": "This should not be allowed.",
        },
    }

    response = await client.post("/capsules", headers=headers, json=payload)

    assert (
        response.status_code == 403
    ), f"Read-only key should be forbidden from performing write operations. Got {response.status_code} instead."
