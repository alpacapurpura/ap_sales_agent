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
    title: str
    day_of_week: str
    time: str
    duration_minutes: int = 60


class ProductDetails(BaseEntity):
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

    @model_validator(mode="after")
    def validate_fulfillment_logic(self):
        if (
            self.format == DigitalFormat.PHYSICAL_ITEM
            and self.fulfillment_type != FulfillmentType.PHYSICAL_SHIPPING
        ):
            msg = "Format is PHYSICAL but fulfillment is set to Digital."
            raise ValueError(msg)
        return self


class ServiceDetails(BaseEntity):
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


class ProgramModule(BaseEntity):
    title: str
    description: str | None = None
    topics: list[str] = []


class ProgramDetails(BaseEntity):
    curriculum: list[ProgramModule] = []
    structure_type: ProgramStructure | None = None
    start_date: datetime | None = None
    registration_end_date: datetime | None = None
    end_date: datetime | None = None
    is_end_date_estimated: bool = False
    duration_weeks: int | None = None
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
    def validate_program_logic(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            msg = "End date cannot be before start date."
            raise ValueError(msg)
        return self


class SubscriptionDetails(BaseEntity):
    billing_cycle: BillingFrequency | None = None
    trial_period_days: int = 0
    tier_name: str | None = None
    platform_name: str | None = None
    cancellation_policy: str | None = None
    content_update_freq: str | None = None
    expert_guests: bool = False
    networking_events: bool = False


class EventDetails(BaseEntity):
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
    def validate_event_logistics(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            msg = "Event end_date must be after start_date."
            raise ValueError(msg)
        if self.location_type == EventLocationType.VIRTUAL and (
            self.venue_address or self.venue_name
        ):
            msg = "Virtual events should not have a physical venue address/name."
            raise ValueError(msg)
        return self
