"""Unit tests for individual sales graph nodes in isolation.

Tests each node function directly (not through the graph) to verify
prompt construction, LLM parameters, and state transformations.
"""

import importlib
from unittest.mock import patch, MagicMock

from src.core.enums import ModelRole
from src.modules.sales_agent.application.agents.sales.nodes import (
    _build_system_prompt,
    _determine_stage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TRACE_PATCH = "src.modules.sales_agent.infrastructure.monitoring.tracing.trace_node"


def _noop_trace(name):
    def decorator(func):
        return func
    return decorator


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


# ---------------------------------------------------------------------------
# _build_system_prompt tests
# ---------------------------------------------------------------------------


class TestBuildSystemPrompt:
    def test_prepends_agent_identity(self):
        state = _base_state(agent_identity="Soy Nicolify, tu asistente de ventas.")
        result = _build_system_prompt(state, "Skill prompt here")
        assert result.startswith("Soy Nicolify")
        assert "---" in result
        assert "Skill prompt here" in result

    def test_returns_skill_prompt_when_no_identity(self):
        state = _base_state(agent_identity="")
        result = _build_system_prompt(state, "Skill prompt here")
        assert result == "Skill prompt here"

    def test_returns_skill_prompt_when_identity_is_none(self):
        state = _base_state()
        state["agent_identity"] = None
        result = _build_system_prompt(state, "Skill prompt here")
        assert result == "Skill prompt here"


# ---------------------------------------------------------------------------
# Supervisor tests
# ---------------------------------------------------------------------------


class TestSupervisorNode:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_passes_accumulated_context_to_prompt(self):
        """Verify that node_sales_supervisor passes buying_signals_count,
        objection_count, etc. to prompt_loader.render."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state(
            buying_signals=[{"type": "a"}, {"type": "b"}, {"type": "c"}],
            objection_history=[{"type": "money"}, {"type": "time"}],
            qualification_answers={"q1": "a", "q2": "b", "q3": "c", "q4": "d"},
            turn_count=7,
            last_specialist="product_expert",
        )

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory, \
             patch.object(nodes_mod, "prompt_loader") as mock_prompt:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "qualifier"
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "routing prompt"

            nodes_mod.node_sales_supervisor(state)

            render_kwargs = mock_prompt.render.call_args.kwargs
            assert render_kwargs["buying_signals_count"] == 3
            assert render_kwargs["objection_count"] == 2
            assert render_kwargs["qualification_completeness"] == 4
            assert render_kwargs["turn_count"] == 7
            assert render_kwargs["last_specialist"] == "product_expert"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_supervisor_uses_fast_model_low_temperature(self):
        """Verify supervisor calls LLM with model_type='fast' and temperature=0.0."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state()

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory, \
             patch.object(nodes_mod, "prompt_loader") as mock_prompt:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "qualifier"
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "routing prompt"

            nodes_mod.node_sales_supervisor(state)

            call_kwargs = mock_service.generate_response.call_args.kwargs
            assert call_kwargs["model_type"] == ModelRole.FAST
            assert call_kwargs["temperature"] == 0.0
            assert call_kwargs["max_output_tokens"] == 10


# ---------------------------------------------------------------------------
# Qualifier tests
# ---------------------------------------------------------------------------


class TestQualifierNode:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_builds_system_prompt_with_identity(self):
        """Verify qualifier prepends agent_identity to the skill prompt."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state(agent_identity="Brand Identity: Nicolify Premium")

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory, \
             patch.object(nodes_mod, "prompt_loader") as mock_prompt:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "Hola! Cuéntame más."
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "qualifier skill prompt"

            nodes_mod.node_qualifier(state)

            call_kwargs = mock_service.generate_response.call_args.kwargs
            system_prompt = call_kwargs["system_prompt"]
            assert "Brand Identity: Nicolify Premium" in system_prompt
            assert "qualifier skill prompt" in system_prompt

    @patch(_TRACE_PATCH, _noop_trace)
    def test_qualifier_uses_smart_model(self):
        """Verify qualifier uses model_type='smart'."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state()

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory, \
             patch.object(nodes_mod, "prompt_loader") as mock_prompt:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "Respuesta"
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "prompt"

            nodes_mod.node_qualifier(state)

            call_kwargs = mock_service.generate_response.call_args.kwargs
            assert call_kwargs["model_type"] == ModelRole.REASONING
            assert call_kwargs["temperature"] == 0.2


# ---------------------------------------------------------------------------
# Closer tests
# ---------------------------------------------------------------------------


class TestCloserNode:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_closer_uses_higher_temperature(self):
        """Verify closer uses temperature=0.4 for more creative closing responses."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state()

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory, \
             patch.object(nodes_mod, "prompt_loader") as mock_prompt:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "Perfecto, aquí va tu link."
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "closer prompt"

            nodes_mod.node_closer(state)

            call_kwargs = mock_service.generate_response.call_args.kwargs
            assert call_kwargs["temperature"] == 0.4
            assert call_kwargs["model_type"] == ModelRole.REASONING


# ---------------------------------------------------------------------------
# Signal Accumulator stage progression tests
# ---------------------------------------------------------------------------


class TestSignalAccumulatorStageProgression:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_stage_progression_to_discovery(self):
        """1 qualification answer -> discovery."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="rapport",
            turn_count=1,
            messages=[{
                "role": "assistant",
                "content": '[QUALIFICATION_DATA: {"budget": "5k"}] Genial!',
            }],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["current_state"] == "discovery"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_stage_progression_to_presentation(self):
        """3 qualification answers -> presentation."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="discovery",
            turn_count=3,
            qualification_answers={"q1": "a", "q2": "b"},
            messages=[{
                "role": "assistant",
                "content": '[QUALIFICATION_DATA: {"q3": "c"}] Excelente!',
            }],
        )
        result = nodes_mod.node_signal_accumulator(state)
        # q1, q2 (existing) + q3 (new) = 3 answers -> presentation
        assert result["current_state"] == "presentation"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_stage_progression_to_closing(self):
        """score >= 70 and 3 buying signals -> closing."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="presentation",
            turn_count=5,
            lead_score=55,
            buying_signals=[
                {"type": "asked_price", "turn": 1},
                {"type": "mentioned_deadline", "turn": 2},
            ],
            messages=[{
                "role": "assistant",
                "content": '[SIGNALS: {"buying": ["ready_to_commit"], "objections": []}] Vamos!',
            }],
        )
        result = nodes_mod.node_signal_accumulator(state)
        # 55 base + 15 (1 buying signal) = 70, 3 total signals -> closing
        assert result["lead_score"] == 70
        assert len(result["buying_signals"]) == 3
        assert result["current_state"] == "closing"


