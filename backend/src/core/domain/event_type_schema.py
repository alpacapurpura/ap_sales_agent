from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class SchedulingLimits(BaseModel):
    max_advance_days: int = Field(default=60)
    min_advance_hours: int = Field(default=4)

class BookingConfig(BaseModel):
    buffer_minutes: int = Field(default=30)
    max_per_day: Optional[int] = None
    guest_permissions: bool = Field(default=True)

class ConfirmationButtonConfig(BaseModel):
    enabled: bool = Field(default=False)
    text: Optional[str] = Field(default="Volver al inicio")
    url: Optional[str] = None

class EventType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    duration: int = 30 # minutes
    slug: str
    is_hidden: bool = False
    
    # Relationships
    availability_id: Optional[str] = None # If None, use default schedule
    calendar_id: Optional[str] = None # Google Calendar ID
    
    # Configs
    scheduling_limits: SchedulingLimits = Field(default_factory=SchedulingLimits)
    booking_config: BookingConfig = Field(default_factory=BookingConfig)
    confirmation_button: ConfirmationButtonConfig = Field(default_factory=ConfirmationButtonConfig)

class EventTypeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    slug: Optional[str] = None
    is_hidden: Optional[bool] = None
    availability_id: Optional[str] = None
    calendar_id: Optional[str] = None
    scheduling_limits: Optional[SchedulingLimits] = None
    booking_config: Optional[BookingConfig] = None
    confirmation_button: Optional[ConfirmationButtonConfig] = None
