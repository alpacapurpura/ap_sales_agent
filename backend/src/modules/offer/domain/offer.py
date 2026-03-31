from typing import List, Optional, Union, Dict, Type, Any
from uuid import UUID
from pydantic import Field, model_validator, computed_field
from src.shared.domain.base_entity import BaseEntity
from src.modules.offer.domain.enums import (
    OfferType, OfferArchetype, OfferDeliveryModel, GuaranteeType, OfferStatus, DeliverableFormat,
    OfferValueLevel, PaymentPlanType, AccessDuration, PrerequisiteType, OnboardingMechanism,
    OFFER_METADATA, ARCHETYPE_DEFAULT_DELIVERY
)
from src.modules.crm.domain.enums import FinancialCapacity, AvatarPersona
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.offer.domain.details import (
    ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails
)

# --- ARCHETYPE → DETAILS MAPPING ---
ARCHETYPE_TO_DETAILS_MAPPING: Dict[OfferArchetype, Type[BaseEntity]] = {
    OfferArchetype.PRODUCTO: ProductDetails,
    OfferArchetype.PROGRAMA: ProgramDetails,
    OfferArchetype.SERVICIO: ServiceDetails,
    OfferArchetype.MEMBRESIA: SubscriptionDetails,
    OfferArchetype.EXPERIENCIA: EventDetails,
}

# --- LEGACY TYPE → DETAILS MAPPING ---
OFFER_TYPE_TO_DETAILS_MAPPING: Dict[OfferType, Type[BaseEntity]] = {
    # LEVEL 0
    OfferType.FREE_RESOURCE: ProductDetails,
    OfferType.COMMUNITY_LITE: SubscriptionDetails,
    OfferType.CONTENT_ASSET_PODCAST: ProductDetails,
    OfferType.FREE_WEBINAR_CHALLENGE: ProgramDetails,

    # LEVEL 1
    OfferType.TRIPWIRE_OFFER: ProductDetails,
    OfferType.SELF_PACED_COURSE: ProductDetails,
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION: SubscriptionDetails,
    OfferType.PHYSICAL_MERCH: ProductDetails,

    # LEVEL 2
    OfferType.HYBRID_MENTORSHIP: ProgramDetails,
    OfferType.COHORT_BASED_COURSE: ProgramDetails,
    OfferType.GROUP_COACHING_PROGRAM: ProgramDetails,

    # LEVEL 3
    OfferType.VIP_DAY_STRATEGY: ServiceDetails,
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING: ServiceDetails,
    OfferType.DEEP_DIVE_AUDIT: ServiceDetails,

    # LEVEL 4
    OfferType.PRODUCTIZED_SERVICE: ServiceDetails,
    OfferType.ECOMMERCE_DEVELOPMENT: ServiceDetails,
    OfferType.MONTHLY_RETAINER: ServiceDetails,
    OfferType.PERFORMANCE_REV_SHARE: ServiceDetails,

    # LEVEL 5
    OfferType.MASTERMIND_NETWORK: EventDetails,
    OfferType.LUXURY_RETREAT: EventDetails,

    # LEVEL 6
    OfferType.CORPORATE_TRAINING: ServiceDetails,
    OfferType.BRAND_SPONSORSHIP: ServiceDetails,
    OfferType.KEYNOTE_SPEAKING: ServiceDetails,
}

class PricingStructure(BaseEntity):
    label: str
    plan_type: Optional[PaymentPlanType] = None
    total_amount: float
    deposit_required: float = 0.0
    number_of_installments: int = 1
    installment_amount: float = 0.0
    is_default: bool = False
    savings_claim: Optional[str] = None

class DeliverableItem(BaseEntity):
    name: str
    format: DeliverableFormat
    quantity: str
    value_stack_price: float

class ObjectionItem(BaseEntity):
    """An anticipated objection with a rebuttal strategy for the Sales Agent."""
    id: Optional[str] = None
    type: str  # e.g. "price", "time", "trust", "partner", "custom"
    trigger_phrases: List[str] = []  # semantic anchors for SemanticRouter
    strategy: str = ""  # e.g. "ROI Reframing", "Paradox", "Risk Reversal"
    rebuttal: str = ""  # the actual script/response

