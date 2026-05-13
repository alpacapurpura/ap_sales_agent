"""Plan approval/rejection stub endpoints (CONTRACT §4, plan stubs)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user, get_tenant_context
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from luana_core_platform.domain.datetime_utils import utc_now
from pydantic import BaseModel

# Runtime imports — required at runtime for FastAPI's Annotated[X, Depends(f)] resolver.
from sqlalchemy.orm import Session

logger = structlog.get_logger()

router = APIRouter()


class PlanApproveResponse(BaseModel):
    """Response for POST /plan/{plan_id}/approve."""

    plan_id: UUID
    approved_at: datetime
    status: Literal["approved"]


class PlanRejectResponse(BaseModel):
    """Response for POST /plan/{plan_id}/reject."""

    plan_id: UUID
    rejected_at: datetime
    status: Literal["rejected"]


@router.post(
    "/plan/{plan_id}/approve",
    response_model=PlanApproveResponse,
    status_code=202,
    summary="Aprobar plan de cambios del copilot",
)
async def approve_plan(
    plan_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],  # reserved for DB writes in next sprint
) -> PlanApproveResponse:
    """Mark a pending copilot plan as approved.

    This is a stub — full plan execution is wired in a later sprint.
    The endpoint validates that the caller belongs to a tenant and
    records the approval timestamp.
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    now = utc_now()
    logger.info(
        "plan_approved",
        plan_id=str(plan_id),
        tenant_id=str(tenant_id),
        user_id=str(current_user.id),
    )
    return PlanApproveResponse(
        plan_id=plan_id,
        approved_at=now,
        status="approved",
    )


@router.post(
    "/plan/{plan_id}/reject",
    response_model=PlanRejectResponse,
    status_code=202,
    summary="Rechazar plan de cambios del copilot",
)
async def reject_plan(
    plan_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],  # reserved for DB writes in next sprint
) -> PlanRejectResponse:
    """Mark a pending copilot plan as rejected.

    This is a stub — full plan cancellation is wired in a later sprint.
    The endpoint validates that the caller belongs to a tenant and
    records the rejection timestamp.
    """
    if not tenant_id or not current_user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    now = utc_now()
    logger.info(
        "plan_rejected",
        plan_id=str(plan_id),
        tenant_id=str(tenant_id),
        user_id=str(current_user.id),
    )
    return PlanRejectResponse(
        plan_id=plan_id,
        rejected_at=now,
        status="rejected",
    )
