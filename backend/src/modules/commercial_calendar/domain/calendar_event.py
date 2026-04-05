from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class CalendarEvent:
    id: UUID
    country_code: str
    date: date
    year: int
    week_number: int
    name: str
    tenant_id: UUID | None = None
    category: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_system(self) -> bool:
        return self.tenant_id is None
