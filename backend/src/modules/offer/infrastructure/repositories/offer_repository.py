from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.offer.domain.offer import ARCHETYPE_TO_DETAILS_MAPPING, Offer
from src.modules.offer.infrastructure.models.product_model import ProductModel
from src.modules.offer.infrastructure.repositories.enum_normalizer import (
    normalize_archetype,
    normalize_deliverables,
    normalize_delivery_model,
    normalize_financial_capacity,
    normalize_guarantee_type,
    normalize_pricing_options,
    normalize_specific_details,
    normalize_status,
    normalize_value_level,
)


class OfferRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: ProductModel) -> Offer:
        archetype = normalize_archetype(model.archetype, offer_id=model.id)

        offer_data = {
            "id": model.id,
            "tenant_id": model.tenant_id,
            "internal_sku": model.internal_sku or "",
            "public_name": model.name,
            "archetype": archetype,
            "format_hint": model.format_hint,
            "is_lead_magnet": model.is_lead_magnet or False,
            "value_level": normalize_value_level(model.value_level),
            "status": normalize_status(model.status),
            "headline_promise": model.headline_promise or "",
            "primary_outcome": model.primary_outcome or "",
            "time_to_value": model.time_to_value or "",
            "target_avatar_match": model.target_avatar_match or [],
            "access_duration": model.access_duration,
            "access_duration_text": model.access_duration_text,
            "support_duration_days": model.support_duration_days,
            "delivery_model": normalize_delivery_model(model.delivery_model),
            "instructors": [],
            "requires_application": model.requires_application or False,
            "min_financial_capacity": normalize_financial_capacity(
                model.min_financial_capacity
            ),
            "prerequisites": model.prerequisites or [],
            "anti_avatar_keywords": model.anti_avatar_keywords or [],
            "guarantee_type": normalize_guarantee_type(model.guarantee_type),
            "guarantee_terms": model.guarantee_terms or "",
            "downsell_offer_id": model.downsell_product_id,
            "upsell_offer_id": model.upsell_product_id,
            "includes_offers": model.includes_offers or [],
            "onboarding_action": model.onboarding_action,
            "onboarding_url": model.onboarding_url,
            "vsl_link": model.vsl_link,
            "checkout_page_url": model.checkout_page_url,
            "calendar_type_id": model.calendar_type_id,
            "landing_page_config": model.landing_page_config or None,
            "marketing_pain_points": model.marketing_pain_points or [],
            "marketing_desires": model.marketing_desires or [],
            "objections": model.objections or [],
            "metadata_info": model.metadata_info or {},
            "price_pay_in_full": None,
            "currency": model.currency or "USD",
            "pricing_options": normalize_pricing_options(model.pricing or []),
            "deliverables": normalize_deliverables(model.deliverables or []),
        }

        # Polymorphic Details
        details_json = model.specific_details or {}
        if details_json:
            detail_class = ARCHETYPE_TO_DETAILS_MAPPING.get(archetype)
            if detail_class:
                normalized = normalize_specific_details(details_json)
                try:
                    offer_data["specific_details"] = detail_class(**normalized)
                except Exception as e:
                    raise ValueError(
                        f"Error parsing specific_details for offer {model.id}: {e!s}"
                    )

        return Offer(**offer_data)

    def _to_model(self, offer: Offer) -> ProductModel:
        pricing_data = [p.model_dump(mode="json") for p in offer.pricing_options]
        deliverables_data = [d.model_dump(mode="json") for d in offer.deliverables]
        details_data = (
            offer.specific_details.model_dump(mode="json")
            if offer.specific_details
            else {}
        )
        landing_config_data = (
            offer.landing_page_config.model_dump(mode="json")
            if offer.landing_page_config
            else {}
        )

        return ProductModel(
            id=offer.id,
            tenant_id=offer.tenant_id,
            name=offer.public_name,
            archetype=offer.archetype.value,
            format_hint=offer.format_hint,
            is_lead_magnet=offer.is_lead_magnet,
            status=offer.status.value,
            internal_sku=offer.internal_sku,
            pricing=pricing_data,
            currency=offer.currency,
            specific_details=details_data,
            deliverables=deliverables_data,
            headline_promise=offer.headline_promise,
            primary_outcome=offer.primary_outcome,
            time_to_value=offer.time_to_value,
            target_avatar_match=offer.target_avatar_match,
            access_duration=offer.access_duration,
            access_duration_text=offer.access_duration_text,
            support_duration_days=offer.support_duration_days,
            delivery_model=offer.delivery_model,
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
            objections=[o.model_dump(mode="json") for o in offer.objections],
            metadata_info=offer.metadata_info,
        )

    def get_by_id(self, offer_id: UUID, tenant_id: UUID) -> Offer | None:
        stmt = select(ProductModel).where(
            ProductModel.id == offer_id,
            ProductModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model:
            return self._to_domain(model)
        return None

    def get_all_by_tenant(self, tenant_id: UUID) -> list[Offer]:
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == tenant_id,
            ProductModel.status != "archived",
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def create(self, offer: Offer) -> Offer:
        model = self._to_model(offer)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(self, offer: Offer, tenant_id: UUID) -> Offer:
        stmt = select(ProductModel).where(
            ProductModel.id == offer.id,
            ProductModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            raise ValueError("Offer not found")

        new_model_data = self._to_model(offer)
        ignored_keys = {
            "_sa_instance_state",
            "created_at",
            "updated_at",
            "id",
            "tenant_id",
        }
        for key, value in new_model_data.__dict__.items():
            if key in ignored_keys:
                continue
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
