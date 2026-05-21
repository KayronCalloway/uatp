"""verify-receipts command for offline agent receipt bundle verification."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import click

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
def verify_receipts_cmd(
    bundle: str,
    artifact_root: str | None,
    strict: bool,
    output_format: str,
    no_color: bool,
) -> None:
    """Verify a signed agent receipt bundle offline."""
    report = verify_agent_receipt_bundle(
        Path(bundle),
        artifact_root=Path(artifact_root) if artifact_root else None,
        strict=strict,
    )

    if output_format == "json":
        click.echo(json.dumps(_report_to_dict(report), indent=2, default=str))
    else:
        click.echo(_format_receipt_report(report, no_color=no_color))

    sys.exit(_exit_code_for_report(report))
