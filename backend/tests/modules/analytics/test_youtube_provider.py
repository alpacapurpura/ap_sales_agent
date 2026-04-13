"""Tests for YouTubeProvider — YouTube organic channel.

Mocks YouTubeAnalyticsAdapter methods.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

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

MOCK_OVERVIEW = {
    "views": 15000,
    "likes": 500,
    "dislikes": 10,
    "estimatedMinutesWatched": 45000,
    "averageViewDuration": 180.5,
    "subscribersGained": 120,
    "subscribersLost": 15,
    "comments": 340,
    "shares": 85,
    "averageViewPercentage": 42.3,
}

MOCK_CARD_DATA = {
    "cardClicks": 250,
    "cardImpressions": 5000,
    "endScreenElementClicks": 180,
    "endScreenElementImpressions": 3000,
}


def _patch_adapter_and_thread(overview=None, card_data=None):
    """Return a context manager that patches the adapter + asyncio.to_thread."""
    overview = overview if overview is not None else MOCK_OVERVIEW
    card_data = card_data if card_data is not None else MOCK_CARD_DATA

    adapter_patch = patch(
        "src.modules.analytics.infrastructure.providers.youtube_provider.YouTubeAnalyticsAdapter",
    )
    # asyncio.to_thread calls the function — we need to route by function
    call_results = {
        "get_channel_overview": overview,
        "get_card_metrics": card_data,
    }

    async def fake_to_thread(fn, *args, **kwargs):
        name = getattr(fn, "_mock_name", None) or getattr(fn, "__name__", "")
        if name in call_results:
            return call_results[name]
        return fn(*args, **kwargs)

    thread_patch = patch(
        "src.modules.analytics.infrastructure.providers.youtube_provider.asyncio.to_thread",
        side_effect=fake_to_thread,
    )
    return adapter_patch, thread_patch, call_results


class TestYouTubeProviderBasics:
    def test_provider_name(self):
        assert YouTubeProvider().provider_name() == "youtube"

    def test_rate_limit_config(self):
        cfg = YouTubeProvider().rate_limit_config()
        assert "requests_per_minute" in cfg


class TestYouTubeOrganic:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread()

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=MOCK_CARD_DATA)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        metrics = result.metrics
        yt_metrics = [m for m in metrics if m.channel_slug == "yt-organic"]
        assert len(yt_metrics) >= 2

        views = next(m for m in yt_metrics if m.metric_name == "views")
        assert views.value == 15000.0

        engagement = next(m for m in yt_metrics if m.metric_name == "engagement")
        assert engagement.value == 510.0  # likes + dislikes (total interactions)


class TestYouTubeExpandedMetrics:
    """Tests for expanded overview metrics: comments, shares, avg_view_percentage, subscribers_lost."""

    @pytest.mark.asyncio
    async def test_comments_and_shares(self):
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread()

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=MOCK_CARD_DATA)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        yt_metrics = {m.metric_name: m for m in result.metrics if m.channel_slug == "yt-organic"}

        assert "comments" in yt_metrics
        assert yt_metrics["comments"].value == 340.0

        assert "shares" in yt_metrics
        assert yt_metrics["shares"].value == 85.0

    @pytest.mark.asyncio
    async def test_subscribers_lost(self):
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread()

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=MOCK_CARD_DATA)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        yt_metrics = {m.metric_name: m for m in result.metrics if m.channel_slug == "yt-organic"}

        assert "subscribers_lost" in yt_metrics
        assert yt_metrics["subscribers_lost"].value == 15.0

    @pytest.mark.asyncio
    async def test_avg_view_percentage(self):
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread()

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=MOCK_CARD_DATA)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        yt_metrics = {m.metric_name: m for m in result.metrics if m.channel_slug == "yt-organic"}

        assert "avg_view_percentage" in yt_metrics
        assert yt_metrics["avg_view_percentage"].value == 42.3
        assert yt_metrics["avg_view_percentage"].unit == "percentage"


class TestYouTubeCardMetrics:
    """Tests for card and end screen sub-extractor."""

    @pytest.mark.asyncio
    async def test_card_metrics_happy_path(self):
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread()

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=MOCK_CARD_DATA)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        yt_metrics = {m.metric_name: m for m in result.metrics if m.channel_slug == "yt-organic"}

        assert "card_clicks" in yt_metrics
        assert yt_metrics["card_clicks"].value == 250.0
        assert "card_impressions" in yt_metrics
        assert yt_metrics["card_impressions"].value == 5000.0
        assert "end_screen_clicks" in yt_metrics
        assert yt_metrics["end_screen_clicks"].value == 180.0
        assert "end_screen_impressions" in yt_metrics
        assert yt_metrics["end_screen_impressions"].value == 3000.0

        # Calculated rates
        assert "card_click_rate" in yt_metrics
        assert yt_metrics["card_click_rate"].value == 5.0  # 250/5000 * 100
        assert "end_screen_click_rate" in yt_metrics
        assert yt_metrics["end_screen_click_rate"].value == 6.0  # 180/3000 * 100

    @pytest.mark.asyncio
    async def test_zero_impressions_no_rate(self):
        """When impressions = 0, click rates should not be emitted."""
        zero_card_data = {
            "cardClicks": 0,
            "cardImpressions": 0,
            "endScreenElementClicks": 0,
            "endScreenElementImpressions": 0,
        }
        adapter_patch, thread_patch, _ = _patch_adapter_and_thread(
            card_data=zero_card_data,
        )

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(return_value=zero_card_data)
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        yt_metrics = {m.metric_name: m for m in result.metrics}
        assert "card_click_rate" not in yt_metrics
        assert "end_screen_click_rate" not in yt_metrics

    @pytest.mark.asyncio
    async def test_card_api_failure_partial_success(self):
        """Card API failure should not block overview metrics (partial success)."""
        adapter_patch = patch(
            "src.modules.analytics.infrastructure.providers.youtube_provider.YouTubeAnalyticsAdapter",
        )

        async def fake_to_thread(fn, *args, **kwargs):
            name = getattr(fn, "_mock_name", None) or getattr(fn, "__name__", "")
            if name == "get_channel_overview":
                return MOCK_OVERVIEW
            if name == "get_card_metrics":
                msg = "Card metrics unavailable"
                raise RuntimeError(msg)
            return fn(*args, **kwargs)

        thread_patch = patch(
            "src.modules.analytics.infrastructure.providers.youtube_provider.asyncio.to_thread",
            side_effect=fake_to_thread,
        )

        with adapter_patch as MockAdapter, thread_patch:
            adapter_instance = MagicMock()
            adapter_instance.get_channel_overview = MagicMock(
                return_value=MOCK_OVERVIEW,
            )
            adapter_instance.get_card_metrics = MagicMock(
                side_effect=RuntimeError("Card metrics unavailable"),
            )
            MockAdapter.return_value = adapter_instance

            provider = YouTubeProvider()
            result = await provider.extract_metrics(
                TENANT_ID,
                CREDS,
                date(2026, 3, 1),
                date(2026, 3, 15),
            )

        # Overview metrics should still be present
        yt_metrics = {m.metric_name: m for m in result.metrics}
        assert "views" in yt_metrics
        assert "engagement" in yt_metrics

        # Card metrics should be absent
        assert "card_clicks" not in yt_metrics

        # Should report a partial failure
        assert result.has_partial_failures
        assert any(f.extractor_name == "youtube_cards" for f in result.failures)


class TestYouTubeProviderErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        provider = YouTubeProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_api_exception(self):
        """API exceptions propagate to the pipeline, which handles them as FAILED runs."""
        with patch(
            "src.modules.analytics.infrastructure.providers.youtube_provider.YouTubeAnalyticsAdapter",
        ) as MockAdapter:
            MockAdapter.side_effect = Exception("Auth failed")

            provider = YouTubeProvider()
            with pytest.raises(Exception, match="Auth failed"):
                await provider.extract_metrics(
                    TENANT_ID,
                    CREDS,
                    date(2026, 3, 1),
                    date(2026, 3, 15),
                )
