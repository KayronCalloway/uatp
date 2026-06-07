#!/usr/bin/env python3
"""Run the public agent receipt tamper-failure demo.

This script intentionally depends only on the checked-in fixture bundle files
and the offline verifier CLI. It does not need Hermes, SQLite, a backend, or
network access.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "docs" / "examples" / "agent-receipts"


@dataclass(frozen=True)
class DemoCase:
    name: str
    bundle: str
    artifact_root: str
    expected_exit: int
    expected_text: str


def _run_case(case: DemoCase) -> tuple[bool, str]:
    command = [
        sys.executable,
        "-m",
        "src.cli.main",
        "verify-receipts",
        str(FIXTURE_ROOT / case.bundle),
        "--artifact-root",
        str(FIXTURE_ROOT / case.artifact_root),
        "--strict",
        "--no-color",
    ]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = result.stdout
    ok = result.returncode == case.expected_exit and case.expected_text in output
    status = "PASS" if ok else "FAIL"
    return (
        ok,
        f"{status}: {case.name} exit={result.returncode} expected={case.expected_exit}",
    )


def main() -> int:
    cases = [
        DemoCase(
            name="valid bundle verifies",
            bundle="valid_bundle.json",
            artifact_root="artifacts",
            expected_exit=0,
            expected_text="Agent receipt verification PASSED",
        ),
        DemoCase(
            name="event payload tamper fails",
            bundle="tampered_event_bundle.json",
            artifact_root="artifacts",
            expected_exit=1,
            expected_text="event_hash does not match signed event payload",
        ),
        DemoCase(
            name="parent hash tamper fails",
            bundle="tampered_parent_bundle.json",
            artifact_root="artifacts",
            expected_exit=1,
            expected_text="parent_event_hash",
        ),
        DemoCase(
            name="signature tamper fails",
            bundle="tampered_signature_bundle.json",
            artifact_root="artifacts",
            expected_exit=1,
            expected_text="placeholder signature is not valid evidence",
        ),
        DemoCase(
            name="artifact tamper fails",
            bundle="valid_bundle.json",
            artifact_root="artifacts_tampered",
            expected_exit=1,
            expected_text="artifact verification failed",
        ),
    ]

    results = [_run_case(case) for case in cases]
    for _ok, line in results:
        print(line)

    return 0 if all(ok for ok, _line in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
