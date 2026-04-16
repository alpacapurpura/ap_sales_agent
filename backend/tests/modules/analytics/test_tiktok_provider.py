"""Tests for TikTokProvider — TikTok organic + TikTok Ads.

Mocks TikTokAdapter methods.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.providers.tiktok_provider import (
    TikTokProvider,
)

TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_tiktok_token",
    "advertiser_id": "adv_123",
}


class TestTikTokProviderBasics:
    def test_provider_name(self):
        assert TikTokProvider().provider_name() == "tiktok"

    def test_rate_limit_config(self):
        cfg = TikTokProvider().rate_limit_config()
        assert "requests_per_minute" in cfg


class TestTikTokOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_organic = [
            {"video_views": 8000, "likes": 300, "comments": 50, "shares": 20},
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.tiktok_provider.create_tiktok_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.get_organic_insights = AsyncMock(return_value=mock_organic)
            adapter_instance.get_ads_report = AsyncMock(return_value=[])
            adapter_instance.get_advertiser_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = TikTokProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        organic = [m for m in metrics if m.channel_slug == "tiktok-organic"]
        assert len(organic) >= 2

        video_views = next(m for m in organic if m.metric_name == "video_views")
        assert video_views.value == 8000.0

        engagement = next(m for m in organic if m.metric_name == "engagement")
        assert engagement.value == 370.0  # 300+50+20


class TestTikTokAds:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_ads = [
            {
                "metrics": {
                    "reach": "25000",
                    "clicks": "1200",
                    "conversion": "45",
                    "spend": "250.50",
                },
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.tiktok_provider.create_tiktok_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.get_organic_insights = AsyncMock(return_value=[])
            adapter_instance.get_ads_report = AsyncMock(return_value=mock_ads)
            adapter_instance.get_advertiser_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = TikTokProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        ads = [m for m in metrics if m.channel_slug == "tiktok-ads"]
        assert len(ads) >= 4

        reach = next(m for m in ads if m.metric_name == "reach")
        assert reach.value == 25000.0

        spend = next(m for m in ads if m.metric_name == "spend")
        assert spend.value == 250.50
        assert spend.unit == "currency"


class TestTikTokProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        provider = TikTokProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_adapter_exception(self):
        with patch(
            "src.modules.analytics.infrastructure.providers.tiktok_provider.create_tiktok_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.get_organic_insights = AsyncMock(
                side_effect=Exception("API down"),
            )
            adapter_instance.get_ads_report = AsyncMock(
                side_effect=Exception("API down"),
            )
            adapter_instance.get_advertiser_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = TikTokProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        assert result.metrics == []
