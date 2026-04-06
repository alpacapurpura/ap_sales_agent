"""Channel dashboard DTOs for per-channel detail views.

These DTOs power the channel-specific dashboard that displays KPIs with
industry benchmarks, time-series charts, ad funnels, and frequency alerts.
Each DTO is intentionally flat and serialisation-friendly so the frontend
can consume them without transformation.
"""

from pydantic import BaseModel


class BenchmarkRangeDTO(BaseModel):
    """Industry benchmark range for a single metric."""

    low: float
    median: float
    high: float
    unit: str
    interpretation: str


class SparkDataPointDTO(BaseModel):
    """Lightweight data point for sparkline mini-charts."""

    date: str  # ISO date string (YYYY-MM-DD)
    value: float


class MetricKpiDTO(BaseModel):
    """A single KPI card with optional benchmark and delta tracking."""

    metric_name: str
    display_name: str
    current_value: float
    previous_value: float | None = None
    delta_percent: float | None = None
    delta_absolute: float | None = None
    unit: str
    currency: str | None = None
    higher_is_better: bool = True
    benchmark: BenchmarkRangeDTO | None = None


class TimeSeriesDataPointDTO(BaseModel):
    """Single data point in a time-series chart."""

    date: str
    value: float


class MetricTimeSeriesDTO(BaseModel):
    """Full time-series for one metric, used in line/area charts."""

    metric_name: str
    display_name: str
    unit: str
    data_points: list[TimeSeriesDataPointDTO]


class FunnelStepDTO(BaseModel):
    """One step in an advertising funnel (impressions -> clicks -> leads)."""

    label: str
    metric_name: str
    value: float
    conversion_rate_from_previous: float | None = None


class AdFunnelDTO(BaseModel):
    """Ordered advertising funnel with conversion rates between steps."""

    steps: list[FunnelStepDTO]


class FrequencyAlertDTO(BaseModel):
    """Alert when ad frequency exceeds healthy thresholds."""

    current_value: float
    severity: str  # "warning" | "critical"
    message: str


class ChannelDashboardDTO(BaseModel):
    """Top-level response for a channel's detail dashboard view."""

    channel_slug: str
    channel_name: str
    industry_category: str
    period: str
    kpis: list[MetricKpiDTO]
    time_series: list[MetricTimeSeriesDTO]
    funnel: AdFunnelDTO
    frequency_alert: FrequencyAlertDTO | None = None


# ---------------------------------------------------------------------------
# Demographics breakdown DTOs
# ---------------------------------------------------------------------------


class DemographicSegmentDTO(BaseModel):
    """Single segment in a demographic breakdown (age, gender, placement)."""

    label: str
    value: float
    percentage: float


class DemographicsDTO(BaseModel):
    """Audience demographics breakdown for a channel."""

    age: list[DemographicSegmentDTO] = []
    gender: list[DemographicSegmentDTO] = []
    placement: list[DemographicSegmentDTO] = []
