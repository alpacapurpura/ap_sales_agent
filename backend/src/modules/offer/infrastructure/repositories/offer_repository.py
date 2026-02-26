from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.offer.domain.offer import Offer, OfferType, OFFER_TYPE_TO_DETAILS_MAPPING
from src.modules.offer.infrastructure.models.product_model import ProductModel

class OfferRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: ProductModel) -> Offer:
        # 1. Basic Fields Mapping
        offer_data = {
            "id": model.id,
            "tenant_id": model.tenant_id,
            "internal_sku": model.internal_sku or "",
            "public_name": model.name,
            "type": model.type,
            "status": model.status,
            "headline_promise": model.headline_promise or "",
            "primary_outcome": model.primary_outcome or "",
            "time_to_value": model.time_to_value or "",
            "target_avatar_match": model.target_avatar_match or [],
            "access_duration": model.access_duration,
            "access_duration_text": model.access_duration_text,
            "support_duration_days": model.support_duration_days,
            "delivery_model": model.delivery_model,
            "requires_application": model.requires_application,
            "min_financial_capacity": model.min_financial_capacity,
            "prerequisites": model.prerequisites or [],
            "anti_avatar_keywords": model.anti_avatar_keywords or [],
            "guarantee_type": model.guarantee_type,
            "guarantee_terms": model.guarantee_terms or "",
            "downsell_offer_id": model.downsell_product_id,
            "upsell_offer_id": model.upsell_product_id,
            "includes_offers": model.includes_offers or [],
            "onboarding_action": model.onboarding_action,
            "onboarding_url": model.onboarding_url,
            "vsl_link": model.vsl_link,
            "checkout_page_url": model.checkout_page_url,
            "calendar_type_id": model.calendar_type_id,
            "landing_page_config": model.landing_page_config,
            "marketing_pain_points": model.marketing_pain_points or [],
            "marketing_desires": model.marketing_desires or [],
            "metadata_info": model.metadata_info or {}
        }

        # 2. Complex Fields (JSONB)
        offer_data["pricing_options"] = model.pricing or []
        offer_data["deliverables"] = model.deliverables or []
        
        # 3. Polymorphic Details
        details_json = model.specific_details or {}
        if details_json:
            offer_type_enum = OfferType(model.type)
            detail_class = OFFER_TYPE_TO_DETAILS_MAPPING.get(offer_type_enum)
            if detail_class:
                offer_data["specific_details"] = detail_class(**details_json)

        return Offer(**offer_data)

    def _to_model(self, offer: Offer) -> ProductModel:
        # Convert Pydantic models to dict/json for storage
        pricing_data = [p.model_dump(mode='json') for p in offer.pricing_options]
        deliverables_data = [d.model_dump(mode='json') for d in offer.deliverables]
        details_data = offer.specific_details.model_dump(mode='json') if offer.specific_details else {}
        landing_config_data = offer.landing_page_config.model_dump(mode='json') if offer.landing_page_config else {}

        return ProductModel(
            id=offer.id,
            tenant_id=offer.tenant_id,
            name=offer.public_name,
            type=offer.type.value,
            status=offer.status.value,
            internal_sku=offer.internal_sku,
            pricing=pricing_data,
            specific_details=details_data,
            deliverables=deliverables_data,
            headline_promise=offer.headline_promise,
            primary_outcome=offer.primary_outcome,
            time_to_value=offer.time_to_value,
            target_avatar_match=offer.target_avatar_match, # List of enums/strings
            access_duration=offer.access_duration,
            access_duration_text=offer.access_duration_text,
            support_duration_days=offer.support_duration_days,
            delivery_model=offer.delivery_model,
            requires_application=offer.requires_application,
            min_financial_capacity=offer.min_financial_capacity,
            prerequisites=offer.prerequisites,
            anti_avatar_keywords=offer.anti_avatar_keywords,
            guarantee_type=offer.guarantee_type,
            guarantee_terms=offer.guarantee_terms,
            downsell_product_id=offer.downsell_offer_id,
            upsell_product_id=offer.upsell_offer_id,
            includes_offers=offer.includes_offers,
            onboarding_action=offer.onboarding_action,
            onboarding_url=offer.onboarding_url,
            calendar_type_id=offer.calendar_type_id,
            checkout_page_url=offer.checkout_page_url,
            vsl_link=offer.vsl_link,
            landing_page_config=landing_config_data,
            marketing_pain_points=offer.marketing_pain_points,
            marketing_desires=offer.marketing_desires,
            metadata_info=offer.metadata_info
        )

    def get_by_id(self, offer_id: UUID) -> Optional[Offer]:
        model = self.db.query(ProductModel).filter(ProductModel.id == offer_id).first()
        if model:
            return self._to_domain(model)
        return None

    def get_all_by_tenant(self, tenant_id: UUID) -> List[Offer]:
        models = self.db.query(ProductModel).filter(ProductModel.tenant_id == tenant_id).all()
        return [self._to_domain(m) for m in models]

    def create(self, offer: Offer) -> Offer:
        model = self._to_model(offer)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(self, offer: Offer) -> Offer:
        # Fetch existing model
        model = self.db.query(ProductModel).filter(ProductModel.id == offer.id).first()
        if not model:
            raise ValueError("Offer not found")
            
        # Convert domain entity to model instance (detached)
        new_model_data = self._to_model(offer)
        
        # Dynamically update fields
        # We skip internal SQLAlchemy state and primary keys if needed, 
        # but here we trust _to_model to have correct IDs.
        # Typically we want to avoid updating 'id' or 'created_at' if not intended,
        # but _to_model preserves ID. created_at is usually handled by DB server_default.
        
        ignored_keys = {'_sa_instance_state', 'created_at', 'updated_at'}
        
        for key, value in new_model_data.__dict__.items():
            if key in ignored_keys:
                continue
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
