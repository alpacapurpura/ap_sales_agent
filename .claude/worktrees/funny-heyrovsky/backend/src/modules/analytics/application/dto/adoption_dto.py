"""Adoption stage (Stage 5) DTOs for the metrics dashboard.

Provides the data contract for GET /metrics/adoption endpoint:
- AdoptionDetailDTO (top-level response)
- AdoptionHeaderKpisDTO (active/inactive customers, health %, TTV, refunds)
- OfferHealthDTO (per-offer customer health card)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

from typing import List, Optional

from pydantic import BaseModel

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO


class OfferHealthDTO(BaseModel):
    """Per-offer customer health card."""

    offer_id: str
    public_name: str
    total_customers: int
    active_count: int
    inactive_count: int
    health_pct: float  # 0-100
    ttv_days: Optional[float] = None  # average TTV for this offer's customers


class AdoptionHeaderKpisDTO(BaseModel):
    """3 primary + 2 secondary KPIs."""

    active_customers: int
    inactive_customers: int
    health_pct: float  # active / total * 100
    avg_ttv_days: Optional[float] = None
    refund_count: int = 0
    refund_amount: float = 0.0
    refund_currency: str = "USD"
    refund_amount_usd: Optional[float] = None


class AdoptionDetailDTO(BaseModel):
    """Full adoption stage (Stage 5) detail response."""

    header_kpis: AdoptionHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Ventas -> Activos
    offers: List[OfferHealthDTO]
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
