"""MailerLiteProvider — extracts email-marketing metrics from MailerLite API.

Dispatches by funnel stage to different extraction strategies:
- capture: forms + subscriber growth
- nurture/opportunity/expansion/evangelization/retention: campaign-based
- delivery/adoption: automation-based

Channel slugs follow the pattern ``email-<stage>`` so the Growth Studio
can render each stage independently in the Bowtie funnel.

Uses httpx async client directly (per-instance, no singleton) for
tenant isolation — same pattern as MetaProvider.
"""

import asyncio
import logging
from datetime import date, datetime

import sentry_sdk
from typing import Dict, List, Optional, Set
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://connect.mailerlite.com/api"

# All stages this provider serves
EMAIL_STAGES = [
    "capture", "nurture", "opportunity", "delivery",
    "retention", "adoption", "expansion", "evangelization",
]

# Stage -> channel slug for ExtractedMetric.channel_slug
STAGE_TO_SLUG: Dict[str, str] = {
    "capture": "email-capture",
    "nurture": "email-nurture",
    "opportunity": "email-launch",
    "delivery": "email-delivery",
    "adoption": "email-onboarding",
    "retention": "email-retention",
    "expansion": "email-upsell",
    "evangelization": "email-referral",
}

# Campaign-based stages (extract from /campaigns filtered by group mapping)
CAMPAIGN_STAGES: Set[str] = {
    "nurture", "opportunity", "expansion", "evangelization", "retention",
}

# Automation-based stages
AUTOMATION_STAGES: Set[str] = {"delivery", "adoption"}

# MailerLite API field -> (canonical metric_name, unit)
MAILERLITE_METRIC_MAP: Dict[str, tuple] = {
    "sent": ("emails_sent", "count"),
    "unique_opens_count": ("unique_opens", "count"),
    "unique_clicks_count": ("unique_clicks", "count"),
    "open_rate": ("open_rate", "percentage"),
    "click_rate": ("click_rate", "percentage"),
    "click_to_open_rate": ("click_to_open_rate", "percentage"),
    "hard_bounces_count": ("hard_bounces", "count"),
    "soft_bounces_count": ("soft_bounces", "count"),
    "unsubscribes_count": ("unsubscribes", "count"),
    "spam_count": ("spam_reports", "count"),
    "forwards_count": ("forwards", "count"),
}

# Rate-limit budget: 100 requests/min of 120 allowed  →  0.6s between paginated calls
_RATE_LIMIT_SLEEP = 0.6
_RETRY_BASE_DELAY = 5.0
_MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_headers(api_key: str) -> dict:
    """Build auth + content-type headers for MailerLite API."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _api_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    *,
    params: Optional[dict] = None,
) -> httpx.Response:
    """GET with exponential-backoff retry on 429 (rate limited).

    Raises on non-retryable HTTP errors.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code == 429:
            delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "mailerlite_rate_limited url=%s attempt=%d delay=%.1fs",
                url, attempt, delay,
            )
            await asyncio.sleep(delay)
            continue
        if resp.status_code >= 400:
            body = resp.text[:500]
            logger.error(
                "mailerlite_api_error url=%s status=%s body=%s",
                url, resp.status_code, body,
            )
            resp.raise_for_status()
        return resp

    # Exhausted retries
    logger.error("mailerlite_retries_exhausted url=%s", url)
    raise httpx.HTTPStatusError(
        "Rate limit retries exhausted",
        request=resp.request,  # type: ignore[possibly-undefined]
        response=resp,  # type: ignore[possibly-undefined]
    )


