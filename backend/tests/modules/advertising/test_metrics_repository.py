"""Tests for advertising MetricsRepository helpers.

Focus: timezone-aware `resolve_period_window`. Ensures tenants far from
UTC get the correct "today" date and invalid timezones fall back to UTC
without crashing.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.modules.advertising.infrastructure.repositories import metrics_repository
from src.modules.advertising.infrastructure.repositories.metrics_repository import (
    resolve_period_window,
)


class TestResolvePeriodWindow:
    def test_30d_utc_returns_today_minus_29(self) -> None:
        start, end = resolve_period_window("30d", tz="UTC")
        assert end - start == timedelta(days=29)

    def test_7d_window(self) -> None:
        start, end = resolve_period_window("7d", tz="UTC")
        assert end - start == timedelta(days=6)

    def test_90d_window(self) -> None:
        start, end = resolve_period_window("90d", tz="UTC")
        assert end - start == timedelta(days=89)

    def test_unknown_period_defaults_to_30d(self) -> None:
        start, end = resolve_period_window("foo", tz="UTC")
        assert end - start == timedelta(days=29)

    def test_lima_vs_utc_differs_at_midnight_boundary(self) -> None:
        """Near UTC midnight, America/Lima (UTC-5) is still the prior day.

        Freeze the clock at 2026-03-15 02:00 UTC. In UTC that's the 15th.
        In Lima (UTC-5) that's still 2026-03-14 21:00. A 30-day window
        from Lima ends on the 14th, from UTC on the 15th.
        """
        frozen = datetime(2026, 3, 15, 2, 0, tzinfo=ZoneInfo("UTC"))

        class _FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                return frozen.astimezone(tz) if tz else frozen

        with patch.object(metrics_repository, "datetime", _FakeDatetime):
            _lima_start, lima_end = resolve_period_window("30d", tz="America/Lima")
            _utc_start, utc_end = resolve_period_window("30d", tz="UTC")

        assert lima_end == date(2026, 3, 14)
        assert utc_end == date(2026, 3, 15)
        assert lima_end != utc_end

    def test_invalid_timezone_falls_back_to_utc(self) -> None:
        # Should not raise; should return a valid tuple equivalent to UTC.
        start, end = resolve_period_window("30d", tz="invalid/TZ")
        utc_start, utc_end = resolve_period_window("30d", tz="UTC")
        # Equal windows — both fell to UTC.
        assert (start, end) == (utc_start, utc_end)

    def test_empty_timezone_falls_back_to_utc(self) -> None:
        start, end = resolve_period_window("7d", tz="")
        utc_start, utc_end = resolve_period_window("7d", tz="UTC")
        assert (start, end) == (utc_start, utc_end)
