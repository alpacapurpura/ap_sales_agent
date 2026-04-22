"""Pydantic schemas for the assets module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from src.modules.assets.domain.enums import AssetPurpose, AssetScope
from src.shared.domain.base_entity import BaseEntity

# Purposes whose ``scope`` is ``deliverable`` — they *must* carry an entity
# link when promoted, otherwise the asset has no consumer and the
# promotion is meaningless.
_DELIVERABLE_PURPOSES: frozenset[str] = frozenset(
    {
        AssetPurpose.OFFER_COLLATERAL.value,
        AssetPurpose.LEGAL_DOC.value,
    },
)


class AssetDto(BaseEntity):
    """Represent asset dto."""

    id: UUID
    tenant_id: UUID | None = None
    offer_id: UUID | None = None

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

    # Lifecycle + extraction (migration 057)
    scope: str = AssetScope.EPHEMERAL.value
    purpose: str = AssetPurpose.CONTEXT_EXTRACT.value
    extracted_summary: str | None = None
    extraction_status: str | None = None
    expires_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class PromoteAssetRequest(BaseEntity):
    """Body for POST /assets/{id}/promote.

    Deliverable purposes (``offer_collateral``, ``legal_doc``) require
    ``entity_type`` + ``entity_id`` + ``role``. Library purposes ignore
    those fields.
    """

    purpose: AssetPurpose
    entity_type: str | None = Field(default=None, max_length=40)
    entity_id: UUID | None = None
    role: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _require_link_for_deliverable(self) -> "PromoteAssetRequest":
        if self.purpose.value in _DELIVERABLE_PURPOSES:
            missing = [
                name
                for name, val in (
                    ("entity_type", self.entity_type),
                    ("entity_id", self.entity_id),
                    ("role", self.role),
                )
                if not val
            ]
            if missing:
                msg = f"purpose '{self.purpose.value}' requiere: {', '.join(missing)}"
                raise ValueError(msg)
        return self


# Backward Compatibility
class GalleryImageDto(AssetDto):
    """Represent gallery image dto."""
