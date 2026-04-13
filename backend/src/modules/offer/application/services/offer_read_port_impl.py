"""OfferReadPort implementation -- lives in offer module.

Same pattern as ConnectionPortImpl in connections module:
ABC defined in analytics.domain.ports, implementation here queries
ProductModel directly without crossing DDD boundaries.
"""

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.offer.infrastructure.models.product_model import ProductModel
from src.shared.domain.ports import OfferReadDTO, OfferReadPort


class OfferReadPortImpl(OfferReadPort):
    """Adapter implementing OfferReadPort for the offer bounded context."""

    def __init__(self, db: Session) -> None:
        """Initialize instance."""
        self.db = db

    async def get_offers_by_tenant(self, tenant_id: UUID) -> list[OfferReadDTO]:
        """All active offers for a tenant (excludes archived and soft-deleted).

        Post-migration 040 the archive lifecycle lives on ``archived_at`` /
        ``deleted_at`` — ``status`` is purely operational (draft/active/paused/…)
        and must not be used as an archival marker.
        """
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == tenant_id,
            ProductModel.archived_at.is_(None),
            ProductModel.deleted_at.is_(None),
        )
        result = await asyncio.to_thread(self.db.execute, stmt)
        models = result.scalars().all()
        return [self._to_dto(m) for m in models]

    async def get_offer_by_id(
        self,
        offer_id: UUID,
        tenant_id: UUID | None = None,
    ) -> OfferReadDTO | None:
        """Single offer by ID, scoped to tenant when provided."""
        conditions = [ProductModel.id == offer_id]
        if tenant_id is not None:
            conditions.append(ProductModel.tenant_id == tenant_id)
        stmt = select(ProductModel).where(*conditions)
        result = await asyncio.to_thread(self.db.execute, stmt)
        model = result.scalar_one_or_none()
        return self._to_dto(model) if model else None

    def _to_dto(self, m: ProductModel) -> OfferReadDTO:
        """Map ProductModel to lightweight OfferReadDTO."""
        pricing_type = "one_time"
        if m.pricing:
            for p in m.pricing:
                if isinstance(p, dict) and p.get("plan_type") in (
                    "subscription",
                    "payment_plan",
                ):
                    pricing_type = p["plan_type"]
                    break

        # Extract landing URL from landing_page_config JSONB if present.
        landing_url: str | None = None
        if isinstance(m.landing_page_config, dict):
            raw_url = m.landing_page_config.get("url")
            if isinstance(raw_url, str) and raw_url.strip():
                landing_url = raw_url.strip()

        return OfferReadDTO(
            id=m.id,
            tenant_id=m.tenant_id,
            public_name=m.name,
            offer_type=m.archetype,
            value_level=m.value_level,
            pricing_type=pricing_type,
            currency=m.currency or "USD",
            is_lead_magnet=bool(m.is_lead_magnet),
            onboarding_action=m.onboarding_action,
            checkout_page_url=m.checkout_page_url,
            landing_page_url=landing_url,
            internal_sku=m.internal_sku,
            status=m.status,
        )
