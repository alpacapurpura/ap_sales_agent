"""Stage Overview DTOs for lightweight progressive loading.

Provides a much smaller payload (~50-100 fields) compared to full
stage detail endpoints (~500+ fields). Used by the frontend to render
the stage header, channel list, and group tabs without loading all data.
"""

from pydantic import BaseModel, ConfigDict


class MetricValueDTO(BaseModel):
    """Single named KPI value for the overview."""

    model_config = ConfigDict(from_attributes=True)
    name: str
    value: float
    unit: str | None = None


class ChannelOverviewDTO(BaseModel):
    """Lightweight channel info with a single headline KPI.

    Contains only the data needed to render a channel card in a list,
    not the full multi-metric payload from the detail endpoint.
    """

    model_config = ConfigDict(from_attributes=True)
    slug: str
    name: str
    channel_type: str
    group_key: str
    connected: bool
    headline_kpi: MetricValueDTO | None = None
    last_updated: str | None = None
    stale: bool = False
    provider_name: str | None = None


class GroupOverviewDTO(BaseModel):
    """Summary info for a channel group (e.g., organic_social, paid)."""

    model_config = ConfigDict(from_attributes=True)
    group_key: str
    group_label: str
    channel_count: int


class MiniFunnelOverviewDTO(BaseModel):
    """Stage transition mini-funnel: source -> target = conversion_rate%."""

    model_config = ConfigDict(from_attributes=True)
    source_label: str
    source_value: float
    target_label: str
    target_value: float
    conversion_rate: float


class BottleneckOverviewDTO(BaseModel):
    """Simplified bottleneck alert for the overview."""

    model_config = ConfigDict(from_attributes=True)
    type: str
    metric_label: str
    severity: str


class StageOverviewDTO(BaseModel):
    """Top-level overview response for a funnel stage.

    Returns header KPIs, channel list with 1 headline KPI each,
    group summaries, and optional mini-funnel / bottleneck data.
    ~50-100 fields vs ~500+ for the full detail endpoint.
    """

    model_config = ConfigDict(from_attributes=True)
    stage: str
    header_kpis: dict[str, float | None]
    mini_funnel: MiniFunnelOverviewDTO | None = None
    groups: list[GroupOverviewDTO]
    channel_list: list[ChannelOverviewDTO]
    bottlenecks: list[BottleneckOverviewDTO]
    period: str = "last_30_days"
    last_updated: str | None = None
