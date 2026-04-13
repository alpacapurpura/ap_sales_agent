import datetime
import secrets
from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.api.dto.common import (
    AppointmentItem,
    BookingLinkResponse,
    BookMeetingResponse,
    ConnectionTestResponse,
    PersonalizedLinkResponse,
    SlotsResponse,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.google_calendar import (
    GoogleCalendarAdapter,
)
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.crm.domain.lead import Lead
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.scheduling.api.dto.calendar import (
    BookMeetingRequest,
    CalendarStatusResponse,
    CreateBookingLinkRequest,
)
from src.modules.scheduling.application.booking_url import get_booking_base_url
from src.modules.scheduling.application.services.availability_service import (
    AvailabilityService,
)
from src.modules.scheduling.domain.availability_schema import (
    AvailabilitySchedule,
    ScheduleUpdate,
)
from src.modules.scheduling.infrastructure.models.booking_link import BookingLink
from src.shared.links.models import ShareableLink
from src.shared.links.service import LinkService

router = APIRouter(tags=["calendar"])
logger = structlog.get_logger()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


@router.get("/auth-url")
async def get_auth_url(
    user: Annotated[User, Depends(get_current_user)],
    redirect_uri: str | None = None,
):
    url, state = GoogleCalendarAdapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: Annotated[str, Body(embed=True)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
    redirect_uri: Annotated[str | None, Body(embed=True)] = None,
):
    try:
        creds_data = GoogleCalendarAdapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.exception("oauth_exchange_failed", error=str(e))
        raise HTTPException(
            status_code=400,
            detail="Error de autenticacion con Google",
        ) from e

    try:
        adapter = GoogleCalendarAdapter(creds_data)
        service = adapter.get_service()
        calendar = service.calendars().get(calendarId="primary").execute()
        email = calendar.get("id")
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("failed_to_get_calendar_info", error=str(e))
        email = "Unknown"

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.GOOGLE_CALENDAR,
        credentials=creds_data,
        config={"email": email},
    )

    return {"status": "connected", "email": email}


@router.get("/status", response_model=CalendarStatusResponse)
async def get_status(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_CALENDAR)

    stmt = (
        select(ShareableLink)
        .where(
            ShareableLink.tenant_id == user.tenant_id,
            ShareableLink.target_type == "booking",
            ShareableLink.is_active.is_(True),
        )
        .order_by(ShareableLink.created_at.desc())
    )
    link = db.execute(stmt).scalars().first()

    base_url = get_booking_base_url(user.tenant_id, db)
    booking_link = f"{base_url}/visit/{link.token}" if link else None

    if not connection:
        return CalendarStatusResponse(
            is_connected=False,
            booking_link=booking_link,
        )

    return CalendarStatusResponse(
        is_connected=True,
        email=connection.config.get("email"),
        booking_link=booking_link,
    )


@router.post("/link", response_model=BookingLinkResponse)
async def create_booking_link(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = LinkService(db)
    link = service.create_link(
        tenant_id=user.tenant_id,
        target_type="booking",
        created_by=user.id,
    )
    base_url = get_booking_base_url(user.tenant_id, db)
    return {"token": link.token, "url": f"{base_url}/visit/{link.token}"}


@router.post("/personalized-link", response_model=PersonalizedLinkResponse)
async def create_personalized_link(
    payload: CreateBookingLinkRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    lead = (
        db.execute(
            select(Lead).where(
                Lead.id == payload.lead_id,
                Lead.tenant_id == user.tenant_id,
            ),
        )
        .scalars()
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    token = secrets.token_urlsafe(16)
    expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        days=payload.expiration_days,
    )

    link = BookingLink(
        tenant_id=user.tenant_id,
        lead_id=payload.lead_id,
        event_slug=payload.event_slug,
        token=token,
        expires_at=expires_at,
        status="ACTIVE",
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    tenant_slug = user.tenant.slug if user.tenant else "unknown"
    base_url = get_booking_base_url(user.tenant_id, db)

    return {
        "token": link.token,
        "url": f"{base_url}/book/{tenant_slug}/{payload.event_slug}?token={link.token}",
        "expires_at": link.expires_at,
    }


@router.delete("/disconnect")
async def disconnect(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_by_tenant_and_type(
        user.tenant_id,
        ChannelType.GOOGLE_CALENDAR,
    )
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_CALENDAR)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Calendario no conectado")

    try:
        adapter = GoogleCalendarAdapter(connection.credentials)
        now = datetime.datetime.now(datetime.UTC)
        end = now + datetime.timedelta(days=1)
        busy = adapter.list_busy_periods(now, end)
        return {
            "status": "ok",
            "message": "Conexion exitosa",
            "data": {"busy_slots": len(busy), "email": connection.config.get("email")},
        }
    except Exception as e:
        logger.exception("calendar_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}


@router.get("/slots", response_model=SlotsResponse)
async def get_slots(
    start_date: datetime.date,
    end_date: datetime.date,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    duration: int = 30,
):
    service = AvailabilityService(db, user.tenant_id)
    slots = service.get_available_slots(start_date, end_date, duration_minutes=duration)
    return {"slots": slots}


@router.post("/book", response_model=BookMeetingResponse)
async def book_meeting(
    payload: BookMeetingRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    try:
        event = service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=payload.duration_minutes,
            lead_data=payload.lead_data,
        )
        return {"status": "booked", "event_link": event.get("htmlLink")}
    except Exception as e:
        logger.exception("booking_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/appointments", response_model=list[AppointmentItem])
async def list_appointments(
    start_date: datetime.date,
    end_date: datetime.date,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    events = service.list_appointments(start_date, end_date)

    result = []
    for e in events:
        start = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")
        end_time = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
        meet_link = e.get("hangoutLink")

        result.append(
            {
                "id": e.get("id"),
                "summary": e.get("summary"),
                "start": start,
                "end": end_time,
                "meet_link": meet_link,
                "attendees": [a.get("email") for a in e.get("attendees", [])],
            },
        )
    return result


# --- Availability Management Endpoints ---


@router.get("/schedules", response_model=list[AvailabilitySchedule])
async def list_schedules(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    return service.list_schedules()


@router.post("/schedules", response_model=AvailabilitySchedule)
async def create_schedule(
    schedule: AvailabilitySchedule,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    return service.create_schedule(schedule)


@router.patch("/schedules/{schedule_id}", response_model=AvailabilitySchedule)
async def update_schedule(
    schedule_id: str,
    update: ScheduleUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    updated = service.update_schedule(schedule_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = AvailabilityService(db, user.tenant_id)
    deleted = service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Schedule not found or is last remaining",
        )
    return {"status": "deleted"}
