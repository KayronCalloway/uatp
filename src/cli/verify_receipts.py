"""verify-receipts command for offline agent receipt bundle verification."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import click

from src.agent_receipts.signing import ReceiptTrustPolicy
from src.agent_receipts.verifier import (
    AgentReceiptBundleVerificationReport,
    verify_agent_receipt_bundle,
)
from src.cli.verify import ExitCode


def _report_to_dict(report: AgentReceiptBundleVerificationReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["errors"] = list(report.errors)
    payload["warnings"] = list(report.warnings)
    return payload


def _build_trust_policy(
    trusted_signers: tuple[str, ...],
) -> ReceiptTrustPolicy | None:
    if not trusted_signers:
        return None

    trusted: dict[str, list[str]] = {}
    for value in trusted_signers:
        if "=" not in value:
            raise click.ClickException(
                "trusted signer must use signer_id=public_key_hex format"
            )
        signer_id, public_key = value.split("=", 1)
        if not signer_id or not public_key:
            raise click.ClickException(
                "trusted signer must use signer_id=public_key_hex format"
            )
        try:
            bytes.fromhex(public_key)
        except ValueError as exc:
            raise click.ClickException("trusted signer public key must be hex") from exc
        if len(public_key) != 64:
            raise click.ClickException(
                "trusted signer public key must be a 32-byte Ed25519 hex key"
            )
        trusted.setdefault(signer_id, []).append(public_key)

    return ReceiptTrustPolicy.from_signers(
        {signer_id: tuple(keys) for signer_id, keys in trusted.items()}
    )


def _load_trusted_tsa_certificates(
    certificate_paths: tuple[str, ...],
) -> tuple[bytes, ...]:
    certificates: list[bytes] = []
    for value in certificate_paths:
        path = Path(value).expanduser()
        if not path.exists() or not path.is_file():
            raise click.ClickException(f"trusted TSA certificate not found: {value}")
        try:
            certificate = path.read_bytes()
        except OSError as exc:
            raise click.ClickException(
                f"could not read trusted TSA certificate: {value}"
            ) from exc
        if not certificate.strip():
            raise click.ClickException(f"trusted TSA certificate is empty: {value}")
        certificates.append(certificate)
    return tuple(certificates)


def _format_receipt_report(
    report: AgentReceiptBundleVerificationReport,
    *,
    no_color: bool = False,
) -> str:
    def style(text: str, **kwargs: Any) -> str:
        if no_color:
            return text
        return click.style(text, **kwargs)

    lines: list[str] = []
    if report.valid:
        lines.append(
            style("✓ Agent receipt verification PASSED", fg="green", bold=True)
        )
    else:
        lines.append(style("✗ Agent receipt verification FAILED", fg="red", bold=True))

    lines.extend(
        [
            "",
            f"  Schema: {report.schema_version or 'unknown'}",
            f"  Receipts: {report.receipt_count}",
            f"  Capsule drafts: {report.capsule_draft_count}",
            f"  Artifacts checked: {report.artifacts_checked}",
            f"  Chain root: {report.chain_root_hash or 'unverified'}",
            f"  Chain tip: {report.chain_tip_hash or 'unverified'}",
            f"  Trusted timestamp: {report.trusted_timestamp_status}",
        ]
    )

    if report.errors:
        lines.append("")
        lines.append(style("Errors:", fg="red"))
        for error in report.errors:
            lines.append(f"  • {error}")

    if report.warnings:
        lines.append("")
        lines.append(style("Warnings:", fg="yellow"))
        for warning in report.warnings:
            lines.append(f"  • {warning}")

    return "\n".join(lines)


def _exit_code_for_report(report: AgentReceiptBundleVerificationReport) -> ExitCode:
    if not report.valid:
        return ExitCode.FAILED
    if report.warnings:
        return ExitCode.WARNINGS
    return ExitCode.SUCCESS


@click.command("verify-receipts")
@click.argument("bundle", type=click.Path(exists=False, dir_okay=False))
@click.option(
    "--artifact-root",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    default=None,
    help="Root directory for content-addressed receipt artifacts",
)
@click.option(
    "--strict/--non-strict",
    default=False,
    help="Fail if artifact refs are present but cannot be checked",
)
@click.option(
    "--output",
    "output_format",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option(
    "--require-trusted-timestamp",
    is_flag=True,
    help="Fail unless the bundle has independently verified trusted timestamp evidence",
)
@click.option(
    "--trusted-signer",
    "trusted_signers",
    multiple=True,
    help="Trusted signer binding as signer_id=ed25519_public_key_hex; repeat for rotations",
)
@click.option(
    "--trusted-tsa-certificate",
    "trusted_tsa_certificate_paths",
    multiple=True,
    type=click.Path(exists=False, dir_okay=False),
    help="PEM/DER TSA certificate bundle or trust anchor for RFC 3161 verification; repeatable",
)
def verify_receipts_cmd(
    bundle: str,
    artifact_root: str | None,
    strict: bool,
    output_format: str,
    no_color: bool,
    require_trusted_timestamp: bool,
    trusted_signers: tuple[str, ...],
    trusted_tsa_certificate_paths: tuple[str, ...],
) -> None:
    """Verify a signed agent receipt bundle offline."""
    trust_policy = _build_trust_policy(trusted_signers)
    trusted_tsa_certificates = _load_trusted_tsa_certificates(
        trusted_tsa_certificate_paths
    )
    report = verify_agent_receipt_bundle(
        Path(bundle),
        artifact_root=Path(artifact_root) if artifact_root else None,
        strict=strict,
        trust_policy=trust_policy,
        require_trusted_timestamp=require_trusted_timestamp,
        trusted_tsa_certificates=trusted_tsa_certificates,
    )

    if output_format == "json":
        click.echo(json.dumps(_report_to_dict(report), indent=2, default=str))
    else:
        click.echo(_format_receipt_report(report, no_color=no_color))

    sys.exit(_exit_code_for_report(report))
