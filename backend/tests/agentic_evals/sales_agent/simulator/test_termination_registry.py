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
    formalizes pytest fixture for cleanup (see ``cleanup_test_policies``
    fixture below).
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


# ════════════════════════════════════════════════════════════════════════
# T-10 EXTEND — register custom policy + cleanup fixture
# ════════════════════════════════════════════════════════════════════════


@pytest.fixture
def cleanup_test_policies() -> Any:
    """Pytest fixture — auto-cleanup test-registered policies post-test.

    Yields a list registry to which tests append the names they register.
    Teardown removes each name from ``TERMINATION_POLICIES`` so the
    default 4 policies (max_turns, customer_exit, agent_error,
    goal_completion) remain intact for downstream tests.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    registered_test_names: list[str] = []

    yield registered_test_names

    # Teardown — remove each test-registered name (idempotent — pop with default)
    for name in registered_test_names:
        TERMINATION_POLICIES.pop(name, None)


def test_register_custom_policy_works_with_graph_evaluation(
    cleanup_test_policies: list[str],
) -> None:
    """Story H/I/E pattern: ``register_termination_policy('budget_exceeded', predicate)``.

    Asserts:
    - Custom predicate is registered + appears in TERMINATION_POLICIES.
    - When ``evaluate_termination`` runs against a state matching the
      predicate, the custom name's reason is returned (Story H/I/E
      append-safe).

    Cleanup via ``cleanup_test_policies`` fixture removes the test policy
    post-test so the default 4 policies are restored.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
        evaluate_termination,
    )

    test_name = "_pytest_only_budget_exceeded"
    cleanup_test_policies.append(test_name)

    def _budget_predicate(state: Any) -> TerminationReason | None:
        # Match if eval_metadata signals budget bust (synthetic state only)
        if isinstance(state.eval_metadata, dict) and state.eval_metadata.get("budget_busted") == "true":
            return TerminationReason.BUDGET_EXCEEDED
        return None

    register_termination_policy(test_name, _budget_predicate)
    assert test_name in TERMINATION_POLICIES, (
        f"register_termination_policy did not insert {test_name!r}; got {list(TERMINATION_POLICIES)}"
    )

    # Build a synthetic SimulationState with budget_busted='true' to exercise predicate.
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
    from tests.agentic_evals.sales_agent.simulator.state import SimulationState

    actor = ActorProfile(
        id="test-budget-actor",
        name="Test Budget",
        actor_goal="Test budget exceeded",
        dialect_code="es-419",
        traits=["test"],
        pain_points=["test"],
        objections=["test"],
        budget_hint="alto",
        urgency="high",
        communication_style="test",
        initial_message="Hola.",
        persona_kind="happy",
    )
    state = SimulationState(
        simulation_id=uuid4(),
        run_id=uuid4(),
        tenant_id=uuid4(),
        archetype_slug="tenant_coach_lat",
        actor_profile=actor,
        current_turn=1,
        iterations=1,
        max_turns=10,
        eval_metadata={"budget_busted": "true"},
    )

    reason = evaluate_termination(state)
    # Default policies (max_turns, customer_exit, agent_error,
    # goal_completion) should NOT match this synthetic state. Our custom
    # predicate is registered LAST in evaluation order, so reason MUST be
    # BUDGET_EXCEEDED.
    assert reason == TerminationReason.BUDGET_EXCEEDED, (
        f"Custom predicate not honored: expected BUDGET_EXCEEDED; got {reason}"
    )


def test_register_idempotent_no_duplicate_entries(
    cleanup_test_policies: list[str],
) -> None:
    """Re-registering the same name MUST NOT create duplicate entries.

    Re-registration overrides the previous predicate (last wins) without
    bloating the registry with parallel entries.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    test_name = "_pytest_only_dedup_test"
    cleanup_test_policies.append(test_name)

    def _predicate_v1(_state: Any) -> TerminationReason | None:
        return None

    def _predicate_v2(_state: Any) -> TerminationReason | None:
        return None

    initial_size = len(TERMINATION_POLICIES)

    register_termination_policy(test_name, _predicate_v1)
    register_termination_policy(test_name, _predicate_v2)
    register_termination_policy(test_name, _predicate_v1)

    # Registry size grew by exactly 1 (the new test entry), not by 3.
    assert len(TERMINATION_POLICIES) == initial_size + 1, (
        f"Re-registration MUST be idempotent on name; got {len(TERMINATION_POLICIES) - initial_size} new entries instead of 1"
    )

    # Last-wins semantics — the binding is _predicate_v1 (last registered)
    assert TERMINATION_POLICIES[test_name] is _predicate_v1, (
        f"Re-registration MUST be last-wins; got {TERMINATION_POLICIES[test_name]} expected {_predicate_v1}"
    )


def test_cleanup_teardown_restores_default_policies(
    cleanup_test_policies: list[str],
) -> None:
    """The cleanup fixture MUST remove test-registered policies post-test.

    Even after registering several test policies, the teardown should
    restore the registry to the default 4 policies (max_turns,
    customer_exit, agent_error, goal_completion). Verified via assertions
    BEFORE teardown + a follow-up test that introspects the default state.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    def _predicate(_state: Any) -> TerminationReason | None:
        return None

    test_names = ["_pytest_only_t1", "_pytest_only_t2", "_pytest_only_t3"]
    for name in test_names:
        cleanup_test_policies.append(name)
        register_termination_policy(name, _predicate)

    # Before teardown — all 3 test entries present
    for name in test_names:
        assert name in TERMINATION_POLICIES, f"Test policy {name!r} missing pre-teardown"

    # Teardown happens at fixture finalization — verified by the next
    # test in the same module observing only default policies.


def test_default_policies_present_after_prior_test_teardown() -> None:
    """Defensive: the default 4 policies MUST remain intact after T-10 EXTEND tests.

    Runs AFTER ``test_cleanup_teardown_restores_default_policies`` (pytest
    discovers tests in source order) and verifies the cleanup fixture
    restored the registry to its baseline state.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    expected_defaults = {"max_turns", "customer_exit", "agent_error", "goal_completion"}
    actual = set(TERMINATION_POLICIES.keys())

    assert expected_defaults.issubset(actual), (
        f"Default policies missing after T-10 EXTEND tests; expected superset {expected_defaults}, got {actual}. "
        f"Cleanup fixture failed to restore default state."
    )

    # Defensive: no _pytest_only_* names should remain (cleanup ran)
    leaked = {name for name in actual if name.startswith("_pytest_only_")}
    assert leaked == set(), f"Cleanup fixture leaked test policies: {leaked}"
