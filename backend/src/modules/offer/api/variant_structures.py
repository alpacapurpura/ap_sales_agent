"""Variant-structures API — exposes the sixth SSoT axis to clients.

The catalog is pure domain metadata (not tenant-scoped) and highly
cacheable. The frontend consumes it to render the future "¿cómo varía tu
oferta?" wizard step (Sprint 8+), the per-offer variant rail, and
structure-aware validation.

Mirrors the contract of ``/offer/archetypes/catalog`` and
``/offer/value-levels/catalog``: versioned response wrapper so clients
cache by string key.

See ``docs/domains/offer/variant-structure-catalog.md`` for the design
rationale and DAG position.
"""

from __future__ import annotations

from fastapi import APIRouter
from luana_core_offer_studio.domain.variant_structure_catalog import (
    VARIANT_STRUCTURE_CATALOG,
    VariantStructureMetadata,
)
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class VariantStructureMetadataDTO(BaseModel):
    """DTO mirror of :class:`VariantStructureMetadata`.

    Declared explicitly (not derived) because the domain dataclass uses
    ``slots`` and is pydantic-unaware. Preserves the DDD boundary between
    the domain catalog and the API surface.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    order: int
    label_es: str
    description_es: str
    noun_es: str
    noun_plural_es: str
    icon_name: str
    requires_temporal_anchor: bool
    requires_location: bool
    supports_capacity: bool
    supports_pricing_tiers: bool
    supports_sort_rank: bool
    clone_policy: str
    cardinality: str
    required_structure_data_fields: list[str]
    forbidden_base_fields: list[str]
    wizard_prompt_es: str | None

    @classmethod
    def from_domain(cls, metadata: VariantStructureMetadata) -> VariantStructureMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            key=metadata.key.value,
            order=metadata.order,
            label_es=metadata.label_es,
            description_es=metadata.description_es,
            noun_es=metadata.noun_es,
            noun_plural_es=metadata.noun_plural_es,
            icon_name=metadata.icon_name,
            requires_temporal_anchor=metadata.requires_temporal_anchor,
            requires_location=metadata.requires_location,
            supports_capacity=metadata.supports_capacity,
            supports_pricing_tiers=metadata.supports_pricing_tiers,
            supports_sort_rank=metadata.supports_sort_rank,
            clone_policy=metadata.clone_policy.value,
            cardinality=metadata.cardinality.value,
            required_structure_data_fields=list(metadata.required_structure_data_fields),
            forbidden_base_fields=list(metadata.forbidden_base_fields),
            wizard_prompt_es=metadata.wizard_prompt_es,
        )


class VariantStructuresCatalogResponse(BaseModel):
    """Versioned wrapper so clients cache the whole catalog by version."""

    model_config = ConfigDict(frozen=True)

    version: str
    variant_structures: list[VariantStructureMetadataDTO]


# Bump this when ``variant_structure_catalog.py`` changes materially.
# Clients use it as the cache key so old copies are evicted on deploy.
_CATALOG_VERSION = "2026-04-20-variant-structures-v4"


@router.get(
    "/catalog",
    response_model=VariantStructuresCatalogResponse,
    summary="Offer variant-structure catalog (public, cacheable)",
)
async def get_variant_structures_catalog() -> VariantStructuresCatalogResponse:
    """Return metadata for every variant structure, sorted by declared order.

    Not tenant-scoped — this is domain metadata shared across tenants.
    """
    sorted_entries = sorted(VARIANT_STRUCTURE_CATALOG.values(), key=lambda m: m.order)
    return VariantStructuresCatalogResponse(
        version=_CATALOG_VERSION,
        variant_structures=[VariantStructureMetadataDTO.from_domain(m) for m in sorted_entries],
    )
