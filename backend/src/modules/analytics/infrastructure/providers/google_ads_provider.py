"""GoogleAdsProvider — extracts Google Ads and YouTube Ads metrics.

Separates campaigns by advertising_channel_type:
- VIDEO campaigns -> yt-ads channel slug
- All other campaigns (SEARCH, DISPLAY, etc.) -> google-ads channel slug

CRITICAL: cost_micros must be divided by 1_000_000 for actual currency value.

Uses GoogleAdsAdapter.run_gaql_query() wrapped in asyncio.to_thread()
(sync Google Ads SDK).
"""

import os

import sentry_sdk
import structlog
from collections import defaultdict
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

logger = structlog.get_logger(__name__)

GAQL_CAMPAIGN_METRICS = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.advertising_channel_type,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions_value
    FROM campaign
    WHERE segments.date BETWEEN '{start}' AND '{end}'
        AND campaign.status = 'ENABLED'
"""

GAQL_CAMPAIGN_METRICS_DAILY = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.advertising_channel_type,
        segments.date,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions_value
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

            base_metrics = self._aggregate_by_channel(rows, end_date)
            search_term_metrics = await self._extract_search_terms(
                adapter, customer_id, developer_token, credentials, start_date, end_date
            )
            return base_metrics + search_term_metrics
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception(
                "google_ads_provider_extract_failed tenant=%s", tenant_id
            )
            return []

    async def _extract_search_terms(
        self,
        adapter: GoogleAdsAdapter,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract top search terms as a JSON snapshot metric."""
        try:
            search_terms = await adapter.run_search_terms_query(
                customer_id=customer_id,
                developer_token=developer_token,
                credentials=credentials,
                start_date=start_date,
                end_date=end_date,
            )
            if not search_terms:
                return []

            terms_list = [
                {
                    "term": r["search_term"],
                    "impressions": int(r["impressions"]),
                    "clicks": int(r["clicks"]),
                }
                for r in search_terms[:20]
            ]
            return [
                ExtractedMetric(
                    provider="google_ads",
                    channel_slug="google-ads",
                    metric_name="search_terms",
                    value=0.0,
                    unit="json",
                    date=end_date,
                    extra={"terms": terms_list},
                )
            ]
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("google_ads_search_terms_extract_failed")
            return []

    def _aggregate_retargeting(
        self, rows: List[dict], metric_date: date
    ) -> List[ExtractedMetric]:
        """Aggregate remarketing campaign rows into google-retargeting slug.

        Filters campaigns with 'remarketing' or 'retargeting' in name.
        """
        total_impressions = 0.0
        total_clicks = 0.0
        total_spend = 0.0

        for row in rows:
            campaign_name = (row.get("campaign_name", "") or "").lower()
            if "remarketing" in campaign_name or "retargeting" in campaign_name:
                total_impressions += float(row.get("impressions", 0))
                total_clicks += float(row.get("clicks", 0))
                total_spend += float(row.get("cost_micros", 0)) / 1_000_000

        if total_impressions == 0.0 and total_clicks == 0.0 and total_spend == 0.0:
            return []

        # Compute derived metrics
        ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0

        metric_tuples = [
            ("impressions", total_impressions, "count", None),
            ("clicks", total_clicks, "count", None),
            ("spend", total_spend, "currency", "USD"),
            ("ctr", ctr, "percentage", None),
            ("cpc", cpc, "currency", "USD"),
        ]

        return [
            ExtractedMetric(
                provider="google_ads",
                channel_slug="google-retargeting",
                metric_name=name,
                value=value,
                unit=unit,
                currency=currency,
                date=metric_date,
            )
            for name, value, unit, currency in metric_tuples
        ]

    def _aggregate_by_channel(
        self, rows: List[dict], metric_date: date
    ) -> List[ExtractedMetric]:
        """Aggregate campaign rows into google-ads and yt-ads slugs."""
        channel_data: Dict[str, Dict[str, float]] = {
            "google-ads": {
                "impressions": 0.0, "clicks": 0.0, "conversions": 0.0,
                "spend": 0.0, "conversion_value": 0.0,
            },
            "yt-ads": {
                "impressions": 0.0, "clicks": 0.0, "conversions": 0.0,
                "spend": 0.0, "conversion_value": 0.0,
            },
        }

        for row in rows:
            channel_type = row.get("advertising_channel_type", "")
            slug = "yt-ads" if channel_type == "VIDEO" else "google-ads"

            channel_data[slug]["impressions"] += float(row.get("impressions", 0))
            channel_data[slug]["clicks"] += float(row.get("clicks", 0))
            channel_data[slug]["conversions"] += float(row.get("conversions", 0))
            # CRITICAL: divide cost_micros by 1_000_000
            channel_data[slug]["spend"] += float(row.get("cost_micros", 0)) / 1_000_000
            channel_data[slug]["conversion_value"] += float(
                row.get("conversions_value", 0)
            )

        metrics: List[ExtractedMetric] = []
        for slug, data in channel_data.items():
            # Skip slugs with zero activity
            if all(v == 0.0 for v in data.values()):
                continue

            # Compute derived metrics from aggregated totals
            impressions = data["impressions"]
            clicks = data["clicks"]
            ctr = (clicks / impressions) if impressions > 0 else 0.0
            cpc = (data["spend"] / clicks) if clicks > 0 else 0.0

            metric_tuples = [
                ("impressions", data["impressions"], "count", None),
                ("clicks", data["clicks"], "count", None),
                ("conversions", data["conversions"], "count", None),
                ("spend", data["spend"], "currency", "USD"),
                ("ctr", ctr, "percentage", None),
                ("cpc", cpc, "currency", "USD"),
                ("conversion_value", data["conversion_value"], "currency", "USD"),
            ]

            for metric_name, value, unit, currency in metric_tuples:
                metrics.append(
                    ExtractedMetric(
                        provider="google_ads",
                        channel_slug=slug,
                        metric_name=metric_name,
                        value=value,
                        unit=unit,
                        currency=currency,
                        date=metric_date,
                    )
                )

        return metrics

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Optimized daily extraction — GAQL with segments.date."""
        customer_id = credentials.get("customer_id")
        developer_token = credentials.get(
            "developer_token",
            os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        )

        if not customer_id or not developer_token:
            return []

        try:
            adapter = GoogleAdsAdapter()
            rows = await adapter.run_gaql_query(
                customer_id=customer_id,
                developer_token=developer_token,
                credentials=credentials,
                query=GAQL_CAMPAIGN_METRICS_DAILY,
                start_date=start_date,
                end_date=end_date,
            )

            if not rows:
                return []

            # Group rows by date, then aggregate
            by_date: Dict[str, List[dict]] = defaultdict(list)
            for row in rows:
                date_str = row.get("segments_date", row.get("date", ""))
                by_date[date_str].append(row)

            metrics: List[ExtractedMetric] = []
            for date_str, day_rows in by_date.items():
                try:
                    metric_date = date.fromisoformat(date_str)
                except (ValueError, AttributeError):
                    continue

                if stage == "nurturing":
                    metrics.extend(
                        self._aggregate_retargeting(day_rows, metric_date)
                    )
                else:
                    metrics.extend(
                        self._aggregate_by_channel(day_rows, metric_date)
                    )

            return metrics
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception(
                "google_ads_provider_extract_daily_failed tenant=%s", tenant_id
            )
            return []
