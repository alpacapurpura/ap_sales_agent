"""Offer repository."""

from typing import Any
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
from src.shared.domain.datetime_utils import utc_now


class OfferRepository:
    """Repository for offer persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
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
            "preset_id": model.preset_id,
            "is_lead_magnet": model.is_lead_magnet or False,
            "has_editions": bool(model.has_editions) if model.has_editions is not None else None,
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
                model.min_financial_capacity,
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
            # --- Narrative: promise ---
            "before_state": model.before_state,
            "after_state": model.after_state,
            "why_now": model.why_now,
            "measurable_outcomes": model.measurable_outcomes or [],
            # --- Narrative: psychology ---
            "cultural_trust_barriers": model.cultural_trust_barriers or [],
            "emotional_triggers": model.emotional_triggers or [],
            "status_drivers": model.status_drivers or [],
            "regret_scenarios": model.regret_scenarios or [],
            # --- Narrative: closing ---
            "refund_process_description": model.refund_process_description,
            "urgency_drivers": model.urgency_drivers or [],
            "scarcity_reason_honest": model.scarcity_reason_honest,
            "bonus_if_act_now": model.bonus_if_act_now,
            "final_push_copy": model.final_push_copy,
            "metadata_info": model.metadata_info or {},
            "price_pay_in_full": None,
            # Pass-through: nulls stay null. Callers/UI resolve via TenantLocale.
            "currency": model.currency,
            "pricing_options": normalize_pricing_options(model.pricing or []),
            # Pricing LATAM (Fase 01)
            "tax_included": model.tax_included,
            "installments_available": model.installments_available,
            "accepted_payment_providers": list(model.accepted_payment_providers or []),
            "deliverables": normalize_deliverables(model.deliverables or []),
            "archived_at": model.archived_at,
            "deleted_at": model.deleted_at,
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
                    msg = f"Error parsing specific_details for offer {model.id}: {e!s}"
                    raise ValueError(msg) from e

        return Offer(**offer_data)

    def _to_model(self, offer: Offer) -> ProductModel:
        pricing_data = [p.model_dump(mode="json") for p in offer.pricing_options]
        deliverables_data = [d.model_dump(mode="json") for d in offer.deliverables]
        details_data = offer.specific_details.model_dump(mode="json") if offer.specific_details else {}
        # landing_page_config is typed as dict in the domain. Legacy callers
        # may still hand a Pydantic model — handle both for safety.
        raw_landing = offer.landing_page_config
        if raw_landing is None:
            landing_config_data: dict[str, Any] = {}
        elif hasattr(raw_landing, "model_dump"):
            landing_config_data = raw_landing.model_dump(mode="json")
        else:
            landing_config_data = dict(raw_landing)

        return ProductModel(
            id=offer.id,
            tenant_id=offer.tenant_id,
            name=offer.public_name,
            archetype=offer.archetype.value,
            format_hint=offer.format_hint,
            preset_id=offer.preset_id,
            is_lead_magnet=offer.is_lead_magnet,
            has_editions=bool(offer.has_editions),
            status=offer.status.value,
            internal_sku=offer.internal_sku,
            pricing=pricing_data,
            currency=offer.currency,
            tax_included=offer.tax_included,
            installments_available=offer.installments_available,
            accepted_payment_providers=list(offer.accepted_payment_providers or []),
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
            before_state=offer.before_state,
            after_state=offer.after_state,
            why_now=offer.why_now,
            measurable_outcomes=list(offer.measurable_outcomes or []),
            cultural_trust_barriers=list(offer.cultural_trust_barriers or []),
            emotional_triggers=list(offer.emotional_triggers or []),
            status_drivers=list(offer.status_drivers or []),
            regret_scenarios=list(offer.regret_scenarios or []),
            refund_process_description=offer.refund_process_description,
            urgency_drivers=list(offer.urgency_drivers or []),
            scarcity_reason_honest=offer.scarcity_reason_honest,
            bonus_if_act_now=offer.bonus_if_act_now,
            final_push_copy=offer.final_push_copy,
            metadata_info=offer.metadata_info,
        )

    def get_by_id(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> Offer | None:
        """Fetch an offer by id within tenant scope.

        By default hides archived and soft-deleted rows. Pass
        ``include_archived=True`` to access the /archived view flow and
        ``include_deleted=True`` to see soft-deleted rows (admin only).
        """
        conditions = [
            ProductModel.id == offer_id,
            ProductModel.tenant_id == tenant_id,
        ]
        if not include_archived:
            conditions.append(ProductModel.archived_at.is_(None))
        if not include_deleted:
            conditions.append(ProductModel.deleted_at.is_(None))

        stmt = select(ProductModel).where(*conditions)
        model = self.db.execute(stmt).scalar_one_or_none()
        if model:
            return self._to_domain(model)
        return None

    def list_active(self, tenant_id: UUID) -> list[Offer]:
        """Return offers that are neither archived nor soft-deleted."""
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == tenant_id,
            ProductModel.archived_at.is_(None),
            ProductModel.deleted_at.is_(None),
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_archived(self, tenant_id: UUID) -> list[Offer]:
        """Return offers archived but not soft-deleted, newest first."""
        stmt = (
            select(ProductModel)
            .where(
                ProductModel.tenant_id == tenant_id,
                ProductModel.archived_at.is_not(None),
                ProductModel.deleted_at.is_(None),
            )
            .order_by(ProductModel.archived_at.desc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def get_all_by_tenant(self, tenant_id: UUID) -> list[Offer]:
        """Backward-compat wrapper — returns only active offers.

        Kept so legacy callers do not break. Prefer ``list_active`` in new code.
        """
        return self.list_active(tenant_id)

    def archive(self, offer_id: UUID, tenant_id: UUID) -> Offer | None:
        """Set ``archived_at`` if not already set. Idempotent."""
        stmt = select(ProductModel).where(
            ProductModel.id == offer_id,
            ProductModel.tenant_id == tenant_id,
            ProductModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        if model.archived_at is None:
            model.archived_at = utc_now()
            self.db.commit()
            self.db.refresh(model)
        return self._to_domain(model)

    def restore(self, offer_id: UUID, tenant_id: UUID) -> Offer | None:
        """Clear ``archived_at``. No-op if already active."""
        stmt = select(ProductModel).where(
            ProductModel.id == offer_id,
            ProductModel.tenant_id == tenant_id,
            ProductModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        if model.archived_at is not None:
            model.archived_at = None
            self.db.commit()
            self.db.refresh(model)
        return self._to_domain(model)

    def soft_delete(self, offer_id: UUID, tenant_id: UUID) -> bool:
        """Mark the offer as soft-deleted. Returns True on success."""
        stmt = select(ProductModel).where(
            ProductModel.id == offer_id,
            ProductModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            return False
        if model.deleted_at is None:
            model.deleted_at = utc_now()
            self.db.commit()
        return True

    def create(self, offer: Offer) -> Offer:
        """Create."""
        model = self._to_model(offer)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(self, offer: Offer, tenant_id: UUID) -> Offer:
        """Update."""
        stmt = select(ProductModel).where(
            ProductModel.id == offer.id,
            ProductModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            msg = "Offer not found"
            raise ValueError(msg)

        new_model_data = self._to_model(offer)

        ignored_keys = {
            "_sa_instance_state",
            "created_at",
            "updated_at",
            "id",
            "tenant_id",
            # Lifecycle columns are managed exclusively by archive/restore/
            # soft_delete methods — generic update() must never touch them.
            "archived_at",
            "deleted_at",
        }

        for key, value in new_model_data.__dict__.items():
            if key in ignored_keys:
                continue
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
