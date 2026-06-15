from __future__ import annotations

from datetime import datetime, timezone

from src.agent_receipts.personal_intelligence_vault import (
    LocalPersonalMemoryVault,
    PurposePolicy,
    ScopedMemoryRef,
    build_personal_memory_denial_receipt_events,
    build_personal_memory_receipt_events,
)
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle
from src.agent_receipts.verifier import verify_agent_receipt_bundle


def ts(second: int) -> datetime:
    return datetime(2026, 6, 8, 18, 30, second, tzinfo=timezone.utc)


def standard_policy(**overrides) -> PurposePolicy:
    values = {
        "purpose": "answer_user_request",
        "allowed_app": "hermes-cli",
        "allowed_model": "claude-sonnet-4",
        "locality_requirement": "local_only",
        "training_allowed": False,
        "retention_expires_at": ts(59),
        "licensing_terms": "not_licensed",
    }
    values.update(overrides)
    return PurposePolicy(**values)


def test_local_vault_returns_scoped_refs_without_raw_memory() -> None:
    vault = LocalPersonalMemoryVault()
    vault.put_memory(
        memory_id="mem_style_001",
        raw_memory={
            "preference": "proof before marketplace",
            "secret_note": "do not expose",
        },
        scope=["public_voice", "style_preference"],
        capsule_ref="uatp://capsules/mem_style_001",
    )

    grant = vault.request_context(
        requested_scopes=["public_voice"],
        policy=standard_policy(),
        app="hermes-cli",
        model="claude-sonnet-4",
    )

    assert grant.granted is True
    assert grant.refs == [
        ScopedMemoryRef(
            memory_id="mem_style_001",
            capsule_ref="uatp://capsules/mem_style_001",
            digest=grant.refs[0].digest,
            scope=["public_voice"],
        )
    ]
    assert grant.denial_reason is None
    assert grant.refs[0].digest.startswith("sha256:")
    assert "raw_memory" not in grant.to_receipt_payload()
    assert "secret_note" not in str(grant.to_receipt_payload())


def test_local_vault_denies_policy_mismatch_and_emits_no_refs() -> None:
    vault = LocalPersonalMemoryVault()
    vault.put_memory(
        memory_id="mem_style_001",
        raw_memory={"preference": "proof before marketplace"},
        scope=["public_voice"],
        capsule_ref="uatp://capsules/mem_style_001",
    )

    grant = vault.request_context(
        requested_scopes=["public_voice"],
        policy=standard_policy(allowed_model="claude-sonnet-4"),
        app="hermes-cli",
        model="unauthorized-model",
    )

    assert grant.granted is False
    assert grant.refs == []
    assert grant.denial_reason == "model_not_allowed"
    assert grant.to_receipt_payload()["granted"] is False
    assert grant.to_receipt_payload()["granted_refs"] == []


def test_denied_context_request_builds_refusal_bundle_without_memory_refs() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="vault_denial_test")
    policy = standard_policy()
    events = build_personal_memory_denial_receipt_events(
        session_id="sess_vault_denial",
        adapter_name="personal-intelligence-vault-demo",
        agent_name="Hermes Agent",
        user_id_hash="sha256:" + "b" * 64,
        request_id="ctx_req_denied",
        requested_scopes=["private_finance"],
        policy=policy,
        denial_reason="scope_not_available",
        started_at=ts(0),
    )

    assert [event.event_type for event in events] == [
        "session.started",
        "decision.point",
        "refusal",
        "session.ended",
    ]
    refusal = events[2]
    assert refusal.payload["reason"] == "scope_not_available"
    assert refusal.payload["granted_refs"] == []
    assert "raw_memory" not in refusal.payload

    bundle = build_signed_receipt_bundle(events, signer)["public"]
    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "agent_session",
        "decision_point",
        "refusal",
    ]
    assert verify_agent_receipt_bundle(bundle).valid is True


