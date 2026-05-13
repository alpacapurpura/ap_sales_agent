"""Integration tests: copilot emitters use outbox adapter (EventBusAdapter).

Verifies the routing logic inside EventBusAdapter for copilot module:
  - Flag OFF (default) → delegates to legacy in-memory EventBus.publish
  - Flag ON + session=None → warns + fallback to legacy
  - Flag ON + sync session → calls outbox.enqueue_sync (best-effort)
  - Outbox failure is swallowed (best-effort contract)

No Postgres required. Tests mock at the adapter boundary.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
)
from luana_core_events.outbox.domain.event import DomainEvent


def _make_card_emitted_event() -> DomainEvent:
    return DomainEvent(
        event_name="copilot_card_emitted",
        tenant_id=uuid4(),
        payload={
            "card_kind": "proposal_card",
            "conversation_id": str(uuid4()),
            "turn_id": str(uuid4()),
        },
    )


def _make_routing_decided_event() -> DomainEvent:
    return DomainEvent(
        event_name="copilot_routing_decided",
        tenant_id=uuid4(),
        payload={
            "tier": "fast",
            "conversation_id": str(uuid4()),
            "turn_id": str(uuid4()),
        },
    )


class TestCopilotOutboxAdapterFlagOff:
    """Flag OFF (default, USE_OUTBOX_PATTERN_COPILOT=False) — legacy in-memory bus."""

    def test_card_emitted_flag_off_routes_to_legacy(self) -> None:
        """Card emitted event goes to legacy bus when copilot outbox flag is OFF.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        legacy_called: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False),
        ):
            adapter = EventBusAdapter()
            event = _make_card_emitted_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        assert len(legacy_called) == 1
        assert legacy_called[0] == "copilot_card_emitted"

    def test_routing_decided_flag_off_routes_to_legacy(self) -> None:
        """Routing decided event goes to legacy bus when copilot outbox flag is OFF.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        legacy_called: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False),
        ):
            adapter = EventBusAdapter()
            event = _make_routing_decided_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        assert len(legacy_called) == 1
        assert legacy_called[0] == "copilot_routing_decided"

    def test_flag_off_is_default_for_copilot_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify flag OFF path returns False when settings flag is False.

        Production default is True (config.py); test forces False via
        monkeypatch.setattr to assert the flag-off branch contract.
        """
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(USE_OUTBOX_PATTERN_COPILOT=False, USE_OUTBOX_PATTERN_DEFAULT=False),
        )
        result = EventBusAdapter._is_outbox_enabled("copilot")
        assert result is False

    def test_monkeypatch_env_flag_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify flag OFF via monkeypatch.setattr on settings (pydantic-settings
        loads env at startup; setenv after import does not propagate)."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(USE_OUTBOX_PATTERN_COPILOT=False, USE_OUTBOX_PATTERN_DEFAULT=False),
        )
        result = EventBusAdapter._is_outbox_enabled("copilot")
        assert result is False


class TestCopilotOutboxAdapterFlagOn:
    """Flag ON (USE_OUTBOX_PATTERN_COPILOT=True) via monkeypatch."""

    def test_flag_on_via_monkeypatch_enqueues_outbox(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Flag ON + sync session → outbox.enqueue_sync called for copilot event.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_COPILOT", "true")

        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_card_emitted_event()
        mock_session = MagicMock()

        with (
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "luana_core_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ),
        ):
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=mock_session)

        mock_outbox.enqueue_sync.assert_called_once_with(
            event,
            session=mock_session,
            idempotency_key=None,
        )

    def test_flag_on_no_session_falls_back_to_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Flag ON + session=None → warn + legacy fallback for copilot event.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_COPILOT", "true")
        legacy_called: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
        ):
            adapter = EventBusAdapter()
            event = _make_routing_decided_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        # Falls back to legacy — best-effort, no crash
        assert len(legacy_called) == 1
        assert legacy_called[0] == "copilot_routing_decided"

    def test_flag_on_outbox_failure_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Outbox enqueue failure must not propagate — best-effort contract.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_COPILOT", "true")

        mock_outbox = MagicMock()
        mock_outbox.enqueue_sync.side_effect = RuntimeError("DB down")

        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_card_emitted_event()
        mock_session = MagicMock()

        with (
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "luana_core_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ),
        ):
            # Must NOT raise — best-effort contract
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=mock_session)

        mock_outbox.enqueue_sync.assert_called_once()


class TestDomainSubscribersRegistration:
    """Verify copilot domain_subscribers wires onto EventBus correctly."""

    def test_register_subscribers_wires_card_emitted_handler(self) -> None:
        """register_subscribers registers on_card_emitted for copilot_card_emitted."""
        from luana_core_platform.domain.events import EventBus as LegacyEventBus

        # Clear to start fresh
        LegacyEventBus.clear()

        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from luana_core_copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        mock_repo = MagicMock(spec=TraceEventRepository)
        mock_repo.add = MagicMock(return_value=MagicMock())
        mock_repo.db = None

        register_subscribers(repo_factory=lambda: mock_repo)

        # Verify handlers registered — adapter.subscribe delegates to legacy bus _handlers
        from luana_core_copilot.domain.events import EVENT_CARD_EMITTED

        assert EVENT_CARD_EMITTED in LegacyEventBus._handlers, (
            f"Expected '{EVENT_CARD_EMITTED}' to be registered in LegacyEventBus._handlers"
        )

    def test_register_subscribers_idempotent(self) -> None:
        """Calling register_subscribers twice does not duplicate handlers."""
        from luana_core_platform.domain.events import EventBus as LegacyEventBus

        LegacyEventBus.clear()

        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from luana_core_copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        mock_repo = MagicMock(spec=TraceEventRepository)

        register_subscribers(repo_factory=lambda: mock_repo)
        from luana_core_copilot.domain.events import EVENT_CARD_EMITTED

        handlers_after_first = len(getattr(LegacyEventBus, "_handlers", {}).get(EVENT_CARD_EMITTED, []))

        register_subscribers(repo_factory=lambda: mock_repo)

        handlers_after_second = len(getattr(LegacyEventBus, "_handlers", {}).get(EVENT_CARD_EMITTED, []))

        assert handlers_after_second == handlers_after_first, (
            "register_subscribers is not idempotent — duplicate handlers registered"
        )
