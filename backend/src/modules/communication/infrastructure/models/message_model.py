from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from src.shared.infrastructure.db.base_model import Base

class MessageModel(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    sender_type = Column(String, nullable=False) # user / assistant / system
    content = Column(Text, nullable=False)
    channel = Column(String, nullable=True) # whatsapp / telegram
    external_id = Column(String, nullable=True) # Message ID from channel
    
    metadata_info = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    lead = relationship("src.modules.sales.infrastructure.models.lead_model.LeadModel", back_populates="messages")
