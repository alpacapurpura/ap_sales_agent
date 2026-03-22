from enum import Enum

class IdentityType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    COOKIE_ID = "cookie_id"
    USER_ID = "user_id" # Internal User ID
    EXTERNAL_ID = "external_id" # CRM, Shopify, etc.
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"

class LifecycleStage(str, Enum):
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MQL = "mql"
    SQL = "sql"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"
    CHURNED = "churned"

class FinancialCapacity(str, Enum):
    BROKE_STUDENT = "BROKE_STUDENT"
    LOW_INCOME = "LOW_INCOME"
    MIDDLE_CLASS = "MIDDLE_CLASS"
    UPPER_MIDDLE = "UPPER_MIDDLE"
    HIGH_NET_WORTH = "HIGH_NET_WORTH"
    ULTRA_HIGH_NET_WORTH = "ULTRA_HIGH_NET_WORTH"

class SophisticationLevel(str, Enum):
    UNAWARE = "UNAWARE"
    PROBLEM_AWARE = "PROBLEM_AWARE"
    SOLUTION_AWARE = "SOLUTION_AWARE"
    PRODUCT_AWARE = "PRODUCT_AWARE"
    MOST_AWARE = "MOST_AWARE"

class AuthorityLevel(str, Enum):
    SOLO = "SOLO"
    PARTNER = "PARTNER"
    INFLUENCER = "INFLUENCER"
    GATEKEEPER = "GATEKEEPER"
    COMMITTEE = "COMMITTEE"

class LeadTemperature(str, Enum):
    COLD = "COLD"
    WARM = "WARM"
    HOT = "HOT"

class AvatarPersona(str, Enum):
    NEWBIE = "NEWBIE"
    SKEPTIC = "SKEPTIC"
    VIP = "VIP"
    ACHIEVER = "ACHIEVER"
    RESEARCHER = "RESEARCHER"

class FunnelStage(str, Enum):
    RAPPORT = "S1_Rapport"
    DISCOVERY = "S2_Discovery"
    GAP = "S3_Gap"
    PITCH = "S4_Pitch"
    ANCHORING = "S5_Anchoring"
    CLOSING = "S6_Closing"
    DOWNSELL_EXIT = "DOWNSELL_EXIT"

class LeadStatus(str, Enum):
    AWARENESS = "awareness"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEGOTIATION = "negotiation"
    ENROLLED = "enrolled"
    OBJECTION_HANDLING = "objection_handling"
    CALL_BOOKED = "call_booked"
    DOWNSELL_ACCEPTED = "downsell_accepted"

class ProductLaunchStage(str, Enum):
    PRE_LAUNCH = "pre_launch"
    OPEN_CART = "open_cart"
    CLOSE_CART = "close_cart"
    EVERGREEN = "evergreen"

class BusinessStage(str, Enum):
    ACTIVE = "Negocio Activo"
    IDEA = "Idea Clara"
    NONE = "Sin Idea"

class SaleStatus(str, Enum):
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    PENDING = "PENDING"
    FAILED = "FAILED"

class SaleStage(str, Enum):
    CONVERSION = "CONVERSION"
    EXPANSION = "EXPANSION"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    WIRE = "WIRE"
    CASH = "CASH"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    MANUAL = "MANUAL"
