"""Tenant isolation tests for CalendarEventRepository.

Proves at the repository level that:
- Tenant B cannot list events owned by Tenant A
- get_by_id with wrong tenant returns None
- System events (tenant_id=None) are visible to any tenant
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from luana_core_commercial_calendar.domain.calendar_event import CalendarEvent
from luana_core_commercial_calendar.infrastructure.repositories.calendar_event_repository import (
    CalendarEventRepository,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


def _make_event(
    tenant_id: uuid.UUID | None,
    name: str = "Test Event",
    country_code: str = "PE",
    event_date: date = date(2026, 8, 1),
) -> CalendarEvent:
    return CalendarEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        country_code=country_code,
        date=event_date,
        year=event_date.year,
        week_number=event_date.isocalendar()[1],
        name=name,
        category="test",
        description="Test description",
    )


class TestListEventsTenantIsolation:
    def test_tenant_b_cannot_list_tenant_a_events(self, db: Session):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(TENANT_A, name="Evento A"))

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_B)
        names = [r.name for r in results]
        assert "Evento A" not in names

    def test_tenant_a_sees_own_events(self, db: Session):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(TENANT_A, name="Evento A"))

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_A)
        names = [r.name for r in results]
        assert "Evento A" in names

    def test_tenant_sees_system_events_but_not_other_tenant(self, db: Session):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(None, name="Sistema"))
        repo.create(_make_event(TENANT_A, name="Privado A"))

        # Tenant B should see system events but NOT Tenant A's private event
        results_b = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_B)
        names_b = [r.name for r in results_b]
        assert "Sistema" in names_b
        assert "Privado A" not in names_b


class TestGetByIdTenantIsolation:
    def test_get_by_id_wrong_tenant_returns_none(self, db: Session):
        repo = CalendarEventRepository(db)
        created = repo.create(_make_event(TENANT_A, name="Evento A"))

        result = repo.get_by_id(created.id, tenant_id=TENANT_B)
        assert result is None

    def test_get_by_id_correct_tenant_returns_event(self, db: Session):
        repo = CalendarEventRepository(db)
        created = repo.create(_make_event(TENANT_A, name="Evento A"))

        result = repo.get_by_id(created.id, tenant_id=TENANT_A)
        assert result is not None
        assert result.id == created.id
        assert result.tenant_id == TENANT_A

    def test_get_by_id_system_event_visible_to_any_tenant(self, db: Session):
        repo = CalendarEventRepository(db)
        created = repo.create(_make_event(None, name="Feriado Nacional"))

        # System event (tenant_id=None) should be accessible by any tenant
        result_a = repo.get_by_id(created.id, tenant_id=TENANT_A)
        assert result_a is not None
        assert result_a.name == "Feriado Nacional"

        result_b = repo.get_by_id(created.id, tenant_id=TENANT_B)
        assert result_b is not None

    def test_get_by_id_nonexistent_returns_none(self, db: Session):
        repo = CalendarEventRepository(db)
        result = repo.get_by_id(uuid.uuid4(), tenant_id=TENANT_A)
        assert result is None
