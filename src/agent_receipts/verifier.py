"""Offline verification for signed agent receipt bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nacl.exceptions import BadSignatureError

from src.agent_receipts.artifacts import verify_artifact_ref
from src.agent_receipts.events import ArtifactRef
from src.agent_receipts.hashing import sha256_digest
from src.agent_receipts.signing import (
    ReceiptTrustPolicy,
    SignedReceipt,
    verify_hash_signature,
    verify_signed_receipt_chain,
)
from src.agent_receipts.sink import SCHEMA_VERSION
from src.security.rfc3161_timestamps import RFC3161Timestamper, TimestampToken


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
    timestamp_verified: bool = False
    trusted_timestamp_status: str = "missing"


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


def _verify_bundle_manifest(
    *,
    bundle: dict[str, Any],
    signed_receipts: list[SignedReceipt],
    trust_policy: ReceiptTrustPolicy | None = None,
) -> list[str]:
    errors: list[str] = []
    manifest = bundle.get("bundle_manifest")
    if not isinstance(manifest, dict):
        return ["bundle_manifest must be an object"]

    payload = manifest.get("payload")
    if not isinstance(payload, dict):
        return ["bundle_manifest.payload must be an object"]

    expected_payload = {
        "schema_version": bundle.get("schema_version"),
        "chain_report_hash": sha256_digest(bundle.get("chain_report", {})),
        "chain_root_hash": bundle.get("chain_report", {}).get("chain_root_hash")
        if isinstance(bundle.get("chain_report"), dict)
        else None,
        "chain_tip_hash": bundle.get("chain_report", {}).get("chain_tip_hash")
        if isinstance(bundle.get("chain_report"), dict)
        else None,
        "event_count": bundle.get("chain_report", {}).get("event_count")
        if isinstance(bundle.get("chain_report"), dict)
        else None,
        "signed_receipt_hashes": [
            sha256_digest(receipt.to_dict()) for receipt in signed_receipts
        ],
        "capsule_drafts_hash": sha256_digest(bundle.get("capsule_drafts", [])),
    }
    for key, expected_value in expected_payload.items():
        if payload.get(key) != expected_value:
            errors.append(f"bundle_manifest.{key} does not match computed value")

    computed_manifest_hash = sha256_digest(payload)
    if manifest.get("manifest_hash") != computed_manifest_hash:
        errors.append("bundle_manifest.manifest_hash does not match payload")

    manifest_signer_id = manifest.get("signer_id")
    manifest_public_key = manifest.get("public_key")
    receipt_signers = {
        (receipt.signer_id, receipt.public_key) for receipt in signed_receipts
    }
    if (manifest_signer_id, manifest_public_key) not in receipt_signers:
        errors.append("bundle_manifest signer does not match any signed receipt signer")

    if trust_policy is not None:
        manifest_trust_errors = trust_policy.validate(
            SignedReceipt(
                event={},
                event_hash=manifest.get("manifest_hash", ""),
                signature=manifest.get("signature", ""),
                public_key=manifest_public_key or "",
                signer_id=manifest_signer_id or "",
                signature_algorithm=manifest.get("signature_algorithm", "Ed25519"),
            )
        )
        errors.extend(f"bundle_manifest {error}" for error in manifest_trust_errors)

    try:
        verify_hash_signature(
            public_key=manifest["public_key"],
            signature=manifest["signature"],
            digest=manifest["manifest_hash"],
            signer_id=manifest["signer_id"],
            signature_algorithm=manifest.get("signature_algorithm", "Ed25519"),
        )
    except KeyError as exc:
        errors.append(f"bundle_manifest malformed: missing {exc}")
    except (BadSignatureError, TypeError, ValueError) as exc:
        errors.append(f"bundle_manifest signature verification failed: {exc}")

    return errors


def _verify_trusted_timestamp(manifest: dict[str, Any]) -> tuple[str, bool, list[str]]:
    """Verify the RFC3161 proof over the signed bundle manifest hash.

    Missing timestamp proof is not itself a bundle-integrity failure; it means
    the bundle has no independently verified time. Malformed or present-but-
    unverifiable proofs fail closed because they would otherwise invite false
    "timestamped" claims.
    """
    timestamp_info = manifest.get("trusted_timestamp")
    if timestamp_info is None:
        return "missing", False, []
    if not isinstance(timestamp_info, dict) or "rfc3161" not in timestamp_info:
        return (
            "invalid",
            False,
            ["trusted timestamp verification failed: missing RFC 3161 token"],
        )

    manifest_hash = manifest.get("manifest_hash")
    if not isinstance(manifest_hash, str):
        return (
            "invalid",
            False,
            ["trusted timestamp verification failed: manifest_hash missing"],
        )

    try:
        token = TimestampToken.from_dict(timestamp_info["rfc3161"])
        timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)
        verified, reason = timestamper.verify_timestamp(
            token,
            manifest_hash.encode("utf-8"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        return "invalid", False, [f"trusted timestamp verification failed: {exc}"]

    if not verified:
        return "invalid", False, [f"trusted timestamp verification failed: {reason}"]
    return "verified", True, []


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
    timestamp_verified: bool = False,
    trusted_timestamp_status: str = "missing",
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
        timestamp_verified=timestamp_verified,
        trusted_timestamp_status=trusted_timestamp_status,
    )


def verify_agent_receipt_bundle(
    bundle_or_path: dict[str, Any] | str | Path,
    *,
    artifact_root: str | Path | None = None,
    strict: bool = True,
    trust_policy: ReceiptTrustPolicy | None = None,
    require_trusted_timestamp: bool = False,
) -> AgentReceiptBundleVerificationReport:
    """Verify a public signed agent receipt bundle without Hermes or database state.

    Strict mode fails when artifact refs are present but no artifact root is supplied.
    Non-strict mode reports missing artifact roots as warnings so detached receipt
    chains can still be checked.
    """
    errors: list[str] = []
    warnings: list[str] = []
    timestamp_verified = False
    trusted_timestamp_status = "missing"

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
        chain_report = verify_signed_receipt_chain(
            signed_receipts,
            trust_policy=trust_policy,
        )
    except (TypeError, ValueError) as exc:
        return _invalid_report(
            errors=[f"receipt chain verification failed: {exc}"],
            schema_version=schema_version,
            receipt_count=len(signed_receipts),
        )

    if not chain_report.valid:
        errors.extend(chain_report.errors)

    errors.extend(
        _verify_bundle_manifest(
            bundle=bundle,
            signed_receipts=signed_receipts,
            trust_policy=trust_policy,
        )
    )
    manifest = bundle.get("bundle_manifest")
    if isinstance(manifest, dict):
        (
            trusted_timestamp_status,
            timestamp_verified,
            timestamp_errors,
        ) = _verify_trusted_timestamp(manifest)
        errors.extend(timestamp_errors)
    if require_trusted_timestamp and not timestamp_verified:
        if trusted_timestamp_status == "missing":
            errors.append("trusted timestamp proof missing")
        elif not any(
            "trusted timestamp verification failed" in error for error in errors
        ):
            errors.append("trusted timestamp proof unverified")

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
        timestamp_verified=timestamp_verified,
        trusted_timestamp_status=trusted_timestamp_status,
    )
