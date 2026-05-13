"""Brand Studio sections API — exposes the section catalog to clients.

Mirror of ``backend/src/modules/offer/api/archetypes.py`` at a smaller
scale: just the section list (no archetype capabilities). Public,
cacheable, not tenant-scoped.

refs: docs/refactors/field-contract-ssot/phases/03-section-catalog-dedup/SPEC.md §C
"""

from __future__ import annotations

from fastapi import APIRouter
from luana_core_brand_studio.domain.section_catalog import (
    BRAND_SECTION_CATALOG,
    BrandSectionMetadata,
)
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class BrandSectionMetadataDTO(BaseModel):
    """DTO mirror of :class:`BrandSectionMetadata`.

    Preserves the DDD boundary between the domain dataclass and the API
    layer (domain uses ``slots`` and is pydantic-unaware).
    """

    model_config = ConfigDict(frozen=True)

    key: str
    label_es: str
    icon_name: str
    kind: str  # singleton | collection

    @classmethod
    def from_domain(cls, meta: BrandSectionMetadata) -> BrandSectionMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            key=meta.key.value,
            label_es=meta.label_es,
            icon_name=meta.icon_name,
            kind=meta.kind.value,
        )


class BrandSectionCatalogResponse(BaseModel):
    """Wrapper so clients cache by version string."""

    model_config = ConfigDict(frozen=True)

    version: str
    sections: list[BrandSectionMetadataDTO]


# Bump when ``section_catalog.py`` changes materially.
_CATALOG_VERSION = "2026-04-24-fase-03-initial"


@router.get(
    "/catalog",
    response_model=BrandSectionCatalogResponse,
    summary="Brand Studio section catalog (public, cacheable)",
)
async def get_brand_section_catalog() -> BrandSectionCatalogResponse:
    """Return the 14 brand-studio sections ordered by catalog insertion.

    Not tenant-scoped — this is domain metadata shared across tenants.
    """
    return BrandSectionCatalogResponse(
        version=_CATALOG_VERSION,
        sections=[BrandSectionMetadataDTO.from_domain(m) for m in BRAND_SECTION_CATALOG.values()],
    )
