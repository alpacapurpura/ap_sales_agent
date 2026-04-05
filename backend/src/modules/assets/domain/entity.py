from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.assets.domain.enums import AssetStatus, AssetType, StorageProvider
from src.shared.domain.base_entity import BaseEntity


class Asset(BaseEntity):
    """
    Asset Domain Model.
    """

    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None  # Now Optional

    type: str = AssetType.IMAGE.value
    filename: str
    mime_type: str | None = None

    storage_provider: str = StorageProvider.LOCAL.value
    storage_path: str | None = None  # Internal path
    public_url: str

    user_description: str | None = None

    # AI Metadata
    ai_metadata: dict[str, Any] = Field(default_factory=dict)
    # Legacy fields mapping
    ai_description: str | None = None
    ai_colors: list[str] = Field(default_factory=list)

    status: str = AssetStatus.PROCESSING.value
    error_message: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


# Alias for backward compatibility (Deprecated)
GalleryImage = Asset
