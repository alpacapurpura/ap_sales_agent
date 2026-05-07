"""Termination registry contract tests — H8 Strategy pattern.

T-4 acceptance A2: TERMINATION_POLICIES exposes 4 default policies +
register_termination_policy public.

Per `06-tickets.yaml` T-4 deliverable §8: only `test_default_policies_registered`
in this story; T-10 will add `test_register_custom_policy` + cleanup teardown.
"""

# voseo-allowed: docstring references regional dialect en español neutro tests

from typing import Any

import pytest

from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
    register_termination_policy,
)


pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# T-4 acceptance A2 — default registry surface
# ════════════════════════════════════════════════════════════════════════


def test_default_policies_registered() -> None:
    """Default 4 policies must be registered at module import time."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    expected = {"goal_completion", "max_turns", "customer_exit", "agent_error"}
    actual = set(TERMINATION_POLICIES.keys())
    assert expected.issubset(actual), f"Default policies missing: expected superset {expected}, got {actual}"


def test_register_termination_policy_is_public() -> None:
    """register_termination_policy MUST be importable from public termination module."""
    # Import via public path
    from tests.agentic_evals.sales_agent.simulator import termination as term_mod

    assert hasattr(term_mod, "register_termination_policy"), (
        "register_termination_policy not exported from termination module"
    )
    assert callable(term_mod.register_termination_policy), "register_termination_policy must be callable"


def test_termination_reason_strenum_six_values() -> None:
    """H8 — TerminationReason 6 values exact (story B + future stories pre-allocated)."""
    expected_values = {
        "goal_completion",
        "max_turns",
        "customer_exit",
        "agent_error",
        "adversarial_detected",
        "budget_exceeded",
    }
    actual = {member.value for member in TerminationReason}
    assert actual == expected_values, f"TerminationReason values mismatch: expected {expected_values}, got {actual}"


def test_agent_error_subtype_strenum_four_values() -> None:
    """H7 — AgentErrorSubtype 4 values exact."""
    expected_values = {"timeout", "empty_response", "http_error", "invalid_state"}
    actual = {member.value for member in AgentErrorSubtype}
    assert actual == expected_values, f"AgentErrorSubtype values mismatch: expected {expected_values}, got {actual}"


def test_register_termination_policy_rejects_non_callable() -> None:
    """register_termination_policy must raise TypeError on non-callable predicate."""
    with pytest.raises(TypeError):
        register_termination_policy("bogus", "not_a_callable")  # type: ignore[arg-type]


def test_register_termination_policy_idempotent_on_name() -> None:
    """Re-registering same name overrides predicate (idempotent on name).

    Cleanup: remove test entry post-test to avoid pollution. Story T-10
    formalizes pytest fixture for cleanup.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    test_name = "_pytest_only_test_idempotent"

    def _predicate(_state: Any) -> TerminationReason | None:
        return None

    try:
        register_termination_policy(test_name, _predicate)
        assert test_name in TERMINATION_POLICIES
        # Re-register same name does not raise
        register_termination_policy(test_name, _predicate)
        assert test_name in TERMINATION_POLICIES
    finally:
        TERMINATION_POLICIES.pop(test_name, None)
