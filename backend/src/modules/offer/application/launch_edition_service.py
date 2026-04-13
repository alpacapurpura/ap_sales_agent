"""Business logic for managing launch editions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import LaunchEdition
from src.modules.offer.domain.offer import PricingStructure
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)


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
        start_date: datetime,
        edition_name: str | None = None,
        end_date: datetime | None = None,
        registration_start: datetime | None = None,
        registration_end: datetime | None = None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        capacity: int | None = None,
        location_override: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> LaunchEdition:
        """Create edition."""
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
            capacity=capacity,
            location_override=location_override,
            notes=notes,
        )

    def get_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        """Retrieve edition."""
        return self.repo.get_by_id(edition_id, tenant_id)

    def list_editions(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        """List editions."""
        return self.repo.list_by_offer(offer_id, tenant_id)

    def update_edition(
        self,
        edition_id: UUID,
        tenant_id: UUID,
        data: dict,
    ) -> LaunchEdition:
        """Update edition."""
        return self.repo.update(edition_id, tenant_id, data)

    def delete_edition(self, edition_id: UUID, tenant_id: UUID) -> None:
        """Delete edition."""
        self.repo.soft_delete(edition_id, tenant_id)

    def duplicate_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition:
        """Duplicate edition."""
        original = self.repo.get_by_id(edition_id, tenant_id)
        if not original:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)

        return self.repo.create(
            offer_id=original.offer_id,
            tenant_id=tenant_id,
            edition_name=None,  # Auto-generate name
            start_date=original.start_date,
            end_date=original.end_date,
            registration_start=original.registration_start,
            registration_end=original.registration_end,
            timezone=original.timezone,
            pricing_override=original.pricing_override,
            capacity=original.capacity,
            location_override=original.location_override,
            notes=original.notes,
        )

    def resolve_effective_pricing(
        self,
        edition: LaunchEdition,
        tenant_id: UUID,
    ) -> tuple[list[dict[str, Any]], str]:
        """Return (pricing_list, currency). Uses override if set, else offer's pricing."""
        offer = self.offer_repo.get_by_id(edition.offer_id, tenant_id)
        if not offer:
            msg = f"Offer {edition.offer_id} not found"
            raise ValueError(msg)

        currency = offer.currency

        if edition.pricing_override is not None:
            return (
                [p.model_dump(mode="json") for p in edition.pricing_override],
                currency,
            )

        return (
            [p.model_dump(mode="json") for p in offer.pricing_options],
            currency,
        )
