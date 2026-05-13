"""DTOs for ``POST /offers/{id}/status`` — lifecycle transitions."""

from __future__ import annotations

from uuid import UUID

from luana_core_offer_studio.domain.lifecycle import OfferLifecycleStatus
from pydantic import BaseModel, ConfigDict


class OfferStatusChangeRequest(BaseModel):
    """Body for the header status switcher."""

    new_status: OfferLifecycleStatus
    actor_user_id: UUID | None = None


class OfferStatusChangeResponse(BaseModel):
    """Minimal confirmation returned after a successful transition."""

    model_config = ConfigDict(from_attributes=True)

    offer_id: UUID
    status: OfferLifecycleStatus


__all__ = ["OfferStatusChangeRequest", "OfferStatusChangeResponse"]
