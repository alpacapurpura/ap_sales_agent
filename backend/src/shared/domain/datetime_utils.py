"""Centralized datetime utilities — replaces ad-hoc datetime.utcnow() usage.

Rules:
- Backend ALWAYS stores UTC.
- Frontend converts to tenant timezone for display.
- Use utc_now() instead of datetime.utcnow() (deprecated Python 3.12+).
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Timezone-aware UTC now. Drop-in replacement for deprecated datetime.utcnow()."""
    return datetime.now(UTC)


def to_tenant_tz(dt: datetime, tz_name: str) -> datetime:
    """Convert a datetime to the tenant's local timezone for display.

    If the input is naive, it is assumed to be UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(tz_name))


def ensure_utc(dt: datetime) -> datetime:
    """Normalize any datetime to UTC.

    - Naive datetimes are assumed UTC (tzinfo added).
    - Aware datetimes are converted to UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def is_valid_timezone(tz_name: str) -> bool:
    """Check if a string is a valid IANA timezone identifier."""
    try:
        ZoneInfo(tz_name)
        return True
    except (KeyError, ValueError):
        return False
