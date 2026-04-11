"""DTOs for ``GET /offers/{id}/counts`` — tab-bar badges."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OfferCountsResponse(BaseModel):
    """Counts surfaced on the header tab bar."""

    model_config = ConfigDict(from_attributes=True)

    assets: int
    campaigns: int
    knowledge: int


__all__ = ["OfferCountsResponse"]
