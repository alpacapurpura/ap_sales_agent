import datetime
from typing import Any

from pydantic import BaseModel


class CalendarStatusResponse(BaseModel):
    is_connected: bool
    email: str | None = None
    booking_link: str | None = None


class BookMeetingRequest(BaseModel):
    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: dict[str, Any]  # {id, name, email, dealContext...}


class AppointmentResponse(BaseModel):
    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    meet_link: str | None = None
    attendees: list[str] = []


class CreateBookingLinkRequest(BaseModel):
    lead_id: str
    event_slug: str
    expiration_days: int = 7
