"""Business logic for managing launch editions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.modules.offer.domain.archetype_catalog import get_capabilities
from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
    LaunchEdition,
    PricingTier,
    resolve_active_tier,
)
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.offer.domain.offer import PricingStructure


class LaunchEditionService:
    """Service for launch edition operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with dependencies."""
        self.db = db
        self.repo = LaunchEditionRepository(db)
        self.offer_repo = OfferRepository(db)

    def create_edition(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        *,
        start_date: datetime | None = None,
        edition_name: str | None = None,
        end_date: datetime | None = None,
        registration_start: datetime | None = None,
        registration_end: datetime | None = None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        pricing_tiers: list[PricingTier] | None = None,
        capacity: int | None = None,
        location_override: dict[str, Any] | None = None,
        notes: str | None = None,
        visibility: EditionVisibility = EditionVisibility.PRIVATE,
    ) -> LaunchEdition:
        """Create a launch edition.

        Defaults to DRAFT + PRIVATE. The user publishes explicitly via
        ``publish_edition`` once fields are filled in.
        """
        offer = self.offer_repo.get_by_id(offer_id, tenant_id)
        if not offer:
            msg = f"Offer {offer_id} not found"
            raise ValueError(msg)

        return self.repo.create(
            offer_id=offer_id,
            tenant_id=tenant_id,
            edition_name=edition_name,
            start_date=start_date,
            end_date=end_date,
            registration_start=registration_start,
            registration_end=registration_end,
            timezone=timezone,
            pricing_override=pricing_override,
            pricing_tiers=pricing_tiers,
            capacity=capacity,
            location_override=location_override,
            notes=notes,
            visibility=visibility,
        )

    def get_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        """Retrieve a single edition by id, tenant-scoped."""
        return self.repo.get_by_id(edition_id, tenant_id)

    def list_editions(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        """List all non-cancelled editions for an offer."""
        return self.repo.list_by_offer(offer_id, tenant_id)

    def list_public_editions(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        """List PUBLIC editions (UPCOMING/ACTIVE) — the set the sales agent may offer.

        Foundation for Phase 6 agent tools. Kept here so the access rule is
        one method, reusable by API, agent, and copilot.
        """
        return self.repo.list_public(offer_id, tenant_id)

    def update_edition(
        self,
        edition_id: UUID,
        tenant_id: UUID,
        data: dict,
    ) -> LaunchEdition:
        """Patch an edition. Domain invariants are re-validated by the entity."""
        current = self.repo.get_by_id(edition_id, tenant_id)
        if not current:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        # Build the prospective state and run domain validation BEFORE writing.
        projected = current.model_copy(update=data)
        LaunchEdition.model_validate(projected.model_dump())

        return self.repo.update(edition_id, tenant_id, data)

    def publish_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition:
        """Promote an edition to UPCOMING + PUBLIC.

        Enforces the full archetype-aware publishing contract, in the order
        the user would expect to resolve it (cheapest fix first):

        1. ``start_date`` must be set (all archetypes).
        2. ``end_date`` must be set if the archetype requires it (COHORT).
        3. ``location_override`` must be set if the archetype requires it
           (EXPERIENCIA / in-person events).

        This is the single path through which a placeholder becomes
        visible to the sales agent. Consolidating all publish rules here
        keeps the "ready to publish?" logic auditable in one place — the
        ``LaunchEdition`` entity never validates against an archetype
        because it doesn't know its own archetype.
        """
        edition = self.repo.get_by_id(edition_id, tenant_id)
        if edition is None:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        # Start-date check first — every archetype requires it to publish.
        if edition.start_date is None:
            msg = "upcoming edition requires start_date"
            raise ValueError(msg)

        offer = self.offer_repo.get_by_id(edition.offer_id, tenant_id)
        if offer is None:
            msg = f"Offer {edition.offer_id} not found"
            raise ValueError(msg)

        caps = get_capabilities(offer.archetype)

        if caps.requires_end_date_on_publish and edition.end_date is None:
            msg = f"{offer.archetype.value} edition requires end_date to publish"
            raise ValueError(msg)

        if caps.requires_location_on_publish and not edition.location_override:
            msg = f"{offer.archetype.value} edition requires location to publish"
            raise ValueError(msg)

        return self.update_edition(
            edition_id,
            tenant_id,
            {
                "status": EditionStatus.UPCOMING,
                "visibility": EditionVisibility.PUBLIC,
            },
        )

    def unpublish_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition:
        """Flip an edition back to PRIVATE. Does NOT change the status."""
        return self.update_edition(
            edition_id,
            tenant_id,
            {"visibility": EditionVisibility.PRIVATE},
        )

    def delete_edition(self, edition_id: UUID, tenant_id: UUID) -> None:
        """Soft-delete (transition to CANCELLED)."""
        self.repo.soft_delete(edition_id, tenant_id)

    def duplicate_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition:
        """Duplicate an edition — clones dates/pricing/capacity only.

        The richer clone-with-evolution flow (landing + assets + AI regen)
        lands in Phase 3 as a separate ``EditionCloneService``. This method
        preserves today's contract so existing callers keep working.
        """
        original = self.repo.get_by_id(edition_id, tenant_id)
        if not original:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        return self.repo.create(
            offer_id=original.offer_id,
            tenant_id=tenant_id,
            edition_name=None,  # auto-generates "Edición #N"
            start_date=original.start_date,
            end_date=original.end_date,
            registration_start=original.registration_start,
            registration_end=original.registration_end,
            timezone=original.timezone,
            pricing_override=original.pricing_override,
            capacity=original.capacity,
            location_override=original.location_override,
            notes=original.notes,
            # Duplicates start PRIVATE + DRAFT by default — user must
            # publish explicitly.
            visibility=EditionVisibility.PRIVATE,
            status=EditionStatus.DRAFT,
            cloned_from_edition_id=original.id,
        )

    def resolve_effective_pricing(
        self,
        edition: LaunchEdition,
        tenant_id: UUID,
    ) -> tuple[list[dict[str, Any]], str]:
        """Return ``(pricing_list, currency)`` — legacy two-tuple shape.

        Resolution precedence: active ``PricingTier`` → ``pricing_override``
        → offer-level ``pricing_options``. The tuple shape is preserved for
        existing callers; new code should use :meth:`resolve_effective_pricing_full`.
        """
        pricing_list, currency, _ = self.resolve_effective_pricing_full(edition, tenant_id)
        return pricing_list, currency

    def resolve_effective_pricing_full(
        self,
        edition: LaunchEdition,
        tenant_id: UUID,
        *,
        now: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], str, PricingTier | None]:
        """Return ``(pricing_list, currency, active_tier)``.

        Precedence:

        1. Temporal pricing tiers — if the edition has any tier active
           at ``now`` (default ``utc_now()``), use that tier's pricing.
        2. Legacy ``pricing_override`` — still read so editions written
           before Phase 4 keep working until migration 048 drops the
           column.
        3. Offer-level ``pricing_options`` — baseline.
        """
        offer = self.offer_repo.get_by_id(edition.offer_id, tenant_id)
        if not offer:
            msg = f"Offer {edition.offer_id} not found"
            raise ValueError(msg)

        currency = offer.currency or ""
        active_tier = resolve_active_tier(edition.pricing_tiers, now or utc_now()) if edition.pricing_tiers else None

        if active_tier is not None:
            return (
                [p.model_dump(mode="json") for p in active_tier.pricing],
                currency,
                active_tier,
            )

        if edition.pricing_override is not None:
            return (
                [p.model_dump(mode="json") for p in edition.pricing_override],
                currency,
                None,
            )

        return (
            [p.model_dump(mode="json") for p in offer.pricing_options],
            currency,
            None,
        )
