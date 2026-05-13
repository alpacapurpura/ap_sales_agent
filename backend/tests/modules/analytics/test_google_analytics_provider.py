"""Tests for GoogleAnalyticsProvider — GA4 organic search segmentation.

Mocks GoogleAnalyticsAdapter.run_report() responses.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_analytics_engine.infrastructure.providers.google_analytics_provider import (
    GoogleAnalyticsProvider,
)

TENANT_ID = uuid4()
CREDS = {
    "property_id": "123456",
    "client_id": "test_client",
    "client_secret": "test_secret",
    "refresh_token": "test_refresh",
    "token": "test_token",
}


class TestGAProviderBasics:
    def test_provider_name(self):
        p = GoogleAnalyticsProvider()
        assert p.provider_name() == "google_analytics"

    def test_rate_limit_config(self):
        cfg = GoogleAnalyticsProvider().rate_limit_config()
        assert cfg["requests_per_minute"] == 20


class TestGA4Segmentation:
    @pytest.mark.asyncio
    async def test_segments_google_organic(self):
        mock_report = {
            "row_count": 3,
            "rows": [
                {
                    "dimensions": ["google", "organic"],
                    "metrics": [
                        "1000",
                        "800",
                        "0.35",
                        "650",
                        "500",
                        "1200",
                        "750",
                        "0.65",
                    ],
                },
                {
                    "dimensions": ["(direct)", "(none)"],
                    "metrics": [
                        "500",
                        "400",
                        "0.20",
                        "400",
                        "300",
                        "600",
                        "380",
                        "0.80",
                    ],
                },
                {
                    "dimensions": ["bing", "organic"],
                    "metrics": ["100", "80", "0.50", "50", "40", "90", "75", "0.50"],
                },
            ],
            "metadata": {},
        }

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.google_analytics_provider.create_google_analytics_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        google_organic = [m for m in metrics if m.channel_slug == "google-organic"]
        assert len(google_organic) == 8  # 8 metrics now
        sessions = next(m for m in google_organic if m.metric_name == "sessions")
        assert sessions.value == 1000.0
        users = next(m for m in google_organic if m.metric_name == "users")
        assert users.value == 800.0
        bounce = next(m for m in google_organic if m.metric_name == "bounceRate")
        assert bounce.value == pytest.approx(0.35)
        assert bounce.unit == "percentage"
        engaged = next(m for m in google_organic if m.metric_name == "engagedSessions")
        assert engaged.value == 650.0
        new_users = next(m for m in google_organic if m.metric_name == "newUsers")
        assert new_users.value == 500.0
        page_views = next(m for m in google_organic if m.metric_name == "screenPageViews")
        assert page_views.value == 1200.0
        active_users = next(m for m in google_organic if m.metric_name == "activeUsers")
        assert active_users.value == 750.0
        engagement = next(m for m in google_organic if m.metric_name == "engagementRate")
        assert engagement.value == pytest.approx(0.65)
        assert engagement.unit == "percentage"

    @pytest.mark.asyncio
    async def test_segments_direct(self):
        mock_report = {
            "row_count": 1,
            "rows": [
                {
                    "dimensions": ["(direct)", "(none)"],
                    "metrics": [
                        "500",
                        "400",
                        "0.20",
                        "400",
                        "300",
                        "600",
                        "380",
                        "0.80",
                    ],
                },
            ],
            "metadata": {},
        }

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.google_analytics_provider.create_google_analytics_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        direct = [m for m in metrics if m.channel_slug == "direct"]
        assert len(direct) == 8
        sessions = next(m for m in direct if m.metric_name == "sessions")
        assert sessions.value == 500.0

    @pytest.mark.asyncio
    async def test_segments_ai_search(self):
        mock_report = {
            "row_count": 2,
            "rows": [
                {
                    "dimensions": ["perplexity.ai", "referral"],
                    "metrics": [
                        "200",
                        "180",
                        "0.10",
                        "180",
                        "150",
                        "300",
                        "170",
                        "0.90",
                    ],
                },
                {
                    "dimensions": ["chatgpt.com", "referral"],
                    "metrics": [
                        "150",
                        "120",
                        "0.20",
                        "120",
                        "90",
                        "200",
                        "110",
                        "0.80",
                    ],
                },
            ],
            "metadata": {},
        }

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.google_analytics_provider.create_google_analytics_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        ai_search = [m for m in metrics if m.channel_slug == "ai-search-organic"]
        assert len(ai_search) == 8
        sessions = next(m for m in ai_search if m.metric_name == "sessions")
        assert sessions.value == 350.0  # 200+150
        users = next(m for m in ai_search if m.metric_name == "users")
        assert users.value == 300.0  # 180+120
        # bounceRate should be weighted average: (0.10*200 + 0.20*150) / 350
        bounce = next(m for m in ai_search if m.metric_name == "bounceRate")
        expected_bounce = (0.10 * 200 + 0.20 * 150) / 350
        assert bounce.value == pytest.approx(expected_bounce, rel=1e-3)


class TestGA4DailyExtraction:
    @pytest.mark.asyncio
    async def test_extract_metrics_daily_returns_per_day(self):
        """extract_metrics_daily with date dimension returns per-day metrics."""
        mock_report = {
            "rows": [
                {
                    "dimensions": ["google", "organic", "20260301"],
                    "metrics": ["100", "80", "0.30", "70", "50", "120", "75", "0.70"],
                },
                {
                    "dimensions": ["google", "organic", "20260302"],
                    "metrics": [
                        "200",
                        "160",
                        "0.25",
                        "150",
                        "100",
                        "240",
                        "150",
                        "0.75",
                    ],
                },
                {
                    "dimensions": ["(direct)", "(none)", "20260301"],
                    "metrics": ["50", "40", "0.15", "45", "30", "60", "38", "0.90"],
                },
            ],
        }

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.google_analytics_provider.create_google_analytics_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            result = await provider.extract_metrics_daily(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 2),
            )

        metrics = result.metrics
        # Google organic on March 1
        go_mar1 = [m for m in metrics if m.channel_slug == "google-organic" and m.date == date(2026, 3, 1)]
        assert len(go_mar1) == 8
        sessions_mar1 = next(m for m in go_mar1 if m.metric_name == "sessions")
        assert sessions_mar1.value == 100.0

        # Google organic on March 2
        go_mar2 = [m for m in metrics if m.channel_slug == "google-organic" and m.date == date(2026, 3, 2)]
        assert len(go_mar2) == 8
        sessions_mar2 = next(m for m in go_mar2 if m.metric_name == "sessions")
        assert sessions_mar2.value == 200.0

        # Direct on March 1
        direct_mar1 = [m for m in metrics if m.channel_slug == "direct" and m.date == date(2026, 3, 1)]
        assert len(direct_mar1) == 8

    @pytest.mark.asyncio
    async def test_extract_metrics_daily_missing_property(self):
        provider = GoogleAnalyticsProvider()
        result = await provider.extract_metrics_daily(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 2),
        )
        assert result.metrics == []


class TestGAProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_property_id(self):
        provider = GoogleAnalyticsProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_empty_report(self):
        mock_report = {"row_count": 0, "rows": [], "metadata": {}}

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.google_analytics_provider.create_google_analytics_adapter",
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
        assert result.metrics == []
