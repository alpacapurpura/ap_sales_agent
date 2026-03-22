from typing import Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import Field
from src.shared.domain.base_entity import BaseEntity

class ExtractRequest(BaseEntity):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field("brand_identity", description="Type of extraction to perform")

class Avatar(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    name: str
    scope: str = "GLOBAL"
    icp_description: Optional[str] = None
    anti_avatar: Optional[str] = None
    voice_tone_config: Dict[str, Any] = {}
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
