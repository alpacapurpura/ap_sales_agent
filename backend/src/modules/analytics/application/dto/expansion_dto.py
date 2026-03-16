"""Expansion stage (Stage 6) DTOs for the metrics dashboard.

Provides the data contract for GET /metrics/expansion endpoint:
- ExpansionDetailDTO (top-level response)
- ExpansionHeaderKpisDTO (Net MRR, Avg LTV, Churn Rate)
- ExpansionGroupDTO (Retencion, Crecimiento, Cancelaciones)
- ExpansionOfferDTO (per-offer revenue within a group)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

from typing import List, Optional

from pydantic import BaseModel

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO


class ExpansionOfferDTO(BaseModel):
    """Single offer within an expansion group."""

    offer_id: str
    public_name: str
    count: int
    revenue: float
    currency: str
    usd_revenue: Optional[float] = None


class ExpansionGroupDTO(BaseModel):
    """Category group: retencion, crecimiento, or cancelaciones."""

    group_key: str  # "retencion" | "crecimiento" | "cancelaciones"
    group_label: str
    group_subtitle: str
    total_count: int
    total_revenue: float
    total_revenue_usd: Optional[float] = None
    currency: str
    rate_pct: Optional[float] = None  # retention rate, expansion rate, or churn rate
    offers: List[ExpansionOfferDTO]


class ExpansionHeaderKpisDTO(BaseModel):
    """Net MRR, Avg LTV, Churn Rate."""

    net_mrr: float
    net_mrr_usd: Optional[float] = None
    currency: str
    avg_ltv: float
    avg_ltv_usd: Optional[float] = None
    churn_rate_pct: float  # 0-100


class ExpansionDetailDTO(BaseModel):
    """Full expansion stage (Stage 6) detail response."""

    header_kpis: ExpansionHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Activos -> Expansion
    retencion: ExpansionGroupDTO
    crecimiento: ExpansionGroupDTO
    cancelaciones: ExpansionGroupDTO
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
