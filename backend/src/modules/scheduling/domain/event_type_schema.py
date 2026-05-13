"""Event Type Schema domain definitions.

Canonical location: src.shared.domain.schemas.scheduling
Re-exported here for backward compatibility.
"""

from luana_core_platform.domain.schemas.scheduling import (
    BookingConfig,
    ConfirmationButton,
    EventType,
    EventTypeUpdate,
    SchedulingLimits,
)

__all__ = [
    "BookingConfig",
    "ConfirmationButton",
    "EventType",
    "EventTypeUpdate",
    "SchedulingLimits",
]
