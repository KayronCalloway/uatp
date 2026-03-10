"""
Centralized timezone utilities for UATP Capsule Engine.

POLICY: All timestamps MUST be timezone-aware UTC.
Never use datetime.utcnow() - it creates naive datetimes that cause 8-hour offsets.

Author: UATP Engineering Team
Date: 2025-12-14
Issue: Fixed systemic timezone bug (97 instances of datetime.utcnow())
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Use this instead of datetime.utcnow() or datetime.now().

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> from src.utils.timezone_utils import utc_now
        >>> timestamp = utc_now()
        >>> assert timestamp.tzinfo is not None  # Always has timezone
        >>> print(timestamp.isoformat())
        '2025-12-14T18:30:45+00:00'

    Note:
        This function replaces datetime.utcnow() which creates naive datetimes.
        Naive datetimes are interpreted as local time by PostgreSQL, causing
        incorrect timestamps (8 hours off in PST timezone).
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.

    Args:
        dt: Datetime object (naive or aware)

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> from datetime import datetime
        >>> naive = datetime(2025, 12, 14, 18, 0, 0)
        >>> aware = ensure_utc(naive)
        >>> aware.tzinfo
        datetime.timezone.utc

    Note:
        If given a naive datetime, assumes it represents UTC time.
        In stricter implementations, you might raise an error instead.
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC and make it aware
        return dt.replace(tzinfo=timezone.utc)

    # Already aware - convert to UTC if needed
    return dt.astimezone(timezone.utc)


def timestamp_to_iso(dt: Optional[datetime] = None) -> str:
    """
    Convert datetime to ISO 8601 string in UTC.

    Args:
        dt: Datetime to convert (defaults to current time)

    Returns:
        ISO 8601 formatted string with UTC timezone

    Example:
        >>> timestamp_to_iso()
        '2025-12-14T18:30:45+00:00'
        >>> dt = datetime(2025, 12, 14, 10, 30, 0, tzinfo=timezone.utc)
        >>> timestamp_to_iso(dt)
        '2025-12-14T10:30:00+00:00'
    """
    if dt is None:
        dt = utc_now()
    return ensure_utc(dt).isoformat()


def parse_iso_timestamp(iso_string: str) -> datetime:
    """
    Parse ISO 8601 timestamp string to timezone-aware datetime.

    Args:
        iso_string: ISO 8601 formatted timestamp

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> parse_iso_timestamp('2025-12-14T18:30:45+00:00')
        datetime.datetime(2025, 12, 14, 18, 30, 45, tzinfo=datetime.timezone.utc)

    Raises:
        ValueError: If string is not valid ISO 8601 format
    """
    dt = datetime.fromisoformat(iso_string)
    return ensure_utc(dt)


# Deprecated warning if anyone tries to use old pattern
def utcnow():
    """
    DEPRECATED: This function is deprecated.

    Use utc_now() instead to get timezone-aware UTC datetime.

    Raises:
        DeprecationWarning: Always raised to prevent usage
    """
    raise DeprecationWarning(
        "datetime.utcnow() is deprecated. "
        "Use src.utils.timezone_utils.utc_now() instead. "
        "See TIMEZONE_FIX_PLAN.md for details."
    )
