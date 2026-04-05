import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Customer Link
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("customer_profiles.id"), nullable=True
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

    # Deep Memory
    conversation_summary = Column(Text, nullable=True)
    key_objections_history = Column(JSONB, default=[])

    # Style / Persona Data
    style_profile = Column(JSONB, default={}, nullable=True)  # Output of Psychologist
    custom_system_instruction = Column(String, nullable=True)  # Output of Architect

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Tenant Link
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    tenant = relationship("TenantModel", back_populates="leads")

    # Relationships
    messages = relationship(
        "MessageModel", back_populates="lead", cascade="all, delete-orphan"
    )
    appointments = relationship(
        "AppointmentModel", back_populates="lead", cascade="all, delete-orphan"
    )
    # agent_traces = relationship("src.shared.infrastructure.models.agent_trace_model.AgentTrace", back_populates="lead", cascade="all, delete-orphan")
