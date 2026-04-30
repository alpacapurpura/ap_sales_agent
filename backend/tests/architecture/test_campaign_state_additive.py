"""PR-7 Sub-J — campaign-state ADDITIVE arch gate.

# [SALES-AGENT-OUTBOUND-PR7] -> docs/pm-nico/pis/active/PI-1-campaigns-module/
#                                sprints/S3-mvp-telegram/prs/PR-7-outbound-orchestrator/CONTRACT.md

Locks in CONTRACT.md Decision 28 (additive TypedDict, no separate
dataclass) + invariant 1 (inbound chat path NO se rompe):

1. Every PR-7 field is **optional** in the TypedDict (declared as
   ``T | None`` or ``bool``-with-default).
2. Every PR-7 parameter in ``create_initial_state`` has a default in
   the function signature — no positional reorder, no required arg.
3. The full pre-PR-7 AgentState field set is a subset of the current
   AgentState (no legacy field modified or removed).
4. ``create_initial_state`` returns a dict whose key set covers every
   pre-PR-7 field even when called with pre-PR-7 args only.

Sister test of ``test_outbound_orchestrator_non_breaking.py`` — that
file focuses on supervisor branch + signature defaults; this file
focuses on the additive contract of the state shape itself.
"""

from __future__ import annotations

import inspect
import typing
from typing import get_type_hints

from src.modules.sales_agent.application.orchestrator.state import (
    AgentState,
    create_initial_state,
)


# ---------------------------------------------------------------------------
# Frozen baseline — duplicated here intentionally (separate arch test, separate
# concern). Single SSoT lives in ``test_outbound_orchestrator_non_breaking.py``;
# duplication here is the canonical "ratchet baseline" pattern (also used by
# ``test_brand_editable_fields_baseline.py`` — every arch test owns its own
# frozen set so the dependency graph stays flat).
# ---------------------------------------------------------------------------

_PRE_PR7_AGENT_STATE_FIELDS: frozenset[str] = frozenset(
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
    }
)

_PR7_NEW_FIELDS: frozenset[str] = frozenset(
    {
        "campaign_id",
        "campaign_instructions",
        "outbound_mode",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_optional_annotation(annotation: object) -> bool:
    """True if annotation is ``T | None`` (or ``Optional[T]``)."""
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        return type(None) in typing.get_args(annotation)
    # PEP 604 X | Y on 3.10+ uses types.UnionType
    import types

    if isinstance(annotation, types.UnionType):
        return type(None) in typing.get_args(annotation)
    return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pre_pr7_fields_subset_of_current_state() -> None:
    """Every pre-PR-7 AgentState field is still present (no removal)."""
    current_fields = set(AgentState.__annotations__.keys())
    missing = sorted(_PRE_PR7_AGENT_STATE_FIELDS - current_fields)
    assert not missing, (
        f"AgentState removed pre-PR-7 fields: {missing}. "
        f"Backward-incompatible — production checkpoints will fail to deserialize."
    )


def test_no_pre_pr7_field_changed_to_required_only() -> None:
    """Pre-PR-7 fields with optional annotations (T | None) STAY optional.

    A backward-incompatible change is silently re-typing a legacy field
    from ``str | None`` to ``str`` — old serialized state can no longer
    populate the dict. We freeze the optional-ness of every legacy
    field that was originally optional.
    """
    # Captured baseline: legacy fields that were ``T | None`` pre-PR-7.
    # Every entry MUST remain optional. Boolean field ``session_active``
    # was non-optional pre-PR-7 — preserved here so we don't accidentally
    # demand it become Optional either.
    legacy_optional_fields: frozenset[str] = frozenset(
        {
            "next_node",
            "user_id",
            "tenant_id",
            "session_id",
            "current_state",
            "detected_intent",
            "lead_score",
            "lead_data",
            "tenant_config",
            "user_profile",
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
        }
    )

    hints = get_type_hints(AgentState)
    not_optional = [name for name in legacy_optional_fields if not _is_optional_annotation(hints[name])]
    assert not not_optional, (
        f"Legacy AgentState fields lost their optional annotation: {sorted(not_optional)}. "
        f"This is a backward-incompatible TypedDict change — re-add ``| None`` or document the migration."
    )


def test_pr7_fields_are_optional_in_state() -> None:
    """``campaign_id`` + ``campaign_instructions`` annotated as ``T | None``.

    ``outbound_mode`` is bool with default False (verified separately
    via ``create_initial_state`` signature) — the TypedDict may declare
    it as ``bool`` without ``| None`` because the default in
    ``create_initial_state`` guarantees a value is always set.
    """
    hints = get_type_hints(AgentState)
    assert _is_optional_annotation(hints["campaign_id"]), "campaign_id MUST be ``UUID | None`` (Decision 28 — additive)"
    assert _is_optional_annotation(hints["campaign_instructions"]), (
        "campaign_instructions MUST be ``str | None`` (Decision 28 — additive)"
    )
    # outbound_mode is bool — default False enforced by create_initial_state signature
    assert hints["outbound_mode"] is bool, "outbound_mode MUST be ``bool`` (Decision 29 — explicit flag)"


def test_create_initial_state_signature_additive() -> None:
    """Every PR-7 param has a default in ``create_initial_state`` — no positional reorder."""
    sig = inspect.signature(create_initial_state)

    for name in _PR7_NEW_FIELDS:
        assert name in sig.parameters, f"create_initial_state missing PR-7 param '{name}'"
        param = sig.parameters[name]
        assert param.default is not inspect.Parameter.empty, (
            f"create_initial_state param '{name}' MUST have a default value. "
            f"Decision 28 — additive only; required new params would force every "
            f"inbound caller to pass them, breaking the chat path."
        )

    # Also verify legacy params still have defaults (no PR-7 demoted a legacy param to required).
    legacy_defaulted = {
        "session_id",
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
        "current_state",
        "lead_score",
        "session_gap_hours",
        "last_session_summary",
        "is_returning_user",
        "consecutive_questions",
        "follow_up_cadence",
        "_llm_service",
    }
    for name in legacy_defaulted:
        assert name in sig.parameters, f"Legacy param '{name}' missing — backward-incompatible removal"
        param = sig.parameters[name]
        assert param.default is not inspect.Parameter.empty, (
            f"Legacy param '{name}' lost its default — every caller now forced to supply it."
        )


def test_create_initial_state_returns_pre_pr7_keys() -> None:
    """Calling ``create_initial_state`` with pre-PR-7 args yields dict covering every legacy key.

    Smoke test that the return statement still includes every legacy
    field — guards against a refactor that drops a key from the dict
    literal (TypedDict total=True does NOT prevent that at runtime).
    """
    state = create_initial_state(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
    )
    state_keys = set(state.keys())
    missing = sorted(_PRE_PR7_AGENT_STATE_FIELDS - state_keys)
    assert not missing, (
        f"create_initial_state returned dict missing pre-PR-7 keys: {missing}. "
        f"TypedDict declaration alone does not enforce the dict literal — "
        f"add the missing keys back to the return statement."
    )


def test_create_initial_state_returns_pr7_keys() -> None:
    """Returned dict includes the PR-7 keys (so the agent_app can read them)."""
    state = create_initial_state(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-000000000002",
    )
    state_keys = set(state.keys())
    missing = sorted(_PR7_NEW_FIELDS - state_keys)
    assert not missing, (
        f"create_initial_state dropped PR-7 keys from return literal: {missing}. "
        f"Outbound mode would silently default to inbound at runtime."
    )
