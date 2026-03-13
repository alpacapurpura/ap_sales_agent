from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from uuid import UUID

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

from src.modules.scheduling.infrastructure.repositories.appointment_repository import AppointmentRepository
from src.modules.crm.infrastructure.models.lead_model import LeadModel

router = APIRouter(tags=["Scheduling - Agenda"])

class AgendaItem(BaseModel):
    id: UUID
    summary: str
    start_time: datetime
    end_time: datetime
    status: str
    lead_name: Optional[str] = None
    meeting_link: Optional[str] = None

@router.get("/", response_model=List[AgendaItem])
async def get_agenda(
    range: Literal["today", "week"] = "today",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    repo = AppointmentRepository(db)
    now = datetime.now(timezone.utc)
    
    if range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    else: # week
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        
    appointments = repo.get_appointments_by_date_range(start, end, user.tenant_id)
    
    # Enrich with Lead Names (NOTE: Cross-module dependency, consider moving to a service)
    lead_ids = [a.lead_id for a in appointments if a.lead_id]
    lead_map = {}
    if lead_ids:
        # Use joinedload to fetch Customer Profile efficiently
        leads = db.query(LeadModel).options(
            joinedload(LeadModel.customer)
        ).filter(LeadModel.id.in_(lead_ids)).all()
        
        for l in leads:
            # Try to get name from Customer (SSOT), then fallback to Lead profile_data
            customer_name = l.customer.full_name if l.customer else None
            profile = l.profile_data or {}
            
            name = customer_name or profile.get('full_name') or profile.get('name') or "Unknown Lead"
            lead_map[l.id] = name
            
    return [
        AgendaItem(
            id=a.id,
            summary=a.summary,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status.value,
            meeting_link=a.meeting_link,
            lead_name=lead_map.get(a.lead_id, "Unknown Lead")
        ) for a in appointments
    ]
