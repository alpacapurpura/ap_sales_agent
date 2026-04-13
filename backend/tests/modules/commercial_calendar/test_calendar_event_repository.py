"""
Tests for CalendarEventRepository (direct repo layer).

Covers:
- create and get_by_id round-trip
- list_events: country_code + year filter
- list_events: week filter
- list_events: category filter
- list_events: tenant_id=None returns only system events
- list_events: tenant_id=<UUID> returns system + own events, not other tenant's
- bulk_create
- update mutates persistent fields
- delete sets deleted_at (soft delete), excluded from subsequent list
- exists() method
"""

import uuid
from datetime import date

from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent
from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import (
    CalendarEventRepository,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


def _make_event(
    *,
    tenant_id=TENANT_A,
    country_code: str = "PE",
    event_date: date = date(2026, 7, 1),
    name: str = "Test Event",
    category: str = "feriado_nacional",
    description: str = None,
) -> CalendarEvent:
    iso = event_date.isocalendar()
    return CalendarEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        country_code=country_code,
        date=event_date,
        year=event_date.year,
        week_number=iso[1],
        name=name,
        category=category,
        description=description,
    )


class TestCreateAndGetById:
    def test_create_and_get_round_trip(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(name="Fiestas Patrias", event_date=date(2026, 7, 28))
        created = repo.create(evt)

        found = repo.get_by_id(created.id, tenant_id=TENANT_A)
        assert found is not None
        assert found.name == "Fiestas Patrias"
        assert found.date == date(2026, 7, 28)
        assert found.tenant_id == TENANT_A

    def test_get_by_id_returns_none_for_other_tenant(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(tenant_id=TENANT_A, name="Private Event")
        created = repo.create(evt)

        result = repo.get_by_id(created.id, tenant_id=TENANT_B)
        assert result is None

    def test_get_by_id_system_event_accessible_to_any_tenant(self, db):
        repo = CalendarEventRepository(db)
        system_evt = _make_event(tenant_id=None, name="System Holiday")
        created = repo.create(system_evt)

        found = repo.get_by_id(created.id, tenant_id=TENANT_A)
        assert found is not None
        assert found.name == "System Holiday"


class TestListEvents:
    def test_list_filters_by_country_code(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        repo.create(
            _make_event(
                country_code="PE",
                name="Peru Event",
                event_date=date(2026, 3, 1),
            ),
        )
        repo.create(
            _make_event(
                country_code="CO",
                name="Colombia Event",
                event_date=date(2026, 3, 1),
            ),
        )

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_A)
        names = [e.name for e in results]
        assert "Peru Event" in names
        assert "Colombia Event" not in names

    def test_list_filters_by_year(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(event_date=date(2026, 6, 1), name="Year 2026"))
        repo.create(_make_event(event_date=date(2027, 6, 1), name="Year 2027"))

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_A)
        names = [e.name for e in results]
        assert "Year 2026" in names
        assert "Year 2027" not in names

    def test_list_filters_by_week(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        week1_date = date(2026, 1, 5)  # ISO week 2
        week10_date = date(2026, 3, 2)  # ISO week 10
        w1 = week1_date.isocalendar()[1]
        _w10 = week10_date.isocalendar()[1]

        repo.create(_make_event(event_date=week1_date, name="Week 2 Event"))
        repo.create(_make_event(event_date=week10_date, name="Week 10 Event"))

        results = repo.list_events(
            country_code="PE",
            year=2026,
            tenant_id=TENANT_A,
            week=w1,
        )
        names = [e.name for e in results]
        assert "Week 2 Event" in names
        assert "Week 10 Event" not in names

    def test_list_filters_by_category(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(category="feriado_nacional", name="Holiday"))
        repo.create(
            _make_event(
                category="campaña_comercial",
                name="Campaign",
                event_date=date(2026, 11, 27),
            ),
        )

        results = repo.list_events(
            country_code="PE",
            year=2026,
            tenant_id=TENANT_A,
            category="feriado_nacional",
        )
        names = [e.name for e in results]
        assert "Holiday" in names
        assert "Campaign" not in names

    def test_tenant_a_cannot_see_tenant_b_events(self, db):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(tenant_id=TENANT_A, name="A Event"))
        repo.create(_make_event(tenant_id=TENANT_B, name="B Event"))

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_A)
        names = [e.name for e in results]
        assert "A Event" in names
        assert "B Event" not in names

    def test_no_tenant_id_returns_only_system_events(self, db):
        repo = CalendarEventRepository(db)
        repo.create(_make_event(tenant_id=None, name="System Event"))
        repo.create(_make_event(tenant_id=TENANT_A, name="Tenant Event"))

        results = repo.list_events(country_code="PE", year=2026, tenant_id=None)
        names = [e.name for e in results]
        assert "System Event" in names
        assert "Tenant Event" not in names


class TestBulkCreate:
    def test_bulk_create_returns_all(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        events = [
            _make_event(name=f"Bulk {i}", event_date=date(2026, 8, i + 1))
            for i in range(3)
        ]
        created = repo.bulk_create(events)

        assert len(created) == 3
        names = {e.name for e in created}
        assert names == {"Bulk 0", "Bulk 1", "Bulk 2"}


class TestUpdateEvent:
    def test_update_changes_name_and_description(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(name="Original", description="Old desc")
        created = repo.create(evt)

        updated_entity = CalendarEvent(
            id=created.id,
            tenant_id=created.tenant_id,
            country_code=created.country_code,
            date=created.date,
            year=created.year,
            week_number=created.week_number,
            name="Updated Name",
            category=created.category,
            description="New desc",
        )
        result = repo.update(updated_entity)

        assert result is not None
        assert result.name == "Updated Name"
        assert result.description == "New desc"


class TestDeleteEvent:
    def test_soft_delete_excluded_from_list(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(name="Delete Me")
        created = repo.create(evt)

        repo.delete(created.id)

        results = repo.list_events(country_code="PE", year=2026, tenant_id=TENANT_A)
        assert not any(e.id == created.id for e in results)

    def test_soft_delete_preserves_row_in_db(self, db, tenant_id):
        from sqlalchemy import select

        from src.modules.commercial_calendar.infrastructure.models.calendar_event_model import (
            CalendarEventModel,
        )

        repo = CalendarEventRepository(db)
        evt = _make_event(name="Soft Delete Target")
        created = repo.create(evt)

        repo.delete(created.id)

        stmt = select(CalendarEventModel).where(CalendarEventModel.id == created.id)
        row = db.execute(stmt).scalar_one_or_none()
        assert row is not None
        assert row.deleted_at is not None

    def test_delete_nonexistent_returns_false(self, db):
        repo = CalendarEventRepository(db)
        result = repo.delete(uuid.uuid4())
        assert result is False


class TestExists:
    def test_exists_returns_true_when_found(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(name="Existing Event", event_date=date(2026, 5, 1))
        repo.create(evt)

        assert repo.exists("PE", date(2026, 5, 1), "Existing Event", TENANT_A) is True

    def test_exists_returns_false_when_not_found(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        assert repo.exists("PE", date(2026, 5, 2), "Nonexistent", TENANT_A) is False

    def test_exists_returns_false_after_soft_delete(self, db, tenant_id):
        repo = CalendarEventRepository(db)
        evt = _make_event(name="Deleted Check", event_date=date(2026, 4, 1))
        created = repo.create(evt)
        repo.delete(created.id)

        assert repo.exists("PE", date(2026, 4, 1), "Deleted Check", TENANT_A) is False
