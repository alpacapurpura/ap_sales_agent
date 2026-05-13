"""Tests for CaptureStageService."""

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


def _make_svc(cache=None):
    from luana_core_analytics_engine.application.services.stage_services.capture_stage import (
        CaptureStageService,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return CaptureStageService(db=db, cache=cache), db


class TestCaptureStageServiceCacheHit:
    def test_returns_cached_dto(self):
        cache = AsyncMock()
        cached = {
            "header_kpis": {"total_leads": 20, "conversion_rate": 5.0, "cost_per_lead": None},
            "mini_funnel": {
                "source_label": "Visitantes",
                "source_value": 400,
                "target_label": "Leads",
                "target_value": 20,
                "conversion_rate": 5.0,
            },
            "web_infrastructure": {"totals": {}, "channels": []},
            "ai_agent": {"totals": {}, "channels": []},
            "available": None,
            "period": "last_30_days",
            "last_updated": "2026-03-31T00:00:00",
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc, db = _make_svc(cache=cache)

        result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.total_leads == 20
        db.execute.assert_not_called()


class TestCaptureStageServiceCacheMiss:
    def _patch_registry(self):
        return patch("luana_core_analytics_engine.application.services.stage_services.capture_stage.ChannelRegistry")

    def _patch_cost(self):
        return patch("luana_core_analytics_engine.application.services.stage_services.capture_stage.CaptureCostService")

    def _patch_capture_repo(self):
        return patch(
            "luana_core_analytics_engine.application.services.stage_services.capture_stage.CaptureMetricsRepository"
        )

    def _patch_official_repo(self):
        return patch(
            "luana_core_analytics_engine.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        )

    def test_empty_channels_returns_dto(self):
        svc, _db = _make_svc()
        with (
            self._patch_registry() as MockReg,
            self._patch_cost() as MockCost,
            self._patch_capture_repo() as MockCaptRepo,
            self._patch_official_repo() as MockOfficialRepo,
        ):
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = None

            capt_repo = MockCaptRepo.return_value
            capt_repo.count_leads_by_source.return_value = {}
            capt_repo.count_conversations_by_channel.return_value = {}
            capt_repo.count_leads_by_source_detailed.return_value = {}

            MockOfficialRepo.return_value.get_channel_metrics.return_value = {}

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result is not None
        assert result.header_kpis.total_leads == 0

    def test_with_leads_computes_header(self):
        svc, _db = _make_svc()
        with (
            self._patch_registry() as MockReg,
            self._patch_cost() as MockCost,
            self._patch_capture_repo() as MockCaptRepo,
            self._patch_official_repo() as MockOfficialRepo,
        ):
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = None

            capt_repo = MockCaptRepo.return_value
            capt_repo.count_leads_by_source.return_value = {"ig-dm": 15, "email-capture": 5}
            capt_repo.count_conversations_by_channel.return_value = {}
            capt_repo.count_leads_by_source_detailed.return_value = {}

            MockOfficialRepo.return_value.get_channel_metrics.return_value = {}

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.header_kpis.total_leads == 20

    def test_sets_cache_after_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        svc, _db = _make_svc(cache=cache)
        with (
            self._patch_registry() as MockReg,
            self._patch_cost() as MockCost,
            self._patch_capture_repo() as MockCaptRepo,
            self._patch_official_repo() as MockOfficialRepo,
        ):
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(return_value={"connected": [], "available": []})
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = None

            capt_repo = MockCaptRepo.return_value
            capt_repo.count_leads_by_source.return_value = {}
            capt_repo.count_conversations_by_channel.return_value = {}
            capt_repo.count_leads_by_source_detailed.return_value = {}

            MockOfficialRepo.return_value.get_channel_metrics.return_value = {}

            _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        cache.set.assert_called_once()

    def test_available_channels_excluded_from_groups(self):
        svc, _db = _make_svc()
        with (
            self._patch_registry() as MockReg,
            self._patch_cost() as MockCost,
            self._patch_capture_repo() as MockCaptRepo,
            self._patch_official_repo() as MockOfficialRepo,
        ):
            reg = MockReg.return_value
            reg.get_available_channels = AsyncMock(
                return_value={
                    "connected": [],
                    "available": [
                        {
                            "slug": "tiktok-organic",
                            "name": "TikTok",
                            "channel_type": "social",
                            "source_label": "TikTok",
                        }
                    ],
                }
            )
            cost_svc = MockCost.return_value
            cost_svc.get_channel_costs.return_value = {}
            cost_svc.get_prorated_agency_costs.return_value = {}
            cost_svc.calculate_cal.return_value = None

            capt_repo = MockCaptRepo.return_value
            capt_repo.count_leads_by_source.return_value = {}
            capt_repo.count_conversations_by_channel.return_value = {}
            capt_repo.count_leads_by_source_detailed.return_value = {}

            MockOfficialRepo.return_value.get_channel_metrics.return_value = {}

            result = _run(svc.get_metrics(TENANT_ID, DATE_RANGE))

        assert result.available is not None
        assert len(result.available.channels) == 1


class TestMergeManyChat:
    """Test static _merge_manychat_into_meta method."""

    def test_no_meta_or_mc_no_change(self):
        from luana_core_analytics_engine.application.dto.attraction_dto import ChannelMetricDTO
        from luana_core_analytics_engine.application.services.stage_services.capture_stage import (
            CaptureStageService,
        )

        channels = [
            ChannelMetricDTO(
                slug="ig-organic",
                name="IG Organic",
                channel_type="social",
                metrics=[],
                source_label="IG",
                connected=True,
            )
        ]
        CaptureStageService._merge_manychat_into_meta(channels, {}, {})
        assert len(channels) == 1

    def test_merge_manychat_ig_into_igdm(self):
        from luana_core_analytics_engine.application.dto.attraction_dto import ChannelMetricDTO
        from luana_core_analytics_engine.application.services.stage_services.capture_stage import (
            CaptureStageService,
        )

        channels = [
            ChannelMetricDTO(
                slug="ig-dm", name="IG DM", channel_type="messaging", metrics=[], source_label="IG DM", connected=True
            ),
            ChannelMetricDTO(
                slug="manychat-ig",
                name="ManyChat IG",
                channel_type="messaging",
                metrics=[],
                source_label="MC",
                connected=True,
            ),
        ]
        CaptureStageService._merge_manychat_into_meta(
            channels, {"ig-dm": 8, "manychat-ig": 3}, {"ig-dm": 4, "manychat-ig": 2}
        )
        # manychat-ig merged into ig-dm, removed from list
        slugs = [c.slug for c in channels]
        assert "ig-dm" in slugs
        assert "manychat-ig" not in slugs
        ig_dm = next(c for c in channels if c.slug == "ig-dm")
        assert ig_dm.sub_sources is not None
        assert len(ig_dm.sub_sources) == 2


class TestBuildCaptureChannelDto:
    def test_builds_metrics_messaging_channel(self):
        svc, _db = _make_svc()
        ch = {
            "slug": "ig-dm",
            "name": "IG DM",
            "channel_type": "messaging",
            "source_label": "Instagram",
            "provider_name": "meta_direct",
        }
        dto = svc._build_capture_channel_dto(
            ch, TENANT_ID, {"ig-dm": 10}, {"ig-dm": 5}, {}, 200, date(2026, 3, 1), date(2026, 3, 31)
        )
        assert dto.slug == "ig-dm"
        metric_names = [m.name for m in dto.metrics]
        assert "leads" in metric_names
        assert "conversations" in metric_names

    def test_builds_metrics_non_messaging_channel(self):
        svc, _db = _make_svc()
        ch = {
            "slug": "email-capture",
            "name": "Email Capture",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "mailerlite",
        }
        with patch(
            "luana_core_analytics_engine.application.services.stage_services.capture_stage.OfficialMetricsRepository"
        ) as MockRepo:
            MockRepo.return_value.get_channel_metrics.return_value = {}
            dto = svc._build_capture_channel_dto(ch, TENANT_ID, {}, {}, {}, 0, date(2026, 3, 1), date(2026, 3, 31))
        assert dto.slug == "email-capture"
        metric_names = [m.name for m in dto.metrics]
        assert "leads" in metric_names
        # Non-messaging should NOT have conversations
        assert "conversations" not in metric_names
