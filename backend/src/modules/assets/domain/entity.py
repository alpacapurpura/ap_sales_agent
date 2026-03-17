from typing import Optional, List, Dict, Any
from pydantic import Field
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.assets.domain.enums import AssetType, StorageProvider, AssetStatus

class Asset(BaseEntity):
    """
    Asset Domain Model.
    """
    id: UUID
    tenant_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None # Now Optional
    
    type: str = AssetType.IMAGE.value
    filename: str
    mime_type: Optional[str] = None
    
    storage_provider: str = StorageProvider.LOCAL.value
    storage_path: Optional[str] = None # Internal path
    public_url: str
    
    user_description: Optional[str] = None
    
    # AI Metadata
    ai_metadata: Dict[str, Any] = Field(default_factory=dict)
    # Legacy fields mapping
    ai_description: Optional[str] = None
    ai_colors: List[str] = Field(default_factory=list)
    
    status: str = AssetStatus.PROCESSING.value
    error_message: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Alias for backward compatibility (Deprecated)
GalleryImage = Asset
