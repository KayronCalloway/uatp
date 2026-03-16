"""
Environment Context Capture - Gap 4 Implementation
Captures the environment context at the moment of capsule creation.
"""

import os
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def run_git_command(args: List[str], cwd: str = None) -> Optional[str]:
    """Run a git command and return stdout, or None on error."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=cwd or os.getcwd(),
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def capture_git_context(cwd: str = None) -> Dict[str, Any]:
    """
    Capture git repository context.

    Returns:
        Dict with branch, commit, dirty status, and changed files
    """
    working_dir = cwd or os.getcwd()

    # Check if we're in a git repo
    is_git_repo = run_git_command(["rev-parse", "--is-inside-work-tree"], working_dir)
    if is_git_repo != "true":
        return {"is_git_repo": False}

    git_context = {"is_git_repo": True}

    # Current branch
    branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], working_dir)
    if branch:
        git_context["branch"] = branch

    # Current commit hash (short)
    commit = run_git_command(["rev-parse", "--short", "HEAD"], working_dir)
    if commit:
        git_context["commit"] = commit

    # Full commit hash for verification
    full_commit = run_git_command(["rev-parse", "HEAD"], working_dir)
    if full_commit:
        git_context["commit_full"] = full_commit

    # Commit message (first line)
    commit_msg = run_git_command(["log", "-1", "--format=%s"], working_dir)
    if commit_msg:
        git_context["commit_message"] = commit_msg[:100]  # Truncate long messages

    # Check for uncommitted changes
    status = run_git_command(["status", "--porcelain"], working_dir)
    if status is not None:
        git_context["dirty"] = len(status) > 0
        if status:
            # Parse dirty files
            dirty_files = []
            for line in status.split("\n"):
                if line.strip():
                    # Format: XY filename
                    # X = staged status, Y = unstaged status
                    status_code = line[:2]
                    filename = line[3:].strip()
                    dirty_files.append(
                        {"file": filename, "status": status_code.strip()}
                    )
            git_context["dirty_files"] = dirty_files[:20]  # Limit to 20 files
            git_context["dirty_file_count"] = len(dirty_files)
    else:
        git_context["dirty"] = None  # Unknown

    # Remote URL (for attribution)
    remote_url = run_git_command(["remote", "get-url", "origin"], working_dir)
    if remote_url:
        # Sanitize: remove credentials if present
        if "@" in remote_url and "://" in remote_url:
            # https://user:pass@github.com/... -> https://github.com/...
            parts = remote_url.split("@", 1)
            if len(parts) == 2:
                protocol = remote_url.split("://")[0]
                remote_url = f"{protocol}://{parts[1]}"
        git_context["remote_url"] = remote_url

    return git_context


def capture_system_context() -> Dict[str, Any]:
    """
    Capture system/platform context.

    Returns:
        Dict with OS, Python version, and relevant tool versions
    """
    system_context = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
    }

    # Try to get Node.js version (common for frontend projects)
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            system_context["node_version"] = result.stdout.strip()
    except Exception:
        pass

    # Try to get npm version
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            system_context["npm_version"] = result.stdout.strip()
    except Exception:
        pass

    return system_context


def capture_environment_context(cwd: str = None) -> Dict[str, Any]:
    """
    Capture full environment context for a capsule.

    Args:
        cwd: Working directory (defaults to current)

    Returns:
        Complete environment context dict
    """
    working_dir = cwd or os.getcwd()

    environment = {
        "cwd": working_dir,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "git": capture_git_context(working_dir),
        "system": capture_system_context(),
    }

    # Add relevant environment variables (sanitized)
    safe_env_vars = [
        "USER",
        "SHELL",
        "TERM",
        "LANG",
        "LC_ALL",
        "VIRTUAL_ENV",
        "CONDA_DEFAULT_ENV",
        "NODE_ENV",
        "PYTHON_ENV",
    ]

    env_vars = {}
    for var in safe_env_vars:
        value = os.environ.get(var)
        if value:
            env_vars[var] = value

    if env_vars:
        environment["env_vars"] = env_vars

    return environment


if __name__ == "__main__":
    import json

    print("Environment Context Capture Test")
    print("=" * 50)

    context = capture_environment_context()
    print(json.dumps(context, indent=2))
