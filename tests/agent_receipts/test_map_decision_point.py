from datetime import datetime, timedelta, timezone

import pytest

from src.agent_receipts.events import DecisionPointEvent
from src.agent_receipts.hashing import sha256_digest
from src.agent_receipts.mappers import (
    map_decision_point_event_to_decision_point_capsule,
)


def ts() -> datetime:
    return datetime(2026, 5, 8, 21, 13, 0, tzinfo=timezone.utc)


def decision_event(**payload_overrides) -> DecisionPointEvent:
    payload = {
        "decision_id": "dec_001",
        "step_index": 7,
        "decision_summary": "Use UATP 7.4 capsule mapper instead of a Hermes-only schema.",
        "alternatives_considered": ["Hermes-only table", "post-hoc transcript archive"],
        "selected_action": "map neutral events to existing capsule payloads",
        "confidence": 0.91,
        "uncertainty_factors": ["existing schema has limited explicit receipt fields"],
        "evidence_refs": ["sha256:evidence1", "sha256:evidence2"],
        "constraints_applied": ["no raw chain-of-thought by default"],
        "context_summary": "Task 2.4 requires audit-safe reasoning.",
        "raw_reasoning_ref": {"digest": "sha256:raw", "sensitive": True},
    }
    payload.update(payload_overrides)
    return DecisionPointEvent(
        event_id="evt_decision_001",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=ts(),
        parent_event_hash="sha256:parent",
        actor="assistant",
        payload=payload,
        redaction_summary={"raw_reasoning_removed": 1},
        trust_level="local",
    )


def test_decision_point_maps_audit_summary_without_raw_reasoning_by_default() -> None:
    event = decision_event()

    capsule = map_decision_point_event_to_decision_point_capsule(event)

    assert capsule["capsule_type"] == "decision_point"
    assert capsule["payload_key"] == "decision_point"
    assert capsule["decision_point"] == {
        "decision_id": "dec_001",
        "session_id": "sess_001",
        "step_index": 7,
        "reasoning": "Use UATP 7.4 capsule mapper instead of a Hermes-only schema.",
        "alternatives_considered": ["Hermes-only table", "post-hoc transcript archive"],
        "selected_action": "map neutral events to existing capsule payloads",
        "confidence": 0.91,
        "context_summary": "Task 2.4 requires audit-safe reasoning.",
        "constraints_applied": ["no raw chain-of-thought by default"],
        "timestamp": "2026-05-08T21:13:00+00:00",
    }
    assert capsule["receipt_metadata"]["event_hash"]
    assert capsule["receipt_metadata"]["parent_event_hash"] == "sha256:parent"
    assert capsule["receipt_metadata"]["uncertainty_factors"] == [
        "existing schema has limited explicit receipt fields"
    ]
    assert capsule["receipt_metadata"]["evidence_refs"] == [
        "sha256:evidence1",
        "sha256:evidence2",
    ]
    assert capsule["receipt_metadata"]["raw_reasoning_included"] is False
    assert "raw_reasoning_ref" not in capsule["receipt_metadata"]
    assert capsule["receipt_metadata"]["decision_payload_hash"] == sha256_digest(
        event.payload
    )


def test_decision_point_includes_sensitive_raw_reasoning_ref_only_when_enabled() -> (
    None
):
    event = decision_event()

    capsule = map_decision_point_event_to_decision_point_capsule(
        event,
        include_raw_reasoning_ref=True,
    )

    assert capsule["receipt_metadata"]["raw_reasoning_included"] is True
    assert capsule["receipt_metadata"]["raw_reasoning_ref"] == {
        "digest": "sha256:raw",
        "sensitive": True,
        "storage_policy": "local_encrypted_only",
    }


def test_decision_point_rejects_raw_reasoning_ref_not_marked_sensitive() -> None:
    event = decision_event(raw_reasoning_ref={"digest": "sha256:raw"})

    with pytest.raises(ValueError, match="sensitive"):
        map_decision_point_event_to_decision_point_capsule(
            event,
            include_raw_reasoning_ref=True,
        )


def test_decision_point_rejects_inline_raw_reasoning_content() -> None:
    event = decision_event(
        raw_reasoning_ref={
            "digest": "sha256:raw",
            "sensitive": True,
            "content": "raw chain",
        }
    )

    with pytest.raises(ValueError, match="reference-only"):
        map_decision_point_event_to_decision_point_capsule(
            event,
            include_raw_reasoning_ref=True,
        )


def test_decision_point_payload_hash_accepts_datetime_payload_timestamp() -> None:
    event = decision_event(
        timestamp=datetime(2026, 5, 8, 16, 13, tzinfo=timezone(timedelta(hours=-5)))
    )

    capsule = map_decision_point_event_to_decision_point_capsule(event)

    assert capsule["decision_point"]["timestamp"] == "2026-05-08T21:13:00+00:00"
    assert capsule["receipt_metadata"]["decision_payload_hash"] == sha256_digest(
        event.to_dict()["payload"]
    )


def test_decision_point_rejects_missing_decision_summary() -> None:
    event = decision_event(decision_summary="")

    with pytest.raises(ValueError, match="decision_summary"):
        map_decision_point_event_to_decision_point_capsule(event)


def test_decision_point_rejects_missing_selected_action() -> None:
    event = decision_event(selected_action="")

    with pytest.raises(ValueError, match="selected_action"):
        map_decision_point_event_to_decision_point_capsule(event)


def test_decision_point_rejects_missing_decision_id() -> None:
    event = decision_event(decision_id=None)

    with pytest.raises(ValueError, match="decision_id"):
        map_decision_point_event_to_decision_point_capsule(event)
