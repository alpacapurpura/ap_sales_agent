"""Stage service coverage gap-fill — attraction, nurture, sales remaining lines."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

TENANT_ID = uuid.uuid4()


def _run(coro):
    return asyncio.run(coro)


# ─── attraction_stage _enrich_with_derived_metrics (lines 61-76, 99) ─────────


class TestEnrichWithDerivedMetrics:
    def _enrich(self, metrics, repo=None):
        from luana_core_analytics_engine.application.dto.attraction_dto import MetricValueDTO
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            _enrich_with_derived_metrics,
        )

        if repo is None:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {}
        return _enrich_with_derived_metrics(
            metrics, "meta-ads", repo, TENANT_ID, "meta", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )

    def _m(self, name, value, currency=None):
        from luana_core_analytics_engine.application.dto.attraction_dto import MetricValueDTO

        return MetricValueDTO(name=name, value=float(value), currency=currency)

    def test_cpc_computed_from_spend_and_clicks(self):
        """Lines 61-74: cpc appended when spend+clicks available."""
        metrics = [self._m("spend", 100, "USD"), self._m("clicks", 50)]
        result = self._enrich(metrics)
        names = [m.name for m in result]
        assert "cpc" in names
        cpc = next(m for m in result if m.name == "cpc")
        assert cpc.value == 2.0

    def test_cpm_computed_from_spend_and_impressions(self):
        """Lines 74-76: cpm appended when spend+impressions available."""
        metrics = [self._m("spend", 100, "USD"), self._m("impressions", 50000)]
        result = self._enrich(metrics)
        names = [m.name for m in result]
        assert "cpm" in names
        cpm = next(m for m in result if m.name == "cpm")
        assert cpm.value == pytest.approx(2.0, rel=0.01)

    def test_no_cpc_if_already_present(self):
        metrics = [self._m("spend", 100), self._m("clicks", 50), self._m("cpc", 1.5)]
        result = self._enrich(metrics)
        cpc_list = [m for m in result if m.name == "cpc"]
        assert len(cpc_list) == 1  # not duplicated

    def test_reach_appended_from_repo_when_missing(self):
        """Line 99: reach > 0 triggers append."""
        metrics = [self._m("impressions", 5000)]
        repo = MagicMock()
        repo.get_channel_metrics.return_value = {"reach": 3000}
        result = self._enrich(metrics, repo=repo)
        names = [m.name for m in result]
        assert "reach" in names

    def test_reach_not_appended_if_zero(self):
        metrics = [self._m("impressions", 5000)]
        repo = MagicMock()
        repo.get_channel_metrics.return_value = {"reach": 0}
        result = self._enrich(metrics, repo=repo)
        names = [m.name for m in result]
        assert "reach" not in names

    def test_no_spend_no_cpc_cpm(self):
        metrics = [self._m("impressions", 5000)]
        result = self._enrich(metrics)
        names = [m.name for m in result]
        assert "cpc" not in names
        assert "cpm" not in names


import pytest

# ─── attraction_stage _classify_error (line 126 = fallback) ──────────────────


class TestAttractionClassifyError:
    def test_unknown_error_returns_generic_message(self):
        """Line 126: fallback 'Servicio no disponible'."""
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        result = AttractionStageService._classify_error("random unknown error xyz")
        assert result == "Servicio no disponible"

    def test_none_error_returns_none(self):
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        assert AttractionStageService._classify_error(None) is None


# ─── attraction_stage get_metrics manychat channel (lines 258-268) ───────────


class TestAttractionManyChatChannel:
    def test_manychat_channel_supplements_metrics(self):
        """Lines 258-268: manychat provider_name triggers OfficialMetricsRepository."""
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = []
        svc = AttractionStageService(db=db)

        channel_split = {
            "connected": [
                {
                    "slug": "manychat-ig",
                    "name": "ManyChat IG",
                    "channel_type": "messaging",
                    "source_label": "MC",
                    "provider_name": "manychat",
                    "connection_config": {},
                }
            ],
            "available": [],
        }

        with (
            patch(
                "luana_core_analytics_engine.application.services.stage_services.attraction_stage.ChannelRegistry"
            ) as MockReg,
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.extraction_run_repository.ExtractionRunRepository"
            ) as MockRunRepo,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.attraction_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo,
        ):
            reg = MagicMock()
            reg.get_available_channels = AsyncMock(return_value=channel_split)
            MockReg.return_value = reg

            run_repo = MagicMock()
            run_repo.get_last_run.return_value = None
            MockRunRepo.return_value = run_repo

            official_repo = MagicMock()
            official_repo.get_channel_summary.return_value = []
            official_repo.get_channel_metrics.return_value = {"automation_flows": 5}
            MockOfficialRepo.return_value = official_repo

            from luana_core_analytics_engine.domain.period_config import DateRange

            dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")
            result = _run(svc.get_metrics(TENANT_ID, dr))

        assert result is not None


# ─── nurture_stage _supplement_manychat (lines 155-165) ──────────────────────


class TestNurtureSupplementManychat:
    def test_appends_new_metrics(self):
        """Lines 155-165: _supplement_manychat appends missing metrics."""
        from luana_core_analytics_engine.application.dto.attraction_dto import MetricValueDTO
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        db = MagicMock()
        svc = NurtureStageService(db=db)
        metrics = [MetricValueDTO(name="leads", value=5.0)]

        with patch(
            "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {"automation_rate": 80.0}
            MockRepo.return_value = repo

            svc._supplement_manychat(metrics, TENANT_ID, "manychat-ig", date(2026, 3, 1), date(2026, 3, 31))

        names = [m.name for m in metrics]
        assert "automation_rate" in names

    def test_existing_metric_not_duplicated(self):
        from luana_core_analytics_engine.application.dto.attraction_dto import MetricValueDTO
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        db = MagicMock()
        svc = NurtureStageService(db=db)
        metrics = [MetricValueDTO(name="leads", value=5.0)]

        with patch(
            "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {"leads": 10}  # already exists
            MockRepo.return_value = repo

            svc._supplement_manychat(metrics, TENANT_ID, "manychat-ig", date(2026, 3, 1), date(2026, 3, 31))

        leads = [m for m in metrics if m.name == "leads"]
        assert len(leads) == 1


# ─── nurture_stage get_metrics aggregation loop and manychat (lines 189, 229, 232)


class TestNurtureGetMetricsFlow:
    def _setup(self, channel_split=None):
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 0
        db.execute.return_value.all.return_value = []
        svc = NurtureStageService(db=db)
        return svc, db

    def test_aggregation_loop_body_executes(self):
        """Line 189: agg_by_slug[agg.channel_slug].append(agg) inside loop."""
        svc, _db = self._setup()

        agg_row = MagicMock()
        agg_row.channel_slug = "email-nurture"
        agg_row.metric_name = "open_rate"
        agg_row.value = 30.0

        channel_split = {"connected": [], "available": []}

        with (
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.ChannelRegistry"
            ) as MockReg,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
            ) as MockNurtureRepo,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.StageCostService"
            ) as MockCostSvc,
        ):
            reg = MagicMock()
            reg.get_available_channels = AsyncMock(return_value=channel_split)
            MockReg.return_value = reg

            official_repo = MagicMock()
            official_repo.get_channel_summary.return_value = [agg_row]
            MockOfficialRepo.return_value = official_repo

            nurture_repo = MagicMock()
            nurture_repo.count_new_mqls.return_value = 0
            nurture_repo.count_leads_in_period.return_value = 0
            nurture_repo.get_mql_sources.return_value = {}
            nurture_repo.count_followup_events.return_value = {"sent": 0, "replied": 0}
            nurture_repo.count_email_events.return_value = {"emails_sent": 0, "opens": 0, "clicks": 0}
            MockNurtureRepo.return_value = nurture_repo

            cost_svc = MagicMock()
            cost_svc.get_group_cost_per_mql.return_value = 0.0
            cost_svc.calculate_cost_per_mql.return_value = 0.0
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.get_channel_costs.return_value = {}
            MockCostSvc.return_value = cost_svc
            svc._load_nurture_costs = MagicMock(return_value=(0.0, 0.0, 0.0))

            from luana_core_analytics_engine.domain.period_config import DateRange

            dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")
            result = _run(svc.get_metrics(TENANT_ID, dr))

        assert result is not None

    def test_metrics_none_uses_retargeting_fallback_and_manychat_supplement(self):
        """Lines 229+232: metrics is None triggers _build_retargeting_metrics,
        then manychat provider calls _supplement_manychat."""
        svc, _db = self._setup()

        channel_split = {
            "connected": [
                {
                    "slug": "manychat-ig",
                    "name": "ManyChat IG",
                    "channel_type": "automation",
                    "source_label": "MC",
                    "provider_name": "manychat",
                    "connection_config": {},
                }
            ],
            "available": [],
        }

        with (
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.ChannelRegistry"
            ) as MockReg,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
            ) as MockNurtureRepo,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.nurture_stage.StageCostService"
            ) as MockCostSvc,
        ):
            reg = MagicMock()
            reg.get_available_channels = AsyncMock(return_value=channel_split)
            MockReg.return_value = reg

            official_repo = MagicMock()
            official_repo.get_channel_summary.return_value = []  # no aggs → agg_by_slug empty
            official_repo.get_channel_metrics.return_value = {}
            MockOfficialRepo.return_value = official_repo

            nurture_repo = MagicMock()
            nurture_repo.count_new_mqls.return_value = 5
            nurture_repo.count_leads_in_period.return_value = 20
            nurture_repo.get_mql_sources.return_value = {}
            nurture_repo.count_followup_events.return_value = {"sent": 0, "replied": 0}
            nurture_repo.count_email_events.return_value = {"emails_sent": 0, "opens": 0, "clicks": 0}
            MockNurtureRepo.return_value = nurture_repo

            cost_svc = MagicMock()
            cost_svc.get_group_cost_per_mql.return_value = 0.0
            cost_svc.calculate_cost_per_mql.return_value = 0.0
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.get_channel_costs.return_value = {}
            MockCostSvc.return_value = cost_svc
            svc._load_nurture_costs = MagicMock(return_value=(0.0, 0.0, 0.0))

            from luana_core_analytics_engine.domain.period_config import DateRange

            dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")
            result = _run(svc.get_metrics(TENANT_ID, dr))

        assert len(result.automation.channels) == 1


# ─── sales_stage _build_sales_bottlenecks severity=None (line 251) ───────────


class TestSalesBottlenecksNoSeverity:
    def test_low_cac_ratio_no_bottleneck(self):
        """Line 251: severity=None when cac_ratio below warning threshold."""
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        # cac=10, aov=100 → ratio=0.1 < warning threshold
        result = _build_sales_bottlenecks(conv_rate=5.0, sql_count=10, cac=10.0, new_customers=5, total_rev=500.0)
        high_cac = [b for b in result if b.type == "high_cac_ratio"]
        assert len(high_cac) == 0


# ─── sales_stage _enrich_with_shopify (lines 315-323, 327-332) ───────────────


class TestSalesEnrichWithShopify:
    """Direct tests for _enrich_with_shopify method."""

    def _setup(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            SalesStageService,
        )

        db = MagicMock()
        return SalesStageService(db=db), db

    def test_shopify_revenue_fallback_when_crm_zero(self):
        """Lines 327-328: total_rev = shopify_revenue when CRM has no revenue."""
        svc, _db = self._setup()
        with patch(
            "luana_core_analytics_engine.application.services.stage_services.sales_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {"revenue": 5000.0, "order_count": 10, "avg_order_value": 500.0}
            repo.get_metrics.return_value = []
            MockRepo.return_value = repo

            from datetime import datetime, timezone

            sd = datetime(2026, 3, 1, tzinfo=timezone.utc)
            ed = datetime(2026, 3, 31, tzinfo=timezone.utc)
            _header_kpis, new_customers, total_rev = svc._enrich_with_shopify(
                TENANT_ID,
                sd,
                ed,
                "USD",
                total_rev=0.0,
                total_rev_usd=0.0,
                new_customers=0,
                total_investment=0.0,
                cac=None,
            )

        assert total_rev == 5000.0
        assert new_customers == 10

    def test_shopify_currency_from_sample_rows(self):
        """Lines 315-323: shopify_revenue > 0 → get_metrics for currency."""
        svc, _db = self._setup()
        currency_row = MagicMock()
        currency_row.currency = "PEN"

        with patch(
            "luana_core_analytics_engine.application.services.stage_services.sales_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {"revenue": 3000.0, "order_count": 5}
            repo.get_metrics.return_value = [currency_row]
            MockRepo.return_value = repo

            from datetime import datetime, timezone

            sd = datetime(2026, 3, 1, tzinfo=timezone.utc)
            ed = datetime(2026, 3, 31, tzinfo=timezone.utc)
            header_kpis, _, _ = svc._enrich_with_shopify(
                TENANT_ID,
                sd,
                ed,
                "USD",
                total_rev=1000.0,
                total_rev_usd=1000.0,
                new_customers=5,
                total_investment=0.0,
                cac=None,
            )

        assert header_kpis.shopify_currency == "PEN"

    def test_cac_computed_when_investment_and_customers_available(self):
        """Lines 330-332: cac computed when new_customers=0 and shopify_order_count>0."""
        svc, _db = self._setup()
        with patch(
            "luana_core_analytics_engine.application.services.stage_services.sales_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo = MagicMock()
            repo.get_channel_metrics.return_value = {"revenue": 5000.0, "order_count": 10}
            repo.get_metrics.return_value = []
            MockRepo.return_value = repo

            from datetime import datetime, timezone

            sd = datetime(2026, 3, 1, tzinfo=timezone.utc)
            ed = datetime(2026, 3, 31, tzinfo=timezone.utc)
            header_kpis, new_customers, _ = svc._enrich_with_shopify(
                TENANT_ID,
                sd,
                ed,
                "USD",
                total_rev=0.0,
                total_rev_usd=0.0,
                new_customers=0,
                total_investment=1000.0,
                cac=None,
            )

        assert new_customers == 10
        assert header_kpis.cac == 100.0  # 1000 / 10
