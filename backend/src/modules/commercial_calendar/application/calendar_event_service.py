import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent
from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import CalendarEventRepository


class CalendarEventService:
    def __init__(self, db: Session):
        self.repo = CalendarEventRepository(db)

    def list_events(
        self,
        country_code: str,
        year: int,
        tenant_id: Optional[UUID] = None,
        week: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[CalendarEvent]:
        return self.repo.list_events(
            country_code=country_code,
            year=year,
            tenant_id=tenant_id,
            week=week,
            category=category,
        )

    def get_current_week_number(self) -> Tuple[int, int]:
        today = date.today()
        iso = today.isocalendar()
        return iso[1], iso[0]  # (week, year)

    def get_current_week_events(
        self,
        country_code: str,
        tenant_id: Optional[UUID] = None,
    ) -> List[CalendarEvent]:
        week, year = self.get_current_week_number()
        return self.repo.list_events(
            country_code=country_code,
            year=year,
            tenant_id=tenant_id,
            week=week,
        )

    def create_event(
        self,
        country_code: str,
        name: str,
        date_start: date,
        date_end: Optional[date] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> List[CalendarEvent]:
        if date_end is None or date_end <= date_start:
            date_end = date_start

        entities: List[CalendarEvent] = []
        current = date_start
        while current <= date_end:
            iso = current.isocalendar()
            entity = CalendarEvent(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                country_code=country_code,
                date=current,
                year=current.year,
                week_number=iso[1],
                name=name,
                category=category,
                description=description,
            )
            entities.append(entity)
            current += timedelta(days=1)

        return self.repo.bulk_create(entities)

    def update_event(
        self,
        event_id: UUID,
        country_code: Optional[str] = None,
        name: Optional[str] = None,
        event_date: Optional[date] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[CalendarEvent]:
        existing = self.repo.get_by_id(event_id)
        if existing is None:
            return None

        updated = CalendarEvent(
            id=existing.id,
            tenant_id=existing.tenant_id,
            country_code=country_code if country_code is not None else existing.country_code,
            date=event_date if event_date is not None else existing.date,
            year=(event_date if event_date is not None else existing.date).year,
            week_number=(event_date if event_date is not None else existing.date).isocalendar()[1],
            name=name if name is not None else existing.name,
            category=category if category is not None else existing.category,
            description=description if description is not None else existing.description,
        )
        return self.repo.update(updated)

    def delete_event(self, event_id: UUID) -> bool:
        return self.repo.delete(event_id)

    def get_by_id(self, event_id: UUID) -> Optional[CalendarEvent]:
        return self.repo.get_by_id(event_id)
