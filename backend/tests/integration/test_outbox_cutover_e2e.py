"""E2E integration tests — outbox cutover flag-flip per-module (F-4).

Verifies that when ``USE_OUTBOX_PATTERN_{MODULE}=true`` is set, the production
call-sites route through the outbox path WITHOUT requiring any ``module=``
kwarg on the publish call.

This test class catches F-1 regressions: if module inference breaks, the
outbox path is silently bypassed and these tests turn RED.

Markers: ``integration`` — these tests exercise the full
adapter → inference → flag-check → enqueue path using mock sessions.
No live Postgres required here; we mock at the OutboxService boundary.

For truly end-to-end DB-level verification (row in domain_event_outbox),
run the verify_pending_payments worker in a test container. That path is
documented in ``docs/archive/2026/legacy-pis/PI-1-campaigns-module/.../IMPL-LOG.md``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

import src.shared.domain_events.outbox.application.event_bus_adapter as _adapter_mod
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
    _reset_module_inference_cache,
)


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Reset inference cache between tests for deterministic results."""
    _reset_module_inference_cache()
    yield
    _reset_module_inference_cache()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _set_flag(module_upper: str, value: bool) -> None:
    """Directly set a feature flag on the loaded settings singleton.

    ``monkeypatch.setenv`` does NOT work for Pydantic BaseSettings that are
    already instantiated. We use ``object.__setattr__`` to bypass the
    immutable-model guard.
    """
    attr = f"USE_OUTBOX_PATTERN_{module_upper}"
    object.__setattr__(_adapter_mod.settings, attr, value)


def _get_flag(module_upper: str) -> bool:
    """Read the current flag value from the settings singleton."""
    attr = f"USE_OUTBOX_PATTERN_{module_upper}"
    return getattr(_adapter_mod.settings, attr)


def _publish_from_module(
    adapter: EventBusAdapter,
    event,
    session,
    *,
    module_file: str,
) -> None:
    """Call adapter.publish patching sys._getframe so inference sees module_file.

    Simulates the production scenario: the adapter is called from a file
    inside src/modules/{name}/ WITHOUT an explicit module= kwarg.
    """
    fake_frame = MagicMock()
    fake_frame.f_code.co_filename = module_file
    fake_frame.f_back = None

    with patch("sys._getframe", return_value=fake_frame):
        # No module= kwarg — this is the production call-site pattern (F-1)
        adapter.publish(event, session=session)


# ─── sales_agent cutover ──────────────────────────────────────────────────────


@pytest.mark.integration
class TestOutboxCutoverSalesAgent:
    """Flag-flip sales_agent: activating outbox routes without module= kwarg."""

    def test_sales_agent_flag_on_routes_to_outbox_without_module_kwarg(self) -> None:
        """USE_OUTBOX_PATTERN_SALES_AGENT=True → publish from sales_agent file
        routes to outbox.enqueue_sync WITHOUT module= kwarg.

        Regression guard for F-1: broken inference → test turns RED.
        """
        original = _get_flag("SALES_AGENT")
        original_default = _get_flag("DEFAULT")
        try:
            _set_flag("SALES_AGENT", True)
            _set_flag("DEFAULT", False)

            mock_outbox = MagicMock()
            adapter = EventBusAdapter(outbox_service=mock_outbox)

            from src.shared.domain.events import PaymentReceivedEvent

            event = PaymentReceivedEvent.create(
                tenant_id=uuid4(),
                lead_id=uuid4(),
                offer_id=uuid4(),
                payment_id=uuid4(),
                auto_grant=True,
            )
            mock_session = MagicMock()

            with patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ):
                _publish_from_module(
                    adapter,
                    event,
                    mock_session,
                    module_file="/app/src/modules/sales_agent/workers/verify_pending_payments.py",
                )

            mock_outbox.enqueue_sync.assert_called_once()
            call_event = mock_outbox.enqueue_sync.call_args[0][0]
            assert call_event.event_name == "payment_received"
        finally:
            _set_flag("SALES_AGENT", original)
            _set_flag("DEFAULT", original_default)

    def test_sales_agent_flag_off_uses_legacy_without_module_kwarg(self) -> None:
        """Flag OFF: publish from sales_agent file goes to legacy bus (default)."""
        original = _get_flag("SALES_AGENT")
        try:
            _set_flag("SALES_AGENT", False)

            legacy_called: list[str] = []
            with patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ):
                adapter = EventBusAdapter()
                from src.shared.domain.events import LeadCapturedEvent

                event = LeadCapturedEvent.create(
                    tenant_id=uuid4(),
                    profile_id=uuid4(),
                    channel_slug="whatsapp",
                    extracted_field="phone",
                    source_channel_type="whatsapp",
                )
                _publish_from_module(
                    adapter,
                    event,
                    None,
                    module_file="/app/src/modules/sales_agent/application/orchestrator/audit_emitter.py",
                )

            assert len(legacy_called) == 1
            assert legacy_called[0] == "lead_captured"
        finally:
            _set_flag("SALES_AGENT", original)


# ─── copilot cutover ──────────────────────────────────────────────────────────


