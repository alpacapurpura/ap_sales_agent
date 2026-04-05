"""Opportunity stage (Stage 3) DTOs for the metrics dashboard.

Reuses TrafficGroupDTO and AvailableChannelsDTO from attraction_dto
and MiniFunnelDTO from capture_dto to maintain a consistent API shape.
"""

from pydantic import BaseModel

from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO


class OpportunityHeaderKpisDTO(BaseModel):
    """Panel header KPIs: Total SQLs | Conversion Rate (MQL->SQL) | Cost per SQL."""

    total_sqls: int
    conversion_rate: float  # percentage 0-100
    cost_per_sql: float | None = None  # None when no costs configured


class BottleneckDTO(BaseModel):
    """Bottleneck alert for high abandonment or no-show rates."""

    type: str  # "abandoned_cart" or "meeting_no_show"
    metric_label: str  # "Tasa de Abandono" or "Tasa de No-Show"
    current_rate: float  # percentage 0-100
    severity: str  # "normal", "warning", "critical"
    threshold: float  # threshold that was crossed
    tip: str  # actionable tip in Spanish


class OpportunityDetailDTO(BaseModel):
    """Full opportunity stage detail with 3 channel groups.

    Groups:
    - checkout: Checkout Iniciado, Carrito Abandonado (Shopify)
    - payment_links: Link de Pago Enviado (Sales Agent), Checkout Landing Page
    - qualification: Reuniones Agendadas (Scheduling module)
    """

    header_kpis: OpportunityHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # MQLs -> SQLs
    checkout: TrafficGroupDTO
    payment_links: TrafficGroupDTO
    qualification: TrafficGroupDTO
    bottlenecks: list[BottleneckDTO] = []
    available: AvailableChannelsDTO | None = None
    period: str = "last_30_days"
    last_updated: str | None = None
