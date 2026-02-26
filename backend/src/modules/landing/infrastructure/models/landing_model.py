from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.infrastructure.db.base_model import Base

class LandingPageModel(Base):
    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True) # Optional link to Offer
    
    slug = Column(String, unique=True, nullable=False)
    config = Column(JSONB, default={}) # Stores LandingPageConfig
    
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # offer = relationship("ProductModel")
