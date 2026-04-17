"""ExpertBusinessTypes API — exposes the ExpertBusinessType catalog.

The catalog is cross-module domain metadata (see
``shared/domain/expert_business_type.py``). Brand Studio owns the field
on ``BrandIdentity`` that references it, so the endpoint lives here —
but the content is safe to consume from any frontend surface.

Not tenant-scoped. Public. Highly cacheable: clients key their cache by
``version`` and evict on bump.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.shared.domain.expert_business_type import (
    EXPERT_BUSINESS_TYPE_CATALOG,
    ExpertBusinessTypeMetadata,
)

router = APIRouter()


class ExpertBusinessTypeMetadataDTO(BaseModel):
    """DTO mirror of :class:`ExpertBusinessTypeMetadata`.

    Declared explicitly (not derived) because the domain dataclass uses
    ``slots`` and is pydantic-unaware — keeping a dedicated DTO preserves
    the DDD boundary between domain and API.
    """

    model_config = ConfigDict(frozen=True)

    business_type: str
    label_es: str
    description_es: str
    sells_es: str
    icon_name: str
    examples_es: list[str]

    @classmethod
    def from_domain(cls, metadata: ExpertBusinessTypeMetadata) -> ExpertBusinessTypeMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            business_type=metadata.business_type.value,
            label_es=metadata.label_es,
            description_es=metadata.description_es,
            sells_es=metadata.sells_es,
            icon_name=metadata.icon_name,
            examples_es=list(metadata.examples_es),
        )


class ExpertBusinessTypesCatalogResponse(BaseModel):
    """Versioned wrapper so clients can cache the full catalog."""

    model_config = ConfigDict(frozen=True)

    version: str
    business_types: list[ExpertBusinessTypeMetadataDTO]


# Bump this when ``expert_business_type.py`` changes materially (new type,
# renamed label, description rewrite). Frontend caches by this version.
_CATALOG_VERSION = "2026-04-17"


@router.get(
    "/catalog",
    response_model=ExpertBusinessTypesCatalogResponse,
    summary="Expert business type catalog (public, cacheable)",
)
async def get_expert_business_types_catalog() -> ExpertBusinessTypesCatalogResponse:
    """Return metadata for every ``ExpertBusinessType``.

    Public endpoint — the catalog is domain metadata, identical for all
    tenants. Consumers key their cache by the returned ``version``.
    """
    return ExpertBusinessTypesCatalogResponse(
        version=_CATALOG_VERSION,
        business_types=[ExpertBusinessTypeMetadataDTO.from_domain(m) for m in EXPERT_BUSINESS_TYPE_CATALOG.values()],
    )
