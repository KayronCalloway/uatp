"""Regression test for the public agent receipt tamper demo runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_public_agent_receipt_tamper_demo_runner_passes() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/demo/verify_agent_receipt_tamper_demo.py"],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    assert "PASS: valid bundle verifies exit=0 expected=0" in result.stdout
    assert "PASS: event payload tamper fails exit=1 expected=1" in result.stdout
    assert "PASS: parent hash tamper fails exit=1 expected=1" in result.stdout
    assert "PASS: signature tamper fails exit=1 expected=1" in result.stdout
    assert "PASS: artifact tamper fails exit=1 expected=1" in result.stdout
