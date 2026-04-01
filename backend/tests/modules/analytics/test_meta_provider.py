"""Tests for MetaProvider — Instagram organic, Facebook organic, Meta Ads.

All external API calls mocked via httpx responses.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import httpx

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider


TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_token",
    "instagram_account_id": "12345",
    "page_id": "67890",
    "page_access_token": "page_token_abc",
    "ad_account_id": "111222",
    "currency": "MXN",
}


def _ok_response(json_data: dict) -> MagicMock:
    """Build a mock response with status 200 that passes raise_for_status."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _error_response(status: int = 500) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.text = "Server error"
    resp.json.return_value = {"error": {"message": "Server error"}}
    resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=resp,
        )
    )
    return resp


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
        mock_insights_response = _ok_response({
            "data": [
                {
                    "name": "reach",
                    "values": [{"value": 1000}, {"value": 2000}, {"value": 500}],
                }
            ]
        })

        mock_media_response = _ok_response({
            "data": [
                {"like_count": 100, "comments_count": 50},
                {"like_count": 200, "comments_count": 30},
            ]
        })

        async def mock_get(url, **kwargs):
            if "/insights" in url:
                return mock_insights_response
            if "/media" in url:
                return mock_media_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        metrics = result.metrics

        ig_metrics = [m for m in metrics if m.channel_slug == "ig-organic"]
        assert len(ig_metrics) >= 2

        reach = next(m for m in ig_metrics if m.metric_name == "reach")
        assert reach.value == 3500.0  # 1000+2000+500
        assert reach.provider == "meta"

        engagement = next(m for m in ig_metrics if m.metric_name == "engagement")
        assert engagement.value == 380.0  # 100+200+50+30
        assert engagement.extra.get("likes") == 300
        assert engagement.extra.get("comments") == 80

    @pytest.mark.asyncio
    async def test_uses_auth_header_not_query_param(self):
        """P1: access_token must be in Authorization header, not query params."""
        captured_kwargs = []

        async def mock_get(url, **kwargs):
            captured_kwargs.append(kwargs)
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        for call_kwargs in captured_kwargs:
            params = call_kwargs.get("params", {})
            assert "access_token" not in params, "Token must not appear in query params"
            headers = call_kwargs.get("headers", {})
            assert "Authorization" in headers, "Must use Authorization header"


class TestFacebookOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_reach_response = _ok_response({
            "data": [
                {
                    "name": "page_impressions_unique",
                    "values": [{"value": 5000}],
                }
            ]
        })

        mock_engagement_response = _ok_response({
            "data": [
                {
                    "name": "page_post_engagements",
                    "values": [{"value": 800}],
                }
            ]
        })

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            metric = params.get("metric", "")
            if "page_impressions_unique" in metric:
                return mock_reach_response
            if "page_post_engagements" in metric:
                return mock_engagement_response
            # Instagram calls — return empty
            if "/insights" in url and "page_" not in metric:
                return _ok_response({"data": []})
            if "/media" in url:
                return _ok_response({"data": []})
            # Ads — return empty
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        metrics = result.metrics

        fb_metrics = [m for m in metrics if m.channel_slug == "fb-organic"]
        assert len(fb_metrics) >= 2

        reach = next(m for m in fb_metrics if m.metric_name == "reach")
        assert reach.value == 5000.0

        engagement = next(m for m in fb_metrics if m.metric_name == "engagement")
        assert engagement.value == 800.0


