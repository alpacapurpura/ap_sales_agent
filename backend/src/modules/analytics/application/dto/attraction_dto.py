"""Attraction stage DTOs with multi-metric support.

ChannelMetricDTO carries a list of MetricValueDTO objects instead of a
single value field.  A backward-compatible ``value`` property returns
the first metric's value (or 0.0 when empty) so callers migrating
incrementally keep working.
"""

from typing import Optional

from pydantic import BaseModel, computed_field


class MetricValueDTO(BaseModel):
    """Single named metric within a channel.

    Examples:
        MetricValueDTO(name="reach", value=5000.0)
        MetricValueDTO(name="engagement", value=1200.0,
                       breakdown={"likes": 800, "comments": 400})
        MetricValueDTO(name="spend", value=123.45, unit="currency", currency="USD")
    """

    name: str
    value: float
    unit: str = "count"
    currency: Optional[str] = None
    breakdown: Optional[dict] = None


class ChannelMetricDTO(BaseModel):
    """Metric data for a single channel, carrying multiple named metrics.

    The ``metrics`` list replaces the former scalar ``value`` field.
    A computed ``value`` property preserves backward compatibility by
    returning the first metric's value or 0.0 when the list is empty.
    """

    slug: str
    name: str
    channel_type: str  # social, search, direct, paid, outbound
    metrics: list[MetricValueDTO]
    source_label: str
    connected: bool

    # ETL-enriched fields (backward-compatible defaults)
    cost_type: Optional[str] = None
    last_updated: Optional[str] = None

    # Error / staleness indicators
    stale: bool = False
    error_message: Optional[str] = None

    @computed_field  # type: ignore[misc]
    @property
    def value(self) -> float:
        """Backward-compat: return first metric value or 0.0."""
        return self.metrics[0].value if self.metrics else 0.0


class TrafficGroupDTO(BaseModel):
    """A group of channels with aggregated totals keyed by metric name.

    Example totals: {"reach": 5000, "engagement": 1200}
    """

    totals: dict[str, float]
    channels: list[ChannelMetricDTO]


class AvailableChannelsDTO(BaseModel):
    """Channels not yet connected -- shown with 'Configurar' badge."""

    channels: list[ChannelMetricDTO]


class AttractionDetailDTO(BaseModel):
    """Full attraction stage detail with 4 channel groups.

    Groups match CONTEXT.md headers:
    - organic_social: Instagram, YouTube, Facebook, TikTok, LinkedIn
    - ga4_search: Google Organic, Direct, AI Search Organic
    - paid: Meta Ads, Google Ads, TikTok Ads, YouTube Ads
    - outbound: Cold Contact
    """

    organic_social: TrafficGroupDTO
    ga4_search: TrafficGroupDTO
    paid: TrafficGroupDTO
    outbound: TrafficGroupDTO
    available: Optional[AvailableChannelsDTO] = None
    period: str = "last_30_days"
    last_updated: Optional[str] = None
