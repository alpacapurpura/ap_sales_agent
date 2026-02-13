from typing import Dict, List
from src.core.domain.offer_enums import OfferType
from src.core.domain.landing_page.enums import LandingPageArchetype

# Strategic Matrix: OfferType -> Default Archetype
# This map implements the specific business logic defined by the user.
OFFER_TO_ARCHETYPE_MAP: Dict[OfferType, LandingPageArchetype] = {
    # 1. The Squeeze (Captura Pura)
    OfferType.FREE_RESOURCE: LandingPageArchetype.THE_SQUEEZE,
    OfferType.COMMUNITY_LITE: LandingPageArchetype.THE_SQUEEZE,
    # Note: PAID_NEWSLETTER can be Squeeze (cheap) or Flash (standard). 
    # Defaulting to Squeeze for low-friction entry, can be overridden.
    
    # 2. The Event (Registro con Urgencia)
    OfferType.FREE_WEBINAR_CHALLENGE: LandingPageArchetype.THE_EVENT,
    OfferType.CONTENT_ASSET_PODCAST: LandingPageArchetype.THE_EVENT,

    # 3. The Flash Offer (Venta Lógica / Tripwire)
    OfferType.TRIPWIRE_OFFER: LandingPageArchetype.THE_FLASH_OFFER,
    OfferType.SELF_PACED_COURSE: LandingPageArchetype.THE_FLASH_OFFER,
    OfferType.PHYSICAL_MERCH: LandingPageArchetype.THE_FLASH_OFFER,
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION: LandingPageArchetype.THE_FLASH_OFFER, # Moving standard paid newsletter here

    # 4. The Transformer (Carta de Ventas Larga)
    OfferType.HYBRID_MENTORSHIP: LandingPageArchetype.THE_TRANSFORMER,
    OfferType.COHORT_BASED_COURSE: LandingPageArchetype.THE_TRANSFORMER,
    OfferType.GROUP_COACHING_PROGRAM: LandingPageArchetype.THE_TRANSFORMER,
    # VIP Day direct sale fits here
    
    # 5. The Velvet Rope (Aplicación / High-Ticket)
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING: LandingPageArchetype.THE_VELVET_ROPE,
    OfferType.DEEP_DIVE_AUDIT: LandingPageArchetype.THE_VELVET_ROPE,
    OfferType.MASTERMIND_NETWORK: LandingPageArchetype.THE_VELVET_ROPE,
    OfferType.LUXURY_RETREAT: LandingPageArchetype.THE_VELVET_ROPE,
    OfferType.VIP_DAY_STRATEGY: LandingPageArchetype.THE_VELVET_ROPE, # Defaulting VIP Day to Application

    # 6. The Brochure (Servicios B2B / Corporativo)
    OfferType.PRODUCTIZED_SERVICE: LandingPageArchetype.THE_BROCHURE,
    OfferType.MONTHLY_RETAINER: LandingPageArchetype.THE_BROCHURE,
    OfferType.PERFORMANCE_REV_SHARE: LandingPageArchetype.THE_BROCHURE,
    OfferType.CORPORATE_TRAINING: LandingPageArchetype.THE_BROCHURE,
    OfferType.KEYNOTE_SPEAKING: LandingPageArchetype.THE_BROCHURE,
    OfferType.BRAND_SPONSORSHIP: LandingPageArchetype.THE_BROCHURE,
}

def get_default_archetype(offer_type: OfferType) -> LandingPageArchetype:
    """
    Returns the strategic default archetype for a given offer type.
    Falls back to THE_SQUEEZE if not explicitly mapped.
    """
    return OFFER_TO_ARCHETYPE_MAP.get(offer_type, LandingPageArchetype.THE_SQUEEZE)

def get_available_archetypes(offer_type: OfferType) -> List[LandingPageArchetype]:
    """
    Future-proofing: Returns a list of valid archetypes for an offer type.
    Currently returns the default, but ready for multi-option expansion.
    """
    default = get_default_archetype(offer_type)
    # TODO: Add alternative mappings here (e.g. Webinar could be Event or Squeeze)
    return [default]
