from datetime import datetime, timezone

import pytest

from src.agent_receipts.events import ToolCallCompleted
from src.agent_receipts.hashing import canonical_json, sha256_digest
from src.agent_receipts.mappers import map_tool_call_event_to_tool_call_capsule


def ts(second: int) -> datetime:
    return datetime(2026, 5, 8, 21, 11, second, tzinfo=timezone.utc)


def tool_event(**payload_overrides) -> ToolCallCompleted:
    payload = {
        "call_id": "call_001",
        "tool_name": "terminal",
        "tool_category": "terminal",
        "arguments": {"command": "pytest -q", "api_token": "secret-value"},
        "result": {"exit_code": 0, "stdout": "ok"},
        "started_at": ts(0),
        "completed_at": ts(2),
        "duration_ms": 2000,
        "status": "success",
        "step_index": 4,
        "parent_call_id": None,
        "policy_digest": "sha256:policy",
    }
    payload.update(payload_overrides)
    return ToolCallCompleted(
        event_id="evt_tool_done",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(2),
        parent_event_hash="sha256:parent",
        actor="assistant",
        payload=payload,
        redaction_summary={"secrets_removed": 1},
        trust_level="local",
    )


def test_successful_tool_event_maps_to_tool_call_capsule_draft() -> None:
    event = tool_event()

    capsule = map_tool_call_event_to_tool_call_capsule(event)

    assert capsule["capsule_type"] == "tool_call"
    assert capsule["payload_key"] == "tool_call"
    assert capsule["tool_call"] == {
        "call_id": "call_001",
        "session_id": "sess_001",
        "tool_name": "terminal",
        "tool_category": "terminal",
        "tool_inputs": {"command": "pytest -q", "api_token": "[REDACTED]"},
        "tool_outputs": {"exit_code": 0, "stdout": "ok"},
        "started_at": "2026-05-08T21:11:00+00:00",
        "completed_at": "2026-05-08T21:11:02+00:00",
        "duration_ms": 2000,
        "status": "success",
        "error_message": None,
        "step_index": 4,
        "parent_call_id": None,
    }
    assert capsule["receipt_metadata"]["event_hash"]
    assert capsule["receipt_metadata"]["parent_event_hash"] == "sha256:parent"
    assert capsule["receipt_metadata"]["arguments_hash"] == sha256_digest(
        {"command": "pytest -q", "api_token": "secret-value"}
    )
    assert capsule["receipt_metadata"]["result_hash"] == sha256_digest(
        {"exit_code": 0, "stdout": "ok"}
    )
    assert capsule["receipt_metadata"]["policy_digest"] == "sha256:policy"
    assert capsule["receipt_metadata"]["redaction_summary"] == {"secrets_removed": 1}


def test_failed_tool_event_maps_error_type_and_redacted_message() -> None:
    event = tool_event(
        status="error",
        result=None,
        error_type="RuntimeError",
        error_message="token secret-value failed",
    )

    capsule = map_tool_call_event_to_tool_call_capsule(event)

    assert capsule["tool_call"]["status"] == "error"
    assert capsule["tool_call"]["tool_outputs"] is None
    assert capsule["tool_call"]["error_message"] == "token [REDACTED] failed"
    assert capsule["receipt_metadata"]["error_type"] == "RuntimeError"
    assert capsule["receipt_metadata"]["result_hash"] is None


def test_tool_result_preview_truncation_records_original_length() -> None:
    result = {"stdout": "x" * 1300}
    event = tool_event(result=result)

    capsule = map_tool_call_event_to_tool_call_capsule(event, preview_limit=20)

    assert capsule["tool_call"]["tool_outputs"] == {"stdout": "xxxxxxxxxxxxxxxxxxxx…"}
    assert capsule["receipt_metadata"]["result_preview_truncated"] is True
    assert capsule["receipt_metadata"]["result_preview_original_length"] == len(
        canonical_json(result)
    )


def test_multi_key_result_truncates_to_schema_valid_preview_dict() -> None:
    result = {"stdout": "x" * 1300, "stderr": "y" * 1300}
    event = tool_event(result=result)

    capsule = map_tool_call_event_to_tool_call_capsule(event, preview_limit=20)

    assert capsule["tool_call"]["tool_outputs"] == {
        "preview": '{"stderr":"yyyyyyyyy…',
        "truncated": True,
    }
    assert capsule["receipt_metadata"]["result_hash"] == sha256_digest(result)
    assert capsule["receipt_metadata"]["result_preview_original_length"] == len(
        canonical_json(result)
    )


def test_large_arguments_are_redacted_and_truncated_with_metadata() -> None:
    arguments = {"command": "x" * 1300, "password": "super-secret"}
    event = tool_event(arguments=arguments)

    capsule = map_tool_call_event_to_tool_call_capsule(event, preview_limit=20)

    assert capsule["tool_call"]["tool_inputs"] == {
        "preview": '{"command":"xxxxxxxx…',
        "truncated": True,
    }
    assert capsule["receipt_metadata"]["arguments_hash"] == sha256_digest(arguments)
    assert capsule["receipt_metadata"]["arguments_preview_truncated"] is True
    assert capsule["receipt_metadata"]["arguments_preview_original_length"] == len(
        canonical_json({"command": "x" * 1300, "password": "[REDACTED]"})
    )


def test_tool_mapper_rejects_missing_call_id() -> None:
    event = tool_event(call_id=None)

    with pytest.raises(ValueError, match="call_id"):
        map_tool_call_event_to_tool_call_capsule(event)


def test_tool_mapper_rejects_non_positive_preview_limit() -> None:
    with pytest.raises(ValueError, match="preview_limit"):
        map_tool_call_event_to_tool_call_capsule(tool_event(), preview_limit=0)
