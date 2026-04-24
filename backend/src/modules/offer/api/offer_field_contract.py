"""Field contract API — versioned structural contract for offer-studio.

Exposes ``FIELD_CONTRACT_SNAPSHOT`` from
``src.modules.offer.domain.field_contract`` over HTTP so FE can consume
the canonical paths + ownership. Fase 01 pilot — pricing section only.

Domain metadata; not tenant-scoped. Public + cacheable like the other
catalog endpoints (archetypes/variant-structures/type-presets).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.field_contract import (
    FIELD_CONTRACT_SNAPSHOT,
    FieldContract,
)

router = APIRouter()


class FieldContractDTO(BaseModel):
    """DTO mirror of :class:`FieldContract`.

    Declared explicitly — the domain dataclass uses ``slots`` and is
    pydantic-unaware. Preserves the DDD boundary.
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
            type=fc.type,
            owner=fc.owner.value,
            section=fc.section,
            required=fc.required,
            archetype_filter=([a.value for a in fc.archetype_filter] if fc.archetype_filter else None),
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

    Fase 01 ships only pricing contracts. Phases 02→04 grow the registry
    until it supersedes ``OFFER_FIELDS_BY_FE_SECTION`` entirely.
    """
    snap = FIELD_CONTRACT_SNAPSHOT
    return FieldContractResponse(
        version=snap.version,
        contracts=[FieldContractDTO.from_domain(fc) for fc in snap.contracts],
    )
