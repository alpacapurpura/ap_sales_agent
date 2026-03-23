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
from datetime import date, datetime, timedelta
from typing import List
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"


def _auth_headers(access_token: str) -> dict:
    """Build Authorization header — keeps token out of query params and logs."""
    return {"Authorization": f"Bearer {access_token}"}


def _raise_for_meta_error(response: httpx.Response, context: str) -> None:
    """Raise on HTTP errors with Meta-specific context in the log message."""
    if response.status_code >= 400:
        body = response.text[:500]
        logger.error(
            "meta_api_error context=%s status=%s body=%s",
            context, response.status_code, body,
        )
        response.raise_for_status()


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

        headers = _auth_headers(access_token)

        try:
            # Account-level reach (daily values summed)
            insights_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                headers=headers,
                params={
                    "metric": "reach",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(insights_resp, "ig_organic_reach")
            reach_data = insights_resp.json().get("data", [])
            total_reach = sum(
                v.get("value", 0)
                for item in reach_data
                for v in item.get("values", [])
            )

            # Per-media engagement breakdown
            media_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/media",
                headers=headers,
                params={
                    "fields": "like_count,comments_count,timestamp",
                    "limit": 100,
                },
            )
            _raise_for_meta_error(media_resp, "ig_organic_media")
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

        headers = _auth_headers(page_token)

        try:
            # Page reach (unique impressions)
            reach_resp = await client.get(
                f"{GRAPH_API_BASE}/{page_id}/insights",
                headers=headers,
                params={
                    "metric": "page_impressions_unique",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(reach_resp, "fb_organic_reach")
            reach_data = reach_resp.json().get("data", [])
            total_reach = sum(
                v.get("value", 0)
                for item in reach_data
                for v in item.get("values", [])
            )

            # Page post engagements
            engagement_resp = await client.get(
                f"{GRAPH_API_BASE}/{page_id}/insights",
                headers=headers,
                params={
                    "metric": "page_post_engagements",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(engagement_resp, "fb_organic_engagement")
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
        currency = credentials.get("currency", "USD")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)

        try:
            # Fetch adsets with targeting info to detect custom audiences
            adsets_resp = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/adsets",
                headers=headers,
                params={
                    "fields": "id,name,targeting,insights.time_range("
                    + json.dumps({"since": start_date.isoformat(), "until": end_date.isoformat()})
                    + "){reach,clicks,spend}",
                    "limit": 200,
                },
            )
            _raise_for_meta_error(adsets_resp, "meta_retargeting_adsets")
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
                    currency=currency,
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
        currency = credentials.get("currency", "USD")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)

        try:
            response = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
                headers=headers,
                params={
                    "fields": "reach,impressions,clicks,spend,frequency,ctr,cpm,actions",
                    "time_range": json.dumps(
                        {
                            "since": start_date.isoformat(),
                            "until": end_date.isoformat(),
                        }
                    ),
                    "level": "account",
                },
            )
            _raise_for_meta_error(response, "meta_ads_insights")
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
                    metric_name="impressions",
                    value=float(data.get("impressions", 0)),
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
                    metric_name="ctr",
                    value=float(data.get("ctr", 0)),
                    unit="percentage",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="cpm",
                    value=float(data.get("cpm", 0)),
                    unit="currency",
                    currency=currency,
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="frequency",
                    value=float(data.get("frequency", 0)),
                    unit="ratio",
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
                    currency=currency,
                    date=end_date,
                ),
            ]
        except Exception:
            logger.exception("meta_ads_extract_failed")
            return []

    # ── Daily extraction methods (for initial load / gap detection) ──

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Like extract_metrics() but returns per-day granularity.

        Uses time_increment=1 (Ads) or parses values[] per-day (Organic)
        to emit one ExtractedMetric per day instead of a single aggregated row.
        """
        access_token = credentials.get("access_token")
        if not access_token:
            logger.warning("meta_provider_no_access_token tenant=%s", tenant_id)
            return []

        metrics: List[ExtractedMetric] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stage == "nurturing":
                    retargeting = await self._extract_meta_retargeting_daily(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(retargeting)
                else:
                    ig = await self._extract_instagram_organic_daily(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(ig)

                    fb = await self._extract_facebook_organic_daily(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(fb)

                    ads = await self._extract_meta_ads_daily(
                        client, credentials, start_date, end_date
                    )
                    metrics.extend(ads)
        except Exception:
            logger.exception("meta_provider_extract_daily_failed tenant=%s", tenant_id)

        return metrics

    async def _extract_instagram_organic_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Parse IG insights values[] array to emit one reach metric per day."""
        access_token = credentials.get("access_token", "")
        ig_account_id = credentials.get("instagram_account_id")
        if not ig_account_id:
            return []

        headers = _auth_headers(access_token)
        try:
            insights_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                headers=headers,
                params={
                    "metric": "reach",
                    "period": "day",
                    "since": int(
                        datetime.combine(start_date, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(end_date, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(insights_resp, "ig_organic_reach_daily")
            reach_data = insights_resp.json().get("data", [])

            metrics: List[ExtractedMetric] = []
            for item in reach_data:
                for v in item.get("values", []):
                    end_time = v.get("end_time", "")
                    try:
                        metric_date = datetime.fromisoformat(
                            end_time.replace("Z", "+00:00")
                        ).date()
                    except (ValueError, AttributeError):
                        continue
                    metrics.append(
                        ExtractedMetric(
                            provider="meta",
                            channel_slug="ig-organic",
                            metric_name="reach",
                            value=float(v.get("value", 0)),
                            unit="count",
                            date=metric_date,
                        )
                    )

            # Engagement from media: no daily breakdown available — single metric
            media_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/media",
                headers=headers,
                params={
                    "fields": "like_count,comments_count,timestamp",
                    "limit": 100,
                },
            )
            _raise_for_meta_error(media_resp, "ig_organic_media_daily")
            media_items = media_resp.json().get("data", [])
            total_likes = sum(m.get("like_count", 0) for m in media_items)
            total_comments = sum(m.get("comments_count", 0) for m in media_items)

            metrics.append(
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
                        "shares": 0,
                        "saves": 0,
                    },
                )
            )
            return metrics
        except Exception:
            logger.exception("meta_instagram_organic_daily_failed")
            return []

    async def _extract_facebook_organic_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Parse FB insights values[] array to emit per-day metrics."""
        page_id = credentials.get("page_id")
        page_token = credentials.get("page_access_token", credentials.get("access_token", ""))
        if not page_id:
            return []

        headers = _auth_headers(page_token)
        metrics: List[ExtractedMetric] = []

        try:
            for metric_name, channel_metric in [
                ("page_impressions_unique", "reach"),
                ("page_post_engagements", "engagement"),
            ]:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/{page_id}/insights",
                    headers=headers,
                    params={
                        "metric": metric_name,
                        "period": "day",
                        "since": int(
                            datetime.combine(start_date, datetime.min.time()).timestamp()
                        ),
                        "until": int(
                            datetime.combine(end_date, datetime.min.time()).timestamp()
                        ),
                    },
                )
                _raise_for_meta_error(resp, f"fb_organic_{channel_metric}_daily")
                data = resp.json().get("data", [])

                for item in data:
                    for v in item.get("values", []):
                        end_time = v.get("end_time", "")
                        try:
                            metric_date = datetime.fromisoformat(
                                end_time.replace("Z", "+00:00")
                            ).date()
                        except (ValueError, AttributeError):
                            continue
                        metrics.append(
                            ExtractedMetric(
                                provider="meta",
                                channel_slug="fb-organic",
                                metric_name=channel_metric,
                                value=float(v.get("value", 0)),
                                unit="count",
                                date=metric_date,
                            )
                        )
            return metrics
        except Exception:
            logger.exception("meta_facebook_organic_daily_failed")
            return []

    async def _extract_meta_ads_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Use time_increment=1 to get per-day Ads breakdowns."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        currency = credentials.get("currency", "USD")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)
        try:
            response = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
                headers=headers,
                params={
                    "fields": "reach,impressions,clicks,spend,frequency,ctr,cpm,actions",
                    "time_range": json.dumps(
                        {
                            "since": start_date.isoformat(),
                            "until": end_date.isoformat(),
                        }
                    ),
                    "time_increment": "1",
                    "level": "account",
                },
            )
            _raise_for_meta_error(response, "meta_ads_insights_daily")
            rows = response.json().get("data", [])

            metrics: List[ExtractedMetric] = []
            for row in rows:
                date_str = row.get("date_start", "")
                try:
                    metric_date = date.fromisoformat(date_str)
                except (ValueError, AttributeError):
                    continue

                conversions = 0
                for action in row.get("actions", []):
                    if action.get("action_type") in (
                        "offsite_conversion.fb_pixel_purchase",
                        "onsite_conversion.purchase",
                    ):
                        conversions += int(action.get("value", 0))

                for name, value, unit, cur in [
                    ("reach", float(row.get("reach", 0)), "count", None),
                    ("impressions", float(row.get("impressions", 0)), "count", None),
                    ("clicks", float(row.get("clicks", 0)), "count", None),
                    ("ctr", float(row.get("ctr", 0)), "percentage", None),
                    ("cpm", float(row.get("cpm", 0)), "currency", currency),
                    ("frequency", float(row.get("frequency", 0)), "ratio", None),
                    ("conversions", float(conversions), "count", None),
                    ("spend", float(row.get("spend", 0)), "currency", currency),
                ]:
                    metrics.append(
                        ExtractedMetric(
                            provider="meta",
                            channel_slug="meta-ads",
                            metric_name=name,
                            value=value,
                            unit=unit,
                            currency=cur,
                            date=metric_date,
                        )
                    )
            return metrics
        except Exception:
            logger.exception("meta_ads_daily_extract_failed")
            return []

    async def _extract_meta_retargeting_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Iterate day by day calling _extract_meta_retargeting for each day."""
        metrics: List[ExtractedMetric] = []
        current = start_date
        while current <= end_date:
            day_metrics = await self._extract_meta_retargeting(
                client, credentials, current, current
            )
            # Override date to match the actual day (original uses end_date)
            for m in day_metrics:
                m.date = current
            metrics.extend(day_metrics)
            current += timedelta(days=1)
        return metrics
