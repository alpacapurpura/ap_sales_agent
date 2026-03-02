from typing import Dict, Any, Optional
from pydantic import Field, ConfigDict
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity

class JourneyEvent(BaseEntity):
    id: UUID
    profile_id: UUID
    tenant_id: Optional[UUID] = None
    
    event_name: str # "page_view", "email_opened", "checkout_completed"
    event_type: str # "track", "page", "screen"
    
    properties: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    occurred_at: Optional[datetime] = None
