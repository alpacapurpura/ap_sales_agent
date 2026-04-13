"""Tests for MetaProvider — Instagram organic, Facebook organic, Meta Ads.

All external API calls mocked via httpx responses.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

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
        ),
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
    async def test_happy_path_excludes_ad_from_breakdown(self):
        """Breakdownable metrics exclude AD values; non-breakdownable kept as-is."""
        # Breakdownable response: includes AD that must be excluded
        mock_breakdown_response = _ok_response(
            {
                "data": [
                    {
                        "name": "reach",
                        "total_value": {
                            "value": 500,
                            "breakdowns": [
                                {
                                    "dimension_keys": ["media_product_type"],
                                    "results": [
                                        {"dimension_values": ["AD"], "value": 200},
                                        {"dimension_values": ["FEED"], "value": 150},
                                        {"dimension_values": ["REELS"], "value": 100},
                                        {"dimension_values": ["STORY"], "value": 50},
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "name": "total_interactions",
                        "total_value": {
                            "value": 900,
                            "breakdowns": [
                                {
                                    "dimension_keys": ["media_product_type"],
                                    "results": [
                                        {"dimension_values": ["AD"], "value": 100},
                                        {"dimension_values": ["FEED"], "value": 500},
                                        {"dimension_values": ["REELS"], "value": 300},
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "name": "likes",
                        "total_value": {
                            "value": 330,
                            "breakdowns": [
                                {
                                    "dimension_keys": ["media_product_type"],
                                    "results": [
                                        {"dimension_values": ["AD"], "value": 30},
                                        {"dimension_values": ["FEED"], "value": 200},
                                        {"dimension_values": ["REELS"], "value": 100},
                                    ],
                                },
                            ],
                        },
                    },
                ],
            },
        )

        # Non-breakdownable response: no breakdown available
        mock_no_breakdown_response = _ok_response(
            {
                "data": [
                    {
                        "name": "accounts_engaged",
                        "total_value": {"value": 250},
                    },
                    {
                        "name": "replies",
                        "total_value": {"value": 45},
                    },
                ],
            },
        )

        mock_user_node_response = _ok_response(
            {
                "id": "12345",
                "followers_count": 28400,
                "media_count": 342,
            },
        )

        mock_demographics_response = _ok_response(
            {
                "data": [
                    {
                        "name": "follower_demographics",
                        "total_value": {
                            "breakdowns": [
                                {
                                    "results": [
                                        {
                                            "dimension_values": ["25-34", "F"],
                                            "value": 4200,
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                ],
            },
        )

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/insights" in url:
                if params.get("period") == "lifetime":
                    return mock_demographics_response
                if "breakdown" in params:
                    return mock_breakdown_response
                return mock_no_breakdown_response
            if url.endswith("/12345") and "fields" in params:
                return mock_user_node_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        ig_metrics = [m for m in metrics if m.channel_slug == "ig-organic"]
        assert len(ig_metrics) >= 5

        # reach is NON_AGGREGABLE — uses last value, AD excluded (500 - 200 = 300)
        reach = next(m for m in ig_metrics if m.metric_name == "reach")
        assert reach.value == 300.0
        assert reach.provider == "meta"

        # total_interactions is ADDITIVE, AD excluded (900 - 100 = 800)
        interactions = next(
            m for m in ig_metrics if m.metric_name == "total_interactions"
        )
        assert interactions.value == 800.0

        # ig_likes is ADDITIVE, AD excluded (330 - 30 = 300)
        likes = next(m for m in ig_metrics if m.metric_name == "ig_likes")
        assert likes.value == 300.0

        # Non-breakdownable metrics kept as-is (no AD exclusion possible)
        engaged = next(m for m in ig_metrics if m.metric_name == "ig_accounts_engaged")
        assert engaged.value == 250.0

        replies = next(m for m in ig_metrics if m.metric_name == "ig_replies")
        assert replies.value == 45.0

        # Snapshot metrics from User Node
        followers = next(m for m in ig_metrics if m.metric_name == "ig_followers_count")
        assert followers.value == 28400.0

        media = next(m for m in ig_metrics if m.metric_name == "ig_media_count")
        assert media.value == 342.0

        # Demographics
        demo = next(
            m for m in ig_metrics if m.metric_name == "ig_follower_demographics"
        )
        assert demo.unit == "json"
        assert demo.value == 0.0

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        for call_kwargs in captured_kwargs:
            params = call_kwargs.get("params", {})
            assert "access_token" not in params, "Token must not appear in query params"
            headers = call_kwargs.get("headers", {})
            assert "Authorization" in headers, "Must use Authorization header"


class TestFacebookOrganic:
    @pytest.mark.asyncio
    async def test_happy_path_uses_organic_metric(self):
        mock_reach_response = _ok_response(
            {
                "data": [
                    {
                        "name": "page_impressions_organic_unique",
                        "values": [{"value": 5000}],
                    },
                ],
            },
        )

        mock_engagement_response = _ok_response(
            {
                "data": [
                    {
                        "name": "page_post_engagements",
                        "values": [{"value": 800}],
                    },
                ],
            },
        )

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            metric = params.get("metric", "")
            if "page_impressions_organic_unique" in metric:
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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        fb_metrics = [m for m in metrics if m.channel_slug == "fb-organic"]
        assert len(fb_metrics) >= 2

        reach = next(m for m in fb_metrics if m.metric_name == "reach")
        assert reach.value == 5000.0

        engagement = next(m for m in fb_metrics if m.metric_name == "engagement")
        assert engagement.value == 800.0


class TestMetaAds:
    """Full expanded mock response used across Meta Ads tests."""

    FULL_ADS_DATA = {
        "reach": "10000",
        "impressions": "45000",
        "clicks": "500",
        "spend": "123.45",
        "ctr": "1.11",
        "cpm": "2.74",
        "cpc": "0.25",
        "cpp": "12.35",
        "frequency": "4.5",
        "inline_link_clicks": "420",
        "inline_post_engagement": "650",
        "cost_per_inline_link_click": "0.29",
        "actions": [
            {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "15"},
            {"action_type": "link_click", "value": "300"},
            {"action_type": "offsite_conversion.fb_pixel_lead", "value": "25"},
            {"action_type": "offsite_conversion.fb_pixel_add_to_cart", "value": "40"},
            {
                "action_type": "offsite_conversion.fb_pixel_initiate_checkout",
                "value": "20",
            },
            {
                "action_type": "offsite_conversion.fb_pixel_complete_registration",
                "value": "10",
            },
            {"action_type": "offsite_conversion.fb_pixel_view_content", "value": "200"},
            {"action_type": "landing_page_view", "value": "350"},
            {"action_type": "video_view", "value": "1200"},
            {"action_type": "post_engagement", "value": "800"},
            {"action_type": "page_engagement", "value": "900"},
        ],
        "action_values": [
            {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "750.00"},
        ],
        "cost_per_action_type": [
            {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "8.23"},
            {"action_type": "offsite_conversion.fb_pixel_lead", "value": "4.94"},
        ],
        "outbound_clicks": [
            {"action_type": "outbound_click", "value": "380"},
        ],
        "cost_per_outbound_click": [
            {"action_type": "outbound_click", "value": "0.32"},
        ],
        "purchase_roas": [
            {"action_type": "omni_purchase", "value": "6.07"},
        ],
        "video_p25_watched_actions": [
            {"action_type": "video_view", "value": "1000"},
        ],
        "video_p50_watched_actions": [
            {"action_type": "video_view", "value": "800"},
        ],
        "video_p75_watched_actions": [
            {"action_type": "video_view", "value": "600"},
        ],
        "video_p100_watched_actions": [
            {"action_type": "video_view", "value": "400"},
        ],
        "video_30_sec_watched_actions": [
            {"action_type": "video_view", "value": "500"},
        ],
        "video_avg_time_watched_actions": [
            {"action_type": "video_view", "value": "15.3"},
        ],
    }

    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_ads_response = _ok_response({"data": [self.FULL_ADS_DATA]})

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        ads_metrics = [m for m in metrics if m.channel_slug == "meta-ads"]
        # 12 simple + 2 outbound + 11 actions + 1 action_values + 2 cost_per_action
        # + 1 roas + 6 video = ~35 metrics
        assert len(ads_metrics) >= 30

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
    async def test_actions_expanded(self):
        """Verify expanded action types are correctly parsed."""
        mock_ads_response = _ok_response({"data": [self.FULL_ADS_DATA]})

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        ads = [m for m in result.metrics if m.channel_slug == "meta-ads"]

        leads = next(m for m in ads if m.metric_name == "meta_leads")
        assert leads.value == 25.0

        atc = next(m for m in ads if m.metric_name == "meta_add_to_cart")
        assert atc.value == 40.0

        checkout = next(m for m in ads if m.metric_name == "meta_initiate_checkout")
        assert checkout.value == 20.0

        regs = next(m for m in ads if m.metric_name == "meta_registrations")
        assert regs.value == 10.0

        lpv = next(m for m in ads if m.metric_name == "meta_landing_page_views")
        assert lpv.value == 350.0

    @pytest.mark.asyncio
    async def test_video_metrics(self):
        """Verify video retention fields are parsed correctly."""
        mock_ads_response = _ok_response({"data": [self.FULL_ADS_DATA]})

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        ads = [m for m in result.metrics if m.channel_slug == "meta-ads"]

        p25 = next(m for m in ads if m.metric_name == "meta_video_p25")
        assert p25.value == 1000.0
        assert p25.unit == "count"

        p100 = next(m for m in ads if m.metric_name == "meta_video_p100")
        assert p100.value == 400.0

        avg_watch = next(m for m in ads if m.metric_name == "meta_video_avg_watch_time")
        assert avg_watch.value == 15.3
        assert avg_watch.unit == "seconds"

    @pytest.mark.asyncio
    async def test_roas_and_conversion_value(self):
        """Verify ROAS and conversion value parsing."""
        mock_ads_response = _ok_response({"data": [self.FULL_ADS_DATA]})

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        ads = [m for m in result.metrics if m.channel_slug == "meta-ads"]

        roas = next(m for m in ads if m.metric_name == "meta_purchase_roas")
        assert roas.value == 6.07
        assert roas.unit == "ratio"

        conv_val = next(m for m in ads if m.metric_name == "meta_conversion_value")
        assert conv_val.value == 750.0
        assert conv_val.unit == "currency"
        assert conv_val.currency == "MXN"

        cpa = next(m for m in ads if m.metric_name == "meta_cost_per_purchase")
        assert cpa.value == 8.23

        cpl = next(m for m in ads if m.metric_name == "meta_cost_per_lead")
        assert cpl.value == 4.94

    @pytest.mark.asyncio
    async def test_empty_optional_fields(self):
        """Graceful handling when video/ROAS/actions are absent."""
        minimal_data = {
            "reach": "5000",
            "impressions": "20000",
            "clicks": "200",
            "spend": "50.00",
            "ctr": "1.0",
            "cpm": "2.5",
            "frequency": "4.0",
            "actions": [],
        }
        mock_ads_response = _ok_response({"data": [minimal_data]})

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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        ads = [m for m in result.metrics if m.channel_slug == "meta-ads"]

        # Should have basic metrics but no video/ROAS/conversion metrics
        names = {m.metric_name for m in ads}
        assert "reach" in names
        assert "spend" in names
        assert "meta_purchase_roas" not in names
        assert "meta_video_p25" not in names
        assert "meta_conversion_value" not in names

    @pytest.mark.asyncio
    async def test_currency_from_credentials(self):
        """P6: Currency should come from credentials, not hardcoded USD."""
        creds_eur = {**CREDS, "currency": "EUR"}
        mock_ads_response = _ok_response(
            {
                "data": [
                    {
                        "reach": "1",
                        "impressions": "1",
                        "clicks": "0",
                        "spend": "10.00",
                        "ctr": "0",
                        "cpm": "0",
                        "frequency": "1",
                        "actions": [],
                    },
                ],
            },
        )

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
                TENANT_ID,
                creds_eur,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        spend = next(
            m
            for m in metrics
            if m.metric_name == "spend" and m.channel_slug == "meta-ads"
        )
        assert spend.currency == "EUR"

    @pytest.mark.asyncio
    async def test_currency_defaults_to_usd(self):
        """P6: Without currency in credentials, should default to USD."""
        creds_no_currency = {k: v for k, v in CREDS.items() if k != "currency"}
        mock_ads_response = _ok_response(
            {
                "data": [
                    {
                        "reach": "1",
                        "impressions": "1",
                        "clicks": "0",
                        "spend": "5.00",
                        "ctr": "0",
                        "cpm": "0",
                        "frequency": "1",
                        "actions": [],
                    },
                ],
            },
        )

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
                TENANT_ID,
                creds_no_currency,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        spend = next(
            m
            for m in metrics
            if m.metric_name == "spend" and m.channel_slug == "meta-ads"
        )
        assert spend.currency == "USD"


class TestExtractMetricsDaily:
    """Tests for extract_metrics_daily() — per-day granularity extraction."""

    @pytest.mark.asyncio
    async def test_ig_organic_daily_emits_per_day_metrics(self):
        """IG organic daily should emit one metric per day, AD excluded from breakdownable."""
        from datetime import datetime as dt

        # Map since-timestamp → per-day breakdownable response (with AD)
        day_breakdown_data = {
            int(dt.combine(date(2026, 3, 1), dt.min.time()).timestamp()): {
                "reach": (1000, 200),  # (total, ad_value)
                "total_interactions": (300, 50),
            },
            int(dt.combine(date(2026, 3, 2), dt.min.time()).timestamp()): {
                "reach": (2000, 500),
                "total_interactions": (400, 100),
            },
            int(dt.combine(date(2026, 3, 3), dt.min.time()).timestamp()): {
                "reach": (500, 0),  # no ads this day
                "total_interactions": (200, 0),
            },
        }

        # Non-breakdownable metrics (same for all days for simplicity)
        no_breakdown_data = {
            "accounts_engaged": 120,
            "replies": 10,
        }

        mock_user_node_response = _ok_response(
            {
                "id": "12345",
                "followers_count": 28400,
                "media_count": 342,
            },
        )

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/insights" in url:
                if params.get("period") == "lifetime":
                    return _ok_response({"data": []})
                since = params.get("since")
                if "breakdown" in params:
                    # Breakdownable call — return with AD breakdown
                    values = day_breakdown_data.get(since, {})
                    return _ok_response(
                        {
                            "data": [
                                {
                                    "name": name,
                                    "total_value": {
                                        "value": total,
                                        "breakdowns": [
                                            {
                                                "dimension_keys": [
                                                    "media_product_type",
                                                ],
                                                "results": [
                                                    {
                                                        "dimension_values": ["AD"],
                                                        "value": ad,
                                                    },
                                                    {
                                                        "dimension_values": ["FEED"],
                                                        "value": total - ad,
                                                    },
                                                ]
                                                if ad > 0
                                                else [
                                                    {
                                                        "dimension_values": ["FEED"],
                                                        "value": total,
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                }
                                for name, (total, ad) in values.items()
                            ],
                        },
                    )
                # Non-breakdownable call
                return _ok_response(
                    {
                        "data": [
                            {"name": name, "total_value": {"value": val}}
                            for name, val in no_breakdown_data.items()
                        ],
                    },
                )
            if url.endswith("/12345") and "fields" in params:
                return mock_user_node_response
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            # Closed range [Mar 1, Mar 3] inclusive → 3 days
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 3),
            )
        metrics = result.metrics

        # Reach: 3 days, AD excluded
        reach_metrics = [
            m
            for m in metrics
            if m.metric_name == "reach" and m.channel_slug == "ig-organic"
        ]
        assert len(reach_metrics) == 3
        assert reach_metrics[0].date == date(2026, 3, 1)
        assert reach_metrics[0].value == 800.0  # 1000 - 200
        assert reach_metrics[1].date == date(2026, 3, 2)
        assert reach_metrics[1].value == 1500.0  # 2000 - 500
        assert reach_metrics[2].date == date(2026, 3, 3)
        assert reach_metrics[2].value == 500.0  # 500 - 0

        # total_interactions: 3 days
        interactions = [
            m
            for m in metrics
            if m.metric_name == "total_interactions" and m.channel_slug == "ig-organic"
        ]
        assert len(interactions) == 3

        # followers_count: one reconstructed row per day in the window.
        # Since this mock returns no follows_and_unfollows data, net deltas
        # are all zero and every day shows the same anchor snapshot.
        followers = sorted(
            (m for m in metrics if m.metric_name == "ig_followers_count"),
            key=lambda m: m.date,
        )
        assert len(followers) == 3
        assert [m.date for m in followers] == [
            date(2026, 3, 1),
            date(2026, 3, 2),
            date(2026, 3, 3),
        ]
        assert all(m.value == 28400.0 for m in followers)

        # media_count stays a single snapshot at end_date (not reconstructable)
        media = [m for m in metrics if m.metric_name == "ig_media_count"]
        assert len(media) == 1
        assert media[0].date == date(2026, 3, 3)
        assert media[0].value == 342.0

    @pytest.mark.asyncio
    async def test_meta_ads_daily_uses_time_increment(self):
        """Meta Ads daily should use time_increment=1 and emit per-day metrics."""
        mock_ads_response = _ok_response(
            {
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
                            {
                                "action_type": "offsite_conversion.fb_pixel_purchase",
                                "value": "5",
                            },
                        ],
                    },
                ],
            },
        )

        captured_params = []

        async def mock_get(url, **kwargs):
            captured_params.append(kwargs.get("params", {}))
            if "/act_" in url:
                params = kwargs.get("params", {})
                # Only the account-level request returns the mock payload.
                # Campaign and ad levels return empty to avoid double-counting,
                # since extract_metrics_daily now calls all three extractors.
                if params.get("level") == "account":
                    return mock_ads_response
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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 2),
            )
        metrics = result.metrics

        ads_metrics = [m for m in metrics if m.channel_slug == "meta-ads"]
        # Day 1: 7 simple fields (no cpc/cpp/inline in mock), 0 actions = 7
        # Day 2: 7 simple fields + 1 conversion from actions = 8
        assert len(ads_metrics) == 15

        # Check time_increment was used
        ads_params = [p for p in captured_params if p.get("time_increment") == "1"]
        assert len(ads_params) >= 1

        # Check day 1 reach
        day1_reach = [
            m
            for m in ads_metrics
            if m.metric_name == "reach" and m.date == date(2026, 3, 1)
        ]
        assert len(day1_reach) == 1
        assert day1_reach[0].value == 5000.0

        # Check day 2 conversions
        day2_conv = [
            m
            for m in ads_metrics
            if m.metric_name == "conversions" and m.date == date(2026, 3, 2)
        ]
        assert len(day2_conv) == 1
        assert day2_conv[0].value == 5.0

    @pytest.mark.asyncio
    async def test_fb_organic_daily_emits_per_day(self):
        """FB organic daily should parse values[] for both reach and engagement."""
        mock_reach_response = _ok_response(
            {
                "data": [
                    {
                        "name": "page_impressions_organic_unique",
                        "values": [
                            {"value": 3000, "end_time": "2026-03-01T08:00:00+0000"},
                            {"value": 4000, "end_time": "2026-03-02T08:00:00+0000"},
                        ],
                    },
                ],
            },
        )
        mock_engagement_response = _ok_response(
            {
                "data": [
                    {
                        "name": "page_post_engagements",
                        "values": [
                            {"value": 200, "end_time": "2026-03-01T08:00:00+0000"},
                            {"value": 300, "end_time": "2026-03-02T08:00:00+0000"},
                        ],
                    },
                ],
            },
        )

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            params = kwargs.get("params", {})
            metric = params.get("metric", "")
            if "page_impressions_organic_unique" in metric:
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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 2),
            )
        metrics = result.metrics

        fb_metrics = [m for m in metrics if m.channel_slug == "fb-organic"]
        reach_d1 = [
            m
            for m in fb_metrics
            if m.metric_name == "reach" and m.date == date(2026, 3, 1)
        ]
        assert len(reach_d1) == 1
        assert reach_d1[0].value == 3000.0

        eng_d2 = [
            m
            for m in fb_metrics
            if m.metric_name == "engagement" and m.date == date(2026, 3, 2)
        ]
        assert len(eng_d2) == 1
        assert eng_d2[0].value == 300.0

    @pytest.mark.asyncio
    async def test_empty_credentials_returns_empty(self):
        provider = MetaProvider()
        result = await provider.extract_metrics_daily(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 3),
        )
        assert result.metrics == []


class TestMetaAdsCampaigns:
    """Phase 2: Campaign-level extraction tests."""

    @pytest.mark.asyncio
    async def test_campaign_level_sets_campaign_id(self):
        """Campaign-level extractor should set campaign_id on each metric."""
        campaign_row = {
            "campaign_id": "camp_123",
            "campaign_name": "Spring Sale",
            "reach": "3000",
            "impressions": "10000",
            "clicks": "150",
            "spend": "45.00",
            "ctr": "1.5",
            "cpm": "4.5",
            "frequency": "3.3",
            "actions": [
                {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "5"},
            ],
        }
        mock_campaign_resp = _ok_response({"data": [campaign_row]})
        mock_account_resp = _ok_response({"data": [TestMetaAds.FULL_ADS_DATA]})

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/act_" in url:
                level = params.get("level", "")
                if level == "campaign":
                    return mock_campaign_resp
                return mock_account_resp
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        campaign_metrics = [m for m in metrics if m.campaign_id == "camp_123"]
        assert len(campaign_metrics) >= 8  # at least the simple fields + conversions

        # All should be meta-ads channel
        assert all(m.channel_slug == "meta-ads" for m in campaign_metrics)

        # Account-level metrics should have no campaign_id
        account_metrics = [
            m for m in metrics if m.channel_slug == "meta-ads" and m.campaign_id is None
        ]
        assert len(account_metrics) >= 30  # from the full data

    @pytest.mark.asyncio
    async def test_campaign_daily_sets_date_and_campaign_id(self):
        """Campaign daily should produce per-day per-campaign metrics."""
        rows = [
            {
                "date_start": "2026-03-01",
                "campaign_id": "camp_A",
                "reach": "1000",
                "impressions": "5000",
                "clicks": "50",
                "spend": "20.00",
                "ctr": "1.0",
                "cpm": "4.0",
                "frequency": "5.0",
                "actions": [],
            },
        ]
        mock_resp = _ok_response({"data": rows})

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            if "/act_" in url and params.get("level") == "campaign":
                return mock_resp
            if "/act_" in url:
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
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 1),
            )
        campaign_metrics = [m for m in result.metrics if m.campaign_id == "camp_A"]
        assert len(campaign_metrics) >= 7
        assert all(m.date == date(2026, 3, 1) for m in campaign_metrics)


class TestMetaAdsBreakdowns:
    """Phase 3: Demographic / placement breakdown tests."""

    @pytest.mark.asyncio
    async def test_breakdowns_age_gender_placement(self):
        """Breakdowns extractor should produce JSON metrics for age, gender, placement."""
        age_data = [
            {"age": "18-24", "reach": "2000", "impressions": "8000", "spend": "30.00"},
            {"age": "25-34", "reach": "5000", "impressions": "20000", "spend": "60.00"},
        ]
        gender_data = [
            {
                "gender": "female",
                "reach": "4000",
                "impressions": "15000",
                "spend": "50.00",
            },
            {
                "gender": "male",
                "reach": "3000",
                "impressions": "13000",
                "spend": "40.00",
            },
        ]
        placement_data = [
            {
                "publisher_platform": "facebook",
                "platform_position": "feed",
                "reach": "5000",
                "impressions": "20000",
                "spend": "60.00",
            },
            {
                "publisher_platform": "instagram",
                "platform_position": "story",
                "reach": "2000",
                "impressions": "8000",
                "spend": "30.00",
            },
        ]

        call_index = 0

        async def mock_get(url, **kwargs):
            nonlocal call_index
            params = kwargs.get("params", {})
            if "/act_" in url:
                breakdowns = params.get("breakdowns", "")
                if breakdowns == "age":
                    return _ok_response({"data": age_data})
                if breakdowns == "gender":
                    return _ok_response({"data": gender_data})
                if "publisher_platform" in breakdowns:
                    return _ok_response({"data": placement_data})
                # account-level or campaign-level
                return _ok_response({"data": [TestMetaAds.FULL_ADS_DATA]})
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        metrics = result.metrics

        # Find breakdown metrics
        breakdown_metrics = [
            m for m in metrics if m.unit == "json" and m.channel_slug == "meta-ads"
        ]
        breakdown_names = {m.metric_name for m in breakdown_metrics}

        # Should have 9 breakdown metrics (3 base x 3 dimensions)
        assert "meta_reach_by_age" in breakdown_names
        assert "meta_spend_by_age" in breakdown_names
        assert "meta_impressions_by_age" in breakdown_names
        assert "meta_reach_by_gender" in breakdown_names
        assert "meta_spend_by_gender" in breakdown_names
        assert "meta_impressions_by_gender" in breakdown_names
        assert "meta_reach_by_placement" in breakdown_names
        assert "meta_spend_by_placement" in breakdown_names
        assert "meta_impressions_by_placement" in breakdown_names

        # Verify age breakdown structure
        age_reach = next(
            m for m in breakdown_metrics if m.metric_name == "meta_reach_by_age"
        )
        assert age_reach.value == 0.0  # JSON metrics use 0 as placeholder
        assert "breakdowns" in age_reach.extra
        assert len(age_reach.extra["breakdowns"]) == 2
        assert age_reach.extra["breakdowns"][0]["dimension_values"] == ["18-24"]
        assert age_reach.extra["breakdowns"][0]["value"] == 2000.0

        # Verify placement breakdown has two dimension values
        placement_reach = next(
            m for m in breakdown_metrics if m.metric_name == "meta_reach_by_placement"
        )
        assert placement_reach.extra["breakdowns"][0]["dimension_values"] == [
            "facebook",
            "feed",
        ]

    @pytest.mark.asyncio
    async def test_breakdowns_empty_data(self):
        """Breakdowns should gracefully handle empty API responses."""

        async def mock_get(url, **kwargs):
            if "/act_" in url:
                return _ok_response({"data": [TestMetaAds.FULL_ADS_DATA]})
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        # Breakdown metrics should not be present when API returns empty
        # But the account-level FULL_ADS_DATA is returned for all /act_ URLs
        # so breakdowns will also get FULL_ADS_DATA (which has reach etc.)
        # The test just ensures no crash
        assert len(result.metrics) > 0


class TestExtractOrganicFromBreakdown:
    """Unit tests for _extract_organic_from_breakdown helper."""

    def test_subtracts_ad_value(self):
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "reach",
            "total_value": {
                "value": 500,
                "breakdowns": [
                    {
                        "dimension_keys": ["media_product_type"],
                        "results": [
                            {"dimension_values": ["AD"], "value": 200},
                            {"dimension_values": ["FEED"], "value": 150},
                            {"dimension_values": ["REELS"], "value": 100},
                            {"dimension_values": ["STORY"], "value": 50},
                        ],
                    },
                ],
            },
        }
        assert _extract_organic_from_breakdown(item) == 300.0

    def test_no_ads_running_returns_total(self):
        """When no ads are active, AD doesn't appear in breakdown — return total."""
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "reach",
            "total_value": {
                "value": 400,
                "breakdowns": [
                    {
                        "dimension_keys": ["media_product_type"],
                        "results": [
                            {"dimension_values": ["FEED"], "value": 250},
                            {"dimension_values": ["REELS"], "value": 150},
                        ],
                    },
                ],
            },
        }
        assert _extract_organic_from_breakdown(item) == 400.0

    def test_empty_breakdowns_returns_total(self):
        """When breakdowns list is empty, return total_value as-is."""
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "likes",
            "total_value": {"value": 100, "breakdowns": []},
        }
        assert _extract_organic_from_breakdown(item) == 100.0

    def test_missing_breakdowns_key_returns_total(self):
        """When breakdowns key is missing entirely, return total_value."""
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "saves",
            "total_value": {"value": 75},
        }
        assert _extract_organic_from_breakdown(item) == 75.0

    def test_all_ad_traffic_returns_zero(self):
        """Edge case: all traffic is from ads."""
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "reach",
            "total_value": {
                "value": 500,
                "breakdowns": [
                    {
                        "dimension_keys": ["media_product_type"],
                        "results": [
                            {"dimension_values": ["AD"], "value": 500},
                        ],
                    },
                ],
            },
        }
        assert _extract_organic_from_breakdown(item) == 0.0

    def test_handles_unknown_media_types(self):
        """Unknown types like CAROUSEL_CONTAINER are preserved (not AD)."""
        from src.modules.analytics.infrastructure.providers.meta_provider import (
            _extract_organic_from_breakdown,
        )

        item = {
            "name": "likes",
            "total_value": {
                "value": 600,
                "breakdowns": [
                    {
                        "dimension_keys": ["media_product_type"],
                        "results": [
                            {"dimension_values": ["AD"], "value": 100},
                            {"dimension_values": ["FEED"], "value": 200},
                            {"dimension_values": ["CAROUSEL_CONTAINER"], "value": 150},
                            {"dimension_values": ["POST"], "value": 150},
                        ],
                    },
                ],
            },
        }
        # 600 - 100 (AD) = 500
        assert _extract_organic_from_breakdown(item) == 500.0


