"""Unit tests — EventBusAdapter module inference (F-1 fix, PI-1 S0 post-REVIEW).

Verifies that ``_infer_module_from_caller()`` and ``_module_name_from_file()``
correctly extract the Nicolify module name from call-stack filenames, enabling
the adapter to route flag-based outbox decisions without requiring callers to
pass ``module=`` explicitly.

No Postgres, no event loop — pure unit tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.domain_events.outbox.application.event_bus_adapter import (
    EventBusAdapter,
    _infer_module_from_caller,
    _module_name_from_file,
    _reset_module_inference_cache,
)
from src.shared.domain_events.outbox.domain.event import DomainEvent


@pytest.fixture(autouse=True)
def clear_inference_cache() -> None:
    """Ensure lru_cache is clean between tests."""
    _reset_module_inference_cache()
    yield
    _reset_module_inference_cache()


# ─── _module_name_from_file unit tests ─────────────────────────────────────


class TestModuleNameFromFile:
    """Direct unit tests for the filename → module name extractor."""

    def test_sales_agent_unix_path(self) -> None:
        """Extracts 'sales_agent' from a Unix-style source path."""
        path = "/home/chris/AISALESHT/backend/src/modules/sales_agent/domain/events.py"
        assert _module_name_from_file(path) == "sales_agent"

    def test_copilot_unix_path(self) -> None:
        """Extracts 'copilot' from a copilot module path."""
        path = "/home/chris/AISALESHT/backend/src/modules/copilot/application/orchestrator/chat.py"
        assert _module_name_from_file(path) == "copilot"

    def test_brand_unix_path(self) -> None:
        """Extracts 'brand' from a brand module path."""
        path = "/home/chris/AISALESHT/backend/src/modules/brand/workers/tasks.py"
        assert _module_name_from_file(path) == "brand"

    def test_analytics_unix_path(self) -> None:
        """Extracts 'analytics' from an analytics module path."""
        path = "/app/src/modules/analytics/application/services/etl_service.py"
        assert _module_name_from_file(path) == "analytics"

    def test_windows_style_path(self) -> None:
        """Extracts module name from a Windows-style path (WSL2 compat)."""
        path = r"C:\Users\chris\AISALESHT\backend\src\modules\sales_agent\workers\verify.py"
        assert _module_name_from_file(path) == "sales_agent"

    def test_outside_modules_returns_none(self) -> None:
        """Returns None for frames outside src/modules/."""
        path = "/home/chris/AISALESHT/backend/src/shared/domain/events.py"
        assert _module_name_from_file(path) is None

    def test_stdlib_frame_returns_none(self) -> None:
        """Returns None for stdlib frames."""
        path = "/usr/lib/python3.12/asyncio/events.py"
        assert _module_name_from_file(path) is None

    def test_tests_directory_returns_none(self) -> None:
        """Returns None for test-file frames (not in src/modules/)."""
        path = "/home/chris/AISALESHT/backend/tests/shared/domain_events/test_foo.py"
        assert _module_name_from_file(path) is None

    def test_empty_string_returns_none(self) -> None:
        """Returns None for empty filename (edge case)."""
        assert _module_name_from_file("") is None

    def test_result_is_cached(self) -> None:
        """Same filename returns cached result without re-running regex."""
        path = "/app/src/modules/copilot/application/tools/my_tool.py"
        result_first = _module_name_from_file(path)
        result_second = _module_name_from_file(path)
        assert result_first == result_second == "copilot"
        # Cache info should show 1 miss + 1 hit
        cache_info = _module_name_from_file.cache_info()
        assert cache_info.hits >= 1


# ─── _infer_module_from_caller integration ─────────────────────────────────


def _caller_from_sales_agent_path() -> str | None:
    """Helper that simulates calling infer from a path matching sales_agent.

    We mock sys._getframe to return a fake frame whose co_filename looks
    like a sales_agent source file, enabling deterministic testing.
    """
    fake_frame = MagicMock()
    fake_frame.f_code.co_filename = "/app/src/modules/sales_agent/workers/verify_pending_payments.py"
    fake_frame.f_back = None

    with patch("sys._getframe", return_value=fake_frame):
        return _infer_module_from_caller()


class TestInferModuleFromCaller:
    """Tests for the call-stack walker."""

    def test_infers_sales_agent_from_frame(self) -> None:
        """Infers 'sales_agent' when top frame is a sales_agent file."""
        result = _caller_from_sales_agent_path()
        assert result == "sales_agent"

    def test_infers_copilot_from_frame(self) -> None:
        """Infers 'copilot' when top frame is a copilot file."""
        fake_frame = MagicMock()
        fake_frame.f_code.co_filename = "/app/src/modules/copilot/application/orchestrator/chat.py"
        fake_frame.f_back = None

        with patch("sys._getframe", return_value=fake_frame):
            result = _infer_module_from_caller()

        assert result == "copilot"

    def test_infers_brand_from_frame(self) -> None:
        """Infers 'brand' when top frame is a brand file."""
        fake_frame = MagicMock()
        fake_frame.f_code.co_filename = "/app/src/modules/brand/infrastructure/repositories/brand_repository.py"
        fake_frame.f_back = None

        with patch("sys._getframe", return_value=fake_frame):
            result = _infer_module_from_caller()

        assert result == "brand"

    def test_fallback_none_for_frame_outside_modules(self) -> None:
        """Returns None when all frames are outside src/modules/."""
        # Frame chain: shared → adapter itself → None
        shared_frame = MagicMock()
        shared_frame.f_code.co_filename = "/app/src/shared/domain/events.py"
        shared_frame.f_back = None

        with patch("sys._getframe", return_value=shared_frame):
            result = _infer_module_from_caller()

        assert result is None

    def test_fallback_none_on_frame_exception(self) -> None:
        """Returns None (not an exception) when sys._getframe raises."""
        with patch("sys._getframe", side_effect=ValueError("no frame")):
            result = _infer_module_from_caller()

        assert result is None

    def test_walks_to_nested_frame(self) -> None:
        """Walks past non-module frames to find the first module frame."""
        # Frame 0 → shared (skip)
        # Frame 1 → brand (match)
        brand_frame = MagicMock()
        brand_frame.f_code.co_filename = "/app/src/modules/brand/workers/tasks.py"
        brand_frame.f_back = None

        shared_frame = MagicMock()
        shared_frame.f_code.co_filename = "/app/src/shared/domain/events.py"
        shared_frame.f_back = brand_frame

        with patch("sys._getframe", return_value=shared_frame):
            result = _infer_module_from_caller()

        assert result == "brand"


# ─── EventBusAdapter.publish module inference end-to-end ───────────────────


def _make_event(event_name: str = "test_event") -> DomainEvent:
    return DomainEvent(event_name=event_name, tenant_id=uuid4(), payload={})


class TestEventBusAdapterPublishWithInferredModule:
    """Verify EventBusAdapter.publish uses inferred module for flag lookup."""

    def test_publish_no_module_kwarg_infers_sales_agent_flag_on(self) -> None:
        """When module=None but inferred='sales_agent' + flag ON → outbox path."""
        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_event("payment_received")
        mock_session = MagicMock()

        with (
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._infer_module_from_caller",
                return_value="sales_agent",
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True),
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ),
        ):
            # No module= kwarg — adapter must infer it
            adapter.publish(event, session=mock_session)

        mock_outbox.enqueue_sync.assert_called_once()

    def test_publish_no_module_kwarg_infers_none_uses_default_flag_off(self) -> None:
        """When module=None, infer fails → default flag OFF → legacy path."""
        legacy_called: list[str] = []

        with (
            patch(
                "src.shared.domain.events.EventBus.publish",
                side_effect=lambda event, session=None: legacy_called.append(event.event_name),
            ),
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._infer_module_from_caller",
                return_value=None,
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False),
        ):
            adapter = EventBusAdapter()
            event = _make_event("brand_section_updated")
            adapter.publish(event, session=None)  # no module kwarg

        assert len(legacy_called) == 1

    def test_explicit_module_kwarg_overrides_inference(self) -> None:
        """Explicit module='copilot' takes precedence over stack inference."""
        mock_outbox = MagicMock()
        adapter = EventBusAdapter(outbox_service=mock_outbox)
        event = _make_event("copilot_card_emitted")
        mock_session = MagicMock()

        # Inference would return "sales_agent" but explicit kwarg = "copilot"
        with (
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._infer_module_from_caller",
                return_value="sales_agent",  # would be wrong without kwarg
            ),
            patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=True) as mock_flag,
            patch(
                "src.shared.domain_events.outbox.application.event_bus_adapter._is_async_session",
                return_value=False,
            ),
        ):
            adapter.publish(event, session=mock_session, module="copilot")

        # _is_outbox_enabled must have been called with "copilot", not "sales_agent"
        mock_flag.assert_called_once_with("copilot")

    def test_is_outbox_enabled_with_inferred_module_routes_correctly(self) -> None:
        """_is_outbox_enabled('sales_agent') respects USE_OUTBOX_PATTERN_SALES_AGENT."""
        import src.shared.domain_events.outbox.application.event_bus_adapter as _mod

        original = _mod.settings.USE_OUTBOX_PATTERN_SALES_AGENT
        try:
            object.__setattr__(_mod.settings, "USE_OUTBOX_PATTERN_SALES_AGENT", True)
            result = EventBusAdapter._is_outbox_enabled("sales_agent")
            assert result is True
        finally:
            object.__setattr__(_mod.settings, "USE_OUTBOX_PATTERN_SALES_AGENT", original)

    def test_is_outbox_enabled_none_uses_default(self) -> None:
        """_is_outbox_enabled(None) reads USE_OUTBOX_PATTERN_DEFAULT."""
        import src.shared.domain_events.outbox.application.event_bus_adapter as _mod

        original = _mod.settings.USE_OUTBOX_PATTERN_DEFAULT
        try:
            object.__setattr__(_mod.settings, "USE_OUTBOX_PATTERN_DEFAULT", False)
            result = EventBusAdapter._is_outbox_enabled(None)
            assert result is False
        finally:
            object.__setattr__(_mod.settings, "USE_OUTBOX_PATTERN_DEFAULT", original)
