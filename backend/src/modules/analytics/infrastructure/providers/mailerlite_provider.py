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
from datetime import date, datetime
from uuid import UUID

import httpx
import structlog

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = structlog.get_logger(__name__)

BASE_URL = "https://connect.mailerlite.com/api"

# All stages this provider serves
EMAIL_STAGES = [
    "capture",
    "nurture",
    "opportunity",
    "delivery",
    "retention",
    "adoption",
    "expansion",
    "evangelization",
]

# Stage -> channel slug for ExtractedMetric.channel_slug
STAGE_TO_SLUG: dict[str, str] = {
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
CAMPAIGN_STAGES: set[str] = {
    "nurture",
    "opportunity",
    "expansion",
    "evangelization",
    "retention",
}

# Automation-based stages
AUTOMATION_STAGES: set[str] = {"delivery", "adoption"}

# MailerLite API field -> (canonical metric_name, unit)
MAILERLITE_METRIC_MAP: dict[str, tuple] = {
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
    "opens_count": ("opens_count", "count"),
    "clicks_count": ("clicks_count", "count"),
}

# Campaign type classification keywords (Spanish + English)
_CAMPAIGN_TYPE_KEYWORDS: dict[str, list[str]] = {
    "newsletter": [
        "newsletter",
        "semanal",
        "quincenal",
        "mensual",
        "edición",
        "digest",
        "novedades",
    ],
    "lanzamiento": [
        "lanzamiento",
        "launch",
        "nuevo",
        "exclusivo",
        "estreno",
        "preventa",
        "acceso",
    ],
    "promocion": [
        "promo",
        "descuento",
        "oferta",
        "%",
        "black friday",
        "cyber",
        "sale",
        "gratis",
        "free",
    ],
    "reengagement": [
        "extrañamos",
        "miss you",
        "vuelve",
        "reactivar",
        "inactivo",
        "última oportunidad",
    ],
}


_AUTOMATION_TYPE_KEYWORDS: dict[str, list[str]] = {
    "welcome": ["bienvenida", "welcome", "onboarding"],
    "nurture": ["nutrición", "nutricion", "nurtur", "secuencia", "drip"],
    "reengagement": [
        "re-engagement",
        "reengagement",
        "reactivación",
        "reactivacion",
        "win-back",
    ],
    "post_compra": [
        "post-compra",
        "post compra",
        "post_compra",
        "thank you",
        "gracias por tu compra",
    ],
}


def _parse_rate(raw: dict[str, float | str] | float | None) -> float:
    """Normalize a MailerLite rate value to a 0-100 percentage.

    MailerLite returns one of:
      - dict with 'float' key: {"float": 0.625, "string": "62.5%"}
      - bare float / int: 0.625
      - None or missing

    Returns 0.0 on any unexpected shape (strings, nested dicts without 'float',
    malformed values) rather than crashing the ETL.
    """
    if raw is None:
        return 0.0
    if isinstance(raw, dict):
        try:
            return float(raw.get("float", 0.0)) * 100
        except (TypeError, ValueError):
            return 0.0
    try:
        return float(raw) * 100
    except (TypeError, ValueError):
        return 0.0


def _extract_step_data(steps: list[dict]) -> list[dict]:
    """Extract per-step data from MailerLite automation steps array.

    Returns list of step dicts with normalized fields for storage in extra.
    Email steps include full stats (subject, opens, clicks, etc.).
    Delay steps include value+unit.
    Other step types get the same base shape with zero/None values.
    """
    result = []
    for idx, step in enumerate(steps):
        step_type = step.get("type", "email")
        base = {
            "step_id": str(step.get("id", f"step-{idx}")),
            "step_number": idx + 1,
            "type": step_type,
        }
        if step_type == "email":
            email_obj = step.get("email", {}) or {}
            stats = email_obj.get("stats", {}) or {}
            base.update(
                {
                    "subject": step.get("subject", "") or "",
                    "from_name": step.get("from_name", "") or "",
                    "emails_sent": int(stats.get("sent", 0) or 0),
                    "unique_opens": int(stats.get("unique_opens_count", 0) or 0),
                    "open_rate": _parse_rate(stats.get("open_rate", 0)),
                    "unique_clicks": int(stats.get("unique_clicks_count", 0) or 0),
                    "click_rate": _parse_rate(stats.get("click_rate", 0)),
                    "unsubscribes": int(stats.get("unsubscribes_count", 0) or 0),
                    "bounces": int(stats.get("hard_bounces_count", 0) or 0)
                    + int(stats.get("soft_bounces_count", 0) or 0),
                    "screenshot_url": email_obj.get("screenshot_url"),
                    "preview_url": email_obj.get("preview_url"),
                    "delay_value": None,
                    "delay_unit": None,
                },
            )
        elif step_type == "delay":
            base.update(
                {
                    "subject": None,
                    "from_name": None,
                    "emails_sent": 0,
                    "unique_opens": 0,
                    "open_rate": 0.0,
                    "unique_clicks": 0,
                    "click_rate": 0.0,
                    "unsubscribes": 0,
                    "bounces": 0,
                    "screenshot_url": None,
                    "preview_url": None,
                    "delay_value": int(step.get("value", 0) or 0),
                    "delay_unit": step.get("unit"),
                },
            )
        else:
            base.update(
                {
                    "subject": None,
                    "from_name": None,
                    "emails_sent": 0,
                    "unique_opens": 0,
                    "open_rate": 0.0,
                    "unique_clicks": 0,
                    "click_rate": 0.0,
                    "unsubscribes": 0,
                    "bounces": 0,
                    "screenshot_url": None,
                    "preview_url": None,
                    "delay_value": None,
                    "delay_unit": None,
                },
            )
        result.append(base)
    return result


def classify_automation_type(name: str) -> str:
    """Classify an automation into a type based on keywords in its name.

    Returns one of: welcome, nurture, reengagement, post_compra, workflow.
    Falls back to 'workflow' when no keyword matches.
    """
    text = name.lower()
    for auto_type, keywords in _AUTOMATION_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return auto_type
    return "workflow"


def classify_campaign_type(name: str, subject: str) -> str:
    """Classify a campaign into a type based on keywords in name and subject.

    Returns one of: newsletter, lanzamiento, promocion, reengagement, contenido.
    Falls back to 'contenido' when no keyword matches.
    """
    text = f"{name} {subject}".lower()
    for campaign_type, keywords in _CAMPAIGN_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return campaign_type
    return "contenido"


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
    params: dict | None = None,
) -> httpx.Response:
    """GET with exponential-backoff retry on 429 (rate limited).

    Raises on non-retryable HTTP errors.
    """
    resp: httpx.Response | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code == 429:
            delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                "mailerlite_rate_limited",
                url=url,
                attempt=attempt,
                delay=delay,
            )
            await asyncio.sleep(delay)
            continue
        if resp.status_code >= 400:
            body = resp.text[:500]
            logger.error(
                "mailerlite_api_error",
                url=url,
                status=resp.status_code,
                body=body,
            )
            resp.raise_for_status()
        return resp

    # Exhausted retries — resp is always set when _MAX_RETRIES >= 1
    logger.error("mailerlite_retries_exhausted", url=url)
    msg = "Rate limit retries exhausted"
    if resp is None:
        raise RuntimeError(msg)
    raise httpx.HTTPStatusError(
        msg,
        request=resp.request,
        response=resp,
    )


