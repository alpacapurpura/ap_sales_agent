"""Offer lifecycle value objects and transition rules.

Pure Python — no framework imports. The canonical state machine table for
the Draft/Active/Paused/Archived flow exposed by the header switcher.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class OfferLifecycleStatus(StrEnum):
    """Writable lifecycle status as exposed by the header switcher.

    Subset of ``OfferStatus`` that the UI can mutate. ``WAITLIST`` and
    ``SOLD_OUT`` remain in ``OfferStatus`` but are out of scope for this
    feature.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


LIFECYCLE_TRANSITIONS: dict[OfferLifecycleStatus, set[OfferLifecycleStatus]] = {
    OfferLifecycleStatus.DRAFT: {
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.ACTIVE: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.PAUSED,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.PAUSED: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    # ARCHIVED is terminal from the header endpoint — use POST /restore.
    OfferLifecycleStatus.ARCHIVED: set(),
}


def is_transition_allowed(
    from_status: OfferLifecycleStatus,
    to_status: OfferLifecycleStatus,
) -> bool:
    """Return True if ``from_status → to_status`` is a legal transition."""
    if from_status == to_status:
        # No-op is always allowed; service layer may choose to short-circuit.
        return True
    return to_status in LIFECYCLE_TRANSITIONS.get(from_status, set())


@dataclass(frozen=True)
class OfferLifecycleTransition:
    """Value object describing a single status change."""

    offer_id: UUID
    tenant_id: UUID
    from_status: OfferLifecycleStatus
    to_status: OfferLifecycleStatus
    occurred_at: datetime
    actor_user_id: UUID | None = None
    reason: str | None = None

    def is_archival(self) -> bool:
        """Check if archival."""
        return self.to_status is OfferLifecycleStatus.ARCHIVED


class InvalidLifecycleTransitionError(ValueError):
    """Raised when the requested transition is not in the state machine."""

    def __init__(
        self,
        from_status: OfferLifecycleStatus,
        to_status: OfferLifecycleStatus,
    ) -> None:
        """Initialize instance."""
        allowed = sorted(s.value for s in LIFECYCLE_TRANSITIONS.get(from_status, set()))
        super().__init__(
            f"Invalid transition {from_status.value} -> {to_status.value}. Allowed targets: {allowed}",
        )
        self.from_status = from_status
        self.to_status = to_status


__all__ = [
    "LIFECYCLE_TRANSITIONS",
    "InvalidLifecycleTransitionError",
    "OfferLifecycleStatus",
    "OfferLifecycleTransition",
    "is_transition_allowed",
]
