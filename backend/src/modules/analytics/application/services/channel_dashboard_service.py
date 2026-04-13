"""Channel dashboard service -- assembles per-channel detail views."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import text

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    AdFunnelDTO,
    BenchmarkRangeDTO,
    ChannelDashboardDTO,
    DemographicsDTO,
    DemographicSegmentDTO,
    FrequencyAlertDTO,
    FunnelStepDTO,
    MetricKpiDTO,
    MetricTimeSeriesDTO,
    TimeSeriesDataPointDTO,
)
from src.modules.analytics.domain.industry_benchmarks import (
    FREQUENCY_FATIGUE_THRESHOLD,
    IndustryCategory,
    get_benchmarks,
    normalize_industry,
)
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.domain.metric_resolver import ALIAS_MAP, MetricResolver
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.period_metrics_repository import (
    PeriodMetricsRepository,
)
from src.shared.domain.datetime_utils import utc_today

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.ports import BrandReadPort

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Per-channel dashboard configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChannelDashboardConfig:
    """Declarative configuration for a channel's dashboard layout."""

    channel_name: str
    hero_metrics: list[str] = field(default_factory=list)
    timeseries_metrics: list[str] = field(default_factory=list)
    funnel_steps: list[tuple[str, str]] = field(default_factory=list)
    has_frequency_alert: bool = False


_CHANNEL_CONFIGS: dict[str, ChannelDashboardConfig] = {
    "meta-ads": ChannelDashboardConfig(
        channel_name="Meta Ads",
        hero_metrics=[
            "spend",
            "ROAS",
            "CPL",
            "CTR",
            "CPC",
            "CPM",
            "CPA",
            "conversions",
        ],
        timeseries_metrics=[
            "spend",
            "impressions",
            "clicks",
            "reach",
            "conversions",
            "ROAS",
            "CPC",
            "CPM",
            "CPL",
        ],
        funnel_steps=[
            ("Impresiones", "impressions"),
            ("Clics", "clicks"),
            ("Vistas de Landing", "meta_landing_page_views"),
            ("Leads", "meta_leads"),
            ("Conversiones", "conversions"),
        ],
        has_frequency_alert=True,
    ),
    "ig-organic": ChannelDashboardConfig(
        channel_name="Instagram Orgánico",
        hero_metrics=[
            "total_interactions",
            "ig_views",
            "ig_follows_and_unfollows",
            "ig_follows_gained",
            "ig_follows_lost",
            "ig_engagement_rate",
        ],
        timeseries_metrics=[
            "total_interactions",
            "ig_views",
            "ig_likes",
            "ig_comments",
            "ig_shares",
            "ig_saves",
            "ig_follows_and_unfollows",
            "ig_follows_gained",
            "ig_follows_lost",
            "ig_profile_links_taps",
        ],
        funnel_steps=[
            ("Vistas", "ig_views"),
            ("Interacciones", "total_interactions"),
            ("Compartidos", "ig_shares"),
            ("Taps en Perfil", "ig_profile_links_taps"),
        ],
        has_frequency_alert=False,
    ),
    "yt-organic": ChannelDashboardConfig(
        channel_name="YouTube Orgánico",
        hero_metrics=[
            "views",
            "watch_time_minutes",
            "subscribers_gained",
            "avg_view_percentage",
        ],
        timeseries_metrics=[
            "views",
            "watch_time_minutes",
            "subscribers_gained",
            "subscribers_lost",
            "avg_view_duration",
            "avg_view_percentage",
            "engagement",
            "comments",
            "shares",
            "card_clicks",
            "end_screen_clicks",
        ],
        funnel_steps=[
            ("Vistas", "views"),
            ("Engagement", "engagement"),
            ("Suscriptores", "subscribers_gained"),
            ("Clics Tarjetas", "card_clicks"),
        ],
        has_frequency_alert=False,
    ),
    "website-total": ChannelDashboardConfig(
        channel_name="Tu Sitio Web",
        hero_metrics=[
            "sessions",
            "engagementRate",
            "bounceRate",
            "conversions",
            "averageSessionDuration",
            "users",
        ],
        timeseries_metrics=[
            "sessions",
            "engagedSessions",
            "bounceRate",
            "conversions",
            "engagementRate",
            "users",
        ],
        funnel_steps=[
            ("Sesiones", "sessions"),
            ("Comprometidas", "engagedSessions"),
            ("Pág. Vistas", "screenPageViews"),
            ("Conversiones", "conversions"),
        ],
        has_frequency_alert=False,
    ),
    "email-nurture": ChannelDashboardConfig(
        channel_name="Email Marketing",
        hero_metrics=[
            "open_rate",
            "click_rate",
            "emails_sent",
            "active_subscribers",
        ],
        timeseries_metrics=[
            "emails_sent",
            "unique_opens",
            "unique_clicks",
            "open_rate",
            "click_rate",
            "click_to_open_rate",
            "hard_bounces",
            "soft_bounces",
            "unsubscribes",
            "forwards",
            "new_subscribers",
            "spam_reports",
            "automation_completed",
            "completion_rate",
        ],
        funnel_steps=[
            ("Enviados", "emails_sent"),
            ("Aperturas", "unique_opens"),
            ("Clics", "unique_clicks"),
            ("Conversiones", "form_conversions"),
        ],
        has_frequency_alert=False,
    ),
}

