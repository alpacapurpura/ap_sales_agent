"""Tests for the group detail endpoint — service integration + DTO shape.

Uses mocked cache to isolate from Redis/DB. Validates:
- Correct DTO response structure
- Empty response for unknown groups
- Tenant ID passed through correctly
- Period parameter forwarded
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.analytics.application.dto.group_detail_dto import GroupDetailDTO
from src.modules.analytics.application.services.stage_services.group_detail import (
    GroupDetailService,
)


@pytest.fixture
def test_tenant_id() -> str:
    return str(uuid.UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def sample_attraction_cache() -> dict:
    """Cached attraction stage data matching the AttractionDetailDTO shape."""
    return {
        "organic_social": {
            "totals": {"reach": 5000},
            "channels": [
                {
                    "slug": "ig-organic",
                    "name": "Instagram",
                    "channel_type": "organic_social",
                    "metrics": [{"name": "reach", "value": 5000.0}],
                    "source_label": "Instagram",
                    "connected": True,
                },
            ],
        },
        "paid": {
            "totals": {"spend": 1500.0, "impressions": 50000.0},
            "channels": [
                {
                    "slug": "meta-ads",
                    "name": "Meta Ads",
                    "channel_type": "paid",
                    "metrics": [
                        {
                            "name": "spend",
                            "value": 1500.0,
                            "unit": "currency",
                            "currency": "USD",
                        },
                        {"name": "impressions", "value": 50000.0},
                    ],
                    "source_label": "Meta",
                    "connected": True,
                },
            ],
        },
        "ga4_search": {"totals": {"sessions": 2000}, "channels": []},
        "outbound": {"totals": {}, "channels": []},
        "period": "last_30_days",
    }


class TestGroupDetailEndpoint:
    """Tests for the group detail service (endpoint layer)."""

    @pytest.mark.asyncio
    async def test_returns_channels_and_totals(
        self,
        test_tenant_id,
        sample_attraction_cache,
    ):
        mock_cache = AsyncMock()
        # Group cache miss, stage cache hit
        mock_cache.get = AsyncMock(side_effect=[None, sample_attraction_cache])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            test_tenant_id,
            "attraction",
            "paid",
            "last_30_days",
        )

        assert isinstance(result, GroupDetailDTO)
        assert result.group_key == "paid"
        assert result.stage == "attraction"
        assert len(result.channels) == 1
        assert result.channels[0].slug == "meta-ads"
        assert result.totals["spend"] == 1500.0
        assert result.totals["impressions"] == 50000.0

    @pytest.mark.asyncio
    async def test_returns_empty_for_unknown_group(
        self,
        test_tenant_id,
        sample_attraction_cache,
    ):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=[None, sample_attraction_cache])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            test_tenant_id,
            "attraction",
            "nonexistent",
            "last_30_days",
        )

        assert result.channels == []
        assert result.totals == {}

    @pytest.mark.asyncio
    async def test_filters_by_tenant(self, sample_attraction_cache):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=[None, sample_attraction_cache])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        tenant_a = str(uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        await service.get_group_detail(tenant_a, "attraction", "paid", "last_30_days")

        # Verify cache was read with correct tenant
        calls = mock_cache.get.call_args_list
        assert calls[0][0][0] == tenant_a  # group cache check
        assert calls[1][0][0] == tenant_a  # stage cache check

    @pytest.mark.asyncio
    async def test_passes_period_param(self, test_tenant_id, sample_attraction_cache):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=[None, sample_attraction_cache])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        await service.get_group_detail(test_tenant_id, "attraction", "paid", "weekly")

        # Verify period was passed to cache reads
        calls = mock_cache.get.call_args_list
        assert calls[0][0][2] == "weekly"  # group cache key period
        assert calls[1][0][2] == "weekly"  # stage cache key period

    @pytest.mark.asyncio
    async def test_channel_dto_has_correct_metrics(
        self,
        test_tenant_id,
        sample_attraction_cache,
    ):
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=[None, sample_attraction_cache])
        mock_cache.set = AsyncMock()
        service = GroupDetailService(cache=mock_cache)

        result = await service.get_group_detail(
            test_tenant_id,
            "attraction",
            "paid",
            "last_30_days",
        )

        channel = result.channels[0]
        assert len(channel.metrics) == 2
        spend_metric = next(m for m in channel.metrics if m.name == "spend")
        assert spend_metric.value == 1500.0
        assert spend_metric.unit == "currency"
        assert spend_metric.currency == "USD"
