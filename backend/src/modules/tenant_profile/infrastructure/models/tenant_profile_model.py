"""SQLAlchemy ORM model for the tenant_profiles table.

Table layout mirrors the schema declared in migration 052:

    CREATE TABLE IF NOT EXISTS tenant_profiles (
        tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
        business_types TEXT[] NOT NULL DEFAULT '{}',
        declared_at TIMESTAMPTZ,
        last_business_types_change_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

No ``id`` surrogate key — ``tenant_id`` IS the primary key (1:1 with tenant).
No ``deleted_at`` — the row is dropped only via FK CASCADE when the tenant is
deleted, which is the correct lifecycle for this aggregate.

Implementation note:
  In production (PostgreSQL) the column is ``TEXT[]`` — native array with GIN
  index for containment lookups. In tests (SQLite) the dialect has no array
  type, so we fall back to ``JSON`` via ``with_variant``. At the Python level
  the value is always a ``list[str]`` regardless of dialect.
"""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TenantProfileModel(Base):
    """ORM model for ``tenant_profiles``."""

    __tablename__ = "tenant_profiles"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    # PostgreSQL: native TEXT[] (matches migration 052, GIN-indexed).
    # SQLite (tests): falls back to JSON for dialect compatibility.
    business_types = Column(
        ARRAY(String).with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    )
    declared_at = Column(DateTime(timezone=True), nullable=True)
    last_business_types_change_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
