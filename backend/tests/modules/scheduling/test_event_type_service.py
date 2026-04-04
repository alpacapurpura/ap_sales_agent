"""
Tests for EventTypeService.

Covers:
- list_event_types returns empty list when none exist
- create_event_type persists and returns the entity
- slug uniqueness enforcement on create
- get_event_type and get_by_slug lookup
- update_event_type partial updates
- delete_event_type
- Legacy migration: is_active -> is_hidden
"""

import uuid

import pytest

from src.modules.scheduling.application.services.event_type_service import EventTypeService
from src.modules.scheduling.domain.event_type_schema import EventType, EventTypeUpdate

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _make_event_type(
    title: str = "Consulta 30 min",
    slug: str = "consulta-30",
    duration: int = 30,
) -> EventType:
    return EventType(title=title, slug=slug, duration=duration)


@pytest.fixture
def tenant(db):
    from tests.factories import TenantFactory

    t = TenantFactory.build(
        id=TENANT_ID,
        name="ET Tenant",
        slug="et-tenant",
        config_json={},
    )
    db.add(t)
    db.commit()
    return t


class TestListEventTypes:
    def test_returns_empty_list_when_none_exist(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        result = svc.list_event_types()
        assert result == []


class TestCreateEventType:
    def test_create_persists_and_returns_entity(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        et = _make_event_type(title="Sesión 60", slug="sesion-60", duration=60)
        created = svc.create_event_type(et)

        assert created.title == "Sesión 60"
        assert created.slug == "sesion-60"
        assert created.duration == 60

        all_ets = svc.list_event_types()
        assert any(e.slug == "sesion-60" for e in all_ets)

    def test_slug_uniqueness_auto_suffix(self, db, tenant):
        """Duplicate slug gets a numeric suffix automatically."""
        svc = EventTypeService(db, TENANT_ID)
        et1 = _make_event_type(title="Consulta", slug="consulta")
        et2 = _make_event_type(title="Consulta 2", slug="consulta")

        svc.create_event_type(et1)
        created2 = svc.create_event_type(et2)

        assert created2.slug == "consulta-1"


class TestGetEventType:
    def test_get_by_id_returns_correct_entity(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        et = _make_event_type(title="Intro Call", slug="intro-call")
        created = svc.create_event_type(et)

        found = svc.get_event_type(created.id)
        assert found is not None
        assert found.title == "Intro Call"

    def test_get_by_id_returns_none_for_unknown(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        result = svc.get_event_type("nonexistent-id")
        assert result is None

    def test_get_by_slug(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        et = _make_event_type(title="Discovery", slug="discovery")
        svc.create_event_type(et)

        found = svc.get_by_slug("discovery")
        assert found is not None
        assert found.title == "Discovery"

    def test_get_by_slug_returns_none_for_unknown(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        result = svc.get_by_slug("unknown-slug")
        assert result is None


class TestUpdateEventType:
    def test_update_title_and_duration(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        et = _make_event_type(title="Short Call", slug="short-call", duration=15)
        created = svc.create_event_type(et)

        update = EventTypeUpdate(title="Long Call", duration=60)
        updated = svc.update_event_type(created.id, update)

        assert updated is not None
        assert updated.title == "Long Call"
        assert updated.duration == 60
        assert updated.slug == "short-call"  # slug unchanged

    def test_update_nonexistent_returns_none(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        update = EventTypeUpdate(title="Ghost")
        result = svc.update_event_type("nonexistent-id", update)
        assert result is None


class TestDeleteEventType:
    def test_delete_removes_from_list(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        et = _make_event_type(title="To Delete", slug="to-delete")
        created = svc.create_event_type(et)

        result = svc.delete_event_type(created.id)
        assert result is True

        all_ets = svc.list_event_types()
        assert not any(e.id == created.id for e in all_ets)

    def test_delete_nonexistent_returns_false(self, db, tenant):
        svc = EventTypeService(db, TENANT_ID)
        result = svc.delete_event_type("nonexistent-id")
        assert result is False


class TestLegacyMigration:
    def test_is_active_migrates_to_is_hidden(self, db, tenant):
        """Legacy is_active=True -> is_hidden=False after migration."""
        legacy_data = {
            "id": str(uuid.uuid4()),
            "title": "Legacy ET",
            "slug": "legacy-et",
            "duration": 30,
            "is_active": True,
        }
        tenant.config_json = {"event_types": [legacy_data]}
        db.commit()

        svc = EventTypeService(db, TENANT_ID)
        ets = svc.list_event_types()

        assert len(ets) == 1
        assert ets[0].is_hidden is False  # is_active=True -> is_hidden=False
