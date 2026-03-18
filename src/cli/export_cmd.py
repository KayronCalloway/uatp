"""
Export subcommand - export capsules as bundles or DSSE envelopes.

Commands:
- uatp export <capsule_id> --format bundle    # Full bundle with verification material
- uatp export <capsule_id> --format dsse      # DSSE envelope only
"""

import json
import sys
from typing import Optional

import click


@click.command("export")
@click.argument("capsule_id")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["bundle", "dsse"]),
    default="bundle",
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option(
    "--server",
    "-s",
    envvar="UATP_SERVER_URL",
    default=None,
    help="UATP server URL (or set UATP_SERVER_URL)",
)
@click.option("--pretty", "-p", is_flag=True, help="Pretty print JSON")
def export_cmd(
    capsule_id: str,
    format: str,
    output: Optional[str],
    server: str,
    pretty: bool,
) -> None:
    """
    Export a capsule as a bundle or DSSE envelope.

    \b
    Examples:
        uatp export caps_2026_03_11_abc                    # Export as bundle to stdout
        uatp export caps_2026_03_11_abc -f dsse            # Export as DSSE envelope
        uatp export caps_2026_03_11_abc -o capsule.json    # Save to file
    """
    try:
        import httpx
    except ImportError:
        click.echo(click.style("Error: httpx required for export", fg="red"), err=True)
        click.echo("Install with: pip install httpx")
        sys.exit(1)

    # Determine endpoint
    if format == "bundle":
        endpoint = f"/capsules/{capsule_id}/export/bundle"
    else:
        endpoint = f"/capsules/{capsule_id}/export/dsse"

    url = f"{server.rstrip('/')}{endpoint}"

    # Fetch
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
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: Failed to export: {e}", fg="red"), err=True)
        sys.exit(1)

    # Format output
    indent = 2 if pretty else None
    json_str = json.dumps(data, indent=indent)

    # Write output
    if output:
        with open(output, "w") as f:
            f.write(json_str)
            f.write("\n")
        click.echo(f"Exported to {output}", err=True)
    else:
        click.echo(json_str)
