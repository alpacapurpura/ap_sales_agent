"""Calendar DTOs."""

import datetime
from typing import Any

from pydantic import BaseModel


class CalendarStatusResponse(BaseModel):
    """Calendar Status Response DTO."""

    is_connected: bool
    email: str | None = None
    booking_link: str | None = None


class BookMeetingRequest(BaseModel):
    """Book Meeting Request DTO."""

    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: dict[str, Any]  # {id, name, email, dealContext...}


class AppointmentResponse(BaseModel):
    """Appointment Response DTO."""

    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    meet_link: str | None = None
    attendees: list[str] = []


class CreateBookingLinkRequest(BaseModel):
    """Create Booking Link Request DTO."""

    lead_id: str
    event_slug: str
    expiration_days: int = 7
