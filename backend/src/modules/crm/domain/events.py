"""CRM domain events — re-exported from shared for backward compatibility.

Canonical location: src.shared.domain.events
New code should import directly from src.shared.domain.events.
"""

from src.shared.domain.events import (
    CHANNEL_TYPE_TO_CAPTURE_SLUG,
    AppointmentEvent,
    ChurnEvent,
    LeadCapturedEvent,
    SaleCompletedEvent,
)

__all__ = [
    "CHANNEL_TYPE_TO_CAPTURE_SLUG",
    "AppointmentEvent",
    "ChurnEvent",
    "LeadCapturedEvent",
    "SaleCompletedEvent",
]
