"""
CRM Pipeline API: lead pipeline view, manual stage override, and transition audit trail.

All endpoints require X-Tenant-ID header for multitenant isolation.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["CRM - Pipeline"])


# --- Response / Request Models ---


class PipelineItem(BaseModel):
    id: UUID
    full_name: str | None
    intent_score: int
    temperature: str
    last_interaction: datetime | None
    channel: str | None
    avatar_url: str | None = None


class StageOverrideRequest(BaseModel):
    """Request body for manual stage override."""

    new_stage: str = Field(
        ...,
        description="Target lifecycle stage (e.g. 'customer', 'mql')",
    )
    note: str = Field("", description="Optional note explaining the override")


class TransitionResponse(BaseModel):
    """Single lifecycle transition audit record."""

    id: UUID
    from_stage: str | None
    to_stage: str
    reason: str
    triggered_by: str
    score_at_transition: float | None
    metadata: dict | None = None
    occurred_at: datetime | None


class StageOverrideResponse(BaseModel):
    """Response for successful stage override."""

    profile_id: UUID
    previous_stage: str
    new_stage: str
    note: str


# --- Endpoints ---


@router.get("/pipeline")
async def get_pipeline(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    min_score: int = 50,
    limit: int = 20,
) -> list[PipelineItem]:
    """Get high-intent leads for the pipeline view."""
    # Fallback to simple query until repo method is robust
    leads_orm = (
        db.execute(
            select(LeadModel)
            .options(joinedload(LeadModel.customer))
            .where(
                LeadModel.tenant_id == user.tenant_id,
                LeadModel.is_blacklisted.is_(False),
            )
            .limit(limit),
        )
        .scalars()
        .all()
    )

    results = []
    for lead in leads_orm:
        customer_name = lead.customer.full_name if lead.customer else None
        profile = lead.profile_data or {}
        name = customer_name or profile.get("full_name") or profile.get("name") or "Unknown Lead"
        results.append(
            PipelineItem(
                id=lead.id,
                full_name=name,
                intent_score=lead.intent_score or 0,
                temperature=lead.temperature or "COLD",
                last_interaction=lead.last_interaction_date,
                channel="Unknown",
            ),
        )
    return results


@router.put("/pipeline/{profile_id}/stage")
async def override_stage(
    profile_id: UUID,
    body: StageOverrideRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> StageOverrideResponse:
    """Manual override of a profile's lifecycle stage.

    Requires X-Tenant-ID header. Creates audit trail with triggered_by='manual'.
    """
    from src.modules.crm.application.services.lifecycle_service import LifecycleService
    from src.modules.crm.domain.enums import LifecycleStage

    # Validate stage value
    try:
        new_stage = LifecycleStage(body.new_stage.lower())
    except ValueError:
        valid = [s.value for s in LifecycleStage]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{body.new_stage}'. Valid stages: {valid}",
        ) from None

    svc = LifecycleService(db)

    # Get current stage for response
    from src.modules.crm.infrastructure.models.customer_model import (
        CustomerProfileModel,
    )

    profile = (
        db.execute(
            select(CustomerProfileModel).where(
                CustomerProfileModel.id == profile_id,
                CustomerProfileModel.tenant_id == user.tenant_id,
            ),
        )
        .scalars()
        .first()
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    previous_stage = profile.lifecycle_stage.value if profile.lifecycle_stage else "unknown"

    svc.force_stage(
        profile_id=profile_id,
        tenant_id=user.tenant_id,
        new_stage=new_stage,
        admin_user_id=str(user.id),
        note=body.note,
    )
    db.commit()

    return StageOverrideResponse(
        profile_id=profile_id,
        previous_stage=previous_stage,
        new_stage=new_stage.value,
        note=body.note,
    )


@router.get(
    "/pipeline/{profile_id}/transitions",
)
async def get_transitions(
    profile_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[TransitionResponse]:
    """Get lifecycle transition audit trail for a profile.

    Returns most recent transitions first. Requires X-Tenant-ID header.
    """
    from src.modules.crm.infrastructure.repositories.lifecycle_repository import (
        LifecycleRepository,
    )

    repo = LifecycleRepository(db)
    transitions = repo.get_transitions_by_profile(
        profile_id=profile_id,
        tenant_id=user.tenant_id,
        limit=limit,
    )

    return [
        TransitionResponse(
            id=t.id,
            from_stage=t.from_stage.value if t.from_stage else None,
            to_stage=t.to_stage.value,
            reason=t.reason,
            triggered_by=t.triggered_by,
            score_at_transition=t.score_at_transition,
            metadata=t.transition_metadata,
            occurred_at=t.occurred_at,
        )
        for t in transitions
    ]
