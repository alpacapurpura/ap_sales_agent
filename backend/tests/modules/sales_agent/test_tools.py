"""
Unit tests for sales agent tool functions and tool executor dispatch.

Covers:
- Individual tool functions (success & error paths)
- TOOL_REGISTRY completeness
- node_tool_executor dispatch, unknown-tool handling, and no-pending-tool case
"""

import json
from unittest.mock import MagicMock, patch

from src.modules.sales_agent.application.agents.sales.tools import (
    TOOL_REGISTRY,
    tool_check_schedule,
    tool_escalate_to_human,
    tool_recommend_product,
    tool_send_payment_link,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _base_state(**overrides) -> dict:
    """Minimal AgentState dict for testing."""
    state = {
        "messages": [{"role": "user", "content": "Hola"}],
        "next_node": None,
        "user_id": None,
        "tenant_id": None,
        "session_id": "test-session",
        "current_state": "rapport",
        "detected_intent": "unknown",
        "lead_score": 0,
        "lead_data": {},
        "tenant_config": {},
        "history": [],
        "user_profile": {},
        "session_active": True,
        "active_enrollment": None,
        "active_product": None,
        "last_intent": None,
        "launch_stage": None,
        "agent_identity": "",
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "turn_count": 0,
        "customer_profile_id": None,
        "channel_type": None,
        "close_strategy": None,
        "internal_turn": 0,
        "error": None,
    }
    state.update(overrides)
    return state


_TRACE_PATCH = "src.modules.sales_agent.infrastructure.monitoring.tracing.trace_node"


def _noop_trace(name):
    """No-op replacement for trace_node decorator in tests."""

    def decorator(func):
        return func

    return decorator


# ---------------------------------------------------------------------------
# tool_send_payment_link
# ---------------------------------------------------------------------------


class TestSendPaymentLink:
    def test_success_with_checkout_url(self):
        state = _base_state(
            active_product={
                "id": "abc-123",
                "name": "Programa Premium",
                "checkout_page_url": "https://pay.example.com/premium",
            },
        )
        result = tool_send_payment_link(state)
        assert result["status"] == "success"
        assert "https://pay.example.com/premium" in result["url"]
        assert "Programa Premium" in result["message"]

    def test_error_when_no_checkout_url(self):
        state = _base_state(active_product={"id": "abc-123", "name": "Curso"})
        result = tool_send_payment_link(state)
        assert result["status"] == "error"
        assert "link de pago" in result["message"].lower()

    def test_error_when_no_active_product(self):
        state = _base_state(active_product=None)
        result = tool_send_payment_link(state)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# tool_check_schedule
# ---------------------------------------------------------------------------


class TestCheckSchedule:
    def test_error_when_no_calendar_type_id(self):
        state = _base_state(active_product={"id": "abc", "name": "Curso"})
        result = tool_check_schedule(state)
        assert result["status"] == "error"
        assert "agenda" in result["message"].lower()

    def test_error_when_no_db_session(self):
        state = _base_state(
            active_product={"id": "abc", "calendar_type_id": "cal-1"},
            tenant_id="aaaa0000-0000-0000-0000-000000000001",
        )
        result = tool_check_schedule(state, db=None)
        assert result["status"] == "error"

    def test_error_when_no_tenant_id(self):
        state = _base_state(
            active_product={"id": "abc", "calendar_type_id": "cal-1"},
            tenant_id=None,
        )
        mock_db = MagicMock()
        result = tool_check_schedule(state, db=mock_db)
        assert result["status"] == "error"

    @patch(
        "src.modules.sales_agent.application.agents.sales.tools.AvailabilityService",
        create=True,
    )
    def test_success_when_calendar_connected(self, _mock_cls):
        """When AvailabilityService is importable and calendar is connected."""
        mock_svc = MagicMock()
        mock_svc.is_connected.return_value = True

        with patch(
            "src.modules.scheduling.application.services.availability_service.AvailabilityService",
            return_value=mock_svc,
            create=True,
        ):
            state = _base_state(
                active_product={"id": "abc", "calendar_type_id": "cal-1"},
                tenant_id="aaaa0000-0000-0000-0000-000000000001",
            )
            mock_db = MagicMock()
            result = tool_check_schedule(state, db=mock_db)

        assert result["status"] == "success"
        assert "cal-1" in result["calendar_type_id"]


# ---------------------------------------------------------------------------
# tool_recommend_product
# ---------------------------------------------------------------------------


class TestRecommendProduct:
    def test_returns_lead_context(self):
        state = _base_state(
            qualification_answers={
                "main_pain": "no tengo tiempo",
                "budget_range": "5000-10000",
                "timeline": "este mes",
            },
        )
        result = tool_recommend_product(state)
        assert result["status"] == "success"
        assert result["lead_context"]["pain"] == "no tengo tiempo"
        assert result["lead_context"]["budget"] == "5000-10000"
        assert result["lead_context"]["timeline"] == "este mes"

    def test_returns_empty_context_when_no_qa(self):
        state = _base_state(qualification_answers={})
        result = tool_recommend_product(state)
        assert result["status"] == "success"
        assert result["lead_context"]["pain"] == ""
        assert result["lead_context"]["budget"] == ""
        assert result["lead_context"]["timeline"] == ""


# ---------------------------------------------------------------------------
# tool_escalate_to_human
# ---------------------------------------------------------------------------


class TestEscalateToHuman:
    def test_returns_escalated_status(self):
        state = _base_state()
        result = tool_escalate_to_human(state)
        assert result["status"] == "escalated"
        assert "conectarte" in result["message"]
        assert "equipo" in result["message"]


# ---------------------------------------------------------------------------
# TOOL_REGISTRY
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_has_all_canonical_tools(self):
        """TOOL_REGISTRY merges base + enrollment + scheduling tools."""
        expected = {
            # Base sales tools
            "send_payment_link",
            "check_schedule",
            "recommend_product",
            "escalate_to_human",
            # Enrollment tools (merged via ENROLLMENT_TOOL_REGISTRY)
            "list_public_editions",
            "create_enrollment",
            "generate_payment_link",
            "mark_enrollment_paid_manual",
            "list_waitlist",
            "promote_waitlist_to_edition",
            "check_payment_status",
            # Scheduling tools (S8 — SCHEDULING_TOOL_REGISTRY)
            "create_booking_link",
            "verify_booking_status",
            "get_available_slots",
        }
        assert set(TOOL_REGISTRY.keys()) == expected

    def test_all_values_are_callable(self):
        for name, fn in TOOL_REGISTRY.items():
            assert callable(fn), f"Tool '{name}' is not callable"


# ---------------------------------------------------------------------------
# node_tool_executor dispatch
# ---------------------------------------------------------------------------


class TestToolExecutor:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_dispatches_to_correct_tool(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            active_product={
                "id": "abc",
                "name": "Curso Premium",
                "checkout_page_url": "https://pay.example.com/curso",
            },
        )
        state["_pending_tool"] = {"tool": "send_payment_link", "args": {}}
        result = nodes_mod.node_tool_executor(state)

        assert result["_pending_tool"] is None
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "tool"

        content = json.loads(result["messages"][0]["content"])
        assert content["status"] == "success"
        assert "https://pay.example.com/curso" in content["url"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_unknown_tool_returns_error(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        state["_pending_tool"] = {"tool": "nonexistent_tool", "args": {}}
        result = nodes_mod.node_tool_executor(state)

        assert result["_pending_tool"] is None
        content = json.loads(result["messages"][0]["content"])
        assert content["status"] == "error"
        assert "nonexistent_tool" in content["message"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_no_pending_tool_returns_respond(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_tool_executor(state)
        assert result["next_node"] == "respond"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_tool_exception_returns_error_message(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        state["_pending_tool"] = {"tool": "send_payment_link", "args": {}}

        # Patch the TOOL_REGISTRY to raise an exception
        with patch(
            "src.modules.sales_agent.application.agents.sales.tools.TOOL_REGISTRY",
            {"send_payment_link": MagicMock(side_effect=RuntimeError("DB exploded"))},
        ):
            # Need to reload nodes again so the lazy import picks up the patched registry
            result = nodes_mod.node_tool_executor(state)

        assert result["_pending_tool"] is None
        content = json.loads(result["messages"][0]["content"])
        assert content["status"] == "error"
        assert "DB exploded" in content["message"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_passes_db_from_state(self):
        """Verifies that _db from state is forwarded to tool functions."""
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        mock_tool = MagicMock(return_value={"status": "success", "message": "ok"})

        state = _base_state()
        state["_pending_tool"] = {"tool": "mock_tool", "args": {}}
        mock_db = MagicMock()
        state["_db"] = mock_db

        with patch(
            "src.modules.sales_agent.application.agents.sales.tools.TOOL_REGISTRY",
            {"mock_tool": mock_tool},
        ):
            nodes_mod.node_tool_executor(state)

        mock_tool.assert_called_once_with(state, db=mock_db)
