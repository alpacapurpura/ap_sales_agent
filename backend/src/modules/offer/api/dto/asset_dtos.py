"""DTOs for ``/offers/{id}/assets`` endpoints.

Mirrors ``OfferAsset`` domain entity; PII-free (no emails/addresses). The
``file_url``/``thumbnail_url`` fields are storage locations, not user PII.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.offer.domain.enums import (
    AssetSource,
    AssetStatus,
    AssetType,
)


class OfferAssetResponse(BaseModel):
    """Offer Asset Response DTO."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    # Edition scoping surfaced to the frontend so the UI can render the
    # right badge (edition chip, shared pin, or offer-level default).
    edition_id: UUID | None = None
    shared_across_editions: bool = False
    name: str
    type: AssetType
    source: AssetSource
    status: AssetStatus
    file_url: str | None = None
    thumbnail_url: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    editable_in_puck: bool = False
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetListResponse(BaseModel):
    """Asset List Response DTO."""

    items: list[OfferAssetResponse]
    total: int
    limit: int
    offset: int


class AssetGenerateRequest(BaseModel):
    """Asset Generate Request DTO."""

    type: AssetType
    name: str | None = None
    prompt_params: dict[str, Any] = Field(default_factory=dict)
    edition_id: UUID | None = None
    shared_across_editions: bool = False


class AssetUpdateRequest(BaseModel):
    """Asset Update Request DTO."""

    name: str | None = None
    metadata: dict[str, Any] | None = None
    thumbnail_url: str | None = None
    # Edition re-binding: move an asset between editions or promote to
    # shared. ``None`` means "leave as-is" — the service uses an
    # unset-aware dump so existing patch semantics are preserved.
    edition_id: UUID | None = None
    shared_across_editions: bool | None = None


class AssetDownloadUrlResponse(BaseModel):
    """Asset Download Url Response DTO."""

    url: str
    expires_at: datetime


__all__ = [
    "AssetDownloadUrlResponse",
    "AssetGenerateRequest",
    "AssetListResponse",
    "AssetUpdateRequest",
    "OfferAssetResponse",
]
