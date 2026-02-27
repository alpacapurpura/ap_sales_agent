from enum import Enum
from typing import Dict, Any, List, Type

class OfferType(str, Enum):
    # Level 0: Free & Lead Magnets
    FREE_RESOURCE = "free_resource"
    COMMUNITY_LITE = "community_lite"
    CONTENT_ASSET_PODCAST = "content_asset_podcast"
    FREE_WEBINAR_CHALLENGE = "free_webinar_challenge"

    # Level 1: Low Ticket ($7 - $97)
    TRIPWIRE_OFFER = "tripwire_offer"
    SELF_PACED_COURSE = "self_paced_course"
    PAID_NEWSLETTER_SUBSCRIPTION = "paid_newsletter_subscription"
    PHYSICAL_MERCH = "physical_merch"

    # Level 2: Mid Ticket ($297 - $997)
    HYBRID_MENTORSHIP = "hybrid_mentorship"
    COHORT_BASED_COURSE = "cohort_based_course"
    GROUP_COACHING_PROGRAM = "group_coaching_program"

    # Level 3: High Ticket ($2k - $10k)
    VIP_DAY_STRATEGY = "vip_day_strategy"
    ONE_ON_ONE_PRIVATE_MENTORING = "one_on_one_private_mentoring"
    DEEP_DIVE_AUDIT = "deep_dive_audit"

    # Level 4: Recurring/Retainer ($1k - $5k/mo)
    PRODUCTIZED_SERVICE = "productized_service"
    ECOMMERCE_DEVELOPMENT = "ecommerce_development"
    MONTHLY_RETAINER = "monthly_retainer"
    PERFORMANCE_REV_SHARE = "performance_rev_share"

    # Level 5: Ultra High Ticket ($15k - $100k+)
    MASTERMIND_NETWORK = "mastermind_network"
    LUXURY_RETREAT = "luxury_retreat"

    # Level 6: Corporate/B2B
    CORPORATE_TRAINING = "corporate_training"
    BRAND_SPONSORSHIP = "brand_sponsorship"
    KEYNOTE_SPEAKING = "keynote_speaking"

class OfferValueLevel(str, Enum):
    LEVEL_0_FREE = "level_0_free"
    LEVEL_1_LOW_TICKET = "level_1_low_ticket"
    LEVEL_2_MID_TICKET = "level_2_mid_ticket"
    LEVEL_3_HIGH_TICKET = "level_3_high_ticket"
    LEVEL_4_RECURRING = "level_4_recurring"
    LEVEL_5_ULTRA_HIGH = "level_5_ultra_high"
    LEVEL_6_CORPORATE = "level_6_corporate"

class OfferDeliveryModel(str, Enum):
    DIY = "diy" # Do It Yourself (Courses, Ebooks)
    DWY = "dwy" # Done With You (Coaching, Mentorship)
    DFY = "dfy" # Done For You (Agency, Service)
    HYBRID = "hybrid" # Mix

class OfferStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    WAITLIST = "waitlist"
    SOLD_OUT = "sold_out"

class GuaranteeType(str, Enum):
    NONE = "none"
    CONDITIONAL_ACTION_BASED = "conditional_action_based" # "Si haces X y no funciona, te devuelvo"
    UNCONDITIONAL_30_DAY = "unconditional_30_day"
    DOUBLE_MONEY_BACK = "double_money_back"
    SATISFACTION_OR_FREE_WORK = "satisfaction_or_free_work"

