"""BuyerPersona REST API endpoints."""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from luana_core_brand_studio.api.dto.buyer_personas import (
    BuyerPersonaCreateDTO,
    BuyerPersonaResponseDTO,
    BuyerPersonaSectionUpdateDTO,
)
from luana_core_brand_studio.domain.buyer_persona import BuyerPersona
from luana_core_brand_studio.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# Fields that count toward completeness (profile-only, not metadata).
_PROFILE_FIELDS = (
    "demographics",
    "psychographics",
    "pain_points",
    "desires",
    "buyer_journey",
    "purchase_triggers",
    "anti_patterns",
)


def _calc_completeness(persona: BuyerPersona) -> float:
    """Return 0.0-100.0 based on how many profile fields are non-empty."""
    filled = 0
    for field in _PROFILE_FIELDS:
        value = getattr(persona, field, None)
        if isinstance(value, (dict, list)) and value:
            filled += 1
    return round((filled / len(_PROFILE_FIELDS)) * 100, 1)


@router.get("", response_model=list[BuyerPersonaResponseDTO])
@router.get("/", response_model=list[BuyerPersonaResponseDTO], include_in_schema=False)
async def list_buyer_personas(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    scope: Literal["GLOBAL", "OFFER", "CAMPAIGN"] | None = None,
) -> list[BuyerPersona]:
    """List buyer personas for the tenant."""
    repo = BuyerPersonaRepository(db)
    return repo.list_by_tenant(user.tenant_id, scope=scope)


@router.post("", response_model=BuyerPersonaResponseDTO)
@router.post("/", response_model=BuyerPersonaResponseDTO, include_in_schema=False)
async def create_buyer_persona(
    dto: BuyerPersonaCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Create a new buyer persona (shell)."""
    repo = BuyerPersonaRepository(db)
    persona = BuyerPersona(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=dto.name,
        tagline=dto.tagline,
        scope=dto.scope,
        offer_id=dto.offer_id,
    )
    return repo.create(persona)


@router.get("/{persona_id}", response_model=BuyerPersonaResponseDTO)
async def get_buyer_persona(
    persona_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Get a single buyer persona by id."""
    repo = BuyerPersonaRepository(db)
    persona = repo.get_by_id(user.tenant_id, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Buyer persona not found")
    return persona


@router.patch("/{persona_id}", response_model=BuyerPersonaResponseDTO)
async def update_buyer_persona(
    persona_id: uuid.UUID,
    dto: BuyerPersonaSectionUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Partial update — only sent fields are written."""
    repo = BuyerPersonaRepository(db)

    existing = repo.get_by_id(user.tenant_id, persona_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Buyer persona not found")

    updates = dto.model_dump(exclude_unset=True)
    # Compute completeness from merged state so a single UPDATE covers everything.
    merged = existing.model_copy(update=updates)
    updates["completeness_score"] = _calc_completeness(merged)

    return repo.update(user.tenant_id, persona_id, updates)


@router.delete("/{persona_id}", status_code=204)
async def delete_buyer_persona(
    persona_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete a buyer persona."""
    repo = BuyerPersonaRepository(db)
    existing = repo.get_by_id(user.tenant_id, persona_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Buyer persona not found")
    repo.soft_delete(user.tenant_id, persona_id)
