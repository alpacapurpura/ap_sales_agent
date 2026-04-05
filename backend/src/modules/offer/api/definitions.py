from typing import Any

from fastapi import APIRouter

from src.modules.offer.domain.enums import (
    GUARANTEE_METADATA,
    AccessDuration,
    AccommodationType,
    BillingFrequency,
    CommunityPlatform,
    DeliverableFormat,
    DigitalFormat,
    EventLocationType,
    FulfillmentType,
    GuaranteeType,
    InteractionMode,
    LiveInteractionType,
    OfferArchetype,
    OfferDeliveryModel,
    OfferStatus,
    OfferValueLevel,
    OnboardingMechanism,
    PaymentPlanType,
    PrerequisiteType,
    ProgramStructure,
    ServiceCategory,
    ServiceFrequency,
    get_enum_options,
)
from src.shared.domain.enums import AvatarPersona, FinancialCapacity, LeadTemperature

router = APIRouter(tags=["System Definitions"])


@router.get("/definitions/offer-studio", response_model=dict[str, Any])
async def get_offer_studio_definitions():
    """
    Returns all the Enum options and Metadata required to build the Offer Studio Form dynamically.
    Includes rich descriptions, hints, and value mapping.
    """
    return {
        "offer_archetypes": get_enum_options(OfferArchetype),
        "offer_value_levels": get_enum_options(OfferValueLevel),
        "delivery_models": get_enum_options(OfferDeliveryModel),
        "guarantee_types": get_enum_options(GuaranteeType, GUARANTEE_METADATA),
        "offer_statuses": get_enum_options(OfferStatus),
        "deliverable_formats": get_enum_options(DeliverableFormat),
        "payment_plan_types": get_enum_options(PaymentPlanType),
        "access_durations": get_enum_options(AccessDuration),
        "prerequisite_types": get_enum_options(PrerequisiteType),
        "onboarding_mechanisms": get_enum_options(OnboardingMechanism),
        "event_location_types": get_enum_options(EventLocationType),
        "billing_frequencies": get_enum_options(BillingFrequency),
        "digital_formats": get_enum_options(DigitalFormat),
        "fulfillment_types": get_enum_options(FulfillmentType),
        "program_structures": get_enum_options(ProgramStructure),
        "live_interaction_types": get_enum_options(LiveInteractionType),
        "community_platforms": get_enum_options(CommunityPlatform),
        "service_categories": get_enum_options(ServiceCategory),
        "interaction_modes": get_enum_options(InteractionMode),
        "service_frequencies": get_enum_options(ServiceFrequency),
        "accommodation_types": get_enum_options(AccommodationType),
        # Lead/Avatar Context for Targeting
        "financial_capacities": get_enum_options(FinancialCapacity),
        "avatar_personas": get_enum_options(AvatarPersona),
        "lead_temperatures": get_enum_options(LeadTemperature),
        # Raw Metadata Maps for client-side logic lookup
        "metadata_map": {"guarantees": GUARANTEE_METADATA},
    }
