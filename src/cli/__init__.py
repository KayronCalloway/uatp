"""
UATP CLI - Command-line interface for UATP capsule verification.

Provides commands for:
- verify: Verify bundles, capsules, and workflows
- export: Export capsules as bundles or DSSE envelopes
- inspect: Examine capsule and bundle contents

Install the CLI with:
    pip install -e .

Then use:
    uatp --help
"""

from src.cli.main import cli, main

__all__ = ["cli", "main"]
