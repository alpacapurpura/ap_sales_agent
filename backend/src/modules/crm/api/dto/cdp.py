from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: UUID
    tenant_id: str
    lifecycle_stage: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    total_sessions: int
    total_ltv: int
    properties: dict[str, Any]
    tags: list[str]
    computed_traits: dict[str, Any]

    class Config:
        from_attributes = True


class RFMResponse(BaseModel):
    recency: float
    frequency: float
    monetary: float


class EventCreate(BaseModel):
    profile_id: UUID | None = None
    event_type: str
    event_name: str | None = None
    channel: str | None = None
    session_id: str | None = None
    url: str | None = None
    properties: dict[str, Any] = {}


class EventResponse(BaseModel):
    id: UUID
    event_type: str
    occurred_at: datetime

    class Config:
        from_attributes = True
