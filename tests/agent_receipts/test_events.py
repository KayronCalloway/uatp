from datetime import datetime, timezone

import pytest

from src.agent_receipts.events import (
    ActionTraceEvent,
    AgentIdentity,
    ArtifactRef,
    DecisionPointEvent,
    EnvironmentSnapshotEvent,
    LLMCallCompleted,
    LLMCallStarted,
    MemoryWriteEvent,
    ReceiptContext,
    SessionEnded,
    SessionStarted,
    SkillMutationEvent,
    ToolCallCompleted,
    ToolCallStarted,
    UserFeedbackEvent,
)


def fixed_timestamp() -> datetime:
    return datetime(2026, 5, 8, 21, 10, 0, tzinfo=timezone.utc)


def common_fields() -> dict:
    return {
        "event_id": "evt_001",
        "session_id": "sess_001",
        "adapter_name": "hermes",
        "agent_name": "Hermes Agent",
        "timestamp": fixed_timestamp(),
        "parent_event_hash": None,
        "actor": "assistant",
        "payload": {"task": "capture"},
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }


def test_session_started_serializes_deterministically_with_expected_keys() -> None:
    event = SessionStarted(**common_fields())

    assert event.to_dict() == {
        "event_id": "evt_001",
        "event_type": "session.started",
        "session_id": "sess_001",
        "adapter_name": "hermes",
        "agent_name": "Hermes Agent",
        "timestamp": "2026-05-08T21:10:00+00:00",
        "parent_event_hash": None,
        "actor": "assistant",
        "payload": {"task": "capture"},
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }


@pytest.mark.parametrize(
    ("event_cls", "expected_event_type"),
    [
        (SessionStarted, "session.started"),
        (SessionEnded, "session.ended"),
        (LLMCallStarted, "llm_call.started"),
        (LLMCallCompleted, "llm_call.completed"),
        (ToolCallStarted, "tool_call.started"),
        (ToolCallCompleted, "tool_call.completed"),
        (ActionTraceEvent, "action.trace"),
        (DecisionPointEvent, "decision.point"),
        (EnvironmentSnapshotEvent, "environment.snapshot"),
        (MemoryWriteEvent, "memory.write"),
        (SkillMutationEvent, "skill.mutation"),
        (UserFeedbackEvent, "user.feedback"),
    ],
)
def test_event_type_is_explicit_for_every_event_subclass(
    event_cls, expected_event_type
) -> None:
    assert event_cls(**common_fields()).event_type == expected_event_type


def test_parent_event_hash_serializes_none_or_string() -> None:
    no_parent = SessionStarted(**common_fields()).to_dict()
    with_parent_fields = common_fields()
    with_parent_fields["parent_event_hash"] = "abc123"
    with_parent = SessionStarted(**with_parent_fields).to_dict()

    assert no_parent["parent_event_hash"] is None
    assert with_parent["parent_event_hash"] == "abc123"


def test_nested_payload_serializes_datetimes_and_sorts_dict_keys() -> None:
    fields = common_fields()
    fields["payload"] = {
        "zeta": [ArtifactRef("sha256:def456", "artifacts/a.txt", 12, "text/plain", {})],
        "alpha": {"when": fixed_timestamp()},
    }

    serialized = SessionStarted(**fields).to_dict()

    assert list(serialized["payload"].keys()) == ["alpha", "zeta"]
    assert serialized["payload"]["alpha"]["when"] == "2026-05-08T21:10:00+00:00"
    assert serialized["payload"]["zeta"] == [
        {
            "digest": "sha256:def456",
            "path": "artifacts/a.txt",
            "size": 12,
            "media_type": "text/plain",
            "redaction": {},
        }
    ]


def test_missing_required_common_fields_fail_construction() -> None:
    fields = common_fields()
    del fields["session_id"]

    with pytest.raises(TypeError):
        SessionStarted(**fields)


def test_artifact_ref_serializes_digest_path_size_media_type_and_redaction_metadata() -> (
    None
):
    artifact = ArtifactRef(
        digest="sha256:abc123",
        path="artifacts/tool-output.json",
        size=42,
        media_type="application/json",
        redaction={"status": "redacted", "fields": ["token"]},
    )

    assert artifact.to_dict() == {
        "digest": "sha256:abc123",
        "path": "artifacts/tool-output.json",
        "size": 42,
        "media_type": "application/json",
        "redaction": {"status": "redacted", "fields": ["token"]},
    }


def test_receipt_context_serializes_agent_identity_and_defaults() -> None:
    context = ReceiptContext(
        session_id="sess_001",
        adapter_name="hermes",
        agent=AgentIdentity(name="Hermes Agent", version="1.0", vendor="Nous"),
    )

    assert context.to_dict() == {
        "session_id": "sess_001",
        "adapter_name": "hermes",
        "agent": {"name": "Hermes Agent", "version": "1.0", "vendor": "Nous"},
        "actor": "assistant",
        "trust_level": "local",
    }
