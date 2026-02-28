from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.shared.infrastructure.db.base_model import Base

class SensitiveData(Base):
    __tablename__ = "sensitive_data_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    source = Column(String, nullable=False) # "prompt", "response", "log"
    detected_pattern = Column(String, nullable=False) # "email", "credit_card", "ssn"
    
    original_text_hash = Column(String, nullable=True) # SHA256 of original (for audit without storing PII)
    redacted_text = Column(Text, nullable=True)
    
    action_taken = Column(String, default="REDACTED") # REDACTED, BLOCKED, FLAGGED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
