"""Offer Ladder Hints API — exposes per-business-type ladder adaptations.

Public, tenant-agnostic, cacheable. Mirrors the versioning pattern used by
``/offer/archetypes/catalog``, ``/offer/value-levels/catalog``, etc.

The response returns all 45 ``(ExpertBusinessType, OfferValueLevel)``
hints flat. Clients (the Offer Studio wizard + dashboard) filter client-
side by the tenant's primary business type. One-call fetch keeps the
cache simple and lets React Query de-duplicate across components.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.offer_ladder_hints import (
    OFFER_LADDER_HINTS,
    LadderHint,
)

router = APIRouter()


class LadderHintDTO(BaseModel):
    """DTO mirror of :class:`LadderHint`."""

    model_config = ConfigDict(frozen=True)

    business_type: str
    value_level: str
    examples_es: list[str]
    typical_offer_type_es: str
    typical_price_min_usd: float | None
    typical_price_max_usd: float | None

    @classmethod
    def from_domain(cls, hint: LadderHint) -> LadderHintDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            business_type=hint.business_type.value,
            value_level=hint.value_level.value,
            examples_es=list(hint.examples_es),
            typical_offer_type_es=hint.typical_offer_type_es,
            typical_price_min_usd=hint.typical_price_min_usd,
            typical_price_max_usd=hint.typical_price_max_usd,
        )


class OfferLadderHintsCatalogResponse(BaseModel):
    """Versioned wrapper so clients can cache the full hint matrix."""

    model_config = ConfigDict(frozen=True)

    version: str
    hints: list[LadderHintDTO]


# Bump this when ``offer_ladder_hints.py`` changes materially (new entry,
# renamed example, price update). Frontend caches by this version.
_CATALOG_VERSION = "2026-04-18"


@router.get(
    "/catalog",
    response_model=OfferLadderHintsCatalogResponse,
    summary="Offer ladder hints catalog (public, cacheable)",
)
async def get_offer_ladder_hints_catalog() -> OfferLadderHintsCatalogResponse:
    """Return every ``(business_type, value_level)`` hint as a flat list.

    Public endpoint — the catalog is domain metadata, identical for all
    tenants. Consumers key their cache by the returned ``version``.
    """
    return OfferLadderHintsCatalogResponse(
        version=_CATALOG_VERSION,
        hints=[LadderHintDTO.from_domain(hint) for hint in OFFER_LADDER_HINTS.values()],
    )
