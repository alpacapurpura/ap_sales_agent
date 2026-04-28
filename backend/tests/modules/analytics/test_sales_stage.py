"""Tests for SalesStageService and its helpers."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.analytics.domain.period_config import DateRange

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DATE_RANGE = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_sales_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.sales_stage import (
        SalesStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return SalesStageService(db=db, cache=cache), db


class TestSalesStageServiceCacheHit:
    def test_cache_hit_skips_db(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {
                "total_revenue": 1000.0,
                "total_revenue_usd": 1000.0,
                "currency": "USD",
                "new_customers": 5,
                "cac": None,
                "cac_incomplete": False,
                "net_sales": 0.0,
                "total_discounts": 0.0,
                "total_tax": 0.0,
                "refund_count": 0,
                "refund_amount": 0.0,
                "shipping_revenue": 0.0,
                "repeat_customers": 0,
                "discount_usage_count": 0,
                "shopify_revenue": 0.0,
                "shopify_order_count": 0,
                "shopify_avg_order_value": 0.0,
                "shopify_currency": "USD",
            },
            "mini_funnel": {
                "source_label": "Oportunidades",
                "source_value": 10,
                "target_label": "Ventas",
                "target_value": 5,
                "conversion_rate": 50.0,
            },
            "adquisicion": {
                "group_key": "adquisicion",
                "group_label": "Adquisicion",
                "total_revenue": 1000.0,
                "total_revenue_usd": 1000.0,
                "customer_count": 5,
                "revenue_percentage": 100.0,
                "currency": "USD",
                "tiers": [],
            },
            "expansion": {
                "group_key": "expansion",
                "group_label": "Expansion",
                "total_revenue": 0.0,
                "total_revenue_usd": 0.0,
                "customer_count": 0,
                "revenue_percentage": 0.0,
                "currency": "USD",
                "tiers": [],
            },
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_sales_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.total_revenue == 1000.0
        db.execute.assert_not_called()


class TestSalesStageServiceCacheMiss:
    def _patch_shopify(self):
        return patch("src.modules.analytics.application.services.stage_services.sales_stage.OfficialMetricsRepository")

    def _patch_cost(self):
        return patch("src.modules.analytics.application.services.stage_services.sales_stage.StageCostService")

    def test_empty_sales_returns_dto(self):
        svc, _db = _make_sales_svc()
        with self._patch_cost() as MockCost, self._patch_shopify() as MockRepo:
            cost_svc = MockCost.return_value
            cost_svc.get_total_funnel_investment.return_value = (0.0, True)

            official_repo = MockRepo.return_value
            official_repo.get_channel_metrics.return_value = {}
            official_repo.get_metrics.return_value = []

            with patch(
                "src.modules.analytics.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
            ) as MockSalesRepo:
                sales_repo = MockSalesRepo.return_value
                sales_repo.get_sales_summary.return_value = []
                sales_repo.get_total_conversion_customers.return_value = 0
                sales_repo.get_total_sql_count.return_value = 0

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.header_kpis.new_customers == 0

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_sales_svc(cache=cache)
        with self._patch_cost() as MockCost, self._patch_shopify() as MockRepo:
            cost_svc = MockCost.return_value
            cost_svc.get_total_funnel_investment.return_value = (0.0, True)

            official_repo = MockRepo.return_value
            official_repo.get_channel_metrics.return_value = {}
            official_repo.get_metrics.return_value = []

            with patch(
                "src.modules.analytics.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
            ) as MockSalesRepo:
                sales_repo = MockSalesRepo.return_value
                sales_repo.get_sales_summary.return_value = []
                sales_repo.get_total_conversion_customers.return_value = 0
                sales_repo.get_total_sql_count.return_value = 0

                _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()


class TestGroupRawSales:
    def test_empty_returns_zero_stage_data(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _group_raw_sales,
        )

        stage_data, stage_revenue, display_currency = _group_raw_sales([], {})
        assert stage_data["adquisicion"] == {}
        assert stage_data["expansion"] == {}
        assert stage_revenue["adquisicion"] == 0.0
        assert display_currency == "USD"

    def test_conversion_stage_grouped_correctly(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _group_raw_sales,
        )

        offer_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        class FakeStageEnum:
            value = "CONVERSION"

        row = (FakeStageEnum(), offer_id, "MANUAL", "USD", 2, 300.0, 2)
        stage_data, stage_revenue, _currency = _group_raw_sales([row], {})
        assert str(offer_id) in stage_data["adquisicion"]
        assert stage_revenue["adquisicion"] == 300.0

    def test_unknown_stage_skipped(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _group_raw_sales,
        )

        offer_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        class FakeStageEnum:
            value = "UNKNOWN_STAGE"

        row = (FakeStageEnum(), offer_id, "MANUAL", "USD", 1, 100.0, 1)
        stage_data, _stage_revenue, _ = _group_raw_sales([row], {})
        assert str(offer_id) not in stage_data["adquisicion"]


class TestBuildSalesBottlenecks:
    def test_no_bottlenecks_healthy(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        result = _build_sales_bottlenecks(60.0, 10, None, 0, 0.0)
        assert result == []

    def test_low_conversion_critical(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        result = _build_sales_bottlenecks(5.0, 10, None, 0, 0.0)
        assert any(b.type == "low_conversion_rate" and b.severity == "critical" for b in result)

    def test_low_conversion_warning(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        result = _build_sales_bottlenecks(18.0, 10, None, 0, 0.0)
        assert any(b.type == "low_conversion_rate" and b.severity == "warning" for b in result)

    def test_no_sqls_no_conversion_bottleneck(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        result = _build_sales_bottlenecks(0.0, 0, None, 0, 0.0)
        assert result == []

    def test_high_cac_critical(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            HIGH_CAC_CRITICAL_RATIO,
            _build_sales_bottlenecks,
        )

        # cac = 500, revenue = 100, customers = 1 → aov = 100, ratio = 5.0 > critical
        result = _build_sales_bottlenecks(60.0, 10, 500.0, 1, 100.0)
        assert any(b.type == "high_cac_ratio" for b in result)


class TestBuildOfferSaleDTO:
    def test_lead_magnet_returns_none(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_offer_sale_dto,
        )

        class MockOffer:
            value_level = "lead_magnet"
            public_name = "Free Lead"
            offer_type = "digital"
            pricing_type = "one_time"
            currency = "USD"

        data = {"count": 1, "revenue": 0.0, "currency": "USD", "sources": {}, "unique_customers": 0}
        result = _build_offer_sale_dto("aaa", data, {"aaa": MockOffer()}, "adquisicion")
        assert result is None

    def test_paid_offer_returns_dto(self):
        from src.modules.analytics.application.services.stage_services.sales_stage import (
            _build_offer_sale_dto,
        )

        class MockOffer:
            value_level = "core"
            public_name = "My Course"
            offer_type = "digital"
            pricing_type = "one_time"
            currency = "USD"

        data = {"count": 3, "revenue": 900.0, "currency": "USD", "sources": {}, "unique_customers": 3}
        result = _build_offer_sale_dto("bbb", data, {"bbb": MockOffer()}, "adquisicion")
        assert result is not None
        assert result.sales_count == 3
        assert result.total_revenue == 900.0
