"""
Verify subcommand - verify bundles, capsules, and workflows.

Exit Codes:
    0 = All checks passed
    1 = Verification failed (signature invalid)
    2 = Warnings only (signature valid, optional checks failed)
    3 = Configuration error (file not found, invalid arguments)
    4 = Network/transient error (timeout, server unavailable)

Commands:
    uatp verify bundle.json              # Verify a bundle file
    uatp verify *.json                   # Batch verify multiple files
    uatp verify --capsule-id <id>        # Fetch and verify from server
    uatp verify --workflow <id>          # Verify workflow chain
    uatp verify bundle.json --output json  # JSON output
"""

import hashlib
import json
import re
import sys
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from src.export import UATPBundle, VerificationResult


class ExitCode(IntEnum):
    """CLI exit codes with semantic meaning."""

    SUCCESS = 0  # All checks passed
    FAILED = 1  # Verification failed
    WARNINGS = 2  # Passed with warnings
    CONFIG_ERROR = 3  # Invalid config/arguments
    NETWORK_ERROR = 4  # Transient/network error


def result_to_dict(
    result: VerificationResult, bundle: Optional[UATPBundle] = None
) -> Dict[str, Any]:
    """Convert verification result to JSON-serializable dict."""
    output = {
        "is_valid": result.is_valid,
        "checks": [],
        "errors": result.errors,
        "warnings": result.warnings,
        "verified_at": result.verified_at.isoformat(),
    }

    if result.signature_valid is not None:
        output["checks"].append(
            {
                "name": "signature",
                "passed": result.signature_valid,
            }
        )

    if result.timestamp_valid is not None:
        output["checks"].append(
            {
                "name": "timestamp",
                "passed": result.timestamp_valid,
            }
        )

    if result.pq_signature_valid is not None:
        output["checks"].append(
            {
                "name": "pq_signature",
                "passed": result.pq_signature_valid,
            }
        )

    if bundle:
        output["bundle"] = {
            "capsule_id": bundle.capsule_id,
            "created_at": bundle.created_at.isoformat() if bundle.created_at else None,
        }
        if bundle.verification:
            output["bundle"]["key_algorithm"] = bundle.verification.key_algorithm
            output["bundle"]["key_id"] = bundle.verification.key_id

    return output


def format_result(
    result: VerificationResult, verbose: bool = False, no_color: bool = False
) -> str:
    """Format verification result for human-readable output."""
    lines = []

    def style(text: str, **kwargs) -> str:
        if no_color:
            return text
        return click.style(text, **kwargs)

    # Status
    if result.is_valid:
        lines.append(style("✓ Verification PASSED", fg="green", bold=True))
    else:
        lines.append(style("✗ Verification FAILED", fg="red", bold=True))

    lines.append("")

    # Details
    if result.signature_valid is not None:
        icon = "✓" if result.signature_valid else "✗"
        color = "green" if result.signature_valid else "red"
        lines.append(
            style(f"  {icon} Signature: ", fg=color)
            + ("valid" if result.signature_valid else "invalid")
        )

    if result.timestamp_valid is not None:
        icon = "✓" if result.timestamp_valid else "✗"
        color = "green" if result.timestamp_valid else "red"
        lines.append(
            style(f"  {icon} Timestamp: ", fg=color)
            + ("valid" if result.timestamp_valid else "invalid")
        )
    elif verbose:
        lines.append(style("  - Timestamp: ", fg="yellow") + "not present")

    if result.pq_signature_valid is not None:
        icon = "✓" if result.pq_signature_valid else "✗"
        color = "green" if result.pq_signature_valid else "red"
        lines.append(
            style(f"  {icon} PQ Signature: ", fg=color)
            + ("valid" if result.pq_signature_valid else "invalid")
        )

    # Errors
    if result.errors:
        lines.append("")
        lines.append(style("Errors:", fg="red"))
        for err in result.errors:
            lines.append(f"  • {err}")

    # Warnings
    if result.warnings:
        lines.append("")
        lines.append(style("Warnings:", fg="yellow"))
        for warn in result.warnings:
            lines.append(f"  • {warn}")

    return "\n".join(lines)


