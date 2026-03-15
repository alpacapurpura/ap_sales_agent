"""Tests for GoogleAdsProvider — Google Ads + YouTube Ads separation.

Mocks GoogleAdsAdapter.run_gaql_query() responses.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.google_ads_provider import (
    GoogleAdsProvider,
)


TENANT_ID = uuid4()
CREDS = {
    "customer_id": "1234567890",
    "developer_token": "test_dev_token",
    "client_id": "test_client",
    "client_secret": "test_secret",
    "refresh_token": "test_refresh",
}


class TestGoogleAdsProviderBasics:
    def test_provider_name(self):
        assert GoogleAdsProvider().provider_name() == "google_ads"

    def test_rate_limit_config(self):
        cfg = GoogleAdsProvider().rate_limit_config()
        assert "requests_per_minute" in cfg


class TestCampaignSeparation:
    @pytest.mark.asyncio
    async def test_separates_video_from_search(self):
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Search Campaign",
                "advertising_channel_type": "SEARCH",
                "impressions": 5000,
                "clicks": 200,
                "conversions": 10.0,
                "cost_micros": 50_000_000,  # $50.00
            },
            {
                "campaign_id": "2",
                "campaign_name": "YouTube Video Campaign",
                "advertising_channel_type": "VIDEO",
                "impressions": 20000,
                "clicks": 800,
                "conversions": 5.0,
                "cost_micros": 30_000_000,  # $30.00
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.GoogleAdsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        # Google Ads (SEARCH)
        ga_metrics = [m for m in metrics if m.channel_slug == "google-ads"]
        assert len(ga_metrics) == 4
        ga_spend = next(m for m in ga_metrics if m.metric_name == "spend")
        assert ga_spend.value == 50.0  # 50_000_000 / 1_000_000

        # YouTube Ads (VIDEO)
        yt_metrics = [m for m in metrics if m.channel_slug == "yt-ads"]
        assert len(yt_metrics) == 4
        yt_spend = next(m for m in yt_metrics if m.metric_name == "spend")
        assert yt_spend.value == 30.0  # 30_000_000 / 1_000_000

    @pytest.mark.asyncio
    async def test_cost_micros_conversion(self):
        """CRITICAL: cost_micros must be divided by 1_000_000."""
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Test",
                "advertising_channel_type": "SEARCH",
                "impressions": 100,
                "clicks": 10,
                "conversions": 1.0,
                "cost_micros": 5_230_000,  # $5.23
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.GoogleAdsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        spend = next(m for m in metrics if m.metric_name == "spend")
        assert spend.value == 5.23


class TestGoogleAdsErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_developer_token(self):
        provider = GoogleAdsProvider()
        metrics = await provider.extract_metrics(
            TENANT_ID,
            {"customer_id": "123"},  # No developer_token
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_empty_results(self):
        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.GoogleAdsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=[])
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        assert metrics == []
