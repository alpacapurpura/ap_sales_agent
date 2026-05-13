"""REST endpoints for Testimonial CRUD."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from luana_core_social_proof.application.dto.testimonial_dto import (
    TestimonialCreateDTO,
    TestimonialResponseDTO,
    TestimonialUpdateDTO,
)
from luana_core_social_proof.application.services.testimonial_service import (
    TestimonialService,
)
from luana_core_social_proof.domain.testimonial import Testimonial
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("", response_model=list[TestimonialResponseDTO])
@router.get("/", response_model=list[TestimonialResponseDTO], include_in_schema=False)
def list_testimonials(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[Testimonial]:
    """List all testimonials for the tenant."""
    return TestimonialService(db).list_tenant(user.tenant_id)


@router.post("", response_model=TestimonialResponseDTO)
@router.post("/", response_model=TestimonialResponseDTO, include_in_schema=False)
def create_testimonial(
    dto: TestimonialCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Testimonial:
    """Create a new Testimonial for the tenant."""
    return TestimonialService(db).create(
        tenant_id=user.tenant_id,
        user_id=user.id,
        **dto.model_dump(),
    )


@router.get("/{testimonial_id}", response_model=TestimonialResponseDTO)
def get_testimonial(
    testimonial_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Testimonial:
    """Return a single Testimonial."""
    entity = TestimonialService(db).get(user.tenant_id, testimonial_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return entity


@router.patch("/{testimonial_id}", response_model=TestimonialResponseDTO)
def patch_testimonial(
    testimonial_id: uuid.UUID,
    dto: TestimonialUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Testimonial:
    """Update partial fields on a Testimonial."""
    updates = dto.model_dump(exclude_unset=True)
    result = TestimonialService(db).update(user.tenant_id, testimonial_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return result


@router.delete("/{testimonial_id}", status_code=204)
def delete_testimonial(
    testimonial_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete a Testimonial. Cascades to its placements."""
    ok = TestimonialService(db).soft_delete(user.tenant_id, testimonial_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Testimonial not found")


@router.post("/{testimonial_id}/clone", response_model=TestimonialResponseDTO)
def clone_testimonial(
    testimonial_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Testimonial:
    """Clone an existing Testimonial for targeted customization."""
    cloned = TestimonialService(db).clone(user.tenant_id, testimonial_id, user.id)
    if cloned is None:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    return cloned
