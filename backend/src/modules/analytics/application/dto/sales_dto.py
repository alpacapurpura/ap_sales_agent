"""Sales stage (Stage 4) DTOs, tier mapping, and utility constants.

Provides the complete data contract for GET /metrics/sales endpoint:
- SalesDetailDTO (top-level response)
- RevenueGroupDTO (CONVERSION/EXPANSION groups)
- TierGroupDTO (offer sub-groups by value_level tier)
- OfferSaleDTO (per-offer revenue card)
- SalesHeaderKpisDTO (revenue, new customers, CAC)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO


# ---------------------------------------------------------------------------
# TIER MAPPING: 7 OfferValueLevel values -> 4 display tiers
# SINGLE SOURCE OF TRUTH for how offers are grouped in the Sales panel.
# If Offer Studio adds new value_levels, add them here.
# Unknown levels default to "high_ticket".
#
# Why this simplification:
# - Business owners think in price ranges, not in 7 granular levels
# - "High Ticket" merges levels 3 (VIP/1:1), 5 (Ultra-High), and 6 (Corporate)
#   because they all represent premium, high-touch sales with similar processes
# - "Recurrente" is separated because recurring revenue has fundamentally
#   different metrics (new vs renewal split, MRR tracking)
# - FREE (level 0) excluded -- lead magnets don't generate revenue (Stage 1)
# ---------------------------------------------------------------------------

VALUE_LEVEL_TO_TIER: dict[str, Optional[str]] = {
    "level_0_free": None,  # Excluded from sales panel
    "level_1_low_ticket": "low_ticket",
    "level_2_mid_ticket": "mid_ticket",
    "level_3_high_ticket": "high_ticket",
    "level_4_recurring": "recurrente",
    "level_5_ultra_high": "high_ticket",
    "level_6_corporate": "high_ticket",
}

TIER_DISPLAY_ORDER = ["low_ticket", "mid_ticket", "high_ticket", "recurrente"]
TIER_LABELS: dict[str, str] = {
    "low_ticket": "Low Ticket",
    "mid_ticket": "Mid Ticket",
    "high_ticket": "High Ticket",
    "recurrente": "Recurrente",
}


def get_tier_for_value_level(value_level: Optional[str]) -> str:
    """Map a value_level string to its display tier.

    Unknown levels default to high_ticket (safe fallback per CONTEXT.md).
    """
    if not value_level:
        return "high_ticket"
    tier = VALUE_LEVEL_TO_TIER.get(value_level)
    if tier is None:
        return "high_ticket"
    return tier


# ---------------------------------------------------------------------------
# Exchange rate constants (static config -- future: API integration)
# ---------------------------------------------------------------------------

DEFAULT_EXCHANGE_RATES: dict[str, float] = {
    "USD": 1.0,
    "MXN": 0.058,   # ~17.2 MXN per USD
    "EUR": 1.08,
    "COP": 0.00024,
    "ARS": 0.0011,
    "BRL": 0.19,
}


def convert_to_usd(amount: float, currency: str) -> Optional[float]:
    """Convert amount to USD using static rates. Returns None if rate unknown."""
    rate = DEFAULT_EXCHANGE_RATES.get(currency)
    if rate is None:
        return None
    return round(amount * rate, 2)


# ---------------------------------------------------------------------------
# Subscription label constants
# ---------------------------------------------------------------------------

SUBSCRIPTION_LABELS: dict[str, Optional[dict]] = {
    "subscription": {
        "new_label": "nuevas suscripciones",
        "renewal_label": "renovaciones",
    },
    "payment_plan": {
        "new_label": "nuevos planes",
        "renewal_label": "cuotas cobradas",
    },
    "one_time": None,
}

RECURRING_SERVICE_TYPES = {
    "productized_service",
    "ecommerce_development",
    "monthly_retainer",
    "performance_rev_share",
}


def get_subscription_labels(
    pricing_type: str, offer_type: str
) -> Optional[dict]:
    """Get new/renewal labels based on pricing type and offer type."""
    if pricing_type == "one_time":
        return None
    if offer_type in RECURRING_SERVICE_TYPES:
        return {"new_label": "nuevos contratos", "renewal_label": "renovaciones"}
    return SUBSCRIPTION_LABELS.get(pricing_type)


# ---------------------------------------------------------------------------
# Bottleneck threshold constants
# ---------------------------------------------------------------------------

LOW_CONVERSION_THRESHOLDS = {"warning": 20.0, "critical": 10.0}
HIGH_CAC_THRESHOLDS = {"warning": 0.50, "critical": 0.50}
# warning: CAC/AOV >= 33%, critical: CAC/AOV >= 50%
HIGH_CAC_WARNING_RATIO = 0.33
HIGH_CAC_CRITICAL_RATIO = 0.50


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class OfferSaleDTO(BaseModel):
    """Single offer's sales data within a tier group."""

    offer_id: str
    public_name: str
    offer_type: str
    pricing_type: str  # "one_time" | "subscription" | "payment_plan"
    total_revenue: float
    sales_count: int
    currency: str
    usd_revenue: Optional[float] = None
    source_breakdown: Dict[str, int] = {}  # {"SHOPIFY": 60, "MANUAL": 15}
    # Subscription split (only for subscription/payment_plan offers)
    new_subscriptions: Optional[int] = None
    new_subscription_revenue: Optional[float] = None
    renewals: Optional[int] = None
    renewal_revenue: Optional[float] = None
    subscription_new_label: Optional[str] = None
    subscription_renewal_label: Optional[str] = None


class TierGroupDTO(BaseModel):
    """Group of offers in same value_level tier."""

    tier_key: str  # "low_ticket" | "mid_ticket" | "high_ticket" | "recurrente"
    tier_label: str  # "Low Ticket" | "Mid Ticket" | "High Ticket" | "Recurrente"
    offers: List[OfferSaleDTO]


class RevenueGroupDTO(BaseModel):
    """Top-level group: Adquisicion or Expansion."""

    group_key: str  # "adquisicion" | "expansion"
    group_label: str  # "Adquisicion" | "Expansion"
    total_revenue: float
    total_revenue_usd: Optional[float] = None
    customer_count: int
    revenue_percentage: float  # of total revenue
    currency: str
    tiers: List[TierGroupDTO]


class SalesHeaderKpisDTO(BaseModel):
    """Panel header KPIs: Revenue Total | Nuevos Clientes | CAC."""

    total_revenue: float
    total_revenue_usd: Optional[float] = None
    currency: str
    new_customers: int  # CONVERSION count
    cac: Optional[float] = None
    cac_incomplete: bool = False  # True when cost data missing


class SalesDetailDTO(BaseModel):
    """Full sales stage (Stage 4) detail response.

    Groups revenue by CONVERSION (adquisicion) and EXPANSION,
    sub-grouped by offer value_level tiers with per-offer cards.
    """

    header_kpis: SalesHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Oportunidades -> Ventas
    adquisicion: RevenueGroupDTO
    expansion: RevenueGroupDTO
    bottlenecks: List[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: Optional[str] = None
