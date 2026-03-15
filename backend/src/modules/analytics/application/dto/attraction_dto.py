from pydantic import BaseModel
from typing import Optional


class ChannelMetricDTO(BaseModel):
    slug: str
    name: str
    channel_type: str  # ORGANIC_SOCIAL, ORGANIC_SEARCH, PAID_MEDIA
    value: float
    cost: Optional[float] = None
    source_label: str
    connected: bool

    # ETL-enriched fields (backward-compatible defaults)
    cost_type: Optional[str] = None  # maps to CostType enum value
    unit: str = "count"  # maps to MetricUnit enum value
    currency: Optional[str] = None
    last_updated: Optional[str] = None  # ISO timestamp of last ETL extraction


class TrafficGroupDTO(BaseModel):
    total_value: float
    total_cost: Optional[float] = None
    channels: list[ChannelMetricDTO]


class AvailableChannelsDTO(BaseModel):
    channels: list[ChannelMetricDTO]


class AttractionDetailDTO(BaseModel):
    organic: TrafficGroupDTO
    paid: TrafficGroupDTO
    available: Optional[AvailableChannelsDTO] = None
    period: str = "last_30_days"
    last_updated: Optional[str] = None
