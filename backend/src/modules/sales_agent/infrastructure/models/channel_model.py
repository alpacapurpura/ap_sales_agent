from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base

class ChannelConnectionModel(Base):
    __tablename__ = "channel_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    channel_type = Column(String, nullable=False) # stored as string to allow flexibility, validated by enum in logic
    
    # Credentials (e.g., {"bot_token": "..."})
    credentials = Column(JSONB, default={})
    
    # Configuration (e.g., {"welcome_message": "...", "bot_name": "..."})
    config = Column(JSONB, default={})
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # tenant = relationship("src.modules.iam.infrastructure.models.tenant_model.TenantModel", back_populates="connections")
