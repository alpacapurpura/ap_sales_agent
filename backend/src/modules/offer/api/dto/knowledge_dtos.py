"""DTOs for ``/offers/{id}/knowledge`` endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)


class KnowledgeSourceResponse(BaseModel):
    """Knowledge Source Response DTO."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    name: str
    type: KnowledgeSourceType
    status: KnowledgeSourceStatus
    source_url: str | None = None
    file_url: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    indexed_chunk_count: int = 0
    last_indexed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeListResponse(BaseModel):
    """Knowledge List Response DTO."""

    items: list[KnowledgeSourceResponse]
    total: int


class KnowledgeUrlRequest(BaseModel):
    """Knowledge Url Request DTO."""

    url: HttpUrl
    type: KnowledgeSourceType = KnowledgeSourceType.URL_ARTICLE
    name: str | None = None


__all__ = [
    "KnowledgeListResponse",
    "KnowledgeSourceResponse",
    "KnowledgeUrlRequest",
]
