"""Evangelization stage (Stage 7) DTOs for the metrics dashboard.

Provides the data contract for GET /metrics/evangelization endpoint:
- EvangelizationDetailDTO (top-level response)
- EvangelizationHeaderKpisDTO (K-Factor, referral conversions, NPS, revenue, evangelists)
- EvangelistDTO (per-evangelist card)
- CandidatoDTO (NPS >= 9 not yet EVANGELIST)
- NpsSummaryDTO (aggregated NPS display)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

from typing import List, Optional

from pydantic import BaseModel

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO


class EvangelizationHeaderKpisDTO(BaseModel):
    """Primary row: k_factor, referral_conversions, nps_score. Secondary row: referral_revenue, active_evangelists."""

    k_factor: float  # X.XX (2 decimals)
    referral_conversions: int
    nps_score: Optional[float] = None  # 0-10 scale (average), None if no responses
    referral_revenue: float
    referral_revenue_usd: Optional[float] = None
    currency: str = "MXN"
    active_evangelists: int


class EvangelistDTO(BaseModel):
    """Per-evangelist card data."""

    customer_id: str
    full_name: str
    referral_code: str
    referrals_sent: int  # total sales attributed via this code
    conversions: int  # completed sales from referrals
    revenue_attributed: float
    currency: str = "MXN"
    usd_revenue: Optional[float] = None
    is_active: bool


class CandidatoDTO(BaseModel):
    """Customer with NPS >= 9 not yet EVANGELIST."""

    customer_id: str
    full_name: str
    nps_score: int  # 0-10
    responded_at: Optional[str] = None


class NpsSummaryDTO(BaseModel):
    """Aggregated NPS display."""

    nps_score: Optional[float] = None  # 0-10 average
    standard_nps: Optional[float] = None  # -100 to +100 (for tooltip)
    promoter_count: int = 0  # 9-10
    passive_count: int = 0  # 7-8
    detractor_count: int = 0  # 0-6
    total_responses: int = 0
    surveys_sent: int = 0
    response_rate_pct: float = 0.0


class EvangelizationDetailDTO(BaseModel):
    """Full evangelization stage (Stage 7) detail response."""

    header_kpis: EvangelizationHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Clientes Activos -> Evangelistas
    referidos: List[EvangelistDTO] = []
    candidatos: List[CandidatoDTO] = []
    nps_summary: NpsSummaryDTO
    ugc_count: int = 0  # total testimonials with consent
    ugc_written: int = 0
    ugc_audio: int = 0
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
