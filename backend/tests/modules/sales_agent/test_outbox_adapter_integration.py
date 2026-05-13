"""Integration tests: sales_agent emitters use outbox adapter (EventBusAdapter).

Verifies the routing logic inside EventBusAdapter:
  - Flag OFF → delegates to legacy in-memory EventBus.publish
  - Flag ON + session=None → warns + fallback to legacy
  - Flag ON + sync session → calls outbox.enqueue_sync (best-effort)
  - Outbox failure is swallowed (best-effort contract)

No Postgres required. Tests mock at the adapter boundary.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from luana_core_platform.domain.events import LeadCapturedEvent, PaymentReceivedEvent
from luana_core_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
)


def _make_lead_captured() -> LeadCapturedEvent:
    return LeadCapturedEvent.create(
        tenant_id="11111111-1111-1111-1111-111111111111",
        profile_id="22222222-2222-2222-2222-222222222222",
        channel_slug="whatsapp",
        extracted_field="phone",
        source_channel_type="whatsapp",
    )


def _make_payment_received() -> PaymentReceivedEvent:
    return PaymentReceivedEvent.create(
        tenant_id="11111111-1111-1111-1111-111111111111",
        lead_id="33333333-3333-3333-3333-333333333333",
        offer_id="44444444-4444-4444-4444-444444444444",
        payment_id="55555555-5555-5555-5555-555555555555",
        auto_grant=True,
    )


class TestEventBusAdapterFlagOff:
    """Flag OFF → legacy in-memory bus, no outbox involvement."""

    def test_publish_flag_off_routes_to_legacy(self) -> None:
        """When outbox is disabled, publish goes to LegacyEventBus.

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
            event = _make_lead_captured()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        assert len(legacy_called) == 1
        assert legacy_called[0] == event.event_name

    def test_subscribe_and_clear_delegate_to_legacy(self) -> None:
        """subscribe/clear are always delegated to the legacy in-memory bus."""
        calls: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.subscribe",
                side_effect=lambda name, h: calls.append(f"sub:{name}"),
            ),
            patch(
                "luana_core_platform.domain.events.EventBus.clear",
                side_effect=lambda: calls.append("clear"),
            ),
        ):
            adapter = EventBusAdapter()
            adapter.subscribe("payment_received", lambda e: None)
            adapter.clear()

        assert "sub:payment_received" in calls
        assert "clear" in calls


class TestEventBusAdapterFlagOn:
    """Flag ON → outbox path."""

    def test_publish_flag_on_no_session_falls_back_to_legacy(self) -> None:
        """Flag ON + session=None → warn + legacy fallback (no crash).

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        legacy_called: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
        ):
            adapter = EventBusAdapter()
            event = _make_lead_captured()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        # Falls back to legacy — best-effort, no crash
        assert len(legacy_called) == 1

    def test_publish_flag_on_with_sync_session_calls_outbox_enqueue(self) -> None:
        """Flag ON + sync session → outbox_service.enqueue_sync called.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)

        event = _make_payment_received()
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

    def test_publish_flag_on_outbox_failure_is_swallowed(self) -> None:
        """Outbox enqueue failure must not propagate (best-effort contract).

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        mock_outbox = MagicMock()
        mock_outbox.enqueue_sync.side_effect = RuntimeError("DB down")

        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_payment_received()
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

        # enqueue_sync was attempted (and swallowed)
        mock_outbox.enqueue_sync.assert_called_once()


class TestSalesAgentLocalEventBus:
    """The local sales_agent EventBus (for internal domain events) is intact."""

    def test_local_event_bus_subscribe_wires_by_class(self) -> None:
        """Local EventBus._subscribers dict supports class-keyed wiring."""
        from luana_core_sales_agent.application.event_bus import EventBus
        from luana_core_sales_agent.domain.events import LeadQualifiedEvent

        bus = EventBus()

        async def handler(event: LeadQualifiedEvent) -> None:
            pass

        bus.subscribe(LeadQualifiedEvent, handler)
        assert LeadQualifiedEvent in bus._subscribers
        assert len(bus._subscribers[LeadQualifiedEvent]) == 1

    def test_local_event_bus_is_independent_class(self) -> None:
        """The local EventBus is the module-internal class, not the adapter."""
        from luana_core_sales_agent.application.event_bus import EventBus

        bus = EventBus()
        # Confirms it has the class-keyed _subscribers (not adapter API)
        assert hasattr(bus, "_subscribers")
        assert isinstance(bus._subscribers, dict)

    def test_register_subscribers_wires_all_four_observability_handlers(self) -> None:
        """register_subscribers wires all 4 sales_agent observability handlers."""
        from luana_core_sales_agent.application.event_bus import EventBus
        from luana_core_sales_agent.domain.events import (
            LeadQualifiedEvent,
            ObjectionHandledEvent,
            StageTransitionedEvent,
            ToolLoopDetectedEvent,
        )
        from luana_core_sales_agent.observability.domain_events.subscribers import (
            register_subscribers,
        )

        bus = EventBus()
        register_subscribers(bus)

        for evt_cls in (
            LeadQualifiedEvent,
            ObjectionHandledEvent,
            StageTransitionedEvent,
            ToolLoopDetectedEvent,
        ):
            assert evt_cls in bus._subscribers
            assert len(bus._subscribers[evt_cls]) == 1