_DEFAULT_CONFIG = ChannelDashboardConfig(channel_name="Canal")

# Channel slug -> human-readable name (kept for backward compat)
_CHANNEL_NAMES: dict[str, str] = {
    "meta-ads": "Meta Ads",
    "google-ads": "Google Ads",
    "yt-ads": "YouTube Ads",
    "tiktok-ads": "TikTok Ads",
    "ig-organic": "Instagram Orgánico",
    "yt-organic": "YouTube Orgánico",
    "email-nurture": "Email Marketing",
    "website-total": "Tu Sitio Web",
}

# Period string -> days
_PERIOD_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "last_30_days": 30,
}


# ---------------------------------------------------------------------------
# Derived metric computation
# ---------------------------------------------------------------------------


def _compute_derived_metrics(metrics: dict[str, float]) -> dict[str, float]:
    """Add in-memory derived metrics that are not stored in DB.

    Currently computes:
    - ig_engagement_rate: total_interactions / ig_views * 100  (IG Organic)
    - card_click_rate: card_clicks / card_impressions * 100    (YouTube)
    - end_screen_click_rate: end_screen_clicks / end_screen_impressions * 100  (YouTube)
    """
    # IG Organic: engagement rate
    ig_views = metrics.get("ig_views", 0)
    interactions = metrics.get("total_interactions", 0)
    if ig_views > 0:
        metrics["ig_engagement_rate"] = round((interactions / ig_views) * 100, 2)
    else:
        metrics["ig_engagement_rate"] = 0.0

    # YouTube: Card CTR
    card_clicks = metrics.get("card_clicks", 0)
    card_impressions = metrics.get("card_impressions", 0)
    if card_impressions > 0:
        metrics["card_click_rate"] = round((card_clicks / card_impressions) * 100, 2)

    # YouTube: End Screen CTR
    end_clicks = metrics.get("end_screen_clicks", 0)
    end_impressions = metrics.get("end_screen_impressions", 0)
    if end_impressions > 0:
        metrics["end_screen_click_rate"] = round(
            (end_clicks / end_impressions) * 100,
            2,
        )

    # Email: CTOR, bounce_rate, unsubscribe_rate
    emails_sent_val = metrics.get("emails_sent", 0)
    unique_opens_val = metrics.get("unique_opens", 0)
    unique_clicks_val = metrics.get("unique_clicks", 0)
    if unique_opens_val > 0 and "click_to_open_rate" not in metrics:
        metrics["click_to_open_rate"] = round(
            (unique_clicks_val / unique_opens_val) * 100,
            2,
        )
    hard_b = metrics.get("hard_bounces", 0)
    soft_b = metrics.get("soft_bounces", 0)
    if emails_sent_val > 0:
        if "bounce_rate" not in metrics:
            metrics["bounce_rate"] = round(
                ((hard_b + soft_b) / emails_sent_val) * 100,
                2,
            )
        if "unsubscribe_rate" not in metrics:
            metrics["unsubscribe_rate"] = round(
                (metrics.get("unsubscribes", 0) / emails_sent_val) * 100,
                2,
            )

    return metrics


