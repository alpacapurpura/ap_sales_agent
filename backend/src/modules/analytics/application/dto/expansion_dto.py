"""Expansion stage (Stage 6) DTOs for the metrics dashboard.

Provides the data contract for GET /metrics/expansion endpoint:
- ExpansionDetailDTO (top-level response)
- ExpansionHeaderKpisDTO (Net MRR, Avg LTV, Churn Rate)
- ExpansionGroupDTO (Retencion, Crecimiento, Cancelaciones)
- ExpansionOfferDTO (per-offer revenue within a group)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

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
    usd_revenue: float | None = None


class ExpansionGroupDTO(BaseModel):
    """Category group: retencion, crecimiento, or cancelaciones."""

    group_key: str  # "retencion" | "crecimiento" | "cancelaciones"
    group_label: str
    group_subtitle: str
    total_count: int
    total_revenue: float
    total_revenue_usd: float | None = None
    currency: str
    rate_pct: float | None = None  # retention rate, expansion rate, or churn rate
    offers: list[ExpansionOfferDTO]


class ExpansionHeaderKpisDTO(BaseModel):
    """Net MRR, Avg LTV, Churn Rate."""

    net_mrr: float
    net_mrr_usd: float | None = None
    currency: str
    avg_ltv: float
    avg_ltv_usd: float | None = None
    churn_rate_pct: float  # 0-100


class ExpansionDetailDTO(BaseModel):
    """Full expansion stage (Stage 6) detail response."""

    header_kpis: ExpansionHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Activos -> Expansion
    retencion: ExpansionGroupDTO
    crecimiento: ExpansionGroupDTO
    cancelaciones: ExpansionGroupDTO
    bottlenecks: list[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: str | None = None
