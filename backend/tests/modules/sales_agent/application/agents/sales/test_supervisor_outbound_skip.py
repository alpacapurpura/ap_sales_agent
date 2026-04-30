"""PR-7 Sub-C — supervisor outbound skip-qualifier branch tests.

Asserts:
- ``outbound_mode=True`` + ``lead_score >= 40`` → next_node="closer" (no LLM call).
- ``outbound_mode=True`` + ``lead_score < 40`` → falls through to LLM normal routing.
- ``outbound_mode=False`` + ``lead_score=99`` → falls through (baseline preserved).

# [SALES-AGENT-OUTBOUND-PR7]
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.sales_agent.application.agents.sales.nodes import node_sales_supervisor


@pytest.fixture(autouse=True)
def _mute_trace_node_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    """``@trace_node`` persists to ``agent_traces`` on real ``SessionLocal``.

    These unit tests focus on supervisor routing logic, not tracing
    persistence. Mock ``SessionLocal`` + ``AuditRepository`` so the
    decorator no-ops cleanly without a live DB.
    """
    fake_session = MagicMock()
    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.monitoring.tracing.SessionLocal",
        lambda: fake_session,
    )

    class _NullRepo:
        def __init__(self, db: object) -> None:
            self.db = db

        def create_trace(self, **_kwargs: object) -> None:
            return None

        def close(self) -> None: ...

    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.monitoring.tracing.AuditRepository",
        _NullRepo,
    )


def _state(**overrides):
    base = {
        "messages": [{"role": "user", "content": "hola"}],
        "tenant_id": uuid4(),
        "user_id": uuid4(),
        "session_id": "sess",
        "current_state": "rapport",
        "detected_intent": None,
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
        "agent_identity": None,
        "brand_voice": None,
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "turn_count": 0,
        "customer_profile_id": None,
        "channel_type": "telegram",
        "close_strategy": None,
        "session_gap_hours": None,
        "last_session_summary": None,
        "is_returning_user": None,
        "consecutive_questions": 0,
        "follow_up_cadence": None,
        "internal_turn": 0,
        "_pending_tool": None,
        "_llm_service": None,
        "campaign_id": None,
        "campaign_instructions": None,
        "outbound_mode": False,
        "error": None,
        "next_node": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Outbound skip-qualifier branch
# ---------------------------------------------------------------------------


class TestOutboundSkipQualifier:
    """outbound_mode=True + lead_score>=40 → direct to closer, no LLM call."""

    def test_outbound_true_lead_score_40_skips_qualifier(self):
        state = _state(outbound_mode=True, lead_score=40)
        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            result = node_sales_supervisor(state)
            # Skip MUST happen BEFORE prompt loader call
            mock_loader.render.assert_not_called()
        assert result == {"next_node": "closer"}

    def test_outbound_true_lead_score_45_skips_qualifier(self):
        state = _state(outbound_mode=True, lead_score=45)
        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            result = node_sales_supervisor(state)
            mock_loader.render.assert_not_called()
        assert result == {"next_node": "closer"}

    def test_outbound_true_lead_score_99_skips_qualifier(self):
        state = _state(outbound_mode=True, lead_score=99)
        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            result = node_sales_supervisor(state)
            mock_loader.render.assert_not_called()
        assert result == {"next_node": "closer"}


class TestOutboundFallThroughLowScore:
    """outbound_mode=True + lead_score<40 → LLM normal routing (no skip)."""

    def test_outbound_true_lead_score_30_falls_through(self):
        state = _state(outbound_mode=True, lead_score=30)
        # LLM mock returns 'qualifier'
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "qualifier"
        state["_llm_service"] = mock_llm

        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            mock_loader.render.return_value = "supervisor system prompt"
            result = node_sales_supervisor(state)
            mock_loader.render.assert_called_once()  # LLM path WAS taken
        assert result == {"next_node": "qualifier"}

    def test_outbound_true_lead_score_zero_falls_through(self):
        state = _state(outbound_mode=True, lead_score=0)
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "qualifier"
        state["_llm_service"] = mock_llm

        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            mock_loader.render.return_value = "supervisor"
            result = node_sales_supervisor(state)
            mock_loader.render.assert_called_once()
        assert result == {"next_node": "qualifier"}

    def test_outbound_true_lead_score_39_falls_through(self):
        """Boundary: 39 < 40 → fall-through (LLM path), 40 → skip (closer)."""
        state = _state(outbound_mode=True, lead_score=39)
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "qualifier"
        state["_llm_service"] = mock_llm

        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            mock_loader.render.return_value = "supervisor"
            result = node_sales_supervisor(state)
            mock_loader.render.assert_called_once()
        assert result["next_node"] == "qualifier"


class TestInboundBaselinePreserved:
    """outbound_mode=False (default) → routing baseline preserved."""

    def test_inbound_lead_score_99_falls_through_normal_routing(self):
        """Inbound with HIGH lead_score must NOT skip — supervisor decides via LLM."""
        state = _state(outbound_mode=False, lead_score=99)
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "closer"
        state["_llm_service"] = mock_llm

        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            mock_loader.render.return_value = "supervisor"
            result = node_sales_supervisor(state)
            # Must invoke LLM (no skip)
            mock_loader.render.assert_called_once()
        assert result == {"next_node": "closer"}

    def test_inbound_default_lead_score_40_falls_through(self):
        """Inbound default mode + lead_score=40 → LLM path (NOT skip)."""
        state = _state(lead_score=40)  # outbound_mode=False default
        mock_llm = MagicMock()
        mock_llm.generate_response.return_value = "qualifier"
        state["_llm_service"] = mock_llm

        with patch("src.modules.sales_agent.application.agents.sales.nodes.prompt_loader") as mock_loader:
            mock_loader.render.return_value = "supervisor"
            result = node_sales_supervisor(state)
            mock_loader.render.assert_called_once()
        assert result == {"next_node": "qualifier"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
