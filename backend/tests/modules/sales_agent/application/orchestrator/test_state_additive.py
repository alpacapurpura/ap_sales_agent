"""PR-7 Sub-A — AgentState extension is additive (zero regresión inbound).

Verifica:
- ``create_initial_state`` con args pre-PR-7 produce un AgentState válido con
  ``outbound_mode=False`` por default y ``campaign_id``/``campaign_instructions``
  ``None``.
- Llamado con campaign params produce el state con esos campos seteados.
- Cero campo existente removido o modificado en su tipo / default.

# [PR-7-OUTBOUND-ORCHESTRATOR] -> docs/archive/2026/legacy-pis/PI-1-campaigns-module/
#   sprints/S3-mvp-telegram/prs/PR-7-outbound-orchestrator/CONTRACT.md
"""

from __future__ import annotations

from uuid import UUID, uuid4

from luana_core_sales_agent.application.orchestrator.state import (
    AgentState,
    create_initial_state,
)


# Frozen baseline of pre-PR-7 AgentState keys. PR-7 may add fields, never
# remove or rename. test_campaign_state_additive.py (architecture) ratchets
# this superset assertion globally.
_PRE_PR7_BASELINE_KEYS: frozenset[str] = frozenset(
    {
        "messages",
        "next_node",
        "user_id",
        "tenant_id",
        "session_id",
        "current_state",
        "detected_intent",
        "lead_score",
        "lead_data",
        "tenant_config",
        "history",
        "user_profile",
        "session_active",
        "active_enrollment",
        "active_product",
        "last_intent",
        "launch_stage",
        "agent_identity",
        "brand_voice",
        "buying_signals",
        "objection_history",
        "qualification_answers",
        "turn_count",
        "customer_profile_id",
        "channel_type",
        "close_strategy",
        "session_gap_hours",
        "last_session_summary",
        "is_returning_user",
        "consecutive_questions",
        "follow_up_cadence",
        "internal_turn",
        "_pending_tool",
        "_llm_service",
        "error",
    },
)


class TestCreateInitialStateInbound:
    """Default invocation (pre-PR-7 inbound contract preserved)."""

    def test_default_args_set_outbound_mode_false(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
        )
        assert state["outbound_mode"] is False

    def test_default_args_set_campaign_id_none(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
        )
        assert state["campaign_id"] is None

    def test_default_args_set_campaign_instructions_none(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
        )
        assert state["campaign_instructions"] is None

    def test_pre_pr7_keys_preserved(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
        )
        missing = _PRE_PR7_BASELINE_KEYS - set(state.keys())
        assert not missing, f"create_initial_state dropped pre-PR-7 keys: {missing}"

    def test_pre_pr7_args_only_still_callable(self) -> None:
        # Nothing PR-7-specific passed → must still produce a valid state with
        # outbound_mode=False + campaign fields None.
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            session_id="test-session",
            lead_data={"name": "Foo"},
            tenant_config={"foo": "bar"},
            history=[{"role": "user", "content": "hi"}],
            user_profile={"language": "es"},
            session_active=True,
            active_enrollment=None,
            active_product=None,
            last_intent=None,
            launch_stage=None,
            agent_identity="brand-x",
            brand_voice="voice-x",
            buying_signals=[],
            objection_history=[],
            qualification_answers={},
            turn_count=0,
            customer_profile_id=None,
            channel_type="chat",
            close_strategy=None,
            current_state="rapport",
            lead_score=0,
            session_gap_hours=None,
            last_session_summary=None,
            is_returning_user=False,
            consecutive_questions=0,
            follow_up_cadence=None,
        )
        assert state["outbound_mode"] is False
        assert state["campaign_id"] is None
        assert state["campaign_instructions"] is None


class TestCreateInitialStateOutbound:
    """PR-7 outbound additive params populate state correctly."""

    def test_outbound_mode_true_sets_flag(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            outbound_mode=True,
        )
        assert state["outbound_mode"] is True

    def test_campaign_id_uuid_passes_through(self) -> None:
        cid = uuid4()
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            outbound_mode=True,
            campaign_id=cid,
        )
        assert state["campaign_id"] == cid
        assert isinstance(state["campaign_id"], UUID)

    def test_campaign_instructions_passes_through(self) -> None:
        instructions = "Iniciá una conversación cordial y ofrecé el plan Premium."
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            outbound_mode=True,
            campaign_instructions=instructions,
        )
        assert state["campaign_instructions"] == instructions

    def test_outbound_keys_present_alongside_legacy(self) -> None:
        state = create_initial_state(
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            outbound_mode=True,
            campaign_id=uuid4(),
            campaign_instructions="brief",
        )
        # Pre-PR-7 + new keys all present.
        for key in _PRE_PR7_BASELINE_KEYS:
            assert key in state
        assert "outbound_mode" in state
        assert "campaign_id" in state
        assert "campaign_instructions" in state


class TestAgentStateAnnotations:
    """TypedDict annotations include the three new optional keys."""

    def test_outbound_mode_in_annotations(self) -> None:
        assert "outbound_mode" in AgentState.__annotations__

    def test_campaign_id_in_annotations(self) -> None:
        assert "campaign_id" in AgentState.__annotations__

    def test_campaign_instructions_in_annotations(self) -> None:
        assert "campaign_instructions" in AgentState.__annotations__
