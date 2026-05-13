"""Events API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from luana_core_commercial_calendar.api.dto.calendar_events import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from luana_core_commercial_calendar.application.calendar_event_service import (
    CalendarEventService,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


def _to_response(event: object) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=event.id,
        tenant_id=event.tenant_id,
        country_code=event.country_code,
        date=event.date,
        year=event.year,
        week_number=event.week_number,
        name=event.name,
        category=event.category,
        description=event.description,
        is_system=event.is_system,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.get("/events")
def list_events(
    country_code: Annotated[str, Query(min_length=2, max_length=2)],
    year: Annotated[int, Query()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    week: Annotated[int | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
) -> list[CalendarEventResponse]:
    """List events."""
    service = CalendarEventService(db)
    events = service.list_events(
        country_code=country_code.upper(),
        year=year,
        tenant_id=user.tenant_id,
        week=week,
        category=category,
    )
    return [_to_response(e) for e in events]


@router.get("/events/current-week")
def get_current_week(
    country_code: Annotated[str, Query(min_length=2, max_length=2)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[CalendarEventResponse]:
    """Retrieve current week."""
    service = CalendarEventService(db)
    events = service.get_current_week_events(
        country_code=country_code.upper(),
        tenant_id=user.tenant_id,
    )
    return [_to_response(e) for e in events]


@router.post("/events", status_code=201)
def create_event(
    body: CalendarEventCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[CalendarEventResponse]:
    """Create a new event."""
    service = CalendarEventService(db)
    created = service.create_event(
        country_code=body.country_code,
        name=body.name,
        date_start=body.date_start,
        date_end=body.date_end,
        category=body.category,
        description=body.description,
        tenant_id=user.tenant_id,
    )
    return [_to_response(e) for e in created]


@router.put("/events/{event_id}")
def update_event(
    event_id: UUID,
    body: CalendarEventUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CalendarEventResponse:
    """Update event."""
    service = CalendarEventService(db)
    existing = service.get_by_id(event_id, tenant_id=user.tenant_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if existing.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify events from another tenant",
        )

    updated = service.update_event(
        event_id=event_id,
        country_code=body.country_code,
        name=body.name,
        event_date=body.date,
        category=body.category,
        description=body.description,
        tenant_id=user.tenant_id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _to_response(updated)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(
    event_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete event."""
    service = CalendarEventService(db)
    existing = service.get_by_id(event_id, tenant_id=user.tenant_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if existing.tenant_id is None:
        raise HTTPException(status_code=403, detail="Cannot delete system events")
    if existing.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete events from another tenant",
        )
    service.delete_event(event_id, tenant_id=user.tenant_id)
