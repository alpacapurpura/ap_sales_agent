from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True) # For subdomain/lookup
    
    # Configuration for Prompts and Rules
    # e.g. { "company_name": "Visionarias", "currency": "USD" }
    config_json = Column(JSONB, default={}) 
    
    # AI Provider Configuration (Multitenant)
    openai_api_key = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    can_use_platform_keys = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    connections = relationship("ChannelConnection", back_populates="tenant", cascade="all, delete-orphan")
