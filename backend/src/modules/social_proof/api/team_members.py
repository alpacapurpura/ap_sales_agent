"""REST endpoints for TeamMember CRUD."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from luana_core_social_proof.application.dto.team_dto import (
    TeamMemberCreateDTO,
    TeamMemberResponseDTO,
    TeamMemberUpdateDTO,
)
from luana_core_social_proof.application.services.team_service import TeamService
from luana_core_social_proof.domain.team_member import TeamMember
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("", response_model=list[TeamMemberResponseDTO])
@router.get("/", response_model=list[TeamMemberResponseDTO], include_in_schema=False)
def list_team_members(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[TeamMember]:
    """List all team members for the tenant, ordered by sort_order."""
    return TeamService(db).list_tenant(user.tenant_id)


@router.post("", response_model=TeamMemberResponseDTO)
@router.post("/", response_model=TeamMemberResponseDTO, include_in_schema=False)
def create_team_member(
    dto: TeamMemberCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TeamMember:
    """Create a new TeamMember."""
    return TeamService(db).create(
        tenant_id=user.tenant_id,
        user_id=user.id,
        **dto.model_dump(),
    )


@router.get("/{member_id}", response_model=TeamMemberResponseDTO)
def get_team_member(
    member_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TeamMember:
    """Return a single TeamMember."""
    entity = TeamService(db).get(user.tenant_id, member_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Team member not found")
    return entity


@router.patch("/{member_id}", response_model=TeamMemberResponseDTO)
def patch_team_member(
    member_id: uuid.UUID,
    dto: TeamMemberUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TeamMember:
    """Update partial fields on a TeamMember."""
    updates = dto.model_dump(exclude_unset=True)
    result = TeamService(db).update(user.tenant_id, member_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Team member not found")
    return result


@router.delete("/{member_id}", status_code=204)
def delete_team_member(
    member_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete a TeamMember. Cascades to its placements."""
    ok = TeamService(db).soft_delete(user.tenant_id, member_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Team member not found")


@router.post("/{member_id}/clone", response_model=TeamMemberResponseDTO)
def clone_team_member(
    member_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TeamMember:
    """Clone an existing TeamMember for targeted customization."""
    cloned = TeamService(db).clone(user.tenant_id, member_id, user.id)
    if cloned is None:
        raise HTTPException(status_code=404, detail="Team member not found")
    return cloned
