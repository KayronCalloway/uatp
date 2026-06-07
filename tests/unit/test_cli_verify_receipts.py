"""CLI tests for offline agent receipt bundle verification."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone

from click.testing import CliRunner

from src.agent_receipts.artifacts import ArtifactStore
from src.agent_receipts.events import ActionTraceEvent
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle
from src.agent_receipts.verifier import AgentReceiptBundleVerificationReport
from src.cli.main import cli
from src.cli.verify import ExitCode


def _write_receipt_bundle(tmp_path):
    artifact_root = tmp_path / "artifacts"
    store = ArtifactStore(artifact_root)
    stdout_ref = store.store_bytes(
        b"safe output\n",
        media_type="text/plain",
        redaction={"status": "none", "redactions": 0},
    )
    event = ActionTraceEvent(
        event_id="evt_cli_receipts_001",
        session_id="sess_cli_receipts",
        adapter_name="hermes",
        agent_name="Hermes",
        timestamp=datetime(2026, 5, 21, 14, 0, tzinfo=timezone.utc),
        parent_event_hash=None,
        actor="assistant",
        payload={
            "action_id": "act_cli_receipts_001",
            "artifact_refs": {"stdout": stdout_ref.to_dict()},
        },
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )
    signer = Ed25519ReceiptSigner.generate(signer_id="cli_receipts_test")
    bundle = build_signed_receipt_bundle([event], signer)["public"]
    bundle_path = tmp_path / "agent_receipts_bundle.json"
    bundle_path.write_text(json.dumps(bundle))
    return bundle_path, artifact_root, bundle


def test_verify_receipts_text_output_passes_valid_bundle(tmp_path) -> None:
    bundle_path, artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert "Agent receipt verification PASSED" in result.output
    assert "Receipts: 1" in result.output
    assert "Artifacts checked: 1" in result.output
    assert "Trusted timestamp: missing" in result.output


def test_verify_receipts_json_output_is_machine_readable(tmp_path) -> None:
    bundle_path, artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    payload = json.loads(result.output)
    assert payload["valid"] is True
    assert payload["receipt_count"] == 1
    assert payload["artifacts_checked"] == 1
    assert payload["errors"] == []


def test_verify_receipts_trusted_signer_policy_accepts_matching_public_key(
    tmp_path,
) -> None:
    bundle_path, artifact_root, bundle = _write_receipt_bundle(tmp_path)
    signed_receipt = bundle["signed_receipts"][0]
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--trusted-signer",
            f"{signed_receipt['signer_id']}={signed_receipt['public_key']}",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert "Agent receipt verification PASSED" in result.output


def test_verify_receipts_trusted_signer_policy_rejects_wrong_public_key(
    tmp_path,
) -> None:
    bundle_path, artifact_root, bundle = _write_receipt_bundle(tmp_path)
    signed_receipt = bundle["signed_receipts"][0]
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--trusted-signer",
            f"{signed_receipt['signer_id']}={'a' * 64}",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "public key is not trusted" in result.output


def test_verify_receipts_trusted_signer_policy_rejects_unknown_signer(
    tmp_path,
) -> None:
    bundle_path, artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--trusted-signer",
            f"other_signer={'a' * 64}",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "signer cli_receipts_test is not trusted" in result.output


def test_verify_receipts_trusted_signer_policy_rejects_malformed_value(
    tmp_path,
) -> None:
    bundle_path, artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--trusted-signer",
            "not-a-policy",
            "--no-color",
        ],
    )

    assert result.exit_code != ExitCode.SUCCESS
    assert "trusted signer must use signer_id=public_key_hex format" in result.output


def test_verify_receipts_returns_failed_exit_for_tampered_bundle(tmp_path) -> None:
    bundle_path, artifact_root, bundle = _write_receipt_bundle(tmp_path)
    tampered = deepcopy(bundle)
    tampered["signed_receipts"][0]["event"]["payload"]["action_id"] = "changed"
    bundle_path.write_text(json.dumps(tampered))
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "Agent receipt verification FAILED" in result.output
    assert "event_hash does not match" in result.output


def test_verify_receipts_returns_warnings_exit_for_non_strict_missing_artifact_root(
    tmp_path,
) -> None:
    bundle_path, _artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["verify-receipts", str(bundle_path), "--no-color"])

    assert result.exit_code == ExitCode.WARNINGS
    assert "Agent receipt verification PASSED" in result.output
    assert "artifact_root not provided" in result.output


def test_verify_receipts_require_trusted_timestamp_fails_missing_timestamp(
    tmp_path,
) -> None:
    bundle_path, artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--artifact-root",
            str(artifact_root),
            "--strict",
            "--require-trusted-timestamp",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "trusted timestamp proof missing" in result.output
    assert "Trusted timestamp: missing" in result.output


def test_verify_receipts_loads_trusted_tsa_certificate_paths(
    tmp_path,
    monkeypatch,
) -> None:
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text("{}")
    tsa_cert_path = tmp_path / "tsa.pem"
    tsa_cert = b"-----BEGIN CERTIFICATE-----\ntrusted-tsa\n-----END CERTIFICATE-----\n"
    tsa_cert_path.write_bytes(tsa_cert)
    captured = {}

    def fake_verify_agent_receipt_bundle(bundle, **kwargs):
        captured["bundle"] = bundle
        captured.update(kwargs)
        return AgentReceiptBundleVerificationReport(
            valid=True,
            errors=(),
            warnings=(),
            schema_version="agent_receipts.v1",
            receipt_count=1,
            capsule_draft_count=1,
            artifacts_checked=0,
            chain_root_hash="root",
            chain_tip_hash="tip",
            timestamp_verified=True,
            trusted_timestamp_status="verified",
        )

    monkeypatch.setattr(
        "src.cli.verify_receipts.verify_agent_receipt_bundle",
        fake_verify_agent_receipt_bundle,
    )
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--trusted-tsa-certificate",
            str(tsa_cert_path),
            "--require-trusted-timestamp",
            "--no-color",
        ],
    )

    assert result.exit_code == ExitCode.SUCCESS
    assert captured["trusted_tsa_certificates"] == (tsa_cert,)
    assert captured["require_trusted_timestamp"] is True
    assert "Trusted timestamp: verified" in result.output


def test_verify_receipts_rejects_missing_trusted_tsa_certificate_path(tmp_path) -> None:
    bundle_path, _artifact_root, _bundle = _write_receipt_bundle(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "verify-receipts",
            str(bundle_path),
            "--trusted-tsa-certificate",
            str(tmp_path / "missing.pem"),
            "--no-color",
        ],
    )

    assert result.exit_code != ExitCode.SUCCESS
    assert "trusted TSA certificate not found" in result.output
