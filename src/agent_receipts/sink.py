"""Sink boundary for signed agent receipt chains and UATP capsule drafts."""

from __future__ import annotations

from typing import Any, Sequence

from src.agent_receipts.chain import build_receipt_chain, verify_receipt_chain
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
from src.agent_receipts.mappers import (
    map_action_trace_event_to_action_trace_capsule,
    map_decision_point_event_to_decision_point_capsule,
    map_environment_snapshot_event_to_environment_snapshot_capsule,
    map_refusal_event_to_refusal_capsule,
    map_session_events_to_agent_session_capsule,
    map_tool_call_event_to_tool_call_capsule,
)
from src.agent_receipts.signing import Ed25519ReceiptSigner, SignedReceipt

SCHEMA_VERSION = "agent_receipts.v1"


def _chain_report_to_dict(report: Any) -> dict[str, Any]:
    return {
        "valid": report.valid,
        "errors": list(report.errors),
        "event_count": report.event_count,
        "chain_tip_hash": report.chain_tip_hash,
        "chain_root_hash": report.chain_root_hash,
    }


def map_events_to_capsule_drafts(
    events: Sequence[AgentReceiptEvent],
) -> list[dict[str, Any]]:
    """Map supported neutral events into UATP capsule drafts.

    SessionStarted/SessionEnded are collapsed into one AGENT_SESSION draft.
    SessionEnded by itself is not emitted because it lacks the start boundary
    needed by the existing AgentSessionPayload schema.
    """
    drafts: list[dict[str, Any]] = []
    start_event = next(
        (event for event in events if isinstance(event, SessionStarted)), None
    )
    end_event = next(
        (event for event in events if isinstance(event, SessionEnded)), None
    )
    if start_event is not None:
        child_events = [
            event
            for event in events
            if event is not start_event and event is not end_event
        ]
        drafts.append(
            map_session_events_to_agent_session_capsule(
                start_event,
                end_event=end_event,
                child_events=child_events,
            )
        )

    for event in events:
        if isinstance(event, ToolCallCompleted):
            drafts.append(map_tool_call_event_to_tool_call_capsule(event))
        elif isinstance(event, ActionTraceEvent):
            drafts.append(map_action_trace_event_to_action_trace_capsule(event))
        elif isinstance(event, DecisionPointEvent):
            drafts.append(map_decision_point_event_to_decision_point_capsule(event))
        elif isinstance(event, RefusalEvent):
            drafts.append(map_refusal_event_to_refusal_capsule(event))
        elif isinstance(event, EnvironmentSnapshotEvent):
            drafts.append(
                map_environment_snapshot_event_to_environment_snapshot_capsule(event)
            )

    return drafts


def build_signed_receipt_bundle(
    events: Sequence[AgentReceiptEvent], signer: Ed25519ReceiptSigner
) -> dict[str, Any]:
    """Build an offline-verifiable signed receipt bundle from neutral events."""
    chained_events = build_receipt_chain(events)
    chain_report = verify_receipt_chain(chained_events)
    signed_receipts: list[SignedReceipt] = [
        signer.sign_event(event) for event in chained_events
    ]
    public_bundle = {
        "schema_version": SCHEMA_VERSION,
        "chain_report": _chain_report_to_dict(chain_report),
        "signed_receipts": [receipt.to_dict() for receipt in signed_receipts],
        "capsule_drafts": map_events_to_capsule_drafts(chained_events),
    }
    return {
        **public_bundle,
        "public": public_bundle,
        "_signed_receipt_objects": signed_receipts,
    }
