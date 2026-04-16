"""YouTubeProvider — extracts YouTube organic channel metrics.

Channel slug: yt-organic
Metrics: overview (views, engagement, watch_time, subs, comments, shares, avg_view_percentage)
       + card/end screen metrics (isolated sub-extractor)

Uses existing YouTubeAnalyticsAdapter wrapped in asyncio.to_thread() (sync Google SDK).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog
from google.auth.exceptions import RefreshError, TransportError

from src.modules.analytics.domain.exceptions import ConnectionRevokedError
from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.shared.links.ports.channel_adapter import create_youtube_adapter

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from src.modules.connections.infrastructure.channels.youtube_analytics import (
        YouTubeAnalyticsAdapter,
    )

logger = structlog.get_logger(__name__)

# Maps YouTube Analytics API response keys to our internal metric names
_DIRECT_MAP = {
    "views": ("views", "count"),
    "estimatedMinutesWatched": ("watch_time_minutes", "count"),
    "averageViewDuration": ("avg_view_duration", "seconds"),
    "subscribersGained": ("subscribers_gained", "count"),
    "subscribersLost": ("subscribers_lost", "count"),
    "comments": ("comments", "count"),
    "shares": ("shares", "count"),
    "averageViewPercentage": ("avg_view_percentage", "percentage"),
}


class YouTubeProvider(BaseMetricsProvider):
    """Extracts YouTube organic metrics via YouTube Analytics API v2."""

    def provider_name(self) -> str:
        """Execute provider name operation."""
        return "youtube"

    def rate_limit_config(self) -> dict:
        """Execute rate limit config operation."""
        return {"requests_per_minute": 30, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract metrics."""
        if not credentials.get("token") and not credentials.get("refresh_token"):
            logger.warning("youtube_provider_no_credentials tenant=%s", tenant_id)
            return ExtractionResult()

        adapter = create_youtube_adapter(credentials_data=credentials)

        # Sub-extractor 1: Overview (core metrics)
        try:
            overview_metrics = await self._extract_overview(
                adapter,
                end_date,
                start_date,
                end_date,
            )
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "youtube_extract_metrics_auth_failure",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            msg = f"YouTube OAuth token revoked/expired: {exc}"
            raise ConnectionRevokedError(
                msg,
                channel_type="youtube",
            ) from exc

        # Sub-extractor 2: Card/End Screen metrics (isolated — fails silently)
        card_metrics, card_failure = await self._safe_extract(
            self._extract_card_metrics,
            adapter,
            end_date,
            start_date,
            end_date,
            extractor_name="youtube_cards",
        )

        all_metrics = overview_metrics + card_metrics
        failures = [card_failure] if card_failure else []

        return ExtractionResult(metrics=all_metrics, failures=failures)

    async def _extract_overview(
        self,
        adapter: YouTubeAnalyticsAdapter,
        metric_date: date,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract overview metrics: views, engagement, watch time, subs, comments, shares, avg_view_percentage."""
        overview = await asyncio.to_thread(
            adapter.get_channel_overview,
            start_date.isoformat(),
            end_date.isoformat(),
        )

        if not overview:
            return []

        metrics: list[ExtractedMetric] = []

        # Engagement (likes + dislikes) — special case with breakdown
        likes = float(overview.get("likes", 0))
        dislikes = float(overview.get("dislikes", 0))
        metrics.append(
            ExtractedMetric(
                provider="youtube",
                channel_slug="yt-organic",
                metric_name="engagement",
                value=likes + dislikes,
                unit="count",
                date=metric_date,
                extra={"likes": int(likes), "dislikes": int(dislikes)},
            ),
        )

        # Direct-mapped metrics
        for api_key, (metric_name, unit) in _DIRECT_MAP.items():
            value = float(overview.get(api_key, 0))
            if value or metric_name == "views":  # Always emit views even if 0
                metrics.append(
                    ExtractedMetric(
                        provider="youtube",
                        channel_slug="yt-organic",
                        metric_name=metric_name,
                        value=value,
                        unit=unit,
                        date=metric_date,
                    ),
                )

        return metrics

    async def _extract_card_metrics(
        self,
        adapter: YouTubeAnalyticsAdapter,
        metric_date: date,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract card and end screen metrics (isolated sub-extractor)."""
        card_data = await asyncio.to_thread(
            adapter.get_card_metrics,
            start_date.isoformat(),
            end_date.isoformat(),
        )

        if not card_data:
            return []

        metrics: list[ExtractedMetric] = []

        card_clicks = float(card_data.get("cardClicks", 0))
        card_impressions = float(card_data.get("cardImpressions", 0))
        end_clicks = float(card_data.get("endScreenElementClicks", 0))
        end_impressions = float(card_data.get("endScreenElementImpressions", 0))

        for metric_name, value in [
            ("card_clicks", card_clicks),
            ("card_impressions", card_impressions),
            ("end_screen_clicks", end_clicks),
            ("end_screen_impressions", end_impressions),
        ]:
            if value:
                metrics.append(
                    ExtractedMetric(
                        provider="youtube",
                        channel_slug="yt-organic",
                        metric_name=metric_name,
                        value=value,
                        unit="count",
                        date=metric_date,
                    ),
                )

        # Calculated rates (only if impressions > 0)
        if card_impressions > 0:
            metrics.append(
                ExtractedMetric(
                    provider="youtube",
                    channel_slug="yt-organic",
                    metric_name="card_click_rate",
                    value=round((card_clicks / card_impressions) * 100, 2),
                    unit="percentage",
                    date=metric_date,
                ),
            )

        if end_impressions > 0:
            metrics.append(
                ExtractedMetric(
                    provider="youtube",
                    channel_slug="yt-organic",
                    metric_name="end_screen_click_rate",
                    value=round((end_clicks / end_impressions) * 100, 2),
                    unit="percentage",
                    date=metric_date,
                ),
            )

        return metrics