# ---------------------------------------------------------------------------
# Escalation node tests
# ---------------------------------------------------------------------------


class TestEscalationNode:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_returns_handoff_message(self):
        """Verify escalation returns empathetic message and routes to respond."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_escalation(state)

        assert len(result["messages"]) == 1
        msg = result["messages"][0]
        assert msg["role"] == "assistant"
        assert "conectarte" in msg["content"]
        assert "equipo" in msg["content"]
        assert result["next_node"] == "respond"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_escalation_content_is_empathetic(self):
        """Handoff message should acknowledge the user's situation."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        importlib.reload(nodes_mod)

        state = _base_state()
        result = nodes_mod.node_escalation(state)
        content = result["messages"][0]["content"]
        assert "Entiendo perfectamente" in content


# ---------------------------------------------------------------------------
# _determine_stage pure function tests
# ---------------------------------------------------------------------------


class TestDetermineStageFromNodes:
    def test_closing_requires_both_score_and_signals(self):
        """High score alone is not enough - need >= 3 signals too."""
        state = _base_state(lead_score=80)
        # High score but only 2 signals -> NOT closing
        updates = {
            "lead_score": 80,
            "buying_signals": [
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
            ],
        }
        assert _determine_stage(state, updates) != "closing"

    def test_enough_signals_but_low_score_not_closing(self):
        """3 signals but low score -> NOT closing."""
        state = _base_state(lead_score=50)
        updates = {
            "lead_score": 50,
            "buying_signals": [
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
        }
        assert _determine_stage(state, updates) != "closing"

    def test_exactly_at_threshold_triggers_closing(self):
        """score == 70 and exactly 3 signals -> closing."""
        state = _base_state()
        updates = {
            "lead_score": 70,
            "buying_signals": [
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
        }
        assert _determine_stage(state, updates) == "closing"

    def test_updates_override_state_for_stage_calculation(self):
        """Updates should take priority over state for qualification_answers."""
        state = _base_state(qualification_answers={"old": "data"})
        updates = {
            "qualification_answers": {"q1": "a", "q2": "b", "q3": "c"},
        }
        assert _determine_stage(state, updates) == "presentation"
