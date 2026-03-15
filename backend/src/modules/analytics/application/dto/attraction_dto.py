from pydantic import BaseModel
from typing import Optional


class ChannelMetricDTO(BaseModel):
    slug: str
    name: str
    channel_type: str  # ORGANIC_SOCIAL, ORGANIC_SEARCH, PAID_MEDIA
    value: int
    cost: Optional[int] = None
    source_label: str
    connected: bool


class TrafficGroupDTO(BaseModel):
    total_value: int
    total_cost: Optional[int] = None
    channels: list[ChannelMetricDTO]


class AttractionDetailDTO(BaseModel):
    organic: TrafficGroupDTO
    paid: TrafficGroupDTO
    period: str = "last_30_days"
