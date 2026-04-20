"""Formats API — exposes FORMAT_CATALOG with optional filtering.

Public, tenant-agnostic, versioned. Supports two optional query params:

- ``archetype`` narrows to one ``OfferArchetype``.
- ``business_types`` is a comma-separated list of ``ExpertBusinessType``
  values. When present, formats are filtered to those with a positive
  suitability score for at least one of the listed types, and sorted by
  the best-matching score descending (the wizard uses this to prioritize
  cards for the tenant's profile).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.enums import OfferArchetype  # noqa: TC001  — FastAPI runtime use
from src.modules.offer.domain.format_catalog import get_formats_suitable_for
from src.shared.domain.expert_business_type import ExpertBusinessType

if TYPE_CHECKING:
    from src.modules.offer.domain.format_catalog import FormatMetadata

router = APIRouter()


class FormatMetadataDTO(BaseModel):
    """DTO mirror of :class:`FormatMetadata`."""

    model_config = ConfigDict(frozen=True)

    format_id: str
    archetype: str
    label_es: str
    description_es: str
    icon_name: str
    format_hint: str
    delivery_model: str
    suitable_for: dict[str, float]
    tags: list[str]
    specific_details_defaults: dict[str, object]

    @classmethod
    def from_domain(cls, metadata: FormatMetadata) -> FormatMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            format_id=metadata.format_id,
            archetype=metadata.archetype.value,
            label_es=metadata.label_es,
            description_es=metadata.description_es,
            icon_name=metadata.icon_name,
            format_hint=metadata.format_hint,
            delivery_model=metadata.delivery_model.value,
            suitable_for={bt.value: score for bt, score in metadata.suitable_for.items()},
            tags=list(metadata.tags),
            specific_details_defaults=dict(metadata.specific_details_defaults),
        )


class FormatsCatalogResponse(BaseModel):
    """Versioned wrapper. Clients cache by the ``version`` string."""

    model_config = ConfigDict(frozen=True)

    version: str
    formats: list[FormatMetadataDTO]


# Bump this when ``format_catalog.py`` changes materially.
_CATALOG_VERSION = "2026-04-17"


def _parse_business_types(raw: str | None) -> list[ExpertBusinessType]:
    if raw is None or not raw.strip():
        return []
    parsed: list[ExpertBusinessType] = []
    valid = {bt.value for bt in ExpertBusinessType}
    for piece in raw.split(","):
        token = piece.strip()
        if not token:
            continue
        if token not in valid:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown ExpertBusinessType: {token!r}",
            )
        parsed.append(ExpertBusinessType(token))
    return parsed


@router.get(
    "/catalog",
    response_model=FormatsCatalogResponse,
    summary="Offer format catalog (public, cacheable, filterable)",
)
async def get_formats_catalog(
    archetype: Annotated[OfferArchetype | None, Query()] = None,
    business_types: Annotated[
        str | None,
        Query(description="Comma-separated ExpertBusinessType values"),
    ] = None,
) -> FormatsCatalogResponse:
    """Return format metadata, optionally filtered by archetype + business types."""
    parsed_types = _parse_business_types(business_types)
    results = get_formats_suitable_for(
        business_types=parsed_types,
        archetype=archetype,
    )
    return FormatsCatalogResponse(
        version=_CATALOG_VERSION,
        formats=[FormatMetadataDTO.from_domain(m) for m in results],
    )
