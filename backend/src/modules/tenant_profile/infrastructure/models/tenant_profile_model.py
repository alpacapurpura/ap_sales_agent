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
  ``business_types`` is declared as ``JSONB`` in the ORM model (not ``ARRAY``)
  for SQLite-in-memory test compatibility. The production migration creates the
  column as ``TEXT[]`` (native array) which PostgreSQL JSONB operators can query
  equivalently. At the ORM level the value is always a Python ``list[str]``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    # Stored as JSONB for cross-dialect test compatibility (SQLite mock via conftest).
    # In PostgreSQL the column type is TEXT[] (see migration 052); JSONB list maps
    # transparently for both read and write operations.
    business_types = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="'[]'",
    )
    declared_at = Column(DateTime(timezone=True), nullable=True)
    last_business_types_change_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
