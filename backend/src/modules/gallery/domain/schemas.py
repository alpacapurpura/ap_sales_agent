from typing import Optional, List
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity

class GalleryImageDto(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    offer_id: UUID
    
    filename: str
    public_url: str
    
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    ai_colors: List[str] = []
    
    status: str
    error_message: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
