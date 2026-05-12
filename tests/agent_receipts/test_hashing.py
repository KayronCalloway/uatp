import re
from datetime import datetime, timezone

import pytest

from src.agent_receipts.events import SessionStarted
from src.agent_receipts.hashing import (
    canonical_json,
    canonical_json_bytes,
    sha256_digest,
)


def test_canonical_json_returns_sorted_key_compact_json_string() -> None:
    value = {"zeta": 1, "alpha": {"beta": True}, "none": None}

    assert canonical_json(value) == '{"alpha":{"beta":true},"none":null,"zeta":1}'


def test_canonical_json_bytes_returns_utf8_bytes() -> None:
    value = {"text": "café"}

    assert canonical_json_bytes(value) == b'{"text":"caf\xc3\xa9"}'


def test_sha256_digest_returns_known_prefixed_lowercase_hex_digest() -> None:
    digest = sha256_digest({"alpha": 1})

    assert (
        digest
        == "sha256:84223d7f45b87d9420493438c0e8ce663665e63c5a55d457816228998db00d59"
    )
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)


def test_digest_is_stable_across_dict_key_order() -> None:
    left = {"alpha": 1, "zeta": {"a": 2, "b": 3}}
    right = {"zeta": {"b": 3, "a": 2}, "alpha": 1}

    assert sha256_digest(left) == sha256_digest(right)


def test_changed_nested_value_changes_digest() -> None:
    original = {"outer": {"inner": "before"}}
    changed = {"outer": {"inner": "after"}}

    assert sha256_digest(original) != sha256_digest(changed)


def test_list_order_changes_digest() -> None:
    assert sha256_digest(["first", "second"]) != sha256_digest(["second", "first"])


class UnsupportedValue:
    pass


def test_unsupported_object_raises_type_error_with_type_name() -> None:
    with pytest.raises(TypeError, match="UnsupportedValue"):
        canonical_json({"unsupported": UnsupportedValue()})


def test_non_string_dict_key_raises_clear_type_error() -> None:
    with pytest.raises(TypeError, match="dict key must be str, got int"):
        canonical_json({1: "one"})


def test_nested_non_string_dict_key_raises_clear_type_error() -> None:
    with pytest.raises(TypeError, match="dict key must be str, got tuple"):
        canonical_json({"outer": {("bad",): "value"}})


def test_non_finite_float_raises_clear_type_error() -> None:
    with pytest.raises(TypeError, match="not JSON canonicalizable"):
        canonical_json({"value": float("nan")})


def test_raw_datetime_raises_type_error() -> None:
    with pytest.raises(TypeError, match="datetime"):
        canonical_json({"timestamp": datetime(2026, 5, 8, 21, 10, tzinfo=timezone.utc)})


def test_session_started_to_dict_output_hashes_because_timestamp_is_iso_string() -> (
    None
):
    event = SessionStarted(
        event_id="evt_001",
        session_id="sess_001",
        adapter_name="hermes",
        agent_name="Hermes Agent",
        timestamp=datetime(2026, 5, 8, 21, 10, tzinfo=timezone.utc),
        parent_event_hash=None,
        actor="assistant",
        payload={"task": "capture"},
        redaction_summary={"secrets_removed": 0},
        trust_level="local",
    )

    digest = sha256_digest(event.to_dict())

    assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
