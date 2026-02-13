from typing import Optional, Dict, Any, List
from src.services.db.models.business import Product
from .base import BaseRepository
import uuid

class OfferRepository(BaseRepository):
    """
    Repository for managing 'Offers' (which are mapped to the Product model in DB).
    Provides specialized methods for Offer Studio contexts.
    """
    
    def get_by_id(self, offer_id: str | uuid.UUID) -> Optional[Product]:
        """Get an offer by ID with tenant security check."""
        if isinstance(offer_id, str):
            try:
                offer_id = uuid.UUID(offer_id)
            except ValueError:
                return None
        
        query = self.db.query(Product).filter(Product.id == offer_id)
        query = self._apply_tenant_filter(query, Product)
        return query.first()
    
    def list_offers(self, limit: int = 20, skip: int = 0) -> List[Product]:
        """List all offers for the current tenant."""
        query = self.db.query(Product)
        query = self._apply_tenant_filter(query, Product)
        return query.order_by(Product.updated_at.desc()).offset(skip).limit(limit).all()

    def update_offer_config(self, offer_id: uuid.UUID, config: Dict[str, Any]) -> Optional[Product]:
        """Update the landing page configuration for an offer."""
        offer = self.get_by_id(offer_id)
        if not offer:
            return None
            
        offer.landing_page_config = config
        self.db.commit()
        self.db.refresh(offer)
        return offer
