"""
Unit tests for the sales subgraph topology and node logic.

Covers:
- Supervisor routing decisions
- Signal accumulator: block extraction, scoring, stage transitions, turn counting
- Escalation node output
- Tool executor stub behavior
- Graph topology (edges, conditional routing)
"""

from unittest.mock import MagicMock, patch

from luana_core_sales_agent.application.agents.sales.nodes import (
    _determine_stage,
    _extract_json_block,
    _strip_blocks,
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


# Shared mock patcher for tracing (prevents DB connections in tests)
_TRACE_PATCH = "luana_core_sales_agent.infrastructure.monitoring.tracing.trace_node"


def _noop_trace(name):
    """No-op replacement for trace_node decorator in tests."""

    def decorator(func):
        return func

    return decorator


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestExtractJsonBlock:
    def test_extracts_qualification_data(self):
        text = 'Hola! [QUALIFICATION_DATA: {"budget": "5000", "timeline": "2 weeks"}] que tal?'
        result = _extract_json_block(text, "QUALIFICATION_DATA")
        assert result == {"budget": "5000", "timeline": "2 weeks"}

    def test_extracts_signals_block(self):
        text = '[SIGNALS: {"buying": ["asked_price", "mentioned_deadline"], "objections": ["too_expensive"]}]'
        result = _extract_json_block(text, "SIGNALS")
        assert result == {
            "buying": ["asked_price", "mentioned_deadline"],
            "objections": ["too_expensive"],
        }

    def test_returns_none_for_missing_block(self):
        text = "Just a regular message without blocks."
        result = _extract_json_block(text, "QUALIFICATION_DATA")
        assert result is None

    def test_returns_none_for_invalid_json(self):
        text = "[QUALIFICATION_DATA: {invalid json here}]"
        result = _extract_json_block(text, "QUALIFICATION_DATA")
        assert result is None

    def test_extracts_tool_request(self):
        text = '[TOOL_REQUEST: {"tool": "check_availability", "args": {"date": "2026-04-01"}}]'
        result = _extract_json_block(text, "TOOL_REQUEST")
        assert result == {"tool": "check_availability", "args": {"date": "2026-04-01"}}


class TestStripBlocks:
    def test_strips_all_block_types(self):
        text = (
            "Hola! "
            '[QUALIFICATION_DATA: {"budget": "5k"}] '
            "Te cuento sobre el programa. "
            '[SIGNALS: {"buying": ["asked_price"], "objections": []}] '
            '[TOOL_REQUEST: {"tool": "schedule"}]'
        )
        result = _strip_blocks(text)
        assert "QUALIFICATION_DATA" not in result
        assert "SIGNALS" not in result
        assert "TOOL_REQUEST" not in result
        assert "Hola!" in result
        assert "Te cuento sobre el programa." in result

    def test_returns_clean_text_unchanged(self):
        text = "Just a normal message."
        result = _strip_blocks(text)
        assert result == text


class TestDetermineStage:
    def test_closing_when_high_score_and_signals(self):
        state = _base_state(lead_score=60)
        updates = {
            "lead_score": 75,
            "buying_signals": [
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
        }
        assert _determine_stage(state, updates) == "closing"

    def test_presentation_when_enough_qa(self):
        state = _base_state()
        updates = {
            "qualification_answers": {"q1": "a", "q2": "b", "q3": "c"},
        }
        assert _determine_stage(state, updates) == "presentation"

    def test_discovery_when_some_qa(self):
        state = _base_state()
        updates = {
            "qualification_answers": {"q1": "a"},
        }
        assert _determine_stage(state, updates) == "discovery"

    def test_rapport_at_turn_zero(self):
        state = _base_state(turn_count=0)
        updates = {}
        assert _determine_stage(state, updates) == "rapport"

    def test_preserves_current_state_when_no_change(self):
        state = _base_state(current_state="discovery", turn_count=5)
        updates = {}
        assert _determine_stage(state, updates) == "discovery"


# ---------------------------------------------------------------------------
# Node tests (with mocked tracing and LLM)
# ---------------------------------------------------------------------------


class TestSupervisorRouting:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_routes_to_qualifier_for_unknown_intent(self):
        # Re-import after patching trace_node so the decorator is no-op
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(detected_intent="unknown", current_state="rapport")
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "qualifier"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                result = nodes_mod.node_sales_supervisor(state)

        assert result["next_node"] == "qualifier"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_routes_to_closer_for_closing_stage(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(detected_intent="buy", current_state="closing")
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "closer"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                result = nodes_mod.node_sales_supervisor(state)

        assert result["next_node"] == "closer"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_fallback_to_closer_in_closing_stage_for_invalid_decision(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(current_state="closing")
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "nonexistent_node"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                result = nodes_mod.node_sales_supervisor(state)

        assert result["next_node"] == "closer"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_fallback_to_qualifier_in_non_closing_stage_for_invalid_decision(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(current_state="rapport")
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "invalid_garbage"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                result = nodes_mod.node_sales_supervisor(state)

        assert result["next_node"] == "qualifier"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_scheduler_maps_to_closer(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "scheduler"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                result = nodes_mod.node_sales_supervisor(state)

        assert result["next_node"] == "closer"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_supervisor_passes_accumulated_context_to_prompt(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            buying_signals=[{"type": "a"}, {"type": "b"}],
            objection_history=[{"type": "x"}],
            qualification_answers={"q1": "a", "q2": "b"},
            turn_count=5,
        )
        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "qualifier"
            mock_llm_factory.get_service.return_value = mock_service
            with patch.object(nodes_mod, "prompt_loader") as mock_prompt:
                mock_prompt.render.return_value = "routing prompt"
                nodes_mod.node_sales_supervisor(state)

                # Verify accumulated context was passed to the prompt
                render_kwargs = mock_prompt.render.call_args
                assert render_kwargs.kwargs["buying_signals_count"] == 2
                assert render_kwargs.kwargs["objection_count"] == 1
                assert render_kwargs.kwargs["qualification_completeness"] == 2
                assert render_kwargs.kwargs["turn_count"] == 5


class TestSignalAccumulator:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_extracts_qualification_data_block(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            messages=[
                {
                    "role": "assistant",
                    "content": 'Genial! [QUALIFICATION_DATA: {"budget": "10k", "team_size": "5"}] Te cuento...',
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["qualification_answers"] == {"budget": "10k", "team_size": "5"}

    @patch(_TRACE_PATCH, _noop_trace)
    def test_extracts_signals_block(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            messages=[
                {
                    "role": "assistant",
                    "content": '[SIGNALS: {"buying": ["asked_price"], "objections": ["too_expensive"]}] Ok!',
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert len(result["buying_signals"]) == 1
        assert result["buying_signals"][0]["type"] == "asked_price"
        assert len(result["objection_history"]) == 1
        assert result["objection_history"][0]["type"] == "too_expensive"
        assert result["objection_history"][0]["resolved"] is False

    @patch(_TRACE_PATCH, _noop_trace)
    def test_strips_blocks_from_output(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        raw_msg = 'Hola! [QUALIFICATION_DATA: {"budget": "5k"}] Te cuento sobre el programa.'
        state = _base_state(
            messages=[{"role": "assistant", "content": raw_msg}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert "messages" in result
        clean_content = result["messages"][0]["content"]
        assert "QUALIFICATION_DATA" not in clean_content
        assert "Hola!" in clean_content
        assert "Te cuento sobre el programa." in clean_content

    @patch(_TRACE_PATCH, _noop_trace)
    def test_increments_turn_count(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(turn_count=3)
        result = nodes_mod.node_signal_accumulator(state)
        assert result["turn_count"] == 4

    @patch(_TRACE_PATCH, _noop_trace)
    def test_increments_internal_turn(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(internal_turn=1)
        result = nodes_mod.node_signal_accumulator(state)
        assert result["internal_turn"] == 2

    @patch(_TRACE_PATCH, _noop_trace)
    def test_stage_transitions(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        # Starts in rapport, adds qualification data → should transition to discovery
        state = _base_state(
            current_state="rapport",
            turn_count=1,
            messages=[
                {
                    "role": "assistant",
                    "content": '[QUALIFICATION_DATA: {"budget": "5k"}] Genial!',
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["current_state"] == "discovery"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_lead_score_increases_with_qualification_data(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            lead_score=20,
            messages=[
                {
                    "role": "assistant",
                    "content": '[QUALIFICATION_DATA: {"budget": "5k", "team": "10"}] Ok!',
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        # 20 base + 10*2 (two qual fields) = 40
        assert result["lead_score"] == 40

    @patch(_TRACE_PATCH, _noop_trace)
    def test_lead_score_capped_at_100(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            lead_score=95,
            messages=[
                {
                    "role": "assistant",
                    "content": (
                        '[QUALIFICATION_DATA: {"a": "1", "b": "2"}] '
                        '[SIGNALS: {"buying": ["x", "y"], "objections": []}] Ok!'
                    ),
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["lead_score"] == 100

    @patch(_TRACE_PATCH, _noop_trace)
    def test_tool_request_routes_to_tool_executor(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            messages=[
                {
                    "role": "assistant",
                    "content": '[TOOL_REQUEST: {"tool": "schedule", "args": {}}] Un momento...',
                },
            ],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["next_node"] == "tool_executor"
        assert result["_pending_tool"] == {"tool": "schedule", "args": {}}

    @patch(_TRACE_PATCH, _noop_trace)
    def test_default_routes_to_respond(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_signal_accumulator(state)
        assert result["next_node"] == "respond"


class TestEscalationNode:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_produces_handoff_message(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_escalation(state)
        assert len(result["messages"]) == 1
        msg = result["messages"][0]
        assert msg["role"] == "assistant"
        assert "conectarte" in msg["content"]
        assert "equipo" in msg["content"]


class TestToolExecutor:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_returns_respond_when_no_pending_tool(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_tool_executor(state)
        assert result["next_node"] == "respond"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_executes_registered_tool_and_clears_pending(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            active_product={
                "name": "Curso Premium",
                "checkout_page_url": "https://pay.example.com/curso",
            },
        )
        state["_pending_tool"] = {"tool": "send_payment_link", "args": {}}
        result = nodes_mod.node_tool_executor(state)
        assert result["_pending_tool"] is None
        assert result["messages"][0]["role"] == "tool"
        assert "pay.example.com" in result["messages"][0]["content"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_returns_error_for_unknown_tool(self):
        import importlib

        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state()
        state["_pending_tool"] = {"tool": "nonexistent", "args": {}}
        result = nodes_mod.node_tool_executor(state)
        assert result["_pending_tool"] is None
        assert result["messages"][0]["role"] == "tool"
        assert "not found" in result["messages"][0]["content"]


# ---------------------------------------------------------------------------
# Graph topology tests
# ---------------------------------------------------------------------------


class TestGraphRouting:
    def test_route_after_supervisor_valid_nodes(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_supervisor,
        )

        for node in [
            "qualifier",
            "product_expert",
            "closer",
            "tool_executor",
            "escalate",
            "respond",
        ]:
            state = _base_state(next_node=node)
            assert _route_after_supervisor(state) == node

    def test_route_after_supervisor_invalid_falls_back_to_qualifier(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_supervisor,
        )

        state = _base_state(next_node="nonexistent")
        assert _route_after_supervisor(state) == "qualifier"

    def test_route_after_supervisor_none_falls_back_to_qualifier(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_supervisor,
        )

        state = _base_state(next_node=None)
        assert _route_after_supervisor(state) == "qualifier"

    def test_route_after_accumulator_respond(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_accumulator,
        )

        state = _base_state(next_node="respond")
        assert _route_after_accumulator(state) == "respond"

    def test_route_after_accumulator_tool_executor(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_accumulator,
        )

        state = _base_state(next_node="tool_executor")
        assert _route_after_accumulator(state) == "tool_executor"

    def test_route_after_accumulator_default_respond(self):
        from luana_core_sales_agent.application.agents.sales.graph import (
            _route_after_accumulator,
        )

        state = _base_state(next_node=None)
        assert _route_after_accumulator(state) == "respond"
