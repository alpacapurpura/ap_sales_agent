"""Enrollments REST API (Phase 5).

Routes:

- ``POST   /enrollments`` — create.
- ``GET    /enrollments`` — list with filters.
- ``GET    /enrollments/waitlist`` — list waitlist for an offer.
- ``GET    /enrollments/{id}`` — get one.
- ``PATCH  /enrollments/{id}/status`` — manual status transition.
- ``POST   /enrollments/{id}/mark-paid`` — manual mark paid.
- ``POST   /enrollments/promote-waitlist`` — bulk waitlist → edition.

Every endpoint returns a typed ``-> Pydantic DTO`` which satisfies the
architectural fitness test ``test_all_endpoints_have_response_model``
(the ``or has_return_type`` branch).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.api.dto.enrollments import (
    EnrollmentCreateRequest,
    EnrollmentDTO,
    EnrollmentListResponse,
    MarkPaidRequest,
    PromoteWaitlistRequest,
    PromoteWaitlistResponse,
    StatusTransitionRequest,
)
from src.modules.sales_agent.application.services.enrollment_service import (
    EnrollmentService,
)
from src.modules.sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentStatus,
)
from src.modules.sales_agent.infrastructure.repositories.enrollment_repository import (
    EnrollmentRepository,
)

router = APIRouter()


def _service(db: Session) -> EnrollmentService:
    return EnrollmentService(EnrollmentRepository(db))


def _to_dto(enrollment: Enrollment) -> EnrollmentDTO:
    return EnrollmentDTO.model_validate(enrollment, from_attributes=True)


# ── Create ──────────────────────────────────────────────────────────────────


@router.post(
    "/enrollments",
    status_code=http_status.HTTP_201_CREATED,
)
def create_enrollment(
    payload: EnrollmentCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EnrollmentDTO:
    """Create a new enrollment."""
    svc = _service(db)
    result = svc.create(
        EnrollmentCreate(**payload.model_dump()),
        user.tenant_id,
    )
    db.commit()
    return _to_dto(result.enrollment)


# ── List ────────────────────────────────────────────────────────────────────


@router.get("/enrollments")
def list_enrollments(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    offer_id: Annotated[UUID | None, Query()] = None,
    edition_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[EnrollmentStatus | None, Query()] = None,
    contact_id: Annotated[UUID | None, Query()] = None,
) -> EnrollmentListResponse:
    """List enrollments filtered by any combination of query params."""
    svc = _service(db)
    items = svc.repo.list_all(
        tenant_id=user.tenant_id,
        offer_id=offer_id,
        edition_id=edition_id,
        status=status,
        contact_id=contact_id,
    )
    return EnrollmentListResponse(
        items=[_to_dto(e) for e in items],
        total=len(items),
    )


@router.get("/enrollments/waitlist")
def list_waitlist(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    offer_id: Annotated[UUID, Query(...)],
) -> EnrollmentListResponse:
    """List waitlist enrollments for an offer."""
    svc = _service(db)
    items = svc.repo.list_waitlist(offer_id, user.tenant_id)
    return EnrollmentListResponse(
        items=[_to_dto(e) for e in items],
        total=len(items),
    )


@router.get("/enrollments/by-conversation/{conversation_id}")
def get_by_conversation(
    conversation_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EnrollmentDTO | None:
    """Return the most recent enrollment for a conversation, or null."""
    svc = _service(db)
    enrollment = svc.repo.get_by_conversation(conversation_id, user.tenant_id)
    return _to_dto(enrollment) if enrollment else None


@router.get("/enrollments/{enrollment_id}")
def get_enrollment(
    enrollment_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EnrollmentDTO:
    """Retrieve one enrollment."""
    svc = _service(db)
    enrollment = svc.repo.get_by_id(enrollment_id, user.tenant_id)
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return _to_dto(enrollment)


# ── Transitions ─────────────────────────────────────────────────────────────


@router.patch("/enrollments/{enrollment_id}/status")
def transition_status(
    enrollment_id: UUID,
    payload: StatusTransitionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EnrollmentDTO:
    """Manual status transition (cancel, refund, mark attended)."""
    svc = _service(db)
    try:
        result = svc.update_status(
            enrollment_id,
            user.tenant_id,
            payload.status,
            actor=f"human:{user.id}" if getattr(user, "id", None) else "human:unknown",
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return _to_dto(result.enrollment)


@router.post("/enrollments/{enrollment_id}/mark-paid")
def mark_paid(
    enrollment_id: UUID,
    payload: MarkPaidRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EnrollmentDTO:
    """Mark an enrollment paid manually (no webhook)."""
    svc = _service(db)
    try:
        result = svc.mark_paid(
            enrollment_id,
            user.tenant_id,
            provider=payload.provider,
            transaction_id=payload.transaction_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return _to_dto(result.enrollment)


@router.post("/enrollments/promote-waitlist")
def promote_waitlist(
    payload: PromoteWaitlistRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> PromoteWaitlistResponse:
    """Bulk-promote a list of waitlist enrollments to a target edition."""
    svc = _service(db)
    results = svc.promote_waitlist(
        payload.enrollment_ids,
        payload.target_edition_id,
        user.tenant_id,
    )
    db.commit()
    promoted = len(results)
    skipped = len(payload.enrollment_ids) - promoted
    return PromoteWaitlistResponse(
        promoted=promoted,
        skipped=skipped,
        items=[_to_dto(r.enrollment) for r in results],
    )
