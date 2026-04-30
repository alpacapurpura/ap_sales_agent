"""Tests for BudgetGuardingLLMService and BudgetGuardingChatModel wrappers.

TDD (RED → GREEN per layer). Tests validate:
- Budget allowed → inner delegate called, return inner result.
- Budget exhausted → BudgetExceeded raised, inner NOT called.
- Soft warn → inner called, structlog warning emitted.
- __getattr__ proxy → bind_tools etc. pass through to inner.
- cost_estimator integration via estimate_llm_cost.

PR-6 / PI-1 S2 Sub-A.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.shared.billing.application.exceptions import BudgetExceeded
from src.shared.billing.application.llm_guards import (
    BudgetGuardingChatModel,
    BudgetGuardingLLMService,
)
from src.shared.billing.domain.budget_decision import BudgetDecision


def _make_decision(
    *,
    allowed: bool = True,
    soft_warn: bool = False,
    pool: str = "others",
    reason: str | None = None,
) -> BudgetDecision:
    return BudgetDecision(
        allowed=allowed,
        pool=pool,
        spent_usd=Decimal("1.00"),
        cap_usd=Decimal("5.00"),
        soft_warn=soft_warn,
        reason=reason,
    )


def _make_guard(decision: BudgetDecision) -> MagicMock:
    guard = MagicMock()
    guard.check = AsyncMock(return_value=decision)
    return guard


# ---------------------------------------------------------------------------
# BudgetGuardingChatModel — async path
# ---------------------------------------------------------------------------


class TestBudgetGuardingChatModelAinvoke:
    """Tests for BudgetGuardingChatModel.ainvoke (async LangGraph path)."""

    @pytest.mark.asyncio
    async def test_allowed_delegates_to_inner(self) -> None:
        """Allowed decision → ainvoke passes to inner and returns result."""
        inner = MagicMock()
        inner.ainvoke = AsyncMock(return_value="response_text")

        guard = _make_guard(_make_decision(allowed=True))
        tenant_id = uuid4()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=guard,
            tenant_id=tenant_id,
            agent_kind="copilot",
            model_hint="gpt-4o-mini",
        )

        result = await wrapper.ainvoke([{"role": "user", "content": "hello"}])

        assert result == "response_text"
        inner.ainvoke.assert_called_once()
        guard.check.assert_called_once_with(
            tenant_id=tenant_id,
            agent_kind="copilot",
            estimated_cost_usd=guard.check.call_args.kwargs["estimated_cost_usd"],
        )

    @pytest.mark.asyncio
    async def test_exhausted_raises_budget_exceeded(self) -> None:
        """Exhausted budget → BudgetExceeded raised, inner NOT called."""
        inner = MagicMock()
        inner.ainvoke = AsyncMock(return_value="should not be called")

        decision = _make_decision(allowed=False, reason="cycle_budget_exhausted", pool="others")
        guard = _make_guard(decision)
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="copilot",
        )

        with pytest.raises(BudgetExceeded) as exc_info:
            await wrapper.ainvoke([{"role": "user", "content": "hello"}])

        assert exc_info.value.decision.allowed is False
        assert exc_info.value.decision.reason == "cycle_budget_exhausted"
        inner.ainvoke.assert_not_called()

    @pytest.mark.asyncio
    async def test_soft_warn_delegates_and_logs(self, caplog: Any) -> None:
        """Soft warn allowed → inner called, structlog warning emitted."""
        import structlog

        inner = MagicMock()
        inner.ainvoke = AsyncMock(return_value="ok")

        decision = _make_decision(allowed=True, soft_warn=True, pool="others")
        guard = _make_guard(decision)
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="copilot",
        )

        result = await wrapper.ainvoke(["some message"])

        assert result == "ok"
        inner.ainvoke.assert_called_once()

    def test_getattr_proxies_to_inner(self) -> None:
        """__getattr__ proxies bind_tools etc. to inner."""
        inner = MagicMock()
        inner.bind_tools = MagicMock(return_value="bound")

        guard = _make_guard(_make_decision())
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="copilot",
        )

        result = wrapper.bind_tools(["tool_a"])
        assert result == "bound"
        inner.bind_tools.assert_called_once_with(["tool_a"])

    def test_getattr_with_structured_output_proxies(self) -> None:
        """with_structured_output proxied to inner."""
        inner = MagicMock()
        inner.with_structured_output = MagicMock(return_value="structured")

        guard = _make_guard(_make_decision())
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="copilot",
        )

        result = wrapper.with_structured_output({"type": "object"})
        assert result == "structured"


# ---------------------------------------------------------------------------
# BudgetGuardingLLMService — sync path
# ---------------------------------------------------------------------------


class TestBudgetGuardingLLMService:
    """Tests for BudgetGuardingLLMService.generate_response (sync surface)."""

    def test_allowed_delegates_to_inner(self) -> None:
        """Allowed decision → generate_response passes to inner."""
        inner = MagicMock()
        inner.generate_response = MagicMock(return_value="response")

        decision = _make_decision(allowed=True, pool="sales_agent")
        guard = MagicMock()
        guard.check = AsyncMock(return_value=decision)

        wrapper = BudgetGuardingLLMService(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="sales_agent",
            model_hint="deepseek-v4-flash",
        )

        result = wrapper.generate_response("test prompt")

        assert result == "response"
        inner.generate_response.assert_called_once()

    def test_exhausted_raises_budget_exceeded(self) -> None:
        """Exhausted SA pool → BudgetExceeded raised."""
        inner = MagicMock()
        inner.generate_response = MagicMock(return_value="should not be called")

        decision = _make_decision(allowed=False, pool="sales_agent", reason="cycle_budget_exhausted")
        guard = MagicMock()
        guard.check = AsyncMock(return_value=decision)

        wrapper = BudgetGuardingLLMService(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="sales_agent",
        )

        with pytest.raises(BudgetExceeded) as exc_info:
            wrapper.generate_response("some prompt")

        assert exc_info.value.decision.pool == "sales_agent"
        inner.generate_response.assert_not_called()

    def test_getattr_proxies_to_inner(self) -> None:
        """Unknown attributes proxy to inner service."""
        inner = MagicMock()
        inner.get_model_name = MagicMock(return_value="deepseek-v4-flash")

        guard = MagicMock()
        guard.check = AsyncMock(return_value=_make_decision())

        wrapper = BudgetGuardingLLMService(
            inner=inner,
            budget_guard=guard,
            tenant_id=uuid4(),
            agent_kind="sales_agent",
        )

        assert wrapper.get_model_name() == "deepseek-v4-flash"


# ---------------------------------------------------------------------------
# BudgetExceeded exception
# ---------------------------------------------------------------------------


class TestBudgetExceeded:
    def test_carries_decision(self) -> None:
        decision = _make_decision(allowed=False, reason="cycle_budget_exhausted")
        exc = BudgetExceeded(decision)
        assert exc.decision is decision
        assert "budget_exceeded" in str(exc)
        assert "cycle_budget_exhausted" in str(exc)

    def test_is_exception(self) -> None:
        exc = BudgetExceeded(_make_decision(allowed=False))
        assert isinstance(exc, Exception)


# ---------------------------------------------------------------------------
# cost_estimator unit tests
# ---------------------------------------------------------------------------


class TestEstimateLlmCost:
    """Unit tests for estimate_llm_cost pure function."""

    def test_fallback_rates_when_no_pricing(self) -> None:
        """No pricing accessor → uses conservative fallback rates."""
        from src.shared.billing.application.cost_estimator import estimate_llm_cost

        cost = estimate_llm_cost(
            prompt="hello world",
            max_output_tokens=100,
            model=None,
            agent_kind="copilot",
            pricing_accessor=None,
        )
        assert isinstance(cost, Decimal)
        assert cost > Decimal(0)

    def test_safety_multiplier_applied(self) -> None:
        """1.10x safety multiplier is applied."""
        from src.shared.billing.application.cost_estimator import estimate_llm_cost

        # With no pricing, same prompt twice → same result (deterministic)
        cost1 = estimate_llm_cost(
            prompt="a" * 100,
            max_output_tokens=100,
            model=None,
            agent_kind="copilot",
            pricing_accessor=None,
        )
        cost2 = estimate_llm_cost(
            prompt="a" * 100,
            max_output_tokens=100,
            model=None,
            agent_kind="copilot",
            pricing_accessor=None,
        )
        assert cost1 == cost2  # Pure / idempotent

    def test_larger_prompt_costs_more(self) -> None:
        """Longer prompt → higher cost estimate."""
        from src.shared.billing.application.cost_estimator import estimate_llm_cost

        short = estimate_llm_cost(
            prompt="hi",
            max_output_tokens=100,
            model=None,
            agent_kind="copilot",
        )
        long = estimate_llm_cost(
            prompt="a" * 10000,
            max_output_tokens=100,
            model=None,
            agent_kind="copilot",
        )
        assert long > short

    def test_with_pricing_snapshot(self) -> None:
        """With pricing snapshot → uses snapshot rates."""
        from src.shared.billing.application.cost_estimator import estimate_llm_cost

        pricing = MagicMock()
        pricing.input_cost_per_token = Decimal("0.000001")
        pricing.output_cost_per_token = Decimal("0.000002")
        pricing.raw_payload = {}

        cost = estimate_llm_cost(
            prompt="test prompt",
            max_output_tokens=200,
            model="gpt-4o-mini",
            agent_kind="copilot",
            pricing_accessor=pricing,
        )
        assert cost > Decimal(0)

    def test_resolve_provider_model_hint(self) -> None:
        """Agent kind → provider/model hint mapping."""
        from src.shared.billing.application.cost_estimator import resolve_provider_model_hint

        provider, model = resolve_provider_model_hint("sales_agent")
        assert provider == "deepseek"
        assert "flash" in model.lower() or "deepseek" in model.lower()

        provider2, model2 = resolve_provider_model_hint("copilot")
        assert provider2 == "openai"

        # Unknown agent_kind falls back to openai
        p, m = resolve_provider_model_hint("unknown")
        assert p == "openai"


# ---------------------------------------------------------------------------
# messages_to_prompt helper
# ---------------------------------------------------------------------------


class TestMessageToPrompt:
    def test_string_passthrough(self) -> None:
        from src.shared.billing.application.cost_estimator import _messages_to_prompt

        assert _messages_to_prompt("hello") == "hello"

    def test_list_of_dicts(self) -> None:
        from src.shared.billing.application.cost_estimator import _messages_to_prompt

        messages = [
            {"role": "system", "content": "You are a helper."},
            {"role": "user", "content": "What is 2+2?"},
        ]
        result = _messages_to_prompt(messages)
        assert "You are a helper." in result
        assert "What is 2+2?" in result

    def test_langchain_message_objects(self) -> None:
        from src.shared.billing.application.cost_estimator import _messages_to_prompt

        msg1 = MagicMock()
        msg1.content = "system content"
        msg2 = MagicMock()
        msg2.content = "user content"

        result = _messages_to_prompt([msg1, msg2])
        assert "system content" in result
        assert "user content" in result

    def test_empty_list(self) -> None:
        from src.shared.billing.application.cost_estimator import _messages_to_prompt

        assert _messages_to_prompt([]) == ""
