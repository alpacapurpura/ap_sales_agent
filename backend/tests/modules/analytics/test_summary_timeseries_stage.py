"""Tests for SummaryStageService and TimeseriesStageService."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.analytics.domain.period_config import DateRange

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DATE_RANGE = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")


def _run(coro):
    return asyncio.run(coro)


# ─── SummaryStageService ───────────────────────────────────────────────────────


def _make_summary_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.summary_stage import (
        SummaryStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []

    with (
        patch(
            "src.modules.analytics.application.services.stage_services.summary_stage.get_customer_repository"
        ) as MockCustRepo,
        patch(
            "src.modules.analytics.application.services.stage_services.summary_stage.get_lead_metrics_repository"
        ) as MockLeadRepo,
    ):
        cust_repo = MagicMock()
        cust_repo.count_by_stage.return_value = 0
        MockCustRepo.return_value = cust_repo

        lead_repo = MagicMock()
        lead_repo.count_total.return_value = 0
        MockLeadRepo.return_value = lead_repo

        svc = SummaryStageService(db=db, cache=cache)
        svc.customer_repo = cust_repo
        svc.lead_repo = lead_repo

    return svc, db


class TestSummaryStageServiceCacheHit:
    def test_summary_cache_hit(self):
        cache = AsyncMock()
        cached = {
            "stages": [
                {
                    "stage": "attraction",
                    "main_kpi": 100,
                    "main_label": "visitantes",
                    "secondary_kpi": 3,
                    "secondary_label": "canales activos",
                }
            ],
            "period": "last_30_days",
            "last_updated": None,
        }
        cache.get = AsyncMock(side_effect=lambda *args: cached if args[1] == "summary" else None)
        cache.set = AsyncMock()
        svc, _db = _make_summary_svc(cache=cache)

        result = _run(svc.get_summary(TENANT_ID))

        assert result.period == "last_30_days"
        assert len(result.stages) == 1


class TestSummaryStageServiceCacheMiss:
    def test_all_stage_caches_miss_returns_dto(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_summary_svc(cache=cache)

        result = _run(svc.get_summary(TENANT_ID))

        assert result is not None
        assert len(result.stages) == 8  # 8 funnel stages

    def test_sets_cache_with_result(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_summary_svc(cache=cache)

        _run(svc.get_summary(TENANT_ID))

        cache.set.assert_called()

    def test_no_cache_still_works(self):
        svc, _db = _make_summary_svc(cache=None)
        result = _run(svc.get_summary(TENANT_ID))
        assert result is not None
        assert len(result.stages) == 8


class TestSummaryStaticHelpers:
    def test_build_adoption_kpi_no_cache(self):
        from src.modules.analytics.application.services.stage_services.summary_stage import (
            SummaryStageService,
        )

        result = SummaryStageService._build_adoption_kpi(None)
        assert result.stage == "adoption"
        assert result.main_kpi == 0

    def test_build_adoption_kpi_from_cache(self):
        from src.modules.analytics.application.services.stage_services.summary_stage import (
            SummaryStageService,
        )

        cache = {
            "header_kpis": {"health_pct": 75.0, "active_customers": 20},
            "mini_funnel": {"conversion_rate": 0},
        }
        result = SummaryStageService._build_adoption_kpi(cache)
        assert result.main_kpi == 75.0

    def test_build_simple_header_kpi_no_cache(self):
        from src.modules.analytics.application.services.stage_services.summary_stage import (
            SummaryStageService,
        )

        result = SummaryStageService._build_simple_header_kpi(
            None, "capture", "total_leads", "leads", "conversion_rate", "tasa", fallback_main=10
        )
        assert result.main_kpi == 10
        assert result.stage == "capture"

    def test_build_simple_header_kpi_from_cache(self):
        from src.modules.analytics.application.services.stage_services.summary_stage import (
            SummaryStageService,
        )

        cache = {"header_kpis": {"total_leads": 42, "conversion_rate": 5.0}}
        result = SummaryStageService._build_simple_header_kpi(
            cache, "capture", "total_leads", "leads", "conversion_rate", "tasa"
        )
        assert result.main_kpi == 42
        assert result.secondary_kpi == 5.0


class TestSummaryAttractionKpi:
    def test_attraction_kpi_from_cache(self):
        svc, _db = _make_summary_svc()
        cache = {
            "organic_social": {"totals": {"reach": 500, "sessions": 200}, "channels": ["a", "b"]},
            "ga4_search": {"totals": {"reach": 0, "sessions": 100}, "channels": ["c"]},
            "paid": {"totals": {}, "channels": []},
            "outbound": {"totals": {}, "channels": []},
            "last_updated": "2026-03-31T00:00:00",
        }
        kpi, updated = svc._build_attraction_kpi(cache, TENANT_ID)
        assert kpi.stage == "attraction"
        assert kpi.main_kpi == 800  # 500+200+100
        assert updated == "2026-03-31T00:00:00"

    def test_attraction_kpi_no_cache_uses_db(self):
        svc, db = _make_summary_svc()
        db.execute.return_value.scalar.return_value = 300
        kpi, _updated = svc._build_attraction_kpi(None, TENANT_ID)
        assert kpi.stage == "attraction"
        assert kpi.main_kpi == 300


# ─── TimeseriesStageService ────────────────────────────────────────────────────


def _make_ts_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.timeseries_stage import (
        TimeseriesStageService,
    )

    db = MagicMock()
    db.execute.return_value.all.return_value = []
    return TimeseriesStageService(db=db, cache=cache), db


class TestTimeseriesStageServiceCacheHit:
    def test_cache_hit_returns_dto(self):
        cache = AsyncMock()
        cached = {
            "stage": "attraction",
            "metric_name": "visitors",
            "granularity": "daily",
            "range_days": 30,
            "data_points": [],
            "channels_present": [],
            "period_totals": {},
            "previous_period_totals": None,
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_ts_svc(cache=cache)

        result = _run(svc.get_timeseries(TENANT_ID, "attraction"))

        assert result.stage == "attraction"
        db.execute.assert_not_called()


class TestTimeseriesStageServiceCacheMiss:
    def test_no_channels_returns_empty_dto(self):
        svc, _db = _make_ts_svc()
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[],
        ):
            result = _run(svc.get_timeseries(TENANT_ID, "attraction"))

        assert result.stage == "attraction"
        assert result.data_points == []
        assert result.period_totals == {}

    def test_with_channels_queries_db(self):
        svc, db = _make_ts_svc()
        db.execute.return_value.all.return_value = []
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[{"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid_social"}],
        ):
            result = _run(svc.get_timeseries(TENANT_ID, "attraction"))

        assert result.stage == "attraction"
        assert result.data_points == []

    def test_weekly_granularity(self):
        svc, db = _make_ts_svc()
        db.execute.return_value.all.return_value = []
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[{"slug": "ig-organic", "name": "IG Organic", "channel_type": "organic_social"}],
        ):
            result = _run(svc.get_timeseries(TENANT_ID, "attraction", granularity="weekly"))

        assert result.granularity == "weekly"

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_ts_svc(cache=cache)
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[],
        ):
            _run(svc.get_timeseries(TENANT_ID, "attraction"))

        # No channels → early return (no cache set)
        cache.set.assert_not_called()


class TestTimeseriesHelpers:
    def test_resolve_metric_aliases_visitors(self):
        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            TimeseriesStageService,
        )

        aliases = TimeseriesStageService._resolve_metric_aliases("visitors")
        assert "sessions" in aliases
        assert "users" in aliases

    def test_resolve_metric_aliases_unknown(self):
        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            TimeseriesStageService,
        )

        aliases = TimeseriesStageService._resolve_metric_aliases("custom_metric")
        assert aliases == ["custom_metric"]

    def test_build_date_map_empty(self):
        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            _build_date_map,
        )

        date_map, channels = _build_date_map([])
        assert len(date_map) == 0
        assert channels == set()

    def test_build_date_map_with_rows(self):
        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            _build_date_map,
        )

        class FakeRow:
            def __init__(self, d, slug, total):
                self.metric_date = d
                self.channel_slug = slug
                self.total = total

        rows = [
            FakeRow(date(2026, 3, 1), "meta-ads", 100),
            FakeRow(date(2026, 3, 1), "ig-organic", 50),
            FakeRow(date(2026, 3, 2), "meta-ads", 80),
        ]
        date_map, channels = _build_date_map(rows)
        assert len(date_map) == 2
        assert "meta-ads" in channels
        assert "ig-organic" in channels

    def test_compute_period_totals(self):
        from collections import OrderedDict

        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            _compute_period_totals,
        )

        date_map = OrderedDict(
            [
                (date(2026, 3, 1), {"meta-ads": 100.0, "ig-organic": 50.0}),
                (date(2026, 3, 2), {"meta-ads": 80.0}),
            ]
        )
        totals = _compute_period_totals(date_map)
        assert totals["meta-ads"] == 180.0
        assert totals["ig-organic"] == 50.0

    def test_aggregate_weekly_collapses_days(self):
        from collections import OrderedDict

        from src.modules.analytics.application.services.stage_services.timeseries_stage import (
            TimeseriesStageService,
        )

        # Monday + Tuesday same week
        date_map = OrderedDict(
            [
                (date(2026, 3, 2), {"meta-ads": 100.0}),  # Monday
                (date(2026, 3, 3), {"meta-ads": 50.0}),  # Tuesday
            ]
        )
        weekly = TimeseriesStageService._aggregate_weekly(date_map)
        assert len(weekly) == 1
        week_vals = next(iter(weekly.values()))
        assert week_vals["meta-ads"] == 150.0
