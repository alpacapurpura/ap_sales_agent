"""Architecture fitness gate — termination policy registry contract (H8).

Story B (T-9) cement: the public ``register_termination_policy(name,
predicate)`` API + ``TERMINATION_POLICIES`` dict MUST satisfy the
Strategy-pattern invariants documented in
``03-arch-agentic.md §4``:

1. ``register_termination_policy`` is a 2-arity callable.
2. ``TERMINATION_POLICIES`` is a dict[str, callable] populated with the
   4 default keys at module import.
3. ``register_termination_policy`` is idempotent on ``name`` — re-register
   overrides the previous predicate without raising.
4. Non-callable predicate raises ``TypeError``.
5. ``TerminationReason`` + ``AgentErrorSubtype`` are StrEnum (D5).
6. ``evaluate_termination(state)`` walks registered policies in
   registration order — first match wins.

These invariants enable Story I (adversarial_detected) + Story H
(budget_exceeded) to append predicates without touching core. Allowlists
intentionally absent — any drift breaks the contract.

The full lifecycle test (register → trigger → cleanup teardown) lives
in T-10 ``test_termination_registry.py``. This gate covers the
*structural* contract only — what the public surface promises.

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import inspect

import pytest

pytestmark = pytest.mark.no_eval


_DEFAULT_POLICY_NAMES: frozenset[str] = frozenset(
    {
        "max_turns",
        "customer_exit",
        "agent_error",
        "goal_completion",
    },
)


# ════════════════════════════════════════════════════════════════════════
# Public API surface — function exists + correct arity
# ════════════════════════════════════════════════════════════════════════


def test_register_termination_policy_importable() -> None:
    """``register_termination_policy`` MUST be importable from the public surface.

    Verified twice: from ``simulator.termination`` (canonical) and from
    ``simulator`` (re-export per H9 ``__all__``).
    """
    from tests.agentic_evals.sales_agent.simulator import termination as canonical_mod
    from tests.agentic_evals.sales_agent.simulator import register_termination_policy as reexport

    assert hasattr(canonical_mod, "register_termination_policy"), (
        "register_termination_policy not found in simulator.termination — H8 SSoT missing."
    )
    assert reexport is canonical_mod.register_termination_policy, (
        "simulator.register_termination_policy MUST be the same callable object "
        "as simulator.termination.register_termination_policy (no re-binding)."
    )


def test_register_termination_policy_arity() -> None:
    """``register_termination_policy(name: str, predicate: Callable)`` — 2 positional/keyword args."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        register_termination_policy,
    )

    sig = inspect.signature(register_termination_policy)
    params = list(sig.parameters.values())
    assert len(params) == 2, (
        f"register_termination_policy MUST take exactly 2 args (name, predicate); "
        f"got {len(params)}: {[p.name for p in params]}"
    )
    assert params[0].name == "name", f"First parameter MUST be named 'name'; got {params[0].name!r}"
    assert params[1].name == "predicate", f"Second parameter MUST be named 'predicate'; got {params[1].name!r}"


# ════════════════════════════════════════════════════════════════════════
# TERMINATION_POLICIES dict — default 4 keys at import
# ════════════════════════════════════════════════════════════════════════


def test_termination_policies_dict_exists_and_correct_type() -> None:
    """``TERMINATION_POLICIES`` MUST be a dict at module level."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    assert isinstance(TERMINATION_POLICIES, dict), (
        f"TERMINATION_POLICIES expected dict, got {type(TERMINATION_POLICIES)}."
    )


def test_default_four_policies_registered_at_import() -> None:
    """All 4 default policies MUST register at ``import simulator.termination``."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    actual_keys = set(TERMINATION_POLICIES.keys())
    missing = _DEFAULT_POLICY_NAMES - actual_keys
    assert not missing, (
        f"Default termination policies missing at import: {sorted(missing)}. "
        f"All 4 of {sorted(_DEFAULT_POLICY_NAMES)} MUST register at module load."
    )


@pytest.mark.parametrize("policy_name", sorted(_DEFAULT_POLICY_NAMES))
def test_each_default_policy_is_callable(policy_name: str) -> None:
    """Each default policy value MUST be callable (state → TerminationReason | None)."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    predicate = TERMINATION_POLICIES.get(policy_name)
    assert predicate is not None, f"Default policy {policy_name!r} not registered."
    assert callable(predicate), f"Default policy {policy_name!r} value not callable: {predicate!r}"


# ════════════════════════════════════════════════════════════════════════
# Idempotency + type-safety contract
# ════════════════════════════════════════════════════════════════════════


def test_register_idempotent_on_name() -> None:
    """Re-registering a name MUST override + leave dict size unchanged.

    Cleanup: removes the test policy at teardown so other arch tests
    see the registry in its default 4-key state.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
        register_termination_policy,
    )

    test_name = "_test_idempotent_arch_fitness"

    # Defensive guard — if a prior test crashed mid-way, clean up first.
    TERMINATION_POLICIES.pop(test_name, None)

    initial_size = len(TERMINATION_POLICIES)

    def _first(_state: object) -> None:
        return None

    def _second(_state: object) -> None:
        return None

    register_termination_policy(test_name, _first)
    assert len(TERMINATION_POLICIES) == initial_size + 1
    assert TERMINATION_POLICIES[test_name] is _first

    # Re-register — size MUST NOT grow; predicate MUST swap.
    register_termination_policy(test_name, _second)
    assert len(TERMINATION_POLICIES) == initial_size + 1, "Re-registering the same name MUST NOT grow the dict."
    assert TERMINATION_POLICIES[test_name] is _second, "Re-registering MUST swap the predicate (idempotent on name)."

    # Cleanup — restore default 4-key state.
    TERMINATION_POLICIES.pop(test_name)


