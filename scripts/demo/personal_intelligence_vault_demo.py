#!/usr/bin/env python3
"""Generate and verify Personal Intelligence Vault receipt demo bundles.

This demo is intentionally local and narrow. It proves scoped memory references,
purpose-policy grant/denial, offline bundle verification, and deterministic
policy-tamper failure. It does not claim Apple integration, PCC parity, or a
marketplace.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agent_receipts.personal_intelligence_vault import (
    LocalPersonalMemoryVault,
    PurposePolicy,
    build_personal_memory_denial_receipt_events,
    build_personal_memory_receipt_events,
)
from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.agent_receipts.sink import build_signed_receipt_bundle
from src.agent_receipts.verifier import verify_agent_receipt_bundle

DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "examples" / "personal-intelligence-vault"


def _timestamp() -> datetime:
    return datetime(2026, 6, 15, 2, 30, tzinfo=timezone.utc)


def _policy() -> PurposePolicy:
    return PurposePolicy(
        purpose="answer_user_request",
        allowed_app="hermes-cli",
        allowed_model="claude-sonnet-4",
        locality_requirement="local_only",
        training_allowed=False,
        retention_expires_at=datetime(2026, 6, 15, 3, 30, tzinfo=timezone.utc),
        licensing_terms="not_licensed",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _build_grant_bundle(signer: Ed25519ReceiptSigner) -> dict[str, Any]:
    vault = LocalPersonalMemoryVault()
    vault.put_memory(
        memory_id="mem_style_001",
        raw_memory={
            "preference": "proof before marketplace",
            "secret_note": "local-only demo input; must not appear in receipts",
        },
        scope=["public_voice", "style_preference"],
        capsule_ref="uatp://capsules/mem_style_001",
    )
    policy = _policy()
    grant = vault.request_context(
        requested_scopes=["public_voice"],
        policy=policy,
        app="hermes-cli",
        model="claude-sonnet-4",
    )
    if not grant.granted:
        raise RuntimeError(f"expected grant, got denial: {grant.denial_reason}")

    events = build_personal_memory_receipt_events(
        session_id="sess_personal_vault_grant_demo",
        adapter_name="personal-intelligence-vault-demo",
        agent_name="Hermes Agent",
        user_id_hash="sha256:" + "b" * 64,
        request_id="ctx_req_grant_demo",
        granted_refs=grant.refs,
        policy=policy,
        model_action_summary="Answered with scoped style memory while keeping marketplace language downstream.",
        correction="Keep proof before compensation.",
        memory_write_id="mem_write_demo_001",
        memory_write_digest="sha256:" + "c" * 64,
        started_at=_timestamp(),
    )
    return build_signed_receipt_bundle(events, signer)["public"]


def _build_denial_bundle(signer: Ed25519ReceiptSigner) -> dict[str, Any]:
    vault = LocalPersonalMemoryVault()
    vault.put_memory(
        memory_id="mem_style_001",
        raw_memory={"preference": "proof before marketplace"},
        scope=["public_voice"],
        capsule_ref="uatp://capsules/mem_style_001",
    )
    policy = _policy()
    denial = vault.request_context(
        requested_scopes=["private_finance"],
        policy=policy,
        app="hermes-cli",
        model="claude-sonnet-4",
    )
    if denial.granted:
        raise RuntimeError("expected denial for unavailable scope")

    events = build_personal_memory_denial_receipt_events(
        session_id="sess_personal_vault_denial_demo",
        adapter_name="personal-intelligence-vault-demo",
        agent_name="Hermes Agent",
        user_id_hash="sha256:" + "b" * 64,
        request_id="ctx_req_denial_demo",
        requested_scopes=["private_finance"],
        policy=policy,
        denial_reason=denial.denial_reason or "scope_not_available",
        started_at=_timestamp(),
    )
    return build_signed_receipt_bundle(events, signer)["public"]


def _tamper_policy(bundle: dict[str, Any]) -> dict[str, Any]:
    tampered = deepcopy(bundle)
    for receipt in tampered["signed_receipts"]:
        event = receipt.get("event", {})
        if event.get("event_type") == "consent":
            event["payload"]["allowed_model"] = "unauthorized-model"
            event["payload"]["policy"]["allowed_model"] = "unauthorized-model"
            return tampered
    raise RuntimeError("grant bundle did not contain consent receipt")


def _assert_report(name: str, valid: bool, expected: bool) -> None:
    status = "PASS" if valid is expected else "FAIL"
    print(f"{status}: {name}")
    if valid is not expected:
        raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where demo receipt bundles are written",
    )
    args = parser.parse_args()

    signer = Ed25519ReceiptSigner.generate(signer_id="personal_vault_demo")
    grant_bundle = _build_grant_bundle(signer)
    denial_bundle = _build_denial_bundle(signer)

    _write_json(args.output_dir / "personal_memory_grant_bundle.json", grant_bundle)
    _write_json(args.output_dir / "personal_memory_denial_bundle.json", denial_bundle)

    grant_report = verify_agent_receipt_bundle(grant_bundle)
    denial_report = verify_agent_receipt_bundle(denial_bundle)
    tamper_report = verify_agent_receipt_bundle(_tamper_policy(grant_bundle))

    _assert_report("scoped memory grant bundle verifies", grant_report.valid, True)
    _assert_report("scoped memory denial bundle verifies", denial_report.valid, True)
    _assert_report("policy tamper fails", tamper_report.valid, False)
    print(f"Wrote demo bundles to: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
