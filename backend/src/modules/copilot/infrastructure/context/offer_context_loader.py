"""Context loader that provides the tenant's Offer Ladder for interview context."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from src.modules.offer.infrastructure.models.product_model import ProductModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

VALUE_LEVEL_ORDER = [
    "LEAD_MAGNET",
    "ACTIVACION",
    "TRANSFORMACION",
    "MAXIMIZACION",
    "CORPORATIVO",
]


class OfferContextLoader:
    """Loads other offers from the tenant for interview context.

    Used by the Offer Interview to show existing ladder positioning
    so the agent can advise on pricing, gaps, and differentiation.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def load(self, tenant_id: UUID, entity_id: UUID | None = None) -> str:
        """Load all offers for tenant, build ladder context string.

        Args:
            tenant_id: Tenant to load offers for.
            entity_id: If given, exclude this offer (the one being interviewed).

        Returns:
            Human-readable string describing the tenant's offer ladder.

        """
        stmt = select(ProductModel).where(ProductModel.tenant_id == tenant_id).where(ProductModel.deleted_at.is_(None))
        if entity_id:
            stmt = stmt.where(ProductModel.id != entity_id)

        result = await self.db.execute(stmt)
        offers = result.scalars().all()

        if not offers:
            return "No hay otros offers en el negocio. Este es el primero."

        def _sort_key(o: ProductModel) -> int:
            vl = getattr(o, "value_level", None)
            if vl in VALUE_LEVEL_ORDER:
                return VALUE_LEVEL_ORDER.index(vl)
            return 99

        lines = ["Otros offers del negocio:"]
        for offer in sorted(offers, key=_sort_key):
            price_display = "sin precio"
            pricing = getattr(offer, "pricing", None)
            if pricing and isinstance(pricing, list) and len(pricing) > 0:
                pay_full = pricing[0].get("pay_in_full") if isinstance(pricing[0], dict) else None
                if pay_full is not None:
                    price_display = str(pay_full)

            currency = getattr(offer, "currency", None) or ""
            archetype = getattr(offer, "archetype", "")
            value_level = getattr(offer, "value_level", "")
            status = getattr(offer, "status", "draft")

            lines.append(
                f"- {offer.name} ({archetype}, {value_level}): {currency} {price_display} — {status}",
            )

        # Identify ladder gaps
        existing_levels = {getattr(o, "value_level", None) for o in offers}
        gaps = [level for level in VALUE_LEVEL_ORDER if level not in existing_levels]
        if gaps:
            lines.append(f"\nGaps en el ladder: {', '.join(gaps)}")

        logger.info(
            "offer_context_loaded",
            tenant_id=str(tenant_id),
            offer_count=len(offers),
            gaps=gaps,
        )
        return "\n".join(lines)
