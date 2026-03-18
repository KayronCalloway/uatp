"""
Inspect subcommand - examine capsule and bundle contents.

Commands:
- uatp inspect bundle.json           # Inspect local bundle
- uatp inspect --capsule-id <id>     # Inspect capsule from server
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import click

from src.export import UATPBundle


def format_bytes(n: int) -> str:
    """Format bytes as human readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def print_tree(data: Dict[str, Any], indent: int = 0) -> None:
    """Print data as a tree structure."""
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            click.echo(f"{prefix}{click.style(key, fg='cyan')}:")
            print_tree(value, indent + 1)
        elif isinstance(value, list):
            click.echo(f"{prefix}{click.style(key, fg='cyan')}: [{len(value)} items]")
            for i, item in enumerate(value[:3]):  # Show first 3
                if isinstance(item, dict):
                    click.echo(f"{prefix}  [{i}]:")
                    print_tree(item, indent + 2)
                else:
                    click.echo(f"{prefix}  [{i}]: {item}")
            if len(value) > 3:
                click.echo(f"{prefix}  ... and {len(value) - 3} more")
        else:
            # Truncate long strings
            if isinstance(value, str) and len(value) > 60:
                display = value[:57] + "..."
            else:
                display = value
            click.echo(f"{prefix}{click.style(key, fg='cyan')}: {display}")


def inspect_bundle_file(path: Path, show_payload: bool = False) -> int:
    """Inspect a bundle file."""
    if not path.exists():
        click.echo(click.style(f"Error: File not found: {path}", fg="red"), err=True)
        return 1

    try:
        with open(path) as f:
            content = f.read()
            bundle = UATPBundle.from_json(content)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to parse bundle: {e}", fg="red"), err=True
        )
        return 1

    # Header
    click.echo(click.style("╔══════════════════════════════════════╗", fg="blue"))
    click.echo(click.style("║        UATP Bundle Inspection        ║", fg="blue"))
    click.echo(click.style("╚══════════════════════════════════════╝", fg="blue"))
    click.echo("")

    # File info
    file_size = path.stat().st_size
    click.echo(click.style("File:", fg="green", bold=True))
    click.echo(f"  Path: {path}")
    click.echo(f"  Size: {format_bytes(file_size)}")
    click.echo(f"  Media Type: {bundle.media_type}")
    click.echo("")

    # Bundle metadata
    click.echo(click.style("Bundle:", fg="green", bold=True))
    click.echo(f"  Capsule ID: {bundle.capsule_id or 'N/A'}")
    click.echo(f"  Created At: {bundle.created_at.isoformat()}")
    click.echo("")

    # DSSE envelope
    if bundle.dsse:
        click.echo(click.style("DSSE Envelope:", fg="green", bold=True))
        click.echo(f"  Payload Type: {bundle.dsse.payload_type}")
        click.echo(f"  Payload Size: {format_bytes(len(bundle.dsse.payload_bytes()))}")
        click.echo(f"  Signatures: {len(bundle.dsse.signatures)}")

        for i, sig in enumerate(bundle.dsse.signatures):
            click.echo(f"    [{i}] Key ID: {sig.keyid}")
            click.echo(f"        Signature: {sig.sig[:32]}...")
        click.echo("")

    # Verification material
    if bundle.verification:
        click.echo(click.style("Verification Material:", fg="green", bold=True))
        v = bundle.verification
        click.echo(f"  Algorithm: {v.key_algorithm}")
        click.echo(f"  Key ID: {v.key_id or 'N/A'}")
        if v.public_key:
            click.echo(f"  Public Key: {v.public_key[:32]}...")
        click.echo(f"  Hybrid: {'Yes' if v.is_hybrid else 'No'}")

        if v.timestamp:
            click.echo("")
            click.echo(click.style("  Timestamp:", fg="yellow"))
            click.echo(f"    Authority: {v.timestamp.authority or 'N/A'}")
            click.echo(f"    Has Token: {'Yes' if v.timestamp.has_token else 'No'}")
            if v.timestamp.timestamp:
                click.echo(f"    Time: {v.timestamp.timestamp.isoformat()}")
        click.echo("")

    # Payload content
    if show_payload and bundle.dsse:
        click.echo(click.style("Payload Content:", fg="green", bold=True))
        try:
            payload = bundle.get_payload()
            print_tree(payload, indent=1)
        except Exception as e:
            click.echo(click.style(f"  Error parsing payload: {e}", fg="red"))
        click.echo("")

    # Quick verify
    click.echo(click.style("Quick Verify:", fg="green", bold=True))
    result = bundle.verify()
    if result.is_valid:
        click.echo(click.style("  ✓ Bundle is valid", fg="green"))
    else:
        click.echo(click.style("  ✗ Bundle verification failed", fg="red"))
        for err in result.errors[:3]:
            click.echo(f"    - {err}")

    return 0


