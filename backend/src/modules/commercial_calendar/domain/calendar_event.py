from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID


@dataclass
class CalendarEvent:
    id: UUID
    country_code: str
    date: date
    year: int
    week_number: int
    name: str
    tenant_id: Optional[UUID] = None
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_system(self) -> bool:
        return self.tenant_id is None
