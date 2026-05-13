"""Tests for PlanConfig value object — domain layer, pure Python.

RED first (TDD-mandatory). Tests cover:
- Required invariant: llm_budget_total_usd > 0
- sales_agent_reserved_pct in [0, 1]
- sa_pool_usd + others_pool_usd == llm_budget_total_usd (Decimal precision)
- is_default field defaults to False (PM Q6)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from luana_core_billing.domain.plan import PlanConfig


def _basic_plan(**overrides) -> PlanConfig:
    defaults = {
        "plan_id": "free",
        "display_name": "Free",
        "llm_budget_total_usd": Decimal("5.00"),
    }
    defaults.update(overrides)
    return PlanConfig(**defaults)


class TestPlanConfigInvariants:
    def test_basic_plan_creates_ok(self) -> None:
        plan = _basic_plan()
        assert plan.plan_id == "free"
        assert plan.llm_budget_total_usd == Decimal("5.00")
        assert plan.is_default is False  # PM Q6: defaults to False

    def test_is_default_defaults_to_false(self) -> None:
        plan = _basic_plan()
        assert plan.is_default is False

    def test_is_default_true_accepted(self) -> None:
        plan = _basic_plan(is_default=True)
        assert plan.is_default is True

    def test_budget_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(llm_budget_total_usd=Decimal("0.00"))

    def test_budget_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(llm_budget_total_usd=Decimal("-1.00"))

    def test_sa_pct_default_is_half(self) -> None:
        plan = _basic_plan()
        assert plan.sales_agent_reserved_pct == Decimal("0.500")

    def test_sa_pct_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(sales_agent_reserved_pct=Decimal("1.001"))

    def test_sa_pct_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(sales_agent_reserved_pct=Decimal("-0.001"))

    def test_sa_pct_zero_allowed(self) -> None:
        plan = _basic_plan(sales_agent_reserved_pct=Decimal("0.000"))
        assert plan.sales_agent_reserved_pct == Decimal("0.000")

    def test_sa_pct_one_allowed(self) -> None:
        plan = _basic_plan(sales_agent_reserved_pct=Decimal("1.000"))
        assert plan.sales_agent_reserved_pct == Decimal("1.000")

    def test_pool_sum_equals_total(self) -> None:
        plan = _basic_plan(
            llm_budget_total_usd=Decimal("10.00"),
            sales_agent_reserved_pct=Decimal("0.500"),
        )
        assert plan.sa_pool_usd + plan.others_pool_usd == plan.llm_budget_total_usd

    def test_pool_sum_with_non_trivial_pct(self) -> None:
        plan = _basic_plan(
            llm_budget_total_usd=Decimal("30.00"),
            sales_agent_reserved_pct=Decimal("0.333"),
        )
        # Allow 1-cent rounding from Decimal quantize
        total_check = plan.sa_pool_usd + plan.others_pool_usd
        assert abs(total_check - plan.llm_budget_total_usd) <= Decimal("0.02")

    def test_others_pool_50pct_plan(self) -> None:
        plan = _basic_plan(
            llm_budget_total_usd=Decimal("10.00"),
            sales_agent_reserved_pct=Decimal("0.500"),
        )
        assert plan.sa_pool_usd == Decimal("5.00")
        assert plan.others_pool_usd == Decimal("5.00")

    def test_others_pool_zero_pct_reserved(self) -> None:
        plan = _basic_plan(
            llm_budget_total_usd=Decimal("10.00"),
            sales_agent_reserved_pct=Decimal("0.000"),
        )
        assert plan.sa_pool_usd == Decimal("0.00")
        assert plan.others_pool_usd == Decimal("10.00")

    def test_frozen_model(self) -> None:
        plan = _basic_plan()
        with pytest.raises((TypeError, AttributeError, ValidationError)):
            plan.plan_id = "changed"  # type: ignore[misc]

    def test_features_default_empty_dict(self) -> None:
        plan = _basic_plan()
        assert plan.features == {}

    def test_plan_id_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(plan_id="a")

    def test_max_outbound_none_allowed(self) -> None:
        plan = _basic_plan(max_outbound_msg_per_day=None)
        assert plan.max_outbound_msg_per_day is None

    def test_max_outbound_zero_allowed(self) -> None:
        plan = _basic_plan(max_outbound_msg_per_day=0)
        assert plan.max_outbound_msg_per_day == 0

    def test_max_outbound_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _basic_plan(max_outbound_msg_per_day=-1)
