"""Tests for MetaProvider — Instagram organic, Facebook organic, Meta Ads.

All external API calls mocked via httpx responses.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider


TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_token",
    "instagram_account_id": "12345",
    "page_id": "67890",
    "page_access_token": "page_token_abc",
    "ad_account_id": "111222",
}


class TestMetaProviderBasics:
    def test_provider_name(self):
        p = MetaProvider()
        assert p.provider_name() == "meta"

    def test_rate_limit_config(self):
        p = MetaProvider()
        cfg = p.rate_limit_config()
        assert cfg["requests_per_minute"] == 200
        assert cfg["burst_size"] == 50


class TestInstagramOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_insights_response = MagicMock()
        mock_insights_response.status_code = 200
        mock_insights_response.json.return_value = {
            "data": [
                {
                    "name": "reach",
                    "values": [{"value": 1000}, {"value": 2000}, {"value": 500}],
                }
            ]
        }

        mock_media_response = MagicMock()
        mock_media_response.status_code = 200
        mock_media_response.json.return_value = {
            "data": [
                {"like_count": 100, "comments_count": 50},
                {"like_count": 200, "comments_count": 30},
            ]
        }

        async def mock_get(url, **kwargs):
            if "/insights" in url:
                return mock_insights_response
            if "/media" in url:
                return mock_media_response
            return MagicMock(status_code=404, json=lambda: {})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        ig_metrics = [m for m in metrics if m.channel_slug == "ig-organic"]
        assert len(ig_metrics) >= 2

        reach = next(m for m in ig_metrics if m.metric_name == "reach")
        assert reach.value == 3500.0  # 1000+2000+500
        assert reach.provider == "meta"

        engagement = next(m for m in ig_metrics if m.metric_name == "engagement")
        assert engagement.value == 380.0  # 100+200+50+30
        assert engagement.extra.get("likes") == 300
        assert engagement.extra.get("comments") == 80


class TestFacebookOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_reach_response = MagicMock()
        mock_reach_response.status_code = 200
        mock_reach_response.json.return_value = {
            "data": [
                {
                    "name": "page_impressions_unique",
                    "values": [{"value": 5000}],
                }
            ]
        }

        mock_engagement_response = MagicMock()
        mock_engagement_response.status_code = 200
        mock_engagement_response.json.return_value = {
            "data": [
                {
                    "name": "page_post_engagements",
                    "values": [{"value": 800}],
                }
            ]
        }

        call_count = {"n": 0}

        async def mock_get(url, **kwargs):
            call_count["n"] += 1
            params = kwargs.get("params", {})
            metric = params.get("metric", "")
            if "page_impressions_unique" in metric:
                return mock_reach_response
            if "page_post_engagements" in metric:
                return mock_engagement_response
            # Instagram calls — return empty
            if "/insights" in url and "page_" not in metric:
                return MagicMock(status_code=200, json=lambda: {"data": []})
            if "/media" in url:
                return MagicMock(status_code=200, json=lambda: {"data": []})
            # Ads — return empty
            return MagicMock(status_code=200, json=lambda: {"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        fb_metrics = [m for m in metrics if m.channel_slug == "fb-organic"]
        assert len(fb_metrics) >= 2

        reach = next(m for m in fb_metrics if m.metric_name == "reach")
        assert reach.value == 5000.0

        engagement = next(m for m in fb_metrics if m.metric_name == "engagement")
        assert engagement.value == 800.0


class TestMetaAds:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_ads_response = MagicMock()
        mock_ads_response.status_code = 200
        mock_ads_response.json.return_value = {
            "data": [
                {
                    "reach": "10000",
                    "clicks": "500",
                    "spend": "123.45",
                    "actions": [
                        {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "15"},
                        {"action_type": "link_click", "value": "300"},
                    ],
                }
            ]
        }

        async def mock_get(url, **kwargs):
            if "/act_" in url:
                return mock_ads_response
            # Other calls return empty
            return MagicMock(status_code=200, json=lambda: {"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        ads_metrics = [m for m in metrics if m.channel_slug == "meta-ads"]
        assert len(ads_metrics) >= 4

        reach = next(m for m in ads_metrics if m.metric_name == "reach")
        assert reach.value == 10000.0

        clicks = next(m for m in ads_metrics if m.metric_name == "clicks")
        assert clicks.value == 500.0

        conversions = next(m for m in ads_metrics if m.metric_name == "conversions")
        assert conversions.value == 15.0

        spend = next(m for m in ads_metrics if m.metric_name == "spend")
        assert spend.value == 123.45
        assert spend.unit == "currency"


class TestMetaProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_credentials(self):
        provider = MetaProvider()
        metrics = await provider.extract_metrics(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 15)
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_api_error(self):
        async def mock_get(url, **kwargs):
            return MagicMock(status_code=500, text="Internal Server Error",
                           json=lambda: {"error": {"message": "Server error"}})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID,
                {"access_token": "bad_token"},
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        # Should return empty, not raise
        assert isinstance(metrics, list)
