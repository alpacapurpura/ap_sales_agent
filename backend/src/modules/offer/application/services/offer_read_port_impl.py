"""OfferReadPort implementation -- lives in offer module.

Same pattern as ConnectionPortImpl in connections module:
ABC defined in analytics.domain.ports, implementation here queries
ProductModel directly without crossing DDD boundaries.
"""

import asyncio
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.analytics.domain.ports import OfferReadDTO, OfferReadPort
from src.modules.offer.infrastructure.models.product_model import ProductModel


class OfferReadPortImpl(OfferReadPort):
    """Adapter implementing OfferReadPort for the offer bounded context."""

    def __init__(self, db: Session):
        self.db = db

    async def get_offers_by_tenant(
        self, tenant_id: UUID
    ) -> List[OfferReadDTO]:
        """All active offers for a tenant (excludes archived)."""
        stmt = select(ProductModel).where(
            ProductModel.tenant_id == tenant_id,
            ProductModel.status != "archived",
        )
        result = await asyncio.to_thread(self.db.execute, stmt)
        models = result.scalars().all()
        return [self._to_dto(m) for m in models]

    async def get_offer_by_id(
        self, offer_id: UUID
    ) -> Optional[OfferReadDTO]:
        """Single offer by ID."""
        stmt = select(ProductModel).where(ProductModel.id == offer_id)
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
        return OfferReadDTO(
            id=m.id,
            tenant_id=m.tenant_id,
            public_name=m.name,
            offer_type=m.type,
            value_level=m.value_level,
            pricing_type=pricing_type,
            currency=m.currency or "USD",
        )
