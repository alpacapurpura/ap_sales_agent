"""Supplemental tests covering remaining uncovered lines across stage services."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_analytics_engine.domain.period_config import DateRange

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DATE_RANGE = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")


def _run(coro):
    return asyncio.run(coro)


# ─── SummaryStageService _build_sales_kpi and _build_evangelization_kpi ───────


def _make_summary_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.summary_stage import (
        SummaryStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []

    with (
        patch(
            "luana_core_analytics_engine.application.services.stage_services.summary_stage.get_customer_repository"
        ) as MockCustRepo,
        patch(
            "luana_core_analytics_engine.application.services.stage_services.summary_stage.get_lead_metrics_repository"
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


class TestSummaryBuildSalesKpiFromCache:
    def test_build_sales_kpi_with_conv_rate(self):
        svc, _ = _make_summary_svc()
        cache = {
            "header_kpis": {"total_revenue": 8000.0, "new_customers": 10},
            "mini_funnel": {"conversion_rate": 15.0},
        }
        result = svc._build_sales_kpi(cache, TENANT_ID)
        assert result.stage == "sales"
        assert result.main_kpi == 8000.0
        assert result.secondary_kpi == 15.0
        assert result.secondary_unit == "%"

    def test_build_sales_kpi_no_conv_rate_uses_customers(self):
        svc, _ = _make_summary_svc()
        cache = {
            "header_kpis": {"total_revenue": 5000.0, "new_customers": 8},
            "mini_funnel": {"conversion_rate": 0},
        }
        result = svc._build_sales_kpi(cache, TENANT_ID)
        assert result.secondary_kpi == 8


class TestSummaryBuildEvangelizationKpiFromCache:
    def test_build_evangelization_kpi_from_cache(self):
        svc, _ = _make_summary_svc()
        cache = {
            "header_kpis": {"k_factor": 1.5},
            "mini_funnel": {"conversion_rate": 8.0},
        }
        result = svc._build_evangelization_kpi(cache, TENANT_ID)
        assert result.stage == "evangelization"
        assert result.main_kpi == 1.5
        assert result.secondary_kpi == 8.0


class TestSummaryGetSummaryWithOpportunityCache:
    def test_opportunity_cache_hit_uses_fallback_zero(self):
        """When opportunity cache exists, fallback_sqls = 0 (line 290)."""
        opportunity_cache = {
            "header_kpis": {"total_sqls": 5, "conversion_rate": 10.0, "cost_per_sql": None},
            "mini_funnel": {
                "source_label": "MQLs",
                "source_value": 50,
                "target_label": "SQLs",
                "target_value": 5,
                "conversion_rate": 10.0,
            },
            "checkout": {"totals": {}, "channels": []},
            "payment_links": {"totals": {}, "channels": []},
            "qualification": {"totals": {}, "channels": []},
            "bottlenecks": [],
            "available": None,
            "period": "last_30_days",
            "last_updated": None,
        }

        call_args = []

        async def mock_get(*args):
            call_args.append(args)
            # Return opportunity cache on the right stage key
            if len(args) > 1 and args[1] == "opportunity":
                return opportunity_cache
            return None

        svc, _ = _make_summary_svc(cache=AsyncMock())
        svc.cache.get = mock_get
        svc.cache.set = AsyncMock()

        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
        ) as MockSales:
            MockSales.return_value.get_sales_summary.return_value = []
            result = _run(svc.get_summary(TENANT_ID))

        assert result is not None
        assert len(result.stages) == 8


# ─── ExpansionStageService — offer_port and renewals/upsells ─────────────────


def _make_expansion_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.expansion_stage import (
        ExpansionStageService,
    )

    db = MagicMock()
    return ExpansionStageService(db=db, cache=cache), db


class TestExpansionWithOfferPort:
    def test_offer_port_called_when_present(self):
        svc, _db = _make_expansion_svc()
        offer_port = AsyncMock()
        offer_port.get_offers_by_tenant = AsyncMock(return_value=[])
        svc.offer_port = offer_port

        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_expansion_sales_grouped.return_value = {"renewals": [], "upsells": []}
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 0
            repo.get_active_customer_count.return_value = 0
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        offer_port.get_offers_by_tenant.assert_called_once_with(TENANT_ID)
        assert result is not None

    def test_renewals_currency_used_when_present(self):
        svc, _db = _make_expansion_svc()

        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            # renewals with currency PEN → lines 162-163
            renewal_row = (uuid.uuid4(), 2, 500.0, "PEN")
            repo.get_expansion_sales_grouped.return_value = {
                "renewals": [renewal_row],
                "upsells": [],
            }
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 0
            repo.get_active_customer_count.return_value = 0
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None

    def test_upsells_currency_used_when_no_renewals(self):
        svc, _db = _make_expansion_svc()

        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.expansion_repository.ExpansionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            # no renewals → upsell currency used → line 165
            upsell_row = (uuid.uuid4(), 1, 200.0, "MXN")
            repo.get_expansion_sales_grouped.return_value = {
                "renewals": [],
                "upsells": [upsell_row],
            }
            repo.get_churn_data_by_offer.return_value = []
            repo.get_total_churn_count.return_value = 0
            repo.get_active_customer_count.return_value = 0
            repo.get_avg_ltv.return_value = (0.0, "USD")
            repo.get_expansion_customer_count.return_value = 0

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None


# ─── AdoptionStageService — offer_port ────────────────────────────────────────


def _make_adoption_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.adoption_stage import (
        AdoptionStageService,
    )

    db = MagicMock()
    return AdoptionStageService(db=db, cache=cache), db


class TestAdoptionWithOfferPort:
    def test_offer_port_called_when_present(self):
        svc, _db = _make_adoption_svc()
        offer_port = AsyncMock()

        offer_mock = MagicMock()
        offer_mock.id = uuid.uuid4()
        offer_mock.public_name = "Oferta Test"
        offer_port.get_offers_by_tenant = AsyncMock(return_value=[offer_mock])
        svc.offer_port = offer_port

        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.adoption_repository.AdoptionMetricsRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_total_customers_and_sales.return_value = (0, 0)
            repo.get_health_rows.return_value = []
            repo.get_refunds.return_value = (0, 0.0, "USD")

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        offer_port.get_offers_by_tenant.assert_called_once_with(TENANT_ID)
        assert result is not None


# ─── NurtureStageService — _build_retargeting_metrics and connected channels ──


def _make_nurture_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
        NurtureStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return NurtureStageService(db=db, cache=cache), db


class TestNurtureBuildRetargetingMetrics:
    def test_agg_rows_with_extra_dict(self):
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        agg = MagicMock()
        agg.metric_name = "reach"
        agg.value = 500.0
        agg.unit = "count"
        agg.currency = None
        agg.extra = {"age_18_24": 100, "age_25_34": 200}

        result = NurtureStageService._build_retargeting_metrics([agg])
        assert len(result) == 1
        assert result[0].name == "reach"
        assert result[0].value == 500.0
        assert result[0].breakdown == {"age_18_24": 100, "age_25_34": 200}

    def test_agg_rows_with_empty_extra_dict(self):
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        agg = MagicMock()
        agg.metric_name = "impressions"
        agg.value = 1000.0
        agg.unit = "count"
        agg.currency = None
        agg.extra = {}  # empty dict → breakdown=None

        result = NurtureStageService._build_retargeting_metrics([agg])
        assert len(result) == 1
        assert result[0].breakdown is None

    def test_agg_rows_with_no_extra(self):
        from luana_core_analytics_engine.application.services.stage_services.nurture_stage import (
            NurtureStageService,
        )

        agg = MagicMock(spec=["metric_name", "value", "unit", "currency"])
        # spec without 'extra' → getattr returns AttributeError → caught as None
        agg.metric_name = "clicks"
        agg.value = 50.0
        agg.unit = "count"
        agg.currency = None

        result = NurtureStageService._build_retargeting_metrics([agg])
        assert len(result) == 1
        assert result[0].breakdown is None


class TestNurtureConnectedChannels:
    def _patch_registry(self):
        return patch("luana_core_analytics_engine.application.services.stage_services.nurture_stage.ChannelRegistry")

    def _patch_cost(self):
        return patch("luana_core_analytics_engine.application.services.stage_services.nurture_stage.StageCostService")

    def test_connected_channel_appears_in_group(self):
        svc, _db = _make_nurture_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(
                return_value={
                    "connected": [
                        {
                            "slug": "email-nurture",
                            "name": "Email Nurture",
                            "channel_type": "email",
                            "source_label": "Email",
                            "provider_name": "mailerlite",
                            "connection_config": {},
                        }
                    ],
                    "available": [],
                }
            )
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None
            cost_svc.get_group_cost_per_mql.return_value = None

            with (
                patch(
                    "luana_core_analytics_engine.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
                ) as MockNurtRepo,
                patch(
                    "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
                ) as MockOfficialRepo,
            ):
                repo = MockNurtRepo.return_value
                repo.count_new_mqls.return_value = 5
                repo.count_leads_in_period.return_value = 50
                repo.count_email_events.return_value = {"emails_sent": 100, "opens": 30, "clicks": 10}
                repo.count_followup_events.return_value = {}
                official = MockOfficialRepo.return_value
                official.get_channel_summary.return_value = []
                official.get_channel_metrics.return_value = {}

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert len(result.automation.channels) == 1
        assert result.automation.channels[0].slug == "email-nurture"

    def test_retargeting_cpm_written_to_totals(self):
        svc, _db = _make_nurture_svc()
        with self._patch_registry() as MockReg, self._patch_cost() as MockCost:
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_retargeting_spend.return_value = {}
            cost_svc.calculate_cost_per_mql.return_value = None
            # Non-None group cost per MQL → triggers lines 272, 275
            cost_svc.get_group_cost_per_mql.side_effect = lambda grp, *args: 5.0 if grp == "retargeting" else 3.0

            with (
                patch(
                    "luana_core_analytics_engine.application.services.stage_services.nurture_stage.NurtureMetricsRepository"
                ) as MockNurtRepo,
                patch(
                    "luana_core_analytics_engine.application.services.stage_services.nurture_stage.OfficialMetricsRepository"
                ) as MockOfficialRepo,
            ):
                repo = MockNurtRepo.return_value
                repo.count_new_mqls.return_value = 10
                repo.count_leads_in_period.return_value = 100
                repo.count_email_events.return_value = {}
                repo.count_followup_events.return_value = {}
                official = MockOfficialRepo.return_value
                official.get_channel_summary.return_value = []

                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.retargeting.totals.get("cost_per_mql") == 5.0
        assert result.automation.totals.get("cost_per_mql") == 3.0


# ─── OpportunityStageService — connected channels and cache set ───────────────


def _make_opp_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.opportunity_stage import (
        OpportunityStageService,
    )

    db = MagicMock()
    return OpportunityStageService(db=db, cache=cache), db


class TestOpportunityConnectedChannels:
    def _patches(self):
        return (
            patch("luana_core_analytics_engine.application.services.stage_services.opportunity_stage.ChannelRegistry"),
            patch("luana_core_analytics_engine.application.services.stage_services.opportunity_stage.StageCostService"),
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ),
        )

    def _setup_opp_mocks(self, mock_reg, mock_cost, mock_opp_repo, connected=None):
        reg = mock_reg.return_value
        reg.get_available_channels = AsyncMock(return_value={"connected": connected or [], "available": []})
        cost_svc = mock_cost.return_value
        cost_svc.get_channel_costs.return_value = {}
        cost_svc.calculate_cost_per_mql.return_value = None

        opp_repo = mock_opp_repo.return_value
        opp_repo.count_new_sqls.return_value = 0
        opp_repo.count_mqls_in_period.return_value = 0
        opp_repo.count_checkout_events.return_value = {
            "checkout_initiated": {"count": 0, "value": 0.0},
            "cart_abandoned": {"count": 0},
        }
        opp_repo.count_meeting_events.return_value = {
            "booked": 0,
            "completed": 0,
            "no_show": 0,
            "rescheduled": 0,
        }
        opp_repo.count_payment_link_events.return_value = {"count": 0, "value": 0.0}

    def test_connected_channel_appears_in_group(self):
        svc, _db = _make_opp_svc()
        connected = [
            {
                "slug": "shopify-checkout",
                "name": "Shopify Checkout",
                "channel_type": "checkout",
                "source_label": "Shopify",
                "provider_name": "shopify",
                "connection_config": {},
            }
        ]
        with (
            patch(
                "luana_core_analytics_engine.application.services.stage_services.opportunity_stage.ChannelRegistry"
            ) as MockReg,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.opportunity_stage.StageCostService"
            ) as MockCost,
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ) as MockOppRepo,
        ):
            self._setup_opp_mocks(MockReg, MockCost, MockOppRepo, connected=connected)
            with patch(
                "luana_core_analytics_engine.application.services.stage_services.opportunity_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo:
                MockOfficialRepo.return_value.get_channel_metrics.return_value = {}
                result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert len(result.checkout.channels) == 1
        assert result.checkout.channels[0].slug == "shopify-checkout"

    def test_cache_set_called_when_cache_present(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_opp_svc(cache=cache)

        with (
            patch(
                "luana_core_analytics_engine.application.services.stage_services.opportunity_stage.ChannelRegistry"
            ) as MockReg,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.opportunity_stage.StageCostService"
            ) as MockCost,
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.opportunity_repository.OpportunityMetricsRepository"
            ) as MockOppRepo,
        ):
            self._setup_opp_mocks(MockReg, MockCost, MockOppRepo)
            _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()


# ─── AttractionStageService static helpers ────────────────────────────────────


class TestAttractionClassifyError:
    def test_no_error_returns_none(self):
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        result = AttractionStageService._classify_error(None)
        assert result is None

    def test_known_error_key_returns_message(self):
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        result = AttractionStageService._classify_error("invalid_token error from meta")
        assert result is not None
        assert isinstance(result, str)

    def test_unknown_error_returns_default_message(self):
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        result = AttractionStageService._classify_error("some_random_error_xyz")
        assert result == "Servicio no disponible"


class TestAttractionDetectStaleStatus:
    def _svc(self):
        from luana_core_analytics_engine.application.services.stage_services.attraction_stage import (
            AttractionStageService,
        )

        return AttractionStageService(db=MagicMock())

    def test_no_provider_name_returns_not_stale(self):
        svc = self._svc()
        stale, err = svc._detect_stale_status("", TENANT_ID, {}, MagicMock())
        assert stale is False
        assert err is None

    def test_internal_provider_returns_not_stale(self):
        svc = self._svc()
        stale, err = svc._detect_stale_status("internal", TENANT_ID, {}, MagicMock())
        assert stale is False
        assert err is None

    def test_provider_run_is_none_returns_not_stale(self):
        svc = self._svc()
        run_repo = MagicMock()
        run_repo.get_latest.return_value = None
        stale, err = svc._detect_stale_status("meta-provider", TENANT_ID, {}, run_repo)
        assert stale is False
        assert err is None

    def test_failed_status_returns_stale(self):
        svc = self._svc()
        run = MagicMock()
        run.status = "failed"
        run.error = "invalid_token"
        run_repo = MagicMock()
        run_repo.get_latest.return_value = run
        stale, _err = svc._detect_stale_status("meta", TENANT_ID, {}, run_repo)
        assert stale is True

    def test_partial_success_with_failures_returns_message(self):
        svc = self._svc()
        run = MagicMock()
        run.status = "partial_success"
        run.sub_extractor_failures = [{"extractor_name": "ig_organic"}, {"extractor_name": "meta_ads"}]
        run_repo = MagicMock()
        run_repo.get_latest.return_value = run
        stale, err = svc._detect_stale_status("meta", TENANT_ID, {}, run_repo)
        assert stale is False
        assert "Parcial" in err

    def test_partial_success_no_failures_not_stale(self):
        svc = self._svc()
        run = MagicMock()
        run.status = "partial_success"
        run.sub_extractor_failures = []
        run_repo = MagicMock()
        run_repo.get_latest.return_value = run
        stale, err = svc._detect_stale_status("meta", TENANT_ID, {}, run_repo)
        assert stale is False
        assert err is None


# ─── SalesStageService — subscription labels, high CAC, _group_raw_sales ──────


class TestSalesGroupRawSalesUnsoldOffers:
    def test_unsold_offer_added_to_adquisicion(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _group_raw_sales,
        )

        offer_mock = MagicMock()
        offer_mock.currency = "MXN"
        offer_mock.value_level = "high"
        offer_id = str(uuid.uuid4())
        offer_map = {offer_id: offer_mock}

        # No raw_sales → offer not sold → should appear in adquisicion with count=0
        stage_data, _stage_revenue, _display_currency = _group_raw_sales([], offer_map)

        assert offer_id in stage_data["adquisicion"]
        assert stage_data["adquisicion"][offer_id]["count"] == 0


class TestSalesBuildOfferSaleDtoSubscription:
    def test_subscription_adquisicion_sets_new_subs(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _build_offer_sale_dto,
        )

        offer = MagicMock()
        offer.value_level = "high"
        offer.public_name = "Plan Premium"
        offer.offer_type = "programa"
        offer.pricing_type = "subscription"
        offer_id = str(uuid.uuid4())
        offer_map = {offer_id: offer}

        data = {
            "count": 5,
            "revenue": 500.0,
            "currency": "MXN",
            "sources": {},
            "unique_customers": 5,
        }

        with patch(
            "luana_core_analytics_engine.application.services.stage_services.sales_stage.get_subscription_labels",
            return_value={"new_label": "Nuevas suscripciones", "renewal_label": "Renovaciones"},
        ):
            result = _build_offer_sale_dto(offer_id, data, offer_map, "adquisicion")

        assert result is not None
        assert result.new_subscriptions == 5  # line 137-138
        assert result.subscription_new_label == "Nuevas suscripciones"

    def test_subscription_expansion_sets_renewals(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _build_offer_sale_dto,
        )

        offer = MagicMock()
        offer.value_level = "high"
        offer.public_name = "Plan Premium"
        offer.offer_type = "programa"
        offer.pricing_type = "subscription"
        offer_id = str(uuid.uuid4())
        offer_map = {offer_id: offer}

        data = {
            "count": 3,
            "revenue": 300.0,
            "currency": "MXN",
            "sources": {},
            "unique_customers": 3,
        }

        with patch(
            "luana_core_analytics_engine.application.services.stage_services.sales_stage.get_subscription_labels",
            return_value={"new_label": "Nuevas suscripciones", "renewal_label": "Renovaciones"},
        ):
            result = _build_offer_sale_dto(offer_id, data, offer_map, "expansion")

        assert result is not None
        assert result.renewals == 3  # lines 140-141


class TestSalesBuildSalesBottlenecksHighCac:
    def test_high_cac_warning_bottleneck(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        # HIGH_CAC_WARNING_RATIO=0.33, HIGH_CAC_CRITICAL_RATIO=0.50
        # cac=40, aov=100 → ratio=0.4 → >= 0.33 but < 0.50 → warning
        bottlenecks = _build_sales_bottlenecks(
            conv_rate=10.0,
            sql_count=10,
            cac=40.0,
            new_customers=10,
            total_rev=1000.0,
        )
        assert any(b.type == "high_cac_ratio" and b.severity == "warning" for b in bottlenecks)

    def test_high_cac_critical_bottleneck(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            _build_sales_bottlenecks,
        )

        # cac=60, aov=100 → ratio=0.6 → >= 0.50 → critical
        bottlenecks = _build_sales_bottlenecks(
            conv_rate=10.0,
            sql_count=10,
            cac=60.0,
            new_customers=10,
            total_rev=1000.0,
        )
        assert any(b.type == "high_cac_ratio" and b.severity == "critical" for b in bottlenecks)


class TestSalesWithOfferPort:
    def test_offer_port_called_when_present(self):
        from luana_core_analytics_engine.application.services.stage_services.sales_stage import (
            SalesStageService,
        )

        db = MagicMock()
        offer_port = AsyncMock()
        offer_mock = MagicMock()
        offer_mock.id = uuid.uuid4()
        offer_mock.value_level = "high"
        offer_mock.public_name = "Test Offer"
        offer_mock.offer_type = "programa"
        offer_mock.pricing_type = "one_time"
        offer_mock.currency = "MXN"
        offer_port.get_offers_by_tenant = AsyncMock(return_value=[offer_mock])

        svc = SalesStageService(db=db, offer_port=offer_port)

        with (
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.sales_metrics_repository.SalesMetricsRepository"
            ) as MockSales,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.sales_stage.StageCostService"
            ) as MockCostSvc,
            patch(
                "luana_core_analytics_engine.application.services.stage_services.sales_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo,
        ):
            MockSales.return_value.get_sales_summary.return_value = []
            MockSales.return_value.get_total_conversion_customers.return_value = 0
            MockSales.return_value.get_total_sql_count.return_value = 0
            cost_svc = MockCostSvc.return_value
            cost_svc.get_total_funnel_investment.return_value = (0.0, False)
            MockOfficialRepo.return_value.get_channel_metrics.return_value = {}
            MockOfficialRepo.return_value.get_metrics.return_value = []
            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        offer_port.get_offers_by_tenant.assert_called_once_with(TENANT_ID)
        assert result is not None
