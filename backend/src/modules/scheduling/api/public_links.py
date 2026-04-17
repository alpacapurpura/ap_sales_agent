"""Public Links API endpoints."""

import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.scheduling.api.dto.public_links import (
    BookingConfirmationResponse,
    BookingLinkResolveResponse,
    BookingRequest,
    EventTypeResolveResponse,
    LinkResolveResponse,
    SlotsResponse,
)
from src.modules.scheduling.application.services.availability_service import (
    AvailabilityService,
)
from src.modules.scheduling.application.services.event_type_service import (
    EventTypeService,
)
from src.modules.scheduling.infrastructure.models.booking_link import BookingLink
from src.shared.links.service import LinkService

logger = structlog.get_logger()

router = APIRouter()

# --- Endpoints ---


@router.get("/booking-links/{token}")
def resolve_booking_link(token: str, db: Annotated[Session, Depends(get_db)]) -> BookingLinkResolveResponse:
    """Handle resolve booking link request."""
    stmt = select(BookingLink).where(
        BookingLink.token == token,
        BookingLink.status == "ACTIVE",
    )
    link = db.execute(stmt).scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link invalid or expired")

    # Check expiration
    if link.expires_at.replace(tzinfo=datetime.UTC) < datetime.datetime.now(
        datetime.UTC,
    ):
        link.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=404, detail="Link expired")

    return BookingLinkResolveResponse(
        valid=True,
        event_slug=link.event_slug,
        lead_name=link.lead.full_name if link.lead else None,
        lead_email=link.lead.email if link.lead else None,
        lead_phone=link.lead.phone if link.lead else None,
        lead_id=str(link.lead_id),
        expires_at=link.expires_at,
    )


@router.get("/resolve/{token}")
def resolve_link(token: str, db: Annotated[Session, Depends(get_db)]) -> LinkResolveResponse:
    """Handle resolve link request."""
    service = LinkService(db)
    link = service.resolve_link(token)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    tenant = service.get_tenant_for_link(link)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant configuration error")

    return LinkResolveResponse(
        valid=True,
        type=link.target_type,
        tenant_name=tenant.name,
        # tenant_avatar could be in config_json or added later
        tenant_avatar=tenant.config_json.get("brand_settings", {}).get("logo_url"),
        params=link.params,
    )


@router.get("/{token}/slots")
def get_public_slots(
    token: str,
    start_date: datetime.date,
    end_date: datetime.date,
    db: Annotated[Session, Depends(get_db)],
) -> SlotsResponse:
    """Public endpoint to fetch slots via token authentication."""
    link_service = LinkService(db)
    link = link_service.resolve_link(token)

    if not link or link.target_type != "booking":
        raise HTTPException(status_code=404, detail="Invalid link for booking")

    av_service = AvailabilityService(db, link.tenant_id)

    try:
        slots = av_service.get_available_slots(start_date, end_date)
        return SlotsResponse(slots=slots)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Event Type Public Endpoints ---


