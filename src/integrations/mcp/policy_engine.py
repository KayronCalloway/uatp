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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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

            # Normalize path for matching
            normalized = str(path).replace("~", "/home/user")

            if denylist:
                matched = any(
                    fnmatch.fnmatch(normalized, pattern) for pattern in denylist
                )
                if matched:
                    checks_failed.append("path_blocked_by_denylist")
                else:
                    checks_passed.append("path_not_in_denylist")

            if allowlist and not checks_failed:
                matched = any(
                    fnmatch.fnmatch(normalized, pattern) for pattern in allowlist
                )
                if matched:
                    checks_passed.append("path_in_allowlist")
                else:
                    checks_failed.append("path_not_in_allowlist")

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
