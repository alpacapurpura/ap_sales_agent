"""Enumeration types for the scheduling domain."""

from enum import StrEnum


class AppointmentStatus(StrEnum):
    """Enumerate appointment status values."""

    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
