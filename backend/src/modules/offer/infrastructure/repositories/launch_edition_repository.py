"""Repository for LaunchEdition CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
    LaunchEdition,
    PricingTier,
)
from src.modules.offer.domain.offer import PricingStructure
from src.modules.offer.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session


class LaunchEditionRepository:
    """Repository for launch edition persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def _to_domain(self, model: LaunchEditionModel) -> LaunchEdition:
        pricing = None
        if model.pricing_override is not None:
            pricing = [PricingStructure(**p) for p in model.pricing_override]

        tiers: list[PricingTier] = []
        if model.pricing_tiers:
            tiers = [PricingTier.model_validate(t) for t in model.pricing_tiers]

        return LaunchEdition(
            id=model.id,
            offer_id=model.offer_id,
            tenant_id=model.tenant_id,
            edition_name=model.edition_name,
            edition_number=model.edition_number,
            start_date=model.start_date,
            end_date=model.end_date,
            registration_start=model.registration_start,
            registration_end=model.registration_end,
            timezone=model.timezone or "UTC",
            pricing_override=pricing,
            pricing_tiers=tiers,
            capacity=model.capacity,
            enrollment_count=model.enrollment_count or 0,
            status=EditionStatus(model.status) if model.status else EditionStatus.DRAFT,
            visibility=(EditionVisibility(model.visibility) if model.visibility else EditionVisibility.PRIVATE),
            location_override=model.location_override,
            notes=model.notes,
            cloned_from_edition_id=model.cloned_from_edition_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_next_edition_number(self, offer_id: UUID) -> int:
        """Return the next sequential edition number for an offer."""
        stmt = select(
            func.coalesce(func.max(LaunchEditionModel.edition_number), 0),
        ).where(
            LaunchEditionModel.offer_id == offer_id,
        )
        result = self.db.execute(stmt).scalar()
        return (result or 0) + 1

    def create(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        *,
        edition_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        registration_start: datetime | None = None,
        registration_end: datetime | None = None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        pricing_tiers: list[PricingTier] | None = None,
        capacity: int | None = None,
        location_override: dict | None = None,
        notes: str | None = None,
        visibility: EditionVisibility = EditionVisibility.PRIVATE,
        status: EditionStatus = EditionStatus.DRAFT,
        cloned_from_edition_id: UUID | None = None,
    ) -> LaunchEdition:
        """Create a new launch edition.

        Domain invariants are validated by ``LaunchEdition`` — the repo here
        trusts the caller has built a valid state. Callers should run the
        domain validation (construct the entity) BEFORE invoking create when
        the state is non-trivial (e.g. a UPCOMING + PUBLIC edition).
        """
        edition_number = self.get_next_edition_number(offer_id)
        if not edition_name:
            edition_name = f"Edición #{edition_number}"

        pricing_json = None
        if pricing_override is not None:
            pricing_json = [p.model_dump(mode="json") for p in pricing_override]

        tiers_json = None
        if pricing_tiers is not None:
            tiers_json = [tier.model_dump(mode="json") for tier in pricing_tiers]

        model = LaunchEditionModel(
            offer_id=offer_id,
            tenant_id=tenant_id,
            edition_name=edition_name,
            edition_number=edition_number,
            start_date=start_date,
            end_date=end_date,
            registration_start=registration_start,
            registration_end=registration_end,
            timezone=timezone,
            pricing_override=pricing_json,
            pricing_tiers=tiers_json,
            capacity=capacity,
            enrollment_count=0,
            status=status.value,
            visibility=visibility.value,
            location_override=location_override,
            notes=notes,
            cloned_from_edition_id=cloned_from_edition_id,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        self.db.commit()
        return self._to_domain(model)

    def get_by_id(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        """Retrieve by id, tenant-scoped."""
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_offer(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        """List all non-cancelled editions for an offer, most-recent-first.

        Editions with NULL ``start_date`` (placeholders) sort last.
        """
        stmt = (
            select(LaunchEditionModel)
            .where(
                LaunchEditionModel.offer_id == offer_id,
                LaunchEditionModel.tenant_id == tenant_id,
                LaunchEditionModel.status != EditionStatus.CANCELLED.value,
            )
            .order_by(LaunchEditionModel.start_date.desc().nulls_last())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_public(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        """List PUBLIC editions that the sales agent may offer to leads.

        Excludes DRAFT, CANCELLED, and any PRIVATE editions regardless of
        status. Ordered ascending by ``start_date`` so the soonest upcoming
        edition comes first — the agent picks ``[0]`` to propose.
        """
        stmt = (
            select(LaunchEditionModel)
            .where(
                LaunchEditionModel.offer_id == offer_id,
                LaunchEditionModel.tenant_id == tenant_id,
                LaunchEditionModel.visibility == EditionVisibility.PUBLIC.value,
                LaunchEditionModel.status.in_([EditionStatus.UPCOMING.value, EditionStatus.ACTIVE.value]),
            )
            .order_by(LaunchEditionModel.start_date.asc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def update(self, edition_id: UUID, tenant_id: UUID, data: dict) -> LaunchEdition:
        """Patch an edition with a dict of field values.

        Unknown keys are ignored. PricingStructure lists may arrive as domain
        objects (auto-serialized) or as pre-serialized dict lists.
        """
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        for key, raw_value in data.items():
            resolved = raw_value
            if (
                key in ("pricing_override", "pricing_tiers")
                and raw_value is not None
                and isinstance(raw_value, list)
                and raw_value
                and hasattr(raw_value[0], "model_dump")
            ):
                resolved = [p.model_dump(mode="json") for p in raw_value]
            if hasattr(model, key):
                setattr(model, key, resolved)

        self.db.flush()
        self.db.refresh(model)
        self.db.commit()
        return self._to_domain(model)

    def soft_delete(self, edition_id: UUID, tenant_id: UUID) -> None:
        """Soft-delete by transitioning to CANCELLED."""
        self.update(edition_id, tenant_id, {"status": EditionStatus.CANCELLED.value})