def test_register_non_callable_predicate_raises_typeerror() -> None:
    """``register_termination_policy(name, non_callable)`` MUST raise ``TypeError``.

    Defense: silent-accepting an int / dict / string predicate would
    surface as ``TypeError`` at call time deep inside the graph,
    obscuring the registration bug.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        register_termination_policy,
    )

    with pytest.raises(TypeError, match=r"predicate must be callable"):
        register_termination_policy("_test_bad_predicate", "not callable")  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════════
# StrEnum cement — TerminationReason + AgentErrorSubtype
# ════════════════════════════════════════════════════════════════════════


def test_termination_reason_is_strenum_with_six_members() -> None:
    """``TerminationReason`` MUST be a StrEnum with EXACTLY 6 members per D5.

    Story B + I + H pre-allocated:
    - GOAL_COMPLETION, MAX_TURNS, CUSTOMER_EXIT, AGENT_ERROR (Story B)
    - ADVERSARIAL_DETECTED (Story I)
    - BUDGET_EXCEEDED (Story H)
    """
    from enum import StrEnum

    from tests.agentic_evals.sales_agent.simulator.termination import (
        TerminationReason,
    )

    assert issubclass(TerminationReason, StrEnum), (
        f"TerminationReason MUST be a StrEnum subclass; got {TerminationReason.__mro__}"
    )

    members = {member.name for member in TerminationReason}
    expected_members = {
        "GOAL_COMPLETION",
        "MAX_TURNS",
        "CUSTOMER_EXIT",
        "AGENT_ERROR",
        "ADVERSARIAL_DETECTED",
        "BUDGET_EXCEEDED",
    }
    assert members == expected_members, (
        f"TerminationReason members drift: expected {sorted(expected_members)}; got {sorted(members)}."
    )


def test_agent_error_subtype_is_strenum_with_four_members() -> None:
    """``AgentErrorSubtype`` MUST be a StrEnum with EXACTLY 4 members per H7."""
    from enum import StrEnum

    from tests.agentic_evals.sales_agent.simulator.termination import (
        AgentErrorSubtype,
    )

    assert issubclass(AgentErrorSubtype, StrEnum), (
        f"AgentErrorSubtype MUST be a StrEnum subclass; got {AgentErrorSubtype.__mro__}"
    )

    members = {member.name for member in AgentErrorSubtype}
    expected_members = {"TIMEOUT", "EMPTY_RESPONSE", "HTTP_ERROR", "INVALID_STATE"}
    assert members == expected_members, (
        f"AgentErrorSubtype members drift: expected {sorted(expected_members)}; got {sorted(members)}."
    )


# ════════════════════════════════════════════════════════════════════════
# evaluate_termination — first-match-wins contract
# ════════════════════════════════════════════════════════════════════════


def test_evaluate_termination_iterates_in_registration_order() -> None:
    """``evaluate_termination(state)`` walks ``TERMINATION_POLICIES`` in registration order.

    Documented invariant in ``03-arch-agentic.md §4`` — first predicate
    that returns a reason wins. Python dict guarantees insertion order
    since 3.7, so this gate verifies registration order is deterministic.
    """
    from tests.agentic_evals.sales_agent.simulator.termination import (
        TERMINATION_POLICIES,
    )

    keys = list(TERMINATION_POLICIES.keys())
    # Default registration order per termination.py module top:
    # max_turns → customer_exit → agent_error → goal_completion
    expected_first_four = ["max_turns", "customer_exit", "agent_error", "goal_completion"]
    assert keys[: len(expected_first_four)] == expected_first_four, (
        f"Default 4 policies MUST register in this order: {expected_first_four}; "
        f"got {keys[: len(expected_first_four)]}. Re-ordering breaks first-match-wins "
        f"semantics relied upon by ``evaluate_termination``."
    )


def test_evaluate_termination_callable() -> None:
    """``evaluate_termination`` is callable + returns TerminationReason | None."""
    from tests.agentic_evals.sales_agent.simulator.termination import (
        evaluate_termination,
    )

    assert callable(evaluate_termination), "evaluate_termination MUST be callable (state → TerminationReason | None)."
    sig = inspect.signature(evaluate_termination)
    params = list(sig.parameters.values())
    assert len(params) == 1, f"evaluate_termination MUST take exactly 1 arg (state); got {len(params)}."
