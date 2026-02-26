from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class OfferGalleryImageSchema(BaseModel):
    id: UUID
    offer_id: UUID
    public_url: str
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    ai_colors: List[str] = []
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