@pytest.mark.integration
class TestOutboxCutoverCopilot:
    """Flag-flip copilot: activating outbox routes without module= kwarg."""

    def test_copilot_flag_on_routes_to_outbox_without_module_kwarg(self) -> None:
        """USE_OUTBOX_PATTERN_COPILOT=True → publish from copilot file routes to outbox."""
        original = _get_flag("COPILOT")
        original_default = _get_flag("DEFAULT")
        try:
            _set_flag("COPILOT", True)
            _set_flag("DEFAULT", False)

            mock_outbox = MagicMock()
            adapter = EventBusAdapter(outbox_service=mock_outbox)

            from src.shared.domain_events.outbox.domain.event import DomainEvent

            event = DomainEvent(
                event_name="copilot_card_emitted",
                tenant_id=uuid4(),
                payload={"card_kind": "proposal_card"},
            )
            mock_session = MagicMock()

            with patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ):
                _publish_from_module(
                    adapter,
                    event,
                    mock_session,
                    module_file="/app/src/modules/copilot/application/orchestrator/chat.py",
                )

            mock_outbox.enqueue_sync.assert_called_once()
            call_event = mock_outbox.enqueue_sync.call_args[0][0]
            assert call_event.event_name == "copilot_card_emitted"
        finally:
            _set_flag("COPILOT", original)
            _set_flag("DEFAULT", original_default)

    def test_copilot_flag_off_uses_legacy_without_module_kwarg(self) -> None:
        """Flag OFF: publish from copilot file goes to legacy bus."""
        original = _get_flag("COPILOT")
        try:
            _set_flag("COPILOT", False)

            legacy_called: list[str] = []
            with patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ):
                from src.shared.domain_events.outbox.domain.event import DomainEvent

                adapter = EventBusAdapter()
                event = DomainEvent(
                    event_name="copilot_routing_decided",
                    tenant_id=uuid4(),
                    payload={"tier": "fast"},
                )
                _publish_from_module(
                    adapter,
                    event,
                    None,
                    module_file="/app/src/modules/copilot/application/extraction_card_flow.py",
                )

            assert len(legacy_called) == 1
            assert legacy_called[0] == "copilot_routing_decided"
        finally:
            _set_flag("COPILOT", original)


# ─── brand cutover ────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestOutboxCutoverBrand:
    """Flag-flip brand: activating outbox routes without module= kwarg."""

    def test_brand_flag_on_routes_to_outbox_without_module_kwarg(self) -> None:
        """USE_OUTBOX_PATTERN_BRAND=True → publish from brand file routes to outbox."""
        original = _get_flag("BRAND")
        original_default = _get_flag("DEFAULT")
        try:
            _set_flag("BRAND", True)
            _set_flag("DEFAULT", False)

            mock_outbox = MagicMock()
            adapter = EventBusAdapter(outbox_service=mock_outbox)

            from src.shared.domain.events import BrandSectionUpdatedEvent

            event = BrandSectionUpdatedEvent.create(
                tenant_id=uuid4(),
                section="identity",
            )
            mock_session = MagicMock()

            with patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ):
                _publish_from_module(
                    adapter,
                    event,
                    mock_session,
                    module_file="/app/src/modules/brand/infrastructure/repositories/brand_repository.py",
                )

            mock_outbox.enqueue_sync.assert_called_once()
            call_event = mock_outbox.enqueue_sync.call_args[0][0]
            assert call_event.event_name == "brand_section_updated"
        finally:
            _set_flag("BRAND", original)
            _set_flag("DEFAULT", original_default)

    def test_brand_flag_off_uses_legacy_without_module_kwarg(self) -> None:
        """Flag OFF: publish from brand file goes to legacy bus."""
        original = _get_flag("BRAND")
        try:
            _set_flag("BRAND", False)

            legacy_called: list[str] = []
            with patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ):
                from src.shared.domain.events import PersonalityProfileUpdatedEvent

                adapter = EventBusAdapter()
                event = PersonalityProfileUpdatedEvent.create(
                    tenant_id=uuid4(),
                    profile_id=uuid4(),
                    action="updated",
                )
                _publish_from_module(
                    adapter,
                    event,
                    None,
                    module_file="/app/src/modules/brand/application/services/personality_service.py",
                )

            assert len(legacy_called) == 1
            assert legacy_called[0] == "personality_profile_updated"
        finally:
            _set_flag("BRAND", original)


# ─── Cross-cutting: no cross-module bleed ────────────────────────────────────


@pytest.mark.integration
class TestOutboxCutoverIsolation:
    """Flipping one module flag does not activate outbox for other modules."""

    def test_sales_agent_flag_on_does_not_activate_copilot(self) -> None:
        """USE_OUTBOX_PATTERN_SALES_AGENT=True must NOT activate copilot outbox."""
        orig_sa = _get_flag("SALES_AGENT")
        orig_cp = _get_flag("COPILOT")
        orig_def = _get_flag("DEFAULT")
        try:
            _set_flag("SALES_AGENT", True)
            _set_flag("COPILOT", False)
            _set_flag("DEFAULT", False)

            mock_outbox = MagicMock()
            legacy_called: list[str] = []

            with patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ):
                adapter = EventBusAdapter(outbox_service=mock_outbox)
                from src.shared.domain_events.outbox.domain.event import DomainEvent

                event = DomainEvent(
                    event_name="copilot_card_emitted",
                    tenant_id=uuid4(),
                    payload={},
                )
                _publish_from_module(
                    adapter,
                    event,
                    None,
                    module_file="/app/src/modules/copilot/application/orchestrator/chat.py",
                )

            # copilot flag is OFF → legacy bus
            assert len(legacy_called) == 1
            mock_outbox.enqueue_sync.assert_not_called()
        finally:
            _set_flag("SALES_AGENT", orig_sa)
            _set_flag("COPILOT", orig_cp)
            _set_flag("DEFAULT", orig_def)
