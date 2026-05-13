"""LLM wrapper factories enforcing BudgetGuard.check() pre-call.

Two wrappers (PR-6 CONTRACT §4.1):

``BudgetGuardingLLMService``
    Wraps sync ``LLMService.generate_response(...)`` (sales_agent path).
    Sync-compatible — bridges to async BudgetGuard.check via
    ``_check_sync_bridge`` which uses nest_asyncio (already pinned in
    pyproject.toml as LangGraph dependency).

``BudgetGuardingChatModel``
    Wraps LangChain ``BaseChatModel`` (copilot / brand path).
    Hooks both ``.ainvoke`` (primary) and ``.invoke`` (fallback).
    Proxies unknown attributes to inner via ``__getattr__`` so
    ``.bind_tools``, ``.with_structured_output``, etc. work transparently.

Rationale (1000 clientes): wrapper in factory = single enforcement point.
New callsites added by future devs are automatically guarded — no manual
BudgetGuard.check needed per callsite.

PR-6 / PI-1 S2.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from luana_core_billing.application.budget_guard import BudgetGuard
from luana_core_billing.application.cost_estimator import (
    _messages_to_prompt,
    estimate_llm_cost,
)
from luana_core_billing.application.exceptions import BudgetExceeded
from luana_core_billing.domain.budget_decision import BudgetDecision

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Sync-to-async bridge
# ---------------------------------------------------------------------------


def _check_sync_bridge(
    *,
    guard: BudgetGuard,
    tenant_id: UUID,
    agent_kind: str,
    estimated_cost_usd: Decimal,
) -> BudgetDecision:
    """Run BudgetGuard.check from a sync context.

    Pattern (PR-6 CONTRACT §4.3):
    - If running inside an event loop (LangGraph node inside ainvoke):
      nest_asyncio is already applied at app startup → run_until_complete
      is safe.
    - If no loop (ARQ workers, unit tests outside asyncio context):
      asyncio.run() creates a new loop and awaits the coroutine.
    - Hard 3s timeout cap → fail-open (BudgetGuard's own fail-open
      contract for infrastructure failures).

    Invariant: never raise on timeout — return allow=True with
    reason="budget_guard_timeout_fail_open".
    """
    _timeout_fallback = BudgetDecision(
        allowed=True,
        pool="sales_agent" if agent_kind == "sales_agent" else "others",
        spent_usd=Decimal("0.00"),
        cap_usd=Decimal("0.00"),
        reason="budget_guard_timeout_fail_open",
    )

    async def _run_with_timeout() -> BudgetDecision:
        return await asyncio.wait_for(
            guard.check(
                tenant_id=tenant_id,
                agent_kind=agent_kind,
                estimated_cost_usd=estimated_cost_usd,
            ),
            timeout=3.0,
        )

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        if loop.is_running():
            # nest_asyncio already applied at app startup (LangGraph dep).
            import nest_asyncio

            nest_asyncio.apply(loop)
            return loop.run_until_complete(_run_with_timeout())
        return loop.run_until_complete(_run_with_timeout())
    except TimeoutError:
        logger.warning(
            "budget_guard_timeout_fail_open",
            tenant_id=str(tenant_id),
            agent_kind=agent_kind,
        )
        return _timeout_fallback
    except RuntimeError:
        try:
            return asyncio.run(_run_with_timeout())
        except TimeoutError:
            logger.warning(
                "budget_guard_timeout_fail_open",
                tenant_id=str(tenant_id),
                agent_kind=agent_kind,
            )
            return _timeout_fallback


# ---------------------------------------------------------------------------
# BudgetGuardingLLMService — wraps sync LLMService (sales_agent path)
# ---------------------------------------------------------------------------


class BudgetGuardingLLMService:
    """Wrapper around ``LLMFactory.get_service()`` instances (sync surface).

    Enforces ``BudgetGuard.check()`` BEFORE every
    ``generate_response(...)`` call.

    The inner BudgetGuard.check is async; the wrapper bridges via
    ``_check_sync_bridge`` (nest_asyncio already applied at startup).
    """

    def __init__(
        self,
        inner: Any,
        budget_guard: BudgetGuard,
        tenant_id: UUID,
        agent_kind: str,
        model_hint: str | None = None,
    ) -> None:
        """Initialise wrapper with guard configuration."""
        self._inner = inner
        self._guard = budget_guard
        self._tenant_id = tenant_id
        self._agent_kind = agent_kind
        self._model_hint = model_hint

    def generate_response(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        """Gate via BudgetGuard then delegate to inner service."""
        est_cost_usd = estimate_llm_cost(
            prompt=prompt,
            max_output_tokens=kwargs.get("max_tokens", 1024),
            model=self._model_hint or kwargs.get("model"),
            agent_kind=self._agent_kind,
        )
        decision = _check_sync_bridge(
            guard=self._guard,
            tenant_id=self._tenant_id,
            agent_kind=self._agent_kind,
            estimated_cost_usd=est_cost_usd,
        )
        if not decision.allowed:
            raise BudgetExceeded(decision)
        if decision.soft_warn:
            logger.warning(
                "budget_soft_warn",
                tenant_id=str(self._tenant_id),
                agent_kind=self._agent_kind,
                pool=decision.pool,
                spent_usd=str(decision.spent_usd),
                cap_usd=str(decision.cap_usd),
            )
        return self._inner.generate_response(prompt, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Proxy unknown attributes to inner so extended API works."""
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# BudgetGuardingChatModel — wraps BaseChatModel (copilot / brand path)
# ---------------------------------------------------------------------------


