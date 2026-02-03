from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uuid

class TimeRange(BaseModel):
    start: str  # Format "HH:MM"
    end: str    # Format "HH:MM"

    @validator('start', 'end')
    def validate_time_format(cls, v):
        try:
            # Simple check, real parsing happens in service
            hour, minute = map(int, v.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            return v
        except:
            raise ValueError("Time must be in HH:MM format")

class DaySchedule(BaseModel):
    active: bool = False
    ranges: List[TimeRange] = []

class WeeklySchedule(BaseModel):
    monday: DaySchedule = Field(default_factory=DaySchedule)
    tuesday: DaySchedule = Field(default_factory=DaySchedule)
    wednesday: DaySchedule = Field(default_factory=DaySchedule)
    thursday: DaySchedule = Field(default_factory=DaySchedule)
    friday: DaySchedule = Field(default_factory=DaySchedule)
    saturday: DaySchedule = Field(default_factory=DaySchedule)
    sunday: DaySchedule = Field(default_factory=DaySchedule)

class AvailabilitySchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    is_default: bool = False
    timezone: str = "UTC"
    schedule: WeeklySchedule

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    is_default: Optional[bool] = None
    timezone: Optional[str] = None
    schedule: Optional[WeeklySchedule] = None
