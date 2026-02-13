from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
import datetime
from typing import List, Optional, Dict, Any
import structlog

from src.services.database import get_db
from src.api.dependencies import get_current_user
from src.services.db.models.user import User
from src.services.db.models.channel_connection import ChannelConnection
from src.services.db.models.link import ShareableLink
from src.services.db.models.business import BookingLink
from src.services.db.models.lead import Lead
import secrets
from src.channels.google_calendar import GoogleCalendarAdapter
from src.core.services.availability_service import AvailabilityService
from src.core.services.link_service import LinkService
from src.core.domain.availability_schema import AvailabilitySchedule, ScheduleUpdate

router = APIRouter(prefix="/calendar", tags=["calendar"])
logger = structlog.get_logger()

# --- Schemas ---
class CalendarStatusResponse(BaseModel):
    is_connected: bool
    email: Optional[str] = None
    booking_link: Optional[str] = None

class BookMeetingRequest(BaseModel):
    slot_time: datetime.datetime
    duration_minutes: int = 30
    lead_data: Dict[str, Any] # {id, name, email, dealContext...}

class AppointmentResponse(BaseModel):
    id: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    meet_link: Optional[str] = None
    attendees: List[str] = []

class CreateBookingLinkRequest(BaseModel):
    lead_id: str
    event_slug: str
    expiration_days: int = 7
    
# --- Endpoints ---

@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Get the Google OAuth2 authorization URL.
    """
    url, state = GoogleCalendarAdapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}

@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exchange the authorization code for tokens and save connection.
    """
    try:
        creds_data = GoogleCalendarAdapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticación con Google")

    # Get email from service to identify
    try:
        adapter = GoogleCalendarAdapter(creds_data)
        service = adapter.get_service()
        # calendarList().get(calendarId='primary') gives some info, or assume primary email
        calendar = service.calendars().get(calendarId='primary').execute()
        email = calendar.get('id')
    except Exception as e:
        logger.warning("failed_to_get_calendar_info", error=str(e))
        email = "Unknown"

    # Save to DB
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'google_calendar'
    ).first()

    if connection:
        connection.credentials = creds_data
        connection.config = {"email": email}
        connection.is_active = True
    else:
        connection = ChannelConnection(
            tenant_id=user.tenant_id,
            channel_type='google_calendar',
            credentials=creds_data,
            config={"email": email},
            is_active=True
        )
        db.add(connection)
    
    db.commit()
    return {"status": "connected", "email": email}

@router.get("/status", response_model=CalendarStatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if Google Calendar is connected and get active booking link.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'google_calendar',
        ChannelConnection.is_active.is_(True)
    ).first()
    
    # Get active booking link
    stmt = select(ShareableLink).where(
        ShareableLink.tenant_id == user.tenant_id,
        ShareableLink.target_type == 'booking',
        ShareableLink.is_active.is_(True)
    ).order_by(ShareableLink.created_at.desc())
    link = db.execute(stmt).scalars().first()
    
    if not connection:
        return CalendarStatusResponse(
            is_connected=False,
            booking_link=f"/visit/{link.token}" if link else None
        )
        
    return CalendarStatusResponse(
        is_connected=True, 
        email=connection.config.get("email"),
        booking_link=f"/visit/{link.token}" if link else None
    )

