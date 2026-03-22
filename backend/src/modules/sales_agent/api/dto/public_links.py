from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime
from src.modules.scheduling.domain.event_type_schema import EventType

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
