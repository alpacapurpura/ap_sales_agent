"""Offer domain module."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, computed_field, model_validator

from src.modules.offer.domain.archetype_catalog import get_capabilities
from src.modules.offer.domain.details import (
    EventDetails,
    ProductDetails,
    ProgramDetails,
    ServiceDetails,
    SubscriptionDetails,
)
from src.modules.offer.domain.enums import (
    AccessDuration,
    DeliverableFormat,
    GuaranteeType,
    OfferArchetype,
    OfferDeliveryModel,
    OfferStatus,
    OfferValueLevel,
    OnboardingMechanism,
    PaymentPlanType,
    PrerequisiteType,
)
from src.shared.domain.base_entity import BaseEntity
from src.shared.domain.enums import AvatarPersona, FinancialCapacity

# --- ARCHETYPE → DETAILS MAPPING ---
ARCHETYPE_TO_DETAILS_MAPPING: dict[OfferArchetype, type[BaseEntity]] = {
    OfferArchetype.PRODUCTO: ProductDetails,
    OfferArchetype.PROGRAMA: ProgramDetails,
    OfferArchetype.SERVICIO: ServiceDetails,
    OfferArchetype.MEMBRESIA: SubscriptionDetails,
    OfferArchetype.EXPERIENCIA: EventDetails,
}


class PricingStructure(BaseEntity):
    """Pricing Structure."""

    label: str
    plan_type: PaymentPlanType | None = None
    total_amount: float
    # Optional ISO 4217 override for this plan. When None the offer falls
    # back to ``Offer.currency`` (which in turn falls back to the tenant
    # locale). A plan may legitimately bill in a different currency than
    # the offer's default (e.g. USD for corporate tier, PEN for local).
    currency: str | None = None
    deposit_required: float = 0.0
    number_of_installments: int = 1
    installment_amount: float = 0.0
    is_default: bool = False
    savings_claim: str | None = None
    # Membership tier fields (stored in JSONB, no migration needed)
    benefits: list[str] = []
    is_highlighted: bool = False
    cta_text: str | None = None


class DeliverableItem(BaseEntity):
    """Deliverable Item."""

    name: str
    format: DeliverableFormat
    quantity: str
    value_stack_price: float


class ObjectionItem(BaseEntity):
    """An anticipated objection with a rebuttal strategy for the Sales Agent."""

    id: str | None = None
    type: str  # e.g. "price", "time", "trust", "partner", "custom"
    trigger_phrases: list[str] = []  # semantic anchors for SemanticRouter
    strategy: str = ""  # e.g. "ROI Reframing", "Paradox", "Risk Reversal"
    rebuttal: str = ""  # the actual script/response


class Offer(BaseEntity):
    """La Entidad Oferta Maestra con Detalles Polimórficos."""

    id: UUID | None = None
    tenant_id: UUID | None = None
    internal_sku: str
    public_name: str
    archetype: OfferArchetype
    format_hint: str | None = None
    # 7th SSoT axis link (Sprint 12 + 14). Optional string key into
    # ``OFFER_TYPE_PRESET_CATALOG``. Nullable because legacy offers and
    # offers created before the wizard rehaul (Sprint 13) will lack it.
    # Drives sales-agent grounding, analytics segmentation and landing
    # generator templates without touching the archetype tag.
    preset_id: str | None = None
    is_lead_magnet: bool = False
    # Wizard-driven: does this offer run in editions/cohorts/batches?
    # Default resolves in validate_consistency based on archetype
    # (True for PROGRAMA/SERVICIO/EXPERIENCIA, False for PRODUCTO/MEMBRESIA).
    has_editions: bool | None = None

    value_level: OfferValueLevel | None = Field(
        None,
        serialization_alias="offer_value_level",
    )
    delivery_model: OfferDeliveryModel | None = None

    headline_promise: str
    target_avatar_match: list[AvatarPersona]
    primary_outcome: str
    time_to_value: str

    access_duration: AccessDuration | None = None
    access_duration_text: str | None = None
    support_duration_days: int | None = None
    instructors: list[str] = []

    requires_application: bool
    min_financial_capacity: FinancialCapacity
    prerequisites: list[PrerequisiteType | str] = []
    anti_avatar_keywords: list[str] = []

    pricing_options: list[PricingStructure]
    price_pay_in_full: float | None = None
    # Optional: resolved to TenantLocale.currency at the application layer
    # when absent. Do not default to a hardcoded ISO code here.
    currency: str | None = None

    guarantee_type: GuaranteeType
    guarantee_terms: str

    downsell_offer_id: UUID | None = None
    upsell_offer_id: UUID | None = None
    includes_offers: list[UUID] = []
    deliverables: list[DeliverableItem] = []

    onboarding_action: OnboardingMechanism | None = None
    onboarding_url: str | None = None

    vsl_link: str | None = None
    checkout_page_url: str | None = None
    calendar_type_id: str | None = None

    marketing_pain_points: list[str] = []
    marketing_desires: list[str] = []
    objections: list[ObjectionItem] = []
    metadata_info: dict[str, Any] = {}

    status: OfferStatus

    # Lifecycle (SaaS archive + soft-delete)
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    specific_details: ProductDetails | ServiceDetails | ProgramDetails | SubscriptionDetails | EventDetails | None = (
        None
    )

    landing_page_config: dict[str, Any] | None = None

    @computed_field
    @property
    def shows_as_lead_magnet(self) -> bool:
        """Only True when the user explicitly marks the offer as lead magnet."""
        return self.is_lead_magnet

    @property
    def is_archived(self) -> bool:
        """Check if archived."""
        return self.archived_at is not None

    @property
    def is_deleted(self) -> bool:
        """Check if deleted."""
        return self.deleted_at is not None

    @model_validator(mode="after")
    def validate_consistency(self) -> Offer:
        """Validate consistency."""
        capabilities = get_capabilities(self.archetype)

        if self.delivery_model is None:
            self.delivery_model = capabilities.default_delivery

        # Archetype-aware enforcement for has_editions. PRODUCTO and MEMBRESIA
        # never have editions (capabilities.supports_editions == False).
        # Archetypes that do support editions default to True unless
        # explicitly set by the wizard.
        if not capabilities.supports_editions:
            self.has_editions = False
        elif self.has_editions is None:
            self.has_editions = True

        expected_detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(self.archetype)
        if (
            expected_detail_class
            and self.specific_details is not None
            and not isinstance(self.specific_details, expected_detail_class)
        ):
            msg = (
                f"Polymorphism Error: Archetype {self.archetype.value} expects "
                f"{expected_detail_class.__name__}, got {type(self.specific_details).__name__}"
            )
            raise ValueError(msg)

        return self


class OfferIdentityUpdate(BaseEntity):
    """Offer Identity Update."""

    internal_sku: str | None = None
    public_name: str | None = None


class OfferStrategyUpdate(BaseEntity):
    """Offer Strategy Update."""

    value_level: OfferValueLevel | None = Field(
        None,
        serialization_alias="offer_value_level",
    )
    delivery_model: OfferDeliveryModel | None = None


class OfferPromiseUpdate(BaseEntity):
    """Offer Promise Update."""

    headline_promise: str | None = None
    primary_outcome: str | None = None
    time_to_value: str | None = None


class OfferPsychologyUpdate(BaseEntity):
    """Offer Psychology Update."""

    target_avatar_match: list[AvatarPersona] | None = None
    anti_avatar_keywords: list[str] | None = None
    marketing_pain_points: list[str] | None = None
    marketing_desires: list[str] | None = None
    objections: list[ObjectionItem] | None = None


class OfferValueStackUpdate(BaseEntity):
    """Offer Value Stack Update."""

    deliverables: list[DeliverableItem] | None = None
    includes_offers: list[UUID] | None = None


class OfferPricingUpdate(BaseEntity):
    """Offer Pricing Update."""

    pricing_options: list[PricingStructure] | None = None
    price_pay_in_full: float | None = None
    currency: str | None = None


class OfferDetailsUpdate(BaseEntity):
    """Offer Details Update."""

    specific_details: ProductDetails | ServiceDetails | ProgramDetails | SubscriptionDetails | EventDetails | None = (
        None
    )
    access_duration: AccessDuration | None = None
    access_duration_text: str | None = None
    support_duration_days: int | None = None


class OfferVisualsUpdate(BaseEntity):
    """Offer Visuals Update."""

    vsl_link: str | None = None
    metadata_info: dict[str, Any] | None = None


class OfferClosingUpdate(BaseEntity):
    """Offer Closing Update."""

    guarantee_type: GuaranteeType | None = None
    guarantee_terms: str | None = None
    checkout_page_url: str | None = None
    calendar_type_id: str | None = None
    onboarding_action: OnboardingMechanism | None = None
    onboarding_url: str | None = None
    downsell_offer_id: UUID | None = None
    upsell_offer_id: UUID | None = None


class OfferResourcesUpdate(BaseEntity):
    """Offer Resources Update."""

    landing_page_config: dict[str, Any] | None = None


class OfferInstructorsUpdate(BaseEntity):
    """Offer Instructors Update."""

    instructors: list[str] | None = None
