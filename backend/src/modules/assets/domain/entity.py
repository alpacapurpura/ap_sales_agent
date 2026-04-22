"""Domain entities for the assets module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.assets.domain.enums import (
    AssetPurpose,
    AssetScope,
    AssetStatus,
    AssetType,
    ExtractionStatus,
    StorageProvider,
)
from src.shared.domain.base_entity import BaseEntity


class Asset(BaseEntity):
    """Asset Domain Model."""

    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None  # Optional, legacy direct offer link

    type: str = AssetType.IMAGE.value
    filename: str
    mime_type: str | None = None

    storage_provider: str = StorageProvider.LOCAL.value
    storage_path: str | None = None  # Internal path
    public_url: str

    user_description: str | None = None

    # AI Metadata (image processing pipeline)
    ai_metadata: dict[str, Any] = Field(default_factory=dict)
    ai_description: str | None = None
    ai_colors: list[str] = Field(default_factory=list)

    status: str = AssetStatus.PROCESSING.value
    error_message: str | None = None

    # ── Lifecycle + intent ───────────────────────────────────────────────
    scope: str = AssetScope.EPHEMERAL.value
    purpose: str = AssetPurpose.CONTEXT_EXTRACT.value

    # ── Text extraction pipeline (document / audio transcript) ───────────
    extracted_text: str | None = None
    extracted_summary: str | None = None
    extracted_at: datetime | None = None
    extraction_status: str = ExtractionStatus.PENDING.value
    extraction_error: str | None = None

    # Retention — when NULL the asset lives indefinitely.
    expires_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetLink(BaseEntity):
    """Typed link between an asset and a domain entity."""

    id: UUID
    tenant_id: UUID
    asset_id: UUID
    entity_type: str
    entity_id: UUID
    role: str
    created_at: datetime | None = None
    deleted_at: datetime | None = None


# Alias for backward compatibility (Deprecated)
GalleryImage = Asset
