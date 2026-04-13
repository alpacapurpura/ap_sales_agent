"""Interview Engine REST API endpoints."""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.document_dto import DocumentProcessingResponse
from src.modules.copilot.api.interview_dto import (
    ActiveInterviewResponse,
    InterviewStateResponse,
    InterviewStatusResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from src.modules.copilot.application.services.document_processor import (
    DocumentProcessor,
)
from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.iam.domain.user import User
from src.shared.application.ai_action_service import AIActionService

logger = structlog.get_logger()

router = APIRouter()


@router.post("/start")
def start_interview(
    request: StartInterviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> StartInterviewResponse:
    """Start interview."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    try:
        result = svc.start_interview(
            tenant_id=tenant_id,
            user_id=current_user.id,
            domain=request.domain,
            resume_session_id=request.resume_session_id,
            entity_id=request.entity_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return result


@router.get("/active", response_model=ActiveInterviewResponse)
def get_active_interview(
    response: Response,
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ActiveInterviewResponse | Response:
    """Return active interview."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    result = svc.get_active(tenant_id)
    if not result:
        return Response(status_code=204)
    return result


@router.get("/{session_id}/state")
def get_interview_state(
    session_id: UUID,
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> InterviewStateResponse:
    """Return interview state."""
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
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Execute pause interview operation."""
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
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Execute abandon interview operation."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    success = svc.abandon(session_id, tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot abandon session")
    return {"status": "abandoned"}


@router.post("/{session_id}/documents")
async def process_interview_documents(
    session_id: UUID,
    files: Annotated[list[UploadFile], File()],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentProcessingResponse:
    """Process uploaded documents and merge extracted data into mapa_global.

    Synchronous (blocking) — the consultant digests everything before continuing.
    """
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    svc = InterviewService(db)
    session = svc.get_session(session_id, tenant_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    extraction_template = session.config_snapshot.get("document_extraction_template")
    if not extraction_template:
        raise HTTPException(
            status_code=400,
            detail="This interview domain does not support document processing",
        )

    processor = DocumentProcessor(ai_service=AIActionService())
    result = await processor.process_for_interview(
        files=files,
        extraction_template=extraction_template,
        existing_mapa=session.mapa_global,
        tenant_id=tenant_id,
    )

    if result.delta:
        svc.update_mapa_global(
            session_id=session_id,
            tenant_id=tenant_id,
            delta=result.delta,
        )
        logger.info(
            "documents_processed_and_merged",
            session_id=str(session_id),
            fields_extracted=result.fields_extracted,
            tenant_id=str(tenant_id),
        )

    return DocumentProcessingResponse(
        delta=result.delta,
        summary=result.summary,
        source_documents=result.source_documents,
        fields_extracted=result.fields_extracted,
        fields_skipped=result.fields_skipped,
    )
