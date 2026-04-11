"""SQLAlchemy model for offer_assets table.

Represents a flyer / video / carousel / document attached to an offer.
Sources: AI-generated (Puck-editable) or externally uploaded.

Uses SA 2.0 `mapped_column` + `Mapped[...]` typing. Postgres-specific types
(`JSONB`, `UUID`) are monkeypatched in the test conftest so SQLite still works.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class OfferAssetModel(Base):
    __tablename__ = "offer_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # AssetType enum value
    source: Mapped[str] = mapped_column(
        String, nullable=False
    )  # AssetSource enum value
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="draft", server_default="draft"
    )

    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Column is named "metadata" in the DB; Python attribute is `metadata_json`
    # because `metadata` clashes with SQLAlchemy's declarative base attribute.
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
    prompt_params: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    editable_in_puck: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_offer_assets_tenant_offer", "tenant_id", "offer_id"),
        Index("ix_offer_assets_deleted_at", "deleted_at"),
    )