class Offer(BaseEntity):
    """
    La Entidad Oferta Maestra con Detalles Polimórficos.
    """
    id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    internal_sku: str
    public_name: str
    type: OfferType

    # New archetype system (nullable for legacy data)
    archetype: Optional[OfferArchetype] = None
    format_hint: Optional[str] = None
    is_lead_magnet: bool = False
    
    value_level: Optional[OfferValueLevel] = Field(None, validation_alias="offer_value_level")
    delivery_model: Optional[OfferDeliveryModel] = None
    
    headline_promise: str
    target_avatar_match: List[AvatarPersona]
    primary_outcome: str
    time_to_value: str
    
    access_duration: Optional[AccessDuration] = None
    access_duration_text: Optional[str] = None
    support_duration_days: Optional[int] = None
    instructors: List[str] = []
    
    requires_application: bool
    min_financial_capacity: FinancialCapacity
    prerequisites: List[Union[PrerequisiteType, str]] = []
    anti_avatar_keywords: List[str] = []
    
    pricing_options: List[PricingStructure]
    price_pay_in_full: Optional[float] = None
    currency: str = "USD"
    
    guarantee_type: GuaranteeType
    guarantee_terms: str
    
    downsell_offer_id: Optional[UUID] = None
    upsell_offer_id: Optional[UUID] = None
    includes_offers: List[UUID] = []
    deliverables: List[DeliverableItem] = []

    onboarding_action: Optional[OnboardingMechanism] = None
    onboarding_url: Optional[str] = None
    
    vsl_link: Optional[str] = None
    checkout_page_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    
    marketing_pain_points: List[str] = []
    marketing_desires: List[str] = []
    objections: List[ObjectionItem] = []
    metadata_info: Dict[str, Any] = {}

    status: OfferStatus
    
    specific_details: Optional[Union[ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails]] = None

    landing_page_config: Optional[LandingPageConfig] = None

    @computed_field
    @property
    def shows_as_lead_magnet(self) -> bool:
        """Auto-detect from price OR manual flag."""
        if self.is_lead_magnet:
            return True
        if self.pricing_options:
            return all(p.total_amount == 0 for p in self.pricing_options)
        return self.value_level == OfferValueLevel.LEVEL_0_FREE

    @model_validator(mode='after')
    def validate_consistency(self):
        # Dual dispatch: archetype takes priority over legacy type
        if self.archetype:
            # Archetype-based dispatch
            if self.delivery_model is None:
                self.delivery_model = ARCHETYPE_DEFAULT_DELIVERY.get(self.archetype)

            expected_detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(self.archetype)
            if expected_detail_class and self.specific_details is not None:
                if not isinstance(self.specific_details, expected_detail_class):
                    raise ValueError(
                        f"Polymorphism Error: Archetype {self.archetype.value} expects "
                        f"{expected_detail_class.__name__}, got {type(self.specific_details).__name__}"
                    )
        elif self.type:
            # Legacy type-based dispatch
            meta = OFFER_METADATA.get(self.type.value, {})
            expected_level = meta.get("level")
            default_delivery = meta.get("default_delivery")

            if self.value_level is None:
                self.value_level = expected_level

            if self.delivery_model is None:
                self.delivery_model = default_delivery

            expected_detail_class = OFFER_TYPE_TO_DETAILS_MAPPING.get(self.type)
            if expected_detail_class and self.specific_details is not None:
                if not isinstance(self.specific_details, expected_detail_class):
                    raise ValueError(
                        f"Polymorphism Error: Expected {expected_detail_class.__name__}, "
                        f"got {type(self.specific_details).__name__}"
                    )

        return self

class OfferIdentityUpdate(BaseEntity):
    internal_sku: Optional[str] = None
    public_name: Optional[str] = None
    type: Optional[OfferType] = None

class OfferStrategyUpdate(BaseEntity):
    value_level: Optional[OfferValueLevel] = Field(None, validation_alias="offer_value_level")
    delivery_model: Optional[OfferDeliveryModel] = None

class OfferPromiseUpdate(BaseEntity):
    headline_promise: Optional[str] = None
    primary_outcome: Optional[str] = None
    time_to_value: Optional[str] = None

class OfferPsychologyUpdate(BaseEntity):
    target_avatar_match: Optional[List[AvatarPersona]] = None
    anti_avatar_keywords: Optional[List[str]] = None
    marketing_pain_points: Optional[List[str]] = None
    marketing_desires: Optional[List[str]] = None
    objections: Optional[List[ObjectionItem]] = None

class OfferValueStackUpdate(BaseEntity):
    deliverables: Optional[List[DeliverableItem]] = None
    includes_offers: Optional[List[UUID]] = None

class OfferPricingUpdate(BaseEntity):
    pricing_options: Optional[List[PricingStructure]] = None
    price_pay_in_full: Optional[float] = None
    currency: Optional[str] = None

class OfferDetailsUpdate(BaseEntity):
    specific_details: Optional[Union[ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails]] = None
    access_duration: Optional[AccessDuration] = None
    access_duration_text: Optional[str] = None
    support_duration_days: Optional[int] = None

class OfferVisualsUpdate(BaseEntity):
    vsl_link: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

class OfferClosingUpdate(BaseEntity):
    guarantee_type: Optional[GuaranteeType] = None
    guarantee_terms: Optional[str] = None
    checkout_page_url: Optional[str] = None
    calendar_type_id: Optional[str] = None
    onboarding_action: Optional[OnboardingMechanism] = None
    onboarding_url: Optional[str] = None
    downsell_offer_id: Optional[UUID] = None
    upsell_offer_id: Optional[UUID] = None

class OfferResourcesUpdate(BaseEntity):
    landing_page_config: Optional[LandingPageConfig] = None

class OfferInstructorsUpdate(BaseEntity):
    instructors: Optional[List[str]] = None
