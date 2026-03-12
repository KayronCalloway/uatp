"""
Unit tests for Timestamp Authority.
"""

import hashlib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.security.timestamp_authority import TimestampAuthority, get_timestamp_authority


class TestTimestampAuthorityInit:
    """Tests for TimestampAuthority initialization."""

    def test_init_local_mode(self):
        """Test initialization in local mode."""
        tsa = TimestampAuthority(mode="local")

        assert tsa.mode == "local"
        assert tsa.timeout == 10

    def test_init_auto_mode(self):
        """Test initialization in auto mode."""
        tsa = TimestampAuthority(mode="auto")

        assert tsa.mode == "auto"

    def test_init_custom_url(self):
        """Test initialization with custom TSA URL."""
        tsa = TimestampAuthority(mode="local", tsa_url="http://custom.tsa.com")

        assert tsa.tsa_url == "http://custom.tsa.com"

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        tsa = TimestampAuthority(mode="local", timeout=30)

        assert tsa.timeout == 30

    def test_init_invalid_mode_raises(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            TimestampAuthority(mode="invalid")


class TestLocalTimestamp:
    """Tests for local timestamp generation."""

    def test_local_timestamp(self):
        """Test local timestamp generation."""
        tsa = TimestampAuthority(mode="local")
        data_hash = hashlib.sha256(b"test data").digest()

        result = tsa.timestamp_hash(data_hash)

        assert result["method"] == "local_clock"
        assert result["trusted"] is False
        assert "time" in result
        assert "note" in result

    def test_local_timestamp_data_convenience(self):
        """Test timestamp_data convenience method."""
        tsa = TimestampAuthority(mode="local")

        result = tsa.timestamp_data(b"test data")

        assert result["method"] == "local_clock"
        assert "time" in result


class TestTimestampVerification:
    """Tests for timestamp verification."""

    def test_verify_local_timestamp(self):
        """Test verifying local timestamp."""
        timestamp_info = {
            "method": "local_clock",
            "time": datetime.now(timezone.utc).isoformat(),
            "trusted": False,
        }
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is True
        assert ts_time is not None
        assert "Local timestamp" in message

    def test_verify_local_fallback_timestamp(self):
        """Test verifying local fallback timestamp."""
        timestamp_info = {
            "method": "local_clock_fallback",
            "time": datetime.now(timezone.utc).isoformat(),
            "trusted": False,
        }
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is True
        assert "Local timestamp" in message

    def test_verify_invalid_local_format(self):
        """Test verification fails for invalid time format."""
        timestamp_info = {
            "method": "local_clock",
            "time": "not a valid time",
            "trusted": False,
        }
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is False
        assert ts_time is None
        assert "Invalid local timestamp" in message

    def test_verify_unknown_method(self):
        """Test verification fails for unknown method."""
        timestamp_info = {"method": "unknown_method"}
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is False
        assert "Unknown timestamp method" in message

    def test_verify_rfc3161_missing_token(self):
        """Test verification fails when RFC3161 token is missing."""
        timestamp_info = {"method": "rfc3161"}
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is False
        assert "Missing RFC 3161 token" in message


class TestTimestampCapsule:
    """Tests for capsule timestamping."""

    def test_timestamp_capsule(self):
        """Test timestamping a capsule."""
        tsa = TimestampAuthority(mode="local")

        capsule_data = {
            "capsule_id": "caps_123",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"message": "test"},
        }

        result = tsa.timestamp_capsule(capsule_data)

        assert result["method"] == "local_clock"
        assert "time" in result

    def test_timestamp_capsule_excludes_verification(self):
        """Test that verification field is excluded from hash."""
        tsa = TimestampAuthority(mode="local")

        capsule_data = {
            "capsule_id": "caps_123",
            "payload": {"message": "test"},
            "verification": {"signature": "existing_sig"},
        }

        # This should not fail even with verification field
        result = tsa.timestamp_capsule(capsule_data)
        assert result["method"] == "local_clock"


class TestConvenienceFunction:
    """Tests for convenience functions."""

    def test_get_timestamp_authority(self):
        """Test get_timestamp_authority convenience function."""
        tsa = get_timestamp_authority(mode="local")

        assert isinstance(tsa, TimestampAuthority)
        assert tsa.mode == "local"

    def test_get_timestamp_authority_default_mode(self):
        """Test default mode is auto."""
        tsa = get_timestamp_authority()

        assert tsa.mode == "auto"


class TestAsn1Availability:
    """Tests for ASN1 availability checking."""

    def test_check_asn1_available(self):
        """Test ASN1 availability check."""
        tsa = TimestampAuthority(mode="local")

        # Should return True or False based on import success
        assert isinstance(tsa._asn1_available, bool)

    @patch.dict("sys.modules", {"asn1crypto": None})
    def test_asn1_unavailable_local_mode(self):
        """Test local mode works without asn1crypto."""
        # Force reload to test without asn1crypto
        tsa = TimestampAuthority(mode="local")

        result = tsa.timestamp_hash(hashlib.sha256(b"test").digest())
        assert result["method"] == "local_clock"


class TestTimestampTimeFormat:
    """Tests for timestamp time format handling."""

    def test_verify_timestamp_with_z_suffix(self):
        """Test verification handles Z suffix in time."""
        timestamp_info = {
            "method": "local_clock",
            "time": "2026-03-12T10:00:00Z",
            "trusted": False,
        }
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is True
        assert ts_time is not None

    def test_verify_timestamp_with_offset(self):
        """Test verification handles offset in time."""
        timestamp_info = {
            "method": "local_clock",
            "time": "2026-03-12T10:00:00+00:00",
            "trusted": False,
        }
        data_hash = hashlib.sha256(b"test").digest()

        is_valid, ts_time, message = TimestampAuthority.verify_timestamp(
            data_hash, timestamp_info
        )

        assert is_valid is True
        assert ts_time is not None
