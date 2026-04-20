"""SQLAlchemy model for the ``social_proof_placements`` link table."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PlacementModel(Base):
    """Mapping of a social-proof source row to a surface (brand, offer, …)."""

    __tablename__ = "social_proof_placements"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    source_table = Column(String(30), nullable=False)
    source_id = Column(PG_UUID(as_uuid=True), nullable=False)

    surface_type = Column(String(30), nullable=False)
    surface_ref_id = Column(PG_UUID(as_uuid=True), nullable=True)

    sort_order = Column(Integer, nullable=False, default=0)
    is_visible = Column(Boolean, nullable=False, default=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_placements_for_surface",
            "tenant_id",
            "surface_type",
            "surface_ref_id",
            "is_visible",
            "deleted_at",
        ),
        Index(
            "ix_placements_by_source",
            "source_table",
            "source_id",
            "deleted_at",
        ),
    )
