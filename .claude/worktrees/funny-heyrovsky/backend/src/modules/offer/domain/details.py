from pydantic import model_validator, HttpUrl
from typing import Optional, List
from src.shared.domain.base_entity import BaseEntity
from src.modules.offer.domain.enums import (
    FulfillmentType, DigitalFormat, ServiceCategory, InteractionMode, ServiceFrequency,
    ProgramStructure, LiveInteractionType, CommunityPlatform, EventLocationType, AccommodationType,
    BillingFrequency
)
from datetime import datetime

class SessionDetails(BaseEntity):
    title: str
    day_of_week: str
    time: str
    duration_minutes: int = 60

class ProductDetails(BaseEntity):
    fulfillment_type: Optional[FulfillmentType] = None
    access_url: Optional[HttpUrl] = None
    access_instructions: Optional[str] = None
    format: Optional[DigitalFormat] = None
    is_downloadable: bool = True
    estimated_consumption_time_minutes: Optional[int] = None
    requires_shipping: bool = False
    sku_inventory_code: Optional[str] = None
    stock_quantity: Optional[int] = None
    shipping_weight_grams: Optional[int] = None

    @model_validator(mode='after')
    def validate_fulfillment_logic(self):
        if self.format == DigitalFormat.PHYSICAL_ITEM and self.fulfillment_type != FulfillmentType.PHYSICAL_SHIPPING:
            raise ValueError("Format is PHYSICAL but fulfillment is set to Digital.")
        return self

class ServiceDetails(BaseEntity):
    category: Optional[ServiceCategory] = None
    interaction_mode: Optional[InteractionMode] = None
    frequency_type: Optional[ServiceFrequency] = None
    deliverables_list: List[str] = []
    revision_rounds: int = 0
    booking_url: Optional[HttpUrl] = None
    session_duration_minutes: Optional[int] = None
    total_sessions_count: Optional[int] = None
    turnaround_time_days: Optional[int] = None
    onboarding_brief_url: Optional[HttpUrl] = None
    min_contract_months: Optional[int] = None
    audience_reach_metric: Optional[str] = None
    technical_requirements: Optional[str] = None
    usage_rights_description: Optional[str] = None
    requires_contract_signature: bool = False

class ProgramModule(BaseEntity):
    title: str
    description: Optional[str] = None
    topics: List[str] = []

class ProgramDetails(BaseEntity):
    curriculum: List[ProgramModule] = []
    structure_type: Optional[ProgramStructure] = None
    start_date: Optional[datetime] = None
    registration_end_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_end_date_estimated: bool = False
    duration_weeks: Optional[int] = None
    cohort_limit: Optional[int] = None
    current_enrollment_count: int = 0
    is_application_required: bool = False
    interaction_type: Optional[LiveInteractionType] = None
    live_schedule_description: Optional[str] = None
    schedule: List[SessionDetails] = []
    lms_url: Optional[HttpUrl] = None
    community_platform: CommunityPlatform = CommunityPlatform.NONE
    community_invite_link: Optional[HttpUrl] = None
    has_certification: bool = False
    homework_submission_required: bool = False

    @model_validator(mode='after')
    def validate_program_logic(self):
        if self.start_date and self.end_date:
             if self.end_date < self.start_date:
                raise ValueError("End date cannot be before start date.")
        return self

class SubscriptionDetails(BaseEntity):
    billing_cycle: BillingFrequency
    trial_period_days: int = 0
    tier_name: str
    platform_name: str
    cancellation_policy: str
    content_update_freq: str
    expert_guests: bool = False
    networking_events: bool = False

class EventDetails(BaseEntity):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: str = "UTC"
    location_type: Optional[EventLocationType] = None
    virtual_meeting_url: Optional[HttpUrl] = None
    is_recorded: bool = True
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    map_link: Optional[HttpUrl] = None
    accommodation_type: AccommodationType = AccommodationType.NOT_INCLUDED
    recommended_airport_code: Optional[str] = None
    is_transfer_included: bool = False
    agenda_highlights: List[str] = []
    dress_code: Optional[str] = None
    dietary_restrictions_form_url: Optional[HttpUrl] = None

    @model_validator(mode='after')
    def validate_event_logistics(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValueError("Event end_date must be after start_date.")
        if self.location_type == EventLocationType.VIRTUAL:
            if self.venue_address or self.venue_name:
                raise ValueError("Virtual events should not have a physical venue address/name.")
        return self
