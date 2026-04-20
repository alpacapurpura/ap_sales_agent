"""REST endpoints for AuthorityItem CRUD."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.social_proof.application.dto.authority_dto import (
    AuthorityCreateDTO,
    AuthorityResponseDTO,
    AuthorityUpdateDTO,
)
from src.modules.social_proof.application.services.authority_service import (
    AuthorityService,
)
from src.modules.social_proof.domain.authority_item import AuthorityItem

router = APIRouter()


@router.get("", response_model=list[AuthorityResponseDTO])
@router.get("/", response_model=list[AuthorityResponseDTO], include_in_schema=False)
def list_authority_items(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AuthorityItem]:
    """List all authority items for the tenant."""
    return AuthorityService(db).list_tenant(user.tenant_id)


@router.post("", response_model=AuthorityResponseDTO)
@router.post("/", response_model=AuthorityResponseDTO, include_in_schema=False)
def create_authority_item(
    dto: AuthorityCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorityItem:
    """Create a new AuthorityItem."""
    return AuthorityService(db).create(
        tenant_id=user.tenant_id,
        user_id=user.id,
        **dto.model_dump(),
    )


@router.get("/{item_id}", response_model=AuthorityResponseDTO)
def get_authority_item(
    item_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorityItem:
    """Return a single AuthorityItem."""
    entity = AuthorityService(db).get(user.tenant_id, item_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Authority item not found")
    return entity


@router.patch("/{item_id}", response_model=AuthorityResponseDTO)
def patch_authority_item(
    item_id: uuid.UUID,
    dto: AuthorityUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorityItem:
    """Update partial fields on an AuthorityItem."""
    updates = dto.model_dump(exclude_unset=True)
    result = AuthorityService(db).update(user.tenant_id, item_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Authority item not found")
    return result


@router.delete("/{item_id}", status_code=204)
def delete_authority_item(
    item_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete an AuthorityItem. Cascades to its placements."""
    ok = AuthorityService(db).soft_delete(user.tenant_id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Authority item not found")


@router.post("/{item_id}/clone", response_model=AuthorityResponseDTO)
def clone_authority_item(
    item_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorityItem:
    """Clone an existing AuthorityItem for targeted customization."""
    cloned = AuthorityService(db).clone(user.tenant_id, item_id, user.id)
    if cloned is None:
        raise HTTPException(status_code=404, detail="Authority item not found")
    return cloned
