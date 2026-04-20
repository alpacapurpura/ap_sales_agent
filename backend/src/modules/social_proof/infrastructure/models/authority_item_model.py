"""SQLAlchemy model for the ``authority_items`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AuthorityItemModel(Base):
    """SQLAlchemy model mapping to the ``authority_items`` table."""

    __tablename__ = "authority_items"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)

    entity_name = Column(String(255), nullable=False)
    authority_type = Column(String(40), nullable=False)
    context = Column(Text, nullable=True)
    proof_url = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    obtained_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
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
            "ix_authority_items_tenant_active",
            "tenant_id",
            "is_active",
            "deleted_at",
        ),
        Index(
            "ix_authority_items_tenant_type",
            "tenant_id",
            "authority_type",
        ),
    )
