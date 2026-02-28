from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import datetime
from src.modules.communication.domain.event_type_schema import EventType

class LinkResolveResponse(BaseModel):
    valid: bool
    type: str
    tenant_name: str
    tenant_avatar: Optional[str] = None
    params: Dict[str, Any] = {}

class BookingRequest(BaseModel):
    slot_time: datetime.datetime
    duration_minutes: int = 30
    name: str
    email: EmailStr
    phone: Optional[str] = None
    notes: Optional[str] = None
    booking_token: Optional[str] = None

class EventTypeResolveResponse(BaseModel):
    event_type: EventType
    tenant_name: str
    tenant_avatar: Optional[str] = None
    tenant_id: str

class BookingLinkResolveResponse(BaseModel):
    valid: bool
    event_slug: str
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_id: str
    expires_at: datetime.datetime
