from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime

from src.core.database import get_db
from src.shared.links.service import LinkService
from src.modules.scheduling.application.services.availability_service import AvailabilityService
from src.modules.scheduling.application.services.event_type_service import EventTypeService
from src.modules.iam.domain.tenant import Tenant
from src.modules.scheduling.infrastructure.models.booking_link import BookingLink
from src.modules.scheduling.api.dto.public_links import LinkResolveResponse, BookingRequest, EventTypeResolveResponse, BookingLinkResolveResponse

router = APIRouter()

# --- Endpoints ---

@router.get("/booking-links/{token}", response_model=BookingLinkResolveResponse)
def resolve_booking_link(token: str, db: Session = Depends(get_db)):
    link = db.query(BookingLink).filter(
        BookingLink.token == token,
        BookingLink.status == 'ACTIVE'
    ).first()
    
    if not link:
         raise HTTPException(status_code=404, detail="Link invalid or expired")
    
    # Check expiration
    if link.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
        link.status = 'EXPIRED'
        db.commit()
        raise HTTPException(status_code=404, detail="Link expired")
        
    return BookingLinkResolveResponse(
        valid=True,
        event_slug=link.event_slug,
        lead_name=link.lead.full_name if link.lead else None,
        lead_email=link.lead.email if link.lead else None,
        lead_phone=link.lead.phone if link.lead else None,
        lead_id=str(link.lead_id),
        expires_at=link.expires_at
    )

@router.get("/resolve/{token}", response_model=LinkResolveResponse)
def resolve_link(token: str, db: Session = Depends(get_db)):
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
        params=link.params
    )

@router.get("/{token}/slots")
def get_public_slots(
    token: str, 
    start_date: datetime.date, 
    end_date: datetime.date,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to fetch slots via token authentication.
    """
    link_service = LinkService(db)
    link = link_service.resolve_link(token)
    
    if not link or link.target_type != 'booking':
        raise HTTPException(status_code=404, detail="Invalid link for booking")
        
    av_service = AvailabilityService(db, link.tenant_id)
    
    try:
        slots = av_service.get_available_slots(start_date, end_date)
        return {"slots": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Event Type Public Endpoints ---

@router.get("/event-types/{tenant_slug}/{event_slug}", response_model=EventTypeResolveResponse)
def resolve_event_type(
    tenant_slug: str,
    event_slug: str,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
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
        tenant_id=str(tenant.id)
    )

@router.get("/event-types/{tenant_slug}/{event_slug}/slots")
def get_event_type_slots(
    tenant_slug: str,
    event_slug: str,
    start_date: datetime.date,
    end_date: datetime.date,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    et_service = EventTypeService(db, tenant.id)
    event_type = et_service.get_by_slug(event_slug)
    if not event_type:
        raise HTTPException(status_code=404, detail="Event Type not found")

    av_service = AvailabilityService(db, tenant.id)
    try:
        slots = av_service.get_event_type_slots(event_type, start_date, end_date)
        return {"slots": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event-types/{tenant_slug}/{event_slug}/book")
def book_event_type(
    tenant_slug: str,
    event_slug: str,
    payload: BookingRequest,
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
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
        link = db.query(BookingLink).filter(
            BookingLink.token == payload.booking_token,
            BookingLink.status == 'ACTIVE'
        ).first()
        
        if not link:
             raise HTTPException(status_code=400, detail="Invalid booking token")
             
        # Check expiration (ensure UTC comparison)
        if link.expires_at.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(datetime.timezone.utc):
            link.status = 'EXPIRED'
            db.commit()
            raise HTTPException(status_code=400, detail="Booking link expired")
            
        if link.event_slug != event_slug:
             raise HTTPException(status_code=400, detail="Token does not match event type")
             
        lead_id_override = str(link.lead_id)
        
        # Mark as used
        link.status = 'USED'
        db.commit()

    lead_data = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "dealContext": f"Booking: {event_type.title}",
        "notes": payload.notes,
        "id": lead_id_override
    }
    
    try:
        event = av_service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=event_type.duration,
            lead_data=lead_data,
            summary=f"{event_type.title}"
        )
        return {"status": "success", "event": event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{token}/book")
def public_book_meeting(
    token: str,
    payload: BookingRequest,
    db: Session = Depends(get_db)
):
    link_service = LinkService(db)
    link = link_service.resolve_link(token)
    
    if not link or link.target_type != 'booking':
        raise HTTPException(status_code=404, detail="Invalid link for booking")
        
    av_service = AvailabilityService(db, link.tenant_id)
    
    # Prepare lead data
    lead_data = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "dealContext": f"Public Booking via Link {token}",
        "notes": payload.notes
    }
    
    try:
        event = av_service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=payload.duration_minutes,
            lead_data=lead_data,
            summary=f"Cita con {payload.name}"
        )
        return {"status": "success", "event": event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