def determine_exit_code(result: VerificationResult) -> ExitCode:
    """Determine appropriate exit code based on result."""
    if result.is_valid:
        if result.warnings:
            return ExitCode.WARNINGS
        return ExitCode.SUCCESS
    return ExitCode.FAILED


_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_HEX.fullmatch(value) is not None


def _require_fields(
    item: Dict[str, Any],
    fields: List[str],
    prefix: str,
    errors: List[str],
) -> None:
    for field in fields:
        if field not in item:
            errors.append(f"{prefix}.{field} missing")


def _validate_hash_field(
    item: Dict[str, Any],
    field: str,
    prefix: str,
    errors: List[str],
) -> None:
    if field in item and not _is_sha256_hex(item[field]):
        errors.append(f"{prefix}.{field} must be lowercase SHA-256 hex")


def _artifact_counts(artifacts: Dict[str, Any]) -> Dict[str, int]:
    files = artifacts.get("files") if isinstance(artifacts.get("files"), list) else []
    commands = (
        artifacts.get("commands") if isinstance(artifacts.get("commands"), list) else []
    )
    verifications = [
        cmd
        for cmd in commands
        if isinstance(cmd, dict) and cmd.get("is_verification") is True
    ]
    return {
        "files_total": len(files),
        "commands_total": len(commands),
        "verification_commands_total": len(verifications),
    }


