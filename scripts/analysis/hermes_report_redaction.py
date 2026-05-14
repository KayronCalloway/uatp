"""Redaction helpers for capsule learning reports."""

from __future__ import annotations

import re

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key\s*=\s*)\S+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(token\s*[=:]\s*)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(jwt\s*=\s*)\S+"),
    re.compile(r"(?i)(signing[_-]?(seed|key)\s*=\s*)\S+"),
)
CONNECTION_RE = re.compile(r"\b(postgresql|postgres|mysql|mongodb)://[^\s)]+")
KAY_PATH_RE = re.compile(r"/Users/kay/")


def redact_report_text(text: str) -> str:
    redacted = text or ""
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
    redacted = CONNECTION_RE.sub(
        lambda match: f"{match.group(1)}://[REDACTED]", redacted
    )
    redacted = KAY_PATH_RE.sub("", redacted)
    return redacted


def redact_report_payload(value: object) -> object:
    """Recursively redact strings in report payloads before serialization."""
    if isinstance(value, str):
        return redact_report_text(value)
    if isinstance(value, list):
        return [redact_report_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_report_payload(item) for item in value)
    if isinstance(value, dict):
        return {
            redact_report_text(str(key))
            if isinstance(key, str)
            else key: redact_report_payload(item)
            for key, item in value.items()
        }
    return value
