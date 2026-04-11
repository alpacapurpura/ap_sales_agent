"""DTOs for landing generation endpoints on the offer header."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LandingStatusResponse(BaseModel):
    """Read model for ``GET /landing/status``.

    ``is_outdated`` is computed at read time as
    ``landing.generated_at < offer.updated_at`` — never stored.
    """

    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime | None = None
    is_published: bool = False
    offer_snapshot_version: str | None = None
    is_outdated: bool = False
    job_id: UUID | None = None
    job_status: str = "idle"


class LandingGenerateResponse(BaseModel):
    """Response for ``POST /landing/generate`` and ``/landing/regenerate``."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    job_status: str
    snapshot_version: str


class LandingPublishResponse(BaseModel):
    """Response for ``POST /landing/publish``."""

    model_config = ConfigDict(from_attributes=True)

    is_published: bool = True


class LandingUnpublishResponse(BaseModel):
    """Response for ``POST /landing/unpublish``."""

    model_config = ConfigDict(from_attributes=True)

    is_published: bool = False


__all__ = [
    "LandingGenerateResponse",
    "LandingPublishResponse",
    "LandingStatusResponse",
    "LandingUnpublishResponse",
]
