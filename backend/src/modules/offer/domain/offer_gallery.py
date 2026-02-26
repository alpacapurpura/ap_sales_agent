from typing import Optional, List
from pydantic import BaseModel, UUID4, ConfigDict
from datetime import datetime

class OfferGalleryImage(BaseModel):
    """
    Offer Gallery Image Domain Model.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    tenant_id: Optional[UUID4] = None
    offer_id: UUID4
    
    filename: str
    file_path: str
    public_url: str
    
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    ai_colors: List[str] = []
    
    status: str = "processing"
    error_message: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
