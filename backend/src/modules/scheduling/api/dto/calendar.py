"""Calendar API endpoints."""

import datetime
from typing import Any

from pydantic import BaseModel


class CalendarStatusResponse(BaseModel):
    """Schema for calendar status response."""

    is_connected: bool
    email: str | None = None
    booking_link: str | None = None


class BookMeetingRequest(BaseModel):
    """Schema for book meeting request."""

    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: dict[str, Any]  # {id, name, email, dealContext...}


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""

    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    meet_link: str | None = None
    attendees: list[str] = []


class CreateBookingLinkRequest(BaseModel):
    """Schema for create booking link request."""

    lead_id: str
    event_slug: str
    expiration_days: int = 7
