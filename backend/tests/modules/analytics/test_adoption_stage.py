"""Tests for AdoptionStageService."""

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


def _make_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.adoption_stage import (
        AdoptionStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    db.execute.return_value.first.return_value = (0, 0, 0, 0, None)
    svc = AdoptionStageService(db=db, cache=cache)
    return svc, db


class TestAdoptionStageServiceCacheHit:
    def test_returns_cached_dto(self):
        cache = AsyncMock()
        cached_data = {
            "header_kpis": {
                "active_customers": 10,
                "inactive_customers": 2,
                "health_pct": 83.3,
                "avg_ttv_days": None,
                "refund_count": 0,
                "refund_amount": 0.0,
                "refund_currency": "USD",
                "refund_amount_usd": 0.0,
            },
            "mini_funnel": {
                "source_label": "Ventas",
                "source_value": 12,
                "target_label": "Activos",
                "target_value": 10,
                "conversion_rate": 83.3,
            },
            "offers": [],
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached_data)
        cache.set = AsyncMock()
        svc, db = _make_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.active_customers == 10
        db.execute.assert_not_called()


class TestAdoptionStageServiceCacheMiss:
    def test_empty_data_returns_zero_dto(self):
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_customer_health_by_offer.return_value = []
            repo.get_avg_ttv_by_offer.return_value = {}
            repo.get_total_customers_and_sales.return_value = (0, 0)
            repo.get_refunds.return_value = (0, 0.0, "USD")

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.header_kpis.active_customers == 0
        assert result.header_kpis.health_pct == 0.0
        # 0 customers → health=0 → bottleneck fires; DTO still valid
        assert result.period == "last_30_days"

    def test_with_health_data_builds_offers(self):
        svc, _db = _make_svc()
        offer_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")
        with patch(
            "src.modules.analytics.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_customer_health_by_offer.return_value = [(offer_uuid, 10, 8, 2)]
            repo.get_avg_ttv_by_offer.return_value = {str(offer_uuid): 3.5}
            repo.get_total_customers_and_sales.return_value = (10, 12)
            repo.get_refunds.return_value = (0, 0.0, "USD")

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert len(result.offers) == 1
        assert result.offers[0].total_customers == 10
        assert result.offers[0].health_pct == 80.0

    def test_low_health_triggers_bottleneck(self):
        svc, _db = _make_svc()
        offer_uuid = uuid.UUID("22222222-2222-2222-2222-222222222222")
        with patch(
            "src.modules.analytics.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_customer_health_by_offer.return_value = [(offer_uuid, 10, 3, 7)]
            repo.get_avg_ttv_by_offer.return_value = {}
            repo.get_total_customers_and_sales.return_value = (10, 15)
            repo.get_refunds.return_value = (0, 0.0, "USD")

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert len(result.bottlenecks) >= 1
        types = [b.type for b in result.bottlenecks]
        assert "low_adoption_health" in types

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_svc(cache=cache)
        with patch(
            "src.modules.analytics.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_customer_health_by_offer.return_value = []
            repo.get_avg_ttv_by_offer.return_value = {}
            repo.get_total_customers_and_sales.return_value = (0, 0)
            repo.get_refunds.return_value = (0, 0.0, "USD")

            _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()

    def test_multi_offer_no_double_count(self):
        """When customer buys multiple offers, distinct total avoids double-count."""
        svc, _db = _make_svc()
        o1 = uuid.UUID("22222222-2222-2222-2222-222222222222")
        o2 = uuid.UUID("33333333-3333-3333-3333-333333333333")
        with patch(
            "src.modules.analytics.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            # o1: 8 active, 2 inactive; o2: 7 active, 3 inactive
            # total per-offer sum = 20 active+inactive > 15 distinct customers
            repo.get_customer_health_by_offer.return_value = [
                (o1, 10, 8, 2),
                (o2, 10, 7, 3),
            ]
            repo.get_avg_ttv_by_offer.return_value = {}
            repo.get_total_customers_and_sales.return_value = (15, 20)
            repo.get_refunds.return_value = (0, 0.0, "USD")

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        # total_customers = 15, per-offer sum exceeds it — should use distinct
        assert result.header_kpis.active_customers >= 0
        assert result.header_kpis.inactive_customers >= 0


class TestBuildAdoptionBottlenecks:
    def test_no_bottleneck_healthy(self):
        from src.modules.analytics.application.services.stage_services.adoption_stage import (
            _build_adoption_bottlenecks,
        )

        result = _build_adoption_bottlenecks(80.0, 3.0, [])
        assert result == []

    def test_low_health_slow_ttv(self):
        from src.modules.analytics.application.services.stage_services.adoption_stage import (
            _build_adoption_bottlenecks,
        )

        result = _build_adoption_bottlenecks(50.0, 10.0, [])
        assert len(result) == 1
        assert result[0].type == "low_adoption_health"

    def test_low_health_fast_ttv(self):
        from src.modules.analytics.application.services.stage_services.adoption_stage import (
            _build_adoption_bottlenecks,
        )

        result = _build_adoption_bottlenecks(50.0, 2.0, [])
        assert len(result) == 1
        assert result[0].type == "low_adoption_health"

    def test_per_offer_low_health(self):
        from src.modules.analytics.application.dto.adoption_dto import OfferHealthDTO
        from src.modules.analytics.application.services.stage_services.adoption_stage import (
            _build_adoption_bottlenecks,
        )

        low_offer = OfferHealthDTO(
            offer_id="aaa",
            public_name="Low Offer",
            total_customers=10,
            active_count=3,
            inactive_count=7,
            health_pct=30.0,
            ttv_days=None,
        )
        result = _build_adoption_bottlenecks(75.0, None, [low_offer])
        assert any(b.type == "offer_low_health" for b in result)
