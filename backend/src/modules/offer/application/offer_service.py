from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
from src.modules.offer.domain.offer import Offer, OfferType

class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = OfferRepository(db)

    def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        return self.repository.get_by_id(offer_id)

    def list_offers(self, tenant_id: UUID) -> List[Offer]:
        return self.repository.get_all_by_tenant(tenant_id)

    def create_offer(self, name: str, offer_type: OfferType, tenant_id: UUID, internal_sku: str = "") -> Offer:
        # Initialize default Offer
        new_offer = Offer(
            tenant_id=tenant_id,
            public_name=name,
            internal_sku=internal_sku,
            type=offer_type,
            headline_promise="",
            primary_outcome="",
            time_to_value="",
            target_avatar_match=[],
            requires_application=False,
            min_financial_capacity="low", # Default enum value? Needs import or string. String "low" matches default in many schemas
            pricing_options=[],
            guarantee_type="none",
            guarantee_terms="",
            status="draft"
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

        # Merge updates using model_copy as requested.
        # Note: If update_data contains raw dictionaries for nested Pydantic models,
        # model_copy might assign them as dicts. The repository expects Pydantic models.
        # If specific_details or similar complex fields are updated, ensure update_data
        # contains properly instantiated models or that the repository can handle dicts.
        updated_offer = offer.model_copy(update=update_data)
        
        return self.repository.update(updated_offer)
