from typing import Dict, Any, Optional
from pydantic import Field
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.scheduling.domain.enums import AppointmentStatus

class Appointment(BaseEntity):
    id: UUID
    tenant_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    
    summary: str
    start_time: datetime
    end_time: datetime
    
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    meeting_link: Optional[str] = None
    
    external_event_id: Optional[str] = None # Google Calendar ID
    metadata_info: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
