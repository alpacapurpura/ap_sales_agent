from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class ShareableLink(Base):
    __tablename__ = "shareable_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Secure Token (Public ID)
    token = Column(String, unique=True, nullable=False, index=True)
    
    # Configuration
    target_type = Column(String, nullable=False) # e.g., 'booking', 'offer', 'payment'
    params = Column(JSONB, default={}) # Stores encoded params, source, campaign_id, etc.
    
    # Security & Lifecycle
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Audit
    visit_count = Column(Integer, default=0)
    last_visited_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    creator = relationship("User")
