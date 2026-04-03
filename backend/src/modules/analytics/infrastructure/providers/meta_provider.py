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
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
from uuid import UUID

import httpx

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"

_META_ACTION_MAP = {
    "offsite_conversion.fb_pixel_purchase": "conversions",
    "onsite_conversion.purchase": "conversions",
    "offsite_conversion.fb_pixel_lead": "meta_leads",
    "lead": "meta_leads",
    "offsite_conversion.fb_pixel_add_to_cart": "meta_add_to_cart",
    "offsite_conversion.fb_pixel_initiate_checkout": "meta_initiate_checkout",
    "offsite_conversion.fb_pixel_complete_registration": "meta_registrations",
    "offsite_conversion.fb_pixel_view_content": "meta_view_content",
    "offsite_conversion.fb_pixel_search": "meta_search_actions",
    "landing_page_view": "meta_landing_page_views",
    "onsite_conversion.messaging_conversation_started_7d": "meta_conversations_started",
    "link_click": "meta_link_clicks",
    "post_engagement": "meta_post_engagement",
    "page_engagement": "meta_page_engagement",
    "video_view": "meta_video_views",
}

_ADS_EXPANDED_FIELDS = (
    "reach,impressions,clicks,spend,frequency,ctr,cpm,cpc,cpp,actions,"
    "action_values,cost_per_action_type,inline_link_clicks,outbound_clicks,"
    "inline_post_engagement,purchase_roas,"
    "video_p25_watched_actions,video_p50_watched_actions,"
    "video_p75_watched_actions,video_p100_watched_actions,"
    "video_30_sec_watched_actions,video_avg_time_watched_actions,"
    "cost_per_inline_link_click,cost_per_outbound_click"
)


_IG_INSIGHTS_MAX_DAYS = 30  # Meta enforces ≤30 days for period=day


