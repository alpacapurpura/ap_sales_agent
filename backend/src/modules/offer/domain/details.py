"""Details domain module."""

from __future__ import annotations

from datetime import datetime

from pydantic import HttpUrl, model_validator

from src.modules.offer.domain.enums import (
    AccommodationType,
    BillingFrequency,
    CommunityPlatform,
    DigitalFormat,
    EventLocationType,
    FulfillmentType,
    InteractionMode,
    LiveInteractionType,
    ProgramStructure,
    ServiceCategory,
    ServiceFrequency,
)
from src.shared.domain.base_entity import BaseEntity


class SessionDetails(BaseEntity):
    """Session Details."""

    title: str
    day_of_week: str
    time: str
    duration_minutes: int = 60


class ProductDetails(BaseEntity):
    """Product Details.

    Fase 02 · Block F adds:
      - digital: ``sample_preview_url`` (30-50% conversion uplift when shared)
      - physical: ``packaging_description`` (unboxing experience),
        ``return_policy_days`` (Latam consumer-law floor),
        ``shipping_carriers_accepted`` (carriers reales Latam, not UPS/FedEx),
        ``shipping_estimate_by_region`` (reduce '¿cuándo llega?' tickets 60%).
    """

    fulfillment_type: FulfillmentType | None = None
    access_url: HttpUrl | None = None
    access_instructions: str | None = None
    format: DigitalFormat | None = None
    is_downloadable: bool = True
    estimated_consumption_time_minutes: int | None = None
    requires_shipping: bool = False
    sku_inventory_code: str | None = None
    stock_quantity: int | None = None
    shipping_weight_grams: int | None = None
    # Fase 02 · Block F — digital preview + physical logistics ----------
    sample_preview_url: HttpUrl | None = None
    packaging_description: str | None = None
    return_policy_days: int | None = None
    shipping_carriers_accepted: str | None = None
    shipping_estimate_by_region: str | None = None

    @model_validator(mode="after")
    def validate_fulfillment_logic(self) -> ProductDetails:
        """Validate fulfillment logic."""
        if self.format == DigitalFormat.PHYSICAL_ITEM and self.fulfillment_type != FulfillmentType.PHYSICAL_SHIPPING:
            msg = "Format is PHYSICAL but fulfillment is set to Digital."
            raise ValueError(msg)
        return self


class ServiceDetails(BaseEntity):
    """Service for details operations.

    Fase 02 · Block E adds three scope/expectation fields:
    ``response_time_hours`` (agent-facing SLA), ``onboarding_flow`` (what
    the client receives in the first days), and ``scope_excluded`` (what
    is deliberately NOT included — 80% of Latam post-venta disputes trace
    back to undeclared scope-out).
    """

    category: ServiceCategory | None = None
    interaction_mode: InteractionMode | None = None
    frequency_type: ServiceFrequency | None = None
    deliverables_list: list[str] = []
    revision_rounds: int = 0
    booking_url: HttpUrl | None = None
    session_duration_minutes: int | None = None
    total_sessions_count: int | None = None
    turnaround_time_days: int | None = None
    onboarding_brief_url: HttpUrl | None = None
    min_contract_months: int | None = None
    audience_reach_metric: str | None = None
    technical_requirements: str | None = None
    usage_rights_description: str | None = None
    requires_contract_signature: bool = False
    # Fase 02 · Block E — scope + expectation fields ------------------
    response_time_hours: int | None = None
    onboarding_flow: str | None = None
    scope_excluded: str | None = None


class ProgramModule(BaseEntity):
    """Program Module."""

    title: str
    description: str | None = None
    topics: list[str] = []


class ProgramDetails(BaseEntity):
    """Program Details."""

    curriculum: list[ProgramModule] = []
    structure_type: ProgramStructure | None = None
    start_date: datetime | None = None
    registration_end_date: datetime | None = None
    end_date: datetime | None = None
    is_end_date_estimated: bool = False
    duration_weeks: int | None = None
    # Fase 02 · Block C — expected weekly commitment in hours. Lead #1
    # question before buying; sub-declaring causes churn at week 3.
    weekly_time_commitment_hours: int | None = None
    # Narrative prerequisites replacing the legacy categorical enum — Latam
    # programs frame prerequisites as free-text ("nivel intermedio de X",
    # "haber tomado módulo Y") rather than strict gates.
    prerequisites_text: str | None = None
    cohort_limit: int | None = None
    current_enrollment_count: int = 0
    is_application_required: bool = False
    interaction_type: LiveInteractionType | None = None
    live_schedule_description: str | None = None
    schedule: list[SessionDetails] = []
    lms_url: HttpUrl | None = None
    community_platform: CommunityPlatform = CommunityPlatform.NONE
    community_invite_link: HttpUrl | None = None
    has_certification: bool = False
    homework_submission_required: bool = False

    @model_validator(mode="after")
    def validate_program_logic(self) -> ProgramDetails:
        """Validate program logic."""
        if self.start_date and self.end_date and self.end_date < self.start_date:
            msg = "End date cannot be before start date."
            raise ValueError(msg)
        return self


