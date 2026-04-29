"""Tests for NurtureStageService and OpportunityStageService."""

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


# ─── NurtureStageService ───────────────────────────────────────────────────────


def _make_nurture_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.nurture_stage import (
        NurtureStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return NurtureStageService(db=db, cache=cache), db


class TestNurtureStageServiceCacheHit:
    def test_cache_hit_skips_db(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {"total_mqls": 5, "conversion_rate": 10.0, "cost_per_mql": None},
            "mini_funnel": {
                "source_label": "Leads",
                "source_value": 50,
                "target_label": "MQLs",
                "target_value": 5,
                "conversion_rate": 10.0,
            },
            "retargeting": {"totals": {}, "channels": []},
            "automation": {"totals": {}, "channels": []},
            "available": None,
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_nurture_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.total_mqls == 5
        db.execute.assert_not_called()


class TestNurtureStageServiceCacheMiss:
    def _patch_registry(self):
        return patch("src.modules.analytics.application.services.stage_services.nurture_stage.ChannelRegistry")

    def _patch_cost(self):
        return patch("src.modules.analytics.application.services.stage_services.nurture_stage.StageCostService")

    def test_empty_channels_returns_dto(self):
        svc, _db = _make_nurture_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None
            cost_svc.get_group_cost_per_mql.return_value = None

            with patch(
                "src.modules.analytics.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
            ) as MockNurtRepo:
                repo = MockNurtRepo.return_value
                repo.count_new_mqls.return_value = 0
                repo.count_leads_in_period.return_value = 0
                repo.count_email_events.return_value = {}
                repo.count_followup_events.return_value = {}

                with patch(
                    "src.modules.analytics.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
                ) as MockOfficialRepo:
                    official = MockOfficialRepo.return_value
                    official.get_channel_summary.return_value = []

                    result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.header_kpis.total_mqls == 0

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_nurture_svc(cache=cache)
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None
            cost_svc.get_group_cost_per_mql.return_value = None

            with patch(
                "src.modules.analytics.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
            ) as MockNurtRepo:
                repo = MockNurtRepo.return_value
                repo.count_new_mqls.return_value = 0
                repo.count_leads_in_period.return_value = 0
                repo.count_email_events.return_value = {}
                repo.count_followup_events.return_value = {}

                with patch(
                    "src.modules.analytics.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
                ) as MockOfficialRepo:
                    official = MockOfficialRepo.return_value
                    official.get_channel_summary.return_value = []

                    _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()


class TestNurtureStaticHelpers:
    def test_build_email_nurture_metrics_empty(self):
        from src.modules.analytics.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        result = NurtureStageService._build_email_nurture_metrics({})
        assert len(result) == 3
        assert result[0].name == "emails_sent"
        assert result[0].value == 0.0

    def test_build_email_nurture_rates(self):
        from src.modules.analytics.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        result = NurtureStageService._build_email_nurture_metrics({"emails_sent": 100, "opens": 30, "clicks": 10})
        open_rate = next(m for m in result if m.name == "open_rate")
        assert open_rate.value == 30.0

    def test_build_ai_sdr_metrics_empty(self):
        from src.modules.analytics.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        result = NurtureStageService._build_ai_sdr_metrics({})
        assert len(result) == 2
        assert result[0].name == "followups"

    def test_build_ai_sdr_response_rate(self):
        from src.modules.analytics.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        result = NurtureStageService._build_ai_sdr_metrics({"sent": 10, "replied": 4})
        rate = next(m for m in result if m.name == "response_rate")
        assert rate.value == 40.0

    def test_build_retargeting_metrics_empty(self):
        from src.modules.analytics.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        result = NurtureStageService._build_retargeting_metrics([])
        assert result == []


# ─── OpportunityStageService ───────────────────────────────────────────────────


def _make_opp_svc(cache=None):
    from src.modules.analytics.application.services.stage_services.opportunity_stage import (
        OpportunityStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return OpportunityStageService(db=db, cache=cache), db


def _checkout_events(initiated=0, abandoned=0):
    return {
        "checkout_initiated": {"count": initiated, "value": 0.0},
        "cart_abandoned": {"count": abandoned, "value": 0.0},
    }


def _meeting_events(booked=0, completed=0, no_show=0, rescheduled=0):
    return {
        "booked": booked,
        "completed": completed,
        "no_show": no_show,
        "rescheduled": rescheduled,
    }


class TestOpportunityStageServiceCacheHit:
    def test_cache_hit_skips_db(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {"total_sqls": 3, "conversion_rate": 5.0, "cost_per_sql": None},
            "mini_funnel": {
                "source_label": "MQLs",
                "source_value": 60,
                "target_label": "SQLs",
                "target_value": 3,
                "conversion_rate": 5.0,
            },
            "checkout": {"totals": {}, "channels": []},
            "payment_links": {"totals": {}, "channels": []},
            "qualification": {"totals": {}, "channels": []},
            "bottlenecks": [],
            "available": None,
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_opp_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.total_sqls == 3
        db.execute.assert_not_called()


class TestOpportunityStageServiceCacheMiss:
    def _patch_registry(self):
        return patch("src.modules.analytics.application.services.stage_services.opportunity_stage.ChannelRegistry")

    def _patch_cost(self):
        return patch("src.modules.analytics.application.services.stage_services.opportunity_stage.StageCostService")

    def test_empty_channels_returns_dto(self):
        svc, _db = _make_opp_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None
            cost_svc.get_total_funnel_investment = MagicMock(return_value=(0.0, False))

            with patch(
                "src.modules.analytics.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ) as MockOppRepo:
                repo = MockOppRepo.return_value
                repo.count_new_sqls.return_value = 0
                repo.count_mqls_in_period.return_value = 0
                repo.count_checkout_events.return_value = _checkout_events()
                repo.count_meeting_events.return_value = _meeting_events()
                repo.count_payment_link_events.return_value = {"count": 0, "value": 0.0}

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.header_kpis.total_sqls == 0
        assert result.bottlenecks == []

    def test_high_abandon_rate_critical_bottleneck(self):
        svc, _db = _make_opp_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None

            with patch(
                "src.modules.analytics.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ) as MockOppRepo:
                repo = MockOppRepo.return_value
                repo.count_new_sqls.return_value = 0
                repo.count_mqls_in_period.return_value = 0
                repo.count_checkout_events.return_value = _checkout_events(initiated=10, abandoned=6)
                repo.count_meeting_events.return_value = _meeting_events()
                repo.count_payment_link_events.return_value = {"count": 0, "value": 0.0}

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "abandoned_cart" for b in result.bottlenecks)

    def test_no_show_bottleneck(self):
        svc, _db = _make_opp_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None

            with patch(
                "src.modules.analytics.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ) as MockOppRepo:
                repo = MockOppRepo.return_value
                repo.count_new_sqls.return_value = 0
                repo.count_mqls_in_period.return_value = 0
                repo.count_checkout_events.return_value = _checkout_events()
                repo.count_meeting_events.return_value = _meeting_events(booked=10, no_show=5)
                repo.count_payment_link_events.return_value = {"count": 0, "value": 0.0}

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert any(b.type == "meeting_no_show" for b in result.bottlenecks)


class TestOpportunityStaticHelpers:
    def test_detect_bottlenecks_no_data(self):
        from src.modules.analytics.application.services.stage_services.opportunity_stage import (
            OpportunityStageService,
        )

        result = OpportunityStageService._detect_opportunity_bottlenecks(_checkout_events(), _meeting_events())
        assert result == []

    def test_abandoned_cart_warning(self):
        from src.modules.analytics.application.services.stage_services.opportunity_stage import (
            OpportunityStageService,
        )

        result = OpportunityStageService._detect_opportunity_bottlenecks(
            _checkout_events(initiated=10, abandoned=4), _meeting_events()
        )
        assert any(b.type == "abandoned_cart" and b.severity == "warning" for b in result)

    def test_build_slug_metrics_checkout_init(self):
        from src.modules.analytics.application.services.stage_services.opportunity_stage import (
            OpportunityStageService,
        )

        metrics = OpportunityStageService._build_slug_metrics(
            "checkout-init",
            _checkout_events(initiated=5),
            _meeting_events(),
            {"count": 0, "value": 0.0},
        )
        assert any(m.name == "count" and m.value == 5.0 for m in metrics)

    def test_build_slug_metrics_abandoned_cart(self):
        from src.modules.analytics.application.services.stage_services.opportunity_stage import (
            OpportunityStageService,
        )

        metrics = OpportunityStageService._build_slug_metrics(
            "abandoned-cart",
            _checkout_events(initiated=10, abandoned=3),
            _meeting_events(),
            {"count": 0, "value": 0.0},
        )
        assert any(m.name == "abandonment_rate" for m in metrics)
