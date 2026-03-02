from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.assets.domain.enums import AssetType, AssetStatus

class AssetDto(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None # Optional now
    
    type: str
    filename: str
    mime_type: Optional[str] = None
    public_url: str
    
    user_description: Optional[str] = None
    ai_metadata: Dict[str, Any] = {}
    ai_description: Optional[str] = None
    ai_colors: List[str] = []
    
    status: str
    error_message: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Backward Compatibility
class GalleryImageDto(AssetDto):
    pass
