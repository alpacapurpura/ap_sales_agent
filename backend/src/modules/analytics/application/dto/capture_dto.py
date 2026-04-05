"""Capture stage (Stage 1) DTOs for the metrics dashboard.

Reuses TrafficGroupDTO and AvailableChannelsDTO from attraction_dto
to maintain a consistent API shape across stages.
"""

from pydantic import BaseModel

from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    TrafficGroupDTO,
)


class CaptureHeaderKpisDTO(BaseModel):
    """Panel header KPIs: Total Leads | Conversion Rate | CAL."""

    total_leads: int
    conversion_rate: float  # percentage 0-100
    cost_per_lead: float | None = None  # None when no costs configured


class MiniFunnelDTO(BaseModel):
    """Mini arrow funnel: Visitors -> Leads = X%."""

    source_label: str  # "Visitantes"
    source_value: int  # Stage 0 total visitors
    target_label: str  # "Leads"
    target_value: int  # Stage 1 total leads
    conversion_rate: float  # percentage


class CaptureDetailDTO(BaseModel):
    """Full capture stage detail with 2 channel groups.

    Groups:
    - web_infrastructure: Landing Page Form, MailerLite
    - ai_agent: Instagram DM, Facebook Messenger, TikTok DM, WhatsApp Inbound
    """

    header_kpis: CaptureHeaderKpisDTO
    mini_funnel: MiniFunnelDTO
    web_infrastructure: TrafficGroupDTO  # reuse from attraction_dto
    ai_agent: TrafficGroupDTO  # reuse from attraction_dto
    available: AvailableChannelsDTO | None = None
    period: str = "last_30_days"
    last_updated: str | None = None
