from datetime import datetime, timezone

from src.agent_receipts.events import ActionTraceEvent
from src.agent_receipts.hashing import sha256_digest
from src.agent_receipts.mappers import map_action_trace_event_to_action_trace_capsule


def ts() -> datetime:
    return datetime(2026, 5, 8, 21, 12, 0, tzinfo=timezone.utc)


def action_event(**payload_overrides) -> ActionTraceEvent:
    payload = {
        "action_id": "act_001",
        "tool_call_id": "call_001",
        "action_type": "terminal.command",
        "command": "./.venv/bin/python -m pytest tests/agent_receipts -q",
        "cwd": "/Users/kay/uatp-capsule-engine",
        "exit_code": 0,
        "stdout": "51 passed",
        "stderr": "",
        "duration_ms": 1200,
        "bytes_affected": None,
    }
    payload.update(payload_overrides)
    return ActionTraceEvent(
        event_id="evt_action_001",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(),
        parent_event_hash="sha256:parent",
        actor="assistant",
        payload=payload,
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )


def test_terminal_action_maps_to_action_trace_capsule_draft() -> None:
    event = action_event()

    capsule = map_action_trace_event_to_action_trace_capsule(event)

    assert capsule["capsule_type"] == "action_trace"
    assert capsule["payload_key"] == "action_trace"
    assert capsule["action_trace"] == {
        "action_id": "act_001",
        "session_id": "sess_001",
        "tool_call_id": "call_001",
        "action_type": "terminal.command",
        "command": "./.venv/bin/python -m pytest tests/agent_receipts -q",
        "exit_code": 0,
        "stdout_hash": sha256_digest("51 passed"),
        "stderr_hash": sha256_digest(""),
        "url": None,
        "selector": None,
        "browser_action": None,
        "file_path": None,
        "file_operation": None,
        "bytes_affected": None,
        "executed_at": "2026-05-08T21:12:00+00:00",
        "duration_ms": 1200,
    }
    assert capsule["receipt_metadata"]["command_hash"] == sha256_digest(
        "./.venv/bin/python -m pytest tests/agent_receipts -q"
    )
    assert capsule["receipt_metadata"]["cwd"] == "/Users/kay/uatp-capsule-engine"
    assert capsule["receipt_metadata"]["output_preview"] == {
        "stdout": "51 passed",
        "stderr": "",
    }
    assert capsule["receipt_metadata"]["verification_classification"] == "pytest"
    assert capsule["receipt_metadata"]["parent_event_hash"] == "sha256:parent"


def test_file_action_maps_file_fields_and_content_hashes() -> None:
    event = action_event(
        action_id="act_file",
        action_type="file.write",
        command=None,
        file_path="src/agent_receipts/mappers.py",
        file_operation="write",
        before_content="old",
        after_content="new",
        bytes_affected=3,
    )

    capsule = map_action_trace_event_to_action_trace_capsule(event)

    assert capsule["action_trace"]["file_path"] == "src/agent_receipts/mappers.py"
    assert capsule["action_trace"]["file_operation"] == "write"
    assert capsule["action_trace"]["bytes_affected"] == 3
    assert capsule["receipt_metadata"]["before_hash"] == sha256_digest("old")
    assert capsule["receipt_metadata"]["after_hash"] == sha256_digest("new")


def test_browser_action_maps_browser_fields() -> None:
    event = action_event(
        action_id="act_browser",
        action_type="browser.click",
        command=None,
        url="https://example.com",
        selector="#submit",
        browser_action="click",
    )

    capsule = map_action_trace_event_to_action_trace_capsule(event)

    assert capsule["action_trace"]["url"] == "https://example.com"
    assert capsule["action_trace"]["selector"] == "#submit"
    assert capsule["action_trace"]["browser_action"] == "click"


def test_action_mapper_rejects_missing_action_id() -> None:
    event = action_event(action_id=None)

    try:
        map_action_trace_event_to_action_trace_capsule(event)
    except ValueError as exc:
        assert "action_id" in str(exc)
    else:
        raise AssertionError("expected missing action_id to fail")
