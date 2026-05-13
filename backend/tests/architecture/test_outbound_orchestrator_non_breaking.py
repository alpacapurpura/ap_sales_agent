"""PR-7 Sub-J — outbound orchestrator NON-BREAKING arch gate.

# [SALES-AGENT-OUTBOUND-PR7] -> docs/archive/2026/legacy-pis/PI-1-campaigns-module/
#                                sprints/S3-mvp-telegram/prs/PR-7-outbound-orchestrator/CONTRACT.md

Locks in CONTRACT.md §12 invariants 1, 8, 10:

1. Inbound chat path NO se rompe — ``AgentState`` shape pre-PR-7 ⊆
   post-PR-7 (every legacy field still present, every new field
   ``| None`` or has a default in ``create_initial_state``).
2. ``outbound_mode`` defaults to ``False`` in both the TypedDict
   contract (verified via ``create_initial_state(...)``) and the
   constructor signature default.
3. ``campaign_id`` defaults to ``None`` and ``campaign_instructions``
   defaults to ``None`` — neither is required to construct an inbound
   AgentState.
4. ``create_initial_state`` is callable with **only** pre-PR-7
   keyword arguments — no caller in the inbound chat path must be
   modified to pass new params.

Ratchet semantics: this test is **shrink-only** in the same sense as
the catalog baselines — the frozen baseline of pre-PR-7 fields can
NEVER lose an entry (would mean PR-7 removed an existing field, which
is a backward-incompatible change). New fields are appended via the
``_PR7_NEW_FIELDS`` set; if a future PR removes any of those, this
test fails until the constant is updated explicitly (signals review
awareness).
"""

from __future__ import annotations

import inspect

from luana_core_sales_agent.application.orchestrator.state import (
    AgentState,
    create_initial_state,
)


# ---------------------------------------------------------------------------
# Frozen baseline — AgentState fields that existed BEFORE PR-7.
# Captured from state.py at PR-7 Sub-A landing (commit 9200b6cc parent).
# This set NEVER shrinks — removing a legacy field breaks every inbound
# checkpoint already persisted in production.
# ---------------------------------------------------------------------------

_PRE_PR7_AGENT_STATE_FIELDS: frozenset[str] = frozenset(
    {
        # Messaging
        "messages",
        # Routing
        "next_node",
        # Context
        "user_id",
        "tenant_id",
        "session_id",
        # Agent Memory (Short Term)
        "current_state",
        "detected_intent",
        "lead_score",
        # Lead Data
        "lead_data",
        # Configuration & History
        "tenant_config",
        "history",
        "user_profile",
        # Session Status
        "session_active",
        "active_enrollment",
        "active_product",
        "last_intent",
        "launch_stage",
        # Agent Knowledge System (AKS)
        "agent_identity",
        "brand_voice",
        # Accumulated Signals
        "buying_signals",
        "objection_history",
        "qualification_answers",
        "turn_count",
        "customer_profile_id",
        "channel_type",
        "close_strategy",
        # Session continuity (Fase 2)
        "session_gap_hours",
        "last_session_summary",
        "is_returning_user",
        # Question fatigue (Fase 3)
        "consecutive_questions",
        "follow_up_cadence",
        # Internal (graph loop control)
        "internal_turn",
        "_pending_tool",
        "_llm_service",  # PR-6 BudgetGuardingLLMService DI slot
        # Errors
        "error",
    }
)

# Fields ADDED by PR-7 (Sub-A AgentState extension). Additive — every
# entry MUST default to None / False so inbound callers don't break.
_PR7_NEW_FIELDS: frozenset[str] = frozenset(
    {
        "campaign_id",
        "campaign_instructions",
        "outbound_mode",
    }
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_agent_state_baseline_subset_of_current() -> None:
    """Pre-PR-7 fields ⊆ current AgentState — no legacy field removed."""
    current_fields = set(AgentState.__annotations__.keys())
    missing = sorted(_PRE_PR7_AGENT_STATE_FIELDS - current_fields)
    assert not missing, (
        f"AgentState lost pre-PR-7 fields: {missing}. "
        f"Removing legacy fields breaks inbound checkpoint deserialization in production. "
        f"If the removal is intentional, update the schema migration plan + bump "
        f"checkpoint version."
    )


def test_agent_state_pr7_fields_present() -> None:
    """PR-7 added the expected outbound fields (sanity check)."""
    current_fields = set(AgentState.__annotations__.keys())
    missing = sorted(_PR7_NEW_FIELDS - current_fields)
    assert not missing, (
        f"PR-7 fields missing from AgentState: {missing}. "
        f"If you intentionally removed a PR-7 field, update _PR7_NEW_FIELDS in this test."
    )


def test_create_initial_state_callable_with_pre_pr7_args_only() -> None:
    """Inbound callers MUST keep working without passing PR-7 params.

    Every legacy caller in the chat path (ChatOrchestrator,
    ConversationPipeline.build_initial_state, tools, etc.) invokes
    create_initial_state with the pre-PR-7 keyword surface. They must
    keep producing a valid AgentState with outbound_mode=False.
    """
    state = create_initial_state(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
    )
    # Inbound shape preserved
    assert state["outbound_mode"] is False, "Default outbound_mode MUST be False (inbound path)"
    assert state["campaign_id"] is None, "Default campaign_id MUST be None (inbound path)"
    assert state["campaign_instructions"] is None, "Default campaign_instructions MUST be None (inbound path)"


def test_create_initial_state_pr7_params_have_defaults() -> None:
    """PR-7 params in ``create_initial_state`` MUST have defaults — no positional reorder.

    Ensures any caller continues to work without passing the new params,
    AND the new params can never become required without an explicit
    breaking-change PR.
    """
    sig = inspect.signature(create_initial_state)
    for name in _PR7_NEW_FIELDS:
        assert name in sig.parameters, f"create_initial_state missing PR-7 param '{name}'"
        param = sig.parameters[name]
        assert param.default is not inspect.Parameter.empty, (
            f"create_initial_state param '{name}' MUST have a default value "
            f"(else inbound callers break). PR-7 invariant — Decision 28 / 29."
        )

    # Specific defaults documented in CONTRACT §2 must hold
    assert sig.parameters["outbound_mode"].default is False
    assert sig.parameters["campaign_id"].default is None
    assert sig.parameters["campaign_instructions"].default is None


def test_supervisor_outbound_skip_branch_present() -> None:
    """Supervisor node has the outbound skip-qualifier branch (Sub-C invariant).

    Reads source — runtime introspection wrapped by ``@trace_node``
    decorator returns ``*args, **kwargs``. AST-level grep mirrors the
    pattern used by ``test_budget_guard_pre_llm_call.test_sales_agent_pipeline_accepts_budget_guard``.
    """
    from pathlib import Path

    nodes_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "modules"
        / "sales_agent"
        / "application"
        / "agents"
        / "sales"
        / "nodes.py"
    )
    source = nodes_path.read_text(encoding="utf-8")
    assert 'state.get("outbound_mode")' in source, (
        "Supervisor MUST read state['outbound_mode'] to enable skip-qualifier branch (PR-7 Sub-C)."
    )
    assert 'state.get("lead_score"' in source, (
        "Supervisor outbound skip MUST gate on lead_score threshold (CONTRACT §11 Decision 36)."
    )
