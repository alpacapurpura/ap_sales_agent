from typing import Optional, Dict, Any, List
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
        
        query = self.db.query(Product).filter(Product.id == product_id)
        query = self._apply_tenant_filter(query, Product)
        return query.first()
    
    def list_products(self, limit: int = 20, skip: int = 0) -> List[Product]:
        query = self.db.query(Product)
        query = self._apply_tenant_filter(query, Product)
        return query.order_by(Product.name).offset(skip).limit(limit).all()

    def update_product(self, product_id: str | uuid.UUID, update_data: Dict[str, Any]) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if not product:
            return None

        # Generic Update for all top-level fields
        for field, value in update_data.items():
            if hasattr(product, field) and value is not None:
                setattr(product, field, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def create_product(self, name: str, type: str = "program") -> Product:
        product = Product(name=name, type=type, status="DRAFT")
        self._set_tenant(product)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
