"""Cross-module shared enums.

Enums that are used by 3+ bounded contexts live here to avoid
cross-module DDD boundary violations.  Each source module
re-exports these for internal backwards-compatibility.
"""

from enum import StrEnum

# ── Originally in crm/domain/enums.py ────���─────────────────────


class IdentityType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    COOKIE_ID = "cookie_id"
    USER_ID = "user_id"  # Internal User ID
    EXTERNAL_ID = "external_id"  # CRM, Shopify, etc.
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class LifecycleStage(StrEnum):
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MQL = "mql"
    SQL = "sql"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"
    CHURNED = "churned"


class FinancialCapacity(StrEnum):
    BROKE_STUDENT = "BROKE_STUDENT"
    LOW_INCOME = "LOW_INCOME"
    MIDDLE_CLASS = "MIDDLE_CLASS"
    UPPER_MIDDLE = "UPPER_MIDDLE"
    HIGH_NET_WORTH = "HIGH_NET_WORTH"
    ULTRA_HIGH_NET_WORTH = "ULTRA_HIGH_NET_WORTH"


class AvatarPersona(StrEnum):
    NEWBIE = "NEWBIE"
    SKEPTIC = "SKEPTIC"
    VIP = "VIP"
    ACHIEVER = "ACHIEVER"
    RESEARCHER = "RESEARCHER"


class SaleStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    PENDING = "PENDING"
    FAILED = "FAILED"


class SaleStage(StrEnum):
    CONVERSION = "CONVERSION"
    EXPANSION = "EXPANSION"


class LeadTemperature(StrEnum):
    COLD = "COLD"
    WARM = "WARM"
    HOT = "HOT"


# ── Originally in connections/domain/enums.py ────────────��─────


class ChannelType(StrEnum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"  # Evolution / QR
    WHATSAPP_CLOUD = "whatsapp_cloud"  # Meta Cloud API
    MANYCHAT = "manychat"

    # Marketing & E-commerce
    SHOPIFY = "shopify"
    MAILERLITE = "mailerlite"
    GOOGLE_ANALYTICS = "google_analytics"
    META = "meta"  # Meta Ads / Facebook — master credential (user token)
    FACEBOOK_PAGE = "facebook_page"  # Per-page asset (has its own page_access_token)
    INSTAGRAM_ACCOUNT = "instagram_account"  # IG Business Account linked to a Page
    META_ADS_ACCOUNT = "meta_ads_account"  # Ad Account (uses user token for reads)
    META_PIXEL = "meta_pixel"  # Meta (Facebook) Pixel for conversion tracking
    WHATSAPP_BUSINESS_ACCOUNT = "whatsapp_business_account"  # WABA from Meta Business Manager
    YOUTUBE = "youtube"
    YOUTUBE_ANALYTICS = "youtube_analytics"

    # Calendar & Email
    GOOGLE_CALENDAR = "google_calendar"
    GMAIL = "gmail"
