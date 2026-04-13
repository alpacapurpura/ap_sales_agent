"""Centralized datetime utilities — replaces ad-hoc datetime.utcnow() usage.

Rules:
- Backend ALWAYS stores UTC.
- Frontend converts to tenant timezone for display.
- Use utc_now() instead of datetime.utcnow() (deprecated Python 3.12+).
- Use utc_today() instead of date.today() (timezone-naive).
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """Timezone-aware UTC now. Drop-in replacement for deprecated datetime.utcnow()."""
    return datetime.now(UTC)


def utc_today() -> date:
    """Today's date in UTC. Drop-in replacement for timezone-naive date.today()."""
    return datetime.now(UTC).date()


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
