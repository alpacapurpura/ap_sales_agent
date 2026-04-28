"""Tests for JourneyEvent domain entity."""

from datetime import UTC, datetime
from uuid import uuid4

from src.modules.analytics.domain.event import JourneyEvent


class TestJourneyEvent:
    def _make(self, **kwargs: object) -> JourneyEvent:
        defaults = {
            "id": uuid4(),
            "profile_id": uuid4(),
            "tenant_id": uuid4(),
            "event_name": "page_view",
            "event_type": "track",
        }
        defaults.update(kwargs)
        return JourneyEvent(**defaults)  # type: ignore[arg-type]

    def test_basic_construction(self) -> None:
        evt = self._make()
        assert evt.event_name == "page_view"
        assert evt.event_type == "track"
        assert evt.properties == {}
        assert evt.context == {}
        assert evt.occurred_at is None

    def test_with_properties_and_context(self) -> None:
        evt = self._make(
            properties={"url": "/home", "referrer": "google"},
            context={"ip": "1.2.3.4"},
        )
        assert evt.properties["url"] == "/home"
        assert evt.context["ip"] == "1.2.3.4"

    def test_with_occurred_at(self) -> None:
        ts = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
        evt = self._make(occurred_at=ts)
        assert evt.occurred_at == ts

    def test_tenant_id_optional(self) -> None:
        evt = self._make(tenant_id=None)
        assert evt.tenant_id is None

    def test_ids_are_uuids(self) -> None:
        eid = uuid4()
        pid = uuid4()
        evt = self._make(id=eid, profile_id=pid)
        assert evt.id == eid
        assert evt.profile_id == pid

    def test_event_types(self) -> None:
        for etype in ("track", "page", "screen"):
            evt = self._make(event_type=etype)
            assert evt.event_type == etype

    def test_from_attributes(self) -> None:
        # BaseEntity uses from_attributes=True
        class _Fake:
            id = uuid4()
            profile_id = uuid4()
            tenant_id = uuid4()
            event_name = "form_submitted"
            event_type = "track"
            properties: dict = {}
            context: dict = {}
            occurred_at = None

        evt = JourneyEvent.model_validate(_Fake())
        assert evt.event_name == "form_submitted"
