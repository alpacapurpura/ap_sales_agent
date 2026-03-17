from typing import Optional, Dict, Any
from src.shared.domain.base_entity import BaseEntity
from pydantic import Field
import uuid

class SchedulingLimits(BaseEntity):
    max_advance_days: int = 60
    min_advance_hours: int = 4

class BookingConfig(BaseEntity):
    buffer_minutes: int = 30
    max_per_day: Optional[int] = None
    guest_permissions: bool = True

class ConfirmationButton(BaseEntity):
    enabled: bool = False

class EventType(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    description: Optional[str] = None
    duration: int = 30
    is_hidden: bool = False
    
    scheduling_limits: SchedulingLimits = Field(default_factory=SchedulingLimits)
    booking_config: BookingConfig = Field(default_factory=BookingConfig)
    confirmation_button: ConfirmationButton = Field(default_factory=ConfirmationButton)
    
    metadata_info: Dict[str, Any] = {}

class EventTypeUpdate(BaseEntity):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    is_hidden: Optional[bool] = None
    
    scheduling_limits: Optional[SchedulingLimits] = None
    booking_config: Optional[BookingConfig] = None
    confirmation_button: Optional[ConfirmationButton] = None
    
    metadata_info: Optional[Dict[str, Any]] = None
