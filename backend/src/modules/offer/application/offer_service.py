from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.modules.offer.domain.enums import (
    GuaranteeType,
    OfferArchetype,
    OfferStatus,
    OfferValueLevel,
)
from src.modules.offer.domain.offer import ARCHETYPE_TO_DETAILS_MAPPING, Offer
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from src.shared.domain.enums import FinancialCapacity


class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = OfferRepository(db)

    def get_offer(self, offer_id: UUID, tenant_id: UUID) -> Offer | None:
        return self.repository.get_by_id(offer_id, tenant_id)

    def list_offers(self, tenant_id: UUID) -> list[Offer]:
        return self.repository.get_all_by_tenant(tenant_id)

    def create_offer(
        self,
        name: str,
        tenant_id: UUID,
        archetype: OfferArchetype,
        format_hint: str | None = None,
        is_lead_magnet: bool = False,
        has_editions: bool | None = None,
        internal_sku: str = "",
        headline_promise: str = "",
        avatar_id: UUID | None = None,
        value_level: OfferValueLevel | None = None,
        currency: str | None = None,
    ) -> Offer:
        new_offer = Offer(
            tenant_id=tenant_id,
            public_name=name,
            internal_sku=internal_sku,
            archetype=archetype,
            format_hint=format_hint,
            is_lead_magnet=is_lead_magnet,
            has_editions=has_editions,
            value_level=value_level,
            headline_promise=headline_promise,
            primary_outcome="",
            time_to_value="",
            target_avatar_match=[],
            requires_application=False,
            min_financial_capacity=FinancialCapacity.LOW_INCOME,
            pricing_options=[],
            # Resolved from TenantLocale at the API layer. Persisted as-is so
            # the offer always carries an explicit currency after creation.
            currency=currency,
            guarantee_type=GuaranteeType.NONE,
            guarantee_terms="",
            status=OfferStatus.DRAFT,
        )
        return self.repository.create(new_offer)

    def update_offer(self, offer: Offer, tenant_id: UUID) -> Offer:
        return self.repository.update(offer, tenant_id)

    def list_archived_offers(self, tenant_id: UUID) -> list[Offer]:
        """Return offers archived but not soft-deleted."""
        return self.repository.list_archived(tenant_id)

    def archive_offer(self, offer_id: UUID, tenant_id: UUID) -> Offer:
        """Archive an offer and unpublish its embedded landing page config.

        Side-effect: if the offer carries an embedded ``landing_page_config``
        with ``is_published=True``, it is flipped to False in the same
        transaction. Other config fields are preserved so republishing later
        is a one-flag change. The landing_page_config lives inside the Offer
        aggregate (JSONB column), so no cross-module call is needed.
        """
        offer = self.repository.get_by_id(offer_id, tenant_id, include_archived=True)
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")

        # Unpublish embedded landing page config if present + published.
        if offer.landing_page_config and offer.landing_page_config.get("is_published"):
            offer.landing_page_config = {
                **offer.landing_page_config,
                "is_published": False,
            }
            self.repository.update(offer, tenant_id)

        archived = self.repository.archive(offer_id, tenant_id)
        if archived is None:
            # Should not happen because we just loaded it — defensive.
            raise HTTPException(status_code=404, detail="Offer not found")
        return archived

    def restore_offer(self, offer_id: UUID, tenant_id: UUID) -> Offer:
        """Clear the archived_at flag. Does NOT republish landings."""
        offer = self.repository.restore(offer_id, tenant_id)
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        return offer

    def delete_offer(self, offer_id: UUID, tenant_id: UUID) -> None:
        """Soft-delete an offer. Requires the offer to be archived first.

        Returns 409 if the offer is active — the UI should force archival
        before deletion to prevent accidental removal from the active list.
        """
        offer = self.repository.get_by_id(offer_id, tenant_id, include_archived=True)
        if offer is None:
            raise HTTPException(status_code=404, detail="Offer not found")
        if offer.archived_at is None:
            raise HTTPException(
                status_code=409,
                detail="Archivá el offer antes de eliminarlo.",
            )
        if not self.repository.soft_delete(offer_id, tenant_id):
            raise HTTPException(status_code=404, detail="Offer not found")

    def patch_offer(
        self, offer_id: UUID, tenant_id: UUID, update_data: dict[str, Any]
    ) -> Offer:
        offer = self.repository.get_by_id(offer_id, tenant_id)
        if not offer:
            raise ValueError(f"Offer with id {offer_id} not found")

        current_data = offer.model_dump()

        if "specific_details" in update_data and isinstance(
            update_data["specific_details"], dict
        ):
            detail_class = None
            archetype = offer.archetype
            if isinstance(archetype, str):
                archetype = OfferArchetype(archetype)
            detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(archetype)
            if detail_class:
                try:
                    update_data["specific_details"] = detail_class(
                        **update_data["specific_details"]
                    )
                except Exception as e:
                    raise ValueError(
                        f"Invalid specific_details structure for archetype {archetype}: {e!s}"
                    )

        current_data.update(update_data)

        try:
            updated_offer = Offer.model_validate(current_data)
        except Exception as e:
            raise ValueError(f"Invalid update data: {e!s}")

        return self.repository.update(updated_offer, tenant_id)
