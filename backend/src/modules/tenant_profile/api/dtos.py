"""Pydantic v2 DTOs for the tenant_profile API.

Naming follows the contract (§3.2):
- ``TenantProfileResponse``      — GET and PATCH response.
- ``UpdateTenantProfileRequest`` — PATCH request body.
- ``BusinessTypeMetadataDTO``    — single entry in the catalog response.
- ``BusinessTypesCatalogResponse`` — GET catalog response.

``ExpertBusinessTypeSlug`` is an alias for ``str`` with a semantic name so
the OpenAPI schema documents the intent without coupling the DTO to the enum.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from luana_core_platform.domain.expert_business_type import (
    EXPERT_BUSINESS_TYPE_CATALOG,
    ExpertBusinessType,
)
from luana_core_tenant_profile.domain.tenant_profile import (
    BUSINESS_TYPES_MAX,
    BUSINESS_TYPES_MIN,
)
from pydantic import BaseModel, ConfigDict, Field

# Type alias — slug strings that correspond to ExpertBusinessType values.
ExpertBusinessTypeSlug = str


class TenantProfileResponse(BaseModel):
    """Full profile response returned by GET and PATCH /api/v1/tenant/profile."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    business_types: list[ExpertBusinessTypeSlug]
    declared_at: datetime | None
    updated_at: datetime
    is_complete: bool
    can_change_now: bool
    next_allowed_change_at: datetime | None


class UpdateTenantProfileRequest(BaseModel):
    """Request body for PATCH /api/v1/tenant/profile."""

    business_types: list[ExpertBusinessTypeSlug] = Field(
        min_length=BUSINESS_TYPES_MIN,
        max_length=BUSINESS_TYPES_MAX,
        description=(
            "List of ExpertBusinessType slugs to declare for this tenant. "
            f"Must have between {BUSINESS_TYPES_MIN} and {BUSINESS_TYPES_MAX} entries, "
            "no duplicates."
        ),
    )


class BusinessTypeMetadataDTO(BaseModel):
    """Metadata for a single ExpertBusinessType — mirrors ExpertBusinessTypeMetadata."""

    model_config = ConfigDict(frozen=True)

    slug: ExpertBusinessTypeSlug
    label_es: str
    description_es: str
    icon_name: str
    examples_es: list[str]


class BusinessTypesCatalogResponse(BaseModel):
    """Versioned catalog response for GET /api/v1/catalogs/business-types."""

    model_config = ConfigDict(frozen=True)

    version: str
    business_types: list[BusinessTypeMetadataDTO]


def _build_catalog_response(version: str) -> BusinessTypesCatalogResponse:
    """Build the full catalog response from the shared domain catalog."""
    entries = [
        BusinessTypeMetadataDTO(
            slug=meta.business_type.value,
            label_es=meta.label_es,
            description_es=meta.description_es,
            icon_name=meta.icon_name,
            examples_es=list(meta.examples_es),
        )
        for meta in EXPERT_BUSINESS_TYPE_CATALOG.values()
    ]
    return BusinessTypesCatalogResponse(version=version, business_types=entries)


def profile_to_response(profile: object) -> TenantProfileResponse:
    """Convert a :class:`TenantProfile` aggregate to the API response DTO.

    Accepts ``object`` to avoid importing the domain type in test stubs, but
    at runtime it must be a ``TenantProfile`` instance.
    """
    from luana_core_tenant_profile.domain.tenant_profile import TenantProfile

    assert isinstance(profile, TenantProfile)  # noqa: S101 — internal assertion
    return TenantProfileResponse(
        tenant_id=profile.tenant_id,
        business_types=[bt.value for bt in profile.business_types],
        declared_at=profile.declared_at,
        updated_at=profile.updated_at,
        is_complete=profile.is_complete,
        can_change_now=profile.can_change_business_types(),
        next_allowed_change_at=profile.next_allowed_change_at(),
    )


def parse_business_types_request(
    slugs: list[str],
) -> tuple[ExpertBusinessType, ...]:
    """Validate and convert slug strings to :class:`ExpertBusinessType` values.

    Raises:
        ValueError: If any slug is not a valid ``ExpertBusinessType`` value.
    """
    valid = {member.value for member in ExpertBusinessType}
    result: list[ExpertBusinessType] = []
    unknown: list[str] = []
    for slug in slugs:
        if slug in valid:
            result.append(ExpertBusinessType(slug))
        else:
            unknown.append(slug)
    if unknown:
        msg = f"Unknown business type slugs: {unknown}. Valid values: {sorted(valid)}"
        raise ValueError(msg)
    return tuple(result)