class BudgetGuardingChatModel:
    """LangChain-compatible wrapper for ``BaseChatModel``.

    Used by copilot's ``provider_factory.build_chat_model(...)`` and
    brand's ``_get_guarded_llm_service`` to wrap the returned
    ``BaseChatModel`` before binding tools / passing to LangGraph.

    Hooks both async ``.ainvoke`` (primary LangGraph path) and sync
    ``.invoke`` (rare fallback / subagent path).

    ``__getattr__`` proxies to inner so ``.bind_tools``,
    ``.with_structured_output``, ``.bind``, etc. work transparently.
    """

    def __init__(
        self,
        inner: Any,
        budget_guard: BudgetGuard,
        tenant_id: UUID,
        agent_kind: str,
        model_hint: str | None = None,
    ) -> None:
        """Initialise wrapper with guard configuration."""
        self._inner = inner
        self._guard = budget_guard
        self._tenant_id = tenant_id
        self._agent_kind = agent_kind
        self._model_hint = model_hint

    async def ainvoke(self, messages: Any, **kwargs: Any) -> Any:
        """Async gate via BudgetGuard then delegate."""
        est_cost_usd = estimate_llm_cost(
            prompt=_messages_to_prompt(messages),
            max_output_tokens=kwargs.get("max_tokens", 1024),
            model=self._model_hint,
            agent_kind=self._agent_kind,
        )
        decision = await self._guard.check(
            tenant_id=self._tenant_id,
            agent_kind=self._agent_kind,
            estimated_cost_usd=est_cost_usd,
        )
        if not decision.allowed:
            raise BudgetExceeded(decision)
        if decision.soft_warn:
            logger.warning(
                "budget_soft_warn",
                tenant_id=str(self._tenant_id),
                agent_kind=self._agent_kind,
                pool=decision.pool,
                spent_usd=str(decision.spent_usd),
                cap_usd=str(decision.cap_usd),
            )
        return await self._inner.ainvoke(messages, **kwargs)

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        """Sync fallback gate (LangGraph subagents may call sync)."""
        est_cost_usd = estimate_llm_cost(
            prompt=_messages_to_prompt(messages),
            max_output_tokens=kwargs.get("max_tokens", 1024),
            model=self._model_hint,
            agent_kind=self._agent_kind,
        )
        decision = _check_sync_bridge(
            guard=self._guard,
            tenant_id=self._tenant_id,
            agent_kind=self._agent_kind,
            estimated_cost_usd=est_cost_usd,
        )
        if not decision.allowed:
            raise BudgetExceeded(decision)
        if decision.soft_warn:
            logger.warning(
                "budget_soft_warn",
                tenant_id=str(self._tenant_id),
                agent_kind=self._agent_kind,
                pool=decision.pool,
            )
        return self._inner.invoke(messages, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Proxy unknown attributes to inner so bind_tools / bind etc. work."""
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# get_guarded_llm_service — centralised helper (PR-7 Sub-G)
# ---------------------------------------------------------------------------


def get_guarded_llm_service(
    *,
    tenant_id: UUID | None,
    agent_kind: str,
    budget_guard: BudgetGuard | None = None,
    model_hint: str | None = None,
) -> Any:
    """Return a BudgetGuard-wrapped LLM service when DI guard provided.

    Stable seam (PR-7 Sub-G — closes DR-7 brand callsites architecturally):
    callsites uniformly invoke this helper instead of ``LLMFactory.get_service()``.
    When a real ``BudgetGuard`` is threaded through DI (FastAPI provider or
    ARQ worker startup — S4 wiring), the helper transparently wraps. Until
    then, callers pass ``budget_guard=None`` and the plain service is
    returned (current behavior preserved).

    Construction contract:
    - ``tenant_id is None`` OR ``budget_guard is None`` → plain ``LLMFactory.get_service()``.
    - Both provided → ``BudgetGuardingLLMService(inner, budget_guard, tenant_id, agent_kind, model_hint)``.

    The helper deliberately does NOT construct ``BudgetGuard`` itself —
    construction requires async ``MVRefreshLogRepository`` + ``cost_reader``
    + ``PlanService`` and belongs at the DI boundary (request scope). That
    keeps callsites synchronous and decoupled from infra.

    Args:
        tenant_id: Tenant UUID; ``None`` disables guarding.
        agent_kind: Bucket key for BudgetGuard (e.g. ``"brand"``,
            ``"copilot"``, ``"sales_agent"``).
        budget_guard: Optional pre-constructed ``BudgetGuard`` (DI). When
            ``None`` the helper returns plain LLM service (S4 will wire DI).
        model_hint: Optional model SKU hint for cost estimation.

    Returns:
        ``BudgetGuardingLLMService`` when both ``tenant_id`` and
        ``budget_guard`` provided; else plain LLM service.
    """
    from luana_core_llm.factory import LLMFactory

    inner = LLMFactory.get_service()

    if tenant_id is None or budget_guard is None:
        return inner

    return BudgetGuardingLLMService(
        inner=inner,
        budget_guard=budget_guard,
        tenant_id=tenant_id,
        agent_kind=agent_kind,
        model_hint=model_hint,
    )
