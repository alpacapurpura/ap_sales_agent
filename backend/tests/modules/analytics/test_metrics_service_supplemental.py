"""Supplemental tests for MetricsService — covering uncovered lines."""

import asyncio
import uuid
from collections import OrderedDict
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _run(coro):
    return asyncio.run(coro)


def _make_svc(cache=None, db=None):
    from luana_core_analytics_engine.application.services.metrics_service import MetricsService

    db = db or MagicMock()
    return MetricsService(db=db, cache=cache)


# ─── _compute_period_totals (module-level function) ───────────────────────────


class TestComputePeriodTotals:
    def test_empty_returns_empty(self):
        from luana_core_analytics_engine.application.services.metrics_service import _compute_period_totals

        assert _compute_period_totals({}) == {}

    def test_single_date_single_channel(self):
        from luana_core_analytics_engine.application.services.metrics_service import _compute_period_totals

        d = date(2026, 3, 1)
        result = _compute_period_totals({d: {"ig-organic": 100.0}})
        assert result == {"ig-organic": 100.0}

    def test_multiple_dates_same_channel_summed(self):
        from luana_core_analytics_engine.application.services.metrics_service import _compute_period_totals

        d1, d2 = date(2026, 3, 1), date(2026, 3, 2)
        date_map = {d1: {"ig-organic": 100.0}, d2: {"ig-organic": 200.0}}
        result = _compute_period_totals(date_map)
        assert result["ig-organic"] == 300.0

    def test_multiple_channels_accumulated(self):
        from luana_core_analytics_engine.application.services.metrics_service import _compute_period_totals

        d = date(2026, 3, 1)
        date_map = {d: {"ig-organic": 100.0, "fb-organic": 50.0}}
        result = _compute_period_totals(date_map)
        assert result["ig-organic"] == 100.0
        assert result["fb-organic"] == 50.0


# ─── _build_date_map (static method) ─────────────────────────────────────────


class TestBuildDateMap:
    def _make_row(self, metric_date, channel_slug, total):
        row = MagicMock()
        row.metric_date = metric_date
        row.channel_slug = channel_slug
        row.total = total
        return row

    def test_empty_rows_returns_empty(self):
        from luana_core_analytics_engine.application.services.metrics_service import MetricsService

        date_map, channels = MetricsService._build_date_map([], "daily")
        assert len(date_map) == 0
        assert len(channels) == 0

    def test_daily_groups_by_date(self):
        from luana_core_analytics_engine.application.services.metrics_service import MetricsService

        d1, d2 = date(2026, 3, 1), date(2026, 3, 2)
        rows = [
            self._make_row(d1, "ig-organic", 100),
            self._make_row(d2, "ig-organic", 200),
        ]
        date_map, channels = MetricsService._build_date_map(rows, "daily")
        assert len(date_map) == 2
        assert "ig-organic" in channels

    def test_weekly_aggregates_to_week_start(self):
        from luana_core_analytics_engine.application.services.metrics_service import MetricsService

        # Wednesday Mar 5, 2026 → week starts Monday Mar 3, 2026
        d_wed = date(2026, 3, 5)
        d_thu = date(2026, 3, 6)
        rows = [
            self._make_row(d_wed, "ig-organic", 100),
            self._make_row(d_thu, "ig-organic", 200),
        ]
        date_map, _ = MetricsService._build_date_map(rows, "weekly")
        # Both dates fall in same week (Mon Mar 3)
        assert len(date_map) == 1
        week_start = next(iter(date_map.keys()))
        assert week_start == date(2026, 3, 2)  # Mon of that week
        assert date_map[week_start]["ig-organic"] == 300.0

    def test_weekly_different_weeks_separate(self):
        from luana_core_analytics_engine.application.services.metrics_service import MetricsService

        # Mon Mar 2 = week 1, Mon Mar 9 = week 2
        d1 = date(2026, 3, 2)  # Monday
        d2 = date(2026, 3, 9)  # Monday
        rows = [
            self._make_row(d1, "ig-organic", 100),
            self._make_row(d2, "ig-organic", 150),
        ]
        date_map, _ = MetricsService._build_date_map(rows, "weekly")
        assert len(date_map) == 2

    def test_daily_duplicate_slug_on_same_date_accumulated(self):
        from luana_core_analytics_engine.application.services.metrics_service import MetricsService

        d = date(2026, 3, 1)
        rows = [
            self._make_row(d, "ig-organic", 100),
            self._make_row(d, "ig-organic", 50),
        ]
        date_map, _ = MetricsService._build_date_map(rows, "daily")
        assert date_map[d]["ig-organic"] == 150.0


# ─── _query_previous_period_totals ────────────────────────────────────────────


class TestQueryPreviousPeriodTotals:
    def test_returns_none_when_empty(self):
        svc = _make_svc()
        svc.db.execute.return_value.all.return_value = []
        result = svc._query_previous_period_totals(
            TENANT_ID,
            ["ig-organic"],
            ["reach"],
            date(2026, 2, 1),
            date(2026, 3, 1),
        )
        assert result is None

    def test_returns_dict_when_rows_present(self):
        svc = _make_svc()
        row = MagicMock()
        row.channel_slug = "ig-organic"
        row.total = 500.0
        svc.db.execute.return_value.all.return_value = [row]
        result = svc._query_previous_period_totals(
            TENANT_ID,
            ["ig-organic"],
            ["reach"],
            date(2026, 2, 1),
            date(2026, 3, 1),
        )
        assert result is not None
        assert result["ig-organic"] == 500.0

    def test_multiple_channels_in_result(self):
        svc = _make_svc()
        rows = []
        for slug, total in [("ig-organic", 100.0), ("fb-organic", 200.0)]:
            row = MagicMock()
            row.channel_slug = slug
            row.total = total
            rows.append(row)
        svc.db.execute.return_value.all.return_value = rows
        result = svc._query_previous_period_totals(
            TENANT_ID,
            ["ig-organic", "fb-organic"],
            ["reach"],
            date(2026, 2, 1),
            date(2026, 3, 1),
        )
        assert result["ig-organic"] == 100.0
        assert result["fb-organic"] == 200.0
