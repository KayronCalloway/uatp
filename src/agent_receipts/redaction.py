"""Shared redaction helpers for framework-neutral agent receipts."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = ("token", "secret", "password", "api_key", "apikey", "auth")

_BEARER_RE = re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s'\"&]+)")
_KEY_ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|AUTH)[A-Z0-9_]*\s*=\s*)([^\s'\"&]+)"
)
_QUERY_SECRET_RE = re.compile(
    r"(?i)([?&](?:access_token|api[_-]?key|apikey|auth|password|secret|token)=)([^&#\s'\"]+)"
)


def is_sensitive_key(key: str) -> bool:
    """Return True when a mapping key conventionally carries secret material."""
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact_string(value: str) -> str:
    """Redact common inline secret patterns from free-form strings."""
    redacted = _BEARER_RE.sub(rf"\1{REDACTED}", value)
    redacted = _KEY_ASSIGNMENT_RE.sub(rf"\1{REDACTED}", redacted)
    return _QUERY_SECRET_RE.sub(rf"\1{REDACTED}", redacted)


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive mapping values and inline string secrets.

    The returned structure is detached from the input so callers can safely hash,
    preview, or persist the redacted value without mutating source evidence.
    """
    if isinstance(value, dict):
        return {
            key: REDACTED if is_sensitive_key(str(key)) else redact_value(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_value(child) for child in value]
    if isinstance(value, tuple):
        return [redact_value(child) for child in value]
    if isinstance(value, str):
        return redact_string(value)
    return deepcopy(value)


def redact_error_message(message: str | None, arguments: Any) -> str | None:
    """Redact a tool/action error message using argument values and string patterns."""
    if message is None:
        return None

    redacted = redact_string(message)
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            if is_sensitive_key(str(key)) and isinstance(value, str):
                redacted = redacted.replace(value, REDACTED)
    return redacted
