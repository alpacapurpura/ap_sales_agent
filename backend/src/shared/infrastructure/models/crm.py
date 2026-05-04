"""CRM SQLAlchemy ORM models — shared across bounded contexts.

These models live here so that analytics, sales_agent, and other modules
can JOIN against CRM tables without importing from src.modules.crm.*,
which would violate DDD boundaries.

The src.modules.crm.infrastructure.models.* files re-export from here
for backward compatibility within the CRM module itself.
"""

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base
from src.shared.domain.enums import IdentityType, LifecycleStage, SaleStage, SaleStatus


class PaymentMethod(StrEnum):
    """Payment method options for sale records."""

    CREDIT_CARD = "CREDIT_CARD"
    WIRE = "WIRE"
    CASH = "CASH"
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    MANUAL = "MANUAL"


# ── customer_model.py ────────────────────────────────────────────────────────


class CustomerProfileModel(Base):
    """SQLAlchemy model for customer profile."""

    __tablename__ = "customer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Unified Identity
    primary_email = Column(String, nullable=True, index=True)
    primary_phone = Column(String, nullable=True)
    full_name = Column(String, nullable=True)

    # Scoring & Segmentation
    lifecycle_stage = Column(
        Enum(LifecycleStage, values_callable=lambda enum: [e.value for e in enum]),
        default=LifecycleStage.SUBSCRIBER,
    )
    lead_score = Column(Float, default=0.0)
    rfm_segment = Column(String, nullable=True)  # e.g. "Champions", "At Risk"

    # Lifecycle & Activity
    lifetime_value = Column(Float, default=0.0, server_default="0")
    last_activity_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_inactive = Column(Boolean, default=False, server_default="false")
    first_conversion_at = Column(DateTime(timezone=True), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), nullable=True)
    lead_source = Column(String, nullable=True, index=True)
    lead_source_detail = Column(String, nullable=True)

    # Metadata
    traits = Column(JSONB, default=dict)  # Demographics, etc.
    computed_traits = Column(JSONB, default=dict)  # LTV, Last Seen, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    identities = relationship(
        "CustomerIdentityModel",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    journey_events = relationship(
        "JourneyEventModel",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class CustomerIdentityModel(Base):
    """SQLAlchemy model for customer identity."""

    __tablename__ = "customer_identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    type = Column(
        Enum(IdentityType, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    value = Column(String, nullable=False, index=True)  # The actual email, phone, or ID

    is_primary = Column(Boolean, default=False)
    verification_status = Column(String, default="unverified")

    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("CustomerProfileModel", back_populates="identities")


class JourneyEventModel(Base):
    """SQLAlchemy model for journey event."""

    __tablename__ = "journey_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_name = Column(
        String,
        nullable=False,
    )  # "page_view", "email_opened", "checkout_completed"
    event_type = Column(String, nullable=False)  # "track", "page", "screen"

    properties = Column(JSONB, default=dict)
    context = Column(JSONB, default=dict)

    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("CustomerProfileModel", back_populates="journey_events")


# ── lead_model.py ────────────────────────────────────────────────────────────


class LeadModel(Base):
    """SQLAlchemy model for lead."""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Customer Link
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=True,
    )
    customer = relationship("CustomerProfileModel", foreign_keys=[customer_id])

    # Channel specific IDs
    telegram_id = Column(String, unique=True, nullable=True)
    whatsapp_id = Column(String, unique=True, nullable=True)
    instagram_id = Column(String, unique=True, nullable=True)
    tiktok_id = Column(String, unique=True, nullable=True)
    api_id = Column(String, unique=True, nullable=True)  # Generic External ID

    # Profile Data (The "Valeria" Profile)
    # Stores the full UserProfile schema (psychographics + demographics + qualification)
    profile_data = Column(JSONB, default={})

    # Dynamic Scoring & System Flags
    fit_score = Column(Integer, default=0)
    intent_score = Column(Integer, default=0)
    temperature = Column(String, default="COLD")  # Enum: LeadTemperature
    is_blacklisted = Column(Boolean, default=False)

    last_interaction_date = Column(DateTime(timezone=True), nullable=True)
    next_scheduled_action = Column(DateTime(timezone=True), nullable=True)

    # Geographic segmentation (ISO 3166-1 alpha-2 lowercase, e.g. "pe", "mx").
    # Column added via migration 110 ALTER TABLE leads ADD COLUMN country VARCHAR(2).
    # Mapping added here in PR-4 S1 (closes PR-2 deuda — column existed in migration only).
    country = Column(String(2), nullable=True, index=True)

    # Deep Memory
    conversation_summary = Column(Text, nullable=True)
    key_objections_history = Column(JSONB, default=[])

    # Style / Persona Data
    style_profile = Column(JSONB, default={}, nullable=True)  # Output of Psychologist
    custom_system_instruction = Column(String, nullable=True)  # Output of Architect

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Tenant Link
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    tenant = relationship("TenantModel", back_populates="leads")

    # Relationships
    messages = relationship(
        "MessageModel",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    appointments = relationship(
        "AppointmentModel",
        back_populates="lead",
        cascade="all, delete-orphan",
    )


# ── sale_model.py ────────────────────────────────────────────────────────────


class SaleModel(Base):
    """SQLAlchemy model for sale."""

    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    transaction_id = Column(String, nullable=True, index=True)

    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True)

    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING)
    stage = Column(Enum(SaleStage), nullable=False)

    source = Column(String, default="MANUAL")
    payment_method = Column(Enum(PaymentMethod), nullable=True)

    metadata_info = Column(JSONB, default=dict)
    occurred_at = Column(DateTime(timezone=True), default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("CustomerProfileModel", backref="sales")
    offer = relationship("ProductModel")


# ── lifecycle_transition_model.py ────────────────────────────────────────────


class LifecycleTransitionModel(Base):
    """SQLAlchemy model for lifecycle transition."""

    __tablename__ = "lifecycle_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    from_stage = Column(
        Enum(LifecycleStage, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
    )  # null for initial assignment
    to_stage = Column(
        Enum(LifecycleStage, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )

    reason = Column(
        String,
        nullable=False,
    )  # Human-readable: "Score crossed MQL threshold (42.5 >= 40)"
    triggered_by = Column(
        String,
        nullable=False,
    )  # Values: scoring_rule, sale_event, churn_event, manual, decay, reactivation

    score_at_transition = Column(Float, nullable=True)

    transition_metadata = Column(
        "metadata",
        JSONB,
        default=dict,
    )  # Flexible context per trigger type
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())


# ── nps_models.py ────────────────────────────────────────────────────────────


class NpsSurveyModel(Base):
    """SQLAlchemy model for nps survey."""

    __tablename__ = "nps_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    offer_id = Column(UUID(as_uuid=True), nullable=True)  # null = individual survey
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=True,
    )
    delivery_channel = Column(
        String,
        default="universal_link",
    )  # "universal_link" | "whatsapp"
    status = Column(
        String,
        default="pending",
    )  # "pending" | "sent" | "responded" | "expired"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_nps_surveys_tenant_customer", "tenant_id", "customer_id"),)


class NpsResponseModel(Base):
    """SQLAlchemy model for nps response."""

    __tablename__ = "nps_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    survey_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nps_surveys.id"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    score = Column(Integer, nullable=False)  # 0-10
    feedback_text = Column(String, nullable=True)
    testimonial_text = Column(String, nullable=True)
    testimonial_audio_url = Column(String, nullable=True)
    consent_public_use = Column(Boolean, default=False)
    responded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_nps_responses_tenant_survey", "tenant_id", "survey_id"),)


# ── referral_code_model.py ───────────────────────────────────────────────────


class ReferralCodeModel(Base):
    """SQLAlchemy model for referral code."""

    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    code = Column(String, nullable=False, unique=True, index=True)
    source = Column(String, default="internal")  # "internal" | "shopify" | "external"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (Index("ix_referral_codes_tenant_customer", "tenant_id", "customer_id"),)
