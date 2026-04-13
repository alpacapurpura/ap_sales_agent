"""Offer Gallery DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OfferGalleryImageSchema(BaseModel):
    """Offer Gallery Image Schema DTO."""

    id: UUID
    offer_id: UUID
    public_url: str
    user_description: str | None = None
    ai_description: str | None = None
    ai_colors: list[str] = []
    status: str
    error_message: str | None = None
    created_at: datetime

    class Config:
        """Model configuration."""

        from_attributes = True
