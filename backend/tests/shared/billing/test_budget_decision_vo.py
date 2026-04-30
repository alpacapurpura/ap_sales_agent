"""Tests for BudgetDecision value object — domain layer."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.shared.billing.domain.budget_decision import BudgetDecision


class TestBudgetDecisionInvariants:
    def test_allowed_no_warn(self) -> None:
        d = BudgetDecision(
            allowed=True,
            pool="others",
            spent_usd=Decimal("1.00"),
            cap_usd=Decimal("5.00"),
        )
        assert d.allowed is True
        assert d.soft_warn is False
        assert d.reason is None

    def test_blocked_with_reason(self) -> None:
        d = BudgetDecision(
            allowed=False,
            pool="sales_agent",
            spent_usd=Decimal("5.00"),
            cap_usd=Decimal("5.00"),
            reason="cycle_budget_exhausted",
        )
        assert d.allowed is False
        assert d.reason == "cycle_budget_exhausted"

    def test_soft_warn_still_allowed(self) -> None:
        d = BudgetDecision(
            allowed=True,
            pool="others",
            spent_usd=Decimal("4.10"),
            cap_usd=Decimal("5.00"),
            soft_warn=True,
        )
        assert d.allowed is True
        assert d.soft_warn is True

    def test_frozen(self) -> None:
        d = BudgetDecision(
            allowed=True,
            pool="others",
            spent_usd=Decimal(0),
            cap_usd=Decimal("5.00"),
        )
        with pytest.raises((TypeError, AttributeError)):
            d.allowed = False  # type: ignore[misc]
