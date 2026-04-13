import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.shared.domain.base_entity import Base


class CustomerProfileModel(Base):
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
