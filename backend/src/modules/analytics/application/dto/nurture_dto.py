"""Nurture stage (Stage 2) DTOs for the metrics dashboard.

Reuses TrafficGroupDTO and AvailableChannelsDTO from attraction_dto
and MiniFunnelDTO from capture_dto to maintain a consistent API shape.
"""

from pydantic import BaseModel

from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO


class NurtureHeaderKpisDTO(BaseModel):
    """Panel header KPIs: Total MQLs | Conversion Rate | Cost per MQL."""

    total_mqls: int
    conversion_rate: float  # percentage 0-100
    cost_per_mql: float | None = None  # None when no costs configured


class CampaignMetricDTO(BaseModel):
    """Individual campaign metrics within a retargeting channel."""

    campaign_name: str
    campaign_id: str | None = None
    metrics: list  # List of MetricValueDTO


class NurtureDetailDTO(BaseModel):
    """Full nurture stage detail with 2 channel groups.

    Groups:
    - retargeting: Meta Retargeting, Google Retargeting, TikTok Retargeting
    - automation: Mailerlite, AI SDR
    """

    header_kpis: NurtureHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Leads -> MQLs
    retargeting: TrafficGroupDTO
    automation: TrafficGroupDTO
    available: AvailableChannelsDTO | None = None
    period: str = "last_30_days"
    last_updated: str | None = None
