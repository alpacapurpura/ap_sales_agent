from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CalendarEventCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country_code: str
    name: str
    date_start: date
    date_end: Optional[date] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if len(v) != 2:
            raise ValueError("country_code must be a 2-letter ISO code")
        return v.upper()


class CalendarEventUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country_code: Optional[str] = None
    name: Optional[str] = None
    date: Optional[date] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) != 2:
            raise ValueError("country_code must be a 2-letter ISO code")
        return v.upper() if v else v


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: Optional[UUID]
    country_code: str
    date: date
    year: int
    week_number: int
    name: str
    category: Optional[str]
    description: Optional[str]
    is_system: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
