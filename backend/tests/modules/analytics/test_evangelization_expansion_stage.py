"""Tests for EvangelizationStageService and ExpansionStageService."""

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


# ─── EvangelizationStageService ───────────────────────────────────────────────


def _make_evang_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.evangelization_stage import (
        EvangelizationStageService,
    )

    db = MagicMock()
    return EvangelizationStageService(db=db, cache=cache), db


def _evangelization_data() -> dict:
    """Minimal valid evangelization data payload."""
    return {
        "k_factor": 0.0,
        "nps_response_rate_pct": 0.0,
        "surveys_sent": 0,
        "header_kpis": {
            "k_factor": 0.0,
            "referral_conversions": 0,
            "referral_revenue": 0.0,
            "active_evangelists": 0,
        },
        "mini_funnel": {
            "source_label": "Activos",
            "source_value": 0,
            "target_label": "Referidos",
            "target_value": 0,
            "conversion_rate": 0.0,
        },
        "referidos": [],
        "candidatos": [],
        "nps_summary": {},
        "ugc_count": 0,
        "ugc_written": 0,
        "ugc_audio": 0,
    }


class TestEvangelizationStageServiceCacheHit:
    def test_cache_hit_returns_dto(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {
                "k_factor": 0.5,
                "referral_conversions": 0,
                "referral_revenue": 0.0,
                "active_evangelists": 0,
            },
            "mini_funnel": {
                "source_label": "Activos",
                "source_value": 0,
                "target_label": "Referidos",
                "target_value": 0,
                "conversion_rate": 0.0,
            },
            "referidos": [],
            "candidatos": [],
            "nps_summary": {},
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_evang_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.period == "last_30_days"
        db.execute.assert_not_called()


class TestEvangelizationStageServiceCacheMiss:
    def test_empty_data_returns_dto(self):
        svc, _db = _make_evang_svc()
        data = _evangelization_data()
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        # k_factor=0 < 0.5 fires a bottleneck; DTO still valid
        assert result is not None
        assert result.period == "last_30_days"

    def test_low_k_factor_critical_bottleneck(self):
        svc, _db = _make_evang_svc()
        data = _evangelization_data()
        data["k_factor"] = 0.2
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "low_k_factor" and b.severity == "critical" for b in result.bottlenecks)

    def test_medium_k_factor_warning_bottleneck(self):
        svc, _db = _make_evang_svc()
        data = _evangelization_data()
        data["k_factor"] = 0.7
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "low_k_factor" and b.severity == "warning" for b in result.bottlenecks)

    def test_low_nps_response_rate_critical(self):
        svc, _db = _make_evang_svc()
        data = _evangelization_data()
        data["surveys_sent"] = 50
        data["nps_response_rate_pct"] = 5.0
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "low_nps_response" and b.severity == "critical" for b in result.bottlenecks)

    def test_nps_response_warning(self):
        svc, _db = _make_evang_svc()
        data = _evangelization_data()
        data["surveys_sent"] = 50
        data["nps_response_rate_pct"] = 20.0
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "low_nps_response" and b.severity == "warning" for b in result.bottlenecks)

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_evang_svc(cache=cache)
        data = _evangelization_data()
        with patch(
            "src.modules.analytics.infrastructure.repositories.evangelization_repository.EvangelizationRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_evangelization_data = AsyncMock(return_value=data)

            _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()


# ─── ExpansionStageService ─────────────────────────────────────────────────────


def _make_expansion_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.expansion_stage import (
        ExpansionStageService,
    )

    db = MagicMock()
    return ExpansionStageService(db=db, cache=cache), db


class TestExpansionStageServiceCacheHit:
    def test_cache_hit_returns_dto(self):
        cache = AsyncMock()
        cached_data = {
            "header_kpis": {
                "net_mrr": 0.0,
                "net_mrr_usd": 0.0,
                "currency": "USD",
                "avg_ltv": 0.0,
                "avg_ltv_usd": 0.0,
                "churn_rate_pct": 0.0,
            },
            "mini_funnel": {
                "source_label": "Activos",
                "source_value": 0,
                "target_label": "Expansion",
                "target_value": 0,
                "conversion_rate": 0.0,
            },
            "retencion": {
                "group_key": "retencion",
                "group_label": "Retencion",
                "group_subtitle": "",
                "total_count": 0,
                "total_revenue": 0.0,
                "total_revenue_usd": 0.0,
                "currency": "USD",
                "rate_pct": 0.0,
                "offers": [],
            },
            "crecimiento": {
                "group_key": "crecimiento",
                "group_label": "Crecimiento",
                "group_subtitle": "",
                "total_count": 0,
                "total_revenue": 0.0,
                "total_revenue_usd": 0.0,
                "currency": "USD",
                "rate_pct": 0.0,
                "offers": [],
            },
            "cancelaciones": {
                "group_key": "cancelaciones",
                "group_label": "Cancelaciones",
                "group_subtitle": "",
                "total_count": 0,
                "total_revenue": 0.0,
                "total_revenue_usd": 0.0,
                "currency": "USD",
                "rate_pct": 0.0,
                "offers": [],
            },
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached_data)
        cache.set = AsyncMock()
        svc, db = _make_expansion_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.period == "last_30_days"
        db.execute.assert_not_called()


class TestExpansionStageServiceCacheMiss:
    def test_empty_data_no_bottlenecks(self):
        svc, _db = _make_expansion_svc()
        with patch(
            "src.modules.analytics.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_expansion_sales_grouped.return_value = {"renewals": [], "upsells": []}
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 0
            repo.get_active_customer_count.return_value = 0
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.bottlenecks == []
        assert result.header_kpis.churn_rate_pct == 0.0

    def test_high_churn_critical_bottleneck(self):
        svc, _db = _make_expansion_svc()
        with patch(
            "src.modules.analytics.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_expansion_sales_grouped.return_value = {"renewals": [], "upsells": []}
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 6
            repo.get_active_customer_count.return_value = 100
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "high_churn_rate" and b.severity == "critical" for b in result.bottlenecks)

    def test_medium_churn_warning_bottleneck(self):
        svc, _db = _make_expansion_svc()
        with patch(
            "src.modules.analytics.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_expansion_sales_grouped.return_value = {"renewals": [], "upsells": []}
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 4
            repo.get_active_customer_count.return_value = 100
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "high_churn_rate" and b.severity == "warning" for b in result.bottlenecks)

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_expansion_svc(cache=cache)
        with patch(
            "src.modules.analytics.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_expansion_sales_grouped.return_value = {"renewals": [], "upsells": []}
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 0
            repo.get_active_customer_count.return_value = 0
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()


class TestExpansionHelpers:
    def test_build_expansion_offers_empty(self):
        from src.modules.analytics.application.services.stage_services.expansion_stage import (
            _build_expansion_offers,
        )

        result = _build_expansion_offers([], {}, "USD")
        assert result == []

    def test_build_expansion_offers_with_items(self):
        from src.modules.analytics.application.services.stage_services.expansion_stage import (
            _build_expansion_offers,
        )

        items = [(uuid.UUID("22222222-2222-2222-2222-222222222222"), 3, 500.0, "USD")]
        result = _build_expansion_offers(items, {}, "USD")
        assert len(result) == 1
        assert result[0].count == 3
        assert result[0].revenue == 500.0

    def test_build_expansion_group(self):
        from src.modules.analytics.application.services.stage_services.expansion_stage import (
            _build_expansion_group,
        )

        result = _build_expansion_group("retencion", "Retencion", "sub", [], 90.0, "USD")
        assert result.group_key == "retencion"
        assert result.rate_pct == 90.0
        assert result.total_count == 0
