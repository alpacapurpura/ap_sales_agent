"""LaunchEdition domain entity — represents one launch of an offer.

An edition is the concrete instance of an offer at a moment in time: a
masterclass on March 15, a bootcamp cohort starting July 1, a service
intake for Q3. Each edition owns its own dates, pricing tiers, landing,
and assets (per-edition scoping lands in Phase 3).

Lifecycle (``EditionStatus``):

    DRAFT ──► UPCOMING ──► ACTIVE ──► COMPLETED
      │          │            │           ▲
      └──► CANCELLED  ◄───────┘           │
                                         (terminal)

Visibility (``EditionVisibility``):

    PRIVATE (default)  →  editor-only, invisible to sales agent & public URLs
    PUBLIC             →  available for enrollment by leads

Placeholder editions: every offer of an edition-supporting archetype is
born with a DRAFT + PRIVATE placeholder edition #1 that has no dates.
The user fills it in and eventually publishes it.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import model_validator

from src.modules.offer.domain.offer import PricingStructure
from src.shared.domain.base_entity import BaseEntity


class EditionStatus(StrEnum):
    """Lifecycle state of a launch edition."""

    DRAFT = "draft"  # being configured, not ready to publish
    UPCOMING = "upcoming"  # dates set, published (or ready to publish)
    ACTIVE = "active"  # currently running
    COMPLETED = "completed"  # finished successfully
    CANCELLED = "cancelled"  # soft-deleted / cancelled


class EditionVisibility(StrEnum):
    """Whether the edition is discoverable outside the editor.

    PRIVATE editions are invisible to the sales agent (never offered to leads)
    and to public landing URLs. PUBLIC editions are offered for enrollment.

    Decoupled from ``EditionStatus`` on purpose: an ACTIVE edition may be
    temporarily flipped to PRIVATE to pause intake without archiving it,
    and a DRAFT edition cannot be PUBLIC under any circumstance (validator
    enforces this).
    """

    PRIVATE = "private"
    PUBLIC = "public"


# Statuses that require a start_date to be set. DRAFT may have a null
# start_date (placeholder), but UPCOMING/ACTIVE must have a concrete date
# for the sales agent to make any promise about "when".
_STATUSES_REQUIRING_START_DATE: frozenset[EditionStatus] = frozenset({EditionStatus.UPCOMING, EditionStatus.ACTIVE})


class LaunchEdition(BaseEntity):
    """One launch/edition of an offer (cohort, event date, workshop run).

    See module docstring for lifecycle & visibility rules.
    """

    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    edition_name: str
    edition_number: int

    # Nullable: placeholder editions have no date yet. Transitions to
    # UPCOMING / ACTIVE / PUBLIC require a concrete value (enforced below).
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

    pricing_override: list[PricingStructure] | None = None

    capacity: int | None = None
    enrollment_count: int = 0

    status: EditionStatus = EditionStatus.DRAFT
    visibility: EditionVisibility = EditionVisibility.PRIVATE

    location_override: dict[str, Any] | None = None
    notes: str | None = None

    # Set when this edition was created by cloning another. Used by the
    # clone-with-evolution flow (Phase 3) to surface provenance in the UI
    # and to inherit landing/asset templates.
    cloned_from_edition_id: UUID | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_invariants(self) -> LaunchEdition:
        """Enforce the lifecycle + visibility invariants.

        Rules:

        - ``end_date`` >= ``start_date`` when both set.
        - ``registration_end`` >= ``registration_start`` when both set.
        - PUBLIC editions MUST have a ``start_date`` (can't offer undated
          editions to leads).
        - UPCOMING / ACTIVE editions MUST have a ``start_date``.
        - DRAFT editions MUST be PRIVATE (can't publish a draft).

        Raises :class:`ValueError` if any rule is violated — Pydantic wraps
        this into a ``ValidationError`` at the boundary.
        """
        if self.end_date and self.start_date and self.end_date < self.start_date:
            msg = "end_date cannot be before start_date"
            raise ValueError(msg)

        if self.registration_start and self.registration_end and self.registration_end < self.registration_start:
            msg = "registration_end cannot be before registration_start"
            raise ValueError(msg)

        if self.visibility == EditionVisibility.PUBLIC and self.start_date is None:
            msg = "A public edition requires start_date"
            raise ValueError(msg)

        if self.status in _STATUSES_REQUIRING_START_DATE and self.start_date is None:
            msg = f"{self.status.value} edition requires start_date"
            raise ValueError(msg)

        if self.status == EditionStatus.DRAFT and self.visibility == EditionVisibility.PUBLIC:
            msg = "A draft edition cannot be public; promote to upcoming first"
            raise ValueError(msg)

        return self


class LaunchEditionCreate(BaseEntity):
    """DTO for creating a new edition."""

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None
    cloned_from_edition_id: UUID | None = None


class LaunchEditionUpdate(BaseEntity):
    """DTO for patching an edition (all fields optional)."""

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str | None = None
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    enrollment_count: int | None = None
    status: EditionStatus | None = None
    visibility: EditionVisibility | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None