def test_personal_memory_receipt_chain_records_policy_without_raw_memory() -> None:
    policy = PurposePolicy(
        purpose="answer_user_request",
        allowed_app="hermes-cli",
        allowed_model="claude-sonnet-4",
        locality_requirement="local_only",
        training_allowed=False,
        retention_expires_at=ts(59),
        licensing_terms="not_licensed",
    )
    memory_ref = ScopedMemoryRef(
        memory_id="mem_style_001",
        capsule_ref="uatp://capsules/mem_style_001",
        digest="sha256:" + "a" * 64,
        scope=["public_voice", "style_preference"],
    )

    events = build_personal_memory_receipt_events(
        session_id="sess_vault_demo",
        adapter_name="personal-intelligence-vault-demo",
        agent_name="Hermes Agent",
        user_id_hash="sha256:" + "b" * 64,
        request_id="ctx_req_001",
        granted_refs=[memory_ref],
        policy=policy,
        model_action_summary="Drafted a public UATP paragraph using scoped style memory.",
        correction="Keep marketplace language downstream of signed receipts.",
        memory_write_id="mem_write_001",
        memory_write_digest="sha256:" + "c" * 64,
        started_at=ts(0),
    )

    assert [event.event_type for event in events] == [
        "session.started",
        "decision.point",
        "consent",
        "llm_call.completed",
        "user.feedback",
        "memory.write",
        "session.ended",
    ]

    context_grant = events[2]
    assert context_grant.payload["policy"] == policy.to_dict()
    assert context_grant.payload["granted_refs"] == [memory_ref.to_dict()]
    assert "raw_memory" not in context_grant.payload
    assert context_grant.payload["training_allowed"] is False
    assert context_grant.payload["licensing_terms"] == "not_licensed"

    memory_write = events[5]
    assert memory_write.payload["memory_write_digest"] == "sha256:" + "c" * 64
    assert "raw_memory" not in memory_write.payload


def test_personal_memory_receipt_bundle_verifies_and_policy_tamper_fails() -> None:
    signer = Ed25519ReceiptSigner.generate(signer_id="vault_test")
    policy = PurposePolicy(
        purpose="answer_user_request",
        allowed_app="hermes-cli",
        allowed_model="claude-sonnet-4",
        locality_requirement="local_only",
        training_allowed=False,
        retention_expires_at=ts(59),
        licensing_terms="not_licensed",
    )
    memory_ref = ScopedMemoryRef(
        memory_id="mem_style_001",
        capsule_ref="uatp://capsules/mem_style_001",
        digest="sha256:" + "a" * 64,
        scope=["public_voice"],
    )
    events = build_personal_memory_receipt_events(
        session_id="sess_vault_demo",
        adapter_name="personal-intelligence-vault-demo",
        agent_name="Hermes Agent",
        user_id_hash="sha256:" + "b" * 64,
        request_id="ctx_req_001",
        granted_refs=[memory_ref],
        policy=policy,
        model_action_summary="Answered using scoped memory.",
        correction="Keep proof before compensation.",
        memory_write_id="mem_write_001",
        memory_write_digest="sha256:" + "c" * 64,
        started_at=ts(0),
    )
    bundle = build_signed_receipt_bundle(events, signer)["public"]

    assert [draft["capsule_type"] for draft in bundle["capsule_drafts"]] == [
        "agent_session",
        "decision_point",
        "consent",
        "reasoning_trace",
        "feedback_assimilation",
        "audit",
    ]
    consent_draft = bundle["capsule_drafts"][2]
    assert consent_draft["consent"]["grantor"] == "sha256:" + "b" * 64
    assert consent_draft["receipt_metadata"]["training_allowed"] is False
    assert consent_draft["receipt_metadata"]["granted_refs"] == [memory_ref.to_dict()]
    assert "raw_memory" not in consent_draft["consent"]
    assert "raw_memory" not in consent_draft["receipt_metadata"]

    report = verify_agent_receipt_bundle(bundle)
    assert report.valid is True

    tampered = {
        **bundle,
        "signed_receipts": [dict(r) for r in bundle["signed_receipts"]],
    }
    tampered["signed_receipts"][2] = {
        **tampered["signed_receipts"][2],
        "event": {
            **tampered["signed_receipts"][2]["event"],
            "payload": {
                **tampered["signed_receipts"][2]["event"]["payload"],
                "training_allowed": True,
            },
        },
    }

    tamper_report = verify_agent_receipt_bundle(tampered)
    assert tamper_report.valid is False
    assert any(
        "signature" in error or "hash" in error for error in tamper_report.errors
    )
