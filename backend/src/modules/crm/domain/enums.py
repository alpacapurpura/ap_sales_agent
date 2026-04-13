from enum import StrEnum

# Re-export shared enums for internal CRM backwards-compatibility
from src.shared.domain.enums import (  # noqa: F401
    AvatarPersona,
    FinancialCapacity,
    IdentityType,
    LeadTemperature,
    LifecycleStage,
    SaleStage,
    SaleStatus,
)


class SophisticationLevel(StrEnum):
    UNAWARE = "UNAWARE"
    PROBLEM_AWARE = "PROBLEM_AWARE"
    SOLUTION_AWARE = "SOLUTION_AWARE"
    PRODUCT_AWARE = "PRODUCT_AWARE"
    MOST_AWARE = "MOST_AWARE"


class AuthorityLevel(StrEnum):
    SOLO = "SOLO"
    PARTNER = "PARTNER"
    INFLUENCER = "INFLUENCER"
    GATEKEEPER = "GATEKEEPER"
    COMMITTEE = "COMMITTEE"


class FunnelStage(StrEnum):
    RAPPORT = "S1_Rapport"
    DISCOVERY = "S2_Discovery"
    GAP = "S3_Gap"
    PITCH = "S4_Pitch"
    ANCHORING = "S5_Anchoring"
    CLOSING = "S6_Closing"
    DOWNSELL_EXIT = "DOWNSELL_EXIT"


class LeadStatus(StrEnum):
    AWARENESS = "awareness"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEGOTIATION = "negotiation"
    ENROLLED = "enrolled"
    OBJECTION_HANDLING = "objection_handling"
    CALL_BOOKED = "call_booked"
    DOWNSELL_ACCEPTED = "downsell_accepted"


class ProductLaunchStage(StrEnum):
    PRE_LAUNCH = "pre_launch"
    OPEN_CART = "open_cart"
    CLOSE_CART = "close_cart"
    EVERGREEN = "evergreen"


class BusinessStage(StrEnum):
    ACTIVE = "Negocio Activo"
    IDEA = "Idea Clara"
    NONE = "Sin Idea"


class PaymentMethod(StrEnum):
    CREDIT_CARD = "CREDIT_CARD"
    WIRE = "WIRE"
    CASH = "CASH"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    MANUAL = "MANUAL"
