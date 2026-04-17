"""TenantPeriodConfig — pure value object for period boundary calculations.

Encapsulates all tenant-specific period logic (week start day, fiscal year)
so that ETL, aggregation, and API layers can compute consistent boundaries.

DateRange — resolved date range carrying both dates and the period key.
Used as the unified parameter for all stage service get_metrics() calls.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone


@dataclass(frozen=True)
class DateRange:
    """Resolved date range for a period — carries both dates and the period key.

    Attributes:
        start_date: First day of the range (inclusive).
        end_date: Last day of the range (inclusive).
        period_type: The period string used as cache key ("last_30_days", "weekly", etc.).

    """

    start_date: date
    end_date: date
    period_type: str

    @property
    def days(self) -> int:
        """Number of days in the range (inclusive)."""
        return (self.end_date - self.start_date).days + 1

    def to_datetime_range(self) -> tuple[datetime, datetime]:
        """Convert date boundaries to UTC datetimes (inclusive).

        Returns start at 00:00:00 UTC and end at 23:59:59.999999 UTC,
        suitable for CRM repos that filter on datetime columns.
        """
        return (
            datetime.combine(self.start_date, time.min, tzinfo=timezone.utc),
            datetime.combine(self.end_date, time.max, tzinfo=timezone.utc),
        )


@dataclass(frozen=True)
class TenantPeriodConfig:
    """Tenant-specific period configuration.

    Attributes:
        weekly_start_day: 0=Monday, 1=Tuesday, ..., 6=Sunday (ISO weekday convention).
        fiscal_year_start_month: Month (1-12) when the fiscal year begins.
        fiscal_year_start_day: Day of month when the fiscal year begins.

    """

    weekly_start_day: int = 0  # Monday (ISO default)
    fiscal_year_start_month: int = 1  # January
    fiscal_year_start_day: int = 1

    def get_week_boundaries(self, d: date) -> tuple[date, date]:
        """Return (week_start, week_end) for the week containing ``d``."""
        days_since_start = (d.weekday() - self.weekly_start_day) % 7
        week_start = d - timedelta(days=days_since_start)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    def get_month_boundaries(self, d: date) -> tuple[date, date]:
        """Return (first day, last day) of the calendar month containing ``d``."""
        month_start = d.replace(day=1)
        last_day = calendar.monthrange(d.year, d.month)[1]
        month_end = d.replace(day=last_day)
        return month_start, month_end

    def get_quarter_boundaries(self, d: date) -> tuple[date, date]:
        """Return (quarter_start, quarter_end) according to the fiscal year config."""
        q = self.get_quarter_number(d)
        # Quarter start month relative to fiscal year
        offset_months = (q - 1) * 3

        # Determine fiscal year that contains this date
        fy_start = self._fiscal_year_start_for(d)
        q_start = date(fy_start.year, fy_start.month, 1)
        # Advance by offset_months
        for _ in range(offset_months):
            q_start = _next_month(q_start)

        q_end = q_start
        for _ in range(2):
            q_end = _next_month(q_end)
        last_day = calendar.monthrange(q_end.year, q_end.month)[1]
        q_end = q_end.replace(day=last_day)

        return q_start, q_end

    def get_quarter_number(self, d: date) -> int:
        """Return quarter number (1-4) relative to the fiscal year start."""
        fy_start = self._fiscal_year_start_for(d)
        months_since = (d.year - fy_start.year) * 12 + (d.month - fy_start.month)
        return (months_since // 3) + 1

    def resolve_period(self, period_type: str, today: date) -> DateRange:
        """Convert a period string to a concrete DateRange.

        Args:
            period_type: One of "last_30_days", "weekly", "monthly", "quarterly".
            today: Reference date. Callers pass ``utc_today()`` from
                   ``shared.domain.datetime_utils`` — domain layer takes it as
                   a parameter to stay framework-free.

        Returns:
            DateRange with resolved start/end dates and the period_type key.

        Raises:
            ValueError: If ``period_type`` is not recognized.

        """
        if period_type == "last_30_days":
            return DateRange(today - timedelta(days=29), today, period_type)
        if period_type == "weekly":
            s, e = self.get_week_boundaries(today)
            return DateRange(s, e, period_type)
        if period_type == "monthly":
            s, e = self.get_month_boundaries(today)
            return DateRange(s, e, period_type)
        if period_type == "quarterly":
            s, e = self.get_quarter_boundaries(today)
            return DateRange(s, e, period_type)

        msg = f"Unknown period_type: {period_type!r}"
        raise ValueError(msg)

    def is_period_boundary(self, d: date, period_type: str) -> bool:
        """Return True if ``d`` is the last day of the given period type."""
        if period_type == "weekly":
            _, we = self.get_week_boundaries(d)
            return d == we
        if period_type == "monthly":
            _, me = self.get_month_boundaries(d)
            return d == me
        if period_type == "quarterly":
            _, qe = self.get_quarter_boundaries(d)
            return d == qe
        return False

    def compute_period_keys(self, d: date) -> dict:
        """Return period key columns for a given date.

        Returns:
            {"iso_week_start": date, "month_key": "YYYY-MM", "quarter_key": "YYYY-QN"}

        """
        ws, _ = self.get_week_boundaries(d)
        return {
            "iso_week_start": ws,
            "month_key": d.strftime("%Y-%m"),
            "quarter_key": f"{d.year}-Q{self.get_quarter_number(d)}",
        }

    def _fiscal_year_start_for(self, d: date) -> date:
        """Return the fiscal year start date that contains ``d``."""
        fy_start_this_year = date(
            d.year,
            self.fiscal_year_start_month,
            self.fiscal_year_start_day,
        )
        if d >= fy_start_this_year:
            return fy_start_this_year
        return date(
            d.year - 1,
            self.fiscal_year_start_month,
            self.fiscal_year_start_day,
        )


def _next_month(d: date) -> date:
    """Advance ``d`` to the first day of the next month."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)