def inspect_capsule_from_server(
    capsule_id: str,
    server_url: str,
    show_payload: bool = False,
) -> int:
    """Inspect capsule from server."""
    try:
        import httpx
    except ImportError:
        click.echo(
            click.style("Error: httpx required for remote inspection", fg="red"),
            err=True,
        )
        return 1

    url = f"{server_url.rstrip('/')}/capsules/{capsule_id}"

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            click.echo(
                click.style(f"Error: Capsule not found: {capsule_id}", fg="red"),
                err=True,
            )
        else:
            click.echo(
                click.style(
                    f"Error: Server returned {e.response.status_code}", fg="red"
                ),
                err=True,
            )
        return 1
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to fetch capsule: {e}", fg="red"), err=True
        )
        return 1

    # Header
    click.echo(click.style("╔══════════════════════════════════════╗", fg="blue"))
    click.echo(click.style("║       UATP Capsule Inspection        ║", fg="blue"))
    click.echo(click.style("╚══════════════════════════════════════╝", fg="blue"))
    click.echo("")

    # Capsule info
    click.echo(click.style("Capsule:", fg="green", bold=True))
    click.echo(f"  ID: {data.get('capsule_id', 'N/A')}")
    click.echo(f"  Type: {data.get('capsule_type', data.get('type', 'N/A'))}")
    click.echo(f"  Timestamp: {data.get('timestamp', 'N/A')}")
    click.echo("")

    # Verification status
    verification = data.get("verification", {})
    click.echo(click.style("Verification:", fg="green", bold=True))
    click.echo(f"  Signed: {'Yes' if verification.get('signature') else 'No'}")
    click.echo(f"  Algorithm: {verification.get('algorithm', 'N/A')}")
    if verification.get("timestamp_token"):
        click.echo("  Has RFC3161 Timestamp: Yes")
    click.echo("")

    # Measurements
    measurements = data.get("measurements", {})
    if measurements:
        click.echo(click.style("Measurements:", fg="green", bold=True))
        for key, value in list(measurements.items())[:10]:
            click.echo(f"  {key}: {value}")
        if len(measurements) > 10:
            click.echo(f"  ... and {len(measurements) - 10} more")
        click.echo("")

    # Payload
    if show_payload:
        payload = data.get("payload", {})
        if payload:
            click.echo(click.style("Payload:", fg="green", bold=True))
            print_tree(payload, indent=1)

    return 0


@click.command("inspect")
@click.argument("file", required=False, type=click.Path(exists=False))
@click.option("--capsule-id", "-c", help="Inspect capsule by ID from server")
@click.option(
    "--server",
    "-s",
    envvar="UATP_SERVER_URL",
    default=None,
    help="UATP server URL (or set UATP_SERVER_URL)",
)
@click.option("--payload", "-p", is_flag=True, help="Show payload content")
def inspect_cmd(
    file: Optional[str],
    capsule_id: Optional[str],
    server: str,
    payload: bool,
) -> None:
    """
    Inspect UATP bundles or capsules.

    \b
    Examples:
        uatp inspect bundle.json               # Inspect local bundle file
        uatp inspect bundle.json --payload     # Show payload content
        uatp inspect -c caps_2026_03_11_abc    # Inspect capsule from server
    """
    if file:
        exit_code = inspect_bundle_file(Path(file), payload)
    elif capsule_id:
        exit_code = inspect_capsule_from_server(capsule_id, server, payload)
    else:
        click.echo("Error: Provide a file path or --capsule-id", err=True)
        exit_code = 1

    sys.exit(exit_code)
