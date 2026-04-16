"""Availability Schema domain definitions.

Canonical definitions live in ``shared/domain/schemas/scheduling.py``.
This module re-exports them for backward compatibility within the scheduling module.
"""

from src.shared.domain.schemas.scheduling import (
    AvailabilitySchedule,
    DaySchedule,
    ScheduleUpdate,
    TimeRange,
    WeeklySchedule,
)

__all__ = [
    "AvailabilitySchedule",
    "DaySchedule",
    "ScheduleUpdate",
    "TimeRange",
    "WeeklySchedule",
]
