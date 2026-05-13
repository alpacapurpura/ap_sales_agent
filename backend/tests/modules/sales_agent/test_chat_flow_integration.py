"""Integration test: simulates multi-turn conversations through the sales graph.

Tests the full graph flow end-to-end with mocked LLM and tracing to verify
that state propagates correctly across supervisor → specialist → signal_accumulator.
"""

import importlib
from unittest.mock import MagicMock, patch

from luana_core_sales_agent.application.orchestrator.state import create_initial_state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(**overrides):
    """Helper to create a test state with defaults."""
    base = create_initial_state(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
        session_id="test-session",
        agent_identity="Test Brand Identity",
    )
    base.update(overrides)
    return base


# No-op replacement for trace_node to avoid DB connections
_TRACE_PATCH = "luana_core_sales_agent.infrastructure.monitoring.tracing.trace_node"


def _noop_trace(name):
    def decorator(func):
        return func

    return decorator


def _reload_graph():
    """Reload nodes and graph modules after patching trace_node."""
    import src.modules.sales_agent.application.agents.sales.graph as graph_mod
    import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

    importlib.reload(nodes_mod)
    importlib.reload(graph_mod)
    return nodes_mod, graph_mod


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestChatFlowIntegration:
    """End-to-end graph flow tests with mocked LLM."""

    @patch(_TRACE_PATCH, _noop_trace)
    def test_new_user_routes_to_qualifier(self):
        """State with no signals -> supervisor returns 'qualifier' ->
        qualifier generates response -> signal_accumulator processes ->
        state has incremented turn_count."""
        nodes_mod, graph_mod = _reload_graph()

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "system prompt"

            # Supervisor returns "qualifier", qualifier returns a simple response
            mock_service.generate_response.side_effect = [
                "qualifier",  # supervisor call
                "Hola! Cuéntame sobre ti.",  # qualifier call
            ]

            graph = graph_mod.create_sales_subgraph()
            state = _make_state(messages=[{"role": "user", "content": "Hola"}])
            result = graph.invoke(state)

        assert result["turn_count"] == 1
        # The final messages reflect the last node's output.
        # Since qualifier returned a clean message (no blocks), signal_accumulator
        # doesn't override messages, so the qualifier's message persists.
        last_msg = result["messages"][-1]
        assert last_msg["role"] == "assistant"
        assert "Hola" in last_msg["content"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_qualification_data_extracted(self):
        """Qualifier returns QUALIFICATION_DATA block -> signal_accumulator
        extracts it -> state.qualification_answers has the data."""
        nodes_mod, graph_mod = _reload_graph()

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "system prompt"

            mock_service.generate_response.side_effect = [
                "qualifier",
                'Hola Ana! [QUALIFICATION_DATA: {"name": "Ana", "main_pain": "no time"}] Cuéntame más.',
            ]

            graph = graph_mod.create_sales_subgraph()
            state = _make_state(messages=[{"role": "user", "content": "Hola soy Ana"}])
            result = graph.invoke(state)

        assert result["qualification_answers"]["name"] == "Ana"
        assert result["qualification_answers"]["main_pain"] == "no time"
        # Blocks should be stripped from the output message
        last_msg = result["messages"][-1]
        assert "QUALIFICATION_DATA" not in last_msg["content"]
        assert "Ana" in last_msg["content"]

    @patch(_TRACE_PATCH, _noop_trace)
    def test_buying_signal_increments_score(self):
        """Response with SIGNALS block -> lead_score increases by 15 per signal."""
        nodes_mod, graph_mod = _reload_graph()

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "system prompt"

            mock_service.generate_response.side_effect = [
                "qualifier",
                'Genial! [SIGNALS: {"buying": ["interest_after_explanation"], "objections": []}] Te cuento.',
            ]

            graph = graph_mod.create_sales_subgraph()
            state = _make_state(
                messages=[{"role": "user", "content": "Me interesa"}],
                lead_score=10,
            )
            result = graph.invoke(state)

        # 10 base + 15 for 1 buying signal = 25
        assert result["lead_score"] == 25
        assert len(result["buying_signals"]) == 1
        assert result["buying_signals"][0]["type"] == "interest_after_explanation"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_tool_request_routes_to_tool_executor(self):
        """Response with TOOL_REQUEST -> signal_accumulator sets next_node='tool_executor'
        -> tool_executor runs -> loops back to supervisor -> responds.
        Verifies the _pending_tool was set and cleared during the flow."""
        nodes_mod, graph_mod = _reload_graph()

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "system prompt"

            mock_service.generate_response.side_effect = [
                "closer",  # supervisor (1st pass)
                'Aquí va el link [TOOL_REQUEST: {"tool": "send_payment_link"}]',  # closer
                "respond",  # supervisor (2nd pass, after tool)
            ]

            graph = graph_mod.create_sales_subgraph()
            state = _make_state(
                messages=[{"role": "user", "content": "Quiero pagar"}],
                active_product={
                    "name": "Curso Premium",
                    "checkout_page_url": "https://pay.example.com/curso",
                },
            )
            result = graph.invoke(state)

        # The graph completed the full loop: supervisor -> closer -> accumulator
        # -> tool_executor -> supervisor -> END
        # LLM was called 3 times (2 supervisor + 1 closer)
        assert mock_service.generate_response.call_count == 3
        # The pending tool should be cleared after execution
        assert result.get("_pending_tool") is None
        # Turn count incremented by signal_accumulator
        assert result["turn_count"] == 1

    @patch(_TRACE_PATCH, _noop_trace)
    def test_state_persists_across_turns(self):
        """Verify that pre-existing state (turn_count, buying_signals, etc.)
        carries through graph execution and gets updated."""
        nodes_mod, graph_mod = _reload_graph()

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "system prompt"

            mock_service.generate_response.side_effect = [
                "qualifier",
                "Perfecto, vamos avanzando.",
            ]

            existing_signals = [
                {"type": "asked_price", "turn": 1},
                {"type": "mentioned_deadline", "turn": 2},
            ]
            graph = graph_mod.create_sales_subgraph()
            state = _make_state(
                messages=[{"role": "user", "content": "Sí, dime más"}],
                turn_count=3,
                buying_signals=existing_signals,
                lead_score=30,
                qualification_answers={"budget": "10k"},
            )
            result = graph.invoke(state)

        # turn_count should have incremented from 3 to 4
        assert result["turn_count"] == 4
        # Previous buying signals should persist
        assert len(result["buying_signals"]) >= 2
        # Previous lead score should persist (no new signals = no score change beyond qual)
        assert result["lead_score"] >= 30
        # Qualification answers should persist
        assert result["qualification_answers"]["budget"] == "10k"