def _parse_iso_date(value: str | None) -> datetime | None:
    """Parse an ISO-8601 date string from MailerLite, tolerant of 'Z' suffix."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class MailerLiteProvider(BaseMetricsProvider):
    """Extract email-marketing metrics from MailerLite dispatched by funnel stage."""

    def provider_name(self) -> str:
        """Execute provider name operation."""
        return "mailerlite"

    def rate_limit_config(self) -> dict:
        """Execute rate limit config operation."""
        return {"requests_per_minute": 100, "burst_size": 20}

    # ------------------------------------------------------------------
    # Optimized daily extraction (overrides base day-by-day loop)
    # ------------------------------------------------------------------

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "nurture",
    ) -> ExtractionResult:
        """Optimized: single batch call for the full date range.

        extract_metrics() already fetches all campaigns/subscribers in the
        range and groups by date internally. The base class default would
        call it once per day (N API calls x N days). This override calls
        it once with the full range.
        """
        return await self.extract_metrics(
            tenant_id=tenant_id,
            credentials=credentials,
            start_date=start_date,
            end_date=end_date,
            stage=stage,
        )

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
    ) -> ExtractionResult:
        """Extract metrics."""
        api_key = credentials.get("api_key")
        if not api_key:
            logger.warning("mailerlite_no_api_key", tenant_id=str(tenant_id))
            return ExtractionResult()

        if stage not in EMAIL_STAGES:
            logger.warning(
                "mailerlite_unknown_stage",
                tenant_id=str(tenant_id),
                stage=stage,
            )
            return ExtractionResult()

        headers = _get_headers(api_key)
        slug = STAGE_TO_SLUG[stage]

        metrics: list[ExtractedMetric] = []
        failures = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if stage == "capture":
                m, fail = await self._safe_extract(
                    self._extract_capture,
                    client,
                    headers,
                    credentials,
                    start_date,
                    end_date,
                    slug,
                    extractor_name="mailerlite_capture",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)
            elif stage in CAMPAIGN_STAGES:
                m, fail = await self._safe_extract(
                    self._extract_campaigns,
                    client,
                    headers,
                    credentials,
                    start_date,
                    end_date,
                    stage,
                    slug,
                    extractor_name="mailerlite_campaigns",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)

                # Nurture also extracts automations into the same slug
                if stage == "nurture":
                    auto_m, auto_fail = await self._safe_extract(
                        self._extract_automations,
                        client,
                        headers,
                        credentials,
                        start_date,
                        end_date,
                        slug,
                        extractor_name="mailerlite_automations",
                    )
                    metrics.extend(auto_m)
                    if auto_fail:
                        failures.append(auto_fail)
            elif stage in AUTOMATION_STAGES:
                m, fail = await self._safe_extract(
                    self._extract_automations,
                    client,
                    headers,
                    credentials,
                    start_date,
                    end_date,
                    slug,
                    extractor_name="mailerlite_automations",
                )
                metrics.extend(m)
                if fail:
                    failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

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
    ) -> list[ExtractedMetric]:
        metrics: list[ExtractedMetric] = []
        metric_date = end_date

        # 1. Forms — popup, embedded, promotion
        #    MailerLite API v2: GET /api/forms/{type} (type is a path param)
        total_conversions = 0
        total_conversion_rate = 0.0
        form_count = 0

        for form_type in ("popup", "embedded", "promotion"):
            url = f"{BASE_URL}/forms/{form_type}"
            try:
                resp = await _api_get(client, url, headers, params={"limit": 100})
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "mailerlite_forms_fetch_failed",
                    form_type=form_type,
                    status=exc.response.status_code,
                    detail=exc.response.text[:200],
                )
                continue
            data = resp.json().get("data", [])
            for form in data:
                conversions = form.get("conversions_count", 0)
                raw_rate = form.get("conversion_rate", 0.0)
                # conversion_rate may be a dict like {"float": 0.5, "string": "50%"}
                if isinstance(raw_rate, dict):
                    raw_rate = raw_rate.get("float", 0.0)
                total_conversions += conversions
                total_conversion_rate += float(raw_rate)
                form_count += 1
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        metrics.append(
            ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="form_conversions",
                value=float(total_conversions),
                unit="count",
                date=metric_date,
            ),
        )
        if form_count > 0:
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="form_conversion_rate",
                    value=(total_conversion_rate / form_count) * 100,
                    unit="percentage",
                    date=metric_date,
                ),
            )

        # 2. Active subscribers (current total)
        #    With limit=0, MailerLite returns {"total": N} at root (no "meta" wrapper)
        subs_url = f"{BASE_URL}/subscribers?filter[status]=active&limit=0"
        subs_resp = await _api_get(client, subs_url, headers)
        subs_body = subs_resp.json()
        active_total = subs_body.get("total", 0)

        # 3. New subscribers in date range (paginated, grouped by day)
        daily_new_subs = await self._count_new_subscribers_daily(
            client,
            headers,
            start_date,
            end_date,
        )
        for day, count in sorted(daily_new_subs.items()):
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="new_subscribers",
                    value=float(count),
                    unit="count",
                    date=day,
                ),
            )

        # 4. Reconstruct daily active_subscribers curve backwards from today's total.
        #    MailerLite only gives the current snapshot, so we estimate:
        #    active(day) = active(today) - new_subs_after(day)
        #    Emit for EVERY day in the range so the chart line is continuous.
        from datetime import timedelta as _td

        all_days = [start_date + _td(days=i) for i in range((end_date - start_date).days + 1)]

        # Cumulative new subs after each day (sum of new_subs from day+1 to end)
        cumulative_after = 0
        daily_active: dict[date, float] = {}
        for day in reversed(all_days):
            daily_active[day] = max(0, active_total - cumulative_after)
            cumulative_after += daily_new_subs.get(day, 0)

        metrics.extend(
            ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="active_subscribers",
                value=daily_active[day],
                unit="count",
                date=day,
            )
            for day in all_days
        )

        return metrics

    async def _count_new_subscribers_daily(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_date: date,
        end_date: date,
    ) -> dict[date, int]:
        """Paginate through subscribers and count per day within range."""
        from collections import defaultdict

        daily: dict[date, int] = defaultdict(int)
        cursor: str | None = None
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
                    stop_pagination = True
                    break
                if start_date <= sub_date <= end_date:
                    daily[sub_date] += 1

            if stop_pagination:
                break

            next_cursor = body.get("meta", {}).get("next_cursor")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        return dict(daily)

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
    ) -> list[ExtractedMetric]:
        stage_group_mapping: dict[str, list[str]] = credentials.get(
            "stage_group_mapping",
            {},
        )
        known_groups: list[str] = credentials.get("known_groups", [])
        known_groups_set: set[str] = set(known_groups)

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
                    "mailerlite_new_group_detected",
                    group_id=gid,
                    name=grp.get("name", ""),
                    auto_assign="nurture",
                )
                stage_group_mapping.setdefault("nurture", []).append(gid)
                known_groups_set.add(gid)

        # Build reverse lookup: group_id -> stage
        group_to_stage: dict[str, str] = {}
        for stg, gids in stage_group_mapping.items():
            for gid in gids:
                group_to_stage[str(gid)] = stg

        # 2. Fetch sent campaigns (paginated, newest first)
        campaigns = await self._fetch_sent_campaigns(
            client,
            headers,
            start_date,
            end_date,
        )

        # 3. Filter campaigns that match the requested stage
        matched_campaigns: list[dict] = []
        for campaign in campaigns:
            campaign_stage = self._classify_campaign_stage(
                campaign,
                group_to_stage,
            )
            if campaign_stage == stage:
                matched_campaigns.append(campaign)

        if not matched_campaigns:
            logger.info(
                "mailerlite_no_campaigns",
                stage=stage,
                start_date=str(start_date),
                end_date=str(end_date),
            )
            return []

        # 4. Group campaigns by day and aggregate per day
        from collections import defaultdict

        daily_campaigns: dict[date, list[dict]] = defaultdict(list)
        for campaign in matched_campaigns:
            campaign_date = self._get_campaign_date(campaign) or end_date
            daily_campaigns[campaign_date].append(campaign)

        metrics: list[ExtractedMetric] = []
        for day, day_campaigns in sorted(daily_campaigns.items()):
            day_metrics = self._aggregate_campaign_metrics(
                day_campaigns,
                slug,
                day,
                known_groups_set,
            )
            metrics.extend(day_metrics)

        return metrics

    async def _fetch_sent_campaigns(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Fetch sent campaigns within the date range, paginated.

        Uses fallback date chain: finished_at -> sent_at -> created_at
        because finished_at can be null for some campaign types.
        Does NOT rely on server-side sort (not documented in MailerLite API).
        """
        campaigns: list[dict] = []
        page = 1
        total_api_count = 0

        while True:
            url = f"{BASE_URL}/campaigns?filter[status]=sent&limit=50&page={page}"
            resp = await _api_get(client, url, headers)
            body = resp.json()
            data = body.get("data", [])

            if not data:
                break

            total_api_count += len(data)

            for campaign in data:
                campaign_date = self._get_campaign_date(campaign)
                if campaign_date is None:
                    logger.warning(
                        "mailerlite_campaign_no_date",
                        campaign_id=campaign.get("id"),
                        name=campaign.get("name", ""),
                    )
                    continue
                if start_date <= campaign_date <= end_date:
                    campaigns.append(campaign)

            # Check if there are more pages
            total_from_meta = body.get("meta", {}).get("total", 0)
            if page * 50 >= total_from_meta:
                break

            page += 1
            await asyncio.sleep(_RATE_LIMIT_SLEEP)

        logger.info(
            "mailerlite_campaigns_fetched",
            total_from_api=total_api_count,
            matched_date_range=len(campaigns),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        return campaigns

    @staticmethod
    def _get_campaign_date(campaign: dict) -> date | None:
        """Extract the best available date from a campaign.

        Fallback chain: finished_at -> sent_at -> started_at -> created_at.
        """
        for field in ("finished_at", "sent_at", "started_at", "created_at"):
            dt = _parse_iso_date(campaign.get(field))
            if dt is not None:
                return dt.date()
        return None

    def _classify_campaign_stage(
        self,
        campaign: dict,
        group_to_stage: dict[str, str],
    ) -> str:
        """Determine which funnel stage a campaign belongs to based on its targeted groups.

        Default to 'nurture' if no group match.
        """
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

    def _normalize_campaign_stats(self, stats: dict) -> dict[str, tuple]:
        """Apply MAILERLITE_METRIC_MAP to raw campaign stats.

        Returns dict of canonical_name -> (value, unit).
        """
        result: dict[str, tuple] = {}
        for api_field, (canonical_name, unit) in MAILERLITE_METRIC_MAP.items():
            raw = stats.get(api_field)
            if raw is None:
                continue
            if isinstance(raw, dict):
                # MailerLite returns rates as {"float": 0.31, "string": "31.35%"}
                raw = raw.get("float", 0.0)
            value = float(raw)
            # MailerLite percentages come as 0.0-1.0 — convert to 0-100
            if unit == "percentage":
                value *= 100
            result[canonical_name] = (value, unit)
        return result

    def _aggregate_campaign_metrics(
        self,
        campaigns: list[dict],
        slug: str,
        metric_date: date,
        known_groups_set: set[str],
    ) -> list[ExtractedMetric]:
        """Aggregate metrics across matched campaigns and compute derived metrics."""
        totals: dict[str, float] = {}
        rate_sums: dict[str, float] = {}
        campaign_count = len(campaigns)

        # Build per-campaign metadata for the Campanas tab
        campaigns_metadata = self._build_campaigns_metadata(
            campaigns,
            totals,
            rate_sums,
        )

        metrics: list[ExtractedMetric] = []

        # --- Per-campaign rows (for the Campañas tab) ---
        self._emit_per_campaign_rows(
            campaigns,
            campaigns_metadata,
            slug,
            metric_date,
            metrics,
        )

        # --- Daily aggregate rows (for trend charts) ---
        self._emit_daily_aggregates(
            totals,
            rate_sums,
            campaign_count,
            slug,
            metric_date,
            metrics,
        )

        # --- Derived rates ---
        self._emit_derived_rates(totals, slug, metric_date, metrics)

        # Attach campaign metadata to all metrics for the Campanas tab
        if metrics and campaigns_metadata:
            for metric in metrics:
                metric.extra["campaigns"] = campaigns_metadata

        # Attach updated config info for traceability (new group auto-mapping)
        if metrics and known_groups_set:
            metrics[0].extra["updated_known_groups"] = sorted(known_groups_set)

        return metrics

    def _build_campaigns_metadata(
        self,
        campaigns: list[dict],
        totals: dict[str, float],
        rate_sums: dict[str, float],
    ) -> list[dict[str, str | None]]:
        """Build per-campaign metadata and accumulate totals/rate_sums."""
        campaigns_metadata: list[dict[str, str | None]] = []
        for campaign in campaigns:
            stats = campaign.get("stats", campaign.get("campaign_stats", {}))
            normalized = self._normalize_campaign_stats(stats)

            for name, (value, unit) in normalized.items():
                if unit == "percentage":
                    rate_sums[name] = rate_sums.get(name, 0.0) + value
                else:
                    totals[name] = totals.get(name, 0.0) + value

            campaign_name = campaign.get("name", "")
            emails_list = campaign.get("emails") or [{}]
            first_email = emails_list[0] if emails_list else {}
            campaign_subject = first_email.get("subject", "")
            screenshot_url = first_email.get("screenshot_url")
            preview_url = first_email.get("preview_url")
            campaign_type = classify_campaign_type(campaign_name, campaign_subject)
            campaigns_metadata.append(
                {
                    "campaign_name": campaign_name,
                    "campaign_subject": campaign_subject,
                    "campaign_type": campaign_type,
                    "screenshot_url": screenshot_url,
                    "preview_url": preview_url,
                },
            )
        return campaigns_metadata

    def _emit_per_campaign_rows(
        self,
        campaigns: list[dict],
        campaigns_metadata: list[dict[str, str | None]],
        slug: str,
        metric_date: date,
        metrics: list[ExtractedMetric],
    ) -> None:
        """Emit per-campaign metric rows for the Campañas tab."""
        for campaign, meta in zip(campaigns, campaigns_metadata, strict=True):
            cid = str(campaign.get("id", ""))
            if not cid:
                continue
            stats = campaign.get("stats", campaign.get("campaign_stats", {}))
            normalized = self._normalize_campaign_stats(stats)
            for name, (value, unit) in normalized.items():
                metrics.append(
                    ExtractedMetric(
                        provider="mailerlite",
                        channel_slug=slug,
                        metric_name=name,
                        value=value,
                        unit=unit,
                        date=metric_date,
                        campaign_id=cid,
                        extra={
                            "campaign_name": meta["campaign_name"],
                            "campaign_subject": meta["campaign_subject"],
                            "campaign_type": meta["campaign_type"],
                            "screenshot_url": meta["screenshot_url"],
                            "preview_url": meta["preview_url"],
                        },
                    ),
                )

    @staticmethod
    def _emit_daily_aggregates(
        totals: dict[str, float],
        rate_sums: dict[str, float],
        campaign_count: int,
        slug: str,
        metric_date: date,
        metrics: list[ExtractedMetric],
    ) -> None:
        """Emit summed count metrics and averaged rate metrics."""
        for name, value in totals.items():
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name=name,
                    value=value,
                    unit="count",
                    date=metric_date,
                ),
            )

        if campaign_count > 0:
            for name, total in rate_sums.items():
                metrics.append(
                    ExtractedMetric(
                        provider="mailerlite",
                        channel_slug=slug,
                        metric_name=name,
                        value=total / campaign_count,
                        unit="percentage",
                        date=metric_date,
                    ),
                )

    @staticmethod
    def _emit_derived_rates(
        totals: dict[str, float],
        slug: str,
        metric_date: date,
        metrics: list[ExtractedMetric],
    ) -> None:
        """Derive bounce_rate, unsubscribe_rate, and reactivation_rate."""
        sent = totals.get("emails_sent", 0.0)
        if sent <= 0:
            return

        hard = totals.get("hard_bounces", 0.0)
        soft = totals.get("soft_bounces", 0.0)
        metrics.append(
            ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="bounce_rate",
                value=(hard + soft) / sent * 100,
                unit="percentage",
                date=metric_date,
            ),
        )

        unsubs = totals.get("unsubscribes", 0.0)
        metrics.append(
            ExtractedMetric(
                provider="mailerlite",
                channel_slug=slug,
                metric_name="unsubscribe_rate",
                value=unsubs / sent * 100,
                unit="percentage",
                date=metric_date,
            ),
        )

        # For retention stage: derive reactivation_rate
        if slug == STAGE_TO_SLUG.get("retention"):
            opens = totals.get("unique_opens", 0.0)
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="reactivation_rate",
                    value=opens / sent * 100,
                    unit="percentage",
                    date=metric_date,
                ),
            )

    # ------------------------------------------------------------------
    # AUTOMATION extraction (per-automation detail rows)
    # ------------------------------------------------------------------

    async def _extract_automations(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        credentials: dict,
        start_date: date,
        end_date: date,
        slug: str,
    ) -> list[ExtractedMetric]:
        """Extract per-automation metric rows from Mailerlite.

        Each automation gets multiple ExtractedMetric rows with
        campaign_id = automation_id and metadata in extra (source=automation).
        Stats come directly from GET /automations (no per-automation API calls).
        """
        url = f"{BASE_URL}/automations?filter[enabled]=true&limit=100"
        resp = await _api_get(client, url, headers)
        automations = resp.json().get("data", [])
        await asyncio.sleep(_RATE_LIMIT_SLEEP)

        if not automations:
            logger.info("mailerlite_no_automations", slug=slug)
            return []

        metrics: list[ExtractedMetric] = []
        metric_date = end_date

        for auto in automations:
            auto_id = str(auto.get("id", ""))
            if not auto_id:
                continue

            name = auto.get("name", "")
            stats = auto.get("stats", {})
            steps = auto.get("steps", [])

            sent = int(stats.get("sent", 0))
            completed = int(stats.get("completed_subscribers_count", 0))
            in_queue = int(stats.get("subscribers_in_queue_count", 0))

            # Parse rates (MailerLite returns {"float": 0.625, "string": "62.5%"})
            raw_open = stats.get("open_rate", 0.0)
            raw_click = stats.get("click_rate", 0.0)
            raw_ctor = stats.get("click_to_open_rate", 0.0)
            open_rate = float(
                raw_open.get("float", 0.0) if isinstance(raw_open, dict) else raw_open,
            )
            click_rate = float(
                raw_click.get("float", 0.0) if isinstance(raw_click, dict) else raw_click,
            )
            ctor = float(
                raw_ctor.get("float", 0.0) if isinstance(raw_ctor, dict) else raw_ctor,
            )
            unsubs = int(stats.get("unsubscribes_count", 0))

            extra = {
                "source": "automation",
                "automation_name": name,
                "automation_status": "active" if auto.get("enabled", True) else "paused",
                "automation_type": classify_automation_type(name),
                "completed_subscribers": completed,
                "subscribers_in_queue": in_queue,
                "steps_count": len(steps),
                "steps": _extract_step_data(steps),
            }

            # Per-automation metric rows
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="emails_sent",
                    value=float(sent),
                    unit="count",
                    date=metric_date,
                    campaign_id=auto_id,
                    extra=dict(extra),
                ),
            )
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="open_rate",
                    value=open_rate * 100,
                    unit="percentage",
                    date=metric_date,
                    campaign_id=auto_id,
                    extra=dict(extra),
                ),
            )
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="click_rate",
                    value=click_rate * 100,
                    unit="percentage",
                    date=metric_date,
                    campaign_id=auto_id,
                    extra=dict(extra),
                ),
            )
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="click_to_open_rate",
                    value=ctor * 100,
                    unit="percentage",
                    date=metric_date,
                    campaign_id=auto_id,
                    extra=dict(extra),
                ),
            )
            metrics.append(
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug=slug,
                    metric_name="unsubscribes",
                    value=float(unsubs),
                    unit="count",
                    date=metric_date,
                    campaign_id=auto_id,
                    extra=dict(extra),
                ),
            )

        logger.info(
            "mailerlite_automations_extracted",
            slug=slug,
            automation_count=len([a for a in automations if a.get("id")]),
            metric_count=len(metrics),
        )

        return metrics
