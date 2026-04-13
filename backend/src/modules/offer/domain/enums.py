from enum import Enum, StrEnum
from typing import Any


class OfferArchetype(StrEnum):
    PRODUCTO = "producto"  # ProductDetails
    PROGRAMA = "programa"  # ProgramDetails
    SERVICIO = "servicio"  # ServiceDetails
    MEMBRESIA = "membresia"  # SubscriptionDetails
    EXPERIENCIA = "experiencia"  # EventDetails


class OfferValueLevel(StrEnum):
    LEAD_MAGNET = "lead_magnet"
    ACTIVACION = "activacion"
    TRANSFORMACION = "transformacion"
    MAXIMIZACION = "maximizacion"
    CORPORATIVO = "corporativo"


class OfferDeliveryModel(StrEnum):
    DIY = "diy"  # Do It Yourself (Courses, Ebooks)
    DWY = "dwy"  # Done With You (Coaching, Mentorship)
    DFY = "dfy"  # Done For You (Agency, Service)
    HYBRID = "hybrid"  # Mix


class OfferStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    WAITLIST = "waitlist"
    SOLD_OUT = "sold_out"


class AssetType(StrEnum):
    FLYER = "flyer"
    VIDEO = "video"
    CAROUSEL = "carousel"
    DOCUMENT = "document"
    IMAGE = "image"


class AssetSource(StrEnum):
    AI = "ai"
    EXTERNAL = "external"


class AssetStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class KnowledgeSourceType(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    VIDEO = "video"
    URL_YOUTUBE = "url_youtube"
    URL_ARTICLE = "url_article"
    URL_GOOGLE_DOC = "url_google_doc"


class KnowledgeSourceStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class LandingJobStatus(StrEnum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class GuaranteeType(StrEnum):
    NONE = "none"
    CONDITIONAL_ACTION_BASED = (
        "conditional_action_based"  # "Si haces X y no funciona, te devuelvo"
    )
    UNCONDITIONAL_30_DAY = "unconditional_30_day"
    DOUBLE_MONEY_BACK = "double_money_back"
    SATISFACTION_OR_FREE_WORK = "satisfaction_or_free_work"


class PaymentPlanType(StrEnum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    PAYMENT_PLAN = "payment_plan"  # e.g. 3x $500


class DeliverableFormat(StrEnum):
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    LIVE_SESSION = "live_session"
    TEMPLATE = "template"
    COMMUNITY_ACCESS = "community_access"
    SOFTWARE_ACCESS = "software_access"
    PHYSICAL_ITEM = "physical_item"
    SERVICE_HOURS = "service_hours"


class AccessDuration(StrEnum):
    LIFETIME = "lifetime"
    LIMITED_TIME = "limited_time"  # Requires end date or duration
    SUBSCRIPTION_ACTIVE = "subscription_active"


class PrerequisiteType(StrEnum):
    NONE = "none"
    APPLICATION_APPROVED = "application_approved"
    PRIOR_PROGRAM_COMPLETION = "prior_program_completion"
    INCOME_LEVEL = "income_level"


class OnboardingMechanism(StrEnum):
    INSTANT_ACCESS_EMAIL = "instant_access_email"
    BOOK_KICKOFF_CALL = "book_kickoff_call"
    FILL_INTAKE_FORM = "fill_intake_form"
    JOIN_COMMUNITY = "join_community"


class EventLocationType(StrEnum):
    VIRTUAL = "virtual"
    PHYSICAL_LOCAL = "physical_local"
    DESTINATION_RETREAT = "destination_retreat"


class BillingFrequency(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONE_OFF = "one_off"


class FulfillmentType(StrEnum):
    DIGITAL_DOWNLOAD = "digital_download"
    LMS_ACCESS = "lms_access"
    PHYSICAL_SHIPPING = "physical_shipping"
    MANUAL_PROVISIONING = "manual_provisioning"


class DigitalFormat(StrEnum):
    PDF_EBOOK = "pdf_ebook"
    VIDEO_COURSE = "video_course"
    AUDIO_SERIES = "audio_series"
    NOTION_TEMPLATE = "notion_template"
    SOFTWARE_SAAS = "software_access"
    PHYSICAL_ITEM = "physical_item"  # Fallback


class ProgramStructure(StrEnum):
    FIXED_COHORT = "fixed_cohort"  # Start/End Date Fixed
    ROLLING_ADMISSION = "rolling_admission"  # Start anytime, N weeks duration
    CHALLENGE = "challenge"  # Fixed short duration (e.g. 5 days)
    MEMBERSHIP = "membership"  # Ongoing


class LiveInteractionType(StrEnum):
    NONE = "none"
    GROUP_Q_AND_A = "group_q_and_a"
    ONE_ON_ONE_CHECKINS = "one_on_one_checkins"
    HOT_SEATS = "hot_seats"
    WORKSHOPS = "workshops"


class CommunityPlatform(StrEnum):
    NONE = "none"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SKOOL = "skool"
    CIRCLE = "circle"
    FACEBOOK_GROUP = "facebook_group"
    SLACK = "slack"


class ServiceCategory(StrEnum):
    ADVISORY = "advisory"  # Selling Wisdom (Consulting)
    AGENCY = "agency"  # Selling Hands (Done For You)
    AUTHORITY = "authority"  # Selling Influence (Sponsorships)


class InteractionMode(StrEnum):
    SYNC = "sync"  # Real time calls
    ASYNC = "async"  # Loom/Email/Docs
    HYBRID = "hybrid"


class ServiceFrequency(StrEnum):
    ONE_OFF = "one_off"  # Project based
    RETAINER = "retainer"  # Ongoing


class AccommodationType(StrEnum):
    NOT_INCLUDED = "not_included"
    SHARED_ROOM = "shared_room"
    PRIVATE_ROOM = "private_room"
    LUXURY_SUITE = "luxury_suite"


GUARANTEE_METADATA: dict[str, dict[str, Any]] = {
    GuaranteeType.NONE.value: {"risk_level": "High", "conversion_boost": "None"},
    GuaranteeType.CONDITIONAL_ACTION_BASED.value: {
        "risk_level": "Medium",
        "conversion_boost": "High",
    },
    GuaranteeType.UNCONDITIONAL_30_DAY.value: {
        "risk_level": "Low",
        "conversion_boost": "Very High",
    },
    GuaranteeType.DOUBLE_MONEY_BACK.value: {
        "risk_level": "Very Low",
        "conversion_boost": "Extreme",
    },
    GuaranteeType.SATISFACTION_OR_FREE_WORK.value: {
        "risk_level": "Medium",
        "conversion_boost": "High",
    },
}

ARCHETYPE_DEFAULT_DELIVERY: dict[OfferArchetype, OfferDeliveryModel] = {
    OfferArchetype.PRODUCTO: OfferDeliveryModel.DIY,
    OfferArchetype.PROGRAMA: OfferDeliveryModel.DWY,
    OfferArchetype.SERVICIO: OfferDeliveryModel.DFY,
    OfferArchetype.MEMBRESIA: OfferDeliveryModel.DIY,
    OfferArchetype.EXPERIENCIA: OfferDeliveryModel.DWY,
}


def get_enum_options(
    enum_class: type[Enum], metadata: dict[str, dict[str, Any]] = None
) -> list[dict[str, Any]]:
    options = []
    for e in enum_class:
        item = {"value": e.value, "label": e.name.replace("_", " ").title()}
        if metadata and e.value in metadata:
            item.update(metadata[e.value])
        options.append(item)
    return options
