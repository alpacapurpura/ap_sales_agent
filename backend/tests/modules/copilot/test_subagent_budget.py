"""Tests for SubagentBudget caps."""

from __future__ import annotations

import pytest

from luana_core_copilot.application.orchestrator.subagent_budget import (
    DEFAULT_BUDGET,
    SubagentBudget,
    SubagentBudgetError,
    check_depth,
    check_iterations,
    check_per_turn_calls,
)


class TestDefaultBudget:
    def test_defaults_match_design(self) -> None:
        assert DEFAULT_BUDGET.max_subagents_per_turn == 2
        assert DEFAULT_BUDGET.max_subagent_depth == 1
        assert DEFAULT_BUDGET.max_subagent_iterations == 6

    def test_budget_is_frozen(self) -> None:
        with pytest.raises((AttributeError, TypeError)):
            DEFAULT_BUDGET.max_subagents_per_turn = 99  # type: ignore[misc]


class TestCheckPerTurnCalls:
    def test_under_cap_passes(self) -> None:
        check_per_turn_calls(0)
        check_per_turn_calls(1)

    def test_at_cap_raises(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_per_turn_calls(2)
        assert "per turn exceeded" in str(exc.value)

    def test_over_cap_raises(self) -> None:
        with pytest.raises(SubagentBudgetError):
            check_per_turn_calls(5)

    def test_custom_budget_overrides_default(self) -> None:
        budget = SubagentBudget(max_subagents_per_turn=5)
        check_per_turn_calls(4, budget)  # passes
        with pytest.raises(SubagentBudgetError):
            check_per_turn_calls(5, budget)


class TestCheckDepth:
    def test_root_depth_zero_passes(self) -> None:
        check_depth(0)

    def test_at_cap_raises(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_depth(1)
        assert "nesting depth" in str(exc.value)

    def test_custom_depth_budget(self) -> None:
        budget = SubagentBudget(max_subagent_depth=3)
        check_depth(2, budget)
        with pytest.raises(SubagentBudgetError):
            check_depth(3, budget)


class TestCheckIterations:
    def test_under_cap_passes(self) -> None:
        for i in range(6):
            check_iterations(i)

    def test_at_cap_raises(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_iterations(6)
        assert "iterations" in str(exc.value)


class TestErrorMessages:
    """Mensajes de error son user-facing (eventualmente llegan al modelo
    como ToolMessage). Spanish neutro LatAm + accionable."""

    def test_per_turn_message_explains_action(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_per_turn_calls(2)
        msg = str(exc.value)
        assert "consolida" in msg.lower() or "una sola" in msg.lower()

    def test_depth_message_explains_action(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_depth(1)
        msg = str(exc.value)
        assert "no pueden invocar" in msg.lower() or "deja que el parent" in msg.lower()

    def test_iterations_message_explains_action(self) -> None:
        with pytest.raises(SubagentBudgetError) as exc:
            check_iterations(6)
        msg = str(exc.value)
        assert "termina" in msg.lower() or "no sigas" in msg.lower()
