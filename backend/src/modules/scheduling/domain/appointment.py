"""Appointment domain definitions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.scheduling.domain.enums import AppointmentStatus
from src.shared.domain.base_entity import BaseEntity


class Appointment(BaseEntity):
    """Represent appointment."""

    id: UUID
    tenant_id: UUID | None = None
    lead_id: UUID | None = None

    summary: str
    start_time: datetime
    end_time: datetime

    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    meeting_link: str | None = None

    external_event_id: str | None = None  # Google Calendar ID
    metadata_info: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
