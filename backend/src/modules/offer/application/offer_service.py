"""Offer service."""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.modules.offer.domain.archetype_catalog import get_capabilities
from src.modules.offer.domain.enums import (
    GuaranteeType,
    OfferArchetype,
    OfferStatus,
    OfferValueLevel,
)
from src.modules.offer.domain.offer import (
    ARCHETYPE_TO_DETAILS_MAPPING,
    Offer,
    PricingStructure,
)
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from src.shared.domain.enums import FinancialCapacity


class OfferService:
    """Service for offer operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with dependencies."""
        self.db = db
        self.repository = OfferRepository(db)
        self._edition_repo = LaunchEditionRepository(db)

    def get_offer(self, offer_id: UUID, tenant_id: UUID) -> Offer | None:
        """Retrieve offer."""
        return self.repository.get_by_id(offer_id, tenant_id)

    def list_offers(self, tenant_id: UUID) -> list[Offer]:
        """List offers."""
        return self.repository.get_all_by_tenant(tenant_id)

    def create_offer(
        self,
        name: str,
        tenant_id: UUID,
        archetype: OfferArchetype,
        format_hint: str | None = None,
        preset_id: str | None = None,
        is_lead_magnet: bool = False,
        has_editions: bool | None = None,
        internal_sku: str = "",
        headline_promise: str = "",
        avatar_id: UUID | None = None,
        value_level: OfferValueLevel | None = None,
        currency: str | None = None,
        pricing_options: list[PricingStructure] | None = None,
    ) -> Offer:
        """Create offer."""
        # Invariant: value_level == LEAD_MAGNET iff is_lead_magnet. The
        # wizard can pass either flag; we normalize here so the ladder
        # grouping (frontend) never sees an inconsistent state. Default
        # for paid offers is ACTIVACION (first paid rung), never NULL —
        # a NULL value_level used to collapse into LEAD_MAGNET via a
        # silent frontend fallback, which is the bug this guards against.
        is_lead_magnet, value_level = self._normalize_ladder_position(
            is_lead_magnet=is_lead_magnet,
            value_level=value_level,
        )
        new_offer = Offer(
            tenant_id=tenant_id,
            public_name=name,
            internal_sku=internal_sku,
            archetype=archetype,
            format_hint=format_hint,
            preset_id=preset_id,
            is_lead_magnet=is_lead_magnet,
            has_editions=has_editions,
            value_level=value_level,
            headline_promise=headline_promise,
            primary_outcome="",
            time_to_value="",
            target_avatar_match=[],
            requires_application=False,
            min_financial_capacity=FinancialCapacity.LOW_INCOME,
            pricing_options=list(pricing_options or []),
            # Resolved from TenantLocale at the API layer. Persisted as-is so
            # the offer always carries an explicit currency after creation.
            currency=currency,
            guarantee_type=GuaranteeType.NONE,
            guarantee_terms="",
            status=OfferStatus.DRAFT,
        )
        created = self.repository.create(new_offer)
        self._ensure_placeholder_edition(created)
        return created

    @staticmethod
    def _normalize_ladder_position(
        *,
        is_lead_magnet: bool,
        value_level: OfferValueLevel | None,
    ) -> tuple[bool, OfferValueLevel]:
        """Enforce the ``value_level == LEAD_MAGNET iff is_lead_magnet`` invariant.

        Either flag can arrive as the source of truth (wizard sends
        ``is_lead_magnet``; IA pipelines and legacy payloads may send
        ``value_level``). Any inconsistency is resolved toward the
        lead-magnet state when either signal says so, and paid offers
        default to ``ACTIVACION`` instead of NULL.
        """
        if is_lead_magnet or value_level == OfferValueLevel.LEAD_MAGNET:
            return True, OfferValueLevel.LEAD_MAGNET
        return False, value_level or OfferValueLevel.ACTIVACION

    def _ensure_placeholder_edition(self, offer: Offer) -> None:
        """Create a DRAFT + PRIVATE placeholder edition #1 for edition-supporting offers.

        Idempotent: if the offer already has an edition (e.g. seeded by
        migration, or created via a different code path), this is a no-op.
        Runs in the same session as the offer insert for atomicity — if the
        edition write fails the offer insert is rolled back by the caller's
        transaction.
        """
        if offer.id is None or offer.tenant_id is None:
            return
        if not get_capabilities(offer.archetype).supports_editions:
            return
        existing = self._edition_repo.list_by_offer(offer.id, offer.tenant_id)
        if existing:
            return
        self._edition_repo.create(
            offer_id=offer.id,
            tenant_id=offer.tenant_id,
            start_date=None,
            edition_name="Edición #1",
        )

    def update_offer(self, offer: Offer, tenant_id: UUID) -> Offer:
        """Update offer."""
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
        self,
        offer_id: UUID,
        tenant_id: UUID,
        update_data: dict[str, Any],
    ) -> Offer:
        """Patch offer."""
        offer = self.repository.get_by_id(offer_id, tenant_id)
        if not offer:
            msg = f"Offer with id {offer_id} not found"
            raise ValueError(msg)

        current_data = offer.model_dump()

        if "specific_details" in update_data and isinstance(
            update_data["specific_details"],
            dict,
        ):
            detail_class = None
            archetype = offer.archetype
            if isinstance(archetype, str):
                archetype = OfferArchetype(archetype)
            detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(archetype)
            if detail_class:
                try:
                    update_data["specific_details"] = detail_class(
                        **update_data["specific_details"],
                    )
                except Exception as e:
                    msg = f"Invalid specific_details structure for archetype {archetype}: {e!s}"
                    raise ValueError(msg) from e

        current_data.update(update_data)

        try:
            updated_offer = Offer.model_validate(current_data)
        except Exception as e:
            msg = f"Invalid update data: {e!s}"
            raise ValueError(msg) from e

        return self.repository.update(updated_offer, tenant_id)
