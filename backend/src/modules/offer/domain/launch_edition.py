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

from pydantic import Field, model_validator

from src.modules.offer.domain.enums import VariantStructure
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


class PricingTier(BaseEntity):
    """One validity window inside an edition's pricing timeline.

    Models the ``early bird → regular → last call`` pattern that almost
    every launch uses. Each tier owns a slice of time and the pricing
    structure that applies during that slice.

    Windows are **half-open** (``[valid_from, valid_until)``): the
    instant a tier ends is the instant the next one begins. That
    eliminates the off-by-one ambiguity of closed intervals and the
    both-active overlap of fully-closed ones.

    ``valid_from`` / ``valid_until`` of ``None`` mean open-ended on
    that side, so ``PricingTier(label='regular', pricing=[...])`` with
    both bounds unset is "always active" — the default carried over
    from Phase 3 ``pricing_override`` rows.
    """

    label: str
    pricing: list[PricingStructure] = Field(..., min_length=1)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    sort_order: int = 0

    @model_validator(mode="after")
    def validate_window(self) -> PricingTier:
        """Reject inverted bounds — ``valid_until`` must be strictly after ``valid_from``."""
        if self.valid_from is not None and self.valid_until is not None and self.valid_until <= self.valid_from:
            msg = "valid_until must be strictly after valid_from"
            raise ValueError(msg)
        return self


def resolve_active_tier(tiers: list[PricingTier], now: datetime) -> PricingTier | None:
    """Return the tier whose window contains ``now`` with lowest ``sort_order``.

    Half-open semantics: ``valid_from <= now < valid_until``. When two
    tiers' windows overlap (should not happen because
    :class:`LaunchEdition` rejects that at the boundary — but defensive
    here), ``sort_order`` breaks the tie deterministically.
    """
    if not tiers:
        return None
    applicable = [
        tier
        for tier in sorted(tiers, key=lambda x: x.sort_order)
        if (tier.valid_from is None or tier.valid_from <= now) and (tier.valid_until is None or now < tier.valid_until)
    ]
    return applicable[0] if applicable else None


def _windows_overlap(a: PricingTier, b: PricingTier) -> bool:
    """True iff ``a`` and ``b`` share ANY instant under half-open semantics.

    Equivalent to: ``a.start < b.end AND b.start < a.end`` with
    ``None`` bounds treated as ``-inf``/``+inf``.
    """
    a_start = a.valid_from
    a_end = a.valid_until
    b_start = b.valid_from
    b_end = b.valid_until

    # Treat unbounded sides as ±∞. Two open-ended tiers overlap by
    # definition (both cover "always"), so the fast-path below catches
    # it without special-casing None.
    start_before_end = a_start is None or b_end is None or a_start < b_end
    b_start_before_a_end = b_start is None or a_end is None or b_start < a_end
    return start_before_end and b_start_before_a_end


class LaunchEdition(BaseEntity):
    """One launch/edition of an offer (cohort, event date, workshop run).

    See module docstring for lifecycle & visibility rules.
    """

    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    edition_name: str
    edition_number: int

    # Sixth SSoT axis (Sprint 7) — what kind of variant this row represents.
    # Source of truth at creation time is the parent offer's archetype, via
    # ``ARCHETYPE_CATALOG[archetype].default_variant_structure``. Defaults to
    # ``TEMPORAL_COHORT`` here only as a Pydantic-construction safety net for
    # historical fixtures and clone paths; the placeholder service derives the
    # real value from the archetype catalog and the architecture test
    # ``test_archetype_default_variant_structure_alignment`` guarantees every
    # edition-supporting archetype declares one.
    variant_structure: VariantStructure = VariantStructure.TEMPORAL_COHORT
    structure_data: dict[str, Any] = Field(default_factory=dict)
    sort_rank: int | None = None

    # Nullable: placeholder editions have no date yet. Transitions to
    # UPCOMING / ACTIVE / PUBLIC require a concrete value (enforced below).
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

    pricing_override: list[PricingStructure] | None = None
    # Temporal pricing ladder. Replaces ``pricing_override`` on new
    # code paths; read-path still inspects override for backward-compat
    # until migration 048 drops the column. See :func:`resolve_active_tier`.
    pricing_tiers: list[PricingTier] = Field(default_factory=list)

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

    @property
    def is_placeholder(self) -> bool:
        """Return True iff this edition is the auto-created placeholder.

        An edition is a placeholder iff it is DRAFT + PRIVATE with no
        start_date, pricing override, or location override — i.e. the
        default row spawned by ``OfferService`` for every edition-supporting
        offer. Once the user fills any of these in, it is no longer a
        placeholder. Computed from domain state so every consumer (API,
        frontend, copilot) agrees on the definition.
        """
        return (
            self.status == EditionStatus.DRAFT
            and self.visibility == EditionVisibility.PRIVATE
            and self.start_date is None
            and self.pricing_override is None
            and self.location_override is None
        )

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

        Archetype-specific publishing constraints (``requires_end_date``,
        ``requires_location``) are enforced by
        ``LaunchEditionService.publish_edition`` — which has access to the
        archetype via the parent offer — not here, because the edition
        entity doesn't know its own archetype.

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

        self._enforce_non_overlapping_tiers()
        return self

    def _enforce_non_overlapping_tiers(self) -> None:
        """Reject ambiguous pricing timelines at construction time.

        Two tiers whose windows share any instant would let the resolver
        pick either one; the sales agent must never have to guess which
        price is "live" right now. Half-open comparison means adjacent
        windows that only touch at a boundary are allowed.
        """
        tiers = self.pricing_tiers
        for i, tier_a in enumerate(tiers):
            for tier_b in tiers[i + 1 :]:
                if _windows_overlap(tier_a, tier_b):
                    msg = f"pricing tiers {tier_a.label!r} and {tier_b.label!r} overlap in time"
                    raise ValueError(msg)


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
