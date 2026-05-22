"""Export MCP gateway capsule rows as offline-verifiable agent receipts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.agent_receipts.events import (
    DecisionPointEvent,
    RefusalEvent,
    ToolCallCompleted,
)
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle
from src.integrations.mcp.store import CapsuleStore


def export_mcp_receipt_bundle(
    store: CapsuleStore,
    session_id: str,
    signer: Ed25519ReceiptSigner,
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Export one stored MCP session as a public signed receipt bundle."""
    capsule_rows = store.get_session_graph(session_id)
    events = [
        event
        for row in capsule_rows
        if (event := receipt_event_from_capsule_row(row)) is not None
    ]
    bundle = build_signed_receipt_bundle(events, signer)["public"]
    bundle["source"] = {
        "boundary": "mcp_gateway",
        "session_id": session_id,
        "store_path": str(store.db_path),
    }

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")

    return bundle


def receipt_event_from_capsule_row(
    row: dict[str, Any],
) -> DecisionPointEvent | RefusalEvent | ToolCallCompleted | None:
    """Map a stored MCP capsule row into a neutral agent receipt event."""
    capsule_type = row.get("capsule_type")
    timestamp = datetime.fromisoformat(row["timestamp"])
    base_kwargs = {
        "event_id": row["capsule_id"],
        "session_id": row["session_id"],
        "adapter_name": "mcp_gateway",
        "agent_name": "UATP MCP Gateway",
        "timestamp": timestamp,
        "parent_event_hash": None,
        "actor": "assistant",
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }

    if capsule_type == "DECISION_POINT":
        payload = row["payload"]
        selected_action = payload["decision"]["selected_action"]["value"]
        policy = payload.get("policy", {})
        checks_passed = policy.get("checks_passed", {}).get("value") or []
        checks_failed = policy.get("checks_failed", {}).get("value") or []
        return DecisionPointEvent(
            **base_kwargs,
            payload={
                "decision_id": row["capsule_id"],
                "decision_summary": f"MCP policy decision for {selected_action}",
                "selected_action": selected_action,
                "alternatives_considered": payload["decision"]["candidate_actions"][
                    "value"
                ],
                "constraints_applied": [*checks_passed, *checks_failed],
                "timestamp": timestamp,
            },
        )

    if capsule_type == "TOOL_CALL":
        payload = row["payload"]
        execution = payload["execution"]
        tool = payload["tool"]
        output = payload["output"]
        return ToolCallCompleted(
            **base_kwargs,
            payload={
                "call_id": row["capsule_id"],
                "tool_name": tool["name"]["value"],
                "tool_category": "mcp",
                "arguments": {
                    "hash": tool["arguments_hash"]["value"],
                    "preview": tool["arguments_preview"]["value"],
                },
                "result": {
                    "hash": output["content_hash"]["value"],
                    "preview": output["preview"]["value"],
                },
                "started_at": execution["started_at"]["value"],
                "completed_at": execution["ended_at"]["value"],
                "duration_ms": execution["latency_ms"]["value"],
                "status": execution["status"]["value"],
                "error_message": execution["error_message"]["value"],
                "parent_call_id": row.get("parent_id"),
            },
        )

    if capsule_type == "REFUSAL":
        payload = row["payload"]
        policy_checks = payload.get("policy_checks", {})
        violations = policy_checks.get("checks_failed") or []
        return RefusalEvent(
            **base_kwargs,
            payload={
                "refusal_id": row["capsule_id"],
                "parent_decision_id": payload["parent_decision_id"]["value"],
                "attempted_tool": payload["attempted_tool"]["value"],
                "reason": payload["reason"]["value"],
                "violations": violations,
                "policy_checks": policy_checks,
                "policy_version": payload["policy_version"]["value"],
            },
        )

    return None
