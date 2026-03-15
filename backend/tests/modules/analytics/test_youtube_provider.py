"""Tests for YouTubeProvider — YouTube organic channel.

Mocks YouTubeAnalyticsAdapter methods.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.youtube_provider import (
    YouTubeProvider,
)


TENANT_ID = uuid4()
CREDS = {
    "token": "test_token",
    "refresh_token": "test_refresh",
    "client_id": "test_client",
    "client_secret": "test_secret",
}


class TestYouTubeProviderBasics:
    def test_provider_name(self):
        assert YouTubeProvider().provider_name() == "youtube"

    def test_rate_limit_config(self):
        cfg = YouTubeProvider().rate_limit_config()
        assert "requests_per_minute" in cfg


class TestYouTubeOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_overview = {
            "views": 15000,
            "likes": 500,
            "dislikes": 10,
            "estimatedMinutesWatched": 45000,
        }

        with patch(
            "src.modules.analytics.infrastructure.providers.youtube_provider.YouTubeAnalyticsAdapter"
        ) as MockAdapter:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(return_value=mock_overview)
            MockAdapter.return_value = adapter_instance

            with patch("asyncio.to_thread", new_callable=lambda: AsyncMock) as mock_thread:
                mock_thread.return_value = mock_overview

                provider = YouTubeProvider()
                metrics = await provider.extract_metrics(
                    TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
                )

        yt_metrics = [m for m in metrics if m.channel_slug == "yt-organic"]
        assert len(yt_metrics) >= 2

        reach = next(m for m in yt_metrics if m.metric_name == "reach")
        assert reach.value == 15000.0

        engagement = next(m for m in yt_metrics if m.metric_name == "engagement")
        assert engagement.value == 510.0  # likes + dislikes (total interactions)


class TestYouTubeProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        provider = YouTubeProvider()
        metrics = await provider.extract_metrics(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 15)
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_api_exception(self):
        with patch(
            "src.modules.analytics.infrastructure.providers.youtube_provider.YouTubeAnalyticsAdapter"
        ) as MockAdapter:
            MockAdapter.side_effect = Exception("Auth failed")

            provider = YouTubeProvider()
            metrics = await provider.extract_metrics(
                TENANT_ID, CREDS, date(2026, 3, 1), date(2026, 3, 15)
            )
        assert metrics == []
