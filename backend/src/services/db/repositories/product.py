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

        # Helper to update nested dictionary fields properly
        def update_nested_dict(target_obj, field_name, new_data):
            current_data = getattr(target_obj, field_name, {}) or {}
            if new_data:
                # Merge logic: new keys overwrite old keys
                merged = {**current_data, **new_data}
                setattr(target_obj, field_name, merged)

      # Fields that map to metadata_info
        metadata_fields = [
            'onboarding_action', 'onboarding_url', 'calendar_type_id', 
            'checkout_page_url', 'vsl_link',
            'support_duration_days',
            'marketing_pain_points', 'marketing_desires'
        ]

        # DEFENSIVE STRATEGY: Process raw metadata_info FIRST if present
        # This prevents it from overwriting specific property updates (like marketing_pain_points)
        # that might come in the same payload but should take precedence.
        if 'metadata_info' in update_data:
            raw_metadata = update_data.pop('metadata_info')
            if raw_metadata:
                 if product.metadata_info is None:
                    product.metadata_info = {}
                 # Merge existing with incoming raw metadata
                 merged_meta = {**product.metadata_info, **raw_metadata}
                 product.metadata_info = merged_meta

        # Generic Update for remaining fields
        for field, value in update_data.items():
            # Handle special metadata fields mapping
            if field in metadata_fields:
                if product.metadata_info is None:
                    product.metadata_info = {}
                # Important: Create a new dict to trigger SQLAlchemy detection
                new_meta = dict(product.metadata_info)
                new_meta[field] = value
                product.metadata_info = new_meta
                continue

            # SYNC LOGIC: specific_details -> columns
            # Ensure critical flags in specific_details are synced to top-level columns for querying
            if field == 'specific_details' and isinstance(value, dict):
                if 'is_application_required' in value:
                    product.requires_application = value['is_application_required']

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
