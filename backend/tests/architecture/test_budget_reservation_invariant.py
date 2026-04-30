"""Architecture fitness — budget reservation invariant.

Property-based invariant (manual coverage, no Hypothesis dependency):

INVARIANT: When copilot is exhausted (Others pool at 100%), it MUST NOT
consume the sales_agent reserved pool even if SA pool has budget left.
Conversely, SA exhausted MUST NOT consume Others pool.

This enforces the hard bucket separation in BudgetGuard:
  - agent_kind == "sales_agent" → ONLY SA pool checked.
  - agent_kind != "sales_agent" → ONLY Others pool checked.

Property coverage:
  - (plan_budget, sa_pct, spent_others, spent_sa, agent_kind) combinations.
  - Verifies that decision.pool aligns strictly with agent_kind.
  - Verifies that Others exhausted → copilot blocked, SA unaffected.
  - Verifies that SA exhausted → SA blocked, Others unaffected.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.shared.billing.application.budget_guard import BudgetGuard, SA_AGENT_KIND
from src.shared.billing.domain.budget_decision import BudgetDecision
from src.shared.billing.domain.plan import PlanConfig


# ── Test fixtures and helpers ────────────────────────────────────────────────


def _make_plan(
    total_usd: str = "30.00",
    sa_pct: str = "0.50",
) -> PlanConfig:
    """Create a minimal PlanConfig for invariant testing."""
    return PlanConfig(
        plan_id="test_plan",
        display_name="Test Plan",
        llm_budget_total_usd=Decimal(total_usd),
        sales_agent_reserved_pct=Decimal(sa_pct),
    )


def _make_guard(
    plan: PlanConfig,
    others_spent: Decimal,
    sa_spent: Decimal,
    mv_stale: bool = False,
) -> BudgetGuard:
    """Build a BudgetGuard with mocked dependencies."""
    plan_service = AsyncMock()
    plan_service.get_effective = AsyncMock(return_value=plan)

    cost_reader = AsyncMock()
    cost_reader.get_cycle_spend = AsyncMock(return_value=sa_spent)
    cost_reader.get_others_cycle_spend = AsyncMock(return_value=others_spent)

    mv_repo = AsyncMock()
    if mv_stale:
        mv_repo.get_last_refresh = AsyncMock(return_value=None)
    else:
        fresh_log = MagicMock()
        fresh_log.status = "ok"
        fresh_log.refreshed_at = dt.datetime.now(dt.timezone.utc)
        mv_repo.get_last_refresh = AsyncMock(return_value=fresh_log)

    return BudgetGuard(
        plan_service=plan_service,
        cost_reader=cost_reader,
        mv_refresh_log_repo=mv_repo,
    )


# ── Invariant 1: Bucket assignment is strict ─────────────────────────────────


@pytest.mark.parametrize(
    "agent_kind, expected_pool",
    [
        ("sales_agent", "sales_agent"),
        ("copilot", "others"),
        ("campaign", "others"),
        ("unknown_agent", "others"),
    ],
)
@pytest.mark.asyncio
async def test_bucket_assignment_strict(agent_kind: str, expected_pool: str) -> None:
    """Decision.pool must match strict bucket assignment rule."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    guard = _make_guard(plan, others_spent=Decimal("0.00"), sa_spent=Decimal("0.00"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind=agent_kind,
        estimated_cost_usd=Decimal("0.01"),
    )

    assert decision.pool == expected_pool, (
        f"agent_kind={agent_kind!r} must map to pool={expected_pool!r}, got pool={decision.pool!r}"
    )


# ── Invariant 2: Others exhausted → copilot blocked, SA pool unaffected ──────


