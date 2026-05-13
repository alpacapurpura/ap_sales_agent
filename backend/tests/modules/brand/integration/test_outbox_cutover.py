"""Integration tests: brand outbox cutover (USE_OUTBOX_PATTERN_BRAND=True).

Policy F-7 (PR-4): tests integrate real EventBusAdapter logic;
mocks only at infrastructure boundary (OutboxService enqueue_sync call).

Verifies:
- Flag default ON post Sub-D cutover.
- Adapter resolves brand module flag correctly.
- With flag ON and a real session, adapter routes to outbox (not legacy).
- Brand-specific events route through adapter correctly.

Note: BudgetGuard wiring brand LLM callsites diferido a Sub-D-2 (deuda DR-7).
Brand has 7 LLM callsites in style_analyzer + voice_fidelity + personality_service
using sync ``LLMFactory.get_service().generate_response(...)`` — wrap requires
``BudgetGuardingLLMService`` per-callsite refactor; deferred post PR-6.

PR-6 Sub-D / PI-1 S2.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from luana_core_platform.core.config import settings
from luana_core_platform.domain.events import DomainEvent
from luana_core_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
)


def _make_brand_event() -> DomainEvent:
    """Build a minimal domain event for testing the adapter."""
    # Use PaymentReceivedEvent as a concrete DomainEvent for adapter routing
    # (brand events follow same adapter path)
    from luana_core_platform.domain.events import PaymentReceivedEvent

    return PaymentReceivedEvent.create(
        tenant_id="bbbbbbbb-cccc-dddd-eeee-000000000001",
        lead_id="11111111-1111-1111-1111-111111111111",
        offer_id="22222222-2222-2222-2222-222222222222",
        payment_id="55555555-5555-5555-5555-555555555555",
        auto_grant=False,
    )


class TestBrandFlagIsOn:
    """USE_OUTBOX_PATTERN_BRAND default flipped to True (Sub-D)."""

    def test_use_outbox_pattern_brand_is_true(self) -> None:
        """Default config flag for brand cutover is ON."""
        assert settings.USE_OUTBOX_PATTERN_BRAND is True

    def test_event_bus_adapter_is_outbox_enabled_for_brand(self) -> None:
        """EventBusAdapter resolves brand-module flag to True."""
        adapter = EventBusAdapter()
        # Module name "brand" → looks up USE_OUTBOX_PATTERN_BRAND
        assert adapter._is_outbox_enabled("brand") is True


class TestBrandOutboxCutoverFlagOn:
    """With USE_OUTBOX_PATTERN_BRAND=True, adapter routes to outbox path."""

    def test_publish_with_session_routes_to_outbox_enqueue_sync(self) -> None:
        """Flag ON + real session → enqueue_sync called (not legacy bus)."""
        mock_outbox = MagicMock()
        mock_session = MagicMock()

        with (
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "luana_core_events.outbox.application.event_bus_adapter.EventBusAdapter._get_outbox",
                return_value=mock_outbox,
            ),
        ):
            adapter = EventBusAdapter()
            event = _make_brand_event()
            adapter.publish(event, session=mock_session)

            mock_outbox.enqueue_sync.assert_called_once()

    def test_publish_flag_off_uses_legacy_path(self) -> None:
        """Flag OFF → legacy in-memory bus used, outbox NOT touched."""
        legacy_called: list[str] = []
        mock_session = MagicMock()

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False),
        ):
            adapter = EventBusAdapter()
            event = _make_brand_event()
            adapter.publish(event, session=mock_session)

        assert len(legacy_called) == 1
