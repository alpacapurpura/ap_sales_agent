"""Public Links API endpoints."""

import datetime
from typing import Any

from pydantic import BaseModel, EmailStr

from src.modules.scheduling.domain.event_type_schema import EventType
from src.shared.links.schemas import (
    LinkResolveResponse as LinkResolveResponse,  # noqa: PLC0414 — re-export
)


class BookingRequest(BaseModel):
    """Schema for booking request."""

    slot_time: datetime.datetime
    duration_minutes: int = 30
    name: str
    email: EmailStr
    phone: str | None = None
    notes: str | None = None
    booking_token: str | None = None


class EventTypeResolveResponse(BaseModel):
    """Schema for event type resolve response."""

    event_type: EventType
    tenant_name: str
    tenant_avatar: str | None = None
    tenant_id: str


class BookingLinkResolveResponse(BaseModel):
    """Schema for booking link resolve response."""

    valid: bool
    event_slug: str
    lead_name: str | None = None
    lead_email: str | None = None
    lead_phone: str | None = None
    lead_id: str
    expires_at: datetime.datetime


class SlotsResponse(BaseModel):
    """Schema for slots response."""

    slots: list[datetime.datetime]


class BookingConfirmationResponse(BaseModel):
    """Schema for booking confirmation response."""

    status: str
    event: dict[str, Any]