@pytest.mark.asyncio
async def test_others_pool_exhausted_blocks_copilot() -> None:
    """When Others pool is at 100%, copilot call must be blocked."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    # Others pool = 30 * 0.50 = 15.00; spend others = 15.00 (exhausted)
    guard = _make_guard(plan, others_spent=Decimal("15.00"), sa_spent=Decimal("0.00"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="copilot",
        estimated_cost_usd=Decimal("0.01"),
    )

    assert not decision.allowed, "Copilot must be BLOCKED when Others pool is exhausted"
    assert decision.pool == "others"


@pytest.mark.asyncio
async def test_others_pool_exhausted_does_not_block_sales_agent() -> None:
    """CRITICAL INVARIANT: Others exhausted must NOT block sales_agent.

    The SA pool is separate. Even if copilot has burned 100% of Others
    pool, sales_agent must still be allowed (SA pool is fresh).
    """
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    # Others pool exhausted; SA pool fresh
    guard = _make_guard(plan, others_spent=Decimal("15.00"), sa_spent=Decimal("0.00"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="sales_agent",
        estimated_cost_usd=Decimal("0.01"),
    )

    assert decision.allowed, (
        "INVARIANT VIOLATED: sales_agent must NOT be blocked by Others pool exhaustion. "
        "SA pool is independent of Others pool."
    )
    assert decision.pool == "sales_agent"


# ── Invariant 3: SA exhausted → SA blocked, Others pool unaffected ────────────


@pytest.mark.asyncio
async def test_sa_pool_exhausted_blocks_sales_agent() -> None:
    """When SA pool is at 100%, sales_agent calls must be blocked."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    # SA pool = 30 * 0.50 = 15.00; spend sa = 15.00 (exhausted)
    guard = _make_guard(plan, others_spent=Decimal("0.00"), sa_spent=Decimal("15.00"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="sales_agent",
        estimated_cost_usd=Decimal("0.01"),
    )

    assert not decision.allowed, "sales_agent must be BLOCKED when SA pool is exhausted"
    assert decision.pool == "sales_agent"


@pytest.mark.asyncio
async def test_sa_pool_exhausted_does_not_block_copilot() -> None:
    """CRITICAL INVARIANT: SA exhausted must NOT block copilot.

    The Others pool is separate. Even if sales_agent burned 100% of SA
    pool, copilot must still be allowed (Others pool is fresh).
    """
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    # SA pool exhausted; Others pool fresh
    guard = _make_guard(plan, others_spent=Decimal("0.00"), sa_spent=Decimal("15.00"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="copilot",
        estimated_cost_usd=Decimal("0.01"),
    )

    assert decision.allowed, (
        "INVARIANT VIOLATED: copilot must NOT be blocked by SA pool exhaustion. Others pool is independent of SA pool."
    )
    assert decision.pool == "others"


# ── Invariant 4: Both pools exhausted → both blocked ─────────────────────────


@pytest.mark.asyncio
async def test_both_pools_exhausted_blocks_all_agents() -> None:
    """When both pools are exhausted, all agents must be blocked."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    # Both pools exhausted
    guard = _make_guard(plan, others_spent=Decimal("15.00"), sa_spent=Decimal("15.00"))

    for agent_kind in ("sales_agent", "copilot", "campaign"):
        decision = await guard.check(
            tenant_id=uuid.uuid4(),
            agent_kind=agent_kind,
            estimated_cost_usd=Decimal("0.01"),
        )
        assert not decision.allowed, f"agent_kind={agent_kind!r} must be BLOCKED when its pool is exhausted"


# ── Invariant 5: Zero SA reservation → no SA pool, 100% for others ───────────


@pytest.mark.asyncio
async def test_zero_sa_reservation_gives_all_budget_to_others() -> None:
    """With sa_pct=0, SA pool=0 (always blocked), Others=total budget."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.00")
    assert plan.sa_pool_usd == Decimal("0.00")
    assert plan.others_pool_usd == Decimal("30.00")

    guard = _make_guard(plan, others_spent=Decimal("0.00"), sa_spent=Decimal("0.00"))

    copilot_decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="copilot",
        estimated_cost_usd=Decimal("0.01"),
    )
    assert copilot_decision.allowed, "Others pool should be full at sa_pct=0"
    assert copilot_decision.cap_usd == Decimal("30.00"), (
        f"Others cap_usd should be 30.00 when sa_pct=0, got {copilot_decision.cap_usd}"
    )


# ── Invariant 6: SA constant SA_AGENT_KIND is "sales_agent" ──────────────────


def test_sa_agent_kind_constant() -> None:
    """SA_AGENT_KIND constant must be 'sales_agent' — immutable contract."""
    assert SA_AGENT_KIND == "sales_agent", (
        f"SA_AGENT_KIND must be 'sales_agent', got {SA_AGENT_KIND!r}. "
        "Changing this constant breaks the bucket reservation invariant across the codebase."
    )


# ── Invariant 7: BudgetDecision shape ────────────────────────────────────────


@pytest.mark.asyncio
async def test_decision_has_required_fields() -> None:
    """Every BudgetDecision must carry pool, spent_usd, cap_usd, decision_id."""
    plan = _make_plan(total_usd="30.00", sa_pct="0.50")
    guard = _make_guard(plan, others_spent=Decimal("1.00"), sa_spent=Decimal("0.50"))

    decision = await guard.check(
        tenant_id=uuid.uuid4(),
        agent_kind="copilot",
        estimated_cost_usd=Decimal("0.01"),
    )

    assert isinstance(decision, BudgetDecision)
    assert decision.pool in ("sales_agent", "others")
    assert isinstance(decision.spent_usd, Decimal)
    assert isinstance(decision.cap_usd, Decimal)
    assert decision.decision_id, "decision_id must be a non-empty string"
