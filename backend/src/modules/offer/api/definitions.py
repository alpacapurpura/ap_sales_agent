from fastapi import APIRouter
from typing import Dict, Any
from src.modules.offer.domain.enums import (
    OfferType,
    OfferDeliveryModel,
    GuaranteeType,
    OfferStatus,
    DeliverableFormat,
    OfferValueLevel,
    PaymentPlanType,
    AccessDuration,
    PrerequisiteType,
    OnboardingMechanism,
    EventLocationType,
    BillingFrequency,
    DigitalFormat,
    FulfillmentType,
    ProgramStructure,
    LiveInteractionType,
    CommunityPlatform,
    ServiceCategory,
    InteractionMode,
    ServiceFrequency,
    AccommodationType,
    OFFER_METADATA,
    GUARANTEE_METADATA,
    get_enum_options,
)
from src.modules.sales.domain.lead_enums import FinancialCapacity, AvatarPersona, LeadTemperature

router = APIRouter(tags=["System Definitions"])

@router.get("/definitions/offer-studio", response_model=Dict[str, Any])
async def get_offer_studio_definitions():
    """
    Returns all the Enum options and Metadata required to build the Offer Studio Form dynamically.
    Includes rich descriptions, hints, and value mapping.
    """
    return {
        "offer_types": get_enum_options(OfferType, OFFER_METADATA),
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
        "metadata_map": {
            "offers": OFFER_METADATA,
            "guarantees": GUARANTEE_METADATA
        }
    }