def _ig_day_chunks(start_date: date, end_date: date):
    """Yield (chunk_start, chunk_end) pairs of at most 30 days."""
    cursor = start_date
    while cursor < end_date:
        chunk_end = min(cursor + timedelta(days=_IG_INSIGHTS_MAX_DAYS), end_date)
        yield cursor, chunk_end
        cursor = chunk_end


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

    def has_period_extraction(self) -> bool:
        return True

    async def extract_period_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        period_type: str,
        period_start: date,
        period_end: date,
        metric_names: list[str],
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract NON_AGGREGABLE metrics for an entire period.

        IG Organic: uses `period=week` for weekly, `period=days_28` for monthly.
        Meta Ads: uses `time_range` with exact date boundaries for all periods.
        """
        access_token = credentials.get("access_token")
        if not access_token:
            return ExtractionResult()

        all_metrics: list[ExtractedMetric] = []
        all_failures = []

        ig_user_id = (
            credentials.get("instagram_business_account_id")
            or credentials.get("tracked_ig_id")
            or credentials.get("instagram_account_id")
        )
        ad_account_id = credentials.get("ad_account_id")

        # ── IG Organic period extraction ──
        if ig_user_id and any(m in metric_names for m in ("reach", "ig_accounts_engaged")):
            ig_metrics, ig_fail = await self._safe_extract(
                self._extract_ig_organic_period,
                access_token, ig_user_id, period_type, period_start, period_end,
                extractor_name="ig_organic_period",
            )
            all_metrics.extend(ig_metrics)
            if ig_fail:
                all_failures.append(ig_fail)

        # ── Meta Ads period extraction ──
        if ad_account_id and any(m in metric_names for m in ("reach", "frequency")):
            ads_metrics, ads_fail = await self._safe_extract(
                self._extract_meta_ads_period,
                access_token, ad_account_id, period_start, period_end,
                extractor_name="meta_ads_period",
            )
            all_metrics.extend(ads_metrics)
            if ads_fail:
                all_failures.append(ads_fail)

        return ExtractionResult(metrics=all_metrics, failures=all_failures)

    async def _extract_ig_organic_period(
        self,
        access_token: str,
        ig_user_id: str,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> list[ExtractedMetric]:
        """Extract IG organic reach/engaged for a period using Meta period param."""
        metrics = []
        since_ts = int(datetime.combine(period_start, datetime.min.time()).timestamp())
        until_ts = int(datetime.combine(period_end + timedelta(days=1), datetime.min.time()).timestamp())

        if period_type == "weekly":
            meta_period = "week"
        elif period_type in ("monthly", "last_30_days"):
            meta_period = "days_28"
        else:
            # quarterly: use days_28 as approximation
            meta_period = "days_28"

        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{GRAPH_API_BASE}/{ig_user_id}/insights"
            params = {
                "metric": "reach,accounts_engaged",
                "metric_type": "total_value",
                "period": meta_period,
                "since": since_ts,
                "until": until_ts,
            }
            resp = await client.get(url, headers=_auth_headers(access_token), params=params)
            _raise_for_meta_error(resp, f"ig_organic_period_{period_type}")

            data = resp.json().get("data", [])
            for item in data:
                name = item.get("name", "")
                metric_name = "ig_accounts_engaged" if name == "accounts_engaged" else name
                # metric_type=total_value → {total_value: {value: N}}
                val = item.get("total_value", {}).get("value")
                if val is None:
                    # Fallback for legacy format
                    values = item.get("values", [])
                    val = values[-1].get("value", 0) if values else 0
                if val:
                    metrics.append(ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=float(val),
                        unit="count",
                        date=period_start,
                        extra={"period_type": period_type, "meta_period": meta_period},
                    ))

        return metrics

    async def _extract_meta_ads_period(
        self,
        access_token: str,
        ad_account_id: str,
        period_start: date,
        period_end: date,
    ) -> list[ExtractedMetric]:
        """Extract Meta Ads reach/frequency for an exact date range."""
        metrics = []
        time_range = json.dumps({
            "since": period_start.isoformat(),
            "until": period_end.isoformat(),
        })

        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{GRAPH_API_BASE}/act_{ad_account_id}/insights"
            params = {
                "fields": "reach,impressions,frequency",
                "time_range": time_range,
            }
            resp = await client.get(url, headers=_auth_headers(access_token), params=params)
            _raise_for_meta_error(resp, "meta_ads_period")

            data = resp.json().get("data", [])
            if data:
                row = data[0]
                for field in ("reach", "frequency"):
                    val = row.get(field)
                    if val is not None:
                        metrics.append(ExtractedMetric(
                            provider="meta",
                            channel_slug="meta-ads",
                            metric_name=field,
                            value=float(val),
                            unit="count" if field == "reach" else "ratio",
                            date=period_start,
                            extra={"period_exact": True},
                        ))

        return metrics

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 200, "burst_size": 50}

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
            logger.warning("meta_provider_no_access_token tenant=%s", tenant_id)
            return ExtractionResult()

        metrics: List[ExtractedMetric] = []
        failures = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            if stage == "nurturing":
                ig_metrics, fail = await self._safe_extract(
                    self._extract_meta_retargeting,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_retargeting",
                )
                metrics.extend(ig_metrics)
                if fail:
                    failures.append(fail)
            else:
                ig_metrics, fail = await self._safe_extract(
                    self._extract_instagram_organic,
                    client, credentials, start_date, end_date,
                    extractor_name="instagram_organic",
                )
                metrics.extend(ig_metrics)
                if fail:
                    failures.append(fail)

                fb_metrics, fail = await self._safe_extract(
                    self._extract_facebook_organic,
                    client, credentials, start_date, end_date,
                    extractor_name="facebook_organic",
                )
                metrics.extend(fb_metrics)
                if fail:
                    failures.append(fail)

                ads_metrics, fail = await self._safe_extract(
                    self._extract_meta_ads,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_ads",
                )
                metrics.extend(ads_metrics)
                if fail:
                    failures.append(fail)

                campaigns_metrics, fail = await self._safe_extract(
                    self._extract_meta_ads_campaigns,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_ads_campaigns",
                )
                metrics.extend(campaigns_metrics)
                if fail:
                    failures.append(fail)

                breakdowns_metrics, fail = await self._safe_extract(
                    self._extract_meta_ads_breakdowns,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_ads_breakdowns",
                )
                metrics.extend(breakdowns_metrics)
                if fail:
                    failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

    # Mapping from IG Insights API metric name → internal metric_name
    _IG_API_TO_METRIC: dict[str, str] = {
        "reach": "reach",
        "views": "ig_views",
        "total_interactions": "total_interactions",
        "likes": "ig_likes",
        "comments": "ig_comments",
        "shares": "ig_shares",
        "saves": "ig_saves",
        "replies": "ig_replies",
        "reposts": "ig_reposts",
        "accounts_engaged": "ig_accounts_engaged",
        "follows_and_unfollows": "ig_follows_and_unfollows",
        "profile_links_taps": "ig_profile_links_taps",
    }

    # NON_AGGREGABLE metrics — use last day value instead of sum
    _IG_NON_AGGREGABLE = {"reach", "accounts_engaged"}

    # All IG Insights day-period metrics in a single batch
    _IG_INSIGHTS_METRICS = ",".join(_IG_API_TO_METRIC.keys())

    async def _extract_instagram_organic(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Instagram organic metrics (15 metrics, 3-4 API calls)."""
        access_token = credentials.get("access_token", "")
        ig_account_id = (
            credentials.get("instagram_account_id")
            or credentials.get("tracked_ig_id")
            or credentials.get("instagram_business_account_id")
        )
        if not ig_account_id:
            return []

        headers = _auth_headers(access_token)
        metrics: List[ExtractedMetric] = []

        # ── Call 1: Account Insights (total_value format, ≤30-day chunks) ──
        # Meta API with metric_type=total_value returns {total_value: {value: N}}
        # instead of {values: [{value, end_time}, ...]}. Sum chunks for ADDITIVE,
        # keep last chunk for NON_AGGREGABLE.
        totals: dict[str, float] = defaultdict(float)
        last_values: dict[str, float] = {}

        for chunk_start, chunk_end in _ig_day_chunks(start_date, end_date):
            insights_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                headers=headers,
                params={
                    "metric": self._IG_INSIGHTS_METRICS,
                    "metric_type": "total_value",
                    "period": "day",
                    "since": int(
                        datetime.combine(chunk_start, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(chunk_end, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(insights_resp, "ig_organic_insights")

            for item in insights_resp.json().get("data", []):
                api_name = item.get("name", "")
                metric_name = self._IG_API_TO_METRIC.get(api_name)
                if not metric_name:
                    continue

                val = float(
                    item.get("total_value", {}).get("value", 0)
                )
                if api_name in self._IG_NON_AGGREGABLE:
                    last_values[metric_name] = val
                else:
                    totals[metric_name] += val

        for metric_name, total in totals.items():
            metrics.append(
                ExtractedMetric(
                    provider="meta",
                    channel_slug="ig-organic",
                    metric_name=metric_name,
                    value=total,
                    unit="count",
                    date=end_date,
                )
            )
        for metric_name, val in last_values.items():
            metrics.append(
                ExtractedMetric(
                    provider="meta",
                    channel_slug="ig-organic",
                    metric_name=metric_name,
                    value=val,
                    unit="count",
                    date=end_date,
                )
            )

        # ── Call 2: User Node fields (snapshots) ──
        user_resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_account_id}",
            headers=headers,
            params={"fields": "followers_count,media_count"},
        )
        _raise_for_meta_error(user_resp, "ig_organic_user_node")
        user_data = user_resp.json()

        for field_name, metric_name in [
            ("followers_count", "ig_followers_count"),
            ("media_count", "ig_media_count"),
        ]:
            val = user_data.get(field_name)
            if val is not None:
                metrics.append(
                    ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=float(val),
                        unit="count",
                        date=end_date,
                    )
                )

        # ── Call 3-4: Demographics (lifetime) ──
        for demo_metric, metric_name in [
            ("follower_demographics", "ig_follower_demographics"),
            ("engaged_audience_demographics", "ig_engaged_audience_demographics"),
        ]:
            try:
                demo_resp = await client.get(
                    f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                    headers=headers,
                    params={
                        "metric": demo_metric,
                        "period": "lifetime",
                        "metric_type": "total_value",
                    },
                )
                _raise_for_meta_error(demo_resp, f"ig_organic_{demo_metric}")
                demo_data = demo_resp.json().get("data", [])
                extra = {}
                if demo_data:
                    total_value = demo_data[0].get("total_value", {})
                    extra = total_value.get("breakdowns", [{}])
                    if isinstance(extra, list) and extra:
                        extra = extra[0].get("results", [])

                metrics.append(
                    ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=0.0,
                        unit="json",
                        date=end_date,
                        extra={"breakdowns": extra},
                    )
                )
            except httpx.HTTPStatusError:
                logger.warning("ig_organic_%s_unavailable", demo_metric)

        return metrics

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

    @staticmethod
    def _parse_ads_row(
        data: dict, currency: str, metric_date: date,
    ) -> list["ExtractedMetric"]:
        """Parse a single Ads Insights API row into ExtractedMetric list.

        Shared by _extract_meta_ads (aggregated) and _extract_meta_ads_daily (per-day).
        """
        metrics: list[ExtractedMetric] = []

        # A) Simple numeric fields
        _SIMPLE_FIELDS = [
            ("reach", "reach", "count", None),
            ("impressions", "impressions", "count", None),
            ("clicks", "clicks", "count", None),
            ("ctr", "ctr", "percentage", None),
            ("cpm", "cpm", "currency", currency),
            ("cpc", "cpc", "currency", currency),
            ("cpp", "meta_cpp", "currency", currency),
            ("frequency", "frequency", "ratio", None),
            ("spend", "spend", "currency", currency),
            ("inline_link_clicks", "meta_inline_link_clicks", "count", None),
            ("inline_post_engagement", "meta_post_engagement", "count", None),
            ("cost_per_inline_link_click", "meta_cost_per_link_click", "currency", currency),
        ]
        for api_field, metric_name, unit, cur in _SIMPLE_FIELDS:
            val = data.get(api_field)
            if val is not None:
                metrics.append(ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name=metric_name,
                    value=float(val),
                    unit=unit,
                    currency=cur,
                    date=metric_date,
                ))

        # B) Outbound clicks (list of AdsActionStats)
        for entry in data.get("outbound_clicks", []):
            if entry.get("action_type") == "outbound_click":
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_outbound_clicks",
                    value=float(entry.get("value", 0)),
                    unit="count", date=metric_date,
                ))
        for entry in data.get("cost_per_outbound_click", []):
            if entry.get("action_type") == "outbound_click":
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_cost_per_outbound_click",
                    value=float(entry.get("value", 0)),
                    unit="currency", currency=currency, date=metric_date,
                ))

        # C) Actions → expanded conversions (using _META_ACTION_MAP)
        action_counts: dict[str, float] = defaultdict(float)
        for action in data.get("actions", []):
            action_type = action.get("action_type", "")
            mapped = _META_ACTION_MAP.get(action_type)
            if mapped:
                action_counts[mapped] += float(action.get("value", 0))
        for mapped_name, value in action_counts.items():
            metrics.append(ExtractedMetric(
                provider="meta", channel_slug="meta-ads",
                metric_name=mapped_name,
                value=value, unit="count", date=metric_date,
            ))

        # D) Action values → monetary conversion value
        for entry in data.get("action_values", []):
            if entry.get("action_type") in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_conversion_value",
                    value=float(entry.get("value", 0)),
                    unit="currency", currency=currency, date=metric_date,
                ))

        # E) Cost per action type
        for entry in data.get("cost_per_action_type", []):
            action_type = entry.get("action_type", "")
            if action_type in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_cost_per_purchase",
                    value=float(entry.get("value", 0)),
                    unit="currency", currency=currency, date=metric_date,
                ))
            elif action_type in ("offsite_conversion.fb_pixel_lead", "lead"):
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_cost_per_lead",
                    value=float(entry.get("value", 0)),
                    unit="currency", currency=currency, date=metric_date,
                ))

        # F) ROAS
        for entry in data.get("purchase_roas", []):
            if entry.get("action_type") == "omni_purchase":
                metrics.append(ExtractedMetric(
                    provider="meta", channel_slug="meta-ads",
                    metric_name="meta_purchase_roas",
                    value=float(entry.get("value", 0)),
                    unit="ratio", date=metric_date,
                ))

        # G) Video metrics
        _VIDEO_FIELDS = [
            ("video_p25_watched_actions", "meta_video_p25"),
            ("video_p50_watched_actions", "meta_video_p50"),
            ("video_p75_watched_actions", "meta_video_p75"),
            ("video_p100_watched_actions", "meta_video_p100"),
            ("video_30_sec_watched_actions", "meta_video_30sec"),
            ("video_avg_time_watched_actions", "meta_video_avg_watch_time"),
        ]
        for api_field, metric_name in _VIDEO_FIELDS:
            for entry in data.get(api_field, []):
                if entry.get("action_type") == "video_view":
                    unit = "seconds" if "avg" in api_field else "count"
                    metrics.append(ExtractedMetric(
                        provider="meta", channel_slug="meta-ads",
                        metric_name=metric_name,
                        value=float(entry.get("value", 0)),
                        unit=unit, date=metric_date,
                    ))

        return metrics

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

        response = await client.get(
            f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
            headers=headers,
            params={
                "fields": _ADS_EXPANDED_FIELDS,
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

        return self._parse_ads_row(data, currency, end_date)

    # ── Daily extraction methods (for initial load / gap detection) ──

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Like extract_metrics() but returns per-day granularity.

        Uses time_increment=1 (Ads) or parses values[] per-day (Organic)
        to emit one ExtractedMetric per day instead of a single aggregated row.
        """
        access_token = credentials.get("access_token")
        if not access_token:
            logger.warning("meta_provider_no_access_token tenant=%s", tenant_id)
            return ExtractionResult()

        metrics: List[ExtractedMetric] = []
        failures = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            if stage == "nurturing":
                m, fail = await self._safe_extract(
                    self._extract_meta_retargeting_daily,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_retargeting_daily",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)
            else:
                ig, fail = await self._safe_extract(
                    self._extract_instagram_organic_daily,
                    client, credentials, start_date, end_date,
                    extractor_name="instagram_organic_daily",
                )
                metrics.extend(ig)
                if fail:
                    failures.append(fail)

                fb, fail = await self._safe_extract(
                    self._extract_facebook_organic_daily,
                    client, credentials, start_date, end_date,
                    extractor_name="facebook_organic_daily",
                )
                metrics.extend(fb)
                if fail:
                    failures.append(fail)

                ads, fail = await self._safe_extract(
                    self._extract_meta_ads_daily,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_ads_daily",
                )
                metrics.extend(ads)
                if fail:
                    failures.append(fail)

                camps, fail = await self._safe_extract(
                    self._extract_meta_ads_campaigns_daily,
                    client, credentials, start_date, end_date,
                    extractor_name="meta_ads_campaigns_daily",
                )
                metrics.extend(camps)
                if fail:
                    failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

    async def _extract_instagram_organic_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Parse IG insights values[] array to emit one metric per day per metric."""
        access_token = credentials.get("access_token", "")
        ig_account_id = (
            credentials.get("instagram_account_id")
            or credentials.get("tracked_ig_id")
            or credentials.get("instagram_business_account_id")
        )
        if not ig_account_id:
            return []

        headers = _auth_headers(access_token)
        metrics: List[ExtractedMetric] = []

        # ── Call 1: Account Insights per day (total_value format) ──
        # metric_type=total_value returns {total_value: {value: N}} not values[].
        # To get daily granularity, make one call per day (since=day, until=day+1).
        current = start_date
        while current < end_date:
            next_day = current + timedelta(days=1)
            insights_resp = await client.get(
                f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                headers=headers,
                params={
                    "metric": self._IG_INSIGHTS_METRICS,
                    "metric_type": "total_value",
                    "period": "day",
                    "since": int(
                        datetime.combine(current, datetime.min.time()).timestamp()
                    ),
                    "until": int(
                        datetime.combine(next_day, datetime.min.time()).timestamp()
                    ),
                },
            )
            _raise_for_meta_error(insights_resp, "ig_organic_insights_daily")

            for item in insights_resp.json().get("data", []):
                api_name = item.get("name", "")
                metric_name = self._IG_API_TO_METRIC.get(api_name)
                if not metric_name:
                    continue

                val = float(
                    item.get("total_value", {}).get("value", 0)
                )
                metrics.append(
                    ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=val,
                        unit="count",
                        date=current,
                    )
                )
            current = next_day

        # ── Call 2: User Node snapshots (only emit on end_date) ──
        user_resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_account_id}",
            headers=headers,
            params={"fields": "followers_count,media_count"},
        )
        _raise_for_meta_error(user_resp, "ig_organic_user_node_daily")
        user_data = user_resp.json()

        for field_name, metric_name in [
            ("followers_count", "ig_followers_count"),
            ("media_count", "ig_media_count"),
        ]:
            val = user_data.get(field_name)
            if val is not None:
                metrics.append(
                    ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=float(val),
                        unit="count",
                        date=end_date,
                    )
                )

        # ── Call 3-4: Demographics (lifetime, only on end_date) ──
        for demo_metric, metric_name in [
            ("follower_demographics", "ig_follower_demographics"),
            ("engaged_audience_demographics", "ig_engaged_audience_demographics"),
        ]:
            try:
                demo_resp = await client.get(
                    f"{GRAPH_API_BASE}/{ig_account_id}/insights",
                    headers=headers,
                    params={
                        "metric": demo_metric,
                        "period": "lifetime",
                        "metric_type": "total_value",
                    },
                )
                _raise_for_meta_error(demo_resp, f"ig_organic_{demo_metric}_daily")
                demo_data = demo_resp.json().get("data", [])
                extra = {}
                if demo_data:
                    total_value = demo_data[0].get("total_value", {})
                    extra = total_value.get("breakdowns", [{}])
                    if isinstance(extra, list) and extra:
                        extra = extra[0].get("results", [])

                metrics.append(
                    ExtractedMetric(
                        provider="meta",
                        channel_slug="ig-organic",
                        metric_name=metric_name,
                        value=0.0,
                        unit="json",
                        date=end_date,
                        extra={"breakdowns": extra},
                    )
                )
            except httpx.HTTPStatusError:
                logger.warning("ig_organic_%s_daily_unavailable", demo_metric)

        return metrics

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

        response = await client.get(
            f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
            headers=headers,
            params={
                "fields": _ADS_EXPANDED_FIELDS,
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

            metrics.extend(self._parse_ads_row(row, currency, metric_date))
        return metrics

    # ── Phase 2: Campaign-level extraction ──

    async def _extract_meta_ads_campaigns(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Meta Ads metrics at campaign level."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        currency = credentials.get("currency", "USD")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)

        response = await client.get(
            f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
            headers=headers,
            params={
                "fields": f"campaign_id,campaign_name,{_ADS_EXPANDED_FIELDS}",
                "time_range": json.dumps(
                    {
                        "since": start_date.isoformat(),
                        "until": end_date.isoformat(),
                    }
                ),
                "level": "campaign",
                "limit": "500",
            },
        )
        _raise_for_meta_error(response, "meta_ads_campaigns")
        rows = response.json().get("data", [])

        metrics: List[ExtractedMetric] = []
        for row in rows:
            campaign_id = row.get("campaign_id")
            parsed = self._parse_ads_row(row, currency, end_date)
            for m in parsed:
                m.campaign_id = campaign_id
            metrics.extend(parsed)
        return metrics

    async def _extract_meta_ads_campaigns_daily(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract Meta Ads campaign-level metrics with daily granularity."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        currency = credentials.get("currency", "USD")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)

        response = await client.get(
            f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
            headers=headers,
            params={
                "fields": f"campaign_id,campaign_name,{_ADS_EXPANDED_FIELDS}",
                "time_range": json.dumps(
                    {
                        "since": start_date.isoformat(),
                        "until": end_date.isoformat(),
                    }
                ),
                "time_increment": "1",
                "level": "campaign",
                "limit": "500",
            },
        )
        _raise_for_meta_error(response, "meta_ads_campaigns_daily")
        rows = response.json().get("data", [])

        metrics: List[ExtractedMetric] = []
        for row in rows:
            date_str = row.get("date_start", "")
            try:
                metric_date = date.fromisoformat(date_str)
            except (ValueError, AttributeError):
                continue
            campaign_id = row.get("campaign_id")
            parsed = self._parse_ads_row(row, currency, metric_date)
            for m in parsed:
                m.campaign_id = campaign_id
            metrics.extend(parsed)
        return metrics

    # ── Phase 3: Demographic / Placement breakdowns ──

    _BREAKDOWN_METRICS = ["reach", "impressions", "spend"]

    async def _extract_meta_ads_breakdowns(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract demographic and placement breakdowns for Meta Ads."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        headers = _auth_headers(access_token)
        time_range = json.dumps(
            {"since": start_date.isoformat(), "until": end_date.isoformat()}
        )
        fields = ",".join(self._BREAKDOWN_METRICS)
        metrics: List[ExtractedMetric] = []

        breakdown_configs = [
            ("age", "age"),
            ("gender", "gender"),
            ("publisher_platform,platform_position", "placement"),
        ]

        for breakdown_param, breakdown_key in breakdown_configs:
            response = await client.get(
                f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
                headers=headers,
                params={
                    "fields": fields,
                    "time_range": time_range,
                    "breakdowns": breakdown_param,
                    "level": "account",
                    "limit": "500",
                },
            )
            _raise_for_meta_error(response, f"meta_ads_breakdown_{breakdown_key}")
            rows = response.json().get("data", [])

            # Aggregate rows into {metric_name: [{dimension_values: [...], value: ...}]}
            for base_metric in self._BREAKDOWN_METRICS:
                breakdowns_list = []
                for row in rows:
                    val = row.get(base_metric)
                    if val is None:
                        continue
                    if breakdown_key == "placement":
                        dim_values = [
                            row.get("publisher_platform", ""),
                            row.get("platform_position", ""),
                        ]
                    else:
                        dim_values = [row.get(breakdown_key, "")]
                    breakdowns_list.append(
                        {"dimension_values": dim_values, "value": float(val)}
                    )

                if breakdowns_list:
                    metric_name = f"meta_{base_metric}_by_{breakdown_key}"
                    metrics.append(
                        ExtractedMetric(
                            provider="meta",
                            channel_slug="meta-ads",
                            metric_name=metric_name,
                            value=0.0,
                            unit="json",
                            date=end_date,
                            extra={"breakdowns": breakdowns_list},
                        )
                    )

        return metrics

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
