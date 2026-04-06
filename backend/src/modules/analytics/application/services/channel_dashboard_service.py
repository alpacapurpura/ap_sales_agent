"""Channel dashboard service -- assembles per-channel detail views."""

from __future__ import annotations

import asyncio
from collections import defaultdict
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


# Channel slug -> human-readable name
_CHANNEL_NAMES: dict[str, str] = {
    "meta-ads": "Meta Ads",
    "google-ads": "Google Ads",
    "yt-ads": "YouTube Ads",
    "tiktok-ads": "TikTok Ads",
}

# Period string -> days
_PERIOD_DAYS: dict[str, int] = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "last_30_days": 30,
}

# KPI metrics to include in the dashboard hero row
_HERO_METRICS = ["spend", "ROAS", "CPL", "CTR", "CPC", "CPM", "CPA", "conversions"]

# Metrics for time series charts
_TIMESERIES_METRICS = [
    "spend",
    "impressions",
    "clicks",
    "reach",
    "conversions",
    "ROAS",
    "CPC",
    "CPM",
    "CPL",
]

# Funnel steps in order
_FUNNEL_STEPS = [
    ("Impresiones", "impressions"),
    ("Clics", "clicks"),
    ("Vistas de Landing", "meta_landing_page_views"),
    ("Leads", "meta_leads"),
    ("Conversiones", "conversions"),
]


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
                _TIMESERIES_METRICS,
                start,
                today,
            ),
        )

        # Build KPIs
        kpis = self._build_kpis(current_metrics, previous_metrics, industry)

        # Build time series
        time_series = self._build_time_series(daily_data)

        # Build funnel
        funnel = self._build_funnel(current_metrics)

        # Frequency alert
        frequency_alert = self._check_frequency(current_metrics)

        channel_name = _CHANNEL_NAMES.get(channel_slug, channel_slug)

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
    ) -> list[MetricKpiDTO]:
        """Build KPI cards with deltas and benchmarks."""
        kpis: list[MetricKpiDTO] = []
        for metric_name in _HERO_METRICS:
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
    ) -> AdFunnelDTO:
        """Build the ad conversion funnel with step-to-step rates."""
        steps: list[FunnelStepDTO] = []
        prev_value: float | None = None

        for label, metric_name in _FUNNEL_STEPS:
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
