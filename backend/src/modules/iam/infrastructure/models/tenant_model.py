from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.infrastructure.db.base_model import Base

class TenantModel(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False) # For subdomain/lookup
    clerk_org_id = Column(String, nullable=True, index=True)
    
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
    users = relationship("UserModel", secondary="user_tenants", back_populates="tenants")
    leads = relationship("src.modules.sales.infrastructure.models.lead_model.LeadModel", back_populates="tenant")
    connections = relationship("src.modules.communication.infrastructure.models.channel_model.ChannelConnectionModel", back_populates="tenant")
    
    # Loosely coupled relationships (Strings to avoid import cycles)
    # These will need to be resolved at runtime or by importing the models where needed in application layer
