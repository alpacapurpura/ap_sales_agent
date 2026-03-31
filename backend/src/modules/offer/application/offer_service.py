from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
from src.modules.offer.domain.offer import Offer, OfferType, OFFER_TYPE_TO_DETAILS_MAPPING, ARCHETYPE_TO_DETAILS_MAPPING
from src.modules.offer.domain.enums import (
    OfferStatus, GuaranteeType, OfferArchetype, ARCHETYPE_DEFAULT_TYPE
)
from src.modules.crm.domain.enums import FinancialCapacity

class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = OfferRepository(db)

    def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        return self.repository.get_by_id(offer_id)

    def list_offers(self, tenant_id: UUID) -> List[Offer]:
        return self.repository.get_all_by_tenant(tenant_id)

    def create_offer(
        self,
        name: str,
        tenant_id: UUID,
        offer_type: Optional[OfferType] = None,
        archetype: Optional[OfferArchetype] = None,
        format_hint: Optional[str] = None,
        is_lead_magnet: bool = False,
        internal_sku: str = "",
        headline_promise: str = "",
        avatar_id: Optional[UUID] = None,
    ) -> Offer:
        # Resolve type from archetype if not provided
        if archetype and not offer_type:
            offer_type = ARCHETYPE_DEFAULT_TYPE.get(archetype, OfferType.SELF_PACED_COURSE)

        if not offer_type:
            offer_type = OfferType.FREE_RESOURCE

        new_offer = Offer(
            tenant_id=tenant_id,
            public_name=name,
            internal_sku=internal_sku,
            type=offer_type,
            archetype=archetype,
            format_hint=format_hint,
            is_lead_magnet=is_lead_magnet,
            headline_promise=headline_promise,
            primary_outcome="",
            time_to_value="",
            target_avatar_match=[],
            requires_application=False,
            min_financial_capacity=FinancialCapacity.LOW_INCOME,
            pricing_options=[],
            guarantee_type=GuaranteeType.NONE,
            guarantee_terms="",
            status=OfferStatus.DRAFT
        )
        return self.repository.create(new_offer)

    def update_offer(self, offer: Offer) -> Offer:
        return self.repository.update(offer)

    def patch_offer(self, offer_id: UUID, tenant_id: UUID, update_data: Dict[str, Any]) -> Offer:
        offer = self.repository.get_by_id(offer_id)
        if not offer:
            raise ValueError(f"Offer with id {offer_id} not found")
        
        if offer.tenant_id != tenant_id:
            raise ValueError("Access denied: Offer belongs to another tenant")

        # Merge updates using model_dump and model_validate for full validation
        current_data = offer.model_dump()
        
        # Helper: Ensure specific_details is correctly typed before validation to avoid Union ambiguity
        if "specific_details" in update_data and isinstance(update_data["specific_details"], dict):
            # Archetype takes priority for detail class dispatch
            detail_class = None
            if offer.archetype:
                detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(OfferArchetype(offer.archetype) if isinstance(offer.archetype, str) else offer.archetype)
            if not detail_class:
                detail_class = OFFER_TYPE_TO_DETAILS_MAPPING.get(offer.type)
            if detail_class:
                try:
                    # Manually instantiate to force the correct type
                    update_data["specific_details"] = detail_class(**update_data["specific_details"])
                except Exception as e:
                    raise ValueError(f"Invalid specific_details structure for type {offer.type}: {str(e)}")

        # Deep merge for specific_details if needed, but for now we assume replacement or top-level merge
        # If update_data has 'specific_details', it replaces the old one.
        current_data.update(update_data)
        
        # Re-validate the entire object. This ensures:
        # 1. specific_details dict is converted back to the correct Pydantic model (Polymorphism)
        # 2. Consistency rules in Offer.validate_consistency are checked
        try:
            updated_offer = Offer.model_validate(current_data)
        except Exception as e:
            raise ValueError(f"Invalid update data: {str(e)}")
        
        return self.repository.update(updated_offer)