class SubscriptionDetails(BaseEntity):
    """Subscription Details.

    Fase 02 · Block D renames (migration 065):
      - ``billing_cycle`` → ``billing_frequency``
      - ``content_update_freq`` → ``content_update_frequency``
    Nuevos campos: auto-renewal notice, cancellation anticipation,
    grace period on failed payment, member benefits narrative, primary
    communication channel. Todos Latam-compliance o Latam-retention
    críticos — ver ``subscription-details.schema.ts`` para razonamiento.
    """

    billing_frequency: BillingFrequency | None = None
    trial_period_days: int = 0
    tier_name: str | None = None
    platform_name: str | None = None
    cancellation_policy: str | None = None
    content_update_frequency: str | None = None
    expert_guests: bool = False
    networking_events: bool = False

    # Fase 02 · Block D — Latam legal / retention fields -------------
    # Most Latam consumer laws (AR, MX, PE, CO) require prior email/SMS
    # notice before auto-renewal debits. 3-7 days is the standard window.
    auto_renewal_with_notice_days: int | None = None
    # Days of anticipation a member must cancel to avoid the next cycle.
    # 0 = same-day cancellation. 7 is typical; >15 triggers friction.
    cancellation_anticipation_days: int | None = None
    # Grace window to retry failed payments before revoking access.
    # 3-7 days recovers 30-50% of involuntary churn in Latam (expired
    # cards, temp limits, international card blocks).
    grace_period_days_on_failed_payment: int | None = None
    # Narrative list of benefits per billing cycle. Text blob; the FE
    # renders one-per-line. Replaces the missing explicit deliverables
    # surface for memberships.
    member_benefits: str | None = None
    # Preferred ongoing communication channel for the member. Free-form
    # string keyed to the FE enum options (whatsapp_business, email,
    # slack_shared, telegram, platform_internal).
    primary_communication_channel: str | None = None


class PlatformFeature(BaseEntity):
    """Software feature surfaced on a platform/SaaS offer."""

    name: str
    description: str | None = None
    plans_available: str | None = None  # comma-separated plan names
    is_highlighted: bool = False


class PlatformIntegration(BaseEntity):
    """External-system integration surfaced on a platform/SaaS offer."""

    name: str
    category: str | None = None
    logo_url: HttpUrl | None = None
    setup_guide_url: HttpUrl | None = None


class PlatformDetails(BaseEntity):
    """SaaS / platform-flavored offer details (Fase 02 · Block G, ADR-010).

    Composable top-level field on :class:`Offer`. NOT part of the
    polymorphic ``specific_details`` union — any offer can opt-in
    regardless of archetype (SaaS memberships, SaaS services, etc.).
    See ``platform-details.schema.ts`` for Latam-specific rationale on
    each field.
    """

    platform_features: list[PlatformFeature] = []
    platform_integrations: list[PlatformIntegration] = []
    security_compliance: str | None = None
    data_residency: str | None = None
    uptime_guarantee: str | None = None
    status_page_url: HttpUrl | None = None
    support_channels: str | None = None
    api_available: bool | None = None
    api_docs_url: HttpUrl | None = None
    migration_tools: str | None = None
    public_roadmap_url: HttpUrl | None = None
    changelog_url: HttpUrl | None = None
    ai_features_disclosure: str | None = None
    data_export_capability: str | None = None


class EventDetails(BaseEntity):
    """Event Details."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    timezone: str = "UTC"
    location_type: EventLocationType | None = None
    virtual_meeting_url: HttpUrl | None = None
    is_recorded: bool = True
    venue_name: str | None = None
    venue_address: str | None = None
    map_link: HttpUrl | None = None
    accommodation_type: AccommodationType = AccommodationType.NOT_INCLUDED
    recommended_airport_code: str | None = None
    is_transfer_included: bool = False
    agenda_highlights: list[str] = []
    dress_code: str | None = None
    dietary_restrictions_form_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_event_logistics(self) -> EventDetails:
        """Validate event logistics."""
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            msg = "Event end_date must be after start_date."
            raise ValueError(msg)
        if self.location_type == EventLocationType.VIRTUAL and (self.venue_address or self.venue_name):
            msg = "Virtual events should not have a physical venue address/name."
            raise ValueError(msg)
        return self
