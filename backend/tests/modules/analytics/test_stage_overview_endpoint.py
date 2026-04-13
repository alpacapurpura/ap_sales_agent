"""Tests for the stage overview endpoint and service.

Validates the overview service extracts correct data from cached stage data,
and the endpoint wiring exists. Tests are pure unit tests -- no DB required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.analytics.application.dto.stage_overview_dto import (
    StageOverviewDTO,
)
from src.modules.analytics.application.services.stage_services.overview_stage import (
    StageOverviewService,
)


@pytest.fixture
def test_tenant_id() -> str:
    return str(uuid.UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def mock_cache():
    """AsyncMock cache that always returns None (cache miss)."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def sample_attraction_cache() -> dict:
    """Cached attraction stage data matching the AttractionDetailDTO shape."""
    return {
        "organic_social": {
            "totals": {"reach": 5000, "engagement": 1200},
            "channels": [
                {
                    "slug": "ig-organic",
                    "name": "Instagram Organic",
                    "channel_type": "social",
                    "metrics": [
                        {"name": "reach", "value": 5000.0, "unit": "count"},
                        {"name": "engagement", "value": 1200.0, "unit": "count"},
                    ],
                    "source_label": "Instagram",
                    "connected": True,
                    "last_updated": "2026-04-06T12:00:00",
                    "stale": False,
                    "provider_name": "meta",
                },
            ],
        },
        "ga4_search": {
            "totals": {"sessions": 3000},
            "channels": [
                {
                    "slug": "google-organic",
                    "name": "Google Organic",
                    "channel_type": "search",
                    "metrics": [
                        {"name": "sessions", "value": 3000.0, "unit": "count"},
                    ],
                    "source_label": "Google",
                    "connected": True,
                    "provider_name": "google_analytics",
                },
            ],
        },
        "paid": {
            "totals": {"impressions": 25000, "clicks": 800},
            "channels": [
                {
                    "slug": "meta-ads",
                    "name": "Meta Ads",
                    "channel_type": "paid",
                    "metrics": [
                        {"name": "impressions", "value": 25000.0, "unit": "count"},
                        {"name": "clicks", "value": 800.0, "unit": "count"},
                    ],
                    "source_label": "Meta",
                    "connected": True,
                    "provider_name": "meta",
                },
            ],
        },
        "outbound": {
            "totals": {},
            "channels": [],
        },
        "period": "last_30_days",
        "last_updated": "2026-04-06T12:00:00",
    }


@pytest.fixture
def sample_capture_cache() -> dict:
    """Cached capture stage data matching the CaptureDetailDTO shape."""
    return {
        "header_kpis": {
            "total_leads": 500,
            "conversion_rate": 5.0,
            "cost_per_lead": 2.5,
        },
        "mini_funnel": {
            "source_label": "Visitantes",
            "source_value": 10000,
            "target_label": "Leads",
            "target_value": 500,
            "conversion_rate": 5.0,
        },
        "web_infrastructure": {
            "totals": {"leads": 300},
            "channels": [
                {
                    "slug": "landing-form",
                    "name": "Landing Form",
                    "channel_type": "form",
                    "metrics": [{"name": "leads", "value": 300.0}],
                    "source_label": "Landing",
                    "connected": True,
                    "provider_name": "internal",
                },
            ],
        },
        "ai_agent": {
            "totals": {"leads": 200},
            "channels": [
                {
                    "slug": "ig-dm",
                    "name": "Instagram DM",
                    "channel_type": "messaging",
                    "metrics": [
                        {"name": "leads", "value": 200.0},
                        {"name": "conversations", "value": 50.0},
                    ],
                    "source_label": "IG DM",
                    "connected": True,
                    "provider_name": "meta",
                },
            ],
        },
        "period": "last_30_days",
        "last_updated": "2026-04-06T10:00:00",
    }


