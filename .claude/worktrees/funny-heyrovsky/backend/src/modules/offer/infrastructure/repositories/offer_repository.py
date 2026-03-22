from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.offer.domain.offer import Offer, OFFER_TYPE_TO_DETAILS_MAPPING
from src.modules.offer.domain.enums import OfferType, OfferStatus, OfferValueLevel
from src.modules.offer.infrastructure.models.product_model import ProductModel
from src.modules.crm.domain.enums import FinancialCapacity

class OfferRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: ProductModel) -> Offer:
        # 1. Basic Fields Mapping
        raw_type = model.type
        # Fix known legacy types
        if raw_type == "1ON1_PRIVATE_MENTORING":
             raw_type = "one_on_one_private_mentoring"

        try:
            offer_type = OfferType(raw_type)
        except ValueError:
            # Try lowercase as fallback
            try:
                offer_type = OfferType(raw_type.lower())
            except ValueError:
                # Fallback or log error for invalid type in DB
                # For now, we assume data integrity or raise
                raise ValueError(f"Invalid OfferType in DB: {model.type}")

        value_level = None
        if model.value_level:
            try:
                value_level = OfferValueLevel(model.value_level)
            except ValueError:
                pass # or log warning

        # Fix delivery_model
        delivery_model = model.delivery_model
        if delivery_model:
            try:
                # Check if valid enum value
                from src.modules.offer.domain.enums import OfferDeliveryModel
                OfferDeliveryModel(delivery_model)
            except ValueError:
                # Try lowercase
                try:
                    delivery_model = delivery_model.lower()
                    from src.modules.offer.domain.enums import OfferDeliveryModel
                    OfferDeliveryModel(delivery_model)
                except ValueError:
                    delivery_model = None
        
        # Fix guarantee_type
        guarantee_type = model.guarantee_type or "none"
        if guarantee_type == "NO_REFUNDS":
            guarantee_type = "none"
        else:
             try:
                 from src.modules.offer.domain.enums import GuaranteeType
                 GuaranteeType(guarantee_type)
             except ValueError:
                 try:
                     guarantee_type = guarantee_type.lower()
                     from src.modules.offer.domain.enums import GuaranteeType
                     GuaranteeType(guarantee_type)
                 except ValueError:
                     guarantee_type = "none"

        # Fix min_financial_capacity
        min_financial_capacity = model.min_financial_capacity or FinancialCapacity.LOW_INCOME
        if min_financial_capacity == "LOW":
             min_financial_capacity = FinancialCapacity.LOW_INCOME

        offer_data = {
            "id": model.id,
            "tenant_id": model.tenant_id,
            "internal_sku": model.internal_sku or "",
            "public_name": model.name,
            "type": offer_type,
            "value_level": value_level,
            "status": OfferStatus(model.status.lower()) if model.status else OfferStatus.DRAFT,
            "headline_promise": model.headline_promise or "",
            "primary_outcome": model.primary_outcome or "",
            "time_to_value": model.time_to_value or "",
            "target_avatar_match": model.target_avatar_match or [],
            "access_duration": model.access_duration,
            "access_duration_text": model.access_duration_text,
            "support_duration_days": model.support_duration_days,
            "delivery_model": delivery_model,
            "instructors": [], # model.instructors or [], (Removed from DB)
            "requires_application": model.requires_application or False,
            "min_financial_capacity": min_financial_capacity,
            "prerequisites": model.prerequisites or [],
            "anti_avatar_keywords": model.anti_avatar_keywords or [],
            "guarantee_type": guarantee_type,
            "guarantee_terms": model.guarantee_terms or "",
            "downsell_offer_id": model.downsell_product_id,
            "upsell_offer_id": model.upsell_product_id,
            "includes_offers": model.includes_offers or [],
            "onboarding_action": model.onboarding_action,
            "onboarding_url": model.onboarding_url,
            "vsl_link": model.vsl_link,
            "checkout_page_url": model.checkout_page_url,
            "calendar_type_id": model.calendar_type_id,
            "landing_page_config": model.landing_page_config if model.landing_page_config else None,
            "marketing_pain_points": model.marketing_pain_points or [],
            "marketing_desires": model.marketing_desires or [],
            "objections": model.objections or [],
            "metadata_info": model.metadata_info or {},
            "price_pay_in_full": None, # model.price_pay_in_full (Removed from DB)
            "currency": model.currency or "USD"
        }

        # 2. Complex Fields (JSONB)
        pricing_options_raw = model.pricing or []
        pricing_options = []
        for p in pricing_options_raw:
            if isinstance(p, dict):
                new_p = p.copy()
                if new_p.get("plan_type") == "PAY_IN_FULL":
                    new_p["plan_type"] = "one_time"
                if new_p.get("plan_type") == "SPLIT_PAY" or new_p.get("plan_type") == "split_pay":
                    new_p["plan_type"] = "payment_plan"
                
                if new_p.get("plan_type"):
                     try:
                         # check if valid
                         from src.modules.offer.domain.enums import PaymentPlanType
                         PaymentPlanType(new_p["plan_type"])
                     except ValueError:
                         try:
                             new_p["plan_type"] = new_p["plan_type"].lower()
                         except ValueError:
                             pass
                pricing_options.append(new_p)
            else:
                pricing_options.append(p)

        offer_data["pricing_options"] = pricing_options
        
        # Fix deliverables
        deliverables = model.deliverables or []
        for d in deliverables:
            if isinstance(d, dict):
                if d.get("format") == "LIVE_GROUP_CALL":
                     d["format"] = "live_session"
                # Lowercase format if possible
                if d.get("format"):
                     try:
                         from src.modules.offer.domain.enums import DeliverableFormat
                         DeliverableFormat(d["format"])
                     except ValueError:
                         try:
                             d["format"] = d["format"].lower()
                         except ValueError:
                             pass

        offer_data["deliverables"] = deliverables
        
        # 3. Polymorphic Details
        details_json = model.specific_details or {}
        if details_json:
            detail_class = OFFER_TYPE_TO_DETAILS_MAPPING.get(offer_type)
            if detail_class:
                # Fix known data issues in details_json
                if "format" in details_json and details_json["format"] == "RECORDED_CONTENT":
                     details_json["format"] = "video_course"
                
                if "structure_type" in details_json and details_json["structure_type"] == "FIXED_COHORT":
                     details_json["structure_type"] = "fixed_cohort"
                
                if "interaction_type" in details_json and details_json["interaction_type"] == "LIVE_PROGRAM_DELIVERY":
                     details_json["interaction_type"] = "group_q_and_a"
                
                if "community_platform" in details_json and details_json["community_platform"] == "ZOOM":
                     details_json["community_platform"] = "none"
                
                if "location_type" in details_json:
                     if details_json["location_type"] == "VIRTUAL":
                          details_json["location_type"] = "virtual"
                     elif details_json["location_type"] == "DESTINATION_RETREAT":
                          details_json["location_type"] = "destination_retreat"
                
                try:
                    offer_data["specific_details"] = detail_class(**details_json)
                except Exception as e:
                    # Log error but don't crash entire object if details are malformed?
                    # Strict consistency: crash.
                    # Lenient: set to None or empty.
                    # We choose strict to prevent data corruption.
                    raise ValueError(f"Error parsing specific_details for offer {model.id}: {str(e)}")

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
            # price_pay_in_full=offer.price_pay_in_full, (Removed from DB)
            currency=offer.currency,
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
            # instructors=offer.instructors, (Removed from DB)
            value_level=offer.value_level.value if offer.value_level else None,
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
            objections=[o.model_dump(mode='json') for o in offer.objections],
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
        
        ignored_keys = {'_sa_instance_state', 'created_at', 'updated_at', 'id', 'tenant_id'}
        
        for key, value in new_model_data.__dict__.items():
            if key in ignored_keys:
                continue
            if hasattr(model, key):
                setattr(model, key, value)
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
