import uuid

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


class TimeRange(BaseEntity):
    start: str
    end: str


class DaySchedule(BaseEntity):
    active: bool
    ranges: list[TimeRange] = []


class WeeklySchedule(BaseEntity):
    monday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    tuesday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    wednesday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    thursday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    friday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    saturday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))
    sunday: DaySchedule = Field(default_factory=lambda: DaySchedule(active=False))


class AvailabilitySchedule(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    timezone: str = "UTC"
    is_default: bool = False
    schedule: WeeklySchedule


class ScheduleUpdate(BaseEntity):
    name: str | None = None
    timezone: str | None = None
    is_default: bool | None = None
    schedule: WeeklySchedule | None = None
