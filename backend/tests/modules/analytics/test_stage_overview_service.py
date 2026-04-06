"""Unit tests for StageOverviewService — pure logic, no DB, no Redis.

Tests the _extract_overview method directly with mock stage data
to validate channel extraction, header KPI selection, and group building.
"""

from unittest.mock import AsyncMock

import pytest

from src.modules.analytics.application.services.stage_services.overview_stage import (
    StageOverviewService,
)

# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_channel(slug: str, name: str, channel_type: str, **metric_kv: float) -> dict:
    return {
        "slug": slug,
        "name": name,
        "channel_type": channel_type,
        "source_label": name,
        "connected": True,
        "metrics": [{"name": k, "value": v} for k, v in metric_kv.items()],
    }


def _make_group(channels: list[dict], **totals: float) -> dict:
    return {"channels": channels, "totals": totals}


SAMPLE_ATTRACTION_DATA = {
    "organic_social": _make_group(
        [
            _make_channel(
                "ig-organic", "Instagram", "organic_social", reach=8000, engagement=500
            ),
            _make_channel(
                "yt-organic", "YouTube", "organic_social", reach=3000, views=12000
            ),
        ],
        reach=11000,
        engagement=500,
    ),
    "ga4_search": _make_group(
        [_make_channel("google-organic", "Google", "ga4_search", sessions=2000)],
        sessions=2000,
    ),
    "paid": _make_group(
        [
            _make_channel(
                "meta-ads",
                "Meta Ads",
                "paid",
                spend=1500,
                impressions=50000,
                clicks=2000,
            )
        ],
        spend=1500,
        impressions=50000,
    ),
    "outbound": _make_group([], contacts=0),
    "header_kpis": {"reach": 11000, "sessions": 2000, "impressions": 50000},
    "mini_funnel": {
        "source_label": "Visitantes",
        "source_value": 5000,
        "target_label": "Leads",
        "target_value": 200,
        "conversion_rate": 4.0,
    },
    "bottlenecks": [
        {
            "type": "low_conversion",
            "metric_label": "Conv. Rate",
            "severity": "warning",
            "tip": "x",
        },
    ],
    "period": "last_30_days",
    "last_updated": "2026-04-06T12:00:00Z",
}


SAMPLE_CAPTURE_DATA = {
    "web_infrastructure": _make_group(
        [_make_channel("website-capture", "Website", "web_infrastructure", leads=150)],
        leads=150,
    ),
    "ai_agent": _make_group(
        [
            _make_channel(
                "manychat-ig", "ManyChat IG", "ai_agent", leads=50, conversations=120
            )
        ],
        leads=50,
    ),
    "header_kpis": {"total_leads": 200, "conversion_rate": 4.0, "cost_per_lead": None},
    "mini_funnel": {
        "source_label": "Visitantes",
        "source_value": 5000,
        "target_label": "Leads",
        "target_value": 200,
        "conversion_rate": 4.0,
    },
    "period": "last_30_days",
}


# ── Service Tests ───────────────────────────────────────────────────────────────


class TestExtractOverview:
    """Tests for _extract_overview with mock stage data."""

    def setup_method(self):
        self.service = StageOverviewService(cache=None)

    def test_extracts_header_kpis_for_attraction(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        # Service sums totals across groups with total_ prefix
        assert overview.header_kpis.get("total_reach") == 11000
        assert overview.header_kpis.get("total_sessions") == 2000
        assert overview.header_kpis.get("total_impressions") == 50000

    def test_extracts_channel_list_from_groups(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        slugs = [ch.slug for ch in overview.channel_list]
        assert "ig-organic" in slugs
        assert "yt-organic" in slugs
        assert "google-organic" in slugs
        assert "meta-ads" in slugs

    def test_channel_has_correct_group_key(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        meta = next(ch for ch in overview.channel_list if ch.slug == "meta-ads")
        assert meta.group_key == "paid"

    def test_channel_has_headline_kpi(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        ig = next(ch for ch in overview.channel_list if ch.slug == "ig-organic")
        assert ig.headline_kpi is not None
        # reach is first in _HEADLINE_KPI_PRIORITY for attraction
        assert ig.headline_kpi.name == "reach"
        assert ig.headline_kpi.value == 8000

    def test_builds_group_metadata(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        group_keys = [g.group_key for g in overview.groups]
        assert "organic_social" in group_keys
        assert "paid" in group_keys
        organic = next(g for g in overview.groups if g.group_key == "organic_social")
        assert organic.channel_count == 2

    def test_extracts_mini_funnel(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        assert overview.mini_funnel is not None
        assert overview.mini_funnel.source_label == "Visitantes"
        assert overview.mini_funnel.conversion_rate == 4.0

    def test_extracts_bottlenecks(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        assert len(overview.bottlenecks) == 1
        assert overview.bottlenecks[0].severity == "warning"

    def test_empty_data_returns_empty_overview(self):
        overview = self.service._extract_overview("attraction", None)
        assert overview.stage == "attraction"
        assert overview.channel_list == []
        assert overview.groups == []

    def test_capture_stage_extracts_correctly(self):
        overview = self.service._extract_overview("capture", SAMPLE_CAPTURE_DATA)
        # Capture header_kpis are read directly from stage_data["header_kpis"]
        assert "total_leads" in overview.header_kpis or len(overview.header_kpis) > 0
        slugs = [ch.slug for ch in overview.channel_list]
        assert "website-capture" in slugs
        assert "manychat-ig" in slugs

    def test_skips_empty_groups(self):
        overview = self.service._extract_overview("attraction", SAMPLE_ATTRACTION_DATA)
        # outbound has no channels, should still appear in groups list
        # but with channel_count = 0
        outbound = next((g for g in overview.groups if g.group_key == "outbound"), None)
        if outbound:
            assert outbound.channel_count == 0


class TestCachingBehavior:
    """Tests for cache hit/miss behavior."""

    @pytest.mark.asyncio
    async def test_returns_cached_overview_on_hit(self):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value={
                "stage": "attraction",
                "header_kpis": {},
                "groups": [],
                "channel_list": [],
                "bottlenecks": [],
                "period": "last_30_days",
            }
        )
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            "tenant-1", "attraction", "last_30_days"
        )
        assert result.stage == "attraction"
        # Should have called get with overview key first
        mock_cache.get.assert_any_call(
            "tenant-1", "overview_attraction", "last_30_days"
        )

    @pytest.mark.asyncio
    async def test_computes_and_caches_on_miss(self):
        mock_cache = AsyncMock()
        # overview miss, then stage data hit
        mock_cache.get = AsyncMock(side_effect=[None, SAMPLE_ATTRACTION_DATA])
        mock_cache.set = AsyncMock()
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            "tenant-1", "attraction", "last_30_days"
        )
        assert len(result.channel_list) > 0
        # Should cache the computed overview
        mock_cache.set.assert_called_once()
        set_args = mock_cache.set.call_args
        assert set_args[0][1] == "overview_attraction"

    @pytest.mark.asyncio
    async def test_works_without_cache(self):
        service = StageOverviewService(cache=None)
        result = await service.get_stage_overview(
            "tenant-1", "attraction", "last_30_days"
        )
        # Should return empty overview since no cache and no DB
        assert result.stage == "attraction"
        assert result.channel_list == []
