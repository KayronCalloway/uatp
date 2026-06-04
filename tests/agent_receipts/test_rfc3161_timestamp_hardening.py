"""Fail-closed RFC3161 timestamp hardening tests."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pytest

from src.security import rfc3161_timestamps
from src.security.rfc3161_timestamps import RFC3161Timestamper, TimestampToken


def test_parse_timestamp_response_does_not_fallback_to_current_time(
    monkeypatch,
) -> None:
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    with pytest.raises(ValueError, match="could not parse RFC 3161 timestamp response"):
        timestamper._parse_timestamp_response(b"not a timestamp token")


def test_verify_timestamp_rejects_hash_only_verification(monkeypatch) -> None:
    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", False)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"not independently verified",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(token, data)

    assert valid is False
    assert "full RFC 3161 verification unavailable" in reason


def test_verify_timestamp_rejects_rfc3161_without_configured_tsa_trust_anchor(
    monkeypatch,
) -> None:
    class FakeRFC3161:
        @staticmethod
        def verify_timestamp(token_bytes, data):
            return None

    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", True)
    monkeypatch.setattr(rfc3161_timestamps, "rfc3161ng", FakeRFC3161)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"token with matching imprint",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(token, data)

    assert valid is False
    assert "TSA trust anchor verification not configured" in reason


def test_verify_timestamp_rejects_unused_tsa_trust_anchors(monkeypatch) -> None:
    class FakeRFC3161:
        @staticmethod
        def verify_timestamp(token_bytes, data):
            return None

    monkeypatch.setattr(rfc3161_timestamps, "RFC3161_AVAILABLE", True)
    monkeypatch.setattr(rfc3161_timestamps, "rfc3161ng", FakeRFC3161)
    data = b"timestamped manifest hash"
    token = TimestampToken(
        token_bytes=b"token with matching imprint",
        timestamp=datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc),
        tsa_name="freetsa",
        hash_algorithm="sha256",
        message_imprint=hashlib.sha256(data).hexdigest(),
    )
    timestamper = RFC3161Timestamper.__new__(RFC3161Timestamper)

    valid, reason = timestamper.verify_timestamp(
        token,
        data,
        trusted_tsa_certificates=(b"trusted cert not yet wired",),
    )

    assert valid is False
    assert "TSA trust-anchor validation is not implemented" in reason
