"""Deterministic canonical JSON hashing helpers."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

_JSON_SCALARS = (str, int, bool, type(None))


def _validate_canonical_json_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"dict key must be str, got {type(key).__name__}")
            _validate_canonical_json_value(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_canonical_json_value(item)
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError(f"float value {value!r} is not JSON canonicalizable")
        return
    if isinstance(value, _JSON_SCALARS):
        return
    raise TypeError(
        f"Value contains unsupported type for canonical JSON: {type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    """Return compact JSON with recursively sorted object keys."""
    _validate_canonical_json_value(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical JSON encoded as UTF-8 bytes."""
    return canonical_json(value).encode("utf-8")


def sha256_digest(value: Any) -> str:
    """Return the sha256:<hex> digest of canonical JSON bytes."""
    digest = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    return f"sha256:{digest}"