class TestMetaAds:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_ads_response = _ok_response({
            "data": [
                {
                    "reach": "10000",
                    "impressions": "45000",
                    "clicks": "500",
                    "spend": "123.45",
                    "ctr": "1.11",
                    "cpm": "2.74",
                    "frequency": "4.5",
                    "actions": [
                        {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "15"},
                        {"action_type": "link_click", "value": "300"},
                    ],
                }
            ]
        })

        async def mock_get(url, **kwargs):
            if "/act_" in url:
                return mock_ads_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        metrics = result.metrics

        ads_metrics = [m for m in metrics if m.channel_slug == "meta-ads"]
        assert len(ads_metrics) == 8

        reach = next(m for m in ads_metrics if m.metric_name == "reach")
        assert reach.value == 10000.0

        impressions = next(m for m in ads_metrics if m.metric_name == "impressions")
        assert impressions.value == 45000.0

        clicks = next(m for m in ads_metrics if m.metric_name == "clicks")
        assert clicks.value == 500.0

        ctr = next(m for m in ads_metrics if m.metric_name == "ctr")
        assert ctr.value == 1.11
        assert ctr.unit == "percentage"

        cpm = next(m for m in ads_metrics if m.metric_name == "cpm")
        assert cpm.value == 2.74
        assert cpm.currency == "MXN"

        frequency = next(m for m in ads_metrics if m.metric_name == "frequency")
        assert frequency.value == 4.5

        conversions = next(m for m in ads_metrics if m.metric_name == "conversions")
        assert conversions.value == 15.0

        spend = next(m for m in ads_metrics if m.metric_name == "spend")
        assert spend.value == 123.45
        assert spend.unit == "currency"
        assert spend.currency == "MXN"

    @pytest.mark.asyncio
    async def test_currency_from_credentials(self):
        """P6: Currency should come from credentials, not hardcoded USD."""
        creds_eur = {**CREDS, "currency": "EUR"}
        mock_ads_response = _ok_response({
            "data": [{"reach": "1", "impressions": "1", "clicks": "0", "spend": "10.00",
                       "ctr": "0", "cpm": "0", "frequency": "1", "actions": []}]
        })

        async def mock_get(url, **kwargs):
            if "/act_" in url:
                return mock_ads_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID, creds_eur, date(2026, 3, 1), date(2026, 3, 15)
            )
        metrics = result.metrics

        spend = next(m for m in metrics if m.metric_name == "spend" and m.channel_slug == "meta-ads")
        assert spend.currency == "EUR"

    @pytest.mark.asyncio
    async def test_currency_defaults_to_usd(self):
        """P6: Without currency in credentials, should default to USD."""
        creds_no_currency = {k: v for k, v in CREDS.items() if k != "currency"}
        mock_ads_response = _ok_response({
            "data": [{"reach": "1", "impressions": "1", "clicks": "0", "spend": "5.00",
                       "ctr": "0", "cpm": "0", "frequency": "1", "actions": []}]
        })

        async def mock_get(url, **kwargs):
            if "/act_" in url:
                return mock_ads_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID, creds_no_currency, date(2026, 3, 1), date(2026, 3, 15)
            )
        metrics = result.metrics

        spend = next(m for m in metrics if m.metric_name == "spend" and m.channel_slug == "meta-ads")
        assert spend.currency == "USD"


