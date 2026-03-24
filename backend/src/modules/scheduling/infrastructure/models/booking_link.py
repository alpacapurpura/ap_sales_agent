from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.shared.domain.base_entity import Base

class BookingLink(Base):
    __tablename__ = "booking_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String, unique=True, index=True, nullable=False)
    
    status = Column(String, default="ACTIVE") # ACTIVE, EXPIRED, USED
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    event_slug = Column(String, nullable=True)
    
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    lead = relationship("LeadModel")
