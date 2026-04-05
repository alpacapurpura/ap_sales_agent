from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict


class OfferGalleryImage(BaseModel):
    """
    Offer Gallery Image Domain Model.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    tenant_id: UUID4 | None = None
    offer_id: UUID4

    filename: str
    file_path: str
    public_url: str

    user_description: str | None = None
    ai_description: str | None = None
    ai_colors: list[str] = []

    status: str = "processing"
    error_message: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