@router.post("/link")
async def create_booking_link(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Generate a new public booking link.
    """
    service = LinkService(db)
    # Deactivate old links? Or keep them? 
    # Requirement says "revocation mechanism". 
    # Let's just create a new one. The UI can show the latest.
    
    link = service.create_link(
        tenant_id=user.tenant_id,
        target_type="booking",
        created_by=user.id
    )
    
    return {"token": link.token, "url": f"/visit/{link.token}"}

@router.post("/personalized-link")
async def create_personalized_link(
    payload: CreateBookingLinkRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Generate a personalized booking link for a specific lead.
    """
    # Validate lead exists
    lead = db.query(Lead).filter(Lead.id == payload.lead_id, Lead.tenant_id == user.tenant_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # Generate token
    token = secrets.token_urlsafe(16)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=payload.expiration_days)
    
    link = BookingLink(
        tenant_id=user.tenant_id,
        lead_id=payload.lead_id,
        event_slug=payload.event_slug,
        token=token,
        expires_at=expires_at,
        status="ACTIVE"
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    
    # Construct URL
    tenant_slug = user.tenant.slug if user.tenant else "unknown"
    
    return {
        "token": link.token,
        "url": f"/book/{tenant_slug}/{payload.event_slug}?token={link.token}",
        "expires_at": link.expires_at
    }

@router.delete("/disconnect")
async def disconnect(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Google Calendar.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'google_calendar'
    ).first()
    
    if connection:
        db.delete(connection)
        db.commit()
        
    return {"status": "disconnected"}

@router.post("/test")
async def test_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test Calendar connection by listing busy periods.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'google_calendar',
        ChannelConnection.is_active.is_(True)
    ).first()
    
    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Calendario no conectado")
        
    try:
        adapter = GoogleCalendarAdapter(connection.credentials)
        # Test fetching busy periods for today
        now = datetime.datetime.now(datetime.timezone.utc)
        end = now + datetime.timedelta(days=1)
        busy = adapter.list_busy_periods(now, end)
        return {"status": "ok", "message": "Conexión exitosa", "data": {"busy_slots": len(busy), "email": connection.config.get("email")}}
    except Exception as e:
        logger.error("calendar_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

@router.get("/slots")
async def get_slots(
    start_date: datetime.date,
    end_date: datetime.date,
    duration: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get available time slots based on Google Calendar free/busy.
    """
    service = AvailabilityService(db, user.tenant_id)
    slots = service.get_available_slots(start_date, end_date, duration_minutes=duration)
    return {"slots": slots}

@router.post("/book")
async def book_meeting(
    payload: BookMeetingRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Book a meeting on Google Calendar.
    """
    service = AvailabilityService(db, user.tenant_id)
    try:
        event = service.book_meeting(
            slot_time=payload.slot_time,
            duration_minutes=payload.duration_minutes,
            lead_data=payload.lead_data
        )
        return {"status": "booked", "event_link": event.get('htmlLink')}
    except Exception as e:
        logger.error("booking_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointments")
async def list_appointments(
    start_date: datetime.date,
    end_date: datetime.date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List appointments for the dashboard.
    """
    service = AvailabilityService(db, user.tenant_id)
    events = service.list_appointments(start_date, end_date)
    
    # Map to simplified response
    result = []
    for e in events:
        start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
        end = e.get('end', {}).get('dateTime') or e.get('end', {}).get('date')
        
        meet_link = e.get('hangoutLink') # Simplest way to get meet link
        
        result.append({
            "id": e.get('id'),
            "summary": e.get('summary'),
            "start": start,
            "end": end,
            "meet_link": meet_link,
            "attendees": [a.get('email') for a in e.get('attendees', [])]
        })
    return result

# --- Availability Management Endpoints ---

@router.get("/schedules", response_model=List[AvailabilitySchedule])
async def list_schedules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AvailabilityService(db, user.tenant_id)
    return service.list_schedules()

@router.post("/schedules", response_model=AvailabilitySchedule)
async def create_schedule(
    schedule: AvailabilitySchedule,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AvailabilityService(db, user.tenant_id)
    return service.create_schedule(schedule)

@router.patch("/schedules/{schedule_id}", response_model=AvailabilitySchedule)
async def update_schedule(
    schedule_id: str,
    update: ScheduleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AvailabilityService(db, user.tenant_id)
    updated = service.update_schedule(schedule_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return updated

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AvailabilityService(db, user.tenant_id)
    deleted = service.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found or is last remaining")
    return {"status": "deleted"}
