"""Calendar Events API endpoints."""

from datetime import date as DateType  # noqa: N812 — field named 'date' shadows type
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class CalendarEventCreate(BaseModel):
    """Schema for calendar event create."""

    model_config = ConfigDict(from_attributes=True)

    country_code: str
    name: str
    date_start: DateType
    date_end: DateType | None = None
    category: str | None = None
    description: str | None = None

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code."""
        if len(v) != 2:
            msg = "country_code must be a 2-letter ISO code"
            raise ValueError(msg)
        return v.upper()


class CalendarEventUpdate(BaseModel):
    """Schema for calendar event update."""

    model_config = ConfigDict(from_attributes=True)

    country_code: str | None = None
    name: str | None = None
    date: DateType | None = None
    category: str | None = None
    description: str | None = None

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        """Validate country code."""
        if v is not None and len(v) != 2:
            msg = "country_code must be a 2-letter ISO code"
            raise ValueError(msg)
        return v.upper() if v else v


class CalendarEventResponse(BaseModel):
    """Schema for calendar event response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    country_code: str
    date: DateType
    year: int
    week_number: int
    name: str
    category: str | None
    description: str | None
    is_system: bool
    created_at: datetime | None
    updated_at: datetime | None