class PaymentPlanType(str, Enum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    PAYMENT_PLAN = "payment_plan" # e.g. 3x $500

class DeliverableFormat(str, Enum):
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    LIVE_SESSION = "live_session"
    TEMPLATE = "template"
    COMMUNITY_ACCESS = "community_access"
    SOFTWARE_ACCESS = "software_access"
    PHYSICAL_ITEM = "physical_item"
    SERVICE_HOURS = "service_hours"

class AccessDuration(str, Enum):
    LIFETIME = "lifetime"
    LIMITED_TIME = "limited_time" # Requires end date or duration
    SUBSCRIPTION_ACTIVE = "subscription_active"

class PrerequisiteType(str, Enum):
    NONE = "none"
    APPLICATION_APPROVED = "application_approved"
    PRIOR_PROGRAM_COMPLETION = "prior_program_completion"
    INCOME_LEVEL = "income_level"

class OnboardingMechanism(str, Enum):
    INSTANT_ACCESS_EMAIL = "instant_access_email"
    BOOK_KICKOFF_CALL = "book_kickoff_call"
    FILL_INTAKE_FORM = "fill_intake_form"
    JOIN_COMMUNITY = "join_community"

class EventLocationType(str, Enum):
    VIRTUAL = "virtual"
    PHYSICAL_LOCAL = "physical_local"
    DESTINATION_RETREAT = "destination_retreat"

class BillingFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ONE_OFF = "one_off"

class FulfillmentType(str, Enum):
    DIGITAL_DOWNLOAD = "digital_download"
    LMS_ACCESS = "lms_access"
    PHYSICAL_SHIPPING = "physical_shipping"
    MANUAL_PROVISIONING = "manual_provisioning"

class DigitalFormat(str, Enum):
    PDF_EBOOK = "pdf_ebook"
    VIDEO_COURSE = "video_course"
    AUDIO_SERIES = "audio_series"
    NOTION_TEMPLATE = "notion_template"
    SOFTWARE_SAAS = "software_access"
    PHYSICAL_ITEM = "physical_item" # Fallback

class ProgramStructure(str, Enum):
    FIXED_COHORT = "fixed_cohort" # Start/End Date Fixed
    ROLLING_ADMISSION = "rolling_admission" # Start anytime, N weeks duration
    CHALLENGE = "challenge" # Fixed short duration (e.g. 5 days)
    MEMBERSHIP = "membership" # Ongoing

class LiveInteractionType(str, Enum):
    NONE = "none"
    GROUP_Q_AND_A = "group_q_and_a"
    ONE_ON_ONE_CHECKINS = "one_on_one_checkins"
    HOT_SEATS = "hot_seats"
    WORKSHOPS = "workshops"

class CommunityPlatform(str, Enum):
    NONE = "none"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SKOOL = "skool"
    CIRCLE = "circle"
    FACEBOOK_GROUP = "facebook_group"
    SLACK = "slack"

class ServiceCategory(str, Enum):
    ADVISORY = "advisory" # Selling Wisdom (Consulting)
    AGENCY = "agency" # Selling Hands (Done For You)
    AUTHORITY = "authority" # Selling Influence (Sponsorships)

class InteractionMode(str, Enum):
    SYNC = "sync" # Real time calls
    ASYNC = "async" # Loom/Email/Docs
    HYBRID = "hybrid"

class ServiceFrequency(str, Enum):
    ONE_OFF = "one_off" # Project based
    RETAINER = "retainer" # Ongoing

class AccommodationType(str, Enum):
    NOT_INCLUDED = "not_included"
    SHARED_ROOM = "shared_room"
    PRIVATE_ROOM = "private_room"
    LUXURY_SUITE = "luxury_suite"

# --- METADATA REGISTRY ---
OFFER_METADATA: Dict[str, Dict[str, Any]] = {
    OfferType.FREE_RESOURCE.value: {"level": OfferValueLevel.LEVEL_0_FREE, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.COMMUNITY_LITE.value: {"level": OfferValueLevel.LEVEL_0_FREE, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.CONTENT_ASSET_PODCAST.value: {"level": OfferValueLevel.LEVEL_0_FREE, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.FREE_WEBINAR_CHALLENGE.value: {"level": OfferValueLevel.LEVEL_0_FREE, "default_delivery": OfferDeliveryModel.DWY},

    OfferType.TRIPWIRE_OFFER.value: {"level": OfferValueLevel.LEVEL_1_LOW_TICKET, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.SELF_PACED_COURSE.value: {"level": OfferValueLevel.LEVEL_1_LOW_TICKET, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION.value: {"level": OfferValueLevel.LEVEL_1_LOW_TICKET, "default_delivery": OfferDeliveryModel.DIY},
    OfferType.PHYSICAL_MERCH.value: {"level": OfferValueLevel.LEVEL_1_LOW_TICKET, "default_delivery": OfferDeliveryModel.DIY},

    OfferType.HYBRID_MENTORSHIP.value: {"level": OfferValueLevel.LEVEL_2_MID_TICKET, "default_delivery": OfferDeliveryModel.DWY},
    OfferType.COHORT_BASED_COURSE.value: {"level": OfferValueLevel.LEVEL_2_MID_TICKET, "default_delivery": OfferDeliveryModel.DWY},
    OfferType.GROUP_COACHING_PROGRAM.value: {"level": OfferValueLevel.LEVEL_2_MID_TICKET, "default_delivery": OfferDeliveryModel.DWY},

    OfferType.VIP_DAY_STRATEGY.value: {"level": OfferValueLevel.LEVEL_3_HIGH_TICKET, "default_delivery": OfferDeliveryModel.DWY},
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING.value: {"level": OfferValueLevel.LEVEL_3_HIGH_TICKET, "default_delivery": OfferDeliveryModel.DWY},
    OfferType.DEEP_DIVE_AUDIT.value: {"level": OfferValueLevel.LEVEL_3_HIGH_TICKET, "default_delivery": OfferDeliveryModel.DFY},

    OfferType.PRODUCTIZED_SERVICE.value: {"level": OfferValueLevel.LEVEL_4_RECURRING, "default_delivery": OfferDeliveryModel.DFY},
    OfferType.ECOMMERCE_DEVELOPMENT.value: {"level": OfferValueLevel.LEVEL_4_RECURRING, "default_delivery": OfferDeliveryModel.DFY},
    OfferType.MONTHLY_RETAINER.value: {"level": OfferValueLevel.LEVEL_4_RECURRING, "default_delivery": OfferDeliveryModel.DFY},
    OfferType.PERFORMANCE_REV_SHARE.value: {"level": OfferValueLevel.LEVEL_4_RECURRING, "default_delivery": OfferDeliveryModel.DFY},

    OfferType.MASTERMIND_NETWORK.value: {"level": OfferValueLevel.LEVEL_5_ULTRA_HIGH, "default_delivery": OfferDeliveryModel.HYBRID},
    OfferType.LUXURY_RETREAT.value: {"level": OfferValueLevel.LEVEL_5_ULTRA_HIGH, "default_delivery": OfferDeliveryModel.HYBRID},

    OfferType.CORPORATE_TRAINING.value: {"level": OfferValueLevel.LEVEL_6_CORPORATE, "default_delivery": OfferDeliveryModel.DWY},
    OfferType.BRAND_SPONSORSHIP.value: {"level": OfferValueLevel.LEVEL_6_CORPORATE, "default_delivery": OfferDeliveryModel.DFY},
    OfferType.KEYNOTE_SPEAKING.value: {"level": OfferValueLevel.LEVEL_6_CORPORATE, "default_delivery": OfferDeliveryModel.DWY},
}

GUARANTEE_METADATA: Dict[str, Dict[str, Any]] = {
    GuaranteeType.NONE.value: {"risk_level": "High", "conversion_boost": "None"},
    GuaranteeType.CONDITIONAL_ACTION_BASED.value: {"risk_level": "Medium", "conversion_boost": "High"},
    GuaranteeType.UNCONDITIONAL_30_DAY.value: {"risk_level": "Low", "conversion_boost": "Very High"},
    GuaranteeType.DOUBLE_MONEY_BACK.value: {"risk_level": "Very Low", "conversion_boost": "Extreme"},
    GuaranteeType.SATISFACTION_OR_FREE_WORK.value: {"risk_level": "Medium", "conversion_boost": "High"},
}

def get_enum_options(enum_class: Type[Enum], metadata: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    options = []
    for e in enum_class:
        item = {"value": e.value, "label": e.name.replace("_", " ").title()}
        if metadata and e.value in metadata:
            item.update(metadata[e.value])
        options.append(item)
    return options
