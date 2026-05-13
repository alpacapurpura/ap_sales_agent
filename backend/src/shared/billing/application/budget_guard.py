"""BudgetGuard — gate proactivo pre-LLM-call.

Reservación 50% sales_agent invariant ENFORCED.
Copilot exhausto NUNCA consume SA pool aunque SA tenga budget disponible.
2 buckets separados: "sales_agent" y "others".

PM Q4: MV freshness probed via mv_refresh_log (not pg_stat_user_tables).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import time
import uuid as uuid_mod
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from luana_core_billing.domain.budget_decision import BudgetDecision
from luana_core_billing.domain.mv_refresh_log_repository import MVRefreshLogRepository

if TYPE_CHECKING:
    from luana_core_billing.application.plan_service import PlanService

logger = structlog.get_logger(__name__)

# MV name used by BudgetGuard cost queries.
# PM Q4: freshness probed via mv_refresh_log, NOT pg_stat_user_tables.
MV_NAME = "mv_daily_llm_cost_per_tenant_v2"
MV_STALENESS_TOLERANCE_SECONDS = 3600  # 1 hour
SOFT_CAP_OVER_FACTOR = Decimal("1.05")  # 5% tolerance when MV stale
SOFT_WARN_PCT = Decimal("0.80")  # 80% pool consumed triggers soft warning

# agent_kind → bucket. Any value != "sales_agent" → "others".
SA_AGENT_KIND = "sales_agent"


class BudgetGuard:
    """Gate proactivo pre-LLM-call. Reservación 50% SA invariant ENFORCED.

    INVARIANT (architectural, property-based test enforces):
    - agent_kind == "sales_agent" → ONLY checks SA pool.
    - agent_kind != "sales_agent" → ONLY checks Others pool.
    - Copilot exhausted (Others pool 0) CANNOT consume SA pool.
    - SA exhausted (SA pool 0) CANNOT consume Others pool.
    """

    def __init__(
        self,
        plan_service: PlanService,
        cost_reader: Any,  # duck-typed: async def get_cycle_spend(tenant_id, agent_kind, cycle_start) -> Decimal
        mv_refresh_log_repo: MVRefreshLogRepository,
        decision_cache_ttl_seconds: int = 300,
    ) -> None:
        """Initialise BudgetGuard with plan service and cost reader."""
        self._plan_service = plan_service
        self._cost_reader = cost_reader
        self._mv_refresh_log_repo = mv_refresh_log_repo
        self._cache: dict[str, tuple[BudgetDecision, float]] = {}
        self._cache_ttl = decision_cache_ttl_seconds

    async def _is_mv_stale(self) -> bool:
        """PM Q4: query mv_refresh_log for last refresh of MV_NAME.

        Returns True if:
        - No refresh has been recorded.
        - Last refresh status != 'ok'.
        - Last refresh older than MV_STALENESS_TOLERANCE_SECONDS.

        Soft-fail: if query errors → log warning + assume stale (safe default).
        MUST reference mv_refresh_log (not pg_stat_user_tables — PM Q4 decision).
        """
        try:
            last = await self._mv_refresh_log_repo.get_last_refresh(MV_NAME)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "budget_guard_mv_freshness_probe_failed",
                mv_name=MV_NAME,
                error=str(exc),
            )
            return True
        if last is None or last.status != "ok":
            return True
        age_seconds = (dt.datetime.now(dt.timezone.utc) - last.refreshed_at).total_seconds()
        return age_seconds > MV_STALENESS_TOLERANCE_SECONDS

    async def check(
        self,
        tenant_id: UUID,
        agent_kind: str,
        estimated_cost_usd: Decimal,
    ) -> BudgetDecision:
        """Decide if this LLM call can proceed.

        INVARIANT: bucket assignment is strict and exclusive.
        - agent_kind == "sales_agent" → SA pool ONLY.
        - agent_kind != "sales_agent" → Others pool ONLY.
        This is the architectural invariant tested by test_budget_reservation_invariant.py.

        Logic:
        1. Resolve effective plan (cached). Compute SA / Others pool caps.
        2. Assign bucket based on agent_kind (strict separation).
        3. Cache hit → return cached decision.
        4. Probe MV freshness via mv_refresh_log.
        5. Get cycle spend for the bucket's agent_kinds.
        6. Compute new_total = spent + estimated_cost_usd.
        7. Decide: allowed/blocked/soft_warn.
        8. Cache decision (5min).

        Graceful degradation:
        - MV stale → soft cap 105% (admit 5% overrun vs blocking).
        - MV query fails → fail-open (log error, return allowed=True).
        """
        # 1. Resolve plan caps
        plan = await self._plan_service.get_effective(tenant_id)

        # 2. INVARIANT: strict bucket assignment
        if agent_kind == SA_AGENT_KIND:
            pool = SA_AGENT_KIND
            cap_usd = plan.sa_pool_usd
        else:
            pool = "others"
            cap_usd = plan.others_pool_usd

        # 3. Cache hit
        cache_key = f"{tenant_id}:{pool}"
        now = time.monotonic()
        cached = self._cache.get(cache_key)
        if cached is not None:
            decision, expires_at = cached
            if now < expires_at:
                return decision

        # 4. Probe MV freshness
        mv_stale = await self._is_mv_stale()
        effective_cap = cap_usd * SOFT_CAP_OVER_FACTOR if mv_stale else cap_usd

        # 5. Get cycle spend for this bucket
        spent_usd = Decimal("0.00")
        try:
            spent_usd = await self._get_bucket_spend(
                tenant_id=tenant_id,
                agent_kind=agent_kind,
            )
        except Exception as exc:  # noqa: BLE001 — graceful degradation: fail-open
            logger.error(
                "budget_guard_spend_query_failed_fail_open",
                tenant_id=str(tenant_id),
                agent_kind=agent_kind,
                error=str(exc),
            )
            decision = BudgetDecision(
                allowed=True,
                pool=pool,
                spent_usd=Decimal("0.00"),
                cap_usd=effective_cap,
                reason="mv_query_failure_fail_open",
                decision_id=str(uuid_mod.uuid4()),
            )
            self._cache[cache_key] = (decision, now + self._cache_ttl)
            return decision

        # 6. Compute new total
        new_total = spent_usd + estimated_cost_usd

        # 7. Decide
        if new_total >= effective_cap:
            reason = "mv_stale_soft_cap" if mv_stale else "cycle_budget_exhausted"
            decision = BudgetDecision(
                allowed=False,
                pool=pool,
                spent_usd=spent_usd,
                cap_usd=effective_cap,
                reason=reason,
                decision_id=str(uuid_mod.uuid4()),
            )
        elif new_total >= cap_usd * SOFT_WARN_PCT:
            decision = BudgetDecision(
                allowed=True,
                pool=pool,
                spent_usd=spent_usd,
                cap_usd=effective_cap,
                soft_warn=True,
                decision_id=str(uuid_mod.uuid4()),
            )
        else:
            decision = BudgetDecision(
                allowed=True,
                pool=pool,
                spent_usd=spent_usd,
                cap_usd=effective_cap,
                decision_id=str(uuid_mod.uuid4()),
            )

        # 8. Cache
        self._cache[cache_key] = (decision, now + self._cache_ttl)
        return decision

    async def _get_bucket_spend(
        self,
        tenant_id: UUID,
        agent_kind: str,
    ) -> Decimal:
        """Get current cycle spend for the bucket via cost_reader.

        The cost_reader is a duck-typed protocol:
            async def get_cycle_spend(tenant_id, agent_kind) -> Decimal

        For SA pool: only 'sales_agent' spend counts.
        For Others pool: all non-'sales_agent' spend counts (copilot + campaign + future).
        """
        if agent_kind == SA_AGENT_KIND:
            return await self._cost_reader.get_cycle_spend(tenant_id=tenant_id, agent_kind=SA_AGENT_KIND)
        # Others pool: aggregate all non-SA agent kinds
        return await self._cost_reader.get_others_cycle_spend(tenant_id=tenant_id)
