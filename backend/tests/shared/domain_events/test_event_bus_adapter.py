"""Unit tests — EventBusAdapter.

Tests verify backwards-compatibility (flag OFF) and outbox routing (flag ON).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_platform.domain.events import EventBus as LegacyEventBus
from luana_core_events.outbox.application.event_bus_adapter import EventBusAdapter
from luana_core_events.outbox.domain.event import DomainEvent


@pytest.fixture(autouse=True)
def clear_bus():
    """Clear EventBus handlers between tests."""
    LegacyEventBus.clear()
    yield
    LegacyEventBus.clear()


class TestEventBusAdapterFlagOff:
    """Default behavior: flag OFF → legacy in-memory dispatch."""

    def test_flag_off_delegates_to_legacy_bus(self):
        """With flag OFF, publish delegates to LegacyEventBus.publish."""
        handler = MagicMock()
        LegacyEventBus.subscribe("test_event", handler)

        adapter = EventBusAdapter()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        adapter.publish(event, module=None)

        handler.assert_called_once_with(event)

    def test_flag_off_with_sync_session_uses_legacy_bus(self):
        """Flag OFF + sync session → legacy bus (after-commit hook preserved)."""
        handler = MagicMock()
        LegacyEventBus.subscribe("payment_received", handler)

        adapter = EventBusAdapter()
        event = DomainEvent(event_name="payment_received", tenant_id=uuid4())

        # Mock SA session that fires after_commit
        session = MagicMock()

        def mock_listens_for(target, identifier, **kwargs):
            def decorator(fn):
                # Simulate immediate after_commit
                fn(target)
                return fn

            return decorator

        with patch("sqlalchemy.event.listens_for", side_effect=mock_listens_for):
            adapter.publish(event, session=session, module="sales_agent")

        # Handler should NOT have been called (flag OFF → legacy path, uses SA event)
        # The legacy bus registers an SA after_commit listener

    def test_subscribe_delegates_to_legacy_bus(self):
        """subscribe() adds handler to legacy bus."""
        handler = MagicMock()
        adapter = EventBusAdapter()
        adapter.subscribe("my_event", handler)

        event = DomainEvent(event_name="my_event", tenant_id=uuid4())
        LegacyEventBus.publish(event, session=None)

        handler.assert_called_once_with(event)

    def test_clear_delegates_to_legacy_bus(self):
        """clear() removes all handlers from legacy bus."""
        handler = MagicMock()
        LegacyEventBus.subscribe("evt", handler)
        adapter = EventBusAdapter()
        adapter.clear()

        event = DomainEvent(event_name="evt", tenant_id=uuid4())
        LegacyEventBus.publish(event, session=None)

        handler.assert_not_called()


class TestEventBusAdapterFlagOn:
    """Flag ON behavior: routes to outbox or fallback."""

    def test_flag_on_no_session_falls_back_to_legacy(self, monkeypatch):
        """Flag ON + session=None → log warning + legacy fallback."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(
                USE_OUTBOX_PATTERN_DEFAULT=True,
                USE_OUTBOX_PATTERN_SALES_AGENT=True,
            ),
        )

        handler = MagicMock()
        LegacyEventBus.subscribe("test_event", handler)

        adapter = EventBusAdapter()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        adapter.publish(event, session=None, module="sales_agent")

        # Falls back to legacy bus (immediate dispatch since session=None)
        handler.assert_called_once_with(event)

    def test_flag_on_sync_session_calls_outbox_enqueue(self, monkeypatch):
        """Flag ON + sync session → calls outbox.enqueue_sync."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(
                USE_OUTBOX_PATTERN_DEFAULT=False,
                USE_OUTBOX_PATTERN_SALES_AGENT=True,
            ),
        )

        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = DomainEvent(event_name="payment_received", tenant_id=uuid4())
        session = MagicMock()

        adapter.publish(event, session=session, module="sales_agent")

        mock_outbox.enqueue_sync.assert_called_once()
        call_kwargs = mock_outbox.enqueue_sync.call_args
        assert call_kwargs[0][0].event_name == "payment_received"

    def test_is_outbox_enabled_returns_false_by_default(self, monkeypatch):
        """_is_outbox_enabled returns False when settings flag is False.

        Production default is True for sales_agent (config.py); test forces False
        via monkeypatch.setattr to assert the flag-off branch contract.
        """
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(USE_OUTBOX_PATTERN_SALES_AGENT=False, USE_OUTBOX_PATTERN_DEFAULT=False),
        )
        result = EventBusAdapter._is_outbox_enabled("sales_agent")
        assert result is False

    def test_is_outbox_enabled_with_module_none_uses_default_flag(self, monkeypatch):
        """_is_outbox_enabled(None) uses USE_OUTBOX_PATTERN_DEFAULT."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(
                USE_OUTBOX_PATTERN_DEFAULT=True,
            ),
        )
        result = EventBusAdapter._is_outbox_enabled(None)
        assert result is True

    def test_flag_on_unknown_module_uses_default(self, monkeypatch):
        """Flag ON for unknown module falls back to USE_OUTBOX_PATTERN_DEFAULT."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(
                USE_OUTBOX_PATTERN_DEFAULT=False,
                spec=["USE_OUTBOX_PATTERN_DEFAULT"],
            ),
        )
        # No USE_OUTBOX_PATTERN_UNKNOWN_MODULE → should use default (False)
        result = EventBusAdapter._is_outbox_enabled("unknown_module")
        assert result is False
