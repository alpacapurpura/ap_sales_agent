"""Sales stage (Stage 4) DTOs, tier mapping, and utility constants.

Provides the complete data contract for GET /metrics/sales endpoint:
- SalesDetailDTO (top-level response)
- RevenueGroupDTO (CONVERSION/EXPANSION groups)
- TierGroupDTO (offer sub-groups by value_level tier)
- OfferSaleDTO (per-offer revenue card)
- SalesHeaderKpisDTO (revenue, new customers, CAC)

Reuses MiniFunnelDTO from capture_dto and BottleneckDTO from opportunity_dto.
"""

from pydantic import BaseModel

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO

# ---------------------------------------------------------------------------
# TIER MAPPING: OfferValueLevel -> display tiers (aligned with Value Ladder)
# SINGLE SOURCE OF TRUTH for how offers are grouped in the Sales panel.
# Lead magnets excluded (don't generate revenue).
# Unknown levels default to "transformacion" (safest mid-range fallback).
# ---------------------------------------------------------------------------

VALUE_LEVEL_TO_TIER: dict[str, str | None] = {
    "lead_magnet": None,  # Lead magnets don't generate revenue
    "activacion": "activacion",
    "transformacion": "transformacion",
    "maximizacion": "maximizacion",
    "corporativo": "corporativo",
    # Legacy fallbacks (data that wasn't migrated yet):
    "level_0_free": None,
    "level_1_low_ticket": "activacion",
    "level_2_mid_ticket": "transformacion",
    "level_3_high_ticket": "transformacion",
    "level_4_recurring": "transformacion",
    "level_5_ultra_high": "maximizacion",
    "level_6_corporate": "corporativo",
}

TIER_DISPLAY_ORDER = ["activacion", "transformacion", "maximizacion", "corporativo"]
TIER_LABELS: dict[str, str] = {
    "activacion": "Activacion",
    "transformacion": "Transformacion",
    "maximizacion": "Maximizacion",
    "corporativo": "Corporativo",
}


def get_tier_for_value_level(value_level: str | None) -> str:
    """Map a value_level string to its display tier.

    Unknown levels default to transformacion (safe mid-range fallback).
    """
    if not value_level:
        return "transformacion"
    tier = VALUE_LEVEL_TO_TIER.get(value_level)
    if tier is None:
        return "transformacion"
    return tier


# ---------------------------------------------------------------------------
# Exchange rate constants (static config -- future: API integration)
# ---------------------------------------------------------------------------

DEFAULT_EXCHANGE_RATES: dict[str, float] = {
    "USD": 1.0,
    "MXN": 0.058,  # ~17.2 MXN per USD
    "EUR": 1.08,
    "COP": 0.00024,
    "ARS": 0.0011,
    "BRL": 0.19,
}


def convert_to_usd(amount: float, currency: str) -> float | None:
    """Convert amount to USD using static rates. Returns None if rate unknown."""
    rate = DEFAULT_EXCHANGE_RATES.get(currency)
    if rate is None:
        return None
    return round(amount * rate, 2)


# ---------------------------------------------------------------------------
# Subscription label constants
# ---------------------------------------------------------------------------

SUBSCRIPTION_LABELS: dict[str, dict | None] = {
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


def get_subscription_labels(pricing_type: str, offer_type: str) -> dict | None:
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
    usd_revenue: float | None = None
    source_breakdown: dict[str, int] = {}  # {"SHOPIFY": 60, "MANUAL": 15}
    # Subscription split (only for subscription/payment_plan offers)
    new_subscriptions: int | None = None
    new_subscription_revenue: float | None = None
    renewals: int | None = None
    renewal_revenue: float | None = None
    subscription_new_label: str | None = None
    subscription_renewal_label: str | None = None


class TierGroupDTO(BaseModel):
    """Group of offers in same value_level tier."""

    tier_key: str  # "low_ticket" | "mid_ticket" | "high_ticket" | "recurrente"
    tier_label: str  # "Low Ticket" | "Mid Ticket" | "High Ticket" | "Recurrente"
    offers: list[OfferSaleDTO]


class RevenueGroupDTO(BaseModel):
    """Top-level group: Adquisicion or Expansion."""

    group_key: str  # "adquisicion" | "expansion"
    group_label: str  # "Adquisicion" | "Expansion"
    total_revenue: float
    total_revenue_usd: float | None = None
    customer_count: int
    revenue_percentage: float  # of total revenue
    currency: str
    tiers: list[TierGroupDTO]


class SalesHeaderKpisDTO(BaseModel):
    """Panel header KPIs: Revenue Total | Nuevos Clientes | CAC + enriched Shopify metrics."""

    total_revenue: float
    total_revenue_usd: float | None = None
    currency: str
    new_customers: int  # CONVERSION count
    cac: float | None = None
    cac_incomplete: bool = False  # True when cost data missing
    # Enriched Shopify metrics (from official_metrics)
    net_sales: float = 0.0
    total_discounts: float = 0.0
    total_tax: float = 0.0
    refund_count: int = 0
    refund_amount: float = 0.0
    shipping_revenue: float = 0.0
    repeat_customers: int = 0
    discount_usage_count: int = 0
    # Shopify aggregate KPIs (from official_metrics — used for fallback display)
    shopify_revenue: float = 0.0
    shopify_order_count: int = 0
    shopify_avg_order_value: float = 0.0
    shopify_currency: str = "USD"


class SalesDetailDTO(BaseModel):
    """Full sales stage (Stage 4) detail response.

    Groups revenue by CONVERSION (adquisicion) and EXPANSION,
    sub-grouped by offer value_level tiers with per-offer cards.
    """

    header_kpis: SalesHeaderKpisDTO
    mini_funnel: MiniFunnelDTO  # Oportunidades -> Ventas
    adquisicion: RevenueGroupDTO
    expansion: RevenueGroupDTO
    bottlenecks: list[BottleneckDTO] = []
    period: str = "last_30_days"
    last_updated: str | None = None
