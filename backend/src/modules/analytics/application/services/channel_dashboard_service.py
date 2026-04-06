"""Channel dashboard service -- assembles per-channel detail views."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    AdFunnelDTO,
    BenchmarkRangeDTO,
    ChannelDashboardDTO,
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
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)

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
            (end_clicks / end_impressions) * 100, 2
        )

    return metrics


class ChannelDashboardService:
    """Builds the channel dashboard response with KPIs, time series, funnel, and alerts."""

    def __init__(
        self,
        db: Session,
        brand_port: BrandReadPort | None = None,
    ) -> None:
        self.repo = OfficialMetricsRepository(db)
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
        today = date.today()
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

        # Fetch data in parallel via thread pool (sync repo)
        current_metrics, previous_metrics, daily_data = await asyncio.gather(
            asyncio.to_thread(
                self.repo.get_channel_metrics_for_period,
                tenant_id,
                channel_slug,
                start,
                today,
            ),
            asyncio.to_thread(
                self.repo.get_channel_metrics_for_period,
                tenant_id,
                channel_slug,
                prev_start,
                prev_end,
            ),
            asyncio.to_thread(
                self.repo.get_channel_daily_metrics,
                tenant_id,
                channel_slug,
                timeseries_metrics,
                start,
                today,
            ),
        )

        # Compute derived metrics (e.g. ig_engagement_rate)
        _compute_derived_metrics(current_metrics)
        _compute_derived_metrics(previous_metrics)

        # Build KPIs
        kpis = self._build_kpis(current_metrics, previous_metrics, industry, config)

        # Build time series
        time_series = self._build_time_series(daily_data)

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

    def _build_kpis(
        self,
        current: dict[str, float],
        previous: dict[str, float],
        industry: IndustryCategory,
        config: ChannelDashboardConfig | None = None,
    ) -> list[MetricKpiDTO]:
        """Build KPI cards with deltas and benchmarks."""
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

            defn = get_metric_def(metric_name)
            display_name = defn.display_name if defn else metric_name
            unit = defn.unit.value if defn else "count"
            higher_is_better = defn.higher_is_better if defn else True

            # Benchmark lookup
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
                )
            )

        return kpis

    def _build_time_series(
        self,
        daily_data: list[tuple[date, str, float]],
    ) -> list[MetricTimeSeriesDTO]:
        """Group daily data into per-metric time series."""
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
                )
            )

        return series

    def _build_funnel(
        self,
        metrics: dict[str, float],
        config: ChannelDashboardConfig | None = None,
    ) -> AdFunnelDTO:
        """Build the ad conversion funnel with step-to-step rates."""
        fallback_config = _CHANNEL_CONFIGS.get("meta-ads", _DEFAULT_CONFIG)
        funnel_steps = config.funnel_steps if config else fallback_config.funnel_steps
        steps: list[FunnelStepDTO] = []
        prev_value: float | None = None

        for label, metric_name in funnel_steps:
            value = metrics.get(metric_name, 0.0)
            conv_rate = None
            if prev_value is not None and prev_value > 0:
                conv_rate = round((value / prev_value) * 100, 2)

            steps.append(
                FunnelStepDTO(
                    label=label,
                    metric_name=metric_name,
                    value=round(value, 2),
                    conversion_rate_from_previous=conv_rate,
                )
            )
            prev_value = value

        return AdFunnelDTO(steps=steps)

    def _check_frequency(
        self,
        metrics: dict[str, float],
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
