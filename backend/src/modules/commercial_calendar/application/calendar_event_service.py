import uuid
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent
from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.shared.domain.datetime_utils import utc_today


class CalendarEventService:
    def __init__(self, db: Session):
        self.repo = CalendarEventRepository(db)

    def list_events(
        self,
        country_code: str,
        year: int,
        tenant_id: UUID | None = None,
        week: int | None = None,
        category: str | None = None,
    ) -> list[CalendarEvent]:
        return self.repo.list_events(
            country_code=country_code,
            year=year,
            tenant_id=tenant_id,
            week=week,
            category=category,
        )

    def get_current_week_number(self) -> tuple[int, int]:
        today = utc_today()
        iso = today.isocalendar()
        return iso[1], iso[0]  # (week, year)

    def get_current_week_events(
        self,
        country_code: str,
        tenant_id: UUID | None = None,
    ) -> list[CalendarEvent]:
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
        date_end: date | None = None,
        category: str | None = None,
        description: str | None = None,
        tenant_id: UUID | None = None,
    ) -> list[CalendarEvent]:
        if date_end is None or date_end <= date_start:
            date_end = date_start

        entities: list[CalendarEvent] = []
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
        country_code: str | None = None,
        name: str | None = None,
        event_date: date | None = None,
        category: str | None = None,
        description: str | None = None,
        tenant_id: UUID | None = None,
    ) -> CalendarEvent | None:
        existing = self.repo.get_by_id(event_id, tenant_id=tenant_id)
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

    def delete_event(self, event_id: UUID, tenant_id: UUID | None = None) -> bool:
        return self.repo.delete(event_id)

    def get_by_id(
        self,
        event_id: UUID,
        tenant_id: UUID | None = None,
    ) -> CalendarEvent | None:
        return self.repo.get_by_id(event_id, tenant_id=tenant_id)
