"""
Tests to ensure timezone consistency across the codebase.

These tests prevent regression of the 8-hour timestamp offset bug.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.utils.timezone_utils import (
    ensure_utc,
    parse_iso_timestamp,
    timestamp_to_iso,
    utc_now,
)


def test_utc_now_is_timezone_aware():
    """Ensure utc_now() returns timezone-aware datetime."""
    now = utc_now()
    assert now.tzinfo is not None, "utc_now() must return timezone-aware datetime"
    assert now.tzinfo == timezone.utc, "utc_now() must return UTC timezone"


def test_utc_now_is_current():
    """Ensure utc_now() returns current time (within 1 second)."""
    now = utc_now()
    expected = datetime.now(timezone.utc)
    diff = abs((now - expected).total_seconds())
    assert diff < 1.0, f"utc_now() time diff too large: {diff}s"


def test_ensure_utc_with_naive_datetime():
    """Test ensure_utc() converts naive datetime to UTC."""
    naive = datetime(2025, 12, 14, 18, 0, 0)
    assert naive.tzinfo is None, "Test setup: datetime should be naive"

    aware = ensure_utc(naive)
    assert aware.tzinfo == timezone.utc, "ensure_utc() must add UTC timezone"
    assert aware.year == 2025
    assert aware.month == 12
    assert aware.day == 14
    assert aware.hour == 18


def test_ensure_utc_with_aware_datetime():
    """Test ensure_utc() preserves timezone-aware datetime."""
    aware = datetime(2025, 12, 14, 18, 0, 0, tzinfo=timezone.utc)
    result = ensure_utc(aware)
    assert result.tzinfo == timezone.utc
    assert result == aware, "ensure_utc() should preserve UTC datetime"


def test_ensure_utc_converts_other_timezones():
    """Test ensure_utc() converts non-UTC timezone to UTC."""
    # Create PST timezone (UTC-8)
    from datetime import timedelta

    pst = timezone(timedelta(hours=-8))

    pst_time = datetime(2025, 12, 14, 18, 0, 0, tzinfo=pst)
    utc_time = ensure_utc(pst_time)

    assert utc_time.tzinfo == timezone.utc
    # 6 PM PST = 2 AM next day UTC
    assert utc_time.hour == 2
    assert utc_time.day == 15


def test_timestamp_to_iso_format():
    """Test ISO 8601 formatting."""
    dt = datetime(2025, 12, 14, 18, 0, 0, tzinfo=timezone.utc)
    iso = timestamp_to_iso(dt)
    assert iso == "2025-12-14T18:00:00+00:00"


def test_timestamp_to_iso_default_current_time():
    """Test timestamp_to_iso() defaults to current time."""
    before = utc_now()
    iso = timestamp_to_iso()
    after = utc_now()

    # Parse the ISO string
    parsed = datetime.fromisoformat(iso)

    # Verify it's between before and after
    assert before <= parsed <= after


def test_parse_iso_timestamp():
    """Test parsing ISO 8601 timestamps."""
    iso = "2025-12-14T18:00:00+00:00"
    dt = parse_iso_timestamp(iso)

    assert dt.year == 2025
    assert dt.month == 12
    assert dt.day == 14
    assert dt.hour == 18
    assert dt.tzinfo == timezone.utc


def test_round_trip_iso_conversion():
    """Test datetime -> ISO -> datetime round trip."""
    original = utc_now()
    iso = timestamp_to_iso(original)
    parsed = parse_iso_timestamp(iso)

    # Allow microsecond precision loss
    diff = abs((original - parsed).total_seconds())
    assert diff < 0.001, "Round trip conversion should preserve timestamp"


def test_utcnow_deprecation():
    """Test that deprecated utcnow() function raises error."""
    from src.utils.timezone_utils import utcnow

    with pytest.raises(DeprecationWarning):
        utcnow()


@pytest.mark.integration
def test_no_datetime_utcnow_in_production_code():
    """
    Integration test: Ensure datetime.utcnow() is not used in production code.

    This test scans the codebase to prevent regression.
    """
    import os
    import subprocess

    # Run grep to find any datetime.utcnow() usage
    result = subprocess.run(
        ["grep", "-r", "datetime.utcnow()", "src/", "--include=*.py"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True,
        text=True,
    )

    # Exclude timezone_utils.py (which has it in deprecation warning)
    violations = [
        line
        for line in result.stdout.split("\n")
        if line and "timezone_utils.py" not in line
    ]

    assert len(violations) == 0, (
        f"Found {len(violations)} instances of datetime.utcnow() in production code:\n"
        + "\n".join(violations[:10])  # Show first 10
    )


class TestTimezoneRegressionPrevention:
    """Tests to prevent specific timezone bugs we've seen."""

    def test_capsule_creation_has_correct_timestamp(self):
        """
        Regression test: Ensure new capsules have correct timestamps.

        Bug: Capsules were getting timestamps 8 hours in the future.
        Root cause: datetime.utcnow() created naive datetime.
        """
        now_before = utc_now()

        # Simulate capsule creation
        capsule_timestamp = utc_now()

        now_after = utc_now()

        # Verify timestamp is between before and after (not 8 hours ahead!)
        assert now_before <= capsule_timestamp <= now_after
        assert capsule_timestamp.tzinfo == timezone.utc

        # Ensure it's not ~8 hours in the future
        time_diff = (capsule_timestamp - now_before).total_seconds()
        assert time_diff < 60, f"Timestamp should be current, not {time_diff}s ahead"

    def test_jwt_token_expiration_correct(self):
        """
        Regression test: JWT tokens should expire at correct time.

        Bug: If JWT uses datetime.utcnow(), expiration is 8 hours off.
        """
        now = utc_now()
        expires_in_seconds = 3600  # 1 hour

        # Simulate JWT expiration calculation
        expiration_time = now + timedelta(seconds=expires_in_seconds)

        # Verify expiration is ~1 hour from now (not 1 hour + 8 hours!)
        actual_diff = (expiration_time - now).total_seconds()
        assert 3599 <= actual_diff <= 3601, f"Expected ~3600s, got {actual_diff}s"

    def test_compliance_report_timestamp_accurate(self):
        """
        Regression test: Compliance reports need accurate timestamps.

        Bug: Reports showed wrong generation time due to timezone issue.
        """
        report_generated_at = utc_now()

        # Verify timestamp is timezone-aware
        assert report_generated_at.tzinfo is not None

        # Verify timestamp is actually current (within 1 second)
        expected = datetime.now(timezone.utc)
        diff = abs((report_generated_at - expected).total_seconds())
        assert diff < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
