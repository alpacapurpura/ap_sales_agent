"""
Tests for CalendarEventService.update_event.

Covers:
- Full update: name, country_code, date, category, description
- Partial update: only name, other fields unchanged
- Date change recalculates year and week_number
- Update returns None for non-existent event_id
- Multi-day event: updating one day does not affect sibling days
"""

import uuid
from datetime import date

from src.modules.commercial_calendar.application.calendar_event_service import (
    CalendarEventService,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


class TestUpdateEvent:
    def test_full_update_changes_all_fields(self, db, tenant_id):
        svc = CalendarEventService(db)
        created = svc.create_event(
            country_code="PE",
            name="Black Friday",
            date_start=date(2026, 11, 27),
            tenant_id=tenant_id,
            category="campaña_comercial",
            description="Viernes negro",
        )
        event_id = created[0].id

        updated = svc.update_event(
            event_id=event_id,
            name="Cyber Monday",
            event_date=date(2026, 11, 30),
            category="oferta_especial",
            description="Lunes digital",
            country_code="CO",
            tenant_id=tenant_id,
        )

        assert updated is not None
        assert updated.name == "Cyber Monday"
        assert updated.date == date(2026, 11, 30)
        assert updated.category == "oferta_especial"
        assert updated.description == "Lunes digital"
        assert updated.country_code == "CO"

    def test_partial_update_name_only(self, db, tenant_id):
        """Only name changes; other fields remain from original."""
        svc = CalendarEventService(db)
        created = svc.create_event(
            country_code="PE",
            name="Evento Original",
            date_start=date(2026, 6, 15),
            tenant_id=tenant_id,
            category="feriado_nacional",
            description="Descripcion original",
        )
        event_id = created[0].id

        updated = svc.update_event(
            event_id=event_id,
            name="Evento Renombrado",
            tenant_id=tenant_id,
        )

        assert updated.name == "Evento Renombrado"
        assert updated.date == date(2026, 6, 15)
        assert updated.category == "feriado_nacional"
        assert updated.description == "Descripcion original"
        assert updated.country_code == "PE"

    def test_date_change_recalculates_year_and_week(self, db, tenant_id):
        """Updating the date recalculates year and week_number correctly."""
        svc = CalendarEventService(db)
        created = svc.create_event(
            country_code="PE",
            name="Movable Event",
            date_start=date(2026, 1, 5),  # Week 2
            tenant_id=tenant_id,
        )
        event_id = created[0].id

        new_date = date(2026, 12, 31)  # Week 53 in ISO
        updated = svc.update_event(
            event_id=event_id,
            event_date=new_date,
            tenant_id=tenant_id,
        )

        assert updated.date == new_date
        assert updated.year == 2026
        assert updated.week_number == new_date.isocalendar()[1]

    def test_update_nonexistent_returns_none(self, db, tenant_id):
        svc = CalendarEventService(db)
        result = svc.update_event(
            event_id=uuid.uuid4(),
            name="Ghost Event",
            tenant_id=tenant_id,
        )
        assert result is None

    def test_multi_day_update_one_sibling_unchanged(self, db, tenant_id):
        """In a multi-day event, updating one day does not change the other."""
        svc = CalendarEventService(db)
        created = svc.create_event(
            country_code="PE",
            name="Cyber Week",
            date_start=date(2026, 11, 23),
            date_end=date(2026, 11, 24),  # 2 days
            tenant_id=tenant_id,
        )
        assert len(created) == 2
        first_id = created[0].id
        second_id = created[1].id

        svc.update_event(event_id=first_id, name="Day 1 Updated", tenant_id=tenant_id)

        second = svc.get_by_id(second_id, tenant_id=tenant_id)
        assert second.name == "Cyber Week"  # unchanged
