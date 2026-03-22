from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base

class TenantModel(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False) # For subdomain/lookup
    # Configuration for Prompts and Rules
    # Configuration for Prompts and Rules
    # e.g. { "company_name": "Visionarias" }
    config_json = Column(JSONB, default={}) 
    default_currency = Column(String, server_default="USD")
    timezone = Column(String, server_default="UTC")

    # ETL extraction priority: higher value = extracted first (premium tenants)
    extraction_priority = Column(Integer, server_default="0", nullable=False)

    # AI Provider Configuration (Multitenant)
    openai_api_key = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    can_use_platform_keys = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("UserModel", secondary="user_tenants", back_populates="tenants")
    leads = relationship("LeadModel", back_populates="tenant")
    # connections = relationship("src.modules.sales_agent.infrastructure.models.channel_model.ChannelConnectionModel", back_populates="tenant")
    
    # Loosely coupled relationships (Strings to avoid import cycles)
    # These will need to be resolved at runtime or by importing the models where needed in application layer
