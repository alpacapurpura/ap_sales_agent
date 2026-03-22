from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base
from src.shared.infrastructure.database.types import EncryptedJSON


class ChannelConnectionModel(Base):
    __tablename__ = "channel_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    channel_type = Column(String, nullable=False)

    # Encrypted at rest via EncryptedJSON (Fernet symmetric encryption)
    credentials = Column(EncryptedJSON, default={})

    # Non-sensitive configuration (welcome messages, metadata, etc.)
    config = Column(JSONB, default={})

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
