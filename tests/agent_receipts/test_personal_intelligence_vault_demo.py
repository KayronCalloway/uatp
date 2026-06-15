"""Regression test for the Personal Intelligence Vault receipt demo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_personal_intelligence_vault_demo_writes_verifiable_grant_and_denial_bundles(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = tmp_path / "vault-demo"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/demo/personal_intelligence_vault_demo.py",
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    assert "PASS: scoped memory grant bundle verifies" in result.stdout
    assert "PASS: scoped memory denial bundle verifies" in result.stdout
    assert "PASS: policy tamper fails" in result.stdout

    grant_bundle = output_dir / "personal_memory_grant_bundle.json"
    denial_bundle = output_dir / "personal_memory_denial_bundle.json"
    assert grant_bundle.exists()
    assert denial_bundle.exists()

    grant_payload = json.loads(grant_bundle.read_text())
    denial_payload = json.loads(denial_bundle.read_text())
    assert grant_payload["schema_version"] == "agent_receipts.v1"
    assert denial_payload["schema_version"] == "agent_receipts.v1"
    assert "raw_memory" not in grant_bundle.read_text()
    assert "secret_note" not in grant_bundle.read_text()

    for bundle in (grant_bundle, denial_bundle):
        verify_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.main",
                "verify-receipts",
                str(bundle),
                "--no-color",
            ],
            cwd=repo_root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert verify_result.returncode == 0, verify_result.stdout
        assert "Agent receipt verification PASSED" in verify_result.stdout
