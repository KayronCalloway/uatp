"""Offline verification for signed agent receipt bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agent_receipts.artifacts import verify_artifact_ref
from src.agent_receipts.events import ArtifactRef
from src.agent_receipts.signing import SignedReceipt, verify_signed_receipt_chain
from src.agent_receipts.sink import SCHEMA_VERSION


@dataclass(frozen=True)
class AgentReceiptBundleVerificationReport:
    """Structured result for offline agent receipt bundle verification."""

    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    schema_version: str | None
    receipt_count: int
    capsule_draft_count: int
    artifacts_checked: int
    chain_root_hash: str | None
    chain_tip_hash: str | None


def _load_bundle(bundle_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(bundle_or_path, dict):
        return bundle_or_path
    path = Path(bundle_or_path).expanduser()
    return json.loads(path.read_text())


def _signed_receipt_from_dict(value: Any) -> SignedReceipt:
    if not isinstance(value, dict):
        raise TypeError(f"signed receipt must be object, got {type(value).__name__}")
    return SignedReceipt(
        event=value["event"],
        event_hash=value["event_hash"],
        signature=value["signature"],
        public_key=value["public_key"],
        signer_id=value["signer_id"],
        signature_algorithm=value.get("signature_algorithm", "Ed25519"),
    )


def _looks_like_artifact_ref(value: dict[str, Any]) -> bool:
    required = {"digest", "path", "size", "media_type", "redaction"}
    return required.issubset(value.keys())


def _iter_artifact_refs(value: Any):
    if isinstance(value, dict):
        if _looks_like_artifact_ref(value):
            yield value
            return
        for item in value.values():
            yield from _iter_artifact_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_artifact_refs(item)


def _invalid_report(
    *,
    errors: list[str],
    warnings: list[str] | None = None,
    schema_version: str | None = None,
    receipt_count: int = 0,
    capsule_draft_count: int = 0,
    artifacts_checked: int = 0,
    chain_root_hash: str | None = None,
    chain_tip_hash: str | None = None,
) -> AgentReceiptBundleVerificationReport:
    return AgentReceiptBundleVerificationReport(
        valid=False,
        errors=tuple(errors),
        warnings=tuple(warnings or []),
        schema_version=schema_version,
        receipt_count=receipt_count,
        capsule_draft_count=capsule_draft_count,
        artifacts_checked=artifacts_checked,
        chain_root_hash=chain_root_hash,
        chain_tip_hash=chain_tip_hash,
    )


def verify_agent_receipt_bundle(
    bundle_or_path: dict[str, Any] | str | Path,
    *,
    artifact_root: str | Path | None = None,
    strict: bool = True,
) -> AgentReceiptBundleVerificationReport:
    """Verify a public signed agent receipt bundle without Hermes or database state.

    Strict mode fails when artifact refs are present but no artifact root is supplied.
    Non-strict mode reports missing artifact roots as warnings so detached receipt
    chains can still be checked.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        bundle = _load_bundle(bundle_or_path)
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return _invalid_report(errors=[f"bundle load failed: {exc}"])

    schema_version = bundle.get("schema_version") if isinstance(bundle, dict) else None
    if schema_version != SCHEMA_VERSION:
        return _invalid_report(
            errors=[f"unsupported schema_version: {schema_version}"],
            schema_version=schema_version,
        )

    raw_receipts = bundle.get("signed_receipts")
    if not isinstance(raw_receipts, list):
        return _invalid_report(
            errors=["signed_receipts must be a list"],
            schema_version=schema_version,
        )

    try:
        signed_receipts = [_signed_receipt_from_dict(item) for item in raw_receipts]
    except (KeyError, TypeError) as exc:
        return _invalid_report(
            errors=[f"signed receipt envelope malformed: {exc}"],
            schema_version=schema_version,
            receipt_count=len(raw_receipts),
        )

    try:
        chain_report = verify_signed_receipt_chain(signed_receipts)
    except (TypeError, ValueError) as exc:
        return _invalid_report(
            errors=[f"receipt chain verification failed: {exc}"],
            schema_version=schema_version,
            receipt_count=len(signed_receipts),
        )

    if not chain_report.valid:
        errors.extend(chain_report.errors)

    declared_chain = bundle.get("chain_report", {})
    if isinstance(declared_chain, dict):
        if chain_report.valid:
            if declared_chain.get("chain_root_hash") != chain_report.chain_root_hash:
                errors.append("declared chain_root_hash does not match computed root")
            if declared_chain.get("chain_tip_hash") != chain_report.chain_tip_hash:
                errors.append("declared chain_tip_hash does not match computed tip")
            if declared_chain.get("event_count") != chain_report.event_count:
                errors.append("declared event_count does not match receipt count")
    else:
        errors.append("chain_report must be an object")

    capsule_drafts = bundle.get("capsule_drafts")
    if not isinstance(capsule_drafts, list):
        errors.append("capsule_drafts must be a list")
        capsule_draft_count = 0
    else:
        capsule_draft_count = len(capsule_drafts)
        for index, draft in enumerate(capsule_drafts):
            if not isinstance(draft, dict):
                errors.append(f"capsule_drafts[{index}] must be an object")

    artifact_ref_dicts = [
        ref for receipt in signed_receipts for ref in _iter_artifact_refs(receipt.event)
    ]
    artifacts_checked = len(artifact_ref_dicts)
    if artifact_ref_dicts and artifact_root is None:
        message = "artifact_root not provided for bundle artifact refs"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)
    elif artifact_root is not None:
        for index, ref_dict in enumerate(artifact_ref_dicts):
            try:
                ref = ArtifactRef(**ref_dict)
                if not verify_artifact_ref(artifact_root, ref):
                    errors.append(
                        f"artifact verification failed at ref {index}: {ref.path}"
                    )
            except (TypeError, ValueError) as exc:
                errors.append(f"artifact ref {index} malformed: {exc}")

    valid = not errors
    return AgentReceiptBundleVerificationReport(
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
        schema_version=schema_version,
        receipt_count=len(signed_receipts),
        capsule_draft_count=capsule_draft_count,
        artifacts_checked=artifacts_checked,
        chain_root_hash=chain_report.chain_root_hash if valid else None,
        chain_tip_hash=chain_report.chain_tip_hash if valid else None,
    )
