import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ShareableLink(Base):
    __tablename__ = "shareable_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    token = Column(String, unique=True, index=True, nullable=False)
    target_type = Column(String, nullable=False)  # "calendar", "payment", "file"
    params = Column(
        JSONB, default=dict
    )  # Context data (e.g. event_type_slug, offer_id)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    visit_count = Column(Integer, default=0)
    last_visited_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