class TestExtractMetricsDaily:
    """Tests for extract_metrics_daily() — per-day granularity extraction."""

    @pytest.mark.asyncio
    async def test_ig_organic_daily_emits_per_day_reach(self):
        """IG organic daily should emit one reach metric per day from values[] array."""
        mock_insights_response = _ok_response({
            "data": [
                {
                    "name": "reach",
                    "values": [
                        {"value": 1000, "end_time": "2026-03-01T08:00:00+0000"},
                        {"value": 2000, "end_time": "2026-03-02T08:00:00+0000"},
                        {"value": 500, "end_time": "2026-03-03T08:00:00+0000"},
                    ],
                }
            ]
        })

        mock_media_response = _ok_response({
            "data": [
                {"like_count": 100, "comments_count": 50},
            ]
        })

        async def mock_get(url, **kwargs):
            if "/insights" in url:
                return mock_insights_response
            if "/media" in url:
                return mock_media_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 3)
            )
        metrics = result.metrics

        reach_metrics = [m for m in metrics if m.metric_name == "reach" and m.channel_slug == "ig-organic"]
        assert len(reach_metrics) == 3
        assert reach_metrics[0].date == date(2026, 3, 1)
        assert reach_metrics[0].value == 1000.0
        assert reach_metrics[1].date == date(2026, 3, 2)
        assert reach_metrics[1].value == 2000.0
        assert reach_metrics[2].date == date(2026, 3, 3)
        assert reach_metrics[2].value == 500.0

    @pytest.mark.asyncio
    async def test_meta_ads_daily_uses_time_increment(self):
        """Meta Ads daily should use time_increment=1 and emit per-day metrics."""
        mock_ads_response = _ok_response({
            "data": [
                {
                    "date_start": "2026-03-01",
                    "date_stop": "2026-03-01",
                    "reach": "5000",
                    "impressions": "20000",
                    "clicks": "200",
                    "spend": "50.00",
                    "ctr": "1.0",
                    "cpm": "2.5",
                    "frequency": "4.0",
                    "actions": [],
                },
                {
                    "date_start": "2026-03-02",
                    "date_stop": "2026-03-02",
                    "reach": "6000",
                    "impressions": "25000",
                    "clicks": "300",
                    "spend": "60.00",
                    "ctr": "1.2",
                    "cpm": "2.4",
                    "frequency": "4.2",
                    "actions": [
                        {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "5"},
                    ],
                },
            ]
        })

        captured_params = []

        async def mock_get(url, **kwargs):
            captured_params.append(kwargs.get("params", {}))
            if "/act_" in url:
                return mock_ads_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 2)
            )
        metrics = result.metrics

        ads_metrics = [m for m in metrics if m.channel_slug == "meta-ads"]
        # 8 metric types × 2 days = 16
        assert len(ads_metrics) == 16

        # Check time_increment was used
        ads_params = [p for p in captured_params if p.get("time_increment") == "1"]
        assert len(ads_params) >= 1

        # Check day 1 reach
        day1_reach = [m for m in ads_metrics if m.metric_name == "reach" and m.date == date(2026, 3, 1)]
        assert len(day1_reach) == 1
        assert day1_reach[0].value == 5000.0

        # Check day 2 conversions
        day2_conv = [m for m in ads_metrics if m.metric_name == "conversions" and m.date == date(2026, 3, 2)]
        assert len(day2_conv) == 1
        assert day2_conv[0].value == 5.0

    @pytest.mark.asyncio
    async def test_fb_organic_daily_emits_per_day(self):
        """FB organic daily should parse values[] for both reach and engagement."""
        mock_reach_response = _ok_response({
            "data": [
                {
                    "name": "page_impressions_unique",
                    "values": [
                        {"value": 3000, "end_time": "2026-03-01T08:00:00+0000"},
                        {"value": 4000, "end_time": "2026-03-02T08:00:00+0000"},
                    ],
                }
            ]
        })
        mock_engagement_response = _ok_response({
            "data": [
                {
                    "name": "page_post_engagements",
                    "values": [
                        {"value": 200, "end_time": "2026-03-01T08:00:00+0000"},
                        {"value": 300, "end_time": "2026-03-02T08:00:00+0000"},
                    ],
                }
            ]
        })

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            params = kwargs.get("params", {})
            metric = params.get("metric", "")
            if "page_impressions_unique" in metric:
                return mock_reach_response
            if "page_post_engagements" in metric:
                return mock_engagement_response
            if "/insights" in url:
                return _ok_response({"data": []})
            if "/media" in url:
                return _ok_response({"data": []})
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 2)
            )
        metrics = result.metrics

        fb_metrics = [m for m in metrics if m.channel_slug == "fb-organic"]
        reach_d1 = [m for m in fb_metrics if m.metric_name == "reach" and m.date == date(2026, 3, 1)]
        assert len(reach_d1) == 1
        assert reach_d1[0].value == 3000.0

        eng_d2 = [m for m in fb_metrics if m.metric_name == "engagement" and m.date == date(2026, 3, 2)]
        assert len(eng_d2) == 1
        assert eng_d2[0].value == 300.0

    @pytest.mark.asyncio
    async def test_empty_credentials_returns_empty(self):
        provider = MetaProvider()
        result = await provider.extract_metrics_daily(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 3)
        )
        assert result.metrics == []


class TestMetaProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_credentials(self):
        provider = MetaProvider()
        result = await provider.extract_metrics(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 15)
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_api_error_returns_empty(self):
        """P3: HTTP errors should be caught and return empty, not silently return 0s."""
        async def mock_get(url, **kwargs):
            return _error_response(500)

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                {"access_token": "bad_token"},
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        # Should return empty, not raise — and not silently return zeroes
        assert isinstance(result.metrics, list)
        assert len(result.metrics) == 0

    @pytest.mark.asyncio
    async def test_401_does_not_return_zero_metrics(self):
        """P3: A 401 must NOT silently produce metrics with value 0."""
        async def mock_get(url, **kwargs):
            return _error_response(401)

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                {**CREDS, "access_token": "expired_token"},
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        # Must be empty — the old code would have returned metrics with 0 values
        assert len(result.metrics) == 0
