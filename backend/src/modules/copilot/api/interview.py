"""Interview Engine REST API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.interview_dto import (
    ActiveInterviewResponse,
    InterviewStateResponse,
    InterviewStatusResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context

router = APIRouter()


@router.post("/start", response_model=StartInterviewResponse)
def start_interview(
    request: StartInterviewRequest,
    current_user=Depends(get_current_user),
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    try:
        result = svc.start_interview(
            tenant_id=tenant_id,
            user_id=current_user.id,
            domain=request.domain,
            resume_session_id=request.resume_session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return result


@router.get("/active", response_model=ActiveInterviewResponse)
def get_active_interview(
    response: Response,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    result = svc.get_active(tenant_id)
    if not result:
        return Response(status_code=204)
    return result


@router.get("/{session_id}/state", response_model=InterviewStateResponse)
def get_interview_state(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    result = svc.get_state(session_id, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/{session_id}/pause", response_model=InterviewStatusResponse)
def pause_interview(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    success = svc.pause(session_id, tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause session")
    return {"status": "paused"}


@router.post("/{session_id}/abandon", response_model=InterviewStatusResponse)
def abandon_interview(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    success = svc.abandon(session_id, tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot abandon session")
    return {"status": "abandoned"}
