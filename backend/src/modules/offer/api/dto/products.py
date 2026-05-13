"""Products DTOs."""

import uuid
from typing import Any

from luana_core_offer_studio.domain.enums import OfferArchetype, OfferStatus, OfferValueLevel
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductResponse(BaseModel):
    """Product Response DTO."""

    id: uuid.UUID
    name: str
    status: str

    # Archetype system
    archetype: str
    format_hint: str | None = None
    is_lead_magnet: bool | None = False
    shows_as_lead_magnet: bool | None = False

    # OfferTypePreset (Sprint 12 — 7th SSoT axis). Null for legacy offers
    # pre-backfill or offers created before wizard rehaul (Sprint 13).
    # Frontend renders it as a badge + the agent reads it for grounding.
    preset_id: str | None = None

    # Polymorphic fields
    delivery_model: str | None = None
    offer_value_level: str | None = None
    value_level: str | None = None
    headline_promise: str | None = None
    primary_outcome: str | None = None
    time_to_value: str | None = None
    access_duration: str | None = None
    access_duration_text: str | None = None
    support_duration_days: int | None = None
    target_avatar_match: list[str] | None = []

    marketing_pain_points: list[str] | None = []
    marketing_desires: list[str] | None = []

    before_state: str | None = None
    after_state: str | None = None
    why_now: str | None = None
    measurable_outcomes: list[str] | None = []

    cultural_trust_barriers: list[str] | None = []
    emotional_triggers: list[str] | None = []
    status_drivers: list[str] | None = []
    regret_scenarios: list[str] | None = []

    objections: list[dict[str, Any]] | None = []

    refund_process_description: str | None = None
    urgency_drivers: list[str] | None = []
    scarcity_reason_honest: str | None = None
    bonus_if_act_now: str | None = None
    final_push_copy: str | None = None

    requires_application: bool | None = False
    min_financial_capacity: str | None = None
    prerequisites: list[str] | None = []

    pricing_options: list[dict[str, Any]] | None = []
    currency: str | None = None

    @field_validator("pricing_options", mode="before")
    @classmethod
    def normalize_pricing(cls, v: object) -> list[dict[str, Any]] | object:
        """Normalize pricing."""
        if isinstance(v, dict):
            return [v]
        return v

    guarantee_type: str | None = None
    guarantee_terms: str | None = None

    downsell_product_id: uuid.UUID | None = None
    upsell_product_id: uuid.UUID | None = None
    includes_offers: list[uuid.UUID] | None = []
    deliverables: list[dict[str, Any]] | None = []
    specific_details: dict[str, Any] | None = {}

    metadata_info: dict[str, Any] | None = {}
    avatar_id: uuid.UUID | None = None

    onboarding_action: str | None = None
    onboarding_url: str | None = None
    calendar_type_id: str | None = None
    checkout_page_url: str | None = None
    vsl_link: str | None = None

    landing_page_config: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """Product Create DTO.

    Sprint 13 flow: the wizard sends ``preset_id`` + optional
    ``conditional_answers`` and the service derives ``archetype`` +
    ``is_lead_magnet`` from the catalog. ``archetype`` stays accepted
    (Optional) to preserve backwards compat with older clients + the
    archetype-first IA pipelines.
    """

    name: str
    # Optional since Sprint 13: when ``preset_id`` is set the service
    # derives it. For clients on the legacy path this remains the
    # primary selector.
    archetype: OfferArchetype | None = None
    format_hint: str | None = None
    is_lead_magnet: bool = False
    # Wizard answer: will this offer run in editions/cohorts/batches?
    # None = let the domain apply the archetype-aware default.
    has_editions: bool | None = None
    status: OfferStatus = OfferStatus.DRAFT
    # Wizard Sprint-13+ sends preset_id as primary selector; archetype is
    # then derived from ``OfferTypePreset.archetype``.
    preset_id: str | None = None
    # Wizard Sprint-13+ conditional refinement step. Maps ``question_id``
    # → yes/no answer. The service feeds this into
    # ``resolve_preset_flags`` to promote flags like ``IS_LEAD_MAGNET``
    # or ``SUPPORTS_CAPACITY`` without the client having to know them.
    conditional_answers: dict[str, bool] | None = None

    # Optional fields the wizard can set
    value_level: OfferValueLevel | None = None
    headline_promise: str | None = None
    avatar_id: uuid.UUID | None = None
    # Optional ISO 4217 code. If omitted, the API resolves it from
    # TenantLocale so the offer inherits the tenant's default currency.
    currency: str | None = None
    # Seed pricing structures from the wizard — the first becomes the
    # default ``Standard`` one-time plan. Lead magnets send [].
    pricing_options: list[dict[str, Any]] | None = Field(default=None)
    # Optional polymorphic defaults suggested by the format catalog.
    specific_details: dict[str, Any] | None = None
    delivery_model: str | None = None

    @field_validator("archetype", mode="before")
    @classmethod
    def normalize_archetype(cls, v: object) -> object:
        """Normalize archetype."""
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: object) -> object:
        """Normalize status."""
        if isinstance(v, str):
            return v.lower()
        return v


class ProductUpdate(BaseModel):
    """Product Update DTO."""

    name: str | None = None
    internal_sku: str | None = None
    archetype: OfferArchetype | None = None
    format_hint: str | None = None
    is_lead_magnet: bool | None = None
    has_editions: bool | None = None
    offer_value_level: str | None = None
    delivery_model: str | None = None
    status: str | None = None
    # Allow re-assigning the preset (e.g. user corrects the wizard suggestion).
    preset_id: str | None = None

    headline_promise: str | None = None
    primary_outcome: str | None = None
    time_to_value: str | None = None
    access_duration: str | None = None
    access_duration_text: str | None = None
    support_duration_days: int | None = None
    target_avatar_match: list[str] | None = None

    marketing_pain_points: list[str] | None = None
    marketing_desires: list[str] | None = None

    before_state: str | None = None
    after_state: str | None = None
    why_now: str | None = None
    measurable_outcomes: list[str] | None = None

    cultural_trust_barriers: list[str] | None = None
    emotional_triggers: list[str] | None = None
    status_drivers: list[str] | None = None
    regret_scenarios: list[str] | None = None
    objections: list[dict[str, Any]] | None = None

    refund_process_description: str | None = None
    urgency_drivers: list[str] | None = None
    scarcity_reason_honest: str | None = None
    bonus_if_act_now: str | None = None
    final_push_copy: str | None = None

    requires_application: bool | None = None
    min_financial_capacity: str | None = None
    prerequisites: list[str] | None = None

    pricing_options: list[dict[str, Any]] | None = None
    currency: str | None = None

    guarantee_type: str | None = None
    guarantee_terms: str | None = None

    downsell_product_id: uuid.UUID | None = None
    upsell_product_id: uuid.UUID | None = None
    includes_offers: list[uuid.UUID] | None = None
    deliverables: list[dict[str, Any]] | None = None
    specific_details: dict[str, Any] | None = None

    metadata_info: dict[str, Any] | None = None
    avatar_id: uuid.UUID | None = None

    onboarding_action: str | None = None
    onboarding_url: str | None = None
    calendar_type_id: str | None = None
    checkout_page_url: str | None = None
    vsl_link: str | None = None
