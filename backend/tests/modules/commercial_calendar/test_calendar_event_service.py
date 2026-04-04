from datetime import date

from src.modules.commercial_calendar.application.calendar_event_service import CalendarEventService


class TestCreateSingleDayEvent:
    def test_creates_one_record(self, db, tenant_id):
        service = CalendarEventService(db)
        events = service.create_event(
            country_code="PE",
            name="Dia del Trabajo",
            date_start=date(2026, 5, 1),
            tenant_id=tenant_id,
            category="feriado_nacional",
        )
        assert len(events) == 1
        assert events[0].name == "Dia del Trabajo"
        assert events[0].date == date(2026, 5, 1)
        assert events[0].tenant_id == tenant_id


class TestCreateMultiDayEvent:
    def test_creates_n_records_for_n_days(self, db, tenant_id):
        service = CalendarEventService(db)
        events = service.create_event(
            country_code="PE",
            name="Cyber Week",
            date_start=date(2026, 11, 23),
            date_end=date(2026, 11, 27),
            tenant_id=tenant_id,
            category="campaña_comercial",
        )
        assert len(events) == 5
        dates = [e.date for e in events]
        assert dates == [date(2026, 11, d) for d in range(23, 28)]


class TestListEventsTenantIsolation:
    def test_tenant_a_cannot_see_tenant_b_events(self, db, tenant_id, other_tenant_id):
        service = CalendarEventService(db)
        service.create_event(
            country_code="PE",
            name="Evento Tenant A",
            date_start=date(2026, 6, 1),
            tenant_id=tenant_id,
        )
        service.create_event(
            country_code="PE",
            name="Evento Tenant B",
            date_start=date(2026, 6, 1),
            tenant_id=other_tenant_id,
        )

        events_a = service.list_events(country_code="PE", year=2026, tenant_id=tenant_id)
        names_a = [e.name for e in events_a]
        assert "Evento Tenant A" in names_a
        assert "Evento Tenant B" not in names_a


class TestListEventsIncludesSystem:
    def test_tenant_sees_system_events(self, db, tenant_id):
        service = CalendarEventService(db)
        service.create_event(
            country_code="PE",
            name="Feriado Nacional",
            date_start=date(2026, 7, 28),
            tenant_id=None,
            category="feriado_nacional",
        )
        service.create_event(
            country_code="PE",
            name="Mi Campaña",
            date_start=date(2026, 7, 28),
            tenant_id=tenant_id,
        )

        events = service.list_events(country_code="PE", year=2026, tenant_id=tenant_id)
        names = [e.name for e in events]
        assert "Feriado Nacional" in names
        assert "Mi Campaña" in names


class TestDeleteIsSoft:
    def test_delete_sets_deleted_at_not_hard_delete(self, db, tenant_id):
        service = CalendarEventService(db)
        created = service.create_event(
            country_code="PE",
            name="Evento a borrar",
            date_start=date(2026, 8, 1),
            tenant_id=tenant_id,
        )
        event_id = created[0].id

        result = service.delete_event(event_id, tenant_id=tenant_id)
        assert result is True

        # Should not appear in listing
        events = service.list_events(country_code="PE", year=2026, tenant_id=tenant_id)
        assert all(e.id != event_id for e in events)

        # But row still exists in DB (soft deleted)
        from sqlalchemy import select
        from src.modules.commercial_calendar.infrastructure.models.calendar_event_model import CalendarEventModel
        stmt = select(CalendarEventModel).where(CalendarEventModel.id == event_id)
        row = db.execute(stmt).scalar_one_or_none()
        assert row is not None
        assert row.deleted_at is not None


class TestGetByIdTenantIsolation:
    def test_cannot_get_other_tenant_event(self, db, tenant_id, other_tenant_id):
        service = CalendarEventService(db)
        created = service.create_event(
            country_code="PE",
            name="Evento Privado",
            date_start=date(2026, 9, 1),
            tenant_id=tenant_id,
        )
        event_id = created[0].id

        # Owner can see it
        found = service.get_by_id(event_id, tenant_id=tenant_id)
        assert found is not None
        assert found.id == event_id

        # Other tenant cannot
        not_found = service.get_by_id(event_id, tenant_id=other_tenant_id)
        assert not_found is None

    def test_can_get_system_event_with_any_tenant(self, db, tenant_id):
        service = CalendarEventService(db)
        created = service.create_event(
            country_code="PE",
            name="Feriado Sistema",
            date_start=date(2026, 12, 25),
            tenant_id=None,
        )
        event_id = created[0].id

        # Any tenant can see system events
        found = service.get_by_id(event_id, tenant_id=tenant_id)
        assert found is not None
        assert found.name == "Feriado Sistema"
