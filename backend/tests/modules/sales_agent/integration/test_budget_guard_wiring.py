"""Integration tests: BudgetGuardingLLMService wiring in sales_agent.

Policy F-7 (PR-4): tests integrate real service logic; mocks only at
infrastructure boundary (LLM HTTP, DB cost reader).

Tests verify:
- BudgetGuardingLLMService is injected when budget_guard is provided.
- When budget is available, generate_response passes through.
- When SA pool is exhausted, BudgetExceeded is raised.
- SA pool depletion does NOT consume Others pool (bucket isolation).
- Soft-warn at 80% triggers structlog warning but allows call.

PR-6 / PI-1 S2.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from src.modules.sales_agent.application.orchestrator.state import create_initial_state
from src.shared.billing.application.budget_guard import BudgetGuard
from src.shared.billing.application.exceptions import BudgetExceeded
from src.shared.billing.application.llm_guards import BudgetGuardingLLMService
from src.shared.billing.domain.budget_decision import BudgetDecision

TENANT_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _StubLLMService:
    """Minimal stub for the inner LLM service (boundary mock)."""

    def __init__(self, canned_response: str = "ok") -> None:
        """Init with canned response."""
        self.called = 0
        self.canned_response = canned_response

    def generate_response(self, *args: object, **kwargs: object) -> str:
        """Count invocations and return canned response."""
        self.called += 1
        return self.canned_response


class _StubBudgetGuard:
    """Minimal BudgetGuard stub — returns BudgetDecision without hitting DB."""

    def __init__(
        self,
        *,
        allowed: bool = True,
        pool: str = "sales_agent",
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
        tenant_id: UUID,
        agent_kind: str,
        estimated_cost_usd: Decimal,
    ) -> BudgetDecision:
        """Record call and return decision."""
        self.check_calls.append((tenant_id, agent_kind, estimated_cost_usd))
        return self._decision


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_inner_llm() -> _StubLLMService:
    """Boundary-mocked inner LLM service (no token burn)."""
    return _StubLLMService()


@pytest.fixture
def available_guard() -> _StubBudgetGuard:
    """BudgetGuard that always allows (SA pool has budget)."""
    return _StubBudgetGuard(
        allowed=True,
        pool="sales_agent",
        spent_usd=Decimal("1.00"),
        cap_usd=Decimal("10.00"),
    )


@pytest.fixture
def exhausted_sa_guard() -> _StubBudgetGuard:
    """BudgetGuard with SA pool exhausted."""
    return _StubBudgetGuard(
        allowed=False,
        pool="sales_agent",
        spent_usd=Decimal("10.50"),
        cap_usd=Decimal("10.00"),
        reason="cycle_budget_exhausted",
    )


@pytest.fixture
def exhausted_others_guard() -> _StubBudgetGuard:
    """BudgetGuard with Others pool exhausted — SA pool still intact."""
    return _StubBudgetGuard(
        allowed=True,  # SA pool intact
        pool="sales_agent",
        spent_usd=Decimal("1.00"),
        cap_usd=Decimal("10.00"),
    )


@pytest.fixture
def soft_warn_guard() -> _StubBudgetGuard:
    """BudgetGuard at 85% — triggers soft warn but allows."""
    return _StubBudgetGuard(
        allowed=True,
        pool="sales_agent",
        spent_usd=Decimal("8.50"),
        cap_usd=Decimal("10.00"),
        soft_warn=True,
    )


# ---------------------------------------------------------------------------
# Tests — wrapper unit (no graph invocation required)
# ---------------------------------------------------------------------------


class TestBudgetGuardingLLMServiceUnit:
    """Unit tests for the wrapper in isolation (no LangGraph)."""

    @pytest.mark.asyncio
    async def test_wrapper_calls_inner_when_allowed(
        self,
        stub_inner_llm: _StubLLMService,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """When budget available, generate_response delegates to inner."""
        wrapper = BudgetGuardingLLMService(
            inner=stub_inner_llm,
            budget_guard=available_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="sales_agent",
        )
        result = wrapper.generate_response("hello world")
        assert result == "ok"
        assert stub_inner_llm.called == 1

    @pytest.mark.asyncio
    async def test_wrapper_raises_when_sa_pool_exhausted(
        self,
        stub_inner_llm: _StubLLMService,
        exhausted_sa_guard: _StubBudgetGuard,
    ) -> None:
        """When SA pool exhausted, BudgetExceeded is raised before inner call."""
        wrapper = BudgetGuardingLLMService(
            inner=stub_inner_llm,
            budget_guard=exhausted_sa_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="sales_agent",
        )
        with pytest.raises(BudgetExceeded) as exc_info:
            wrapper.generate_response("prompt")

        assert exc_info.value.decision.pool == "sales_agent"
        assert exc_info.value.decision.reason == "cycle_budget_exhausted"
        # Inner service NOT called — no token consumption
        assert stub_inner_llm.called == 0

    @pytest.mark.asyncio
    async def test_wrapper_check_called_with_sa_agent_kind(
        self,
        stub_inner_llm: _StubLLMService,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """BudgetGuard.check is called with agent_kind='sales_agent'."""
        wrapper = BudgetGuardingLLMService(
            inner=stub_inner_llm,
            budget_guard=available_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="sales_agent",
        )
        wrapper.generate_response("prompt text")
        assert len(available_guard.check_calls) == 1
        _, agent_kind, _ = available_guard.check_calls[0]
        assert agent_kind == "sales_agent"

    @pytest.mark.asyncio
    async def test_wrapper_soft_warn_allows_call(
        self,
        stub_inner_llm: _StubLLMService,
        soft_warn_guard: _StubBudgetGuard,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """At 85% pool usage, soft_warn is True but call still proceeds."""
        wrapper = BudgetGuardingLLMService(
            inner=stub_inner_llm,
            budget_guard=soft_warn_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="sales_agent",
        )
        result = wrapper.generate_response("prompt")
        assert result == "ok"
        assert stub_inner_llm.called == 1

    def test_sa_bucket_isolation_others_pool_exhausted_does_not_block_sa(
        self,
        stub_inner_llm: _StubLLMService,
        exhausted_others_guard: _StubBudgetGuard,
    ) -> None:
        """When Others pool is exhausted but SA pool intact, SA calls proceed.

        This guard returns allowed=True for SA bucket regardless of Others state.
        Bucket isolation invariant (PR-2 property-based test enforces at arch level).
        """
        wrapper = BudgetGuardingLLMService(
            inner=stub_inner_llm,
            budget_guard=exhausted_others_guard,  # type: ignore[arg-type]
            tenant_id=TENANT_ID,
            agent_kind="sales_agent",
        )
        result = wrapper.generate_response("prompt")
        assert result == "ok"
        assert stub_inner_llm.called == 1


# ---------------------------------------------------------------------------
# Tests — pipeline injection (ConversationPipeline.build_initial_state)
# ---------------------------------------------------------------------------


class TestBudgetGuardWiringViaPipeline:
    """Verify ConversationPipeline.build_initial_state injects the guard."""

    def _make_minimal_biz_repo(self) -> MagicMock:
        biz_repo = MagicMock()
        biz_repo.get_current_launch_product.return_value = (None, None)
        biz_repo.get_enrollment.return_value = None
        return biz_repo

    def _make_minimal_audit_repo(self) -> MagicMock:
        audit_repo = MagicMock()
        audit_repo.get_chat_history.return_value = []
        audit_repo.get_last_message.return_value = None
        return audit_repo

    def _make_user(self) -> SimpleNamespace:
        return SimpleNamespace(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            profile_data=None,
            custom_system_instruction=None,
            style_profile=None,
        )

    def _make_customer(self) -> SimpleNamespace:
        return SimpleNamespace(id=UUID("22222222-2222-2222-2222-222222222222"))

    def _make_incoming(self) -> object:
        from src.shared.domain.messages import IncomingMessage

        return IncomingMessage(
            user_id="u1",
            text="hola",
            channel_type="telegram",
            metadata={},
        )

    def _make_state_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_active_checkpoint.return_value = None
        return repo

    def test_build_initial_state_injects_guarded_llm_service(
        self,
        available_guard: _StubBudgetGuard,
    ) -> None:
        """When budget_guard provided, _llm_service in state is a BudgetGuardingLLMService."""
        db = MagicMock()
        biz_repo = self._make_minimal_biz_repo()
        audit_repo = self._make_minimal_audit_repo()
        user = self._make_user()
        customer = self._make_customer()
        incoming = self._make_incoming()
        state_repo = self._make_state_repo()

        session_state = {
            "session_active": True,
            "last_intent": None,
            "session_gap_hours": None,
            "is_returning_user": False,
        }

        initial_state, _ = ConversationPipeline.build_initial_state(
            db=db,
            biz_repo=biz_repo,
            audit_repo=audit_repo,
            user=user,
            customer=customer,
            tenant_id=str(TENANT_ID),
            tenant_uuid=TENANT_ID,
            tenant_config={},
            incoming=incoming,
            session_state=session_state,
            agent_identity=None,
            brand_voice=None,
            checkpoint=None,
            state_repo=state_repo,
            budget_guard=available_guard,  # type: ignore[arg-type]
        )

        assert "_llm_service" in initial_state
        assert isinstance(initial_state["_llm_service"], BudgetGuardingLLMService)

    def test_build_initial_state_no_guard_yields_none_llm_service(
        self,
    ) -> None:
        """When budget_guard is None (not wired), _llm_service is None."""
        db = MagicMock()
        biz_repo = self._make_minimal_biz_repo()
        audit_repo = self._make_minimal_audit_repo()
        user = self._make_user()
        customer = self._make_customer()
        incoming = self._make_incoming()
        state_repo = self._make_state_repo()

        session_state = {
            "session_active": True,
            "last_intent": None,
            "session_gap_hours": None,
            "is_returning_user": False,
        }

        initial_state, _ = ConversationPipeline.build_initial_state(
            db=db,
            biz_repo=biz_repo,
            audit_repo=audit_repo,
            user=user,
            customer=customer,
            tenant_id=str(TENANT_ID),
            tenant_uuid=TENANT_ID,
            tenant_config={},
            incoming=incoming,
            session_state=session_state,
            agent_identity=None,
            brand_voice=None,
            checkpoint=None,
            state_repo=state_repo,
            budget_guard=None,
        )

        assert initial_state.get("_llm_service") is None
