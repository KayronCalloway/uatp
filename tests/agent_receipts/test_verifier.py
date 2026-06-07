"""Offline verifier tests for signed agent receipt bundles."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import datetime, timezone

from src.agent_receipts.artifacts import ArtifactStore
from src.agent_receipts.events import ActionTraceEvent
from src.agent_receipts.signing import (
    Ed25519ReceiptSigner,
    ReceiptTrustPolicy,
    SignedReceipt,
)
from src.agent_receipts.sink import build_bundle_manifest, build_signed_receipt_bundle
from src.agent_receipts.verifier import verify_agent_receipt_bundle
from src.security.rfc3161_timestamps import TimestampToken


def _valid_bundle(tmp_path, signer: Ed25519ReceiptSigner | None = None):
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
    signer = signer or Ed25519ReceiptSigner.generate(signer_id="offline_verifier_test")
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
    assert report.timestamp_verified is False
    assert report.trusted_timestamp_status == "missing"


def test_verify_agent_receipt_bundle_requires_trusted_timestamp_when_requested(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)

    report = verify_agent_receipt_bundle(
        bundle,
        artifact_root=tmp_path,
        strict=True,
        require_trusted_timestamp=True,
    )

    assert report.valid is False
    assert report.timestamp_verified is False
    assert report.trusted_timestamp_status == "missing"
    assert any("trusted timestamp proof missing" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_malformed_trusted_timestamp(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)
    bundle["bundle_manifest"]["trusted_timestamp"] = {
        "rfc3161": {
            "token": "not-base64",
            "timestamp": "2026-05-21T12:00:00+00:00",
            "tsa": "freetsa",
            "hash_algorithm": "sha256",
            "message_imprint": "0" * 64,
        }
    }

    report = verify_agent_receipt_bundle(bundle, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert report.timestamp_verified is False
    assert report.trusted_timestamp_status == "invalid"
    assert any(
        "trusted timestamp verification failed" in error for error in report.errors
    )


def test_verify_agent_receipt_bundle_verifies_timestamp_with_tsa_anchor(
    tmp_path,
    monkeypatch,
) -> None:
    captured = {}

    def fake_verify_timestamp(
        self, token, original_data, trusted_tsa_certificates=None
    ):
        captured["token"] = token
        captured["original_data"] = original_data
        captured["trusted_tsa_certificates"] = trusted_tsa_certificates
        return True, "RFC 3161 timestamp verified against TSA trust anchor"

    monkeypatch.setattr(
        "src.agent_receipts.verifier.RFC3161Timestamper.verify_timestamp",
        fake_verify_timestamp,
    )
    bundle = _valid_bundle(tmp_path)
    manifest_hash = bundle["bundle_manifest"]["manifest_hash"]
    token = TimestampToken(
        token_bytes=b"trusted timestamp response der",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="test-tsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(manifest_hash.encode("utf-8")).hexdigest(),
    )
    bundle["bundle_manifest"]["trusted_timestamp"] = {"rfc3161": token.to_dict()}
    anchor = b"-----BEGIN CERTIFICATE-----\ntrusted\n"

    report = verify_agent_receipt_bundle(
        bundle,
        artifact_root=tmp_path,
        strict=True,
        require_trusted_timestamp=True,
        trusted_tsa_certificates=(anchor,),
    )

    assert report.valid is True
    assert report.timestamp_verified is True
    assert report.trusted_timestamp_status == "verified"
    assert captured["original_data"] == manifest_hash.encode("utf-8")
    assert captured["trusted_tsa_certificates"] == (anchor,)


def test_verify_agent_receipt_bundle_applies_trust_policy(tmp_path) -> None:
    trusted_signer = Ed25519ReceiptSigner.generate(signer_id="offline_verifier_test")
    impostor_signer = Ed25519ReceiptSigner.generate(signer_id="offline_verifier_test")
    bundle = _valid_bundle(tmp_path, signer=impostor_signer)
    policy = ReceiptTrustPolicy.from_signers(
        {"offline_verifier_test": trusted_signer.public_key_hex}
    )

    report = verify_agent_receipt_bundle(
        bundle,
        artifact_root=tmp_path,
        strict=True,
        trust_policy=policy,
    )

    assert report.valid is False
    assert any("public key is not trusted" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_tampered_signer_identity(tmp_path) -> None:
    bundle = _valid_bundle(tmp_path)
    tampered = deepcopy(bundle)
    tampered["signed_receipts"][0]["signer_id"] = "different_signer"

    report = verify_agent_receipt_bundle(tampered, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert any("signature verification failed" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_tampered_capsule_draft(tmp_path) -> None:
    bundle = _valid_bundle(tmp_path)
    tampered = deepcopy(bundle)
    tampered["capsule_drafts"][0]["action_trace"]["action_id"] = "changed_after_signing"

    report = verify_agent_receipt_bundle(tampered, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert any("capsule_drafts_hash" in error for error in report.errors)


def test_verify_agent_receipt_bundle_rejects_attacker_resigned_manifest(
    tmp_path,
) -> None:
    trusted_signer = Ed25519ReceiptSigner.generate(signer_id="offline_verifier_test")
    attacker_signer = Ed25519ReceiptSigner.generate(signer_id="attacker_manifest_key")
    bundle = _valid_bundle(tmp_path, signer=trusted_signer)
    bundle["capsule_drafts"][0]["action_trace"]["action_id"] = "changed_after_signing"
    bundle["bundle_manifest"] = build_bundle_manifest(
        schema_version=bundle["schema_version"],
        chain_report=bundle["chain_report"],
        signed_receipts=[
            SignedReceipt(**receipt) for receipt in bundle["signed_receipts"]
        ],
        capsule_drafts=bundle["capsule_drafts"],
        signer=attacker_signer,
    )
    policy = ReceiptTrustPolicy.from_signers(
        {"offline_verifier_test": trusted_signer.public_key_hex}
    )

    report = verify_agent_receipt_bundle(
        bundle,
        artifact_root=tmp_path,
        strict=True,
        trust_policy=policy,
    )

    assert report.valid is False
    assert any(
        "bundle_manifest signer attacker_manifest_key is not trusted" in error
        for error in report.errors
    )


def test_verify_agent_receipt_bundle_reports_malformed_manifest_signature_fields(
    tmp_path,
) -> None:
    bundle = _valid_bundle(tmp_path)
    bundle["bundle_manifest"]["public_key"] = None

    report = verify_agent_receipt_bundle(bundle, artifact_root=tmp_path, strict=True)

    assert report.valid is False
    assert any(
        "bundle_manifest signature verification failed" in error
        for error in report.errors
    )


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