def verify_artifacts_in_capsule(capsule: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the base artifact-proof manifest structure in a capsule payload."""
    errors: List[str] = []
    warnings: List[str] = []
    payload = capsule.get("payload") if isinstance(capsule, dict) else None
    if not isinstance(payload, dict):
        errors.append("payload missing")
        payload = {}

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("payload.artifacts missing")
        artifacts = {}

    files = artifacts.get("files", [])
    commands = artifacts.get("commands", [])
    if not isinstance(files, list):
        errors.append("payload.artifacts.files must be a list")
        files = []
    if not isinstance(commands, list):
        errors.append("payload.artifacts.commands must be a list")
        commands = []

    for index, file_artifact in enumerate(files):
        prefix = f"payload.artifacts.files[{index}]"
        if not isinstance(file_artifact, dict):
            errors.append(f"{prefix} must be an object")
            continue
        _require_fields(file_artifact, ["path", "operation"], prefix, errors)
        operation = file_artifact.get("operation")
        if operation == "write":
            _require_fields(
                file_artifact,
                [
                    "content_hash_after",
                    "content_size_after",
                    "content_preview",
                    "content_preview_truncated",
                    "content_preview_original_length",
                    "redactions",
                ],
                prefix,
                errors,
            )
            _validate_hash_field(file_artifact, "content_hash_after", prefix, errors)
        elif operation == "patch":
            _require_fields(
                file_artifact,
                [
                    "old_string_hash",
                    "new_string_hash",
                    "old_string_size",
                    "new_string_size",
                ],
                prefix,
                errors,
            )
            _validate_hash_field(file_artifact, "old_string_hash", prefix, errors)
            _validate_hash_field(file_artifact, "new_string_hash", prefix, errors)
        elif operation == "read":
            # H1 read artifacts intentionally bind only to the requested path/window.
            # They do not claim a content hash unless a future producer captures one.
            pass
        elif operation is not None:
            errors.append(f"{prefix}.operation unsupported: {operation}")

    for index, command in enumerate(commands):
        prefix = f"payload.artifacts.commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{prefix} must be an object")
            continue
        _require_fields(
            command,
            [
                "command",
                "stdout_hash",
                "stdout_size",
                "stdout_preview",
                "stdout_preview_truncated",
                "stdout_preview_original_length",
                "redactions",
                "is_verification",
                "verification_type",
                "verification_status",
            ],
            prefix,
            errors,
        )
        _validate_hash_field(command, "stdout_hash", prefix, errors)

    counts = _artifact_counts({"files": files, "commands": commands})
    for key, actual in counts.items():
        declared = artifacts.get(key)
        if declared is not None and declared != actual:
            errors.append(
                f"payload.artifacts.{key} expected {actual}, found {declared}"
            )

    return {
        "is_valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "artifact_checks": counts,
    }


def _resolve_artifact_path(root: Path, artifact_path: Any) -> Path | None:
    if not isinstance(artifact_path, str) or not artifact_path:
        return None
    root_resolved = root.resolve()
    candidate = (root_resolved / artifact_path).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate


def verify_artifacts_strict(capsule: Dict[str, Any], root: Path) -> Dict[str, Any]:
    """Strictly verify artifact-proof metadata against the current workspace."""
    result = verify_artifacts_in_capsule(capsule)
    errors = list(result["errors"])
    warnings = list(result["warnings"])
    strict_checks = {
        "files_checked": 0,
        "file_hash_matches": 0,
        "verification_commands_checked": 0,
        "verification_commands_failed": 0,
    }

    payload = capsule.get("payload") if isinstance(capsule, dict) else {}
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else {}
    files = artifacts.get("files", []) if isinstance(artifacts, dict) else []
    commands = artifacts.get("commands", []) if isinstance(artifacts, dict) else []

    for index, file_artifact in enumerate(files if isinstance(files, list) else []):
        if not isinstance(file_artifact, dict):
            continue
        if file_artifact.get("operation") != "write":
            continue
        prefix = f"payload.artifacts.files[{index}]"
        artifact_path = file_artifact.get("path")
        disk_path = _resolve_artifact_path(root, artifact_path)
        if disk_path is None:
            errors.append(f"{prefix}.path escapes strict root")
            continue
        strict_checks["files_checked"] += 1
        if not disk_path.is_file():
            errors.append(f"{prefix}.path missing on disk: {artifact_path}")
            continue
        disk_bytes = disk_path.read_bytes()
        disk_hash = hashlib.sha256(disk_bytes).hexdigest()
        if disk_hash != file_artifact.get("content_hash_after"):
            errors.append(f"{prefix}.content_hash_after mismatch")
            continue
        declared_size = file_artifact.get("content_size_after")
        if isinstance(declared_size, int) and declared_size != len(disk_bytes):
            errors.append(f"{prefix}.content_size_after mismatch")
            continue
        strict_checks["file_hash_matches"] += 1

    for command in commands if isinstance(commands, list) else []:
        if not isinstance(command, dict) or command.get("is_verification") is not True:
            continue
        strict_checks["verification_commands_checked"] += 1
        if command.get("verification_status") == "failed":
            strict_checks["verification_commands_failed"] += 1
            verification_type = command.get("verification_type") or "unknown"
            errors.append(f"verification command failed: {verification_type}")

    result.update(
        {
            "strict": True,
            "is_valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "strict_checks": strict_checks,
        }
    )
    return result


def verify_artifacts_file(
    path: Path,
    output_format: str = "text",
    strict: bool = False,
    root: Optional[Path] = None,
) -> tuple[ExitCode, Dict[str, Any]]:
    """Verify artifact-proof metadata from a local capsule JSON file."""
    if not path.exists():
        data = {"error": f"File not found: {path}", "file": str(path)}
        if output_format == "text":
            click.echo(
                click.style(f"Error: File not found: {path}", fg="red"), err=True
            )
        return ExitCode.CONFIG_ERROR, data

    try:
        capsule = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        data = {"error": f"Invalid JSON: {e}", "file": str(path)}
        if output_format == "text":
            click.echo(click.style(f"Error: Invalid JSON: {e}", fg="red"), err=True)
        return ExitCode.CONFIG_ERROR, data

    result = (
        verify_artifacts_strict(capsule, root or Path.cwd())
        if strict
        else verify_artifacts_in_capsule(capsule)
    )
    result["file"] = str(path)
    if output_format == "text":
        status = "PASSED" if result["is_valid"] else "FAILED"
        mode = "strict artifact" if strict else "artifact"
        click.echo(f"{mode.title()} verification {status}")
        for error in result["errors"]:
            click.echo(f"  • {error}")
    return (ExitCode.SUCCESS if result["is_valid"] else ExitCode.FAILED), result


def verify_bundle_file(
    path: Path,
    verbose: bool = False,
    output_format: str = "text",
    no_color: bool = False,
) -> tuple[ExitCode, Dict[str, Any]]:
    """Verify a bundle file and return exit code + result data."""
    if not path.exists():
        error_data = {"error": f"File not found: {path}", "file": str(path)}
        if output_format == "text":
            click.echo(
                click.style(f"Error: File not found: {path}", fg="red"), err=True
            )
        return ExitCode.CONFIG_ERROR, error_data

    try:
        with open(path) as f:
            bundle = UATPBundle.from_json(f.read())
    except json.JSONDecodeError as e:
        error_data = {"error": f"Invalid JSON: {e}", "file": str(path)}
        if output_format == "text":
            click.echo(click.style(f"Error: Invalid JSON: {e}", fg="red"), err=True)
        return ExitCode.CONFIG_ERROR, error_data
    except Exception as e:
        error_data = {"error": f"Failed to parse bundle: {e}", "file": str(path)}
        if output_format == "text":
            click.echo(
                click.style(f"Error: Failed to parse bundle: {e}", fg="red"), err=True
            )
        return ExitCode.CONFIG_ERROR, error_data

    # Verify
    result = bundle.verify()
    result_data = result_to_dict(result, bundle)
    result_data["file"] = str(path)

    # Output
    if output_format == "text":
        click.echo(format_result(result, verbose, no_color))

        if verbose:
            click.echo("")
            click.echo(click.style("Bundle Info:", fg="blue"))
            click.echo(f"  Capsule ID: {bundle.capsule_id or 'N/A'}")
            click.echo(f"  Created At: {bundle.created_at.isoformat()}")
            if bundle.verification:
                click.echo(f"  Key Algorithm: {bundle.verification.key_algorithm}")
                click.echo(f"  Key ID: {bundle.verification.key_id or 'N/A'}")

    return determine_exit_code(result), result_data


def verify_multiple_files(
    paths: List[Path],
    verbose: bool = False,
    output_format: str = "text",
    no_color: bool = False,
) -> tuple[ExitCode, List[Dict[str, Any]]]:
    """Verify multiple bundle files."""
    results = []
    worst_exit = ExitCode.SUCCESS

    for i, path in enumerate(paths):
        if output_format == "text" and len(paths) > 1:
            click.echo(f"\n[{i + 1}/{len(paths)}] Verifying {path}...")

        exit_code, result_data = verify_bundle_file(
            path, verbose, output_format, no_color
        )
        results.append(result_data)

        # Track worst exit code
        if exit_code.value > worst_exit.value:
            worst_exit = exit_code

    # Summary for text output
    if output_format == "text" and len(paths) > 1:
        passed = sum(1 for r in results if r.get("is_valid", False))
        failed = len(results) - passed
        click.echo("")
        click.echo(f"Summary: {passed}/{len(results)} passed", nl=False)
        if failed > 0:
            click.echo(click.style(f", {failed} failed", fg="red"))
        else:
            click.echo(click.style(" ✓", fg="green"))

    return worst_exit, results


def verify_capsule_from_server(
    capsule_id: str,
    server_url: str,
    verbose: bool = False,
    output_format: str = "text",
    no_color: bool = False,
) -> tuple[ExitCode, Dict[str, Any]]:
    """Fetch and verify capsule from server."""
    try:
        import httpx
    except ImportError:
        error_data = {"error": "httpx required for remote verification"}
        if output_format == "text":
            click.echo(
                click.style("Error: httpx required for remote verification", fg="red"),
                err=True,
            )
            click.echo("Install with: pip install httpx")
        return ExitCode.CONFIG_ERROR, error_data

    # Fetch bundle
    url = f"{server_url.rstrip('/')}/capsules/{capsule_id}/export/bundle"
    if output_format == "text":
        click.echo(f"Fetching bundle from {url}...", err=True)

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        bundle = UATPBundle.from_json(response.text)
    except httpx.TimeoutException:
        error_data = {"error": "Request timeout", "capsule_id": capsule_id}
        if output_format == "text":
            click.echo(click.style("Error: Request timeout", fg="red"), err=True)
        return ExitCode.NETWORK_ERROR, error_data
    except httpx.HTTPStatusError as e:
        error_data = {
            "error": f"Server returned {e.response.status_code}",
            "capsule_id": capsule_id,
        }
        if output_format == "text":
            click.echo(
                click.style(
                    f"Error: Server returned {e.response.status_code}", fg="red"
                ),
                err=True,
            )
        return (
            ExitCode.NETWORK_ERROR
            if e.response.status_code >= 500
            else ExitCode.CONFIG_ERROR,
            error_data,
        )
    except Exception as e:
        error_data = {"error": f"Failed to fetch bundle: {e}", "capsule_id": capsule_id}
        if output_format == "text":
            click.echo(
                click.style(f"Error: Failed to fetch bundle: {e}", fg="red"), err=True
            )
        return ExitCode.NETWORK_ERROR, error_data

    # Verify
    result = bundle.verify()
    result_data = result_to_dict(result, bundle)
    result_data["capsule_id"] = capsule_id

    if output_format == "text":
        click.echo(format_result(result, verbose, no_color))

    return determine_exit_code(result), result_data


def verify_workflow_from_server(
    workflow_id: str,
    server_url: str,
    verbose: bool = False,
    output_format: str = "text",
    no_color: bool = False,
) -> tuple[ExitCode, Dict[str, Any]]:
    """Fetch and verify workflow from server."""
    try:
        import httpx
    except ImportError:
        error_data = {"error": "httpx required for remote verification"}
        if output_format == "text":
            click.echo(
                click.style("Error: httpx required for remote verification", fg="red"),
                err=True,
            )
        return ExitCode.CONFIG_ERROR, error_data

    # Fetch workflow verification
    url = f"{server_url.rstrip('/')}/workflows/{workflow_id}/verify"
    if output_format == "text":
        click.echo(f"Fetching workflow from {url}...", err=True)

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException:
        error_data = {"error": "Request timeout", "workflow_id": workflow_id}
        if output_format == "text":
            click.echo(click.style("Error: Request timeout", fg="red"), err=True)
        return ExitCode.NETWORK_ERROR, error_data
    except httpx.HTTPStatusError as e:
        error_data = {
            "error": f"Server returned {e.response.status_code}",
            "workflow_id": workflow_id,
        }
        if output_format == "text":
            click.echo(
                click.style(
                    f"Error: Server returned {e.response.status_code}", fg="red"
                ),
                err=True,
            )
        return (
            ExitCode.NETWORK_ERROR
            if e.response.status_code >= 500
            else ExitCode.CONFIG_ERROR,
            error_data,
        )
    except Exception as e:
        error_data = {
            "error": f"Failed to fetch workflow: {e}",
            "workflow_id": workflow_id,
        }
        if output_format == "text":
            click.echo(
                click.style(f"Error: Failed to fetch workflow: {e}", fg="red"), err=True
            )
        return ExitCode.NETWORK_ERROR, error_data

    # Display result
    is_valid = data.get("isValid", False)
    data["workflow_id"] = workflow_id

    if output_format == "text":
        if is_valid:
            click.echo(
                click.style("✓ Workflow Verification PASSED", fg="green", bold=True)
            )
        else:
            click.echo(
                click.style("✗ Workflow Verification FAILED", fg="red", bold=True)
            )

        click.echo("")

        # Chain info
        chain = data.get("chain", {})
        click.echo(f"  Steps: {data.get('stepCount', 'N/A')}")
        click.echo(
            f"  Handoffs verified: {chain.get('verifiedHandoffs', 0)}/{chain.get('totalHandoffs', 0)}"
        )

        if chain.get("breaks"):
            click.echo("")
            click.echo(click.style("Chain Breaks:", fg="red"))
            for brk in chain["breaks"]:
                click.echo(
                    f"  • {brk.get('fromStep')} → {brk.get('toStep')}: {brk.get('message')}"
                )

        # Policy
        policy = data.get("policy", {})
        if policy.get("violations"):
            click.echo("")
            click.echo(click.style("Policy Violations:", fg="red"))
            for v in policy["violations"]:
                click.echo(f"  • [{v.get('rule')}] {v.get('message')}")

    return ExitCode.SUCCESS if is_valid else ExitCode.FAILED, data


@click.command("verify")
@click.argument("files", nargs=-1, type=click.Path(exists=False))
@click.option(
    "--artifacts",
    type=click.Path(exists=False),
    help="Verify artifact-proof metadata from a capsule JSON file",
)
@click.option("--capsule-id", "-c", help="Verify capsule by ID from server")
@click.option("--workflow", "-w", help="Verify workflow by ID from server")
@click.option(
    "--server",
    "-s",
    envvar="UATP_SERVER_URL",
    default=None,
    help="UATP server URL (or set UATP_SERVER_URL)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option(
    "--strict",
    is_flag=True,
    help="Strictly verify artifact metadata against the workspace",
)
@click.option(
    "--root",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    default=None,
    help="Workspace root for --strict artifact verification (default: current directory)",
)
def verify_cmd(
    files: tuple,
    artifacts: Optional[str],
    capsule_id: Optional[str],
    workflow: Optional[str],
    server: str,
    output: str,
    verbose: bool,
    no_color: bool,
    strict: bool,
    root: Optional[str],
) -> None:
    """
    Verify UATP bundles, capsules, or workflows.

    \b
    Exit Codes:
        0 = All checks passed
        1 = Verification failed
        2 = Passed with warnings
        3 = Configuration error
        4 = Network error

    \b
    Examples:
        uatp verify bundle.json                # Verify local bundle file
        uatp verify *.json                     # Batch verify multiple files
        uatp verify bundle.json -o json        # JSON output
        uatp verify -c caps_2026_03_11_abc     # Verify capsule from server
        uatp verify -w wf_123                  # Verify workflow from server
    """
    result_data: Any = None

    if artifacts:
        exit_code, result_data = verify_artifacts_file(
            Path(artifacts), output, strict, Path(root) if root else None
        )
    elif files:
        paths = [Path(f) for f in files]
        if len(paths) == 1:
            exit_code, result_data = verify_bundle_file(
                paths[0], verbose, output, no_color
            )
        else:
            exit_code, result_data = verify_multiple_files(
                paths, verbose, output, no_color
            )
    elif capsule_id:
        exit_code, result_data = verify_capsule_from_server(
            capsule_id, server, verbose, output, no_color
        )
    elif workflow:
        exit_code, result_data = verify_workflow_from_server(
            workflow, server, verbose, output, no_color
        )
    else:
        click.echo("Error: Provide file path(s), --capsule-id, or --workflow", err=True)
        sys.exit(ExitCode.CONFIG_ERROR)

    # JSON output
    if output == "json" and result_data:
        click.echo(json.dumps(result_data, indent=2, default=str))

    sys.exit(exit_code)
