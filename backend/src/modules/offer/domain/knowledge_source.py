"""Knowledge source domain entity.

Represents a PDF / video / URL fed to the Sales Agent RAG (Qdrant) for a
specific offer. Pure Pydantic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from src.shared.domain.base_entity import BaseEntity


class KnowledgeSource(BaseEntity):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    offer_id: UUID
    name: str
    type: KnowledgeSourceType
    status: KnowledgeSourceStatus = KnowledgeSourceStatus.QUEUED

    # Origin (one of url / file)
    source_url: str | None = None  # for URL-type sources
    file_url: str | None = None  # for uploaded files
    mime_type: str | None = None
    size_bytes: int | None = None

    # Indexing stats
    indexed_chunk_count: int = 0
    last_indexed_at: datetime | None = None
    qdrant_collection: str | None = None
    qdrant_point_ids: list[str] = Field(default_factory=list)

    # Content metadata (page_count, duration_seconds, transcript_lang, ...)
    metadata: dict[str, Any] = Field(default_factory=dict)

    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


__all__ = ["KnowledgeSource"]
