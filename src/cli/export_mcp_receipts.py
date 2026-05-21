"""export-mcp-receipts command for MCP gateway receipt bundles."""

from __future__ import annotations

from pathlib import Path

import click

from src.agent_receipts.signing import Ed25519ReceiptSigner
from src.integrations.mcp.receipt_export import export_mcp_receipt_bundle
from src.integrations.mcp.store import CapsuleStore


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
def export_mcp_receipts_cmd(
    store_path: Path,
    session_id: str,
    output_path: Path,
) -> None:
    """Export stored MCP gateway capsules as signed agent receipts."""
    signer = Ed25519ReceiptSigner.generate(signer_id="uatp-mcp-gateway")
    bundle = export_mcp_receipt_bundle(
        CapsuleStore(store_path),
        session_id,
        signer,
        output_path=output_path,
    )
    receipt_count = len(bundle.get("signed_receipts", []))
    click.echo(
        f"Exported MCP receipt bundle: {output_path} "
        f"({receipt_count} receipts, session {session_id})"
    )
