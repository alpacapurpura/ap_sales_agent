"""SQLAlchemy model for launch_editions table."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LaunchEditionModel(Base):
    """SQLAlchemy model for launch edition table."""

    __tablename__ = "launch_editions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    edition_name = Column(String, nullable=False)
    edition_number = Column(Integer, nullable=False)

    # Nullable — placeholder editions have no date yet.
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    registration_start = Column(DateTime(timezone=True), nullable=True)
    registration_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")

    pricing_override = Column(JSONB, nullable=True)
    # Phase 4: temporal pricing ladder (replaces pricing_override on new
    # code paths). Populated via service serialization; migration 047
    # backfilled existing override rows into a single "regular" tier.
    pricing_tiers = Column(JSONB, nullable=True)
    capacity = Column(Integer, nullable=True)
    enrollment_count = Column(Integer, default=0)

    status = Column(String, default="draft")
    # 'private' | 'public'. Only PUBLIC editions are surfaced to the sales
    # agent and to public landing URLs.
    visibility = Column(String, nullable=False, default="private", server_default="private")

    location_override = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    # Provenance for clone-with-evolution (Phase 3). SET NULL on delete to
    # keep history even if the source is removed.
    cloned_from_edition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("launch_editions.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
