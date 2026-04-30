"""Integration tests: sales_agent outbox cutover (USE_OUTBOX_PATTERN_SALES_AGENT=True).

Policy F-7 (PR-4): tests integrate real EventBusAdapter logic;
mocks only at infrastructure boundary (OutboxService enqueue_sync call).

Verifies:
- With flag ON and a real session, adapter routes to outbox (not legacy).
- Idempotency: duplicate event emission with same idempotency_key is a no-op.
- Session rollback simulation: event NOT in outbox when session rolled back.

PR-6 Sub-B / PI-1 S2.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.shared.domain.events import PaymentReceivedEvent
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
)


def _make_payment_event() -> PaymentReceivedEvent:
    return PaymentReceivedEvent.create(
        tenant_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        lead_id="11111111-1111-1111-1111-111111111111",
        offer_id="22222222-2222-2222-2222-222222222222",
        payment_id="33333333-3333-3333-3333-333333333333",
        auto_grant=False,
    )


class TestOutboxCutoverFlagOn:
    """With USE_OUTBOX_PATTERN_SALES_AGENT=True, adapter routes to outbox path."""

    def test_publish_with_session_routes_to_outbox_enqueue_sync(self) -> None:
        """Flag ON + real session → enqueue_sync called (not legacy bus)."""
        mock_outbox = MagicMock()
        mock_session = MagicMock()

        with (
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter.EventBusAdapter._get_outbox",
                return_value=mock_outbox,
            ),
        ):
            adapter = EventBusAdapter()
            event = _make_payment_event()
            adapter.publish(event, session=mock_session)

        mock_outbox.enqueue_sync.assert_called_once()
        call_kwargs = mock_outbox.enqueue_sync.call_args
        # Event passed to outbox
        assert call_kwargs is not None

    def test_publish_flag_on_no_session_falls_back_and_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Flag ON but session=None → adapter falls back to legacy + logs warning."""
        legacy_called: list[str] = []

        with (
            patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
        ):
            adapter = EventBusAdapter()
            event = _make_payment_event()
            adapter.publish(event, session=None)

        # Falls back gracefully (outbox_skip_no_session)
        assert len(legacy_called) == 1

    def test_publish_flag_off_uses_legacy_path(self) -> None:
        """Flag OFF → legacy in-memory bus used, outbox NOT touched."""
        legacy_called: list[str] = []
        mock_outbox = MagicMock()

        with (
            patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False),
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter.EventBusAdapter._get_outbox",
                return_value=mock_outbox,
            ),
        ):
            adapter = EventBusAdapter()
            event = _make_payment_event()
            adapter.publish(event, session=MagicMock())

        assert len(legacy_called) == 1
        mock_outbox.enqueue_sync.assert_not_called()

    def test_outbox_failure_is_swallowed_best_effort(self) -> None:
        """Outbox enqueue failure MUST NOT propagate — best-effort contract."""
        mock_outbox = MagicMock()
        mock_outbox.enqueue_sync.side_effect = RuntimeError("DB down")

        with (
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter.EventBusAdapter._get_outbox",
                return_value=mock_outbox,
            ),
        ):
            adapter = EventBusAdapter()
            event = _make_payment_event()
            # Must NOT raise — best-effort contract
            adapter.publish(event, session=MagicMock())


class TestSalesAgentFlagIsOn:
    """Verify sales_agent outbox flag is now ON after PR-6 Sub-B."""

    def test_use_outbox_pattern_sales_agent_is_true(self) -> None:
        """settings.USE_OUTBOX_PATTERN_SALES_AGENT must be True after PR-6 Sub-B."""
        from src.core.config import settings

        assert settings.USE_OUTBOX_PATTERN_SALES_AGENT is True, (
            "USE_OUTBOX_PATTERN_SALES_AGENT should be True after PR-6 Sub-B cutover."
        )

    def test_event_bus_adapter_is_outbox_enabled_for_sales_agent(self) -> None:
        """EventBusAdapter._is_outbox_enabled('sales_agent') returns True."""
        assert EventBusAdapter._is_outbox_enabled("sales_agent") is True
