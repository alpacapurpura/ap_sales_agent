"""Copilot event tracking API — record and query behavioral events."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.dto import (
    EventInsightsResponse,
    EventSummaryResponse,
    RecordEventResponse,
)
from src.modules.copilot.infrastructure.repositories.event_repository import (
    CopilotEventRepository,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.iam.domain.user import User

router = APIRouter()


class RecordEventRequest(BaseModel):
    """Request schema for record event."""

    event_type: str = Field(..., max_length=50)
    event_data: dict = Field(default_factory=dict)
    conversation_id: str | None = None
    route: str | None = None


@router.post("/record", status_code=201, response_model=RecordEventResponse)
def record_event(
    request: RecordEventRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    """Record event."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    repo = CopilotEventRepository(db)
    conv_id = UUID(request.conversation_id) if request.conversation_id else None
    repo.record(
        tenant_id=tenant_id,
        user_id=current_user.id,
        event_type=request.event_type,
        event_data=request.event_data,
        conversation_id=conv_id,
        route=request.route,
    )
    db.commit()
    return {"recorded": True}


@router.get("/summary", response_model=EventSummaryResponse)
def event_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    days: int = 30,
) -> dict[str, str | int | dict[str, int]]:
    """Execute event summary operation."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    repo = CopilotEventRepository(db)
    summary = repo.get_tenant_summary(tenant_id, days=days)
    return {"events": summary, "period_days": days, "tenant_id": str(tenant_id)}


@router.get("/insights", response_model=EventInsightsResponse)
def event_insights(
    current_user: Annotated[User, Depends(get_current_user)],
    tenant_id: Annotated[UUID | None, Depends(get_tenant_context)],
    db: Annotated[Session, Depends(get_db)],
    days: int = 30,
) -> dict[str, str | int | dict]:
    """Execute event insights operation."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    repo = CopilotEventRepository(db)
    return {
        "friction_map": repo.get_friction_map(tenant_id, days=days),
        "engagement": repo.get_engagement_metrics(tenant_id, days=days),
        "procedure_rates": repo.get_procedure_completion_rates(tenant_id, days=days),
        "period_days": days,
        "tenant_id": str(tenant_id),
    }
