"""Map framework-neutral agent receipt events into UATP capsule drafts."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Sequence

from src.agent_receipts.chain import event_hash
from src.agent_receipts.events import (
    ActionTraceEvent,
    AgentReceiptEvent,
    DecisionPointEvent,
    EnvironmentSnapshotEvent,
    RefusalEvent,
    SessionEnded,
    SessionStarted,
    ToolCallCompleted,
)
from src.agent_receipts.hashing import canonical_json, sha256_digest
from src.agent_receipts.redaction import redact_error_message, redact_value
from src.capsule_schema import (
    ActionTracePayload,
    AgentSessionPayload,
    CapsuleType,
    DecisionPointPayload,
    EnvironmentSnapshotPayload,
    RefusalPayload,
    ToolCallPayload,
)

SHA256_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


def _merge_redaction_summaries(events: Sequence[AgentReceiptEvent]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for event in events:
        for key, value in event.redaction_summary.items():
            if isinstance(value, int) and isinstance(merged.get(key), int):
                merged[key] += value
            elif key not in merged:
                merged[key] = value
            elif merged[key] != value:
                merged[key] = [merged[key], value]
    return merged


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _validate_sha256_digest(value: str, field_name: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must use sha256:<64 lowercase hex> format")
    return value


def _hash_redacted_state(
    raw_value: Any,
    provided_hash: str | None,
    *,
    field_name: str,
    required: bool,
) -> str | None:
    if provided_hash:
        return _validate_sha256_digest(provided_hash, field_name)
    if raw_value is None:
        if required:
            raise ValueError(
                f"{field_name} requires raw state or a provided sha256 digest"
            )
        return None
    return sha256_digest(redact_value(raw_value))


def _truncate_preview(value: Any, preview_limit: int) -> tuple[Any, bool, int]:
    if preview_limit <= 0:
        raise ValueError("preview_limit must be positive")

    rendered = canonical_json(value)
    original_length = len(rendered)
    if original_length <= preview_limit:
        return deepcopy(value), False, original_length

    if isinstance(value, dict) and len(value) == 1:
        key, child = next(iter(value.items()))
        if isinstance(child, str):
            return {key: child[:preview_limit] + "…"}, True, original_length

    return (
        {"preview": rendered[:preview_limit] + "…", "truncated": True},
        True,
        original_length,
    )


def map_session_events_to_agent_session_capsule(
    start_event: SessionStarted,
    *,
    end_event: SessionEnded | None = None,
    child_events: Sequence[AgentReceiptEvent] = (),
) -> dict[str, Any]:
    """Convert session boundary events into an AGENT_SESSION capsule draft.

    The mapper returns a draft dict rather than a signed persisted capsule because
    capsule IDs, signatures, and storage are sink responsibilities. The payload
    itself is validated against the existing UATP 7.4 AgentSessionPayload model.
    """
    if end_event is not None and end_event.session_id != start_event.session_id:
        raise ValueError("session start and end events must have the same session_id")
    for child_event in child_events:
        if child_event.session_id != start_event.session_id:
            raise ValueError("child event session_id must match session start event")

    start_payload = start_event.payload
    end_payload = end_event.payload if end_event is not None else {}

    payload = AgentSessionPayload(
        session_id=start_event.session_id,
        agent_type=start_event.adapter_name,
        agent_version=start_payload.get("agent_version"),
        scheduler_type=start_payload.get("scheduler_type"),
        trigger_message=start_payload.get("trigger_message"),
        trigger_source=start_payload.get("trigger_source"),
        user_id_hash=start_payload.get("user_id_hash"),
        goals=list(start_payload.get("goals", [])),
        started_at=start_event.timestamp,
        completed_at=end_event.timestamp if end_event is not None else None,
        status=end_payload.get("status", "running"),
        tool_call_count=end_payload.get("tool_call_count", 0),
        action_count=end_payload.get("action_count", 0),
        decision_count=end_payload.get("decision_count", 0),
        total_duration_ms=end_payload.get("total_duration_ms"),
        outcome_summary=end_payload.get("outcome_summary"),
        error_message=end_payload.get("error_message"),
    )

    receipt_events: list[AgentReceiptEvent] = [start_event, *child_events]
    if end_event is not None:
        receipt_events.append(end_event)

    agent_session_payload = payload.model_dump(mode="json")
    agent_session_payload["started_at"] = start_event.timestamp.isoformat()
    agent_session_payload["completed_at"] = (
        end_event.timestamp.isoformat() if end_event is not None else None
    )

    return {
        "capsule_type": CapsuleType.AGENT_SESSION.value,
        "payload_key": "agent_session",
        "agent_session": agent_session_payload,
        "receipt_metadata": {
            "adapter_name": start_event.adapter_name,
            "agent_name": start_event.agent_name,
            "platform": start_payload.get("platform"),
            "model_provider": start_payload.get("model_provider"),
            "model": start_payload.get("model"),
            "ended_at": end_event.timestamp.isoformat()
            if end_event is not None
            else None,
            "start_event_id": start_event.event_id,
            "end_event_id": end_event.event_id if end_event is not None else None,
            "start_event_hash": event_hash(start_event),
            "end_event_hash": event_hash(end_event) if end_event is not None else None,
            "child_receipt_refs": [event_hash(event) for event in child_events],
            "redaction_summary": _merge_redaction_summaries(receipt_events),
            "trust_level": start_event.trust_level,
            "metadata": start_payload.get("metadata", {}),
        },
    }


def _verification_classification(command: str | None) -> str | None:
    if not command:
        return None
    if "pytest" in command:
        return "pytest"
    if "ruff" in command:
        return "ruff"
    if "py_compile" in command:
        return "py_compile"
    if "git diff --check" in command:
        return "git_diff_check"
    return None


def map_tool_call_event_to_tool_call_capsule(
    event: ToolCallCompleted,
    *,
    preview_limit: int = 1000,
) -> dict[str, Any]:
    """Convert a completed tool event into a TOOL_CALL capsule draft."""
    payload_data = event.payload
    call_id = payload_data.get("call_id")
    if not call_id:
        raise ValueError("tool call event payload must include call_id")

    arguments = payload_data.get("arguments", {})
    result = payload_data.get("result")
    redacted_arguments, arguments_truncated, arguments_original_length = (
        _truncate_preview(redact_value(arguments), preview_limit)
    )
    redacted_result, result_truncated, result_original_length = (
        (None, False, 0)
        if result is None
        else _truncate_preview(redact_value(result), preview_limit)
    )

    tool_payload = ToolCallPayload(
        call_id=call_id,
        session_id=event.session_id,
        tool_name=payload_data.get("tool_name", "unknown"),
        tool_category=payload_data.get("tool_category", "custom"),
        tool_inputs=redacted_arguments,
        tool_outputs=redacted_result,
        started_at=payload_data.get("started_at", event.timestamp),
        completed_at=payload_data.get("completed_at", event.timestamp),
        duration_ms=payload_data.get("duration_ms"),
        status=payload_data.get("status", "success"),
        error_message=redact_error_message(
            payload_data.get("error_message"), arguments
        ),
        step_index=payload_data.get("step_index", 0),
        parent_call_id=payload_data.get("parent_call_id"),
    )

    tool_call = tool_payload.model_dump(mode="json")
    tool_call["started_at"] = _iso(payload_data.get("started_at", event.timestamp))
    tool_call["completed_at"] = _iso(payload_data.get("completed_at", event.timestamp))

    return {
        "capsule_type": CapsuleType.TOOL_CALL.value,
        "payload_key": "tool_call",
        "tool_call": tool_call,
        "receipt_metadata": {
            "adapter_name": event.adapter_name,
            "agent_name": event.agent_name,
            "event_id": event.event_id,
            "event_hash": event_hash(event),
            "parent_event_hash": event.parent_event_hash,
            "arguments_hash": sha256_digest(arguments),
            "arguments_preview_truncated": arguments_truncated,
            "arguments_preview_original_length": arguments_original_length,
            "result_hash": sha256_digest(result) if result is not None else None,
            "result_preview_truncated": result_truncated,
            "result_preview_original_length": result_original_length,
            "error_type": payload_data.get("error_type"),
            "policy_digest": payload_data.get("policy_digest"),
            "redaction_summary": event.redaction_summary,
            "trust_level": event.trust_level,
        },
    }


def _raw_reasoning_ref(payload_data: dict[str, Any]) -> dict[str, Any] | None:
    ref = payload_data.get("raw_reasoning_ref")
    if ref is None:
        return None
    if not isinstance(ref, dict) or ref.get("sensitive") is not True:
        raise ValueError("raw_reasoning_ref must be marked sensitive")

    allowed_keys = {
        "artifact_id",
        "digest",
        "encrypted",
        "encryption",
        "encryption_key_id",
        "media_type",
        "sensitive",
        "size",
        "storage_policy",
        "uri",
    }
    disallowed_keys = set(ref) - allowed_keys
    if disallowed_keys:
        raise ValueError(
            "raw_reasoning_ref must be reference-only; inline content is not allowed"
        )
    return {**ref, "storage_policy": "local_encrypted_only"}


def map_refusal_event_to_refusal_capsule(event: RefusalEvent) -> dict[str, Any]:
    """Convert a refused action event into a REFUSAL capsule draft."""
    payload_data = event.payload
    refusal_payload = RefusalPayload(
        refused_capsule_id=payload_data.get("refusal_id", event.event_id),
        explanation=payload_data.get("reason", "Action refused by policy"),
        violations=payload_data.get("violations", []),
    )
    return {
        "capsule_type": CapsuleType.REFUSAL.value,
        "payload_key": "refusal",
        "refusal": refusal_payload.model_dump(mode="json"),
        "receipt_metadata": {
            "adapter_name": event.adapter_name,
            "agent_name": event.agent_name,
            "event_id": event.event_id,
            "event_hash": event_hash(event),
            "parent_event_hash": event.parent_event_hash,
            "attempted_tool": payload_data.get("attempted_tool"),
            "parent_decision_id": payload_data.get("parent_decision_id"),
            "policy_version": payload_data.get("policy_version"),
            "policy_checks": payload_data.get("policy_checks", {}),
            "redaction_summary": event.redaction_summary,
            "trust_level": event.trust_level,
        },
    }


def map_decision_point_event_to_decision_point_capsule(
    event: DecisionPointEvent,
    *,
    include_raw_reasoning_ref: bool = False,
) -> dict[str, Any]:
    """Convert an audit-safe decision event into a DECISION_POINT capsule draft."""
    payload_data = event.payload
    decision_id = payload_data.get("decision_id")
    if not decision_id:
        raise ValueError("decision point event payload must include decision_id")
    if not payload_data.get("decision_summary"):
        raise ValueError("decision point event payload must include decision_summary")
    if not payload_data.get("selected_action"):
        raise ValueError("decision point event payload must include selected_action")

    decision_payload = DecisionPointPayload(
        decision_id=decision_id,
        session_id=event.session_id,
        step_index=payload_data.get("step_index", 0),
        reasoning=payload_data.get("decision_summary", ""),
        alternatives_considered=payload_data.get("alternatives_considered", []),
        selected_action=payload_data.get("selected_action", ""),
        confidence=payload_data.get("confidence"),
        context_summary=payload_data.get("context_summary"),
        constraints_applied=payload_data.get("constraints_applied", []),
        timestamp=payload_data.get("timestamp", event.timestamp),
    )

    decision_point = decision_payload.model_dump(mode="json")
    decision_point["timestamp"] = decision_payload.timestamp.isoformat()
    metadata = {
        "adapter_name": event.adapter_name,
        "agent_name": event.agent_name,
        "event_id": event.event_id,
        "event_hash": event_hash(event),
        "parent_event_hash": event.parent_event_hash,
        "uncertainty_factors": payload_data.get("uncertainty_factors", []),
        "evidence_refs": payload_data.get("evidence_refs", []),
        "raw_reasoning_included": include_raw_reasoning_ref,
        "decision_payload_hash": sha256_digest(event.to_dict()["payload"]),
        "redaction_summary": event.redaction_summary,
        "trust_level": event.trust_level,
    }
    if include_raw_reasoning_ref:
        metadata["raw_reasoning_ref"] = _raw_reasoning_ref(payload_data)

    return {
        "capsule_type": CapsuleType.DECISION_POINT.value,
        "payload_key": "decision_point",
        "decision_point": decision_point,
        "receipt_metadata": metadata,
    }


def _validate_loaded_skills(
    loaded_skills: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for skill in loaded_skills:
        if not skill.get("content_hash"):
            raise ValueError("loaded skill entries must include content_hash")
    return loaded_skills


def map_environment_snapshot_event_to_environment_snapshot_capsule(
    event: EnvironmentSnapshotEvent,
) -> dict[str, Any]:
    """Convert runtime state into an ENVIRONMENT_SNAPSHOT capsule draft."""
    payload_data = event.payload
    snapshot_id = payload_data.get("snapshot_id")
    if not snapshot_id:
        raise ValueError("environment snapshot event payload must include snapshot_id")

    env_payload = EnvironmentSnapshotPayload(
        snapshot_id=snapshot_id,
        session_id=event.session_id,
        working_directory=payload_data.get("working_directory", ""),
        env_vars_hash=_hash_redacted_state(
            payload_data.get("env_vars"),
            payload_data.get("env_vars_hash"),
            field_name="env_vars_hash",
            required=True,
        ),
        git_branch=payload_data.get("git_branch"),
        git_commit_hash=payload_data.get("git_commit_hash"),
        git_dirty=payload_data.get("git_dirty"),
        open_files=payload_data.get("open_files", []),
        system_load=payload_data.get("system_load"),
        memory_available_gb=payload_data.get("memory_available_gb"),
        timestamp=payload_data.get("timestamp", event.timestamp),
    )

    environment_snapshot = env_payload.model_dump(mode="json")
    environment_snapshot["timestamp"] = env_payload.timestamp.isoformat()

    return {
        "capsule_type": CapsuleType.ENVIRONMENT_SNAPSHOT.value,
        "payload_key": "environment_snapshot",
        "environment_snapshot": environment_snapshot,
        "receipt_metadata": {
            "adapter_name": event.adapter_name,
            "agent_name": event.agent_name,
            "event_id": event.event_id,
            "event_hash": event_hash(event),
            "parent_event_hash": event.parent_event_hash,
            "agent_framework": payload_data.get("agent_framework"),
            "adapter": payload_data.get("adapter"),
            "model_provider": payload_data.get("model_provider"),
            "model": payload_data.get("model"),
            "enabled_tools": payload_data.get("enabled_tools", []),
            "enabled_toolsets": payload_data.get("enabled_toolsets", []),
            "loaded_skills": _validate_loaded_skills(
                payload_data.get("loaded_skills", [])
            ),
            "memory_provider_state_hash": _hash_redacted_state(
                payload_data.get("memory_provider_state"),
                payload_data.get("memory_provider_state_hash"),
                field_name="memory_provider_state_hash",
                required=False,
            ),
            "mcp_servers": redact_value(payload_data.get("mcp_servers", [])),
            "platform": payload_data.get("platform"),
            "gateway_source": payload_data.get("gateway_source"),
            "terminal_backend": payload_data.get("terminal_backend"),
            "config_hash": _hash_redacted_state(
                payload_data.get("config"),
                payload_data.get("config_hash"),
                field_name="config_hash",
                required=False,
            ),
            "redaction_summary": event.redaction_summary,
            "trust_level": event.trust_level,
        },
    }


def map_action_trace_event_to_action_trace_capsule(
    event: ActionTraceEvent,
    *,
    preview_limit: int = 1000,
) -> dict[str, Any]:
    """Convert a side-effect event into an ACTION_TRACE capsule draft."""
    payload_data = event.payload
    action_id = payload_data.get("action_id")
    if not action_id:
        raise ValueError("action trace event payload must include action_id")

    stdout = payload_data.get("stdout", "")
    stderr = payload_data.get("stderr", "")
    command = payload_data.get("command")
    output_preview, output_truncated, output_original_length = _truncate_preview(
        {"stdout": stdout, "stderr": stderr}, preview_limit
    )

    action_payload = ActionTracePayload(
        action_id=action_id,
        session_id=event.session_id,
        tool_call_id=payload_data.get("tool_call_id"),
        action_type=payload_data.get("action_type", "custom"),
        command=command,
        exit_code=payload_data.get("exit_code"),
        stdout_hash=(
            payload_data.get("stdout_hash")
            or (sha256_digest(stdout) if stdout is not None else None)
        ),
        stderr_hash=(
            payload_data.get("stderr_hash")
            or (sha256_digest(stderr) if stderr is not None else None)
        ),
        url=payload_data.get("url"),
        selector=payload_data.get("selector"),
        browser_action=payload_data.get("browser_action"),
        file_path=payload_data.get("file_path"),
        file_operation=payload_data.get("file_operation"),
        bytes_affected=payload_data.get("bytes_affected"),
        executed_at=payload_data.get("executed_at", event.timestamp),
        duration_ms=payload_data.get("duration_ms", 0),
    )

    action_trace = action_payload.model_dump(mode="json")
    action_trace["executed_at"] = _iso(payload_data.get("executed_at", event.timestamp))

    return {
        "capsule_type": CapsuleType.ACTION_TRACE.value,
        "payload_key": "action_trace",
        "action_trace": action_trace,
        "receipt_metadata": {
            "adapter_name": event.adapter_name,
            "agent_name": event.agent_name,
            "event_id": event.event_id,
            "event_hash": event_hash(event),
            "parent_event_hash": event.parent_event_hash,
            "command_hash": sha256_digest(command) if command else None,
            "cwd": payload_data.get("cwd"),
            "before_hash": (
                payload_data.get("before_hash")
                or (
                    sha256_digest(payload_data["before_content"])
                    if "before_content" in payload_data
                    else None
                )
            ),
            "after_hash": (
                payload_data.get("after_hash")
                or (
                    sha256_digest(payload_data["after_content"])
                    if "after_content" in payload_data
                    else None
                )
            ),
            "output_preview": output_preview,
            "output_preview_truncated": output_truncated,
            "output_preview_original_length": output_original_length,
            "verification_classification": _verification_classification(command),
            "redaction_summary": event.redaction_summary,
            "trust_level": event.trust_level,
        },
    }
