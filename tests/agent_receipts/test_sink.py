"""Signed receipt sink tests for neutral event chains."""

from __future__ import annotations

from datetime import datetime, timezone

from src.agent_receipts.events import SessionEnded, SessionStarted, ToolCallCompleted
from src.agent_receipts.signing import Ed25519ReceiptSigner, verify_signed_receipt_chain
from src.agent_receipts.sink import build_signed_receipt_bundle


def event_kwargs(event_id: str, payload: dict) -> dict:
    return {
        "event_id": event_id,
        "session_id": "sess_sink",
        "adapter_name": "hermes",
        "agent_name": "Hermes",
        "timestamp": datetime(2026, 5, 8, 22, 0, tzinfo=timezone.utc),
        "parent_event_hash": None,
        "actor": "assistant",
        "payload": payload,
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }


def test_build_signed_receipt_bundle_chains_signs_and_maps_capsule_drafts() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="sink_test")
    events = [
        SessionStarted(
            **event_kwargs(
                "evt_start",
                {
                    "agent_version": "1.0",
                    "platform": "hermes-cli",
                    "model": "claude-sonnet-4",
                    "goals": ["capture provenance"],
                },
            )
        ),
        ToolCallCompleted(
            **event_kwargs(
                "evt_tool",
                {
                    "call_id": "call_1",
                    "tool_name": "terminal",
                    "tool_category": "command",
                    "arguments": {"command": "pytest tests/agent_receipts -q"},
                    "result": {"exit_code": 0, "stdout": "84 passed"},
                    "status": "success",
                },
            )
        ),
        SessionEnded(
            **event_kwargs(
                "evt_end",
                {
                    "status": "completed",
                    "tool_call_count": 1,
                    "action_count": 1,
                    "decision_count": 0,
                    "outcome_summary": "Captured provenance.",
                },
            )
        ),
    ]

    bundle = build_signed_receipt_bundle(events, signer)

    assert bundle["schema_version"] == "agent_receipts.v1"
    assert bundle["chain_report"]["valid"] is True
    assert bundle["chain_report"]["event_count"] == 3
    assert len(bundle["signed_receipts"]) == 3
    assert len(bundle["capsule_drafts"]) == 2
    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "agent_session",
        "tool_call",
    ]
    assert verify_signed_receipt_chain(bundle["_signed_receipt_objects"]).valid is True


def test_build_signed_receipt_bundle_redacts_private_object_handles_from_public_dict() -> (
    None
):
    signer = Ed25519ReceiptSigner.generate(signer_id="sink_test")
    event = SessionStarted(
        **event_kwargs("evt_start", {"platform": "hermes-cli", "goals": []})
    )

    bundle = build_signed_receipt_bundle([event], signer)

    assert "_signed_receipt_objects" not in bundle["public"]
    assert bundle["public"]["signed_receipts"] == bundle["signed_receipts"]