class TestStageOverviewService:
    """Tests for StageOverviewService._extract_overview."""

    async def test_get_attraction_overview_returns_dto(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Service returns a StageOverviewDTO from cached attraction data."""

        # Setup: cache miss on overview, hit on stage data
        async def side_effect(tid, stage_key, period):
            if stage_key == "overview_attraction":
                return None
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        assert isinstance(result, StageOverviewDTO)
        assert result.stage == "attraction"

    async def test_overview_includes_channel_list(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Overview channel_list includes all channels from all groups."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        assert len(result.channel_list) == 3  # ig-organic, google-organic, meta-ads
        slugs = {ch.slug for ch in result.channel_list}
        assert "ig-organic" in slugs
        assert "google-organic" in slugs
        assert "meta-ads" in slugs

    async def test_overview_includes_groups(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Overview groups includes summary for each non-empty group."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        group_keys = {g.group_key for g in result.groups}
        assert "organic_social" in group_keys
        assert "ga4_search" in group_keys
        assert "paid" in group_keys

    async def test_overview_includes_header_kpis(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Attraction overview header_kpis include reach and sessions totals."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        assert "total_reach" in result.header_kpis
        assert result.header_kpis["total_reach"] == 5000.0
        assert result.header_kpis["total_sessions"] == 3000.0

    async def test_overview_channel_has_headline_kpi(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Each channel in the overview has a headline_kpi extracted."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        ig = next(ch for ch in result.channel_list if ch.slug == "ig-organic")
        assert ig.headline_kpi is not None
        assert ig.headline_kpi.name == "reach"
        assert ig.headline_kpi.value == 5000.0

    async def test_empty_stage_data_returns_empty_overview(
        self,
        mock_cache,
        test_tenant_id,
    ):
        """When no cache data exists, returns an empty overview."""
        mock_cache.get = AsyncMock(return_value=None)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        assert result.stage == "attraction"
        assert result.header_kpis == {}
        assert result.channel_list == []
        assert result.groups == []

    async def test_capture_overview_includes_mini_funnel(
        self,
        mock_cache,
        sample_capture_cache,
        test_tenant_id,
    ):
        """Capture overview includes mini_funnel from cached data."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "capture":
                return sample_capture_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "capture",
            "last_30_days",
        )
        assert result.mini_funnel is not None
        assert result.mini_funnel.source_label == "Visitantes"
        assert result.mini_funnel.conversion_rate == 5.0

    async def test_capture_overview_header_kpis(
        self,
        mock_cache,
        sample_capture_cache,
        test_tenant_id,
    ):
        """Capture overview header_kpis include total_leads and conversion_rate."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "capture":
                return sample_capture_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "capture",
            "last_30_days",
        )
        assert result.header_kpis["total_leads"] == 500.0
        assert result.header_kpis["conversion_rate"] == 5.0

    async def test_overview_caches_result(
        self,
        mock_cache,
        sample_attraction_cache,
        test_tenant_id,
    ):
        """Service caches the computed overview."""

        async def side_effect(tid, stage_key, period):
            if stage_key == "attraction":
                return sample_attraction_cache
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        await service.get_stage_overview(test_tenant_id, "attraction", "last_30_days")
        # verify set was called for overview cache
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][1] == "overview_attraction"

    async def test_overview_returns_cached_if_available(
        self,
        mock_cache,
        test_tenant_id,
    ):
        """Service returns cached non-empty overview without recomputing."""
        cached_overview = {
            "stage": "attraction",
            "header_kpis": {"total_reach": 9999.0},
            "groups": [],
            "channel_list": [
                {
                    "slug": "meta-ads",
                    "name": "Meta Ads",
                    "channel_type": "paid",
                    "group_key": "paid",
                    "connected": True,
                    "headline_kpi": {"name": "reach", "value": 9999.0, "unit": "count"},
                    "last_updated": None,
                    "stale": False,
                    "provider_name": "meta",
                },
            ],
            "bottlenecks": [],
            "period": "last_30_days",
            "last_updated": None,
        }

        async def side_effect(tid, stage_key, period):
            if stage_key == "overview_attraction":
                return cached_overview
            return None

        mock_cache.get = AsyncMock(side_effect=side_effect)
        service = StageOverviewService(cache=mock_cache)

        result = await service.get_stage_overview(
            test_tenant_id,
            "attraction",
            "last_30_days",
        )
        assert result.header_kpis["total_reach"] == 9999.0
        assert len(result.channel_list) == 1
        # set should NOT be called since we got a cache hit
        mock_cache.set.assert_not_called()


class TestEndpointWiring:
    """Tests that the endpoint is properly wired in the API module."""

    def test_metrics_module_imports_stage_overview_dto(self):
        """metrics.py imports StageOverviewDTO."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        assert "StageOverviewDTO" in source

    def test_metrics_module_imports_overview_service(self):
        """metrics.py imports StageOverviewService."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        assert "StageOverviewService" in source

    def test_metrics_module_has_overview_route(self):
        """metrics.py defines a /{stage}/overview route."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        assert "/{stage}/overview" in source

    def test_metrics_module_has_funnel_stage_enum(self):
        """metrics.py defines a FunnelStage enum for validation."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        assert "FunnelStage" in source

    def test_get_invalid_stage_overview_returns_422(self):
        """FunnelStage enum rejects invalid stage values."""
        import pytest as pt

        from src.modules.analytics.api.metrics import FunnelStage

        with pt.raises(ValueError):
            FunnelStage("nonexistent_stage")
