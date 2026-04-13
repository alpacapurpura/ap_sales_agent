"""Pydantic schemas for the assets module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from src.shared.domain.base_entity import BaseEntity


class AssetDto(BaseEntity):
    """Represent asset dto."""

    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None  # Optional now

    type: str
    filename: str
    mime_type: str | None = None
    public_url: str

    user_description: str | None = None
    ai_metadata: dict[str, Any] = {}
    ai_description: str | None = None
    ai_colors: list[str] = []

    status: str
    error_message: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


# Backward Compatibility
class GalleryImageDto(AssetDto):
    """Represent gallery image dto."""
