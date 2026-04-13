"""Availability Schema domain definitions."""

import uuid

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


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
