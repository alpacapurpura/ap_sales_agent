"""Tests for GoogleAdsProvider — Google Ads + YouTube Ads separation.

Mocks GoogleAdsAdapter.run_gaql_query() responses.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

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
                "ctr": 0.04,
                "average_cpc": 250_000,  # $0.25
                "conversions_value": 500.0,
            },
            {
                "campaign_id": "2",
                "campaign_name": "YouTube Video Campaign",
                "advertising_channel_type": "VIDEO",
                "impressions": 20000,
                "clicks": 800,
                "conversions": 5.0,
                "cost_micros": 30_000_000,  # $30.00
                "ctr": 0.04,
                "average_cpc": 37_500,
                "conversions_value": 200.0,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        # Google Ads (SEARCH) — now 7 metrics
        ga_metrics = [m for m in metrics if m.channel_slug == "google-ads"]
        assert len(ga_metrics) == 7
        ga_spend = next(m for m in ga_metrics if m.metric_name == "spend")
        assert ga_spend.value == 50.0
        ga_ctr = next(m for m in ga_metrics if m.metric_name == "ctr")
        assert ga_ctr.value == pytest.approx(200 / 5000)  # clicks/impressions
        ga_cpc = next(m for m in ga_metrics if m.metric_name == "cpc")
        assert ga_cpc.value == pytest.approx(50.0 / 200)  # spend/clicks
        ga_cv = next(m for m in ga_metrics if m.metric_name == "conversion_value")
        assert ga_cv.value == 500.0

        # YouTube Ads (VIDEO) — also 7 metrics
        yt_metrics = [m for m in metrics if m.channel_slug == "yt-ads"]
        assert len(yt_metrics) == 7
        yt_spend = next(m for m in yt_metrics if m.metric_name == "spend")
        assert yt_spend.value == 30.0

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
                "ctr": 0.10,
                "average_cpc": 523_000,
                "conversions_value": 50.0,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        spend = next(m for m in metrics if m.metric_name == "spend")
        assert spend.value == 5.23

    @pytest.mark.asyncio
    async def test_cpc_derived_from_spend_and_clicks(self):
        """CPC is computed as spend/clicks, not from average_cpc."""
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Campaign A",
                "advertising_channel_type": "SEARCH",
                "impressions": 1000,
                "clicks": 50,
                "conversions": 2.0,
                "cost_micros": 25_000_000,  # $25.00
                "ctr": 0.05,
                "average_cpc": 500_000,
                "conversions_value": 100.0,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        cpc = next(m for m in metrics if m.metric_name == "cpc")
        assert cpc.value == pytest.approx(25.0 / 50)  # $0.50
        assert cpc.unit == "currency"


class TestRetargetingExtraction:
    @pytest.mark.asyncio
    async def test_stage_nurturing_extracts_retargeting(self):
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Remarketing - Leads",
                "advertising_channel_type": "DISPLAY",
                "impressions": 10000,
                "clicks": 500,
                "conversions": 0,
                "cost_micros": 15_000_000,
                "ctr": 0.05,
                "average_cpc": 30_000,
                "conversions_value": 0,
            },
            {
                "campaign_id": "2",
                "campaign_name": "Search Campaign",
                "advertising_channel_type": "SEARCH",
                "impressions": 5000,
                "clicks": 200,
                "conversions": 10,
                "cost_micros": 50_000_000,
                "ctr": 0.04,
                "average_cpc": 250_000,
                "conversions_value": 500,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
                stage="nurturing",
            )

        metrics = result.metrics
        # Only retargeting campaigns should appear
        assert all(m.channel_slug == "google-retargeting" for m in metrics)
        impressions = next(m for m in metrics if m.metric_name == "impressions")
        assert impressions.value == 10000.0
        ctr = next(m for m in metrics if m.metric_name == "ctr")
        assert ctr.value == pytest.approx(500 / 10000)
        cpc = next(m for m in metrics if m.metric_name == "cpc")
        assert cpc.value == pytest.approx(15.0 / 500)


class TestDailyExtraction:
    @pytest.mark.asyncio
    async def test_extract_metrics_daily_groups_by_date(self):
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Search",
                "advertising_channel_type": "SEARCH",
                "segments_date": "2026-03-01",
                "impressions": 1000,
                "clicks": 50,
                "conversions": 2.0,
                "cost_micros": 10_000_000,
                "ctr": 0.05,
                "average_cpc": 200_000,
                "conversions_value": 100.0,
            },
            {
                "campaign_id": "1",
                "campaign_name": "Search",
                "advertising_channel_type": "SEARCH",
                "segments_date": "2026-03-02",
                "impressions": 2000,
                "clicks": 100,
                "conversions": 5.0,
                "cost_micros": 20_000_000,
                "ctr": 0.05,
                "average_cpc": 200_000,
                "conversions_value": 250.0,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 2),
            )

        metrics = result.metrics
        mar1 = [m for m in metrics if m.date == date(2026, 3, 1)]
        mar2 = [m for m in metrics if m.date == date(2026, 3, 2)]
        assert len(mar1) == 7  # 7 metrics per slug
        assert len(mar2) == 7

        spend_mar1 = next(m for m in mar1 if m.metric_name == "spend")
        assert spend_mar1.value == 10.0
        spend_mar2 = next(m for m in mar2 if m.metric_name == "spend")
        assert spend_mar2.value == 20.0

    @pytest.mark.asyncio
    async def test_extract_metrics_daily_nurturing(self):
        """Daily extraction with nurturing stage only returns retargeting."""
        mock_rows = [
            {
                "campaign_id": "1",
                "campaign_name": "Retargeting Warm",
                "advertising_channel_type": "DISPLAY",
                "segments_date": "2026-03-01",
                "impressions": 5000,
                "clicks": 250,
                "conversions": 0,
                "cost_micros": 8_000_000,
                "ctr": 0.05,
                "average_cpc": 32_000,
                "conversions_value": 0,
            },
        ]

        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=mock_rows)
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 1),
                stage="nurturing",
            )

        metrics = result.metrics
        assert all(m.channel_slug == "google-retargeting" for m in metrics)
        assert len(metrics) == 5  # reach, clicks, spend, ctr, cpc


class TestGoogleAdsErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_developer_token(self):
        provider = GoogleAdsProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {"customer_id": "123"},  # No developer_token
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_empty_results(self):
        with patch(
            "src.modules.analytics.infrastructure.providers.google_ads_provider.create_google_ads_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_gaql_query = AsyncMock(return_value=[])
            adapter_instance.get_account_currency = AsyncMock(return_value=None)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAdsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        assert result.metrics == []
