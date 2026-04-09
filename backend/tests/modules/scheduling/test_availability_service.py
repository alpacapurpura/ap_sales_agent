"""
Tests for AvailabilityService.

Covers:
- Default schedule creation when tenant has no schedules
- Schedule migration from legacy weekly_hours / is_active / slots keys
- get_available_slots slot generation from WeeklySchedule (no Google Calendar)
- Slot filtering for inactive days
- Schedule CRUD: create, update, delete
"""

import datetime
import uuid

import pytest

from src.modules.scheduling.application.services.availability_service import (
    AvailabilityService,
)
from src.modules.scheduling.domain.availability_schema import (
    AvailabilitySchedule,
    DaySchedule,
    ScheduleUpdate,
    TimeRange,
    WeeklySchedule,
)

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _make_schedule(
    *,
    name: str = "Test Schedule",
    timezone: str = "UTC",
    is_default: bool = True,
    monday_active: bool = True,
) -> AvailabilitySchedule:
    ranges = [TimeRange(start="09:00", end="17:00")]
    return AvailabilitySchedule(
        name=name,
        timezone=timezone,
        is_default=is_default,
        schedule=WeeklySchedule(
            monday=DaySchedule(
                active=monday_active, ranges=ranges if monday_active else []
            ),
            tuesday=DaySchedule(active=False, ranges=[]),
            wednesday=DaySchedule(active=False, ranges=[]),
            thursday=DaySchedule(active=False, ranges=[]),
            friday=DaySchedule(active=False, ranges=[]),
            saturday=DaySchedule(active=False, ranges=[]),
            sunday=DaySchedule(active=False, ranges=[]),
        ),
    )


@pytest.fixture
def tenant(db):
    """Seed a TenantModel into the DB and return it."""
    from tests.factories import TenantFactory

    t = TenantFactory.build(
        id=TENANT_ID, name="Scheduling Tenant", slug="scheduling-tenant", config_json={}
    )
    db.add(t)
    db.commit()
    return t


class TestDefaultScheduleCreation:
    def test_creates_default_when_none_exist(self, db, tenant):
        """list_schedules auto-creates a default Mon-Fri 09-17 schedule."""
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None  # Disable Google Calendar

        schedules = svc.list_schedules()

        assert len(schedules) == 1
        assert schedules[0].is_default is True
        assert schedules[0].schedule.monday.active is True
        assert schedules[0].schedule.saturday.active is False

    def test_default_schedule_uses_tenant_timezone(self, db, tenant):
        """Default schedule timezone matches the tenant's configured timezone."""
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedules = svc.list_schedules()

        # Tenant has no explicit timezone set → falls back to "UTC"
        assert schedules[0].timezone == "UTC"

    def test_default_schedule_uses_custom_tenant_timezone(self, db):
        """Default schedule uses the tenant's timezone when explicitly set."""
        from tests.factories import TenantFactory

        custom_tz_tenant_id = uuid.UUID("aaaa0000-0000-0000-0000-000000000099")
        t = TenantFactory.build(
            id=custom_tz_tenant_id,
            name="Bogota Tenant",
            slug="bogota-tenant",
            config_json={},
            timezone="America/Bogota",
        )
        db.add(t)
        db.commit()

        svc = AvailabilityService(db, custom_tz_tenant_id)
        svc.adapter = None

        schedules = svc.list_schedules()

        assert schedules[0].timezone == "America/Bogota"


class TestScheduleMigration:
    def test_migrates_weekly_hours_to_schedule(self, db, tenant):
        """Legacy weekly_hours key is renamed to schedule."""
        legacy_data = {
            "id": str(uuid.uuid4()),
            "name": "Legado",
            "timezone": "UTC",
            "is_default": True,
            "weekly_hours": {
                "monday": {
                    "active": True,
                    "ranges": [{"start": "08:00", "end": "16:00"}],
                },
            },
        }
        tenant.config_json = {"availability_schedules": [legacy_data]}
        db.commit()

        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedules = svc.list_schedules()

        assert len(schedules) == 1
        assert schedules[0].schedule.monday.active is True

    def test_migrates_is_active_to_active(self, db, tenant):
        """Legacy is_active key in day schedule is renamed to active."""
        legacy_data = {
            "id": str(uuid.uuid4()),
            "name": "Legado 2",
            "timezone": "UTC",
            "is_default": True,
            "schedule": {
                "monday": {
                    "is_active": True,
                    "ranges": [{"start": "09:00", "end": "17:00"}],
                },
            },
        }
        tenant.config_json = {"availability_schedules": [legacy_data]}
        db.commit()

        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedules = svc.list_schedules()

        assert len(schedules) == 1
        assert schedules[0].schedule.monday.active is True


class TestGetAvailableSlots:
    def test_generates_slots_for_active_day(self, db, tenant):
        """Slots are generated for active weekdays only."""
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(monday_active=True)
        svc.create_schedule(schedule)

        # 2026-01-05 = Monday
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 1, 5)

        slots = svc.get_available_slots(
            start_date=start,
            end_date=end,
            duration_minutes=60,
            schedule_override=schedule,
        )

        assert len(slots) == 8  # 09:00-17:00 in 60-min slots

    def test_no_slots_for_inactive_day(self, db, tenant):
        """No slots are returned for inactive days."""
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(monday_active=False)
        svc.create_schedule(schedule)

        start = datetime.date(2026, 1, 5)  # Monday
        end = datetime.date(2026, 1, 5)

        slots = svc.get_available_slots(
            start_date=start,
            end_date=end,
            duration_minutes=30,
            schedule_override=schedule,
        )

        assert slots == []

    def test_slot_count_for_30_min_duration(self, db, tenant):
        """A 09-17 range with 30-min slots yields 16 slots."""
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(monday_active=True)
        svc.create_schedule(schedule)

        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 1, 5)

        slots = svc.get_available_slots(
            start_date=start,
            end_date=end,
            duration_minutes=30,
            schedule_override=schedule,
        )

        assert len(slots) == 16


class TestScheduleCRUD:
    def test_create_and_list(self, db, tenant):
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(name="My Schedule")
        created = svc.create_schedule(schedule)

        assert created.name == "My Schedule"
        all_schedules = svc.list_schedules()
        assert any(s.name == "My Schedule" for s in all_schedules)

    def test_update_name(self, db, tenant):
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(name="Old Name")
        svc.create_schedule(schedule)

        update = ScheduleUpdate(name="New Name")
        updated = svc.update_schedule(schedule.id, update)

        assert updated is not None
        assert updated.name == "New Name"

    def test_delete_schedule(self, db, tenant):
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        schedule = _make_schedule(name="To Delete")
        svc.create_schedule(schedule)

        result = svc.delete_schedule(schedule.id)
        assert result is True

        remaining = svc.list_schedules()
        assert not any(s.name == "To Delete" for s in remaining)

    def test_delete_nonexistent_returns_false(self, db, tenant):
        svc = AvailabilityService(db, TENANT_ID)
        svc.adapter = None

        result = svc.delete_schedule("nonexistent-id")
        assert result is False
