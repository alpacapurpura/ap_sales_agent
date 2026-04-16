"""Calendar DTOs for the connections module.

Defined locally to avoid cross-module imports from scheduling.
"""

import datetime
from typing import Any

from pydantic import BaseModel


class CalendarStatusResponse(BaseModel):
    """Calendar status response."""

    is_connected: bool
    email: str | None = None
    booking_link: str | None = None


class BookMeetingRequest(BaseModel):
    """Book meeting request."""

    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: dict[str, Any]


class CreateBookingLinkRequest(BaseModel):
    """Create personalized booking link request."""

    lead_id: str
    event_slug: str
    expiration_days: int = 7
