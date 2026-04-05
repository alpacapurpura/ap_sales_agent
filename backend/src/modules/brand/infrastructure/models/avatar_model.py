import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AvatarModel(Base):
    __tablename__ = "avatars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Creator

    name = Column(String, nullable=False)
    scope = Column(String, default="GLOBAL")  # GLOBAL, OFFER, CAMPAIGN

    # Core Persona
    icp_description = Column(Text, nullable=True)
    anti_avatar = Column(Text, nullable=True)
    voice_tone_config = Column(JSONB, default=dict)

    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
