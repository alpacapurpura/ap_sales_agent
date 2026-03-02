from pydantic import BaseModel
import datetime
from typing import List, Optional, Dict, Any

class CalendarStatusResponse(BaseModel):
    is_connected: bool
    email: Optional[str] = None
    booking_link: Optional[str] = None

class BookMeetingRequest(BaseModel):
    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: Dict[str, Any] # {id, name, email, dealContext...}

class AppointmentResponse(BaseModel):
    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    meet_link: Optional[str] = None
    attendees: List[str] = []

class CreateBookingLinkRequest(BaseModel):
    lead_id: str
    event_slug: str
    expiration_days: int = 7
