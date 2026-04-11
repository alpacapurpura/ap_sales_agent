"""SQLAlchemy model for offer_knowledge_sources table.

Represents a PDF / video / URL fed to the Sales Agent RAG (Qdrant) for a
specific offer. Uses SA 2.0 `mapped_column` + `Mapped[...]` typing.

Note: `qdrant_point_ids` is stored as JSONB (list of strings) rather than
`ARRAY(String)` so the same model works on SQLite tests (where ARRAY is
unsupported) and Postgres in production.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class KnowledgeSourceModel(Base):
    __tablename__ = "offer_knowledge_sources"

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
    type: Mapped[str] = mapped_column(String, nullable=False)  # KnowledgeSourceType
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="queued", server_default="queued"
    )

    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    indexed_chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    qdrant_collection: Mapped[str | None] = mapped_column(String, nullable=True)
    qdrant_point_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    # Column is named "metadata" in the DB; Python attribute is `metadata_json`
    # because `metadata` clashes with SQLAlchemy's declarative base attribute.
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
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
        Index(
            "ix_offer_knowledge_sources_tenant_offer",
            "tenant_id",
            "offer_id",
        ),
        Index("ix_offer_knowledge_sources_deleted_at", "deleted_at"),
    )
