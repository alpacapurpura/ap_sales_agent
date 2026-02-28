from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class ProfileResponse(BaseModel):
    id: UUID
    tenant_id: str
    lifecycle_stage: Optional[str]
    first_seen_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    total_sessions: int
    total_ltv: int
    properties: Dict[str, Any]
    tags: List[str]
    computed_traits: Dict[str, Any]
    
    class Config:
        from_attributes = True

class RFMResponse(BaseModel):
    recency: float
    frequency: float
    monetary: float

class EventCreate(BaseModel):
    profile_id: Optional[UUID] = None
    event_type: str
    event_name: Optional[str] = None
    channel: Optional[str] = None
    session_id: Optional[str] = None
    url: Optional[str] = None
    properties: Dict[str, Any] = {}

class EventResponse(BaseModel):
    id: UUID
    event_type: str
    occurred_at: datetime
    
    class Config:
        from_attributes = True
