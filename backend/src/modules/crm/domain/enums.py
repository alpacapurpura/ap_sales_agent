"""CRM domain enumerations."""

from enum import StrEnum

# Re-export shared enums for internal CRM backwards-compatibility
from luana_core_platform.domain.enums import (  # noqa: F401
    AvatarPersona,
    FinancialCapacity,
    IdentityType,
    LeadTemperature,
    LifecycleStage,
    SaleStage,
    SaleStatus,
)


class SophisticationLevel(StrEnum):
    """Enumerate sophistication level values."""

    UNAWARE = "UNAWARE"
    PROBLEM_AWARE = "PROBLEM_AWARE"
    SOLUTION_AWARE = "SOLUTION_AWARE"
    PRODUCT_AWARE = "PRODUCT_AWARE"
    MOST_AWARE = "MOST_AWARE"


class AuthorityLevel(StrEnum):
    """Enumerate authority level values."""

    SOLO = "SOLO"
    PARTNER = "PARTNER"
    INFLUENCER = "INFLUENCER"
    GATEKEEPER = "GATEKEEPER"
    COMMITTEE = "COMMITTEE"


class FunnelStage(StrEnum):
    """Enumerate funnel stage values."""

    RAPPORT = "S1_Rapport"
    DISCOVERY = "S2_Discovery"
    GAP = "S3_Gap"
    PITCH = "S4_Pitch"
    ANCHORING = "S5_Anchoring"
    CLOSING = "S6_Closing"
    DOWNSELL_EXIT = "DOWNSELL_EXIT"


class LeadStatus(StrEnum):
    """Enumerate lead status values."""

    AWARENESS = "awareness"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEGOTIATION = "negotiation"
    ENROLLED = "enrolled"
    OBJECTION_HANDLING = "objection_handling"
    CALL_BOOKED = "call_booked"
    DOWNSELL_ACCEPTED = "downsell_accepted"


class ProductLaunchStage(StrEnum):
    """Enumerate product launch stage values."""

    PRE_LAUNCH = "pre_launch"
    OPEN_CART = "open_cart"
    CLOSE_CART = "close_cart"
    EVERGREEN = "evergreen"


class BusinessStage(StrEnum):
    """Enumerate business stage values."""

    ACTIVE = "Negocio Activo"
    IDEA = "Idea Clara"
    NONE = "Sin Idea"


class PaymentMethod(StrEnum):
    """Enumerate payment method values."""

    CREDIT_CARD = "CREDIT_CARD"
    WIRE = "WIRE"
    CASH = "CASH"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    MANUAL = "MANUAL"
