"""
UATP MCP Policy Engine
======================

Thin, scoped policy evaluation for the MCP gateway.

This is NOT the full metaphysics engine of UATP. It answers one question:
"Should this tool call proceed under current scoped rules?"

Design principles:
- Explicit allow/deny lists per tool
- Path scoping for file operations
- No fuzzy heuristic blocking in MVP
- Every block emits a REFUSAL capsule with explicit reason

Policy rules are loaded from a dict or JSON file. Production would add:
- Delegation requirements (e.g., "send_email requires human_approval capsule")
- Rate limiting per tool
- Budget caps per session
- Audit-only vs enforce modes
"""

from __future__ import annotations

import fnmatch
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyResult:
    """Outcome of policy evaluation."""

    allowed: bool
    reason: str = ""
    policy_version: str = ""
    checks_passed: list[str] | None = None
    checks_failed: list[str] | None = None


class PolicyEngine:
    """
    Scoped policy engine for MCP tool calls.
    """

    def __init__(self, rules: dict[str, Any] | None = None, version: str = "mvp"):
        self.rules = rules or self._default_rules()
        self.version = version

    def _default_rules(self) -> dict[str, Any]:
        """
        Conservative defaults for MVP demo.

        Blocks:
        - writing outside allowed directories
        - running shell commands that look destructive
        - any tool not explicitly listed (deny-by-default)
        """
        return {
            "default_action": "deny",
            "tools": {
                "read_file": {"action": "allow"},
                "write_file": {
                    "action": "allow",
                    "constraints": {
                        "path_allowlist": ["~/project/*", "/tmp/*"],
                        "path_denylist": ["/etc/*", "/usr/*", "~/.ssh/*"],
                    },
                },
                "run_command": {
                    "action": "allow",
                    "constraints": {
                        "blocked_commands": ["rm -rf /", "mkfs.*", "dd if=/dev/zero"],
                    },
                },
            },
        }

    @staticmethod
    def _resolve_path(raw_path: str) -> str:
        """
        Resolve a tool-provided path to a canonical absolute path.

        Handles: ~, ., .., symlinks, relative paths.

        Returns the canonical path string, or raises ValueError if
        the path is unresolvable or attempts to escape the filesystem.
        """
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            # Relative paths are rejected for file operations
            # in a governance boundary — implicit cwd makes policy unreliable.
            raise ValueError(f"Relative paths not allowed: {raw_path}")

        try:
            resolved = p.resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Cannot resolve path {raw_path}: {e}")

        # os.path.realpath resolves any remaining symlinks not caught by resolve()
        canonical = os.path.realpath(str(resolved))

        return canonical

    @staticmethod
    def _path_matches_patterns(canonical: str, patterns: list[str]) -> bool:
        """
        Check if a canonical path matches any pattern.

        Patterns can be:
        - Absolute directory: /home/user/project → match /home/user/project/*
        - Absolute with wildcard: /tmp/* → match /tmp/anything

        Uses prefix comparison after normalizing patterns.
        """
        for pattern in patterns:
            # Normalize pattern the same way
            pattern_path = Path(pattern).expanduser()
            pattern_str = str(pattern_path)

            # If pattern has wildcard, strip it and compare prefix
            if "*" in pattern_str:
                prefix = pattern_str.split("*")[0]
                if canonical.startswith(prefix):
                    return True
            elif pattern_str.endswith("/"):
                if canonical.startswith(pattern_str) or canonical == pattern_str.rstrip(
                    "/"
                ):
                    return True
            else:
                # Exact match or child-of-pattern
                if canonical == pattern_str or canonical.startswith(
                    pattern_str + os.sep
                ):
                    return True

        return False

    def evaluate(self, tool_name: str, arguments: dict[str, Any]) -> PolicyResult:
        """
        Evaluate whether a tool call should proceed.
        """
        tool_rules = self.rules.get("tools", {})
        default_action = self.rules.get("default_action", "deny")

        if tool_name not in tool_rules:
            if default_action == "deny":
                return PolicyResult(
                    allowed=False,
                    reason=f"tool_not_registered: {tool_name}",
                    policy_version=self.version,
                    checks_failed=["tool_not_in_allowlist"],
                )
            return PolicyResult(
                allowed=True,
                reason="default_allow",
                policy_version=self.version,
                checks_passed=["default_allow"],
            )

        spec = tool_rules[tool_name]
        action = spec.get("action", default_action)
        constraints = spec.get("constraints", {})

        if action == "deny":
            return PolicyResult(
                allowed=False,
                reason=f"tool_blocked_by_policy: {tool_name}",
                policy_version=self.version,
                checks_failed=["explicit_deny_rule"],
            )

        # Check constraints
        checks_passed: list[str] = []
        checks_failed: list[str] = []

        # Path constraints (for file operations)
        path = arguments.get("path") or arguments.get("file_path")
        if path and constraints:
            allowlist = constraints.get("path_allowlist", [])
            denylist = constraints.get("path_denylist", [])

            try:
                canonical = self._resolve_path(str(path))

                # Log raw argument for audit (hash it separately)
                logger.debug(
                    "Path check: raw=%s canonical=%s", str(path)[:100], canonical
                )

                if denylist:
                    if self._path_matches_patterns(canonical, denylist):
                        checks_failed.append("path_blocked_by_denylist")
                    else:
                        checks_passed.append("path_not_in_denylist")

                if allowlist and not checks_failed:
                    if self._path_matches_patterns(canonical, allowlist):
                        checks_passed.append("path_in_allowlist")
                    else:
                        checks_failed.append("path_not_in_allowlist")

            except ValueError as e:
                checks_failed.append(f"path_unresolvable: {e}")

        # Command constraints (for shell operations)
        command = arguments.get("command")
        if command and constraints:
            blocked = constraints.get("blocked_commands", [])
            if any(fnmatch.fnmatch(command, pattern) for pattern in blocked):
                checks_failed.append("command_blocked")
            else:
                checks_passed.append("command_not_blocked")

        if checks_failed:
            return PolicyResult(
                allowed=False,
                reason=f"constraint_violation: {', '.join(checks_failed)}",
                policy_version=self.version,
                checks_passed=checks_passed or None,
                checks_failed=checks_failed,
            )

        return PolicyResult(
            allowed=True,
            reason="all_constraints_passed",
            policy_version=self.version,
            checks_passed=checks_passed or ["no_constraints_applied"],
        )
