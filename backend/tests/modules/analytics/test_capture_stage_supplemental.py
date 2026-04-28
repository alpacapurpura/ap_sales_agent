"""Tests for CaptureStageService — uncovered methods and branches."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TENANT_ID = uuid.uuid4()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_svc(cache=None, connection_port=None):
    from src.modules.analytics.application.services.stage_services.capture_stage import (
        CaptureStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return CaptureStageService(db=db, cache=cache, connection_port=connection_port), db


# ─── _merge_manychat_into_meta ────────────────────────────────────────────────


class TestMergeManyChat:
    def _ch(self, slug, name="Test"):
        from src.modules.analytics.application.dto.attraction_dto import ChannelMetricDTO

        return ChannelMetricDTO(
            slug=slug, name=name, channel_type="messaging", metrics=[], source_label="Test", connected=True
        )

    def test_no_meta_dto_skips(self):
        svc, _ = _make_svc()
        channels = [self._ch("landing-form")]
        svc._merge_manychat_into_meta(channels, {}, {})
        assert len(channels) == 1  # nothing merged

    def test_no_mc_dto_skips(self):
        svc, _ = _make_svc()
        channels = [self._ch("ig-dm")]
        svc._merge_manychat_into_meta(channels, {}, {})
        assert len(channels) == 1

    def test_both_exist_mc_removed_and_subsources_set(self):
        svc, _ = _make_svc()
        meta_ch = self._ch("ig-dm", "IG DM")
        mc_ch = self._ch("manychat-ig", "MC IG")
        channels = [meta_ch, mc_ch]
        svc._merge_manychat_into_meta(channels, {"ig-dm": 10, "manychat-ig": 5}, {"ig-dm": 8, "manychat-ig": 3})
        assert len(channels) == 1
        assert channels[0].slug == "ig-dm"
        assert len(channels[0].sub_sources) == 2

    def test_mc_metrics_appended_to_meta_dto(self):
        """Lines 102-103: mc_dto metrics not in meta_dto are appended."""
        svc, _ = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import (
            ChannelMetricDTO,
            MetricValueDTO,
        )

        meta_m = MetricValueDTO(name="leads", value=5.0)
        mc_m = MetricValueDTO(name="automation_flows", value=3.0)
        meta_ch = ChannelMetricDTO(
            slug="ig-dm", name="IG DM", channel_type="messaging", metrics=[meta_m], source_label="IG", connected=True
        )
        mc_ch = ChannelMetricDTO(
            slug="manychat-ig",
            name="MC IG",
            channel_type="messaging",
            metrics=[mc_m],
            source_label="MC",
            connected=True,
        )
        channels = [meta_ch, mc_ch]
        svc._merge_manychat_into_meta(channels, {}, {})
        metric_names = [m.name for m in channels[0].metrics]
        assert "automation_flows" in metric_names

    def test_duplicate_metrics_not_appended(self):
        svc, _ = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import (
            ChannelMetricDTO,
            MetricValueDTO,
        )

        shared_m = MetricValueDTO(name="leads", value=5.0)
        meta_ch = ChannelMetricDTO(
            slug="ig-dm", name="IG DM", channel_type="messaging", metrics=[shared_m], source_label="IG", connected=True
        )
        mc_ch = ChannelMetricDTO(
            slug="manychat-ig",
            name="MC IG",
            channel_type="messaging",
            metrics=[shared_m],
            source_label="MC",
            connected=True,
        )
        channels = [meta_ch, mc_ch]
        svc._merge_manychat_into_meta(channels, {}, {})
        # should not duplicate "leads"
        leads = [m for m in channels[0].metrics if m.name == "leads"]
        assert len(leads) == 1


# ─── _build_website_capture_dto ──────────────────────────────────────────────


class TestBuildWebsiteCaptureDtoUnit:
    def test_returns_channel_metric_dto(self):
        """Lines 115-177: body of _build_website_capture_dto."""
        svc, _db = _make_svc()
        ch = {
            "slug": "website-capture",
            "name": "Website Capture",
            "channel_type": "web_capture",
            "source_label": "Website",
        }
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {}
            MockRepo.return_value = repo_instance

            result = svc._build_website_capture_dto(ch, TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))

        assert result.slug == "website-capture"
        assert result.provider_name == "internal"

    def test_total_computed_from_components_when_zero(self):
        svc, _db = _make_svc()
        ch = {
            "slug": "website-capture",
            "name": "Website Capture",
            "channel_type": "web_capture",
            "source_label": "Website",
        }
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()

            # ga4_organic returns sessions=300, others empty
            def mock_get_metrics(tid, provider, slug, sd, ed):
                if slug == "google-organic":
                    return {"sessions": 300}
                return {}

            repo_instance.get_channel_metrics.side_effect = mock_get_metrics
            MockRepo.return_value = repo_instance

            result = svc._build_website_capture_dto(ch, TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))

        visitors_metric = next(m for m in result.metrics if m.name == "visitors")
        assert visitors_metric.value == 300.0

    def test_connected_true_when_data_available(self):
        svc, _db = _make_svc()
        ch = {
            "slug": "website-capture",
            "name": "Website Capture",
            "channel_type": "web_capture",
            "source_label": "Website",
        }
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()

            def mock_get_metrics(tid, provider, slug, sd, ed):
                if slug == "website-total":
                    return {"sessions": 1000}
                return {}

            repo_instance.get_channel_metrics.side_effect = mock_get_metrics
            MockRepo.return_value = repo_instance

            result = svc._build_website_capture_dto(ch, TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))

        assert result.connected is True


# ─── _supplement_manychat_metrics ────────────────────────────────────────────


class TestSupplementManyChat:
    def test_new_metrics_appended(self):
        """Lines 196-207: body of _supplement_manychat_metrics."""
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=5.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {"automation_flows": 10}
            MockRepo.return_value = repo_instance

            svc._supplement_manychat_metrics(metrics, TENANT_ID, "manychat-ig", date(2026, 3, 1), date(2026, 3, 31))

        names = [m.name for m in metrics]
        assert "automation_flows" in names

    def test_existing_metric_not_duplicated(self):
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=5.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {"leads": 8}  # already exists
            MockRepo.return_value = repo_instance

            svc._supplement_manychat_metrics(metrics, TENANT_ID, "manychat-ig", date(2026, 3, 1), date(2026, 3, 31))

        leads_metrics = [m for m in metrics if m.name == "leads"]
        assert len(leads_metrics) == 1

    def test_empty_mc_metrics_no_change(self):
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=5.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {}
            MockRepo.return_value = repo_instance

            svc._supplement_manychat_metrics(metrics, TENANT_ID, "manychat-ig", date(2026, 3, 1), date(2026, 3, 31))

        assert len(metrics) == 1


# ─── _supplement_mailerlite_metrics ──────────────────────────────────────────


class TestSupplementMailerlite:
    def test_lead_count_zero_substitutes_new_subscribers(self):
        """Lines 229-231: lead_count=0 and ns>0 → replace leads metric."""
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=0.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {"new_subscribers": 15}
            MockRepo.return_value = repo_instance

            result = svc._supplement_mailerlite_metrics(
                metrics, 0, TENANT_ID, "email-capture", date(2026, 3, 1), date(2026, 3, 31)
            )

        leads_metrics = [m for m in result if m.name == "leads"]
        assert len(leads_metrics) == 1
        assert leads_metrics[0].value == 15.0

    def test_lead_count_nonzero_keeps_existing(self):
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=5.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {"new_subscribers": 15, "open_rate": 30.0}
            MockRepo.return_value = repo_instance

            result = svc._supplement_mailerlite_metrics(
                metrics, 5, TENANT_ID, "email-capture", date(2026, 3, 1), date(2026, 3, 31)
            )

        leads_metrics = [m for m in result if m.name == "leads"]
        assert leads_metrics[0].value == 5.0  # not replaced
        assert any(m.name == "open_rate" for m in result)

    def test_new_subscribers_not_duplicated_in_metrics(self):
        """new_subscribers excluded from appended metrics (lines 232-235)."""
        svc, _db = _make_svc()
        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        metrics = [MetricValueDTO(name="leads", value=5.0)]
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            repo_instance = MagicMock()
            repo_instance.get_channel_metrics.return_value = {"new_subscribers": 15}
            MockRepo.return_value = repo_instance

            result = svc._supplement_mailerlite_metrics(
                metrics, 5, TENANT_ID, "email-capture", date(2026, 3, 1), date(2026, 3, 31)
            )

        # new_subscribers should NOT appear as extra metric
        assert not any(m.name == "new_subscribers" for m in result)


# ─── _get_merged_costs ────────────────────────────────────────────────────────


class TestGetMergedCosts:
    def test_empty_costs_returns_empty_dict(self):
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
        ) as MockCost:
            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            MockCost.return_value = cost_svc

            _, all_costs = svc._get_merged_costs(TENANT_ID, [])
        assert all_costs == {}

    def test_channel_costs_accumulated(self):
        """Lines 251, 253: loop bodies execute when costs non-empty."""
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
        ) as MockCost:
            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {"ig-dm": 50.0, "meta-ads": 100.0}
            cost_svc.get_prorated_agency_costs.return_value = {"ig-dm": 25.0}
            MockCost.return_value = cost_svc

            _, all_costs = svc._get_merged_costs(TENANT_ID, ["ig-dm", "meta-ads"])

        assert all_costs["ig-dm"] == 75.0  # 50 + 25 prorated
        assert all_costs["meta-ads"] == 100.0

    def test_prorated_only_costs_also_accumulated(self):
        """Line 253: prorated loop body executes."""
        svc, _db = _make_svc()
        with patch(
            "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
        ) as MockCost:
            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {"ig-dm": 30.0}
            MockCost.return_value = cost_svc

            _, all_costs = svc._get_merged_costs(TENANT_ID, ["ig-dm"])

        assert all_costs["ig-dm"] == 30.0


# ─── _build_capture_channel_dto (manychat + email_marketing branches) ─────────


class TestBuildCaptureChannelDtoProviders:
    def _ch(self, provider):
        return {
            "slug": "ig-dm" if provider == "manychat" else "email-capture",
            "name": "Test",
            "channel_type": "messaging",
            "source_label": "Test",
            "provider_name": provider,
            "connection_config": {},
        }

    def test_manychat_provider_calls_supplement(self):
        """Line 315: manychat branch in _build_capture_channel_dto."""
        svc, _db = _make_svc()
        svc._supplement_manychat_metrics = MagicMock()

        with patch("src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"):
            result = svc._build_capture_channel_dto(
                self._ch("manychat"), TENANT_ID, {}, {}, {}, 100, date(2026, 3, 1), date(2026, 3, 31)
            )

        svc._supplement_manychat_metrics.assert_called_once()
        assert result.slug == "ig-dm"

    def test_email_marketing_provider_calls_supplement(self):
        """Line 323: email_marketing branch in _build_capture_channel_dto."""
        svc, _db = _make_svc()

        from src.modules.analytics.application.dto.attraction_dto import MetricValueDTO

        svc._supplement_mailerlite_metrics = MagicMock(return_value=[])

        with patch("src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"):
            svc._build_capture_channel_dto(
                self._ch("email_marketing"), TENANT_ID, {}, {}, {}, 100, date(2026, 3, 1), date(2026, 3, 31)
            )

        svc._supplement_mailerlite_metrics.assert_called_once()


# ─── get_metrics full flow ─────────────────────────────────────────────────────


class TestGetMetricsFlow:
    def _setup_channel_registry(self, connection_port, channels):
        connection_port.get_channels = AsyncMock(return_value=channels)

    def test_cache_hit_returns_dto(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {"total_leads": 10, "conversion_rate": 5.0, "cost_per_lead": 20.0},
            "mini_funnel": {
                "source_label": "Visitantes",
                "source_value": 200,
                "target_label": "Leads",
                "target_value": 10,
                "conversion_rate": 5.0,
            },
            "web_infrastructure": {"totals": {}, "channels": []},
            "ai_agent": {"totals": {}, "channels": []},
            "available": None,
            "period": "last_30_days",
            "last_updated": None,
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, _db = _make_svc(cache=cache)

        from src.modules.analytics.domain.period_config import DateRange

        dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")
        result = _run(svc.get_metrics(TENANT_ID, dr))
        assert result.header_kpis.total_leads == 10

    def test_cache_miss_with_connected_channels_builds_result(self):
        """Lines 396-420: loop body with connected channels executes."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        connection_port = AsyncMock()
        svc, db = _make_svc(cache=cache, connection_port=connection_port)
        db.execute.return_value.scalar.return_value = 0

        channel_split = {
            "connected": [
                {
                    "slug": "ig-dm",
                    "name": "IG DM",
                    "channel_type": "messaging",
                    "source_label": "IG",
                    "provider_name": "",
                    "connection_config": {},
                }
            ],
            "available": [],
        }

        from src.modules.analytics.domain.period_config import DateRange

        dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")

        with (
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.ChannelRegistry"
            ) as MockRegistry,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureMetricsRepository"
            ) as MockCaptureRepo,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
            ) as MockCostSvc,
        ):
            reg_instance = MagicMock()
            reg_instance.get_available_channels = AsyncMock(return_value=channel_split)
            MockRegistry.return_value = reg_instance

            capture_repo = MagicMock()
            capture_repo.count_leads_by_source.return_value = {"ig-dm": 5}
            capture_repo.count_conversations_by_channel.return_value = {}
            capture_repo.count_leads_by_source_detailed.return_value = {}
            MockCaptureRepo.return_value = capture_repo

            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = 0.0
            MockCostSvc.return_value = cost_svc

            result = _run(svc.get_metrics(TENANT_ID, dr))

        assert result.header_kpis.total_leads == 5
        cache.set.assert_called_once()

    def test_website_capture_channel_uses_website_dto(self):
        """Lines 399-409: website-capture slug routes to _build_website_capture_dto."""
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        connection_port = AsyncMock()
        svc, db = _make_svc(cache=cache, connection_port=connection_port)
        db.execute.return_value.scalar.return_value = 500

        channel_split = {
            "connected": [
                {
                    "slug": "website-capture",
                    "name": "Website Capture",
                    "channel_type": "web_capture",
                    "source_label": "Website",
                }
            ],
            "available": [],
        }

        from src.modules.analytics.domain.period_config import DateRange

        dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")

        with (
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.ChannelRegistry"
            ) as MockRegistry,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureMetricsRepository"
            ) as MockCaptureRepo,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
            ) as MockCostSvc,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.OfficialMetricsRepository"
            ) as MockOfficialRepo,
        ):
            reg_instance = MagicMock()
            reg_instance.get_available_channels = AsyncMock(return_value=channel_split)
            MockRegistry.return_value = reg_instance

            capture_repo = MagicMock()
            capture_repo.count_leads_by_source.return_value = {}
            capture_repo.count_conversations_by_channel.return_value = {}
            capture_repo.count_leads_by_source_detailed.return_value = {}
            MockCaptureRepo.return_value = capture_repo

            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = 0.0
            MockCostSvc.return_value = cost_svc

            official_repo = MagicMock()
            official_repo.get_channel_metrics.return_value = {}
            MockOfficialRepo.return_value = official_repo

            result = _run(svc.get_metrics(TENANT_ID, dr))

        # website-capture goes into web_infrastructure group
        assert len(result.web_infrastructure.channels) == 1
        assert result.web_infrastructure.channels[0].slug == "website-capture"

    def test_no_cache_no_channels_returns_empty_result(self):
        svc, db = _make_svc()
        db.execute.return_value.scalar.return_value = 0

        from src.modules.analytics.domain.period_config import DateRange

        dr = DateRange(date(2026, 3, 1), date(2026, 3, 31), "last_30_days")

        with (
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.ChannelRegistry"
            ) as MockRegistry,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureMetricsRepository"
            ) as MockCaptureRepo,
            patch(
                "src.modules.analytics.application.services.stage_services.capture_stage.CaptureCostService"
            ) as MockCostSvc,
        ):
            reg_instance = MagicMock()
            reg_instance.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            MockRegistry.return_value = reg_instance

            capture_repo = MagicMock()
            capture_repo.count_leads_by_source.return_value = {}
            capture_repo.count_conversations_by_channel.return_value = {}
            capture_repo.count_leads_by_source_detailed.return_value = {}
            MockCaptureRepo.return_value = capture_repo

            cost_svc = MagicMock()
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = 0.0
            MockCostSvc.return_value = cost_svc

            result = _run(svc.get_metrics(TENANT_ID, dr))

        assert result.header_kpis.total_leads == 0
