from typing import Dict, Any, Optional, List
from pydantic import Field, ConfigDict
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.crm.domain.enums import IdentityType, LifecycleStage

class CustomerIdentity(BaseEntity):
    id: UUID
    profile_id: UUID
    tenant_id: Optional[UUID] = None
    
    type: IdentityType
    value: str
    
    is_primary: bool = False
    verification_status: str = "unverified"
    
    last_seen_at: Optional[datetime] = None

class CustomerProfile(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    
    # Unified Identity
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    full_name: Optional[str] = None
    
    # Scoring & Segmentation
    lifecycle_stage: Optional[LifecycleStage] = LifecycleStage.SUBSCRIBER
    lead_score: float = 0.0
    rfm_segment: Optional[str] = None # e.g. "Champions", "At Risk"
    
    # Metadata
    traits: Dict[str, Any] = Field(default_factory=dict) # Demographics, etc.
    computed_traits: Dict[str, Any] = Field(default_factory=dict) # LTV, Last Seen, etc.
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    identities: List[CustomerIdentity] = []
