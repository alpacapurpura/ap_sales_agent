"""Time-series DTOs for chart visualization.

Generic endpoint that returns daily/weekly data points grouped by channel,
reusable across all funnel stages.
"""

from pydantic import BaseModel


class ChannelInfoDTO(BaseModel):
    """Channel metadata for chart legend/colors."""

    slug: str
    name: str
    color: str  # hex suggestion, frontend can override


class TimeSeriesPointDTO(BaseModel):
    """Single date point with per-channel values."""

    date: str  # YYYY-MM-DD
    channels: dict[str, float]  # {"meta-ads": 1200, "google-organic": 800}


class StageTimeSeriesDTO(BaseModel):
    """Full time-series response for a funnel stage + metric."""

    stage: str
    metric_name: str
    granularity: str  # "daily" | "weekly"
    range_days: int
    data_points: list[TimeSeriesPointDTO]
    channels_present: list[ChannelInfoDTO]
    period_totals: dict[str, float]
    previous_period_totals: dict[str, float] | None = None
