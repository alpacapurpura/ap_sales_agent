from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from src.services.db.models.business import Product
from .base import BaseRepository
import uuid

class ProductRepository(BaseRepository):
    def get_by_id(self, product_id: str | uuid.UUID) -> Optional[Product]:
        if isinstance(product_id, str):
            try:
                product_id = uuid.UUID(product_id)
            except ValueError:
                return None
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def list_products(self, limit: int = 20, skip: int = 0) -> List[Product]:
        return self.db.query(Product).order_by(Product.name).offset(skip).limit(limit).all()

    def update_product(self, product_id: str | uuid.UUID, update_data: Dict[str, Any]) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Update simple fields
        if "name" in update_data:
            product.name = update_data["name"]
        
        if "avatar_id" in update_data:
            product.avatar_id = update_data["avatar_id"]

        # Update JSONB fields (merge strategy)
        if "pricing" in update_data:
            current_pricing = dict(product.pricing) if product.pricing else {}
            current_pricing.update(update_data["pricing"])
            product.pricing = current_pricing

        if "metadata_info" in update_data:
            current_meta = dict(product.metadata_info) if product.metadata_info else {}
            current_meta.update(update_data["metadata_info"])
            product.metadata_info = current_meta

        self.db.commit()
        self.db.refresh(product)
        return product

    def create_product(self, name: str, type: str = "program") -> Product:
        product = Product(name=name, type=type)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