def _parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 date string from MailerLite, tolerant of 'Z' suffix."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class MailerLiteProvider(BaseMetricsProvider):
    """Extracts email-marketing metrics from MailerLite, dispatched by
    funnel stage."""

    def provider_name(self) -> str:
        return "mailerlite"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 100, "burst_size": 20}

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "nurture",
    ) -> List[ExtractedMetric]:
        api_key = credentials.get("api_key")
        if not api_key:
            logger.warning("mailerlite_no_api_key tenant=%s", tenant_id)
            return []

        if stage not in EMAIL_STAGES:
            logger.warning(
                "mailerlite_unknown_stage tenant=%s stage=%s", tenant_id, stage
            )
            return []

        headers = _get_headers(api_key)
        slug = STAGE_TO_SLUG[stage]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stage == "capture":
                    return await self._extract_capture(
                        client, headers, credentials, start_date, end_date, slug,
                    )
                if stage in CAMPAIGN_STAGES:
                    return await self._extract_campaigns(
                        client, headers, credentials, start_date, end_date, stage, slug,
                    )
                if stage in AUTOMATION_STAGES:
                    return await self._extract_automations(
                        client, headers, credentials, start_date, end_date, slug,
                    )
        except Exception:
            sentry_sdk.set_tag("provider", "mailerlite")
            sentry_sdk.capture_exception()
            logger.exception(
                "mailerlite_extract_failed tenant=%s stage=%s", tenant_id, stage,
            )
        return []

    # ------------------------------------------------------------------
    # CAPTURE stage
    # ------------------------------------------------------------------

    async def _extract_capture(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        credentials: dict,
        start_date: date,
        end_date: date,
        slug: str,
    ) -> List[ExtractedMetric]:
        metrics: List[ExtractedMetric] = []
        metric_date = end_date

        # 1. Forms — popup, embedded, promotion
        total_conversions = 0
        total_conversion_rate = 0.0
        form_count = 0

        for form_type in ("popup", "embedded", "promotion"):
            url = f"{BASE_URL}/forms?type={form_type}&limit=100"
            resp = await _api_get(client, url, headers)
            data = resp.json().get("data", [])
            for form in data:
                conversions = form.get("conversions_count", 0)
                rate = form.get("conversion_rate", 0.0)
                total_conversions += conversions
                total_conversion_rate += rate
                form_count += 1
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        metrics.append(ExtractedMetric(
            provider="mailerlite",
            channel_slug=slug,
            metric_name="form_conversions",
            value=float(total_conversions),
            unit="count",
            date=metric_date,
        ))
        if form_count > 0:
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="form_conversion_rate",
                value=(total_conversion_rate / form_count) * 100,
                unit="percentage",
                date=metric_date,
            ))

        # 2. Active subscribers (total)
        subs_url = f"{BASE_URL}/subscribers?filter[status]=active&limit=0"
        subs_resp = await _api_get(client, subs_url, headers)
        subs_meta = subs_resp.json().get("meta", {})
        active_total = subs_meta.get("total", 0)
        metrics.append(ExtractedMetric(
            provider="mailerlite",
            channel_slug=slug,
            metric_name="active_subscribers",
            value=float(active_total),
            unit="count",
            date=metric_date,
        ))

        # 3. New subscribers in date range (paginated)
        new_subs = await self._count_new_subscribers(
            client, headers, start_date, end_date,
        )
        metrics.append(ExtractedMetric(
            provider="mailerlite",
            channel_slug=slug,
            metric_name="new_subscribers",
            value=float(new_subs),
            unit="count",
            date=metric_date,
        ))

        return metrics

    async def _count_new_subscribers(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_date: date,
        end_date: date,
    ) -> int:
        """Paginate through subscribers and count those subscribed within range."""
        count = 0
        cursor: Optional[str] = None
        page_limit = 100

        while True:
            url = f"{BASE_URL}/subscribers?filter[status]=active&limit={page_limit}&sort=-subscribed_at"
            if cursor:
                url += f"&cursor={cursor}"

            resp = await _api_get(client, url, headers)
            body = resp.json()
            data = body.get("data", [])

            if not data:
                break

            stop_pagination = False
            for sub in data:
                subscribed_dt = _parse_iso_date(sub.get("subscribed_at"))
                if subscribed_dt is None:
                    continue
                sub_date = subscribed_dt.date()
                if sub_date < start_date:
                    # Sorted desc — no more subscribers in range
                    stop_pagination = True
                    break
                if start_date <= sub_date <= end_date:
                    count += 1

            if stop_pagination:
                break

            # Next page cursor
            next_cursor = body.get("meta", {}).get("next_cursor")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        return count

    # ------------------------------------------------------------------
    # CAMPAIGN-BASED stages (nurture, opportunity, expansion, etc.)
    # ------------------------------------------------------------------

    async def _extract_campaigns(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str,
        slug: str,
    ) -> List[ExtractedMetric]:
        stage_group_mapping: Dict[str, List[str]] = credentials.get(
            "stage_group_mapping", {}
        )
        known_groups: List[str] = credentials.get("known_groups", [])
        known_groups_set: Set[str] = set(known_groups)

        # 1. Fetch all groups to detect new ones
        groups_url = f"{BASE_URL}/groups?limit=100"
        groups_resp = await _api_get(client, groups_url, headers)
        all_groups = groups_resp.json().get("data", [])
        await asyncio.sleep(_RATE_LIMIT_SLEEP)

        # Auto-detect new groups
        for grp in all_groups:
            gid = str(grp.get("id", ""))
            if gid and gid not in known_groups_set:
                logger.info(
                    "mailerlite_new_group_detected id=%s name=%s auto_assign=nurture",
                    gid, grp.get("name", ""),
                )
                stage_group_mapping.setdefault("nurture", []).append(gid)
                known_groups_set.add(gid)

        # Build reverse lookup: group_id -> stage
        group_to_stage: Dict[str, str] = {}
        for stg, gids in stage_group_mapping.items():
            for gid in gids:
                group_to_stage[str(gid)] = stg

        # 2. Fetch sent campaigns (paginated, newest first)
        campaigns = await self._fetch_sent_campaigns(
            client, headers, start_date, end_date,
        )

        # 3. Filter campaigns that match the requested stage
        matched_campaigns: List[dict] = []
        for campaign in campaigns:
            campaign_stage = self._classify_campaign_stage(
                campaign, group_to_stage,
            )
            if campaign_stage == stage:
                matched_campaigns.append(campaign)

        if not matched_campaigns:
            logger.info(
                "mailerlite_no_campaigns stage=%s date_range=%s..%s",
                stage, start_date, end_date,
            )
            return []

        # 4. Aggregate stats
        metrics = self._aggregate_campaign_metrics(
            matched_campaigns, slug, end_date, known_groups_set,
        )

        return metrics

    async def _fetch_sent_campaigns(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_date: date,
        end_date: date,
    ) -> List[dict]:
        """Fetch sent campaigns within the date range, paginated."""
        campaigns: List[dict] = []
        page = 1

        while True:
            url = (
                f"{BASE_URL}/campaigns"
                f"?filter[status]=sent&limit=50&sort=-finished_at&page={page}"
            )
            resp = await _api_get(client, url, headers)
            data = resp.json().get("data", [])

            if not data:
                break

            stop = False
            for campaign in data:
                finished_dt = _parse_iso_date(campaign.get("finished_at"))
                if finished_dt is None:
                    continue
                finished_date = finished_dt.date()
                if finished_date < start_date:
                    stop = True
                    break
                if finished_date <= end_date:
                    campaigns.append(campaign)

            if stop:
                break

            page += 1
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        return campaigns

    def _classify_campaign_stage(
        self,
        campaign: dict,
        group_to_stage: Dict[str, str],
    ) -> str:
        """Determine which funnel stage a campaign belongs to based on
        its targeted groups. Defaults to 'nurture' if no group match."""
        # MailerLite campaigns have a 'groups' field listing targeted groups
        groups = campaign.get("groups", [])
        if not groups:
            # Also check filter -> groups (API v2 format variation)
            filter_data = campaign.get("filter", {})
            if isinstance(filter_data, list):
                for f in filter_data:
                    if isinstance(f, dict) and f.get("type") == "group":
                        groups = f.get("args", [])
                        break
            elif isinstance(filter_data, dict):
                groups = filter_data.get("groups", [])

        for grp in groups:
            gid = str(grp.get("id", grp)) if isinstance(grp, dict) else str(grp)
            if gid in group_to_stage:
                return group_to_stage[gid]

        return "nurture"

    def _normalize_campaign_stats(self, stats: dict) -> Dict[str, tuple]:
        """Apply MAILERLITE_METRIC_MAP to raw campaign stats.

        Returns dict of canonical_name -> (value, unit).
        """
        result: Dict[str, tuple] = {}
        for api_field, (canonical_name, unit) in MAILERLITE_METRIC_MAP.items():
            raw = stats.get(api_field)
            if raw is None:
                continue
            if isinstance(raw, dict):
                logger.warning("mailerlite_unexpected_stat_type field=%s type=%s", api_field, type(raw).__name__)
                continue
            value = float(raw)
            # MailerLite percentages come as 0.0-1.0 — convert to 0-100
            if unit == "percentage":
                value *= 100
            result[canonical_name] = (value, unit)
        return result

    def _aggregate_campaign_metrics(
        self,
        campaigns: List[dict],
        slug: str,
        metric_date: date,
        known_groups_set: Set[str],
    ) -> List[ExtractedMetric]:
        """Aggregate metrics across matched campaigns and compute derived metrics."""
        totals: Dict[str, float] = {}
        rate_sums: Dict[str, float] = {}
        campaign_count = len(campaigns)

        for campaign in campaigns:
            stats = campaign.get("stats", campaign.get("campaign_stats", {}))
            normalized = self._normalize_campaign_stats(stats)

            for name, (value, unit) in normalized.items():
                if unit == "percentage":
                    rate_sums[name] = rate_sums.get(name, 0.0) + value
                else:
                    totals[name] = totals.get(name, 0.0) + value

        metrics: List[ExtractedMetric] = []

        # Emit summed count metrics
        for name, value in totals.items():
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name=name,
                value=value,
                unit="count",
                date=metric_date,
            ))

        # Emit averaged rate metrics
        if campaign_count > 0:
            for name, total in rate_sums.items():
                metrics.append(ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name=name,
                    value=total / campaign_count,
                    unit="percentage",
                    date=metric_date,
                ))

        # Derived: bounce_rate
        sent = totals.get("emails_sent", 0.0)
        hard = totals.get("hard_bounces", 0.0)
        soft = totals.get("soft_bounces", 0.0)
        if sent > 0:
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="bounce_rate",
                value=(hard + soft) / sent * 100,
                unit="percentage",
                date=metric_date,
            ))

        # Derived: unsubscribe_rate
        unsubs = totals.get("unsubscribes", 0.0)
        if sent > 0:
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="unsubscribe_rate",
                value=unsubs / sent * 100,
                unit="percentage",
                date=metric_date,
            ))

        # For retention stage: derive reactivation_rate
        if slug == STAGE_TO_SLUG.get("retention") and sent > 0:
            opens = totals.get("unique_opens", 0.0)
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="reactivation_rate",
                value=opens / sent * 100,
                unit="percentage",
                date=metric_date,
            ))

        # Attach updated config info for traceability (new group auto-mapping)
        if metrics and known_groups_set:
            metrics[0].extra["updated_known_groups"] = sorted(known_groups_set)

        return metrics

    # ------------------------------------------------------------------
    # AUTOMATION-BASED stages (delivery, adoption)
    # ------------------------------------------------------------------

    async def _extract_automations(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        credentials: dict,
        start_date: date,
        end_date: date,
        slug: str,
    ) -> List[ExtractedMetric]:
        # 1. Fetch enabled automations
        url = f"{BASE_URL}/automations?filter[enabled]=true&limit=100"
        resp = await _api_get(client, url, headers)
        automations = resp.json().get("data", [])
        await asyncio.sleep(_RATE_LIMIT_SLEEP)

        if not automations:
            logger.info("mailerlite_no_automations slug=%s", slug)
            return []

        total_triggered = 0
        total_completed = 0
        total_sent = 0
        rate_open_sum = 0.0
        rate_click_sum = 0.0
        auto_count = 0

        for auto in automations:
            auto_id = auto.get("id")
            if not auto_id:
                continue

            # 2. Fetch automation activity/stats
            activity_url = f"{BASE_URL}/automations/{auto_id}/activity"
            try:
                activity_resp = await _api_get(client, activity_url, headers)
            except httpx.HTTPStatusError:
                logger.warning(
                    "mailerlite_automation_activity_failed id=%s", auto_id,
                )
                continue
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

            activity = activity_resp.json()
            # Activity may be nested under "data" or at root
            stats = activity.get("data", activity)

            triggered = int(stats.get("triggered", stats.get("emails_sent", 0)))
            completed = int(stats.get("completed", 0))
            sent = int(stats.get("sent", stats.get("emails_sent", 0)))
            open_rate = float(stats.get("open_rate", 0.0))
            click_rate = float(stats.get("click_rate", 0.0))

            total_triggered += triggered
            total_completed += completed
            total_sent += sent
            rate_open_sum += open_rate
            rate_click_sum += click_rate
            auto_count += 1

        metrics: List[ExtractedMetric] = []
        metric_date = end_date

        metrics.append(ExtractedMetric(
            provider="mailerlite",
            channel_slug=slug,
            metric_name="emails_sent",
            value=float(total_sent),
            unit="count",
            date=metric_date,
        ))

        if auto_count > 0:
            # MailerLite percentages are 0.0-1.0
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="open_rate",
                value=(rate_open_sum / auto_count) * 100,
                unit="percentage",
                date=metric_date,
            ))
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="click_rate",
                value=(rate_click_sum / auto_count) * 100,
                unit="percentage",
                date=metric_date,
            ))

        # Completion rate = completed / triggered * 100
        if total_triggered > 0:
            metrics.append(ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="completion_rate",
                value=total_completed / total_triggered * 100,
                unit="percentage",
                date=metric_date,
            ))

        metrics.append(ExtractedMetric(
            provider="mailerlite",
            channel_slug=slug,
            metric_name="automation_completed",
            value=float(total_completed),
            unit="count",
            date=metric_date,
        ))

        return metrics
