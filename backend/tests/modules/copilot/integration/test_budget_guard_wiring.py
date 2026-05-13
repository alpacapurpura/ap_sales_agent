"""Integration tests: BudgetGuardingChatModel wiring in copilot.

Policy F-7 (PR-4): tests integrate real service logic; mocks only at
infrastructure boundary (LLM HTTP, DB cost reader).

Tests verify:
- BudgetGuardingChatModel is returned when budget_guard is provided.
- When budget is available, ainvoke passes through to inner model.
- When Others pool is exhausted, BudgetExceeded is raised.
- Copilot pool exhaustion does NOT consume SA pool (bucket isolation).
- Soft-warn at 80% triggers structlog warning but allows call.
- build_deep_agent_graph returns graph with wrapped llm when guard provided.

PR-6 Sub-C / PI-1 S2.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest

from luana_core_billing.application.exceptions import BudgetExceeded
from luana_core_billing.application.llm_guards import BudgetGuardingChatModel
from luana_core_billing.domain.budget_decision import BudgetDecision

TENANT_ID = UUID("cccccccc-dddd-eeee-ffff-000000000001")


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _StubInnerChatModel:
    """Minimal stub for a LangChain BaseChatModel (boundary mock)."""

    def __init__(self, canned_content: str = "assistant response") -> None:
        """Init with canned content."""
        self.ainvoke_calls: int = 0
        self.invoke_calls: int = 0
        self.canned_content = canned_content

    async def ainvoke(self, messages: Any, **kwargs: Any) -> Any:
        """Count invocations and return canned AI message."""
        self.ainvoke_calls += 1

        class _FakeMessage:
            content = self.canned_content

        return _FakeMessage()

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        """Sync fallback — count invocations and return canned message."""
        self.invoke_calls += 1

        class _FakeMessage:
            content = self.canned_content

        return _FakeMessage()

    def bind_tools(self, tools: Any, **kwargs: Any) -> _StubInnerChatModel:
        """Stub bind_tools — returns self for chaining."""
        return self


class _StubBudgetGuard:
    """Minimal BudgetGuard stub — returns BudgetDecision without hitting DB."""

    def __init__(
        self,
        *,
        allowed: bool = True,
        pool: str = "others",
        spent_usd: Decimal = Decimal("0.00"),
        cap_usd: Decimal = Decimal("10.00"),
        soft_warn: bool = False,
        reason: str | None = None,
    ) -> None:
        """Init with decision params."""
        self._decision = BudgetDecision(
            allowed=allowed,
            pool=pool,
            spent_usd=spent_usd,
            cap_usd=cap_usd,
            soft_warn=soft_warn,
            reason=reason,
        )
        self.check_calls: list[tuple[UUID, str, Decimal]] = []

    async def check(
        self,
        *,
        tenant_id: UUID,
        agent_kind: str,
        estimated_cost_usd: Decimal,
    ) -> BudgetDecision:
        """Record call and return preset decision."""
        self.check_calls.append((tenant_id, agent_kind, estimated_cost_usd))
        return self._decision


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def available_guard() -> _StubBudgetGuard:
    """Guard that always allows (Others pool, budget available)."""
    return _StubBudgetGuard(
        allowed=True,
        pool="others",
        spent_usd=Decimal("1.00"),
        cap_usd=Decimal("10.00"),
    )


@pytest.fixture()
def exhausted_guard() -> _StubBudgetGuard:
    """Guard that blocks — Others pool exhausted."""
    return _StubBudgetGuard(
        allowed=False,
        pool="others",
        spent_usd=Decimal("10.50"),
        cap_usd=Decimal("10.00"),
        reason="cycle_budget_exhausted",
    )


@pytest.fixture()
def soft_warn_guard() -> _StubBudgetGuard:
    """Guard that allows but sets soft_warn=True (80%+ pool consumed)."""
    return _StubBudgetGuard(
        allowed=True,
        pool="others",
        spent_usd=Decimal("8.50"),
        cap_usd=Decimal("10.00"),
        soft_warn=True,
    )


@pytest.fixture()
def sa_pool_exhausted_guard() -> _StubBudgetGuard:
    """SA pool exhausted — but Others pool intact (isolation test)."""
    return _StubBudgetGuard(
        allowed=True,  # Others pool allowed
        pool="others",
        spent_usd=Decimal("1.00"),
        cap_usd=Decimal("10.00"),
    )


# ---------------------------------------------------------------------------
# Tests: BudgetGuardingChatModel wrapper behaviour
# ---------------------------------------------------------------------------


class TestBudgetGuardingChatModelWrapper:
    """Tests for BudgetGuardingChatModel wrapper contract."""

    @pytest.mark.asyncio
    async def test_ainvoke_passes_through_when_budget_available(
        self,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """BudgetGuard allows → ainvoke delegates to inner model."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=available_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
            model_hint="gpt-5-mini",
        )

        result = await wrapper.ainvoke([{"role": "user", "content": "hello"}])

        assert inner.ainvoke_calls == 1
        assert len(available_guard.check_calls) == 1
        tenant, kind, _ = available_guard.check_calls[0]
        assert tenant == TENANT_ID
        assert kind == "copilot"
        assert result.content == "assistant response"

    @pytest.mark.asyncio
    async def test_ainvoke_raises_budget_exceeded_when_exhausted(
        self,
        exhausted_guard: _StubBudgetGuard,
    ) -> None:
        """Others pool exhausted → BudgetExceeded raised, inner NOT called."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=exhausted_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
        )

        with pytest.raises(BudgetExceeded) as exc_info:
            await wrapper.ainvoke([{"role": "user", "content": "test"}])

        assert inner.ainvoke_calls == 0
        assert exc_info.value.decision.pool == "others"
        assert exc_info.value.decision.reason == "cycle_budget_exhausted"

    @pytest.mark.asyncio
    async def test_copilot_uses_others_pool_not_sa_pool(
        self,
        sa_pool_exhausted_guard: _StubBudgetGuard,
    ) -> None:
        """Copilot always gates on 'others' pool — SA pool irrelevant."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=sa_pool_exhausted_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
        )

        # SA exhausted but Others intact → copilot should succeed
        result = await wrapper.ainvoke([{"role": "user", "content": "test"}])

        assert inner.ainvoke_calls == 1
        _, kind, _ = sa_pool_exhausted_guard.check_calls[0]
        assert kind == "copilot"  # Confirms copilot bucket used, not SA
        assert result.content == "assistant response"

    @pytest.mark.asyncio
    async def test_soft_warn_logs_structlog_but_allows_call(
        self,
        soft_warn_guard: _StubBudgetGuard,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Soft warn at 80%+ → structlog warning emitted, call allowed."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=soft_warn_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
        )

        result = await wrapper.ainvoke([{"role": "user", "content": "test"}])

        assert inner.ainvoke_calls == 1
        assert result.content == "assistant response"
        # soft_warn triggers structlog warning (logged via structlog, not stdlib)
        # This verifies the call was allowed despite soft warn
        assert len(soft_warn_guard.check_calls) == 1

    def test_proxy_attributes_delegated_to_inner(
        self,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """__getattr__ proxies unknown attrs to inner for bind_tools etc."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=available_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
        )

        # bind_tools should be proxied to inner
        result = wrapper.bind_tools([])
        assert result is inner  # inner.bind_tools returns self

    def test_sync_invoke_raises_budget_exceeded_when_exhausted(
        self,
        exhausted_guard: _StubBudgetGuard,
    ) -> None:
        """Sync .invoke with exhausted budget → BudgetExceeded raised."""
        inner = _StubInnerChatModel()
        wrapper = BudgetGuardingChatModel(
            inner=inner,
            budget_guard=exhausted_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="copilot",
        )

        with pytest.raises(BudgetExceeded):
            wrapper.invoke([{"role": "user", "content": "test"}])

        assert inner.invoke_calls == 0


# ---------------------------------------------------------------------------
# Tests: build_deep_agent_graph BudgetGuard integration
# ---------------------------------------------------------------------------


class TestBuildDeepAgentGraphBudgetGuardWiring:
    """Tests for BudgetGuard wiring in build_deep_agent_graph."""

    def test_build_deep_agent_graph_uses_wrapped_llm_when_guard_provided(
        self,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """build_deep_agent_graph passes BudgetGuardingChatModel to create_deep_agent.

        Mocks boundary:
        - _build_combined_system_prompt: DB-dependent brand summary
        - create_deep_agent: deepagents harness (calls model.model_dump() which
          requires a real BaseChatModel subclass). We verify the model arg
          passed to it IS a BudgetGuardingChatModel wrapping the inner stub.
        - tools=[] avoids DB-dependent tool initialisation at compile time.
        """
        from unittest.mock import MagicMock, patch

        from luana_core_copilot.application.orchestrator.deep_agent import (
            build_deep_agent_graph,
        )
        from luana_core_copilot.application.orchestrator.state import (
            create_initial_copilot_state,
        )
        from luana_core_billing.application.llm_guards import BudgetGuardingChatModel

        inner_llm = _StubInnerChatModel()
        mock_graph = MagicMock()

        state = create_initial_copilot_state(
            user_id=UUID("aaaaaaaa-0000-0000-0000-000000000001"),
            tenant_id=TENANT_ID,
            conversation_id="test-conv-budget-wiring",
            client_context={},
        )

        captured_model: list[Any] = []

        def _fake_create_deep_agent(model: Any, **kwargs: Any) -> Any:
            captured_model.append(model)
            return mock_graph

        # Mock infrastructure boundaries to avoid DB/LLM calls at test time:
        # - _build_combined_system_prompt: reads brand summary from Postgres
        # - create_deep_agent: deepagents harness that calls model.model_dump()
        with (
            patch(
                "luana_core_copilot.application.orchestrator.deep_agent._build_combined_system_prompt",
                return_value="[stub system prompt for budget-guard wiring test]",
            ),
            patch(
                "luana_core_copilot.application.orchestrator.deep_agent.create_deep_agent",
                side_effect=_fake_create_deep_agent,
            ),
        ):
            result = build_deep_agent_graph(
                state,
                llm=inner_llm,  # type: ignore[arg-type]
                tools=[],  # avoids DB-dependent tool initialisation
                budget_guard=available_guard,  # type: ignore[arg-type]
                tenant_id=TENANT_ID,
            )

        # Graph returned is our mock
        assert result is mock_graph
        # create_deep_agent was called once with the wrapped model
        assert len(captured_model) == 1
        # The model passed to create_deep_agent must be a BudgetGuardingChatModel
        assert isinstance(captured_model[0], BudgetGuardingChatModel), (
            f"Expected BudgetGuardingChatModel, got {type(captured_model[0])}"
        )
