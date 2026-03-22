"""MetaProvider — extracts metrics from Meta Graph API.

Covers three channel slugs:
- ig-organic: Instagram organic reach + engagement
- fb-organic: Facebook page organic reach + engagement
- meta-ads: Meta Ads account reach, clicks, conversions, spend

Uses httpx async client (NOT FacebookAdsApi.init() singleton).
Per Phase 1 decision: per-instance API pattern for tenant isolation.
"""

import json
import logging
from datetime import date, datetime
from typing import List
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"


class MetaProvider(BaseMetricsProvider):
    """Extracts metrics from Meta Graph API for Instagram organic,
    Facebook organic, and Meta Ads."""

    def provider_name(self) -> str:
        return "meta"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 200, "burst_size": 50}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        access_token = credentials.get("access_token")
        if not access_token:
            logger.warning("meta_provider_no_access_token tenant=%s", tenant_id)
            return []

        metrics: List[ExtractedMetric] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stage == "nurturing":
                    # Retargeting: only Meta Ads filtered to custom audiences
                    retargeting_metrics = await self._extract_meta_retargeting(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(retargeting_metrics)
                else:
                    # Standard attraction-stage extraction
                    # Instagram organic
                    ig_metrics = await self._extract_instagram_organic(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(ig_metrics)

                    # Facebook page organic
                    fb_metrics = await self._extract_facebook_organic(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(fb_metrics)

                    # Meta Ads
                    ads_metrics = await self._extract_meta_ads(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(ads_metrics)
        except Exception:
            logger.exception("meta_provider_extract_failed tenant=%s", tenant_id)

        return metrics

    async def _extract_instagram_organic(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Instagram organic reach and engagement."""
        access_token = credentials.get("access_token", "")
        ig_account_id = credentials.get("instagram_account_id")
        if not ig_account_id:
            return []

        try:
            # Account-level reach (daily values summed)
            insights_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                params={
                    "metric": "reach",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                    "access_token": access_token,
                },
            )
            reach_data = insights_resp.json().get("data", [])
            total_reach = sum(
                v.get("value", 0)
                for item in reach_data
                for v in item.get("values", [])
            )

            # Per-media engagement breakdown
            media_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/media",
                params={
                    "fields": "like_count,comments_count,timestamp",
                    "limit": 100,
                    "access_token": access_token,
                },
            )
            media_items = media_resp.json().get("data", [])
            total_likes = sum(m.get("like_count", 0) for m in media_items)
            total_comments = sum(m.get("comments_count", 0) for m in media_items)

            return [
                ExtractedMetric(
                    provider="meta",
                    channel_slug="ig-organic",
                    metric_name="reach",
                    value=float(total_reach),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="ig-organic",
                    metric_name="engagement",
                    value=float(total_likes + total_comments),
                    unit="count",
                    date=end_date,
                    extra={
                        "likes": total_likes,
                        "comments": total_comments,
                        "shares": 0,  # Not available via current API
                        "saves": 0,   # Not available via current API
                    },
                ),
            ]
        except Exception:
            logger.exception("meta_instagram_organic_failed")
            return []

    async def _extract_facebook_organic(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Facebook page organic reach and engagement."""
        page_id = credentials.get("page_id")
        page_token = credentials.get("page_access_token", credentials.get("access_token", ""))
        if not page_id:
            return []

        try:
            # Page reach (unique impressions)
            reach_resp = await client.get(
                f"{GRAPH_API_BASE}/{page_id}/insights",
                params={
                    "metric": "page_impressions_unique",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                    "access_token": page_token,
                },
            )
            reach_data = reach_resp.json().get("data", [])
            total_reach = sum(
                v.get("value", 0)
                for item in reach_data
                for v in item.get("values", [])
            )

            # Page post engagements
            engagement_resp = await client.get(
                f"{GRAPH_API_BASE}/{page_id}/insights",
                params={
                    "metric": "page_post_engagements",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                    "access_token": page_token,
                },
            )
            engagement_data = engagement_resp.json().get("data", [])
            total_engagement = sum(
                v.get("value", 0)
                for item in engagement_data
                for v in item.get("values", [])
            )

            return [
                ExtractedMetric(
                    provider="meta",
                    channel_slug="fb-organic",
                    metric_name="reach",
                    value=float(total_reach),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="fb-organic",
                    metric_name="engagement",
                    value=float(total_engagement),
                    unit="count",
                    date=end_date,
                ),
            ]
        except Exception:
            logger.exception("meta_facebook_organic_failed")
            return []

    async def _extract_meta_retargeting(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Meta Ads retargeting metrics (adsets with custom_audiences).

        Filters to adsets that target custom audiences (audience-first classification
        per CONTEXT.md). Uses channel_slug 'meta-retargeting'. Only extracts reach,
        clicks, spend (no conversions -- those belong in Stage 3).

        NOTE: targeting.custom_audiences lives on adsets, not campaigns (Meta API pitfall).
        """
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        try:
            # Fetch adsets with targeting info to detect custom audiences
            adsets_resp = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/adsets",
                params={
                    "fields": "id,name,targeting,insights.time_range("
                    + json.dumps({"since": start_date.isoformat(), "until": end_date.isoformat()})
                    + "){reach,clicks,spend}",
                    "limit": 200,
                    "access_token": access_token,
                },
            )
            adsets = adsets_resp.json().get("data", [])

            total_reach = 0.0
            total_clicks = 0.0
            total_spend = 0.0

            for adset in adsets:
                targeting = adset.get("targeting", {})
                custom_audiences = targeting.get("custom_audiences", [])
                if not custom_audiences:
                    continue  # Skip non-retargeting adsets

                insights = adset.get("insights", {}).get("data", [{}])
                if insights:
                    data = insights[0]
                    total_reach += float(data.get("reach", 0))
                    total_clicks += float(data.get("clicks", 0))
                    total_spend += float(data.get("spend", 0))

            return [
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-retargeting",
                    metric_name="reach",
                    value=total_reach,
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-retargeting",
                    metric_name="clicks",
                    value=total_clicks,
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-retargeting",
                    metric_name="spend",
                    value=total_spend,
                    unit="currency",
                    currency="USD",
                    date=end_date,
                ),
            ]
        except Exception:
            logger.exception("meta_retargeting_extract_failed")
            return []

    async def _extract_meta_ads(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Meta Ads account-level metrics."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        try:
            response = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
                params={
                    "fields": "reach,clicks,spend,actions",
                    "time_range": json.dumps(
                        {
                            "since": start_date.isoformat(),
                            "until": end_date.isoformat(),
                        }
                    ),
                    "level": "account",
                    "access_token": access_token,
                },
            )
            data = response.json().get("data", [{}])[0]

            # Extract conversions from actions array
            conversions = 0
            for action in data.get("actions", []):
                if action.get("action_type") in (
                    "offsite_conversion.fb_pixel_purchase",
                    "onsite_conversion.purchase",
                ):
                    conversions += int(action.get("value", 0))

            return [
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="reach",
                    value=float(data.get("reach", 0)),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="clicks",
                    value=float(data.get("clicks", 0)),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="conversions",
                    value=float(conversions),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="spend",
                    value=float(data.get("spend", 0)),
                    unit="currency",
                    currency="USD",
                    date=end_date,
                ),
            ]
        except Exception:
            logger.exception("meta_ads_extract_failed")
            return []
