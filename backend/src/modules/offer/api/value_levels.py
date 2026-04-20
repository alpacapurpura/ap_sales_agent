"""Value-levels API — exposes the OfferValueLevel catalog.

Public, tenant-agnostic, highly cacheable. Mirrors
``/offer/archetypes/catalog``: the response carries a ``version`` string
that clients use as cache key.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.value_level_catalog import (
    VALUE_LEVEL_CATALOG,
    ValueLevelMetadata,
)

router = APIRouter()


class ValueLevelMetadataDTO(BaseModel):
    """DTO mirror of :class:`ValueLevelMetadata`."""

    model_config = ConfigDict(frozen=True)

    value_level: str
    order: int
    label_es: str
    description_es: str
    role_in_funnel_es: str
    icon_name: str
    examples_es: list[str]
    is_free: bool
    typical_price_min_usd: float | None
    typical_price_max_usd: float | None

    @classmethod
    def from_domain(cls, metadata: ValueLevelMetadata) -> ValueLevelMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            value_level=metadata.value_level.value,
            order=metadata.order,
            label_es=metadata.label_es,
            description_es=metadata.description_es,
            role_in_funnel_es=metadata.role_in_funnel_es,
            icon_name=metadata.icon_name,
            examples_es=list(metadata.examples_es),
            is_free=metadata.is_free,
            typical_price_min_usd=metadata.typical_price_min_usd,
            typical_price_max_usd=metadata.typical_price_max_usd,
        )


class ValueLevelsCatalogResponse(BaseModel):
    """Versioned wrapper so clients can cache the full ladder."""

    model_config = ConfigDict(frozen=True)

    version: str
    value_levels: list[ValueLevelMetadataDTO]


# Bump this when ``value_level_catalog.py`` changes materially.
_CATALOG_VERSION = "2026-04-18"


@router.get(
    "/catalog",
    response_model=ValueLevelsCatalogResponse,
    summary="Offer value-level catalog (public, cacheable)",
)
async def get_value_levels_catalog() -> ValueLevelsCatalogResponse:
    """Return metadata for every value-ladder rung, sorted by funnel order."""
    sorted_entries = sorted(VALUE_LEVEL_CATALOG.values(), key=lambda m: m.order)
    return ValueLevelsCatalogResponse(
        version=_CATALOG_VERSION,
        value_levels=[ValueLevelMetadataDTO.from_domain(m) for m in sorted_entries],
    )
