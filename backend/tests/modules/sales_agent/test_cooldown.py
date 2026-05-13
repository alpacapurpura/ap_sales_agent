"""Tests for session cooldown, gap temporal calculation, and state enrichment.

Covers:
- session_gap_hours calculation from time_diff
- is_returning_user flag
- create_initial_state with new fields
- consecutive_questions tracking in signal_accumulator
"""

import importlib
from unittest.mock import MagicMock, patch

from luana_core_sales_agent.application.orchestrator.state import create_initial_state

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TRACE_PATCH = "luana_core_sales_agent.infrastructure.monitoring.tracing.trace_node"


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
        "session_gap_hours": None,
        "last_session_summary": None,
        "is_returning_user": None,
        "consecutive_questions": 0,
        "follow_up_cadence": None,
    }
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# create_initial_state with new fields
# ---------------------------------------------------------------------------


class TestCreateInitialStateNewFields:
    def test_session_gap_hours_passed(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
            session_gap_hours=12.5,
        )
        assert state["session_gap_hours"] == 12.5

    def test_last_session_summary_passed(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
            last_session_summary="Maria interested in course",
        )
        assert state["last_session_summary"] == "Maria interested in course"

    def test_is_returning_user_passed(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
            is_returning_user=True,
        )
        assert state["is_returning_user"] is True

    def test_consecutive_questions_defaults_to_zero(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
        )
        assert state["consecutive_questions"] == 0

    def test_consecutive_questions_passed(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
            consecutive_questions=3,
        )
        assert state["consecutive_questions"] == 3

    def test_follow_up_cadence_passed(self):
        cadence = {"delays_hours": [6, 24, 72], "last_follow_up_at": None}
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
            follow_up_cadence=cadence,
        )
        assert state["follow_up_cadence"] == cadence

    def test_defaults_when_not_provided(self):
        state = create_initial_state(
            user_id="user-1",
            tenant_id="tenant-1",
        )
        assert state["session_gap_hours"] is None
        assert state["last_session_summary"] is None
        assert state["is_returning_user"] is None
        assert state["follow_up_cadence"] is None


# ---------------------------------------------------------------------------
# consecutive_questions tracking in signal_accumulator
# ---------------------------------------------------------------------------


class TestConsecutiveQuestionsTracking:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_increments_when_next_node_is_qualifier(self):
        """When the current routing was to qualifier, consecutive_questions increments."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            next_node="qualifier",
            consecutive_questions=2,
            messages=[{"role": "assistant", "content": "¿Cuéntame más?"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["consecutive_questions"] == 3

    @patch(_TRACE_PATCH, _noop_trace)
    def test_resets_when_next_node_is_not_qualifier(self):
        """When routing was to product_expert/closer, consecutive_questions resets to 0."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            next_node="product_expert",
            consecutive_questions=5,
            messages=[{"role": "assistant", "content": "Este programa incluye..."}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["consecutive_questions"] == 0

    @patch(_TRACE_PATCH, _noop_trace)
    def test_resets_when_next_node_is_closer(self):
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            next_node="closer",
            consecutive_questions=3,
            messages=[{"role": "assistant", "content": "¿Lista para arrancar?"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result["consecutive_questions"] == 0


# ---------------------------------------------------------------------------
# Supervisor receives consecutive_questions and session_gap_hours
# ---------------------------------------------------------------------------


class TestSupervisorContextEnrichment:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_passes_consecutive_questions_to_prompt(self):
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(consecutive_questions=4, session_gap_hours=48.0)

        with (
            patch.object(nodes_mod, "LLMFactory") as mock_llm_factory,
            patch.object(nodes_mod, "prompt_loader") as mock_prompt,
        ):
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "product_expert"
            mock_llm_factory.get_service.return_value = mock_service
            mock_prompt.render.return_value = "routing prompt"

            nodes_mod.node_sales_supervisor(state)

            render_kwargs = mock_prompt.render.call_args.kwargs
            assert render_kwargs["consecutive_questions"] == 4
            assert render_kwargs["session_gap_hours"] == 48.0

    @patch(_TRACE_PATCH, _noop_trace)
    def test_qualifier_session_continuity_lands_in_volatile_suffix(self):
        """Post-S3: cooldown context lives in volatile session_continuity slot
        (after CACHE_BOUNDARY_MARKER) — NOT in the cacheable prefix where it
        would poison the cache."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod
        from luana_core_sales_agent.application.prompts.compose import (
            CACHE_BOUNDARY_MARKER,
        )

        importlib.reload(nodes_mod)

        state = _base_state(consecutive_questions=3, session_gap_hours=12.0)

        with patch.object(nodes_mod, "LLMFactory") as mock_llm_factory:
            mock_service = MagicMock()
            mock_service.generate_response.return_value = "Interesante, ¿y qué haces?"
            mock_llm_factory.get_service.return_value = mock_service

            nodes_mod.node_qualifier(state)

            call_kwargs = mock_service.generate_response.call_args.kwargs
            system_prompt = call_kwargs["system_prompt"]
            assert CACHE_BOUNDARY_MARKER in system_prompt
            suffix = system_prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[1]
            assert "12.0 horas" in suffix
            assert "3 preguntas consecutivas" in suffix


# ---------------------------------------------------------------------------
# Checkpoint persistence of new fields
# ---------------------------------------------------------------------------


class TestCheckpointNewFields:
    def test_save_and_load_consecutive_questions(self, db, tenant_id, lead_id):
        from luana_core_sales_agent.infrastructure.repositories.state_repository import (
            StateRepository,
        )

        repo = StateRepository(db)
        cp = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-fatigue",
            current_stage="discovery",
            lead_score=20,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=3,
            consecutive_questions=2,
            follow_up_cadence={"delays_hours": [6, 24, 72]},
        )

        assert cp.consecutive_questions == 2
        assert cp.follow_up_cadence == {"delays_hours": [6, 24, 72]}

        loaded = repo.get_active_checkpoint(tenant_id, lead_id)
        assert loaded.consecutive_questions == 2
        assert loaded.follow_up_cadence == {"delays_hours": [6, 24, 72]}

    def test_defaults_to_zero_when_not_set(self, db, tenant_id, lead_id):
        from luana_core_sales_agent.infrastructure.repositories.state_repository import (
            StateRepository,
        )

        repo = StateRepository(db)
        cp = repo.save_checkpoint(
            tenant_id=tenant_id,
            lead_id=lead_id,
            session_id="sess-defaults",
            current_stage="rapport",
            lead_score=0,
            lead_data={},
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=0,
        )

        assert cp.consecutive_questions == 0
        assert cp.follow_up_cadence is None
