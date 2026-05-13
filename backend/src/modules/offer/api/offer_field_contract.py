"""Field contract API — versioned structural contract for offer-studio.

Exposes :data:`FIELD_CONTRACT_SNAPSHOT` over HTTP so FE can consume
the canonical paths + ownership. Post-Fase 04 the underlying registry
is derived from ``src.shared.domain.field_contract`` — same HTTP shape.

Domain metadata; not tenant-scoped. Public + cacheable like the other
catalog endpoints (archetypes/variant-structures/type-presets).
"""

from __future__ import annotations

from fastapi import APIRouter
from luana_core_offer_studio.domain.field_contract import (
    FIELD_CONTRACT_SNAPSHOT,
)
from luana_core_platform.domain.field_contract import FieldContract
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class FieldContractDTO(BaseModel):
    """DTO mirror of :class:`FieldContract`.

    Preserves the HTTP shape stable across platform refactor. The
    shared ``FieldContract`` has more metadata (copilot, lifecycle) —
    this DTO exposes the subset FE already relied on. Extra fields
    can be added in future iterations without breaking consumers.
    """

    model_config = ConfigDict(frozen=True)

    path: str
    type: str
    owner: str
    section: str
    required: bool
    archetype_filter: list[str] | None = None
    notes: str | None = None

    @classmethod
    def from_domain(cls, fc: FieldContract) -> FieldContractDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            path=fc.path,
            type=fc.type.value,
            owner=fc.owner_module,
            section=fc.section,
            required=fc.is_required_structural,
            archetype_filter=list(fc.archetype_filter) if fc.archetype_filter else None,
            notes=fc.notes,
        )


class FieldContractResponse(BaseModel):
    """Versioned payload so clients can cache by version string."""

    model_config = ConfigDict(frozen=True)

    version: str
    contracts: list[FieldContractDTO]


@router.get(
    "",
    response_model=FieldContractResponse,
    summary="Offer field contract registry (public, cacheable, versioned)",
)
async def get_offer_field_contract() -> FieldContractResponse:
    """Return the full FieldContract registry.

    Post-Fase 04 includes every Offer user-facing path (derived from
    Pydantic). Legacy pricing + value-stack + authority fields remain
    available; new lifecycle / copilot metadata is additive.
    """
    snap = FIELD_CONTRACT_SNAPSHOT
    return FieldContractResponse(
        version=snap.version,
        contracts=[FieldContractDTO.from_domain(fc) for fc in snap.contracts],
    )
