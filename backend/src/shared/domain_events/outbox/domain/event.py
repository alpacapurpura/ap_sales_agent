"""Re-export DomainEvent + typed events from legacy path.

Single SSoT for domain events. Legacy path ``shared/domain/events.py``
is kept as a shim that re-exports from here.
"""

from __future__ import annotations

# Re-export everything from the original module so we don't duplicate definitions.
# This is the canonical location; legacy path re-exports from here.
from src.shared.domain.events import (
    CHANNEL_TYPE_TO_CAPTURE_SLUG,
    AccessGrantedEvent,
    AppointmentEvent,
    BookingLinkCreatedEvent,
    BookingMissedEvent,
    BrandSectionUpdatedEvent,
    ChurnEvent,
    DomainEvent,
    ExtractionJobCompletedEvent,
    ExtractionSectionCompletedEvent,
    LeadCapturedEvent,
    PaymentLinkCreatedEvent,
    PaymentReceivedEvent,
    PersonalityProfileUpdatedEvent,
    SaleCompletedEvent,
)

__all__ = [
    "CHANNEL_TYPE_TO_CAPTURE_SLUG",
    "AccessGrantedEvent",
    "AppointmentEvent",
    "BookingLinkCreatedEvent",
    "BookingMissedEvent",
    "BrandSectionUpdatedEvent",
    "ChurnEvent",
    "DomainEvent",
    "ExtractionJobCompletedEvent",
    "ExtractionSectionCompletedEvent",
    "LeadCapturedEvent",
    "PaymentLinkCreatedEvent",
    "PaymentReceivedEvent",
    "PersonalityProfileUpdatedEvent",
    "SaleCompletedEvent",
]
