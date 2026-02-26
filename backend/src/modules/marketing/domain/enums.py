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
