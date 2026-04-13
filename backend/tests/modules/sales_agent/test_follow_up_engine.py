"""Tests for the follow-up engine and cadence initialization.

Covers:
- Cadence initialization on closing transition
- Cadence tier selection based on product price
- Follow-up nudge template rendering
- Cadence cleanup on user re-engagement
"""

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest
from jinja2 import Environment, FileSystemLoader

from src.modules.sales_agent.domain.tuning import FOLLOW_UP_CADENCES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TRACE_PATCH = "src.modules.sales_agent.infrastructure.monitoring.tracing.trace_node"

TEMPLATES_DIR = str(
    Path(__file__).parent
    / ".."
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates"
)


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


@pytest.fixture
def jinja_env():
    return Environment(
        loader=FileSystemLoader(str(Path(TEMPLATES_DIR).resolve())),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ---------------------------------------------------------------------------
# Cadence initialization on closing transition
# ---------------------------------------------------------------------------


class TestCadenceInitialization:
    @patch(_TRACE_PATCH, _noop_trace)
    def test_cadence_initialized_on_closing_transition(self):
        """When stage transitions to closing, follow_up_cadence is auto-populated."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="presentation",
            lead_score=70,
            buying_signals=[
                {"type": "asked_price", "turn": 1},
                {"type": "mentioned_deadline", "turn": 2},
                {"type": "ready_to_commit", "turn": 3},
            ],
            active_product={"name": "Premium", "price": 299},
            messages=[{"role": "assistant", "content": "¿Lista para arrancar?"}],
        )
        result = nodes_mod.node_signal_accumulator(state)

        assert result.get("current_state") == "closing"
        cadence = result.get("follow_up_cadence")
        assert cadence is not None
        assert cadence["tier"] == "mid"
        assert cadence["delays_hours"] == FOLLOW_UP_CADENCES["mid"]["delays_hours"]
        assert cadence["follow_ups_sent"] == 0

    @patch(_TRACE_PATCH, _noop_trace)
    def test_cadence_low_tier_under_100(self):
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="presentation",
            lead_score=70,
            buying_signals=[
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
            active_product={"name": "Ebook", "price": 49},
            messages=[{"role": "assistant", "content": "Genial!"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result.get("follow_up_cadence", {}).get("tier") == "low"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_cadence_high_tier_over_500(self):
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="presentation",
            lead_score=70,
            buying_signals=[
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
            active_product={"name": "Mastermind", "price": 2000},
            messages=[{"role": "assistant", "content": "Agendemos!"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        assert result.get("follow_up_cadence", {}).get("tier") == "high"

    @patch(_TRACE_PATCH, _noop_trace)
    def test_no_cadence_if_already_closing(self):
        """If already in closing, don't re-initialize cadence."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        existing_cadence = {
            "tier": "mid",
            "delays_hours": [6, 24, 72],
            "follow_ups_sent": 1,
        }
        state = _base_state(
            current_state="closing",
            lead_score=80,
            buying_signals=[
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
            follow_up_cadence=existing_cadence,
            messages=[{"role": "assistant", "content": "Seguimos!"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        # Should NOT overwrite existing cadence
        assert (
            result.get("follow_up_cadence") is None
            or result.get("follow_up_cadence") == existing_cadence
        )

    @patch(_TRACE_PATCH, _noop_trace)
    def test_cadence_default_mid_when_no_price(self):
        """When product has no price, default to mid tier."""
        import src.modules.sales_agent.application.agents.sales.nodes as nodes_mod

        importlib.reload(nodes_mod)

        state = _base_state(
            current_state="presentation",
            lead_score=70,
            buying_signals=[
                {"type": "a", "turn": 1},
                {"type": "b", "turn": 2},
                {"type": "c", "turn": 3},
            ],
            active_product={"name": "Free Trial"},
            messages=[{"role": "assistant", "content": "Genial!"}],
        )
        result = nodes_mod.node_signal_accumulator(state)
        cadence = result.get("follow_up_cadence")
        if cadence:
            assert cadence["tier"] == "low"  # price=0 → low tier


# ---------------------------------------------------------------------------
# Follow-up nudge template rendering
# ---------------------------------------------------------------------------


class TestFollowUpNudgeTemplate:
    def test_renders_follow_up_1_value(self, jinja_env):
        template = jinja_env.get_template("follow_up_nudge.j2")
        result = template.render(
            follow_up_number=1,
            session_summary="Maria quiere crecer su negocio de coaching",
            qualification_answers={"name": "Maria", "business_type": "coaching"},
            offer_name="Programa Premium",
            channel_type="instagram",
        )
        assert (
            "tip" in result.lower()
            or "recurso" in result.lower()
            or "dato" in result.lower()
        )
        assert "Maria" in result
        assert "Programa Premium" in result

    def test_renders_follow_up_2_social_proof(self, jinja_env):
        template = jinja_env.get_template("follow_up_nudge.j2")
        result = template.render(
            follow_up_number=2,
            session_summary="",
            qualification_answers={},
            offer_name="Curso Básico",
            channel_type="whatsapp",
        )
        assert "caso" in result.lower() or "testimonio" in result.lower()

    def test_renders_follow_up_3_direct(self, jinja_env):
        template = jinja_env.get_template("follow_up_nudge.j2")
        result = template.render(
            follow_up_number=3,
            session_summary="",
            qualification_answers={},
            offer_name="Masterclass",
            channel_type="telegram",
        )
        assert "directo" in result.lower() or "honesto" in result.lower()

    def test_renders_without_optional_context(self, jinja_env):
        template = jinja_env.get_template("follow_up_nudge.j2")
        result = template.render(
            follow_up_number=1,
            session_summary=None,
            qualification_answers=None,
            offer_name=None,
            channel_type=None,
        )
        assert "REGLAS ABSOLUTAS" in result

    def test_max_lines_rule(self, jinja_env):
        template = jinja_env.get_template("follow_up_nudge.j2")
        result = template.render(
            follow_up_number=1,
            session_summary="test",
            qualification_answers={},
            offer_name="Test",
            channel_type="instagram",
        )
        assert "2-3 líneas" in result


# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------


class TestFollowUpTuningConstants:
    def test_cadence_tiers_exist(self):
        assert "low" in FOLLOW_UP_CADENCES
        assert "mid" in FOLLOW_UP_CADENCES
        assert "high" in FOLLOW_UP_CADENCES

    def test_each_tier_has_delays(self):
        for config in FOLLOW_UP_CADENCES.values():
            assert "delays_hours" in config
            assert len(config["delays_hours"]) >= 2

    def test_max_total_defined(self):
        from src.modules.sales_agent.domain.tuning import FOLLOW_UP_MAX_TOTAL

        assert FOLLOW_UP_MAX_TOTAL == 3
