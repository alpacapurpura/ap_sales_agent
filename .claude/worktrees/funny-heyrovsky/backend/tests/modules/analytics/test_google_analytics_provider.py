"""Tests for GoogleAnalyticsProvider — GA4 organic search segmentation.

Mocks GoogleAnalyticsAdapter.run_report() responses.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.google_analytics_provider import (
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
        assert cfg["requests_per_minute"] == 10


class TestGA4Segmentation:
    @pytest.mark.asyncio
    async def test_segments_google_organic(self):
        mock_report = {
            "row_count": 3,
            "rows": [
                {"dimensions": ["google", "organic"], "metrics": ["1000", "800"]},
                {"dimensions": ["(direct)", "(none)"], "metrics": ["500", "400"]},
                {"dimensions": ["bing", "organic"], "metrics": ["100", "80"]},
            ],
            "metadata": {"dimensions": ["sessionSource", "sessionMedium"], "metrics": ["sessions", "totalUsers"]},
        }

        with patch(
            "src.modules.analytics.infrastructure.providers.google_analytics_provider.GoogleAnalyticsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        google_organic = [m for m in metrics if m.channel_slug == "google-organic"]
        assert len(google_organic) == 2
        sessions = next(m for m in google_organic if m.metric_name == "sessions")
        assert sessions.value == 1000.0
        users = next(m for m in google_organic if m.metric_name == "users")
        assert users.value == 800.0

    @pytest.mark.asyncio
    async def test_segments_direct(self):
        mock_report = {
            "row_count": 1,
            "rows": [
                {"dimensions": ["(direct)", "(none)"], "metrics": ["500", "400"]},
            ],
            "metadata": {"dimensions": ["sessionSource", "sessionMedium"], "metrics": ["sessions", "totalUsers"]},
        }

        with patch(
            "src.modules.analytics.infrastructure.providers.google_analytics_provider.GoogleAnalyticsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        direct = [m for m in metrics if m.channel_slug == "direct"]
        assert len(direct) == 2
        sessions = next(m for m in direct if m.metric_name == "sessions")
        assert sessions.value == 500.0

    @pytest.mark.asyncio
    async def test_segments_ai_search(self):
        mock_report = {
            "row_count": 2,
            "rows": [
                {"dimensions": ["perplexity.ai", "referral"], "metrics": ["200", "180"]},
                {"dimensions": ["chatgpt.com", "referral"], "metrics": ["150", "120"]},
            ],
            "metadata": {"dimensions": ["sessionSource", "sessionMedium"], "metrics": ["sessions", "totalUsers"]},
        }

        with patch(
            "src.modules.analytics.infrastructure.providers.google_analytics_provider.GoogleAnalyticsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )

        ai_search = [m for m in metrics if m.channel_slug == "ai-search-organic"]
        assert len(ai_search) == 2
        sessions = next(m for m in ai_search if m.metric_name == "sessions")
        assert sessions.value == 350.0  # 200+150
        users = next(m for m in ai_search if m.metric_name == "users")
        assert users.value == 300.0  # 180+120


class TestGAProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_property_id(self):
        provider = GoogleAnalyticsProvider()
        metrics = await provider.extract_metrics(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 15)
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_empty_report(self):
        mock_report = {"row_count": 0, "rows": [], "metadata": {}}

        with patch(
            "src.modules.analytics.infrastructure.providers.google_analytics_provider.GoogleAnalyticsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.run_report = AsyncMock(return_value=mock_report)
            MockAdapter.return_value = adapter_instance

            provider = GoogleAnalyticsProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        assert metrics == []
