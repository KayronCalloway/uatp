"""Offline verifier tests for signed agent receipt bundles."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from src.agent_receipts.artifacts import ArtifactStore
from src.agent_receipts.events import ActionTraceEvent
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle
from src.agent_receipts.verifier import verify_agent_receipt_bundle


def _valid_bundle(tmp_path):
    store = ArtifactStore(tmp_path)
    artifact_ref = store.store_bytes(
        b"redacted tool output\n",
        media_type="text/plain",
        redaction={"status": "redacted", "redactions": 1},
    )
    event = ActionTraceEvent(
        event_id="evt_verifier_001",
        session_id="sess_verifier",
        adapter_name="hermes",
        agent_name="Hermes",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        parent_event_hash=None,
        actor="assistant",
        payload={
            "action_id": "act_001",
            "artifact_refs": {"stdout": artifact_ref.to_dict()},
        },
        redaction_summary={"secrets_removed": 1},
        trust_level="local",
    )
    signer = Ed25519ReceiptSigner.generate(signer_id="offline_verifier_test")
    return build_signed_receipt_bundle([event], signer)["public"]


def test_verify_agent_receipt_bundle_accepts_valid_bundle_with_artifacts(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)

    report = verify_agent_receipt_bundle(bundle, artifact_root=tmp_path, strict=True)

    assert report.valid is True
    assert report.errors == ()
    assert report.warnings == ()
    assert report.schema_version == "agent_receipts.v1"
    assert report.receipt_count == 1
    assert report.chain_root_hash == bundle["chain_report"]["chain_root_hash"]
    assert report.chain_tip_hash == bundle["chain_report"]["chain_tip_hash"]
    assert report.artifacts_checked == 1
    assert report.capsule_draft_count == 1


def test_verify_agent_receipt_bundle_rejects_tampered_event_payload(tmp_path) -> None:
    bundle = _valid_bundle(tmp_path)
    tampered = deepcopy(bundle)
    tampered["signed_receipts"][0]["event"]["payload"]["action_id"] = "changed"

    report = verify_agent_receipt_bundle(tampered, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert any("event_hash does not match" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_malformed_signature_hex(tmp_path) -> None:
    bundle = _valid_bundle(tmp_path)
    tampered = deepcopy(bundle)
    tampered["signed_receipts"][0]["signature"] = "not-hex"

    report = verify_agent_receipt_bundle(tampered, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert any("signature verification failed" in error for error in report.errors)


def test_verify_agent_receipt_bundle_warns_or_fails_missing_artifact_root(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)

    non_strict_report = verify_agent_receipt_bundle(
        bundle, artifact_root=None, strict=False
    )
    strict_report = verify_agent_receipt_bundle(bundle, artifact_root=None, strict=True)

    assert non_strict_report.valid is True
    assert any(
        "artifact_root not provided" in warning
        for warning in non_strict_report.warnings
    )
    assert strict_report.valid is False
    assert any("artifact_root not provided" in error for error in strict_report.errors)


def test_verify_agent_receipt_bundle_fails_missing_artifact_in_strict_mode(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)
    ref = bundle["signed_receipts"][0]["event"]["payload"]["artifact_refs"]["stdout"]
    (tmp_path / ref["path"]).unlink()

    report = verify_agent_receipt_bundle(bundle, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert report.artifacts_checked == 1
    assert any("artifact verification failed" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_wrong_schema_version(tmp_path) -> None:
    bundle = _valid_bundle(tmp_path)
    bundle["schema_version"] = "agent_receipts.v2"

    report = verify_agent_receipt_bundle(bundle, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert report.errors == ("unsupported schema_version: agent_receipts.v2",)