class ChannelDashboardService:
    """Builds the channel dashboard response with KPIs, time series, funnel, and alerts."""

    # NON_AGGREGABLE metrics that should be overridden with period_metrics
    _PERIOD_OVERRIDE_METRICS = ("reach",)

    def __init__(
        self,
        db: Session,
        brand_port: BrandReadPort | None = None,
    ) -> None:
        self.repo = OfficialMetricsRepository(db)
        self.period_repo = PeriodMetricsRepository(db)
        self.brand_port = brand_port

    async def get_dashboard(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str = "30d",
    ) -> ChannelDashboardDTO:
        """Assemble the full channel dashboard."""
        config = _CHANNEL_CONFIGS.get(channel_slug, _DEFAULT_CONFIG)
        days = _PERIOD_DAYS.get(period, 30)
        today = utc_today()
        start = today - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        # Resolve industry for benchmarks
        industry = IndustryCategory.GENERAL
        if self.brand_port:
            industry_text = await self.brand_port.get_industry(tenant_id)
            industry = normalize_industry(industry_text)

        logger.info(
            "channel_dashboard_requested",
            tenant_id=str(tenant_id),
            channel_slug=channel_slug,
            period=period,
            industry=industry.value,
        )

        # Use channel-specific timeseries metrics when available
        timeseries_metrics = config.timeseries_metrics or []

        # Fetch raw daily rows in parallel via thread pool (sync repo)
        current_raw, previous_raw, daily_raw = await asyncio.gather(
            asyncio.to_thread(
                self.repo.get_channel_raw_daily_rows,
                tenant_id,
                channel_slug,
                start,
                today,
            ),
            asyncio.to_thread(
                self.repo.get_channel_raw_daily_rows,
                tenant_id,
                channel_slug,
                prev_start,
                prev_end,
            ),
            asyncio.to_thread(
                self.repo.get_channel_raw_daily_rows,
                tenant_id,
                channel_slug,
                start,
                today,
            ),
        )

        # Use MetricResolver for correct aggregation (fixes double-counting,
        # derived metric recalculation, and alias mapping)
        resolver = MetricResolver()

        # Resolve period KPIs via MetricResolver
        all_requested = list(set(config.hero_metrics) | set(timeseries_metrics))
        current_metrics = resolver.resolve_period_kpis(current_raw, all_requested)
        previous_metrics = resolver.resolve_period_kpis(previous_raw, all_requested)

        # Also compute channel-specific derived metrics not in the catalog
        # (IG engagement rate, card click rate, etc.)
        current_flat = {k: v for k, v in current_metrics.items() if v is not None}
        previous_flat = {k: v for k, v in previous_metrics.items() if v is not None}
        _compute_derived_metrics(current_flat)
        _compute_derived_metrics(previous_flat)
        # Merge back computed derived metrics
        current_metrics.update(current_flat)
        previous_metrics.update(previous_flat)

        # Override NON_AGGREGABLE metrics with period_metrics if available
        await self._apply_period_overrides(
            current_flat,
            tenant_id,
            channel_slug,
            start,
            today,
        )
        await self._apply_period_overrides(
            previous_flat,
            tenant_id,
            channel_slug,
            prev_start,
            prev_end,
        )
        current_metrics.update(current_flat)
        previous_metrics.update(previous_flat)

        # Resolve aliases and recalculate derived metrics (ROAS, CTR, CPC, etc.)
        all_metric_names = list(config.hero_metrics) + [
            m for m in config.timeseries_metrics if m not in config.hero_metrics
        ]
        resolved_current = resolver.resolve_from_aggregated(
            current_metrics,
            all_metric_names,
        )
        resolved_previous = resolver.resolve_from_aggregated(
            previous_metrics,
            all_metric_names,
        )
        # Merge resolved values into metrics dicts (aliases get added as keys)
        for name, val in resolved_current.items():
            if val is not None:
                current_metrics[name] = val
        for name, val in resolved_previous.items():
            if val is not None:
                previous_metrics[name] = val

        # Detect channel currency for monetary KPIs
        try:
            currency_row = self.repo.db.execute(
                text("""
                    SELECT currency FROM official_metrics
                    WHERE tenant_id = :tenant_id
                      AND channel_slug = :channel_slug
                      AND currency IS NOT NULL
                    LIMIT 1
                """),
                {"tenant_id": str(tenant_id), "channel_slug": channel_slug},
            ).fetchone()
            raw = currency_row._mapping["currency"] if currency_row else None
            channel_currency = raw if isinstance(raw, str) else None
        except (TypeError, ValueError):
            channel_currency = None

        # Build KPIs
        kpis = self._build_kpis(
            current_metrics,
            previous_metrics,
            industry,
            config,
            channel_currency,
        )

        # Build time series using MetricResolver for correct daily derivation
        resolved_daily = resolver.resolve_daily_timeseries(
            daily_raw,
            timeseries_metrics,
        )
        time_series = self._build_time_series_from_resolved(resolved_daily)

        # Build funnel
        funnel = self._build_funnel(current_metrics, config)

        # Frequency alert
        frequency_alert = (
            self._check_frequency(current_metrics)
            if config.has_frequency_alert
            else None
        )

        channel_name = _CHANNEL_NAMES.get(channel_slug, config.channel_name)

        return ChannelDashboardDTO(
            channel_slug=channel_slug,
            channel_name=channel_name,
            industry_category=industry.value,
            period=period,
            kpis=kpis,
            time_series=time_series,
            funnel=funnel,
            frequency_alert=frequency_alert,
        )

    _resolver = MetricResolver()

    async def _apply_period_overrides(
        self,
        metrics: dict[str, float],
        tenant_id: UUID,
        channel_slug: str,
        start_date: date,
        end_date: date,
    ) -> None:
        """Override NON_AGGREGABLE metrics with period_metrics values.

        For metrics like reach (unique people), summing daily values overcounts.
        If period_metrics has a row covering the requested date range, use that
        instead. Then recompute frequency = impressions / reach.
        """
        for metric_name in self._PERIOD_OVERRIDE_METRICS:
            if metric_name not in metrics:
                continue

            period_value = await asyncio.to_thread(
                self.period_repo.get_best_period_metric,
                tenant_id,
                channel_slug,
                metric_name,
                start_date,
                end_date,
            )

            if period_value is not None:
                logger.info(
                    "period_metric_override",
                    metric_name=metric_name,
                    daily_value=metrics[metric_name],
                    period_value=period_value,
                    tenant_id=str(tenant_id),
                    channel_slug=channel_slug,
                )
                metrics[metric_name] = period_value

        # Recompute frequency from (potentially overridden) reach + summed impressions
        reach_val = metrics.get("reach", 0)
        impressions_sum = metrics.get("impressions", 0)
        if reach_val > 0 and impressions_sum > 0:
            metrics["frequency"] = round(impressions_sum / reach_val, 2)

    def _build_kpis(
        self,
        current: dict[str, float | None],
        previous: dict[str, float | None],
        industry: IndustryCategory,
        config: ChannelDashboardConfig | None = None,
        channel_currency: str | None = None,
    ) -> list[MetricKpiDTO]:
        """Build KPI cards with deltas and benchmarks.

        Uses ALIAS_MAP to resolve hero_metrics names (e.g. "ROAS") to
        canonical catalog names (e.g. "meta_purchase_roas") for display_name
        and unit lookup, while keeping the original name for benchmark lookup
        (benchmarks use the alias names like "CTR", "ROAS").
        """
        fallback_config = _CHANNEL_CONFIGS.get("meta-ads", _DEFAULT_CONFIG)
        hero_metrics = config.hero_metrics if config else fallback_config.hero_metrics
        kpis: list[MetricKpiDTO] = []
        for metric_name in hero_metrics:
            current_val = current.get(metric_name)
            if current_val is None:
                continue

            prev_val = previous.get(metric_name)
            delta_pct: float | None = None
            delta_abs: float | None = None
            if prev_val is not None and prev_val != 0:
                delta_abs = current_val - prev_val
                delta_pct = round((delta_abs / prev_val) * 100, 1)

            # Resolve alias to canonical name for catalog lookup
            canonical = ALIAS_MAP.get(metric_name, metric_name)
            defn = get_metric_def(canonical)
            display_name = defn.display_name if defn else metric_name
            unit = defn.unit.value if defn else "count"
            higher_is_better = defn.higher_is_better if defn else True

            # Benchmark lookup — benchmarks use alias names (CTR, ROAS, etc.)
            benchmark_entry = get_benchmarks(industry, metric_name)
            benchmark = None
            if benchmark_entry:
                benchmark = BenchmarkRangeDTO(
                    low=benchmark_entry.low,
                    median=benchmark_entry.median,
                    high=benchmark_entry.high,
                    unit=benchmark_entry.unit,
                    interpretation=benchmark_entry.interpretation_es,
                )

            kpis.append(
                MetricKpiDTO(
                    metric_name=metric_name,
                    display_name=display_name,
                    current_value=round(current_val, 2),
                    previous_value=round(prev_val, 2) if prev_val is not None else None,
                    delta_percent=delta_pct,
                    delta_absolute=round(delta_abs, 2)
                    if delta_abs is not None
                    else None,
                    unit=unit,
                    higher_is_better=higher_is_better,
                    benchmark=benchmark,
                    currency=channel_currency if unit == "currency" else None,
                ),
            )

        return kpis

    @staticmethod
    def _resolve_daily_fetch_metrics(
        resolver: MetricResolver,
        timeseries_metrics: list[str],
    ) -> list[str]:
        """Expand timeseries metric names to include component metrics.

        DERIVED/WEIGHTED_AVERAGE metrics (CPC, CPM, CTR, ROAS) don't exist
        as individual rows in the DB — they are recalculated from component
        metrics (spend, clicks, impressions, etc.). This method collects
        all canonical metric names + their components for the DB query.
        """
        from src.modules.analytics.domain.metric_resolver import (
            _get_formula_components,
        )

        fetch_set: set[str] = set()
        for m in timeseries_metrics:
            canonical = resolver.resolve_alias(m)
            fetch_set.add(canonical)
            defn = get_metric_def(canonical)
            if defn is not None:
                components = _get_formula_components(defn)
                if components:
                    fetch_set.add(components[0])  # numerator
                    fetch_set.add(components[1])  # denominator
        return list(fetch_set)

    def _build_time_series(
        self,
        daily_data: list[tuple[date, str, float]],
    ) -> list[MetricTimeSeriesDTO]:
        """Group daily data into per-metric time series (legacy, kept for compat)."""
        grouped: dict[str, list[tuple[date, float]]] = defaultdict(list)
        for metric_date, metric_name, value in daily_data:
            grouped[metric_name].append((metric_date, value))

        series: list[MetricTimeSeriesDTO] = []
        for metric_name, points in grouped.items():
            defn = get_metric_def(metric_name)
            display_name = defn.display_name if defn else metric_name
            unit = defn.unit.value if defn else "count"

            sorted_points = sorted(points, key=lambda x: x[0])
            data_points = [
                TimeSeriesDataPointDTO(date=d.isoformat(), value=round(v, 2))
                for d, v in sorted_points
            ]

            series.append(
                MetricTimeSeriesDTO(
                    metric_name=metric_name,
                    display_name=display_name,
                    unit=unit,
                    data_points=data_points,
                ),
            )

        return series

    def _build_time_series_from_resolved(
        self,
        resolved: dict[str, list[tuple[date, float]]],
    ) -> list[MetricTimeSeriesDTO]:
        """Build time series DTOs from MetricResolver output.

        The resolver returns {metric_name: [(date, value), ...]} with
        aliases preserved and derived metrics already recalculated per-day.
        """
        series: list[MetricTimeSeriesDTO] = []
        for metric_name, points in resolved.items():
            if not points:
                continue

            canonical = ALIAS_MAP.get(metric_name, metric_name)
            defn = get_metric_def(canonical)
            display_name = defn.display_name if defn else metric_name
            unit = defn.unit.value if defn else "count"

            sorted_points = sorted(points, key=lambda x: x[0])
            data_points = [
                TimeSeriesDataPointDTO(date=d.isoformat(), value=round(v, 2))
                for d, v in sorted_points
            ]

            series.append(
                MetricTimeSeriesDTO(
                    metric_name=metric_name,
                    display_name=display_name,
                    unit=unit,
                    data_points=data_points,
                ),
            )

        return series

    def _build_funnel(
        self,
        metrics: dict[str, float | None],
        config: ChannelDashboardConfig | None = None,
    ) -> AdFunnelDTO:
        """Build the ad conversion funnel with step-to-step rates."""
        fallback_config = _CHANNEL_CONFIGS.get("meta-ads", _DEFAULT_CONFIG)
        funnel_steps = config.funnel_steps if config else fallback_config.funnel_steps
        steps: list[FunnelStepDTO] = []
        prev_value: float | None = None

        for label, metric_name in funnel_steps:
            raw_value = metrics.get(metric_name)
            value = raw_value if raw_value is not None else 0.0
            conv_rate = None
            if prev_value is not None and prev_value > 0:
                conv_rate = round((value / prev_value) * 100, 2)

            steps.append(
                FunnelStepDTO(
                    label=label,
                    metric_name=metric_name,
                    value=round(value, 2),
                    conversion_rate_from_previous=conv_rate,
                ),
            )
            prev_value = value

        return AdFunnelDTO(steps=steps)

    def _check_frequency(
        self,
        metrics: dict[str, float | None],
    ) -> FrequencyAlertDTO | None:
        """Check if ad frequency exceeds fatigue thresholds."""
        freq = metrics.get("frequency")
        if freq is None:
            return None

        if freq >= 5.0:
            return FrequencyAlertDTO(
                current_value=round(freq, 2),
                severity="critical",
                message="Fatiga de audiencia -- rotar creativos urgentemente",
            )
        if freq >= FREQUENCY_FATIGUE_THRESHOLD:
            return FrequencyAlertDTO(
                current_value=round(freq, 2),
                severity="warning",
                message="Frecuencia elevada, considerar rotar creativos",
            )

        return None

    # ------------------------------------------------------------------
    # Demographics breakdown
    # ------------------------------------------------------------------

    _DEMOGRAPHICS_SQL = text("""
        SELECT metric_name, extra
        FROM official_metrics
        WHERE tenant_id = :tenant_id
          AND channel_slug = :channel_slug
          AND metric_name IN (
              'meta_reach_by_age',
              'meta_reach_by_gender',
              'meta_reach_by_placement'
          )
          AND metric_date >= CURRENT_DATE - :days_back * INTERVAL '1 day'
        ORDER BY metric_date DESC
    """)

    _METRIC_TO_CATEGORY: dict[str, str] = {
        "meta_reach_by_age": "age",
        "meta_reach_by_gender": "gender",
        "meta_reach_by_placement": "placement",
    }

    def get_demographics(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str = "30d",
    ) -> DemographicsDTO:
        """Parse audience breakdown from official_metrics extra JSON."""
        days = _PERIOD_DAYS.get(period, 30)

        rows = self.repo.db.execute(
            self._DEMOGRAPHICS_SQL,
            {
                "tenant_id": str(tenant_id),
                "channel_slug": channel_slug,
                "days_back": days,
            },
        ).fetchall()

        # Collect the most recent breakdown per category
        seen_categories: set[str] = set()
        age_segments: list[DemographicSegmentDTO] = []
        gender_segments: list[DemographicSegmentDTO] = []
        placement_segments: list[DemographicSegmentDTO] = []

        category_map = {
            "age": age_segments,
            "gender": gender_segments,
            "placement": placement_segments,
        }

        for row in rows:
            r = row._mapping
            metric_name = r["metric_name"]
            category = self._METRIC_TO_CATEGORY.get(metric_name)
            if category is None or category in seen_categories:
                continue  # skip duplicates (we ORDER BY metric_date DESC)

            extra_raw = r["extra"]
            if isinstance(extra_raw, str):
                import json

                try:
                    extra = json.loads(extra_raw)
                except (json.JSONDecodeError, TypeError):
                    extra = {}
            elif isinstance(extra_raw, dict):
                extra = extra_raw
            else:
                extra = {}

            breakdowns = extra.get("breakdowns", [])
            if not breakdowns:
                continue

            segments = self._parse_breakdown_segments(breakdowns)
            if segments:
                category_map[category].extend(segments)
                seen_categories.add(category)

        return DemographicsDTO(
            age=age_segments,
            gender=gender_segments,
            placement=placement_segments,
        )

    @staticmethod
    def _parse_breakdown_segments(
        breakdowns: list[dict],
    ) -> list[DemographicSegmentDTO]:
        """Convert raw breakdown entries to DemographicSegmentDTO with percentages."""
        total = sum(entry.get("value", 0) for entry in breakdowns)
        segments: list[DemographicSegmentDTO] = []
        for entry in breakdowns:
            label = entry.get("dimension_values", ["unknown"])[0]
            value = float(entry.get("value", 0))
            pct = round((value / total) * 100, 1) if total > 0 else 0.0
            segments.append(
                DemographicSegmentDTO(
                    label=label,
                    value=value,
                    percentage=pct,
                ),
            )
        return segments
