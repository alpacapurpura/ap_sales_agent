from typing import Optional
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.landing.domain.content import LandingPageConfig

class LandingPage(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None
    
    slug: str
    config: LandingPageConfig
    
    is_published: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
