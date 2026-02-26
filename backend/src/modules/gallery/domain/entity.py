from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity

class GalleryImage(BaseEntity):
    """
    Gallery Image Domain Model.
    """
    id: UUID
    tenant_id: Optional[UUID] = None
    offer_id: UUID
    
    filename: str
    file_path: str
    public_url: str
    
    user_description: Optional[str] = None
    ai_description: Optional[str] = None
    ai_colors: List[str] = Field(default_factory=list)
    
    status: str = "processing"
    error_message: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
