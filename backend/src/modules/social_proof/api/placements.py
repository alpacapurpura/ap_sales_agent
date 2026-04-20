"""REST endpoints for Placement management + for-surface resolver."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.social_proof.application.dto.placement_dto import (
    PlacedAuthorityItemDTO,
    PlacedTeamMemberDTO,
    PlacedTestimonialDTO,
    PlacementCreateDTO,
    PlacementResponseDTO,
    PlacementUpdateDTO,
    ResolvedSocialProofDTO,
)
from src.modules.social_proof.application.services.placement_service import (
    PlacementService,
)
from src.modules.social_proof.application.services.social_proof_resolver import (
    SocialProofResolver,
)
from src.modules.social_proof.domain.enums import SourceTable, SurfaceType
from src.modules.social_proof.domain.placement import Placement

router = APIRouter()


@router.get("", response_model=list[PlacementResponseDTO])
@router.get("/", response_model=list[PlacementResponseDTO], include_in_schema=False)
def list_placements_by_source(
    source_table: Annotated[SourceTable, Query()],
    source_id: Annotated[uuid.UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Placement]:
    """List live placements that point at a specific source row."""
    return PlacementService(db).list_for_source(user.tenant_id, source_table, source_id)


@router.post("", response_model=PlacementResponseDTO)
@router.post("/", response_model=PlacementResponseDTO, include_in_schema=False)
def create_placement(
    dto: PlacementCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Placement:
    """Link an existing source row to a surface."""
    try:
        return PlacementService(db).add(
            tenant_id=user.tenant_id,
            source_table=dto.source_table,
            source_id=dto.source_id,
            surface_type=dto.surface_type,
            surface_ref_id=dto.surface_ref_id,
            sort_order=dto.sort_order,
            is_visible=dto.is_visible,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{placement_id}", response_model=PlacementResponseDTO)
def patch_placement(
    placement_id: uuid.UUID,
    dto: PlacementUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Placement:
    """Reorder or toggle visibility of a placement."""
    updates = dto.model_dump(exclude_unset=True)
    result = PlacementService(db).update(user.tenant_id, placement_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Placement not found")
    return result


@router.delete("/{placement_id}", status_code=204)
def delete_placement(
    placement_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete a placement. Source row stays intact."""
    ok = PlacementService(db).remove(user.tenant_id, placement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Placement not found")


# ────────────────────────────────────────────
# Resolver (read model) — /for-surface
# ────────────────────────────────────────────


@router.get("/for-surface", response_model=ResolvedSocialProofDTO)  # noqa: FAST001
def get_for_surface(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    surface_type: Annotated[SurfaceType, Query()],
    surface_ref_id: Annotated[uuid.UUID | None, Query()] = None,
    include_brand: Annotated[bool, Query()] = False,
) -> ResolvedSocialProofDTO:
    # response_model= is kept despite matching the return type so the arch
    # test `test_every_endpoint_declares_response_model` stays green.
    """Return every visible social-proof item rendered on a surface."""
    resolved = SocialProofResolver(db).for_surface(
        tenant_id=user.tenant_id,
        surface_type=surface_type,
        surface_ref_id=surface_ref_id,
        include_brand=include_brand,
    )
    return ResolvedSocialProofDTO(
        testimonials=[
            PlacedTestimonialDTO(testimonial=p.testimonial, placement=p.placement) for p in resolved.testimonials
        ],
        authority_items=[
            PlacedAuthorityItemDTO(authority_item=p.authority_item, placement=p.placement)
            for p in resolved.authority_items
        ],
        team_members=[
            PlacedTeamMemberDTO(team_member=p.team_member, placement=p.placement) for p in resolved.team_members
        ],
    )
