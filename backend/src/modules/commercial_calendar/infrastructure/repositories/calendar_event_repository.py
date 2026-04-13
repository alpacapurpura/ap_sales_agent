"""Calendar Event Repository implementation."""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent
from src.modules.commercial_calendar.infrastructure.models.calendar_event_model import (
    CalendarEventModel,
)


class CalendarEventRepository:
    """Concrete repository implementation for calendar event."""

    def __init__(self, db: Session) -> None:
        """Initialize CalendarEventRepository."""
        self.db = db

    def _to_domain(self, model: CalendarEventModel) -> CalendarEvent:
        return CalendarEvent(
            id=model.id,
            tenant_id=model.tenant_id,
            country_code=model.country_code,
            date=model.date,
            year=model.year,
            week_number=model.week_number,
            name=model.name,
            category=model.category,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: CalendarEvent) -> CalendarEventModel:
        return CalendarEventModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            country_code=entity.country_code,
            date=entity.date,
            year=entity.year,
            week_number=entity.week_number,
            name=entity.name,
            category=entity.category,
            description=entity.description,
        )

    def list_events(
        self,
        country_code: str,
        year: int,
        tenant_id: UUID | None = None,
        week: int | None = None,
        category: str | None = None,
    ) -> list[CalendarEvent]:
        """List events."""
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.country_code == country_code,
            CalendarEventModel.year == year,
            CalendarEventModel.deleted_at == None,
        )
        if tenant_id is not None:
            stmt = stmt.where(
                (CalendarEventModel.tenant_id == None) | (CalendarEventModel.tenant_id == tenant_id),
            )
        else:
            stmt = stmt.where(CalendarEventModel.tenant_id == None)
        if week is not None:
            stmt = stmt.where(CalendarEventModel.week_number == week)
        if category is not None:
            stmt = stmt.where(CalendarEventModel.category == category)
        stmt = stmt.order_by(CalendarEventModel.date)
        result = self.db.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    def get_by_id(
        self,
        event_id: UUID,
        tenant_id: UUID | None = None,
    ) -> CalendarEvent | None:
        """Retrieve by id."""
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.id == event_id,
            CalendarEventModel.deleted_at == None,
        )
        if tenant_id is not None:
            stmt = stmt.where(
                (CalendarEventModel.tenant_id == tenant_id) | (CalendarEventModel.tenant_id == None),
            )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def create(self, entity: CalendarEvent) -> CalendarEvent:
        """Handle create operation."""
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def bulk_create(self, entities: list[CalendarEvent]) -> list[CalendarEvent]:
        """Handle bulk create operation."""
        models = [self._to_model(e) for e in entities]
        self.db.add_all(models)
        self.db.commit()
        for m in models:
            self.db.refresh(m)
        return [self._to_domain(m) for m in models]

    def update(self, entity: CalendarEvent) -> CalendarEvent | None:
        """Handle update operation."""
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.id == entity.id,
            CalendarEventModel.deleted_at == None,
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.country_code = entity.country_code
        model.date = entity.date
        model.year = entity.year
        model.week_number = entity.week_number
        model.name = entity.name
        model.category = entity.category
        model.description = entity.description
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def delete(self, event_id: UUID) -> bool:
        """Handle delete operation."""
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.id == event_id,
            CalendarEventModel.deleted_at == None,
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        model.deleted_at = datetime.now(UTC)
        self.db.commit()
        return True

    def exists(
        self,
        country_code: str,
        event_date: date,
        name: str,
        tenant_id: UUID | None,
    ) -> bool:
        """Handle exists operation."""
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.country_code == country_code,
            CalendarEventModel.date == event_date,
            CalendarEventModel.name == name,
            CalendarEventModel.deleted_at == None,
        )
        if tenant_id is None:
            stmt = stmt.where(CalendarEventModel.tenant_id == None)
        else:
            stmt = stmt.where(CalendarEventModel.tenant_id == tenant_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