@router.get("/event-types/by-id/{event_slug}")
def resolve_event_type_by_tenant_id(
    event_slug: str,
    db: Annotated[Session, Depends(get_db)],
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> EventTypeResolveResponse:
    """Resolve an event type using X-Tenant-ID header (UUID).

    Used by booking pages under custom domains where tenant_slug is not in the URL.
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")

    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid X-Tenant-ID format",
        ) from None

    stmt = select(TenantModel).where(TenantModel.id == tenant_uuid)
    tenant = db.execute(stmt).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    service = EventTypeService(db, tenant.id)
    event_type = service.get_by_slug(event_slug)
    if not event_type:
        raise HTTPException(status_code=404, detail="Event Type not found")

    logger.info(
        "event_type_resolved_by_tenant_id",
        tenant_id=x_tenant_id,
        event_slug=event_slug,
    )
    return EventTypeResolveResponse(
        event_type=event_type,
        tenant_name=tenant.name,
        tenant_avatar=(tenant.config_json or {}).get("brand_settings", {}).get("logo_url"),
        tenant_id=str(tenant.id),
    )


@router.get(
    "/event-types/{tenant_slug}/{event_slug}",
)
def resolve_event_type(
    tenant_slug: str,
    event_slug: str,
    db: Annotated[Session, Depends(get_db)],
) -> EventTypeResolveResponse:
    """Handle resolve event type request."""
    stmt = select(Tenant).where(Tenant.slug == tenant_slug)
    tenant = db.execute(stmt).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    service = EventTypeService(db, tenant.id)
    event_type = service.get_by_slug(event_slug)

    if not event_type:
        raise HTTPException(status_code=404, detail="Event Type not found")

    return EventTypeResolveResponse(
        event_type=event_type,
        tenant_name=tenant.name,
        tenant_avatar=tenant.config_json.get("brand_settings", {}).get("logo_url"),
        tenant_id=str(tenant.id),
    )


@router.get(
    "/event-types/{tenant_slug}/{event_slug}/slots",
)
def get_event_type_slots(
    tenant_slug: str,
    event_slug: str,
    start_date: datetime.date,
    end_date: datetime.date,
    db: Annotated[Session, Depends(get_db)],
) -> SlotsResponse:
    """Retrieve event type slots."""
    stmt = select(Tenant).where(Tenant.slug == tenant_slug)
    tenant = db.execute(stmt).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    et_service = EventTypeService(db, tenant.id)
    event_type = et_service.get_by_slug(event_slug)
    if not event_type:
        raise HTTPException(status_code=404, detail="Event Type not found")

    av_service = AvailabilityService(db, tenant.id)
    try:
        slots = av_service.get_event_type_slots(event_type, start_date, end_date)
        return SlotsResponse(slots=slots)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/event-types/{tenant_slug}/{event_slug}/book",
)
def book_event_type(
    tenant_slug: str,
    event_slug: str,
    payload: BookingRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BookingConfirmationResponse:
    """Book event type."""
    tenant_stmt = select(Tenant).where(Tenant.slug == tenant_slug)
    tenant = db.execute(tenant_stmt).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    et_service = EventTypeService(db, tenant.id)
    event_type = et_service.get_by_slug(event_slug)
    if not event_type:
        raise HTTPException(status_code=404, detail="Event Type not found")

    av_service = AvailabilityService(db, tenant.id)

    lead_id_override = None

    # Validate Booking Token if present
    if payload.booking_token:
        link_stmt = select(BookingLink).where(
            BookingLink.token == payload.booking_token,
            BookingLink.status == "ACTIVE",
        )
        link = db.execute(link_stmt).scalars().first()

        if not link:
            raise HTTPException(status_code=400, detail="Invalid booking token")

        # Check expiration (ensure UTC comparison)
        if link.expires_at.replace(tzinfo=datetime.UTC) < datetime.datetime.now(
            datetime.UTC,
        ):
            link.status = "EXPIRED"
            db.commit()
            raise HTTPException(status_code=400, detail="Booking link expired")

        if link.event_slug != event_slug:
            raise HTTPException(
                status_code=400,
                detail="Token does not match event type",
            )

        lead_id_override = str(link.lead_id)

        # Mark as used
        link.status = "USED"
        db.commit()

    lead_data = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "dealContext": f"Booking: {event_type.title}",
        "notes": payload.notes,
        "id": lead_id_override,
    }

    try:
        event = av_service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=event_type.duration,
            lead_data=lead_data,
            summary=f"{event_type.title}",
        )
        return BookingConfirmationResponse(status="success", event=event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{token}/book")
def public_book_meeting(
    token: str,
    payload: BookingRequest,
    db: Annotated[Session, Depends(get_db)],
) -> BookingConfirmationResponse:
    """Handle public book meeting request."""
    link_service = LinkService(db)
    link = link_service.resolve_link(token)

    if not link or link.target_type != "booking":
        raise HTTPException(status_code=404, detail="Invalid link for booking")

    av_service = AvailabilityService(db, link.tenant_id)

    # Prepare lead data
    lead_data = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "dealContext": f"Public Booking via Link {token}",
        "notes": payload.notes,
    }

    try:
        event = av_service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=payload.duration_minutes,
            lead_data=lead_data,
            summary=f"Cita con {payload.name}",
        )
        return BookingConfirmationResponse(status="success", event=event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
