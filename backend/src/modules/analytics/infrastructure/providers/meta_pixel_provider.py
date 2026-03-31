"""MetaPixelProvider — extracts Meta Pixel event metrics.

Uses the Meta Marketing API pixel stats endpoint:
GET /{pixel_id}/stats?aggregation=event&event=PageView,ViewContent,Lead,AddToCart,Purchase
"""

import calendar
import logging
from datetime import date
from typing import List
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

# Meta Pixel event -> our metric name mapping
_EVENT_MAP = {
    "PageView": "pixel_pageviews",
    "ViewContent": "pixel_view_content",
    "Lead": "pixel_leads",
    "AddToCart": "pixel_add_to_cart",
    "Purchase": "pixel_purchases",
}


class MetaPixelProvider(BaseMetricsProvider):
    """Extracts Meta Pixel event counts via the Marketing API."""

    def provider_name(self) -> str:
        return "meta_pixel"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 30, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        pixel_id = credentials.get("asset_id")
        access_token = credentials.get("access_token")
        if not pixel_id or not access_token:
            logger.warning(
                "meta_pixel_no_credentials tenant=%s", tenant_id
            )
            return []

        try:
            start_unix = int(calendar.timegm(start_date.timetuple()))
            end_unix = int(calendar.timegm(end_date.timetuple())) + 86399  # end of day

            events = ",".join(_EVENT_MAP.keys())
            url = (
                f"https://graph.facebook.com/v21.0/{pixel_id}/stats"
                f"?aggregation=event&event={events}"
                f"&start_time={start_unix}&end_time={end_unix}"
                f"&access_token={access_token}"
            )

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            metrics: List[ExtractedMetric] = []
            for item in data.get("data", []):
                event_name = item.get("event")
                count = item.get("count", 0)
                metric_name = _EVENT_MAP.get(event_name)
                if metric_name:
                    metrics.append(
                        ExtractedMetric(
                            provider="meta_pixel",
                            channel_slug="meta-pixel",
                            metric_name=metric_name,
                            value=float(count),
                            unit="count",
                            date=end_date,
                        )
                    )

            return metrics
        except Exception:
            logger.exception(
                "meta_pixel_extract_failed tenant=%s", tenant_id
            )
            return []
