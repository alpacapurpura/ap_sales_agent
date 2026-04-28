"""Tests for StageOverviewService."""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

TENANT_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_svc(cache=None, db=None):
    from src.modules.analytics.application.services.stage_services.overview_stage import (
        StageOverviewService,
    )

    return StageOverviewService(cache=cache, db=db or MagicMock())


# ─── get_stage_overview cache hit ─────────────────────────────────────────────


class TestGetStageOverviewCacheHit:
    def test_non_empty_cached_overview_returned(self):
        cache = AsyncMock()
        cached = {
            "stage": "capture",
            "header_kpis": {"total_leads": 20},
            "mini_funnel": None,
            "groups": [],
            "channel_list": [
                {
                    "slug": "ig-dm",
                    "name": "IG DM",
                    "channel_type": "messaging",
                    "group_key": "ai_agent",
                    "connected": True,
                    "headline_kpi": None,
                    "last_updated": None,
                    "stale": False,
                    "provider_name": None,
                }
            ],
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": None,
        }
        cache.get = AsyncMock(return_value=cached)
        cache.set = AsyncMock()
        svc = _make_svc(cache=cache)

        result = _run(svc.get_stage_overview(TENANT_ID, "capture", "last_30_days"))

        assert result.stage == "capture"
        assert len(result.channel_list) == 1

    def test_empty_cached_overview_falls_through(self):
        cache = AsyncMock()
        # First call: overview cache (empty channels) → fall through
        # Second call: stage cache → None
        call_count = [0]

        async def mock_get(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                # overview cache: no channels → fall through
                return {
                    "stage": "capture",
                    "header_kpis": {},
                    "mini_funnel": None,
                    "groups": [],
                    "channel_list": [],  # empty → fall through
                    "bottlenecks": [],
                    "period": "last_30_days",
                    "last_updated": None,
                }
            return None  # stage cache miss

        cache.get = mock_get
        cache.set = AsyncMock()
        svc = _make_svc(cache=cache)

        result = _run(svc.get_stage_overview(TENANT_ID, "capture", "last_30_days"))
        assert result.stage == "capture"
        assert result.channel_list == []


# ─── get_stage_overview cache miss ────────────────────────────────────────────


class TestGetStageOverviewCacheMiss:
    def test_no_cache_no_db_returns_empty(self):
        svc = _make_svc(cache=None, db=None)
        result = _run(svc.get_stage_overview(TENANT_ID, "attraction", "last_30_days"))
        assert result.stage == "attraction"
        assert result.channel_list == []

    def test_stage_data_in_cache_extracts_overview(self):
        cache = AsyncMock()
        # First call: overview cache miss; second call: stage cache hit
        stage_data = {
            "organic_social": {
                "totals": {"reach": 1000},
                "channels": [
                    {
                        "slug": "ig-organic",
                        "name": "IG Organic",
                        "channel_type": "organic_social",
                        "connected": True,
                        "metrics": [{"name": "reach", "value": 1000, "unit": "count"}],
                    }
                ],
            },
            "ga4_search": {"totals": {}, "channels": []},
            "paid": {"totals": {}, "channels": []},
            "outbound": {"totals": {}, "channels": []},
            "period": "last_30_days",
            "last_updated": None,
        }
        call_count = [0]

        async def mock_get(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # overview cache miss
            return stage_data  # stage cache hit

        cache.get = mock_get
        cache.set = AsyncMock()
        svc = _make_svc(cache=cache)

        result = _run(svc.get_stage_overview(TENANT_ID, "attraction", "last_30_days"))

        assert result.stage == "attraction"
        assert len(result.channel_list) == 1
        assert result.channel_list[0].slug == "ig-organic"
        cache.set.assert_called_once()

    def test_no_stage_data_with_db_triggers_compute(self):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        db = MagicMock()
        svc = _make_svc(cache=cache, db=db)

        # Patch _compute_stage_data to return None (simulating compute failure)
        svc._compute_stage_data = AsyncMock(return_value=None)

        result = _run(svc.get_stage_overview(TENANT_ID, "nurture", "last_30_days"))
        svc._compute_stage_data.assert_called_once()
        assert result.stage == "nurture"
        assert result.channel_list == []


# ─── _extract_overview ────────────────────────────────────────────────────────


class TestExtractOverview:
    def _svc(self):
        return _make_svc()

    def test_none_data_returns_empty(self):
        svc = self._svc()
        result = svc._extract_overview("capture", None)
        assert result.stage == "capture"
        assert result.channel_list == []
        assert result.header_kpis == {}

    def test_attraction_header_kpis_from_groups(self):
        svc = self._svc()
        data = {
            "organic_social": {"totals": {"reach": 500, "sessions": 200, "impressions": 3000}, "channels": []},
            "ga4_search": {"totals": {"reach": 100, "sessions": 50}, "channels": []},
            "paid": {"totals": {}, "channels": []},
            "outbound": {"totals": {}, "channels": []},
            "period": "last_30_days",
        }
        result = svc._extract_overview("attraction", data)
        assert result.header_kpis["total_reach"] == 600.0
        assert result.header_kpis["total_sessions"] == 250.0
        assert result.header_kpis["total_impressions"] == 3000.0

    def test_capture_header_kpis_from_header_dict(self):
        svc = self._svc()
        data = {
            "header_kpis": {"total_leads": 50, "conversion_rate": 5.0, "cost_per_lead": 12.0},
            "mini_funnel": None,
            "period": "last_30_days",
        }
        result = svc._extract_overview("capture", data)
        assert result.header_kpis["total_leads"] == 50.0
        assert result.header_kpis["conversion_rate"] == 5.0


# ─── _extract_header_kpis ─────────────────────────────────────────────────────


class TestExtractHeaderKpis:
    def test_missing_kpi_key_returns_none(self):
        svc = _make_svc()
        data = {"header_kpis": {"total_leads": 20}}  # missing conversion_rate
        result = svc._extract_header_kpis("capture", data)
        assert result["total_leads"] == 20.0
        assert result["conversion_rate"] is None

    def test_string_value_returns_none(self):
        svc = _make_svc()
        data = {"header_kpis": {"total_leads": "N/A"}}
        result = svc._extract_header_kpis("capture", data)
        assert result["total_leads"] is None


# ─── _extract_mini_funnel ─────────────────────────────────────────────────────


class TestExtractMiniFunnel:
    def test_none_returns_none(self):
        svc = _make_svc()
        assert svc._extract_mini_funnel({"mini_funnel": None}) is None

    def test_missing_key_returns_none(self):
        svc = _make_svc()
        assert svc._extract_mini_funnel({}) is None

    def test_non_dict_returns_none(self):
        svc = _make_svc()
        assert svc._extract_mini_funnel({"mini_funnel": "invalid"}) is None

    def test_valid_mini_funnel_extracted(self):
        svc = _make_svc()
        data = {
            "mini_funnel": {
                "source_label": "Visitantes",
                "source_value": 400,
                "target_label": "Leads",
                "target_value": 20,
                "conversion_rate": 5.0,
            }
        }
        result = svc._extract_mini_funnel(data)
        assert result is not None
        assert result.source_label == "Visitantes"
        assert result.conversion_rate == 5.0


# ─── _extract_groups ─────────────────────────────────────────────────────────


class TestExtractGroups:
    def test_missing_stage_returns_empty(self):
        svc = _make_svc()
        result = svc._extract_groups("unknown_stage", {})
        assert result == []

    def test_field_not_in_data_skipped(self):
        svc = _make_svc()
        result = svc._extract_groups("capture", {})  # no ai_agent / web_infrastructure
        assert result == []

    def test_group_with_channel_list_counted(self):
        svc = _make_svc()
        data = {
            "ai_agent": {
                "channels": [{"slug": "ig-dm"}, {"slug": "manychat-ig"}],
                "totals": {},
            }
        }
        result = svc._extract_groups("capture", data)
        groups = {g.group_key: g for g in result}
        assert groups["ai_agent"].channel_count == 2

    def test_non_list_channels_gives_zero_count(self):
        svc = _make_svc()
        data = {"ai_agent": {"channels": "not-a-list", "totals": {}}}
        result = svc._extract_groups("capture", data)
        groups = {g.group_key: g for g in result}
        assert groups["ai_agent"].channel_count == 0


# ─── _extract_channel_list ────────────────────────────────────────────────────


class TestExtractChannelList:
    def test_empty_data_returns_empty(self):
        svc = _make_svc()
        result = svc._extract_channel_list("capture", {})
        assert result == []

    def test_non_dict_group_data_skipped(self):
        svc = _make_svc()
        data = {"ai_agent": "not-a-dict"}
        result = svc._extract_channel_list("capture", data)
        assert result == []

    def test_non_list_channels_skipped(self):
        svc = _make_svc()
        data = {"ai_agent": {"channels": None, "totals": {}}}
        result = svc._extract_channel_list("capture", data)
        assert result == []

    def test_non_dict_channel_skipped(self):
        svc = _make_svc()
        data = {"ai_agent": {"channels": ["not-a-dict"], "totals": {}}}
        result = svc._extract_channel_list("capture", data)
        assert result == []

    def test_valid_channel_extracted_with_headline_kpi(self):
        svc = _make_svc()
        data = {
            "ai_agent": {
                "channels": [
                    {
                        "slug": "ig-dm",
                        "name": "IG DM",
                        "channel_type": "messaging",
                        "connected": True,
                        "metrics": [{"name": "leads", "value": 15, "unit": "count"}],
                    }
                ],
                "totals": {},
            }
        }
        result = svc._extract_channel_list("capture", data)
        assert len(result) == 1
        ch = result[0]
        assert ch.slug == "ig-dm"
        assert ch.headline_kpi is not None
        assert ch.headline_kpi.name == "leads"
        assert ch.headline_kpi.value == 15.0


# ─── _pick_headline_kpi ───────────────────────────────────────────────────────


class TestPickHeadlineKpi:
    from src.modules.analytics.application.services.stage_services.overview_stage import (
        StageOverviewService,
    )

    def test_no_metrics_returns_none(self):
        from src.modules.analytics.application.services.stage_services.overview_stage import (
            StageOverviewService,
        )

        result = StageOverviewService._pick_headline_kpi({"metrics": []}, ["leads"])
        assert result is None

    def test_non_list_metrics_returns_none(self):
        from src.modules.analytics.application.services.stage_services.overview_stage import (
            StageOverviewService,
        )

        result = StageOverviewService._pick_headline_kpi({"metrics": "bad"}, ["leads"])
        assert result is None

    def test_priority_match_returned(self):
        from src.modules.analytics.application.services.stage_services.overview_stage import (
            StageOverviewService,
        )

        channel = {
            "metrics": [
                {"name": "impressions", "value": 5000, "unit": "count"},
                {"name": "reach", "value": 3000, "unit": "count"},
            ]
        }
        result = StageOverviewService._pick_headline_kpi(channel, ["reach", "impressions"])
        assert result.name == "reach"
        assert result.value == 3000.0

    def test_no_priority_match_uses_first(self):
        from src.modules.analytics.application.services.stage_services.overview_stage import (
            StageOverviewService,
        )

        channel = {"metrics": [{"name": "some_metric", "value": 42, "unit": "count"}]}
        result = StageOverviewService._pick_headline_kpi(channel, ["leads"])
        assert result is not None
        assert result.name == "some_metric"
        assert result.value == 42.0


# ─── _extract_bottlenecks ─────────────────────────────────────────────────────


class TestExtractBottlenecks:
    def test_empty_list_returns_empty(self):
        svc = _make_svc()
        result = svc._extract_bottlenecks({"bottlenecks": []})
        assert result == []

    def test_non_list_returns_empty(self):
        svc = _make_svc()
        result = svc._extract_bottlenecks({"bottlenecks": "not-a-list"})
        assert result == []

    def test_missing_key_returns_empty(self):
        svc = _make_svc()
        result = svc._extract_bottlenecks({})
        assert result == []

    def test_valid_bottlenecks_extracted(self):
        svc = _make_svc()
        data = {
            "bottlenecks": [
                {"type": "high_churn_rate", "metric_label": "Churn", "severity": "critical"},
                {"type": "low_k_factor", "metric_label": "K-Factor", "severity": "warning"},
            ]
        }
        result = svc._extract_bottlenecks(data)
        assert len(result) == 2
        assert result[0].type == "high_churn_rate"
        assert result[0].severity == "critical"

    def test_non_dict_bottleneck_skipped(self):
        svc = _make_svc()
        data = {"bottlenecks": ["not-a-dict", {"type": "ok", "metric_label": "X", "severity": "normal"}]}
        result = svc._extract_bottlenecks(data)
        assert len(result) == 1
        assert result[0].type == "ok"
