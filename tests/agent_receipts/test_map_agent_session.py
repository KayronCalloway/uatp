from datetime import datetime, timezone

import pytest

from src.agent_receipts.chain import event_hash
from src.agent_receipts.events import SessionEnded, SessionStarted, ToolCallCompleted
from src.agent_receipts.mappers import map_session_events_to_agent_session_capsule


def ts(second: int) -> datetime:
    return datetime(2026, 5, 8, 21, 10, second, tzinfo=timezone.utc)


def session_start() -> SessionStarted:
    return SessionStarted(
        event_id="evt_session_start",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(0),
        parent_event_hash=None,
        actor="assistant",
        payload={
            "platform": "cli",
            "model_provider": "anthropic",
            "model": "claude-sonnet-4",
            "trigger_message": "continue",
            "trigger_source": "cli",
            "goals": ["implement agent receipts"],
            "scheduler_type": "on_demand",
            "metadata": {"topic": "uatp-hermes"},
        },
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )


def session_end() -> SessionEnded:
    return SessionEnded(
        event_id="evt_session_end",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(5),
        parent_event_hash="sha256:previous",
        actor="assistant",
        payload={
            "status": "completed",
            "outcome_summary": "receipt layer advanced",
            "tool_call_count": 1,
            "action_count": 2,
            "decision_count": 3,
            "total_duration_ms": 5000,
        },
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )


def child_tool_event() -> ToolCallCompleted:
    return ToolCallCompleted(
        event_id="evt_tool_001",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(2),
        parent_event_hash="sha256:parent",
        actor="assistant",
        payload={"tool_name": "terminal", "status": "success"},
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )


def test_session_start_and_end_map_to_agent_session_capsule_draft() -> None:
    start = session_start()
    end = session_end()

    capsule = map_session_events_to_agent_session_capsule(
        start,
        end_event=end,
        child_events=[child_tool_event()],
    )

    assert capsule["capsule_type"] == "agent_session"
    assert capsule["payload_key"] == "agent_session"
    assert capsule["agent_session"] == {
        "session_id": "sess_001",
        "agent_type": "hermes",
        "agent_version": None,
        "scheduler_type": "on_demand",
        "trigger_message": "continue",
        "trigger_source": "cli",
        "user_id_hash": None,
        "goals": ["implement agent receipts"],
        "started_at": "2026-05-08T21:10:00+00:00",
        "completed_at": "2026-05-08T21:10:05+00:00",
        "status": "completed",
        "tool_call_count": 1,
        "action_count": 2,
        "decision_count": 3,
        "total_duration_ms": 5000,
        "outcome_summary": "receipt layer advanced",
        "error_message": None,
    }
    assert capsule["receipt_metadata"]["adapter_name"] == "hermes"
    assert capsule["receipt_metadata"]["agent_name"] == "Hermes Agent"
    assert capsule["receipt_metadata"]["platform"] == "cli"
    assert capsule["receipt_metadata"]["model_provider"] == "anthropic"
    assert capsule["receipt_metadata"]["model"] == "claude-sonnet-4"
    assert capsule["receipt_metadata"]["ended_at"] == "2026-05-08T21:10:05+00:00"
    assert capsule["receipt_metadata"]["start_event_hash"] == event_hash(start)
    assert capsule["receipt_metadata"]["end_event_hash"] == event_hash(end)
    assert capsule["receipt_metadata"]["child_receipt_refs"] == [
        event_hash(child_tool_event())
    ]
    assert capsule["receipt_metadata"]["redaction_summary"] == {"secrets_removed": 0}
    assert capsule["receipt_metadata"]["trust_level"] == "local"


def test_running_session_uses_start_event_without_end_event() -> None:
    capsule = map_session_events_to_agent_session_capsule(session_start())

    assert capsule["agent_session"]["completed_at"] is None
    assert capsule["agent_session"]["status"] == "running"
    assert capsule["receipt_metadata"]["end_event_hash"] is None


def test_session_mapper_rejects_mismatched_session_ids() -> None:
    start = session_start()
    end_fields = session_end().__dict__ | {"session_id": "different"}
    end = SessionEnded(**end_fields)

    with pytest.raises(ValueError, match="same session_id"):
        map_session_events_to_agent_session_capsule(start, end_event=end)


def test_session_mapper_rejects_child_events_from_other_sessions() -> None:
    child_fields = child_tool_event().__dict__ | {"session_id": "different"}
    child = ToolCallCompleted(**child_fields)

    with pytest.raises(ValueError, match="child event"):
        map_session_events_to_agent_session_capsule(
            session_start(), child_events=[child]
        )
