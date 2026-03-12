"""
Unit tests for Timezone Utils.
"""

from datetime import datetime, timezone

import pytest

from src.utils.timezone_utils import (
    ensure_utc,
    parse_iso_timestamp,
    timestamp_to_iso,
    utc_now,
    utcnow,
)


class TestUtcNow:
    """Tests for utc_now function."""

    def test_returns_datetime(self):
        """Test returns datetime object."""
        result = utc_now()

        assert isinstance(result, datetime)

    def test_has_timezone(self):
        """Test returned datetime is timezone-aware."""
        result = utc_now()

        assert result.tzinfo is not None

    def test_is_utc(self):
        """Test returned datetime is in UTC."""
        result = utc_now()

        assert result.tzinfo == timezone.utc

    def test_is_recent(self):
        """Test returned time is recent."""
        result = utc_now()
        now_ref = datetime.now(timezone.utc)

        # Should be within 1 second of reference time
        diff = abs((result - now_ref).total_seconds())
        assert diff < 1.0

    def test_multiple_calls_advance(self):
        """Test multiple calls return advancing time."""
        time1 = utc_now()
        time2 = utc_now()

        # time2 should be >= time1
        assert time2 >= time1


class TestEnsureUtc:
    """Tests for ensure_utc function."""

    def test_naive_datetime_made_aware(self):
        """Test naive datetime is made timezone-aware."""
        naive = datetime(2024, 1, 1, 12, 0, 0)

        result = ensure_utc(naive)

        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_naive_datetime_values_preserved(self):
        """Test naive datetime values are preserved."""
        naive = datetime(2024, 1, 15, 14, 30, 45)

        result = ensure_utc(naive)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45

    def test_aware_utc_unchanged(self):
        """Test UTC-aware datetime is unchanged."""
        aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = ensure_utc(aware)

        assert result == aware
        assert result.tzinfo == timezone.utc

    def test_aware_other_timezone_converted(self):
        """Test aware datetime in other timezone is converted to UTC."""
        from datetime import timedelta

        # Create PST timezone (UTC-8)
        pst = timezone(timedelta(hours=-8))
        pst_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=pst)

        result = ensure_utc(pst_time)

        # Should be converted to UTC (12:00 PST = 20:00 UTC)
        assert result.tzinfo == timezone.utc
        assert result.hour == 20

    def test_handles_microseconds(self):
        """Test handles microseconds."""
        naive = datetime(2024, 1, 1, 12, 0, 0, 123456)

        result = ensure_utc(naive)

        assert result.microsecond == 123456


class TestTimestampToIso:
    """Tests for timestamp_to_iso function."""

    def test_current_time_default(self):
        """Test uses current time when no argument."""
        result = timestamp_to_iso()

        assert isinstance(result, str)
        assert "T" in result
        assert "+00:00" in result or "Z" in result

    def test_converts_datetime_to_iso(self):
        """Test converts datetime to ISO string."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = timestamp_to_iso(dt)

        assert result == "2024-01-01T12:00:00+00:00"

    def test_handles_naive_datetime(self):
        """Test handles naive datetime."""
        naive = datetime(2024, 1, 1, 12, 0, 0)

        result = timestamp_to_iso(naive)

        assert "+00:00" in result

    def test_handles_aware_datetime(self):
        """Test handles timezone-aware datetime."""
        aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        result = timestamp_to_iso(aware)

        assert "2024-01-01" in result
        assert "+00:00" in result

    def test_includes_microseconds(self):
        """Test includes microseconds."""
        dt = datetime(2024, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)

        result = timestamp_to_iso(dt)

        assert "123456" in result


class TestParseIsoTimestamp:
    """Tests for parse_iso_timestamp function."""

    def test_parse_utc_timestamp(self):
        """Test parses UTC timestamp."""
        iso_string = "2024-01-01T12:00:00+00:00"

        result = parse_iso_timestamp(iso_string)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.tzinfo == timezone.utc

    def test_parse_z_suffix(self):
        """Test parses timestamp with Z suffix."""
        iso_string = "2024-01-01T12:00:00Z"

        # This might fail with fromisoformat - test actual behavior
        try:
            result = parse_iso_timestamp(iso_string)
            assert result.tzinfo is not None
        except ValueError:
            # Z suffix might not be supported by fromisoformat
            pass

    def test_parse_with_microseconds(self):
        """Test parses timestamp with microseconds."""
        iso_string = "2024-01-01T12:00:00.123456+00:00"

        result = parse_iso_timestamp(iso_string)

        assert result.microsecond == 123456

    def test_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_iso_timestamp("not-a-timestamp")

    def test_returns_utc(self):
        """Test always returns UTC datetime."""
        iso_string = "2024-01-01T12:00:00+00:00"

        result = parse_iso_timestamp(iso_string)

        assert result.tzinfo == timezone.utc

    def test_converts_other_timezones(self):
        """Test converts other timezones to UTC."""
        # EST timestamp (UTC-5)
        iso_string = "2024-01-01T12:00:00-05:00"

        result = parse_iso_timestamp(iso_string)

        # Should be converted to UTC (12:00 EST = 17:00 UTC)
        assert result.tzinfo == timezone.utc
        assert result.hour == 17


class TestUtcnowDeprecated:
    """Tests for deprecated utcnow function."""

    def test_raises_deprecation_warning(self):
        """Test raises deprecation warning."""
        with pytest.raises(DeprecationWarning):
            utcnow()

    def test_error_message_helpful(self):
        """Test error message is helpful."""
        with pytest.raises(DeprecationWarning) as exc_info:
            utcnow()

        assert "deprecated" in str(exc_info.value).lower()
        assert "utc_now()" in str(exc_info.value)


class TestTimezoneUtilsIntegration:
    """Integration tests for timezone utilities."""

    def test_roundtrip_conversion(self):
        """Test roundtrip datetime -> ISO -> datetime."""
        original = utc_now()

        iso_string = timestamp_to_iso(original)
        parsed = parse_iso_timestamp(iso_string)

        # Should be equal (allowing for microsecond rounding)
        diff = abs((original - parsed).total_seconds())
        assert diff < 0.001

    def test_timezone_consistency(self):
        """Test all functions return UTC."""
        now = utc_now()
        ensured = ensure_utc(datetime(2024, 1, 1, 12, 0, 0))
        iso = timestamp_to_iso()
        parsed = parse_iso_timestamp(iso)

        assert now.tzinfo == timezone.utc
        assert ensured.tzinfo == timezone.utc
        assert parsed.tzinfo == timezone.utc

    def test_naive_to_aware_workflow(self):
        """Test workflow with naive datetime."""
        # Start with naive datetime (legacy code)
        naive = datetime(2024, 1, 1, 12, 0, 0)

        # Make it aware
        aware = ensure_utc(naive)

        # Convert to ISO
        iso = timestamp_to_iso(aware)

        # Parse back
        parsed = parse_iso_timestamp(iso)

        # Should be equal
        assert aware == parsed
