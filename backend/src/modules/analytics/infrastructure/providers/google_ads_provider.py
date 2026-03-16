"""GoogleAdsProvider — extracts Google Ads and YouTube Ads metrics.

Separates campaigns by advertising_channel_type:
- VIDEO campaigns -> yt-ads channel slug
- All other campaigns (SEARCH, DISPLAY, etc.) -> google-ads channel slug

CRITICAL: cost_micros must be divided by 1_000_000 for actual currency value.

Uses GoogleAdsAdapter.run_gaql_query() wrapped in asyncio.to_thread()
(sync Google Ads SDK).
"""

import logging
import os
from datetime import date
from typing import Dict, List
from uuid import UUID

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.google_ads import (
    GoogleAdsAdapter,
)

logger = logging.getLogger(__name__)

GAQL_CAMPAIGN_METRICS = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.advertising_channel_type,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros
    FROM campaign
    WHERE segments.date BETWEEN '{start}' AND '{end}'
        AND campaign.status = 'ENABLED'
"""


class GoogleAdsProvider(BaseMetricsProvider):
    """Extracts metrics from Google Ads API, separating YouTube Ads
    (VIDEO campaigns) from Search/Display campaigns."""

    def provider_name(self) -> str:
        return "google_ads"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 100, "burst_size": 20}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        customer_id = credentials.get("customer_id")
        developer_token = credentials.get(
            "developer_token",
            os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        )

        if not customer_id or not developer_token:
            logger.warning(
                "google_ads_provider_missing_credentials tenant=%s "
                "customer_id=%s dev_token=%s",
                tenant_id,
                bool(customer_id),
                bool(developer_token),
            )
            return []

        try:
            adapter = GoogleAdsAdapter()
            rows = await adapter.run_gaql_query(
                customer_id=customer_id,
                developer_token=developer_token,
                credentials=credentials,
                query=GAQL_CAMPAIGN_METRICS,
                start_date=start_date,
                end_date=end_date,
            )

            if not rows:
                return []

            if stage == "nurturing":
                return self._aggregate_retargeting(rows, end_date)

            return self._aggregate_by_channel(rows, end_date)
        except Exception:
            logger.exception(
                "google_ads_provider_extract_failed tenant=%s", tenant_id
            )
            return []

    def _aggregate_retargeting(
        self, rows: List[dict], metric_date: date
    ) -> List[ExtractedMetric]:
        """Aggregate remarketing campaign rows into google-retargeting slug.

        TODO: Google Ads remarketing detection differs from Meta -- uses UserList
        criterion at ad group level. Current implementation is best-effort: filters
        campaigns with 'remarketing' or 'retargeting' in name. Full ad_group_criterion
        filtering requires additional GAQL query with ad_group_criterion.type = USER_LIST.
        """
        data = {"reach": 0.0, "clicks": 0.0, "spend": 0.0}

        for row in rows:
            campaign_name = (row.get("campaign_name", "") or "").lower()
            if "remarketing" in campaign_name or "retargeting" in campaign_name:
                data["reach"] += float(row.get("impressions", 0))
                data["clicks"] += float(row.get("clicks", 0))
                data["spend"] += float(row.get("cost_micros", 0)) / 1_000_000

        if all(v == 0.0 for v in data.values()):
            return []

        return [
            ExtractedMetric(
                provider="google_ads",
                channel_slug="google-retargeting",
                metric_name=metric_name,
                value=value,
                unit="currency" if metric_name == "spend" else "count",
                currency="USD" if metric_name == "spend" else None,
                date=metric_date,
            )
            for metric_name, value in data.items()
        ]

    def _aggregate_by_channel(
        self, rows: List[dict], metric_date: date
    ) -> List[ExtractedMetric]:
        """Aggregate campaign rows into google-ads and yt-ads slugs."""
        channel_data: Dict[str, Dict[str, float]] = {
            "google-ads": {"reach": 0.0, "clicks": 0.0, "conversions": 0.0, "spend": 0.0},
            "yt-ads": {"reach": 0.0, "clicks": 0.0, "conversions": 0.0, "spend": 0.0},
        }

        for row in rows:
            channel_type = row.get("advertising_channel_type", "")
            slug = "yt-ads" if channel_type == "VIDEO" else "google-ads"

            channel_data[slug]["reach"] += float(row.get("impressions", 0))
            channel_data[slug]["clicks"] += float(row.get("clicks", 0))
            channel_data[slug]["conversions"] += float(row.get("conversions", 0))
            # CRITICAL: divide cost_micros by 1_000_000
            channel_data[slug]["spend"] += float(row.get("cost_micros", 0)) / 1_000_000

        metrics: List[ExtractedMetric] = []
        for slug, data in channel_data.items():
            # Skip slugs with zero activity
            if all(v == 0.0 for v in data.values()):
                continue
            for metric_name, value in data.items():
                metrics.append(
                    ExtractedMetric(
                        provider="google_ads",
                        channel_slug=slug,
                        metric_name=metric_name,
                        value=value,
                        unit="currency" if metric_name == "spend" else "count",
                        currency="USD" if metric_name == "spend" else None,
                        date=metric_date,
                    )
                )

        return metrics
