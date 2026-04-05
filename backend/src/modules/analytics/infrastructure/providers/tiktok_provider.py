"""TikTokProvider — extracts TikTok organic and ads metrics.

Channel slugs:
- tiktok-organic: video_views (as reach) + engagement (likes + comments + shares)
- tiktok-ads: reach, clicks, conversions, spend

Uses TikTokAdapter for API calls. Gracefully handles missing credentials.
"""

from datetime import date
from uuid import UUID

import structlog

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.tiktok import TikTokAdapter

logger = structlog.get_logger(__name__)


class TikTokProvider(BaseMetricsProvider):
    """Extracts metrics from TikTok Business API for organic
    and paid channels."""

    def provider_name(self) -> str:
        return "tiktok"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 60, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        access_token = credentials.get("access_token")
        if not access_token:
            logger.warning("tiktok_provider_no_access_token tenant=%s", tenant_id)
            return ExtractionResult()

        adapter = TikTokAdapter()
        metrics: list[ExtractedMetric] = []
        failures = []

        if stage == "nurturing":
            # Retargeting: only ads filtered to custom audiences
            advertiser_id = credentials.get("advertiser_id")
            if advertiser_id:
                m, fail = await self._safe_extract(
                    self._extract_retargeting,
                    adapter,
                    access_token,
                    advertiser_id,
                    start_date,
                    end_date,
                    extractor_name="tiktok_retargeting",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)
        else:
            # Standard attraction-stage extraction
            # Organic metrics
            m, fail = await self._safe_extract(
                self._extract_organic,
                adapter,
                access_token,
                start_date,
                end_date,
                extractor_name="tiktok_organic",
            )
            metrics.extend(m)
            if fail:
                failures.append(fail)

            # Ads metrics
            advertiser_id = credentials.get("advertiser_id")
            if advertiser_id:
                m, fail = await self._safe_extract(
                    self._extract_ads,
                    adapter,
                    access_token,
                    advertiser_id,
                    start_date,
                    end_date,
                    extractor_name="tiktok_ads",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

    async def _extract_retargeting(
        self,
        adapter: TikTokAdapter,
        access_token: str,
        advertiser_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract TikTok Ads retargeting metrics (Custom Audience campaigns).

        TODO: TikTok Ads API audience_type filtering requires additional API call
        to /audience/list to identify Custom Audience IDs, then filter ad groups.
        Current implementation is best-effort: uses standard ads report and
        filters by campaign name containing 'retargeting' or 'remarketing'.
        """
        data = await adapter.get_ads_report(
            access_token, advertiser_id, start_date, end_date
        )
        if not data:
            return []

        total_reach = 0.0
        total_clicks = 0.0
        total_spend = 0.0

        for row in data:
            # Best-effort retargeting detection by campaign name
            campaign_name = (
                row.get("dimensions", {}).get("campaign_name", "") or ""
            ).lower()
            if (
                "retargeting" not in campaign_name
                and "remarketing" not in campaign_name
            ):
                continue
            row_metrics = row.get("metrics", {})
            total_reach += float(row_metrics.get("reach", 0))
            total_clicks += float(row_metrics.get("clicks", 0))
            total_spend += float(row_metrics.get("spend", 0))

        if total_reach == 0.0 and total_clicks == 0.0 and total_spend == 0.0:
            return []

        return [
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-retargeting",
                metric_name="reach",
                value=total_reach,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-retargeting",
                metric_name="clicks",
                value=total_clicks,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-retargeting",
                metric_name="spend",
                value=total_spend,
                unit="currency",
                date=end_date,
            ),
        ]

    async def _extract_organic(
        self,
        adapter: TikTokAdapter,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract TikTok organic reach and engagement."""
        data = await adapter.get_organic_insights(access_token, start_date, end_date)
        if not data:
            return []

        # Aggregate across all entries
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0

        for entry in data:
            total_views += int(entry.get("video_views", 0))
            total_likes += int(entry.get("likes", 0))
            total_comments += int(entry.get("comments", 0))
            total_shares += int(entry.get("shares", 0))

        total_engagement = total_likes + total_comments + total_shares

        return [
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-organic",
                metric_name="video_views",
                value=float(total_views),
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-organic",
                metric_name="engagement",
                value=float(total_engagement),
                unit="count",
                date=end_date,
                extra={
                    "likes": total_likes,
                    "comments": total_comments,
                    "shares": total_shares,
                },
            ),
        ]

    async def _extract_ads(
        self,
        adapter: TikTokAdapter,
        access_token: str,
        advertiser_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract TikTok Ads metrics."""
        data = await adapter.get_ads_report(
            access_token, advertiser_id, start_date, end_date
        )
        if not data:
            return []

        # Aggregate across all report rows
        total_reach = 0.0
        total_clicks = 0.0
        total_conversions = 0.0
        total_spend = 0.0

        for row in data:
            row_metrics = row.get("metrics", {})
            total_reach += float(row_metrics.get("reach", 0))
            total_clicks += float(row_metrics.get("clicks", 0))
            total_conversions += float(row_metrics.get("conversion", 0))
            total_spend += float(row_metrics.get("spend", 0))

        return [
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-ads",
                metric_name="reach",
                value=total_reach,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-ads",
                metric_name="clicks",
                value=total_clicks,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-ads",
                metric_name="conversions",
                value=total_conversions,
                unit="count",
                date=end_date,
            ),
            ExtractedMetric(
                provider="tiktok",
                channel_slug="tiktok-ads",
                metric_name="spend",
                value=total_spend,
                unit="currency",
                date=end_date,
            ),
        ]
