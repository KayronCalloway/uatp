"""
UATP CLI - Command-line interface for UATP capsule verification.

Usage:
    uatp verify bundle.json              # Verify a bundle file
    uatp verify -c <capsule_id>          # Verify capsule from server
    uatp verify -w <workflow_id>         # Verify workflow chain

    uatp export <capsule_id>             # Export capsule as bundle
    uatp export <capsule_id> -f dsse     # Export as DSSE envelope

    uatp inspect bundle.json             # Inspect bundle contents
    uatp inspect -c <capsule_id>         # Inspect capsule from server
"""

import click

from src.cli.export_cmd import export_cmd
from src.cli.inspect import inspect_cmd
from src.cli.verify import verify_cmd


@click.group()
@click.version_option(version="1.0.0", prog_name="uatp")
def cli() -> None:
    """
    UATP - Universal AI Transparency Protocol CLI.

    Verify, export, and inspect UATP capsules and bundles.
    """
    pass


# Register subcommands
cli.add_command(verify_cmd)
cli.add_command(export_cmd)
cli.add_command(inspect_cmd)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
