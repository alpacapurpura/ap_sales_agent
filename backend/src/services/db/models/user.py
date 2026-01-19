from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    
    # Channel specific IDs
    telegram_id = Column(String, unique=True, nullable=True)
    whatsapp_id = Column(String, unique=True, nullable=True)
    instagram_id = Column(String, unique=True, nullable=True)
    tiktok_id = Column(String, unique=True, nullable=True)
    
    # Profile Data (The "Valeria" Profile)
    # Stores the full UserProfile schema (psychographics + demographics + qualification)
    profile_data = Column(JSONB, default={}) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    messages = relationship("Message", back_populates="user")
