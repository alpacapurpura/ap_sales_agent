"""Unit tests for GroupDetailService — extracts a single group from cached stage data.

Pure logic, no DB, no Redis. Tests extraction, caching behavior,
and edge cases (cache miss, unknown group).
"""

from unittest.mock import AsyncMock

import pytest

from src.modules.analytics.application.services.stage_services.group_detail import (
    GroupDetailService,
)

# ── Fixtures (reuse shapes from overview tests) ─────────────────────────────


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
            _make_channel("ig-organic", "Instagram", "organic_social", reach=8000),
            _make_channel("yt-organic", "YouTube", "organic_social", reach=3000),
        ],
        reach=11000,
    ),
    "ga4_search": _make_group(
        [_make_channel("google-organic", "Google", "ga4_search", sessions=2000)],
        sessions=2000,
    ),
    "paid": _make_group(
        [_make_channel("meta-ads", "Meta Ads", "paid", spend=1500, impressions=50000)],
        spend=1500,
        impressions=50000,
    ),
    "outbound": _make_group([], contacts=0),
    "period": "last_30_days",
    "last_updated": "2026-04-06T12:00:00Z",
}


# ── Service Tests ────────────────────────────────────────────────────────────


class TestGroupDetailExtraction:
    """Tests for extracting a single group from cached stage data."""

    def setup_method(self):
        self.service = GroupDetailService(cache=None)

    def test_extracts_single_group_from_cached_data(self):
        result = self.service._extract_group(
            "attraction",
            SAMPLE_ATTRACTION_DATA,
            "paid",
        )
        assert result is not None
        assert result["group_key"] == "paid"
        assert len(result["channels"]) == 1
        assert result["channels"][0]["slug"] == "meta-ads"
        assert result["totals"]["spend"] == 1500

    def test_extracts_organic_social_group(self):
        result = self.service._extract_group(
            "attraction",
            SAMPLE_ATTRACTION_DATA,
            "organic_social",
        )
        assert result is not None
        assert result["group_key"] == "organic_social"
        assert len(result["channels"]) == 2
        assert result["totals"]["reach"] == 11000

    def test_returns_none_for_unknown_group(self):
        result = self.service._extract_group(
            "attraction",
            SAMPLE_ATTRACTION_DATA,
            "nonexistent",
        )
        assert result is None

    def test_returns_none_when_no_stage_data(self):
        result = self.service._extract_group("attraction", None, "paid")
        assert result is None

    def test_empty_group_returns_empty_channels(self):
        result = self.service._extract_group(
            "attraction",
            SAMPLE_ATTRACTION_DATA,
            "outbound",
        )
        assert result is not None
        assert result["channels"] == []
        assert result["totals"].get("contacts") == 0


class TestGroupDetailCaching:
    """Tests for cache hit/miss behavior."""

    @pytest.mark.asyncio
    async def test_caches_extracted_group(self):
        mock_cache = AsyncMock()
        # group cache miss, then full stage cache hit
        mock_cache.get = AsyncMock(side_effect=[None, SAMPLE_ATTRACTION_DATA])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            "tenant-1",
            "attraction",
            "paid",
            "last_30_days",
        )
        assert result.group_key == "paid"
        assert len(result.channels) == 1

        # Should cache with group-specific key
        mock_cache.set.assert_called_once()
        set_args = mock_cache.set.call_args
        assert set_args[0][1] == "group_attraction_paid"

    @pytest.mark.asyncio
    async def test_group_cache_hit_skips_extraction(self):
        mock_cache = AsyncMock()
        cached_group = {
            "group_key": "paid",
            "stage": "attraction",
            "channels": [
                {
                    "slug": "meta-ads",
                    "name": "Meta Ads",
                    "channel_type": "paid",
                    "metrics": [{"name": "spend", "value": 1500}],
                    "source_label": "Meta",
                    "connected": True,
                },
            ],
            "totals": {"spend": 1500},
            "period": "last_30_days",
        }
        # Group cache hit on first call
        mock_cache.get = AsyncMock(return_value=cached_group)
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            "tenant-1",
            "attraction",
            "paid",
            "last_30_days",
        )
        assert result.group_key == "paid"
        # Should NOT call set (no re-caching needed)
        mock_cache.set.assert_not_called()
        # Should only call get once (group cache)
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_cache(self):
        mock_cache = AsyncMock()
        # Both group and stage cache miss
        mock_cache.get = AsyncMock(side_effect=[None, None])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            "tenant-1",
            "attraction",
            "paid",
            "last_30_days",
        )
        assert result.channels == []
        assert result.totals == {}

    @pytest.mark.asyncio
    async def test_works_without_cache(self):
        service = GroupDetailService(cache=None)
        result = await service.get_group_detail(
            "tenant-1",
            "attraction",
            "paid",
            "last_30_days",
        )
        assert result.group_key == "paid"
        assert result.channels == []
