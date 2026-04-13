"""Agenda API endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.core.database import get_db
from src.modules.crm.infrastructure.models.lead_model import LeadModel
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.scheduling.infrastructure.models.appointment_model import (
    AppointmentModel,
)
from src.modules.scheduling.infrastructure.repositories.appointment_repository import (
    AppointmentRepository,
)

router = APIRouter(tags=["Scheduling - Agenda"])


class AgendaItem(BaseModel):
    """Schema for agenda item."""

    id: UUID
    summary: str
    start_time: datetime
    end_time: datetime
    status: str
    lead_name: str | None = None
    meeting_link: str | None = None


@router.get("/")
async def get_agenda(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    range_: Annotated[Literal["today", "week"], Query(alias="range")] = "today",
) -> list[AgendaItem]:
    """Retrieve agenda."""
    repo = AppointmentRepository(db)
    now = datetime.now(UTC)

    if range_ == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    else:  # week
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)

    appointments = repo.get_appointments_by_date_range(start, end, user.tenant_id)

    # Enrich with Lead Names (NOTE: Cross-module dependency, consider moving to a service)
    lead_ids = [a.lead_id for a in appointments if a.lead_id]
    lead_map = {}
    if lead_ids:
        # Use joinedload to fetch Customer Profile efficiently
        leads_stmt = select(LeadModel).options(joinedload(LeadModel.customer)).where(LeadModel.id.in_(lead_ids))
        leads = db.execute(leads_stmt).scalars().all()

        for lead in leads:
            # Try to get name from Customer (SSOT), then fallback to Lead profile_data
            customer_name = lead.customer.full_name if lead.customer else None
            profile = lead.profile_data or {}

            name = customer_name or profile.get("full_name") or profile.get("name") or "Unknown Lead"
            lead_map[lead.id] = name

    return [
        AgendaItem(
            id=a.id,
            summary=a.summary,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status.value,
            meeting_link=a.meeting_link,
            lead_name=lead_map.get(a.lead_id, "Unknown Lead"),
        )
        for a in appointments
    ]


class AppointmentStatusUpdate(BaseModel):
    """Schema for appointment status update."""

    status: str = Field(..., description="New status: COMPLETED, NO_SHOW, CANCELLED")


class AppointmentStatusResponse(BaseModel):
    """Schema for appointment status response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    appointment_id: str
    old_status: str
    new_status: str


@router.patch("/{appointment_id}/status", response_model=AppointmentStatusResponse)
async def update_appointment_status(
    appointment_id: UUID,
    payload: AppointmentStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Update appointment status and publish event via EventBus."""
    from src.modules.scheduling.domain.enums import AppointmentStatus

    # Validate status
    valid_statuses = {s.value for s in AppointmentStatus}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    stmt = select(AppointmentModel).where(
        AppointmentModel.id == appointment_id,
        AppointmentModel.tenant_id == user.tenant_id,
    )
    appointment = db.execute(stmt).scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    old_status = appointment.status
    appointment.status = payload.status
    db.flush()

    # Publish EventBus event for CRM listeners
    _publish_appointment_event(
        db=db,
        tenant_id=user.tenant_id,
        lead_id=appointment.lead_id,
        appointment_id=appointment.id,
        status=payload.status,
    )
    db.commit()

    return {
        "status": "updated",
        "appointment_id": str(appointment_id),
        "old_status": old_status,
        "new_status": payload.status,
    }


def _publish_appointment_event(
    db: Session,
    tenant_id: UUID,
    lead_id: UUID | None,
    appointment_id: UUID,
    status: str,
) -> None:
    """Publish an AppointmentEvent via EventBus.

    Uses late binding import to avoid circular dependencies.
    """
    from src.shared.domain.events import AppointmentEvent, EventBus

    if not lead_id:
        return

    event = AppointmentEvent.create(
        tenant_id=tenant_id,
        lead_id=lead_id,
        appointment_id=appointment_id,
        appointment_status=status,
    )
    EventBus.publish(event, session=db)
