"""Ed25519 signing tests for agent receipt chains."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from src.agent_receipts.chain import build_receipt_chain, event_hash
from src.agent_receipts.events import ActionTraceEvent
from src.agent_receipts.signing import (
    Ed25519ReceiptSigner,
    sign_receipt_chain,
    verify_signed_receipt,
    verify_signed_receipt_chain,
)


def sample_events() -> list[ActionTraceEvent]:
    base = {
        "session_id": "sess_signing",
        "adapter_name": "hermes",
        "agent_name": "Hermes",
        "timestamp": datetime(2026, 5, 8, 22, 0, tzinfo=timezone.utc),
        "parent_event_hash": None,
        "actor": "assistant",
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }
    return [
        ActionTraceEvent(event_id="evt_001", payload={"action_id": "act_1"}, **base),
        ActionTraceEvent(event_id="evt_002", payload={"action_id": "act_2"}, **base),
    ]


def test_signer_signs_event_hash_and_verifies_public_key_hex() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="test_signer")
    event = build_receipt_chain(sample_events())[0]

    signed = signer.sign_event(event)

    assert signed.signer_id == "test_signer"
    assert signed.event_hash == event_hash(event)
    assert len(signed.signature) == 128
    assert len(signed.public_key) == 64
    assert verify_signed_receipt(signed).valid is True
    assert verify_signed_receipt(signed).errors == ()


def test_tampered_signed_event_fails_signature_verification() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="test_signer")
    signed = signer.sign_event(build_receipt_chain(sample_events())[0])
    tampered = replace(
        signed,
        event={**signed.event, "payload": {"action_id": "changed_after_signing"}},
    )

    report = verify_signed_receipt(tampered)

    assert report.valid is False
    assert report.errors == ("event_hash does not match signed event payload",)


def test_signed_chain_verification_treats_signature_failure_as_fatal() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="chain_signer")
    signed_chain = sign_receipt_chain(sample_events(), signer)
    broken_signature = replace(signed_chain[1], signature="00" * 64)

    report = verify_signed_receipt_chain([signed_chain[0], broken_signature])

    assert report.valid is False
    assert report.chain_root_hash is None
    assert report.chain_tip_hash is None
    assert any("signature verification failed" in error for error in report.errors)


def test_signed_chain_verification_rejects_parent_hash_breaks() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="chain_signer")
    chained = build_receipt_chain(sample_events())
    broken_events = [
        chained[0],
        replace(chained[1], parent_event_hash="sha256:" + "0" * 64),
    ]
    signed_chain = [signer.sign_event(event) for event in broken_events]

    report = verify_signed_receipt_chain(signed_chain)

    assert report.valid is False
    assert report.chain_root_hash is None
    assert report.chain_tip_hash is None
    assert any("parent_event_hash" in error for error in report.errors)
