"""Integration tests: brand emitters use outbox adapter (EventBusAdapter).

Verifies the routing logic inside EventBusAdapter for brand module:
  - Flag OFF (default, USE_OUTBOX_PATTERN_BRAND=False) → legacy in-memory bus
  - Flag ON + session=None → warns + fallback to legacy (best-effort)
  - Flag ON + sync session → calls outbox.enqueue_sync
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


def _make_brand_section_updated_event() -> DomainEvent:
    return DomainEvent(
        event_name="brand_section_updated",
        tenant_id=uuid4(),
        payload={"section": "identity"},
    )


def _make_personality_profile_updated_event() -> DomainEvent:
    return DomainEvent(
        event_name="personality_profile_updated",
        tenant_id=uuid4(),
        payload={"profile_id": str(uuid4()), "action": "updated"},
    )


def _make_extraction_section_completed_event() -> DomainEvent:
    return DomainEvent(
        event_name="extraction_section_completed",
        tenant_id=uuid4(),
        payload={
            "job_id": str(uuid4()),
            "module": "brand",
            "section_slug": "identity",
        },
    )


class TestBrandOutboxAdapterFlagOff:
    """Flag OFF (default, USE_OUTBOX_PATTERN_BRAND=False) → legacy in-memory bus."""

    def test_brand_section_updated_flag_off_routes_to_legacy(self) -> None:
        """BrandSectionUpdatedEvent goes to legacy bus when brand outbox flag is OFF.

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
            event = _make_brand_section_updated_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        assert len(legacy_called) == 1
        assert legacy_called[0] == "brand_section_updated"

    def test_personality_profile_updated_flag_off_routes_to_legacy(self) -> None:
        """PersonalityProfileUpdatedEvent goes to legacy bus when brand flag is OFF.

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
            event = _make_personality_profile_updated_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        assert len(legacy_called) == 1
        assert legacy_called[0] == "personality_profile_updated"

    def test_flag_off_is_default_for_brand_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify flag OFF path returns False when settings flag is False.

        Production default is True (config.py); test forces False via
        monkeypatch.setattr to assert the flag-off branch contract.
        """
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(USE_OUTBOX_PATTERN_BRAND=False, USE_OUTBOX_PATTERN_DEFAULT=False),
        )
        result = EventBusAdapter._is_outbox_enabled("brand")
        assert result is False

    def test_monkeypatch_env_flag_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify flag OFF via monkeypatch.setattr on settings (pydantic-settings
        loads env at startup; setenv after import does not propagate)."""
        monkeypatch.setattr(
            "luana_core_events.outbox.application.event_bus_adapter.settings",
            MagicMock(USE_OUTBOX_PATTERN_BRAND=False, USE_OUTBOX_PATTERN_DEFAULT=False),
        )
        result = EventBusAdapter._is_outbox_enabled("brand")
        assert result is False


class TestBrandOutboxAdapterFlagOn:
    """Flag ON (USE_OUTBOX_PATTERN_BRAND=True) via monkeypatch."""

    def test_flag_on_via_monkeypatch_enqueues_outbox(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Flag ON + sync session → outbox.enqueue_sync called for brand event.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_BRAND", "true")

        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_brand_section_updated_event()
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
        """Flag ON + session=None → warn + legacy fallback for brand event.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_BRAND", "true")
        legacy_called: list[str] = []

        with (
            patch(
                "luana_core_platform.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
        ):
            adapter = EventBusAdapter()
            event = _make_extraction_section_completed_event()
            # No module= kwarg — mirrors production call sites (F-1 fix)
            adapter.publish(event, session=None)

        # Falls back to legacy — best-effort, no crash
        assert len(legacy_called) == 1
        assert legacy_called[0] == "extraction_section_completed"

    def test_flag_on_outbox_failure_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Outbox enqueue failure must not propagate — best-effort contract.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_BRAND", "true")

        mock_outbox = MagicMock()
        mock_outbox.enqueue_sync.side_effect = RuntimeError("DB down")

        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_brand_section_updated_event()
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

    def test_extraction_completed_flag_on_enqueues_outbox(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ExtractionSectionCompletedEvent uses outbox when flag ON + session provided.

        Post-F1-fix: no module= kwarg — adapter infers from call stack.
        """
        monkeypatch.setenv("USE_OUTBOX_PATTERN_BRAND", "true")

        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_extraction_section_completed_event()
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

        mock_outbox.enqueue_sync.assert_called_once()
        call_event = mock_outbox.enqueue_sync.call_args[0][0]
        assert call_event.event_name == "extraction_section_completed"


class TestBrandSummaryRegenDebounceFlow:
    """Verify brand_summary_regen debounce event chain.

    F3 hooks the lighthouse regen worker on ``brand_section_updated``.
    With adapter_bus (flag OFF), behavior is identical to legacy bus:
    the event fires and all subscribers are called.
    """

    def test_brand_section_updated_subscribers_fire_on_legacy_path(self) -> None:
        """Subscribers on brand_section_updated are called when flag OFF."""
        from luana_core_platform.domain.events import EventBus as LegacyEventBus

        LegacyEventBus.clear()
        received: list[object] = []
        LegacyEventBus.subscribe("brand_section_updated", received.append)

        with patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False):
            adapter = EventBusAdapter()
            event = _make_brand_section_updated_event()
            adapter.publish(event, session=None, module="brand")

        assert len(received) == 1
        assert received[0].event_name == "brand_section_updated"
        LegacyEventBus.clear()