class TestFBOrganicMetricName:
    """Verify FB organic uses the organic-only metric variant."""

    @pytest.mark.asyncio
    async def test_uses_organic_unique_metric(self):
        """Ensure _extract_facebook_organic requests page_impressions_organic_unique."""
        captured_params = []

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            captured_params.append(params)
            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        fb_reach_calls = [
            p for p in captured_params if "page_impressions" in p.get("metric", "")
        ]
        assert len(fb_reach_calls) >= 1
        assert fb_reach_calls[0]["metric"] == "page_impressions_organic_unique"


class TestMetaProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_credentials(self):
        provider = MetaProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 15),
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


class TestInstagramFollowTypeBreakdown:
    """Tests for the follows_and_unfollows metric which requires breakdown=follow_type.

    Meta's Graph API returns NO data for `follows_and_unfollows` unless the
    request includes `breakdown=follow_type`. The response is nested:
        total_value.breakdowns[0].results:
            [{dimension_values: ["FOLLOWER"],      value: N},
             {dimension_values: ["NON_FOLLOWER"],  value: M}]

    We emit three separate metrics so the UI can show gained, lost, and net
    independently without losing granularity:
        - ig_follows_gained       = FOLLOWER value      (new followers)
        - ig_follows_lost         = NON_FOLLOWER value  (unfollows)
        - ig_follows_and_unfollows = gained - lost      (net delta)
    """

    @pytest.mark.asyncio
    async def test_daily_emits_gained_lost_and_net_per_day(self):
        """extract_metrics_daily emits 3 metrics per day from the follow_type breakdown."""
        from datetime import datetime as dt

        # Per-day values: (gained, lost). Includes a negative-net day.
        day_values: dict[int, tuple[int, int]] = {
            int(dt.combine(date(2026, 3, 1), dt.min.time()).timestamp()): (42, 3),
            int(dt.combine(date(2026, 3, 2), dt.min.time()).timestamp()): (8, 11),
            int(dt.combine(date(2026, 3, 3), dt.min.time()).timestamp()): (20, 0),
        }

        # Track that the extractor actually passed breakdown=follow_type
        follow_type_call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal follow_type_call_count
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if "/insights" in url and params.get("period") == "lifetime":
                return _ok_response({"data": []})

            if "/insights" in url and metric == "follows_and_unfollows":
                # Must be called with breakdown=follow_type
                assert params.get("breakdown") == "follow_type", (
                    "follows_and_unfollows must be requested with breakdown=follow_type"
                )
                follow_type_call_count += 1
                since = params.get("since")
                gained, lost = day_values.get(since, (0, 0))
                return _ok_response(
                    {
                        "data": [
                            {
                                "name": "follows_and_unfollows",
                                "period": "day",
                                "total_value": {
                                    "breakdowns": [
                                        {
                                            "dimension_keys": ["follow_type"],
                                            "results": [
                                                {
                                                    "dimension_values": ["FOLLOWER"],
                                                    "value": gained,
                                                },
                                                {
                                                    "dimension_values": [
                                                        "NON_FOLLOWER",
                                                    ],
                                                    "value": lost,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                )

            if "/insights" in url:
                # Other IG insights calls — empty
                return _ok_response({"data": []})

            if url.endswith("/12345") and "fields" in params:
                return _ok_response(
                    {"id": "12345", "followers_count": 1000, "media_count": 50},
                )

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            # Closed [Mar 1, Mar 3] inclusive → 3 days
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 3),
            )

        # One dedicated follow_type call per day
        assert follow_type_call_count == 3

        metrics = result.metrics

        gained = sorted(
            (m for m in metrics if m.metric_name == "ig_follows_gained"),
            key=lambda m: m.date,
        )
        lost = sorted(
            (m for m in metrics if m.metric_name == "ig_follows_lost"),
            key=lambda m: m.date,
        )
        net = sorted(
            (m for m in metrics if m.metric_name == "ig_follows_and_unfollows"),
            key=lambda m: m.date,
        )

        assert len(gained) == 3, f"expected 3 gained rows, got {len(gained)}"
        assert len(lost) == 3
        assert len(net) == 3

        # Day 1: gained 42, lost 3, net +39
        assert gained[0].date == date(2026, 3, 1)
        assert gained[0].value == 42.0
        assert lost[0].value == 3.0
        assert net[0].value == 39.0

        # Day 2: gained 8, lost 11, net -3 (negative is valid)
        assert gained[1].value == 8.0
        assert lost[1].value == 11.0
        assert net[1].value == -3.0

        # Day 3: gained 20, lost 0, net +20
        assert gained[2].value == 20.0
        assert lost[2].value == 0.0
        assert net[2].value == 20.0

        # All three metrics must be scoped to ig-organic and tagged with source
        for m in gained + lost + net:
            assert m.channel_slug == "ig-organic"
            assert m.provider == "meta"
            assert m.unit == "count"

    @pytest.mark.asyncio
    async def test_legacy_window_extractor_emits_gained_lost_and_net(self):
        """extract_metrics (window-aggregated) emits the same 3 metrics once per window."""
        follow_type_call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal follow_type_call_count
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if "/insights" in url and params.get("period") == "lifetime":
                return _ok_response({"data": []})

            if "/insights" in url and metric == "follows_and_unfollows":
                assert params.get("breakdown") == "follow_type", (
                    "follows_and_unfollows must be requested with breakdown=follow_type"
                )
                follow_type_call_count += 1
                return _ok_response(
                    {
                        "data": [
                            {
                                "name": "follows_and_unfollows",
                                "period": "day",
                                "total_value": {
                                    "breakdowns": [
                                        {
                                            "dimension_keys": ["follow_type"],
                                            "results": [
                                                {
                                                    "dimension_values": ["FOLLOWER"],
                                                    "value": 120,
                                                },
                                                {
                                                    "dimension_values": [
                                                        "NON_FOLLOWER",
                                                    ],
                                                    "value": 45,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                )

            if "/insights" in url:
                return _ok_response({"data": []})

            if url.endswith("/12345") and "fields" in params:
                return _ok_response(
                    {"id": "12345", "followers_count": 5000, "media_count": 200},
                )

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        assert follow_type_call_count >= 1
        metrics = result.metrics

        ig = [m for m in metrics if m.channel_slug == "ig-organic"]

        gained = [m for m in ig if m.metric_name == "ig_follows_gained"]
        lost = [m for m in ig if m.metric_name == "ig_follows_lost"]
        net = [m for m in ig if m.metric_name == "ig_follows_and_unfollows"]

        assert len(gained) == 1
        assert len(lost) == 1
        assert len(net) == 1

        assert gained[0].value == 120.0
        assert lost[0].value == 45.0
        assert net[0].value == 75.0  # 120 - 45
        assert net[0].date == date(2026, 3, 15)

    @pytest.mark.asyncio
    async def test_missing_dimension_defaults_to_zero(self):
        """If Meta omits a dimension (e.g. no unfollows), its value is treated as 0."""

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if "/insights" in url and params.get("period") == "lifetime":
                return _ok_response({"data": []})

            if "/insights" in url and metric == "follows_and_unfollows":
                # Only FOLLOWER present — NON_FOLLOWER missing entirely
                return _ok_response(
                    {
                        "data": [
                            {
                                "name": "follows_and_unfollows",
                                "period": "day",
                                "total_value": {
                                    "breakdowns": [
                                        {
                                            "dimension_keys": ["follow_type"],
                                            "results": [
                                                {
                                                    "dimension_values": ["FOLLOWER"],
                                                    "value": 17,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                )

            if "/insights" in url:
                return _ok_response({"data": []})

            if url.endswith("/12345") and "fields" in params:
                return _ok_response(
                    {"id": "12345", "followers_count": 100, "media_count": 10},
                )

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            # Closed interval [Mar 1, Mar 1] → single day.
            # Also serves as a regression guard against the half-open loop
            # bug where start == end would silently yield zero iterations.
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 1),
            )

        metrics = result.metrics
        gained = [m for m in metrics if m.metric_name == "ig_follows_gained"]
        lost = [m for m in metrics if m.metric_name == "ig_follows_lost"]
        net = [m for m in metrics if m.metric_name == "ig_follows_and_unfollows"]

        assert len(gained) == 1 and gained[0].value == 17.0
        assert len(lost) == 1 and lost[0].value == 0.0
        assert len(net) == 1 and net[0].value == 17.0

    @pytest.mark.asyncio
    async def test_daily_extractor_covers_single_day_window(self):
        """Regression: when start_date == end_date, the daily loop must still run.

        Before the closed-interval fix, `while current < end_date` skipped
        the loop entirely when start == end. This is exactly what happened
        during ETL backfill when only one day was missing — the extractor
        silently emitted zero metrics.
        """
        calls_seen = 0

        async def mock_get(url, **kwargs):
            nonlocal calls_seen
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if "/insights" in url and params.get("period") == "lifetime":
                return _ok_response({"data": []})

            if "/insights" in url and metric == "follows_and_unfollows":
                calls_seen += 1
                return _ok_response(
                    {
                        "data": [
                            {
                                "name": "follows_and_unfollows",
                                "period": "day",
                                "total_value": {
                                    "breakdowns": [
                                        {
                                            "dimension_keys": ["follow_type"],
                                            "results": [
                                                {
                                                    "dimension_values": ["FOLLOWER"],
                                                    "value": 5,
                                                },
                                                {
                                                    "dimension_values": [
                                                        "NON_FOLLOWER",
                                                    ],
                                                    "value": 1,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                )

            if "/insights" in url:
                return _ok_response({"data": []})

            if url.endswith("/12345") and "fields" in params:
                return _ok_response(
                    {"id": "12345", "followers_count": 100, "media_count": 10},
                )

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            # start_date == end_date — the exact scenario that triggered the bug
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 1),
            )

        # The follow_type call must have happened at least once
        assert calls_seen >= 1, (
            "Daily extractor skipped the single-day window — off-by-one bug"
        )

        gained = [m for m in result.metrics if m.metric_name == "ig_follows_gained"]
        assert len(gained) == 1
        assert gained[0].date == date(2026, 3, 1)
        assert gained[0].value == 5.0

    @pytest.mark.asyncio
    async def test_followers_count_reconstructed_backwards_from_deltas(self):
        """Daily ig_followers_count is rebuilt backwards from current snapshot + deltas.

        Given Meta's user node returns the current followers count and the
        follow_type breakdown gives us per-day gained/lost, we can recover
        the historical follower count curve. Walk backward: the value at end
        of day D-1 is the value at end of D minus the net change of day D.
        """
        from datetime import datetime as dt

        # Daily follower changes as (gained, lost) tuples
        day_values: dict[int, tuple[int, int]] = {
            int(dt.combine(date(2026, 3, 1), dt.min.time()).timestamp()): (10, 2),
            int(dt.combine(date(2026, 3, 2), dt.min.time()).timestamp()): (5, 0),
            int(dt.combine(date(2026, 3, 3), dt.min.time()).timestamp()): (3, 1),
        }
        current_followers = 1000  # snapshot "now"

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if "/insights" in url and params.get("period") == "lifetime":
                return _ok_response({"data": []})

            if "/insights" in url and metric == "follows_and_unfollows":
                since = params.get("since")
                gained, lost = day_values.get(since, (0, 0))
                return _ok_response(
                    {
                        "data": [
                            {
                                "name": "follows_and_unfollows",
                                "period": "day",
                                "total_value": {
                                    "breakdowns": [
                                        {
                                            "dimension_keys": ["follow_type"],
                                            "results": [
                                                {
                                                    "dimension_values": ["FOLLOWER"],
                                                    "value": gained,
                                                },
                                                {
                                                    "dimension_values": [
                                                        "NON_FOLLOWER",
                                                    ],
                                                    "value": lost,
                                                },
                                            ],
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                )

            if "/insights" in url:
                return _ok_response({"data": []})

            if url.endswith("/12345") and "fields" in params:
                return _ok_response(
                    {
                        "id": "12345",
                        "followers_count": current_followers,
                        "media_count": 50,
                    },
                )

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 3),
            )

        followers = sorted(
            (m for m in result.metrics if m.metric_name == "ig_followers_count"),
            key=lambda m: m.date,
        )
        assert len(followers) == 3

        # Walk backward from anchor:
        #   end of Mar 3 = 1000 (anchor)
        #   end of Mar 2 = 1000 - net(Mar 3) = 1000 - (3 - 1) = 998
        #   end of Mar 1 = 998  - net(Mar 2) = 998  - (5 - 0) = 993
        assert followers[2].date == date(2026, 3, 3)
        assert followers[2].value == 1000.0
        assert followers[1].date == date(2026, 3, 2)
        assert followers[1].value == 998.0
        assert followers[0].date == date(2026, 3, 1)
        assert followers[0].value == 993.0

        # Cross-check consistency: end-of-D minus end-of-D-1 must equal net(D)
        net_by_date = {
            m.date: m.value
            for m in result.metrics
            if m.metric_name == "ig_follows_and_unfollows"
        }
        for i in range(1, len(followers)):
            delta = followers[i].value - followers[i - 1].value
            assert delta == net_by_date.get(followers[i].date, 0.0), (
                f"Reconstruction drift on {followers[i].date}: "
                f"delta={delta}, net={net_by_date.get(followers[i].date)}"
            )

    @pytest.mark.asyncio
    async def test_follows_and_unfollows_not_in_generic_no_breakdown_call(self):
        """follows_and_unfollows must NOT be mixed into the generic _IG_NO_BREAKDOWN call.

        Meta returns no total_value for follows_and_unfollows without
        breakdown=follow_type, which silently produced zero values pre-fix.
        Regression guard: no IG insights call should include it without the breakdown.
        """
        calls_without_breakdown: list[str] = []

        async def mock_get(url, **kwargs):
            params = kwargs.get("params", {})
            metric = params.get("metric", "")

            if (
                "/insights" in url
                and params.get("period") != "lifetime"
                and "follows_and_unfollows" in metric
                and not params.get("breakdown")
            ):
                calls_without_breakdown.append(metric)

            return _ok_response({"data": []})

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get = AsyncMock(side_effect=mock_get)
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = MetaProvider()
            await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 3),
            )
            await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 3),
            )

        assert calls_without_breakdown == [], (
            f"follows_and_unfollows was requested without breakdown=follow_type: "
            f"{calls_without_breakdown}"
        )
