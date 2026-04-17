"""Enums domain module."""

from enum import Enum, StrEnum
from typing import Any


class OfferArchetype(StrEnum):
    """Offer Archetype enumeration."""

    PRODUCTO = "producto"  # ProductDetails
    PROGRAMA = "programa"  # ProgramDetails
    SERVICIO = "servicio"  # ServiceDetails
    MEMBRESIA = "membresia"  # SubscriptionDetails
    EXPERIENCIA = "experiencia"  # EventDetails


class OfferValueLevel(StrEnum):
    """Offer Value Level enumeration."""

    LEAD_MAGNET = "lead_magnet"
    ACTIVACION = "activacion"
    TRANSFORMACION = "transformacion"
    MAXIMIZACION = "maximizacion"
    CORPORATIVO = "corporativo"


class OfferDeliveryModel(StrEnum):
    """Offer Delivery Model enumeration."""

    DIY = "diy"  # Do It Yourself (Courses, Ebooks)
    DWY = "dwy"  # Done With You (Coaching, Mentorship)
    DFY = "dfy"  # Done For You (Agency, Service)
    HYBRID = "hybrid"  # Mix


class OfferStatus(StrEnum):
    """Offer Status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    WAITLIST = "waitlist"
    SOLD_OUT = "sold_out"


class AssetType(StrEnum):
    """Asset Type enumeration."""

    FLYER = "flyer"
    VIDEO = "video"
    CAROUSEL = "carousel"
    DOCUMENT = "document"
    IMAGE = "image"


class AssetSource(StrEnum):
    """Asset Source enumeration."""

    AI = "ai"
    EXTERNAL = "external"


class AssetStatus(StrEnum):
    """Asset Status enumeration."""

    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class KnowledgeSourceType(StrEnum):
    """Knowledge Source Type enumeration."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    VIDEO = "video"
    URL_YOUTUBE = "url_youtube"
    URL_ARTICLE = "url_article"
    URL_GOOGLE_DOC = "url_google_doc"


class KnowledgeSourceStatus(StrEnum):
    """Knowledge Source Status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class LandingJobStatus(StrEnum):
    """Landing Job Status enumeration."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class GuaranteeType(StrEnum):
    """Guarantee Type enumeration."""

    NONE = "none"
    CONDITIONAL_ACTION_BASED = "conditional_action_based"  # "Si haces X y no funciona, te devuelvo"
    UNCONDITIONAL_30_DAY = "unconditional_30_day"
    DOUBLE_MONEY_BACK = "double_money_back"
    SATISFACTION_OR_FREE_WORK = "satisfaction_or_free_work"


class PaymentPlanType(StrEnum):
    """Payment Plan Type enumeration."""

    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    PAYMENT_PLAN = "payment_plan"  # e.g. 3x $500


class DeliverableFormat(StrEnum):
    """Deliverable Format enumeration."""

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
    """Access Duration enumeration."""

    LIFETIME = "lifetime"
    LIMITED_TIME = "limited_time"  # Requires end date or duration
    SUBSCRIPTION_ACTIVE = "subscription_active"


class PrerequisiteType(StrEnum):
    """Prerequisite Type enumeration."""

    NONE = "none"
    APPLICATION_APPROVED = "application_approved"
    PRIOR_PROGRAM_COMPLETION = "prior_program_completion"
    INCOME_LEVEL = "income_level"


class OnboardingMechanism(StrEnum):
    """Onboarding Mechanism enumeration."""

    INSTANT_ACCESS_EMAIL = "instant_access_email"
    BOOK_KICKOFF_CALL = "book_kickoff_call"
    FILL_INTAKE_FORM = "fill_intake_form"
    JOIN_COMMUNITY = "join_community"


class EventLocationType(StrEnum):
    """Event Location Type enumeration."""

    VIRTUAL = "virtual"
    PHYSICAL_LOCAL = "physical_local"
    DESTINATION_RETREAT = "destination_retreat"


class BillingFrequency(StrEnum):
    """Billing Frequency enumeration."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONE_OFF = "one_off"


class FulfillmentType(StrEnum):
    """Fulfillment Type enumeration."""

    DIGITAL_DOWNLOAD = "digital_download"
    LMS_ACCESS = "lms_access"
    PHYSICAL_SHIPPING = "physical_shipping"
    MANUAL_PROVISIONING = "manual_provisioning"


class DigitalFormat(StrEnum):
    """Digital Format enumeration."""

    PDF_EBOOK = "pdf_ebook"
    VIDEO_COURSE = "video_course"
    AUDIO_SERIES = "audio_series"
    NOTION_TEMPLATE = "notion_template"
    SOFTWARE_SAAS = "software_access"
    PHYSICAL_ITEM = "physical_item"  # Fallback


class ProgramStructure(StrEnum):
    """Program Structure enumeration."""

    FIXED_COHORT = "fixed_cohort"  # Start/End Date Fixed
    ROLLING_ADMISSION = "rolling_admission"  # Start anytime, N weeks duration
    CHALLENGE = "challenge"  # Fixed short duration (e.g. 5 days)
    MEMBERSHIP = "membership"  # Ongoing


class LiveInteractionType(StrEnum):
    """Live Interaction Type enumeration."""

    NONE = "none"
    GROUP_Q_AND_A = "group_q_and_a"
    ONE_ON_ONE_CHECKINS = "one_on_one_checkins"
    HOT_SEATS = "hot_seats"
    WORKSHOPS = "workshops"


class CommunityPlatform(StrEnum):
    """Community Platform enumeration."""

    NONE = "none"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SKOOL = "skool"
    CIRCLE = "circle"
    FACEBOOK_GROUP = "facebook_group"
    SLACK = "slack"


class ServiceCategory(StrEnum):
    """Service for category operations."""

    ADVISORY = "advisory"  # Selling Wisdom (Consulting)
    AGENCY = "agency"  # Selling Hands (Done For You)
    AUTHORITY = "authority"  # Selling Influence (Sponsorships)


class InteractionMode(StrEnum):
    """Interaction Mode enumeration."""

    SYNC = "sync"  # Real time calls
    ASYNC = "async"  # Loom/Email/Docs
    HYBRID = "hybrid"


class ServiceFrequency(StrEnum):
    """Service for frequency operations."""

    ONE_OFF = "one_off"  # Project based
    RETAINER = "retainer"  # Ongoing


class AccommodationType(StrEnum):
    """Accommodation Type enumeration."""

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


def get_enum_options(
    enum_class: type[Enum],
    metadata: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve enum options."""
    options = []
    for e in enum_class:
        item = {"value": e.value, "label": e.name.replace("_", " ").title()}
        if metadata and e.value in metadata:
            item.update(metadata[e.value])
        options.append(item)
    return options
