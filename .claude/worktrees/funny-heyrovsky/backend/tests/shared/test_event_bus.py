"""Tests for the shared EventBus and DomainEvent."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4

from src.shared.domain.events import DomainEvent, EventBus


@pytest.fixture(autouse=True)
def clean_event_bus():
    """Ensure EventBus handlers are cleared between tests."""
    EventBus.clear()
    yield
    EventBus.clear()


class TestDomainEvent:
    def test_domain_event_has_required_fields(self):
        tenant = uuid4()
        event = DomainEvent(
            event_name="test_event",
            tenant_id=tenant,
            payload={"key": "value"},
        )
        assert event.event_name == "test_event"
        assert event.tenant_id == tenant
        assert event.payload == {"key": "value"}
        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_defaults(self):
        event = DomainEvent(
            event_name="test_event",
            tenant_id=uuid4(),
        )
        assert event.payload == {}
        assert event.occurred_at is not None


class TestEventBusImmediate:
    """Tests for EventBus.publish with session=None (immediate dispatch)."""

    def test_immediate_dispatch_calls_handler(self):
        handler = MagicMock()
        EventBus.subscribe("test_event", handler)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=None)

        handler.assert_called_once_with(event)

    def test_multiple_handlers_for_same_event(self):
        handler1 = MagicMock()
        handler2 = MagicMock()
        EventBus.subscribe("test_event", handler1)
        EventBus.subscribe("test_event", handler2)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=None)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    def test_handler_exception_isolation(self):
        """One handler failing should not prevent other handlers from running."""
        bad_handler = MagicMock(side_effect=ValueError("boom"))
        good_handler = MagicMock()
        EventBus.subscribe("test_event", bad_handler)
        EventBus.subscribe("test_event", good_handler)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        # Should not raise
        EventBus.publish(event, session=None)

        bad_handler.assert_called_once_with(event)
        good_handler.assert_called_once_with(event)

    def test_unknown_event_dispatches_to_no_handlers(self):
        handler = MagicMock()
        EventBus.subscribe("known_event", handler)

        event = DomainEvent(event_name="unknown_event", tenant_id=uuid4())
        # Should not raise
        EventBus.publish(event, session=None)

        handler.assert_not_called()

    def test_publish_without_handlers_does_not_error(self):
        event = DomainEvent(event_name="orphan_event", tenant_id=uuid4())
        # Should not raise
        EventBus.publish(event, session=None)


class TestEventBusAfterCommit:
    """Tests for EventBus.publish with a SQLAlchemy session (after-commit dispatch)."""

    def test_deferred_dispatch_after_commit(self, db):
        """Event handler should be called only after session.commit()."""
        handler = MagicMock()
        EventBus.subscribe("test_event", handler)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=db)

        # Handler should NOT be called yet
        handler.assert_not_called()

        # Now commit
        db.commit()

        # Handler should have been called
        handler.assert_called_once_with(event)

    def test_deferred_dispatch_not_called_on_rollback(self, db):
        """Event handler should NOT be called if session is rolled back."""
        handler = MagicMock()
        EventBus.subscribe("test_event", handler)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=db)

        # Rollback instead of commit
        db.rollback()

        # Handler should NOT have been called
        handler.assert_not_called()

    def test_handler_exception_in_after_commit_is_isolated(self, db):
        """Handler exception in after-commit should be caught, not propagate."""
        bad_handler = MagicMock(side_effect=RuntimeError("after-commit boom"))
        good_handler = MagicMock()
        EventBus.subscribe("test_event", bad_handler)
        EventBus.subscribe("test_event", good_handler)

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=db)

        # Commit should succeed even though handler raises
        db.commit()

        bad_handler.assert_called_once_with(event)
        good_handler.assert_called_once_with(event)


class TestEventBusClear:
    def test_clear_removes_all_handlers(self):
        handler = MagicMock()
        EventBus.subscribe("test_event", handler)

        EventBus.clear()

        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        EventBus.publish(event, session=None)

        handler.assert_not_called()
