from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True) # Lead email (might be different from admin email)
    phone = Column(String, nullable=True)
    
    # Channel specific IDs
    telegram_id = Column(String, unique=True, nullable=True)
    whatsapp_id = Column(String, unique=True, nullable=True)
    instagram_id = Column(String, unique=True, nullable=True)
    tiktok_id = Column(String, unique=True, nullable=True)
    api_id = Column(String, unique=True, nullable=True) # Generic External ID
    
    # Profile Data (The "Valeria" Profile)
    # Stores the full UserProfile schema (psychographics + demographics + qualification)
    profile_data = Column(JSONB, default={}) 
    
    # Style / Persona Data
    style_profile = Column(JSONB, default={}, nullable=True) # Output of Psychologist
    custom_system_instruction = Column(String, nullable=True) # Output of Architect
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Tenant Link
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    tenant = relationship("Tenant", back_populates="leads")

    # Relationships
    enrollments = relationship("Enrollment", back_populates="lead", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="lead", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    agent_traces = relationship("AgentTrace", back_populates="lead", cascade="all, delete-orphan")
