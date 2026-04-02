"""YouTubeProvider — extracts YouTube organic channel metrics.

Channel slug: yt-organic
Metrics: reach (views) + engagement (likes + dislikes)

Uses existing YouTubeAnalyticsAdapter.get_channel_overview() wrapped
in asyncio.to_thread() (sync Google SDK).
"""

import asyncio

import structlog
from datetime import date
from uuid import UUID

from google.auth.exceptions import RefreshError, TransportError

from src.modules.analytics.domain.exceptions import ConnectionRevokedException
from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.youtube_analytics import (
    YouTubeAnalyticsAdapter,
)

logger = structlog.get_logger(__name__)


class YouTubeProvider(BaseMetricsProvider):
    """Extracts YouTube organic metrics via YouTube Analytics API v2."""

    def provider_name(self) -> str:
        return "youtube"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 30, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        if not credentials.get("token") and not credentials.get("refresh_token"):
            logger.warning(
                "youtube_provider_no_credentials tenant=%s", tenant_id
            )
            return ExtractionResult()

        adapter = YouTubeAnalyticsAdapter(credentials_data=credentials)

        try:
            overview = await asyncio.to_thread(
                adapter.get_channel_overview,
                start_date.isoformat(),
                end_date.isoformat(),
            )
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "youtube_extract_metrics_auth_failure",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            raise ConnectionRevokedException(
                f"YouTube OAuth token revoked/expired: {exc}",
                channel_type="youtube",
            ) from exc

        if not overview:
            return ExtractionResult()

        views = float(overview.get("views", 0))
        likes = float(overview.get("likes", 0))
        dislikes = float(overview.get("dislikes", 0))
        total_engagement = likes + dislikes

        metrics: list = [
            ExtractedMetric(
                provider="youtube",
                channel_slug="yt-organic",
                metric_name="views",
                value=views,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="youtube",
                channel_slug="yt-organic",
                metric_name="engagement",
                value=total_engagement,
                unit="count",
                date=end_date,
                extra={
                    "likes": int(likes),
                    "dislikes": int(dislikes),
                },
            ),
        ]

        watch_time = float(overview.get("estimatedMinutesWatched", 0))
        if watch_time:
            metrics.append(ExtractedMetric(
                provider="youtube",
                channel_slug="yt-organic",
                metric_name="watch_time_minutes",
                value=watch_time,
                unit="count",
                date=end_date,
            ))

        avg_duration = float(overview.get("averageViewDuration", 0))
        if avg_duration:
            metrics.append(ExtractedMetric(
                provider="youtube",
                channel_slug="yt-organic",
                metric_name="avg_view_duration",
                value=avg_duration,
                unit="seconds",
                date=end_date,
            ))

        subs_gained = float(overview.get("subscribersGained", 0))
        metrics.append(ExtractedMetric(
            provider="youtube",
            channel_slug="yt-organic",
            metric_name="subscribers_gained",
            value=subs_gained,
            unit="count",
            date=end_date,
        ))

        return ExtractionResult(metrics=metrics)
