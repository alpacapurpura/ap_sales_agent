"""Tests for MetricsService main entrypoints."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _run(coro):
    return asyncio.run(coro)


def _make_svc(cache=None):
    from src.modules.analytics.application.services.metrics_service import MetricsService

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []

    with (
        patch("src.modules.analytics.application.services.metrics_service.get_journey_event_repository") as MockJourney,
        patch("src.modules.analytics.application.services.metrics_service.get_customer_repository") as MockCustomer,
        patch("src.modules.analytics.application.services.metrics_service.get_lead_metrics_repository") as MockLead,
    ):
        journey_repo = MagicMock()
        journey_repo.get_unique_visitors.return_value = 0

        customer_repo = MagicMock()
        customer_repo.count_by_stage.return_value = 0

        lead_repo = MagicMock()
        lead_repo.count_total.return_value = 0
        lead_repo.count_qualified.return_value = 0

        MockJourney.return_value = journey_repo
        MockCustomer.return_value = customer_repo
        MockLead.return_value = lead_repo

        svc = MetricsService(db=db, cache=cache)
        svc.journey_repo = journey_repo
        svc.customer_repo = customer_repo
        svc.lead_repo = lead_repo

    return svc, db


# ─── get_marketing_sankey_metrics ─────────────────────────────────────────────


class TestGetMarketingSankeyMetrics:
    def test_returns_nodes_and_links(self):
        svc, _db = _make_svc()
        result = svc.get_marketing_sankey_metrics(TENANT_ID)

        assert "nodes" in result
        assert "links" in result
        assert "raw_metrics" in result
        assert len(result["nodes"]) == 7
        assert len(result["links"]) == 6

    def test_zero_data_structure(self):
        svc, _db = _make_svc()
        svc.journey_repo.get_unique_visitors.return_value = 0
        svc.customer_repo.count_by_stage.return_value = 0
        svc.lead_repo.count_total.return_value = 0
        svc.lead_repo.count_qualified.return_value = 0

        result = svc.get_marketing_sankey_metrics(TENANT_ID)

        assert result["raw_metrics"]["visitors"] == 0
        assert result["raw_metrics"]["leads"] == 0

    def test_with_actual_counts(self):
        svc, _db = _make_svc()
        svc.journey_repo.get_unique_visitors.return_value = 1000
        svc.lead_repo.count_total.return_value = 50
        svc.lead_repo.count_qualified.return_value = 20
        svc.customer_repo.count_by_stage.side_effect = lambda tid, stage: {
            "MQL": 30,
            "SQL": 15,
            "OPPORTUNITY": 10,
            "CUSTOMER": 8,
            "EVANGELIST": 2,
        }.get(str(stage.value) if hasattr(stage, "value") else str(stage), 0)

        result = svc.get_marketing_sankey_metrics(TENANT_ID)

        assert result["raw_metrics"]["visitors"] == 1000
        assert result["raw_metrics"]["leads"] == 50

    def test_retention_is_40pct_of_customers(self):
        svc, _db = _make_svc()
        svc.customer_repo.count_by_stage.return_value = 10

        result = svc.get_marketing_sankey_metrics(TENANT_ID)
        # retention = int(customers * 0.4) = 4
        assert result["raw_metrics"]["retention"] == 4

    def test_qualified_uses_max_of_qualified_and_mql(self):
        svc, _db = _make_svc()
        svc.lead_repo.count_qualified.return_value = 5
        # count_by_stage called multiple times — first call (MQL) returns 10
        svc.customer_repo.count_by_stage.side_effect = [10, 0, 0, 0, 0]

        result = svc.get_marketing_sankey_metrics(TENANT_ID)
        assert result["raw_metrics"]["qualified"] == 10  # max(5, 10)


# ─── get_bowtie_summary ───────────────────────────────────────────────────────


class TestGetBowtiesSummary:
    def test_cache_hit_returns_dto(self):
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
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, _db = _make_svc(cache=cache)

        result = _run(svc.get_bowtie_summary(TENANT_ID))

        assert result.period == "last_30_days"

    def test_cache_miss_all_fallback(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_svc(cache=cache)
        svc.customer_repo.count_by_stage.return_value = 0
        svc.lead_repo.count_total.return_value = 0

        with patch(
            "src.modules.analytics.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
        ) as MockSales:
            MockSales.return_value.get_sales_summary.return_value = []
            result = _run(svc.get_bowtie_summary(TENANT_ID))

        assert len(result.stages) == 8
        cache.set.assert_called_once()

    def test_no_cache_returns_summary(self):
        svc, _db = _make_svc(cache=None)
        svc.customer_repo.count_by_stage.return_value = 0
        svc.lead_repo.count_total.return_value = 0

        with patch(
            "src.modules.analytics.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
        ) as MockSales:
            MockSales.return_value.get_sales_summary.return_value = []
            result = _run(svc.get_bowtie_summary(TENANT_ID))

        assert len(result.stages) == 8


# ─── KPI builder methods ──────────────────────────────────────────────────────


class TestKpiBuilders:
    def test_build_attraction_kpi_no_cache(self):
        svc, db = _make_svc()
        db.execute.return_value.scalar.return_value = 500
        kpi, updated = svc._build_attraction_kpi(TENANT_ID, None)
        assert kpi.stage == "attraction"
        assert kpi.main_kpi == 500
        assert updated is None

    def test_build_attraction_kpi_from_cache(self):
        svc, _db = _make_svc()
        cache_data = {
            "organic_social": {"totals": {"reach": 300, "sessions": 100}, "channels": ["a"]},
            "ga4_search": {"totals": {}, "channels": []},
            "paid": {"totals": {}, "channels": []},
            "outbound": {"totals": {}, "channels": []},
            "last_updated": "2026-03-31T00:00:00",
        }
        kpi, updated = svc._build_attraction_kpi(TENANT_ID, cache_data)
        assert kpi.main_kpi == 400
        assert updated == "2026-03-31T00:00:00"

    def test_build_capture_kpi_no_cache(self):
        svc, _db = _make_svc()
        svc.lead_repo.count_total.return_value = 25
        kpi = svc._build_capture_kpi(TENANT_ID, None)
        assert kpi.stage == "capture"
        assert kpi.main_kpi == 25

    def test_build_capture_kpi_from_cache(self):
        svc, _db = _make_svc()
        cache = {"header_kpis": {"total_leads": 30, "conversion_rate": 8.0}}
        kpi = svc._build_capture_kpi(TENANT_ID, cache)
        assert kpi.main_kpi == 30

    def test_build_nurture_kpi_no_cache(self):
        svc, _db = _make_svc()
        svc.customer_repo.count_by_stage.return_value = 12
        kpi = svc._build_nurture_kpi(TENANT_ID, None)
        assert kpi.stage == "nurture"
        assert kpi.main_kpi == 12

    def test_build_nurture_kpi_from_cache(self):
        svc, _db = _make_svc()
        cache = {"header_kpis": {"total_mqls": 15, "conversion_rate": 3.0}}
        kpi = svc._build_nurture_kpi(TENANT_ID, cache)
        assert kpi.main_kpi == 15

    def test_build_opportunity_kpi_no_cache(self):
        svc, _db = _make_svc()
        svc.customer_repo.count_by_stage.side_effect = [5, 3]  # SQL + OPPORTUNITY
        kpi = svc._build_opportunity_kpi(TENANT_ID, None)
        assert kpi.main_kpi == 8

    def test_build_opportunity_kpi_from_cache(self):
        svc, _db = _make_svc()
        cache = {"header_kpis": {"total_sqls": 7, "conversion_rate": 2.0}}
        kpi = svc._build_opportunity_kpi(TENANT_ID, cache)
        assert kpi.main_kpi == 7

    def test_build_sales_kpi_no_cache(self):
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
        ) as MockSales:
            MockSales.return_value.get_sales_summary.return_value = []
            kpi = svc._build_sales_kpi(TENANT_ID, None)
        assert kpi.stage == "sales"
        assert kpi.main_kpi == 0.0

    def test_build_sales_kpi_from_cache_with_conv_rate(self):
        svc, _db = _make_svc()
        cache = {
            "header_kpis": {"total_revenue": 5000.0, "new_customers": 10},
            "mini_funnel": {"conversion_rate": 12.5},
        }
        kpi = svc._build_sales_kpi(TENANT_ID, cache)
        assert kpi.main_kpi == 5000.0
        assert kpi.secondary_kpi == 12.5
        assert kpi.secondary_unit == "%"

    def test_build_sales_kpi_from_cache_no_conv_rate(self):
        svc, _db = _make_svc()
        cache = {
            "header_kpis": {"total_revenue": 5000.0, "new_customers": 10},
            "mini_funnel": {"conversion_rate": 0},
        }
        kpi = svc._build_sales_kpi(TENANT_ID, cache)
        assert kpi.secondary_kpi == 10  # new_customers

    def test_build_adoption_kpi_no_cache(self):
        from src.modules.analytics.application.services.metrics_service import MetricsService

        kpi = MetricsService._build_adoption_kpi(None)
        assert kpi.stage == "adoption"
        assert kpi.main_kpi == 0

    def test_build_adoption_kpi_from_cache(self):
        from src.modules.analytics.application.services.metrics_service import MetricsService

        cache = {
            "header_kpis": {"health_pct": 72.0, "active_customers": 15},
            "mini_funnel": {"conversion_rate": 0},
        }
        kpi = MetricsService._build_adoption_kpi(cache)
        assert kpi.main_kpi == 72.0

    def test_build_expansion_kpi_no_cache(self):
        from src.modules.analytics.application.services.metrics_service import MetricsService

        kpi = MetricsService._build_expansion_kpi(None)
        assert kpi.stage == "expansion"
        assert kpi.main_kpi == 0

    def test_build_expansion_kpi_from_cache(self):
        from src.modules.analytics.application.services.metrics_service import MetricsService

        cache = {"header_kpis": {"net_mrr": 3000.0, "churn_rate_pct": 2.5}}
        kpi = MetricsService._build_expansion_kpi(cache)
        assert kpi.main_kpi == 3000.0
        assert kpi.secondary_kpi == 2.5

    def test_build_evangelization_kpi_no_cache(self):
        svc, _db = _make_svc()
        svc.customer_repo.count_by_stage.return_value = 3
        kpi = svc._build_evangelization_kpi(TENANT_ID, None)
        assert kpi.stage == "evangelization"
        assert kpi.secondary_kpi == 3

    def test_build_evangelization_kpi_from_cache(self):
        svc, _db = _make_svc()
        cache = {
            "header_kpis": {"k_factor": 1.2},
            "mini_funnel": {"conversion_rate": 5.0},
        }
        kpi = svc._build_evangelization_kpi(TENANT_ID, cache)
        assert kpi.main_kpi == 1.2
        assert kpi.secondary_kpi == 5.0


# ─── get_stage_timeseries ─────────────────────────────────────────────────────


class TestGetStageTimeseries:
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
        svc, db = _make_svc(cache=cache)

        result = _run(svc.get_stage_timeseries(TENANT_ID, "attraction"))

        assert result.stage == "attraction"
        db.execute.assert_not_called()

    def test_no_channels_returns_empty_dto(self):
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[],
        ):
            result = _run(svc.get_stage_timeseries(TENANT_ID, "attraction"))

        assert result.data_points == []
        assert result.period_totals == {}

    def test_with_channels_queries_db(self):
        svc, db = _make_svc()
        db.execute.return_value.all.return_value = []
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[{"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid_social"}],
        ):
            result = _run(svc.get_stage_timeseries(TENANT_ID, "attraction"))

        assert result.stage == "attraction"

    def test_sets_cache_with_result(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, db = _make_svc(cache=cache)
        db.execute.return_value.all.return_value = []
        with patch(
            "src.modules.analytics.application.services.channel_registry.get_stage_channels",
            return_value=[{"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid_social"}],
        ):
            _run(svc.get_stage_timeseries(TENANT_ID, "attraction"))

        cache.set.assert_called_once()
