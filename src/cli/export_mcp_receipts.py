"""export-mcp-receipts command for MCP gateway receipt bundles."""

from __future__ import annotations

import os
from pathlib import Path

import click

from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.integrations.mcp.receipt_export import export_mcp_receipt_bundle
from src.integrations.mcp.store import CapsuleStore


def _build_export_signer(
    signer_id: str,
    signing_key_env: str | None,
) -> Ed25519ReceiptSigner:
    if signing_key_env is None:
        return Ed25519ReceiptSigner.generate(signer_id=signer_id)

    signing_key_hex = os.environ.get(signing_key_env)
    if not signing_key_hex:
        raise click.ClickException("signing key environment variable is not set")
    try:
        return Ed25519ReceiptSigner.from_hex(signing_key_hex, signer_id=signer_id)
    except ValueError as exc:
        raise click.ClickException("invalid signing key") from exc


@click.command("export-mcp-receipts")
@click.argument(
    "store_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--session-id",
    required=True,
    help="MCP gateway session id to export.",
)
@click.option(
    "--output",
    "output_path",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to write the public receipt bundle JSON.",
)
@click.option(
    "--signer-id",
    default="uatp-mcp-gateway",
    show_default=True,
    help="Signer identity to bind into exported receipt signatures.",
)
@click.option(
    "--signing-key-env",
    default=None,
    help="Environment variable containing a 32-byte Ed25519 signing key hex.",
)
def export_mcp_receipts_cmd(
    store_path: Path,
    session_id: str,
    output_path: Path,
    signer_id: str,
    signing_key_env: str | None,
) -> None:
    """Export stored MCP gateway capsules as signed agent receipts."""
    signer = _build_export_signer(signer_id, signing_key_env)
    try:
        bundle = export_mcp_receipt_bundle(
            CapsuleStore(store_path),
            session_id,
            signer,
            output_path=output_path,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    receipt_count = len(bundle.get("signed_receipts", []))
    click.echo(
        f"Exported MCP receipt bundle: {output_path} "
        f"({receipt_count} receipts, session {session_id})"
    )
    click.echo(f"Signer: {signer.signer_id}")
    click.echo(f"Public key: {signer.public_key_hex}")
