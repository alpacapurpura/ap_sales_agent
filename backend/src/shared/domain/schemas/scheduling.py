"""Scheduling domain schemas shared across modules.

Canonical definitions for EventType, AvailabilitySchedule and related schemas.
These are used by both ``scheduling``, ``connections``, and ``sales_agent`` modules.
"""

import uuid
from typing import Any

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


class SchedulingLimits(BaseEntity):
    """Represent scheduling limits."""

    max_advance_days: int = 60
    min_advance_hours: int = 4


class BookingConfig(BaseEntity):
    """Represent booking config."""

    buffer_minutes: int = 30
    max_per_day: int | None = None
    guest_permissions: bool = True


class ConfirmationButton(BaseEntity):
    """Represent confirmation button."""

    enabled: bool = False


class EventType(BaseEntity):
    """Represent event type."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    description: str | None = None
    duration: int = 30
    is_hidden: bool = False

    scheduling_limits: SchedulingLimits = Field(default_factory=SchedulingLimits)
    booking_config: BookingConfig = Field(default_factory=BookingConfig)
    confirmation_button: ConfirmationButton = Field(default_factory=ConfirmationButton)

    metadata_info: dict[str, Any] = {}


class EventTypeUpdate(BaseEntity):
    """Represent event type update."""

    title: str | None = None
    slug: str | None = None
    description: str | None = None
    duration: int | None = None
    is_hidden: bool | None = None

    scheduling_limits: SchedulingLimits | None = None
    booking_config: BookingConfig | None = None
    confirmation_button: ConfirmationButton | None = None

    metadata_info: dict[str, Any] | None = None


# ── Availability Schedule schemas ─────────────────────────────────────────────
# Moved here from scheduling/domain/availability_schema.py so that
# connections module can import without cross-module violation.


class TimeRange(BaseEntity):
    """Represent time range."""

    start: str
    end: str


class DaySchedule(BaseEntity):
    """Represent day schedule."""

    active: bool
    ranges: list[TimeRange] = []


class WeeklySchedule(BaseEntity):
    """Represent weekly schedule."""

    monday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    tuesday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    wednesday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    thursday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    friday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    saturday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    sunday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))


class AvailabilitySchedule(BaseEntity):
    """Represent availability schedule."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    timezone: str = "UTC"
    is_default: bool = False
    schedule: WeeklySchedule


class ScheduleUpdate(BaseEntity):
    """Represent schedule update."""

    name: str | None = None
    timezone: str | None = None
    is_default: bool | None = None
    schedule: WeeklySchedule | None = None
