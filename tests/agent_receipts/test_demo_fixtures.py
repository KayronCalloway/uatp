"""Regression tests for public agent receipt verification demo fixtures."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from src.cli.main import cli
from src.cli.verify import ExitCode

FIXTURE_ROOT = Path("docs/examples/agent-receipts")


def _run_verify(bundle_name: str, artifact_root: str = "artifacts"):
    runner = CliRunner()
    return runner.invoke(
        cli,
        [
            "verify-receipts",
            str(FIXTURE_ROOT / bundle_name),
            "--artifact-root",
            str(FIXTURE_ROOT / artifact_root),
            "--strict",
            "--no-color",
        ],
    )


def test_valid_agent_receipt_demo_fixture_passes() -> None:
    result = _run_verify("valid_bundle.json")

    assert result.exit_code == ExitCode.SUCCESS
    assert "Agent receipt verification PASSED" in result.output
    assert "Receipts: 2" in result.output
    assert "Artifacts checked: 1" in result.output


def test_tampered_event_demo_fixture_fails_event_hash_verification() -> None:
    result = _run_verify("tampered_event_bundle.json")

    assert result.exit_code == ExitCode.FAILED
    assert "event_hash does not match signed event payload" in result.output


def test_tampered_parent_demo_fixture_fails_chain_verification() -> None:
    result = _run_verify("tampered_parent_bundle.json")

    assert result.exit_code == ExitCode.FAILED
    assert "parent_event_hash" in result.output


def test_tampered_signature_demo_fixture_fails_signature_verification() -> None:
    result = _run_verify("tampered_signature_bundle.json")

    assert result.exit_code == ExitCode.FAILED
    assert "signature verification failed" in result.output


def test_tampered_artifact_demo_fixture_fails_artifact_verification() -> None:
    result = _run_verify("valid_bundle.json", artifact_root="artifacts_tampered")

    assert result.exit_code == ExitCode.FAILED
    assert "artifact verification failed" in result.output
