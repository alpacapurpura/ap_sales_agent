"""YouTubeProvider — extracts YouTube organic channel metrics.

Channel slug: yt-organic
Metrics: reach (views) + engagement (likes + dislikes)

Uses existing YouTubeAnalyticsAdapter.get_channel_overview() wrapped
in asyncio.to_thread() (sync Google SDK).
"""

import asyncio
import logging
from datetime import date
from typing import List
from uuid import UUID

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.youtube_analytics import (
    YouTubeAnalyticsAdapter,
)

logger = logging.getLogger(__name__)


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
    ) -> List[ExtractedMetric]:
        if not credentials.get("token") and not credentials.get("refresh_token"):
            logger.warning(
                "youtube_provider_no_credentials tenant=%s", tenant_id
            )
            return []

        try:
            adapter = YouTubeAnalyticsAdapter(credentials_data=credentials)

            overview = await asyncio.to_thread(
                adapter.get_channel_overview,
                start_date.isoformat(),
                end_date.isoformat(),
            )

            if not overview:
                return []

            views = float(overview.get("views", 0))
            likes = float(overview.get("likes", 0))
            dislikes = float(overview.get("dislikes", 0))
            total_engagement = likes + dislikes

            return [
                ExtractedMetric(
                    provider="youtube",
                    channel_slug="yt-organic",
                    metric_name="reach",
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
        except Exception:
            logger.exception(
                "youtube_provider_extract_failed tenant=%s", tenant_id
            )
            return []
