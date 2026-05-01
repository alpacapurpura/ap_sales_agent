# CONTRACT — PR-6-consumers-cutover

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builder consume este archivo.
>
> Sesión: 2026-04-30 — architect resume post-pause (sesión previa investigando pricing snapshot async query). Skills consultados: `copilot-expert` (LLM call sites + observabilidad), `sales-agent-expert` (BudgetGuard wiring SA pool reservation invariant + LLMFactory `generate_response` sync surface), `tessl__graceful-degradation` (BudgetGuard fallback strategy), `backend-expert` (architectural fitness + DDD).
>
> Reglas duras: `tenant-isolation.md`, `backend-ddd.md`, `architectural-fitness.md`, `tdd-mandatory.md`, `parallel-safety.md`. **PR-1/PR-2 primitivas disponibles**: outbox + `EventBusAdapter` + `BudgetGuard` + `OutboundRateLimiter` + `PricingSnapshotRepository` (sync). **PR-5 wiring precedent**: `TelegramChannelRouter.send` consume `OutboundRateLimiter` + `ComplianceService`.

## 0. Context summary

| Campo | Valor |
|---|---|
| Modules touched | `core/config.py` (3 flag defaults), `modules/sales_agent/application/`, `modules/copilot/application/`, `modules/brand/application/`, `shared/billing/infrastructure/` (NEW async accessor), tests integration + arch |
| Skills consulted | `copilot-expert` (LLM call sites: `llm.invoke` en `intent_classifier.py`, `synthesizer.py`, `url_inspiration_analyzer.py`, `llm_classifier.py`, `judge.py` + `astream_events` graph en `chat.py:1111` — wrapper estrategia `BudgetGuardingChatModel` evita parchar 8 sitios). `sales-agent-expert` (`LLMFactory.get_service().generate_response` en `agents/sales/nodes.py` + `conversation_pipeline.py` + `quality/judge.py` + `safety_service.py` + `follow_up_engine.py` + `appointment_reminder_engine.py` — bucket=`sales_agent` reserved pool 50% invariant ENFORCED). `tessl__graceful-degradation` (BudgetGuard fail-open ya implementado en `_get_bucket_spend` exception → retorna `allowed=True` con `reason="mv_query_failure_fail_open"`). `backend-expert` (DDD inside-out + arch ratchet shrink-only + AST scan precedents). |
| pm-nico/current-state files | `sales-agent.md` (capability "BudgetGuard wired pre-LLM call + outbox path activo cross-instance"), `copilot.md` (idem + cost runaway protection 1000 clientes), `brand.md` (capability "outbox path activo extraction + style_analyzer + voice_fidelity wired BudgetGuard"). All 3 lineage-append, no rewrite. |
| Architecture gates | EXISTING (no romper): `test_outbox_invariants.py`, `test_compliance_used_by_channels.py`, `test_no_hardcoded_plan_prices.py`, `test_budget_reservation_invariant.py` (PR-2), `test_ddd_boundaries.py`, `test_copilot_anchors.py`. **NEW (this PR)**: `test_budget_guard_pre_llm_call.py` (AST scan), `test_no_legacy_event_bus_publish.py` (ratchet shrink-only). |
| Out of scope | Inbound flow ChatOrchestrator BudgetGuard wiring (S3), `OutboundOrchestrator` campaigns (S3), copilot tools campaigns (PI-2), `USE_OUTBOX_PATTERN_DEFAULT=True` global flip (post-PI-1). |

**Decisión arquitectónica clave:** PR-6 es **infra cutover atómico**, sin nueva surface user-facing. El "retire 20 emisores legacy" del PR.md descripción es un **misframe** — los 22 call-sites identificados ya usan `EventBusAdapter` (alias `EventBus`). El cutover real = flip de los 3 flags `USE_OUTBOX_PATTERN_*`. La "retirada legacy" reduce a:
1. Drop import vestigial `from src.shared.domain.events import EventBus as _LegacyEventBus` en `copilot/observability/recording/domain_subscribers.py:120` (single line dead code).
2. Migrar los 4 emisores que pasan `session=None` (mode broadcast) — el adapter con flag ON loggea `outbox_skip_no_session` y cae a legacy. Esto **NO bloquea el cutover** pero introduce silent durabilidad gap. Mitigación: builder pasa `session` real donde haya transacción disponible (3 sites detectables), 1 site (`personality_service.py:122` cache invalidation broadcast) **queda explícitamente en path legacy** documentado en `docs/domains/copilot/INDEX.md` (no requiere durabilidad — invalidation cache).

## 1. Domain entities (modificadas)

**Ninguna entidad nueva.** PR-6 es wiring puro. Las primitivas ya existen:

- `BudgetGuard` (`shared/billing/application/budget_guard.py`) — `check(tenant_id, agent_kind, estimated_cost_usd) -> BudgetDecision`.
- `BudgetDecision` (`shared/billing/domain/budget_decision.py`) — VO frozen.
- `OutboxService.enqueue_*` (`shared/domain_events/outbox/application/outbox_service.py`) — consumido vía `EventBusAdapter.publish(event, session=...)`.
- `PricingSnapshotRepository` (`shared/agent_observability/persistence/pricing_snapshot_repository.py`) — **SYNC**. Bind a `Session` (psycopg2). Necesita accessor async para builders LangChain async (Q-1).

## 2. SQLAlchemy 2.0 models

**Ninguna tabla nueva**. El modelo `ModelPricingSnapshotModel` (existente, SQLAlchemy 1.x-style `Column(...)` legacy — fuera de scope este PR refactor a `mapped_column`) se reutiliza tal cual.

## 3. Pydantic v2 DTOs

**Ningún DTO nuevo**. Re-uso de existentes:

- `BudgetDecision` (dataclass frozen — VO, no Pydantic).
- `PlanConfig`, `TenantSubscription` (Pydantic v2 frozen, ya existentes).
- Excepción `BudgetExceeded` (NEW, escala via raise — no DTO):

```python
# shared/billing/application/exceptions.py (NEW)
from __future__ import annotations
from src.shared.billing.domain.budget_decision import BudgetDecision

class BudgetExceeded(Exception):
    """Raised when BudgetGuard.check returns allowed=False.

    Carries the BudgetDecision so the caller (orchestrator/middleware)
    can map to HTTP 402 with structured payload.
    """
    def __init__(self, decision: BudgetDecision) -> None:
        self.decision = decision
        super().__init__(
            f"budget_exceeded pool={decision.pool} "
            f"spent={decision.spent_usd} cap={decision.cap_usd} "
            f"reason={decision.reason}"
        )
```

## 4. BudgetGuard wiring spec

### 4.1 Wrapper pattern — evita parchar 14 sitios LLM

PR-6 introduce **`BudgetGuardingLLMService`** + **`BudgetGuardingChatModel`** wrappers (NEW, `shared/billing/application/llm_guards.py`). En lugar de parchar cada `llm.invoke(...)` / `LLMFactory.get_service().generate_response(...)` callsite, los **factories** de LLM se reemplazan a nivel orchestrator entry para inyectar el guard.

**Rationale (1000 clientes):** wrapper en factory = single point of enforcement. Si un dev futuro agrega un nuevo callsite LLM en sales_agent / copilot / brand, el wrapper lo gates automáticamente sin que el dev se acuerde de wirear `BudgetGuard.check` manualmente. Arch test (§9) detecta `LLMFactory.get_service()` calls fuera de wrapper como fallback safety.

**Alternativa descartada:** parchar cada sitio inline (14 sitios distintos x 3 módulos). Más visible pero alta deuda — cualquier callsite nuevo se olvida. Decisión D27 confirmada con esta extensión.

### 4.2 Wrapper signatures

```python
# shared/billing/application/llm_guards.py (NEW)
from __future__ import annotations
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from src.shared.billing.application.budget_guard import BudgetGuard
from src.shared.billing.application.exceptions import BudgetExceeded
from src.shared.billing.application.cost_estimator import estimate_llm_cost  # §5

logger = structlog.get_logger(__name__)


class BudgetGuardingLLMService:
    """Wrapper around `LLMFactory.get_service()` instances.

    Enforces BudgetGuard.check() BEFORE every `generate_response(...)`
    call. Sync-compatible — the inner BudgetGuard.check is async, so the
    wrapper requires an async caller; sync callers (sales_agent legacy
    nodes via LangGraph node fn) execute through `_check_sync_bridge`
    which uses `asyncio.run` if no loop, else schedules on the running
    loop and awaits. Decision below.
    """

    def __init__(
        self,
        inner: Any,                 # duck-typed LLMService
        budget_guard: BudgetGuard,
        tenant_id: UUID,
        agent_kind: str,            # "sales_agent" | "copilot" | "brand"
        model_hint: str | None = None,  # for cost estimate fallback
    ) -> None:
        self._inner = inner
        self._guard = budget_guard
        self._tenant_id = tenant_id
        self._agent_kind = agent_kind
        self._model_hint = model_hint

    def generate_response(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        # 1. Estimate cost from prompt + max_tokens kwargs
        est_cost_usd = estimate_llm_cost(
            prompt=prompt,
            max_output_tokens=kwargs.get("max_tokens", 1024),
            model=self._model_hint or kwargs.get("model"),
            agent_kind=self._agent_kind,
        )
        # 2. Sync-bridge to async BudgetGuard.check
        decision = _check_sync_bridge(
            guard=self._guard,
            tenant_id=self._tenant_id,
            agent_kind=self._agent_kind,
            estimated_cost_usd=est_cost_usd,
        )
        if not decision.allowed:
            raise BudgetExceeded(decision)
        # 3. Soft warn — log structlog (no throw)
        if decision.soft_warn:
            logger.warning(
                "budget_soft_warn",
                tenant_id=str(self._tenant_id),
                agent_kind=self._agent_kind,
                pool=decision.pool,
                spent_usd=str(decision.spent_usd),
                cap_usd=str(decision.cap_usd),
            )
        # 4. Pass through to inner LLM
        return self._inner.generate_response(prompt, *args, **kwargs)


class BudgetGuardingChatModel:
    """LangChain-compatible wrapper for `BaseChatModel` (copilot path).

    Used by copilot's `provider_factory.build_chat_model(...)` to wrap
    the returned BaseChatModel before binding tools / passing to
    LangGraph. Hooks both sync `.invoke(messages)` and async
    `.ainvoke(messages)`.
    """

    def __init__(
        self,
        inner: Any,                 # langchain_core.language_models.BaseChatModel
        budget_guard: BudgetGuard,
        tenant_id: UUID,
        agent_kind: str,
        model_hint: str | None = None,
    ) -> None:
        self._inner = inner
        self._guard = budget_guard
        self._tenant_id = tenant_id
        self._agent_kind = agent_kind
        self._model_hint = model_hint

    async def ainvoke(self, messages: Any, **kwargs: Any) -> Any:
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
            )
        return await self._inner.ainvoke(messages, **kwargs)

    def invoke(self, messages: Any, **kwargs: Any) -> Any:
        # LangGraph subagents may invoke sync (rare). Sync bridge:
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
        return self._inner.invoke(messages, **kwargs)

    # __getattr__ proxies to inner so .bind_tools / .with_structured_output / etc. work transparently
    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)
```

### 4.3 Sync-async bridge

```python
def _check_sync_bridge(
    *,
    guard: BudgetGuard,
    tenant_id: UUID,
    agent_kind: str,
    estimated_cost_usd: Decimal,
) -> BudgetDecision:
    """Run BudgetGuard.check from sync context.

    Invariants:
    - If we are inside a running event loop (sales_agent LangGraph node
      executes inside `agent_app.ainvoke(...)`), `loop.is_running()` is
      True → schedule via `asyncio.run_coroutine_threadsafe` ONLY when
      loop accessible from another thread; in same-thread case (most
      common) we await via `asyncio.ensure_future` + a thread-local
      sentinel. **Builder must use `nest_asyncio` already pinned in
      `backend/pyproject.toml`** (already used by LangGraph). Pattern:
      `asyncio.get_event_loop().run_until_complete(coro)` after
      `nest_asyncio.apply()`.
    - If no loop → `asyncio.run(coro)` (covers ARQ workers + cron).
    - On exception → fail-open (BudgetGuard already handles internally;
      bridge re-raises only TimeoutError after 3s hard cap).
    """
    import asyncio
    coro = guard.check(
        tenant_id=tenant_id,
        agent_kind=agent_kind,
        estimated_cost_usd=estimated_cost_usd,
    )
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # nest_asyncio already applied at app startup (LangGraph dep)
            return loop.run_until_complete(asyncio.wait_for(coro, timeout=3.0))
        return loop.run_until_complete(asyncio.wait_for(coro, timeout=3.0))
    except RuntimeError:
        return asyncio.run(asyncio.wait_for(coro, timeout=3.0))
    except TimeoutError:
        # 3s cap → fail-open (BudgetGuard fail-open contract)
        logger.warning("budget_guard_timeout_fail_open", tenant_id=str(tenant_id))
        return BudgetDecision(
            allowed=True,
            pool="sales_agent" if agent_kind == "sales_agent" else "others",
            spent_usd=Decimal("0.00"),
            cap_usd=Decimal("0.00"),
            reason="budget_guard_timeout_fail_open",
        )
```

### 4.4 402 handling

`BudgetExceeded` is raised inside the LLM wrapper. The orchestrator catches it at the outermost boundary and maps:

- **Sales_agent inbound (telegram webhook)** — `application/orchestrator/conversation_pipeline.py` `process_inbound(...)` outermost try/except: `BudgetExceeded` → emit `BudgetExceededEvent` to outbox (NEW domain event, §) + skip OutputManager send + log structlog. **NO 402 returned to webhook** (Telegram retries). Lead receives nothing this turn — graceful degradation.
- **Copilot HTTP route** — `modules/copilot/api/chat.py` (or `suggestions.py`): `BudgetExceeded` → return `JSONResponse(status_code=402, content={"detail": "budget_exhausted", "decision_id": decision.decision_id, "pool": decision.pool, "reason": decision.reason})`. FE handler shows plan_card "presupuesto agotado" (PI-2).
- **Brand worker (extraction / personality / voice_fidelity)** — `modules/brand/workers/tasks.py`: `BudgetExceeded` → mark ARQ job as `status=skipped_budget_exhausted` + emit event. Job NOT retried. Re-runs on next cycle when budget resets.

**No reservation cleanup needed** — `BudgetGuard.check` does NOT reserve. It is a *pre-check gate*. The actual cost is recorded post-call by the existing `BaseAgentCallbackHandler` writing to `*_llm_call` table, which the MV `mv_daily_llm_cost_per_tenant_v2` aggregates. **Reservation = optimistic** (no row written); deduction = post-call via observability path. This matches PR-2 §7 design ("BudgetGuard.check returns BudgetDecision; the actual cost is recorded post-call and re-aggregated by the MV").

### 4.5 Wiring entry points (3 modules)

**Sales_agent**: `application/orchestrator/conversation_pipeline.py::ConversationPipeline.__init__` (or factory `factory.py`): replace `LLMFactory.get_service()` with `BudgetGuardingLLMService(inner=LLMFactory.get_service(), budget_guard=DI, tenant_id=ctx.tenant_id, agent_kind="sales_agent")`. Pass via DI to nodes (currently nodes call `LLMFactory.get_service()` directly — refactor to receive `llm_service` from `state["_llm_service"]` injected at pipeline init).

**Copilot**: `modules/copilot/infrastructure/llm/provider_factory.py::build_chat_model(...)` returns `BudgetGuardingChatModel(inner=base_chat_model, budget_guard=DI, tenant_id=DI, agent_kind="copilot", model_hint=spec.model)`. Single point — every callsite (`llm_classifier.py`, `intent_classifier.py`, `synthesizer.py`, `url_inspiration_analyzer.py`, `judge.py`, deep_agent graph nodes via LangGraph) consumes via factory, so wrapper applies transparently.

**Brand**: `modules/brand/workers/tasks.py` + `modules/brand/application/services/personality_service.py` + `modules/brand/application/voice_fidelity/grader.py` + `modules/brand/application/agents/style_analyzer/nodes.py`: replace `LLMFactory.get_service()` calls with helper `_get_guarded_llm_service(tenant_id, agent_kind="brand")` from `shared/billing/application/llm_guards.py`. The helper wraps once.

### 4.6 DI strategy

`BudgetGuard` instance + `tenant_id` injected via:
- **Sales_agent**: `ConversationPipeline.__init__(... budget_guard=Depends(get_budget_guard) ...)`. tenant_id from `agent_state.tenant_id`.
- **Copilot**: `build_copilot_dependencies()` factory returns `CopilotDeps` dataclass; new field `budget_guard: BudgetGuard`. tenant_id from `request.state.tenant_id` (X-Tenant-ID middleware).
- **Brand workers**: `arq_context["budget_guard"]` injected at worker startup. tenant_id from job payload.

Constructor function `get_budget_guard()` (NEW, `shared/billing/dependencies.py`):

```python
async def get_budget_guard(
    plan_service: PlanService = Depends(get_plan_service),
    cost_reader: Any = Depends(get_cost_reader),
    mv_log: MVRefreshLogRepository = Depends(get_mv_log_repo),
) -> BudgetGuard:
    return BudgetGuard(
        plan_service=plan_service,
        cost_reader=cost_reader,
        mv_refresh_log_repo=mv_log,
    )
```

## 5. Cost estimation algorithm

### 5.1 Function

```python
# shared/billing/application/cost_estimator.py (NEW)
from __future__ import annotations
from decimal import Decimal
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# Conservative fallback (1000 clientes safety): unknown model → assume worst-case
# tier (premium $.0050 / 1k input + $.0150 / 1k output ≈ Claude Opus / GPT-4 Turbo).
# Tuned to over-estimate by ~30% vs typical model — over-estimate forces gate
# slightly earlier when pricing snapshot missing. Better to fail-closed on
# budget than fail-open and runaway.
_FALLBACK_INPUT_RATE = Decimal("0.000005")
_FALLBACK_OUTPUT_RATE = Decimal("0.000015")
_TOKENS_PER_CHAR = Decimal("0.25")  # ~4 chars/token Spanish (LATAM neutro)


def estimate_llm_cost(
    *,
    prompt: str,
    max_output_tokens: int,
    model: str | None,
    agent_kind: str,
    pricing_accessor: Any | None = None,  # injected; falls back to module-level
) -> Decimal:
    """Estimate USD cost BEFORE the LLM call for BudgetGuard.check.

    Algorithm:
    1. estimated_input_tokens = ceil(len(prompt) * _TOKENS_PER_CHAR)
    2. Resolve pricing snapshot via async accessor (§5.2). If sync caller,
       use cached_pricing_lookup(model) — the resolver caches per-process
       LRU 256 keys; misses fall to module-level fallback rates.
    3. cost = (input_tokens * input_cost_per_token) +
              (max_output_tokens * output_cost_per_token)
    4. Tier pricing (Kimi K2.6 / future): if model declares
       `input_cost_per_token_above_200k_tokens` AND estimated_input >
       TIER_THRESHOLD (200k), split via `_split_at_tier()` (re-uses
       calculator.py logic). For agent_kind != "sales_agent" tier rare
       (copilot prompts <100k typical), cheap to compute regardless.
    5. Apply 1.10x safety multiplier (budget cushion vs estimation drift)
       — cap drift documented in PR-2 Q9 acceptance ("estimate within
       ±15% of post-call actual"). 1.10x absorbs +10% drift toward
       under-estimate; if drift exceeds 15% in prod, alert via
       `cost_estimate_drift_alert` (S2 worker).
    6. Return Decimal(2 places).

    Idempotency: pure function. Same inputs → same output. No side
    effects.
    """
    estimated_input_tokens = max(int(Decimal(len(prompt)) * _TOKENS_PER_CHAR), 1)

    pricing = _resolve_pricing(model, pricing_accessor)
    if pricing is None:
        input_rate = _FALLBACK_INPUT_RATE
        output_rate = _FALLBACK_OUTPUT_RATE
        logger.info(
            "cost_estimate_fallback_used",
            model=model,
            agent_kind=agent_kind,
        )
    else:
        input_rate = pricing.input_cost_per_token
        output_rate = pricing.output_cost_per_token

    # Tier handling — reuses calculator's _split_at_tier semantics.
    from src.shared.agent_observability.cost.calculator import _split_at_tier, _resolve_tier_rate, _INPUT_TIER_KEY, _OUTPUT_TIER_KEY
    input_tier = _resolve_tier_rate(pricing, _INPUT_TIER_KEY) if pricing else None
    output_tier = _resolve_tier_rate(pricing, _OUTPUT_TIER_KEY) if pricing else None

    input_cost = _split_at_tier(estimated_input_tokens, input_rate, input_tier)
    output_cost = _split_at_tier(max_output_tokens, output_rate, output_tier)

    raw = input_cost + output_cost
    safety = (raw * Decimal("1.10")).quantize(Decimal("0.01"))
    return safety
```

### 5.2 Pricing snapshot async access — minimal design

**Problem:** `PricingSnapshotRepository.find_active(provider, model)` is **sync** (binds to `Session`). `BudgetGuard.check` is **async** (called from copilot's async LangGraph + sales_agent ARQ workers). Calling sync DB query from async context = blocking event loop = anti-pattern at 1000 clientes (degrades p99 latency).

**Decision (D-NEW-1):** **Builder agrega minimal `PricingSnapshotRepoAsync`** in `shared/billing/infrastructure/pricing_snapshot_repo_async.py`. Mirror of sync repo's `find_active` + `find_at`, bound to `AsyncSession`. Sync repo stays as-is for ARQ pricing sync workers.

**Rationale (1000 clientes):** wrapping sync repo in `asyncio.to_thread()` is tempting but creates thread pool pressure under load (1 thread per concurrent LLM call gating = up to N concurrent threads at peak). Native async query = zero overhead.

**Alternative considered:**
- Reuse sync via `asyncio.to_thread` — rejected (thread pool exhaustion at scale).
- Cache pricing in-process LRU + bypass DB for hot path — accepted as **layer above** async repo (`pricing_resolver.py` adds `@lru_cache(maxsize=256)` keyed on `(provider, model)`, TTL=300s via `cachetools.TTLCache`). LRU + TTL = avoid stale pricing post-LiteLLM-sync.

**Minimal async repo signature** (architect documents — builder implements):

```python
# shared/billing/infrastructure/pricing_snapshot_repo_async.py (NEW)
from __future__ import annotations
import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import or_, select

from src.shared.agent_observability.persistence.models.pricing_snapshot_model import (
    ModelPricingSnapshotModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class PricingSnapshotRepoAsync:
    """Cross-tenant by design (reference data). Mirrors sync repo find_active + find_at."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_active(
        self,
        *,
        provider: str,
        model: str,
    ) -> ModelPricingSnapshotModel | None:
        stmt = select(ModelPricingSnapshotModel).where(
            ModelPricingSnapshotModel.provider == provider,
            ModelPricingSnapshotModel.model == model,
            ModelPricingSnapshotModel.valid_to.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

**Cache layer** (`shared/billing/application/pricing_cache.py`, NEW):

```python
from cachetools import TTLCache
from threading import Lock

_cache: TTLCache[tuple[str, str], ModelPricingSnapshotModel | None] = TTLCache(maxsize=256, ttl=300)
_cache_lock = Lock()

async def resolve_pricing_cached(
    repo: PricingSnapshotRepoAsync,
    provider: str,
    model: str,
) -> ModelPricingSnapshotModel | None:
    key = (provider, model)
    with _cache_lock:
        if key in _cache:
            return _cache[key]
    snapshot = await repo.find_active(provider=provider, model=model)
    with _cache_lock:
        _cache[key] = snapshot
    return snapshot
```

`estimate_llm_cost` consumes via DI accessor `pricing_accessor` (avoids hardcoded import → testable + module boundary clean).

### 5.3 Provider/model resolution

`agent_kind` → typical model mapping (used as fallback hint when caller doesn't pass `model`):

| agent_kind | typical provider | typical model | source |
|---|---|---|---|
| `sales_agent` | `deepseek` | `deepseek-v4-flash` | `LLM_ROLE_BY_SITE` SSoT (sales_agent skill) |
| `copilot` | `openai` | `gpt-5-mini` | copilot `CHAT_MODEL_SPEC` |
| `brand` | `openai` | `gpt-5-mini` | brand `LLMFactory` default |

Builder: implementar `resolve_provider_model_hint(agent_kind: str) -> tuple[str, str]` en `cost_estimator.py` consultando los SSoTs de cada módulo via shared/links port (NO cross-module direct import).

## 6. Cutover order matrix — 8 commits secuenciales

| # | Commit type | Scope | Smoke gate | Rollback |
|---|---|---|---|---|
| 1 | `feat(billing)` | NEW: `BudgetGuardingLLMService` + `BudgetGuardingChatModel` + `cost_estimator` + `PricingSnapshotRepoAsync` + `pricing_cache` + `BudgetExceeded` exception. 0 callsites wired yet. | unit tests verde (RED→GREEN per file). | `git revert <hash>` — 0 user-facing impact. |
| 2 | `feat(billing)` | NEW arch test `test_budget_guard_pre_llm_call.py` con allowlist=ALL existing LLM callsites (so test passes immediately). NEW arch test `test_no_legacy_event_bus_publish.py` con allowlist=ALL existing legacy direct imports. | arch tests verde. | revert. |
| 3 | `feat(sales_agent)` | Wire `BudgetGuardingLLMService` en `ConversationPipeline.__init__` + DI a nodes. Refactor `agents/sales/nodes.py` 4 callsites a recibir `llm_service` desde state injected. + same for `quality/judge.py` + `safety_service.py` + `follow_up_engine.py` + `appointment_reminder_engine.py`. Shrink allowlist en `test_budget_guard_pre_llm_call.py` (sales_agent paths removed from list). | `test_outbox_invariants.py` + `test_budget_reservation_invariant.py` + nuevo `test_budget_guard_wiring_sales_agent.py` integration F-7 verde. Smoke manual: 1 conv telegram dev tenant exhausted budget → `BudgetExceeded` raised → log structlog. | revert single commit. |
| 4 | `feat(sales_agent)` | `core/config.py` flip `USE_OUTBOX_PATTERN_SALES_AGENT: bool = False → True`. **Single line change**. | `test_outbox_cutover_sales_agent.py` integration F-7 verde (event emitter → row in `domain_event_outbox` → dispatcher pickup → handler invocado). + 13 gates `/test-backend` verde. + smoke manual: 1 conv inbound telegram dev tenant → ver row in outbox table. | revert single line. |
| 5 | `feat(copilot)` | Wire `BudgetGuardingChatModel` en `provider_factory.build_chat_model(...)` — single point. tenant_id propagated via copilot `build_copilot_dependencies()`. Shrink allowlist arch test. | `test_copilot_anchors.py` + nuevo `test_budget_guard_wiring_copilot.py` integration F-7 verde. Smoke: 1 turn copilot dev tenant exhausted budget → 402 + plan_card stub (PI-2 implementa render). | revert. |
| 6 | `feat(copilot)` | `core/config.py` flip `USE_OUTBOX_PATTERN_COPILOT: bool = False → True`. | `test_outbox_cutover_copilot.py` F-7 verde + 13 gates verde + smoke: 1 turn copilot → row in outbox. | revert single line. |
| 7 | `feat(brand)` | Wire `_get_guarded_llm_service` helper en brand `workers/tasks.py` + `services/personality_service.py` + `voice_fidelity/grader.py` + `agents/style_analyzer/nodes.py`. Shrink allowlist. **Drop dead import** `_LegacyEventBus` en `copilot/observability/recording/domain_subscribers.py:120`. | `test_budget_guard_wiring_brand.py` F-7 verde + ARQ worker smoke: 1 extraction job dev tenant exhausted → job marked `skipped_budget_exhausted`. | revert. |
| 8 | `feat(brand)` | `core/config.py` flip `USE_OUTBOX_PATTERN_BRAND: bool = False → True`. | `test_outbox_cutover_brand.py` F-7 verde + 13 gates verde + smoke: 1 brand extraction worker run → row in outbox. + IMPL-LOG.md actualizado con flag deltas + decisiones D26-D28 outcomes. | revert single line. |

**Rationale orden** (D26 confirmado):
- Sales_agent **primero** (commits 3-4): blast radius mayor (revenue), maduro, smoke rápido. Si rompe → diagnostic temprano evita arrastrar a copilot/brand.
- Copilot **segundo** (commits 5-6): alta superficie LLM. Tras sales_agent estable.
- Brand **último** (commits 7-8): blast radius menor (extraction async, no real-time).

**Total: 8 commits + 1 IMPL-LOG = 9 commits**. PR.md acceptance dice `~6 commits` — architect ajusta a 8 + 1 IMPL-LOG porque cada wiring + flag flip son commits separados (atomic rollback).

## 7. Decisiones D26-D28 confirmadas

### D26 — Cutover order: secuencial sales_agent → copilot → brand
**CONFIRMADO** sin drift. PR.md plan match con architect findings.

### D27 — BudgetGuard estimation strategy
**CONFIRMADO** opción A (`model_pricing_snapshot` + tokens estimated) **+ extensión wrapper pattern** (§4.1) para evitar parchar 14 callsites individuales. Drift flagged: PR.md describía "wire ANTES cada LLM call site" (parche per-callsite). Architect propone **wrapper en factory** = 3 wiring points (1 per módulo) en lugar de 14. Más mantenible y future-proof. PM debe aprobar.

### D28 — Legacy emisores retire policy
**DRIFT FLAGGED**. PR.md describe "20 emisores legacy `event_bus.publish_in_memory`". Realidad post-grep:
- 0 callsites usan literal `event_bus.publish_in_memory` (string no existe en codebase).
- 22 callsites usan `EventBus.publish(event, session=...)` donde `EventBus` ya es alias del `EventBusAdapter` (PR-1 path unificado).
- Cutover real = flip de los 3 flags. Adapter switchea path automáticamente (Q4 PM matrix).
- **Única deuda real**: 1 import vestigial `_LegacyEventBus` dead code en `copilot/observability/recording/domain_subscribers.py:120` (drop in commit 7).

PM debe re-confirmar D28: scope = "drop dead code import + verify 22 callsites pasan `session=` correcto post-flip" (no "replace 20 callsites"). 4 callsites pasan `session=None` intencionalmente (broadcast cache invalidation): `personality_service.py:122`, posible en `extract_from_doc.py`, `chat.py`, `suggestions.py`. Builder verifica que cada `session=None` está justificado en code comment; si transacción disponible, pasa session real.

## 8. Test strategy detallado — política F-7 (sin mocks de service)

### 8.1 Layer A — Per-module integration F-7

Política F-7 (PR-4 REVIEW): integration tests integran service real, sin mocks de service layer. Mocks solo en *infrastructure boundary* (HTTP clients, LLM providers para no quemar tokens).

**Fixtures comunes** (`backend/tests/conftest.py` o `tests/modules/{m}/conftest.py`):

```python
@pytest.fixture
async def real_budget_guard(async_db: AsyncSession) -> BudgetGuard:
    """Real BudgetGuard with real PlanService + real cost_reader stubbed
    at ONE level: the SQL query for cycle spend (mocked because MV may
    not be populated in test DB). Plan resolution + decision logic = real.
    """
    plan_service = PlanService(async_db)
    cost_reader = StubCostReader(spent_usd=Decimal("0.00"))  # parametrized per test
    mv_log = MVRefreshLogRepository(async_db)
    return BudgetGuard(plan_service, cost_reader, mv_log)


@pytest.fixture
async def exhausted_budget_guard(async_db: AsyncSession, real_plan: PlanConfig) -> BudgetGuard:
    """Tenant with cycle spend > cap_usd → BudgetGuard.check returns allowed=False."""
    plan_service = PlanService(async_db)
    cost_reader = StubCostReader(spent_usd=real_plan.others_pool_usd + Decimal("1.00"))
    mv_log = MVRefreshLogRepository(async_db)
    return BudgetGuard(plan_service, cost_reader, mv_log)


@pytest.fixture
def llm_provider_stub() -> Any:
    """Mocks BOUNDARY (LLM HTTP) only. Returns canned response with
    usage_metadata that BaseAgentCallbackHandler can parse. NEVER hits
    real LLM provider in tests (no token burn).
    """
    return InMemoryLLMStub(canned_response="ok", input_tokens=100, output_tokens=50)
```

### 8.2 Tests integration listing

**`tests/modules/sales_agent/integration/test_budget_guard_wiring.py` (NEW)**

Cases (RED → GREEN):
- `test_sales_agent_llm_call_passes_through_when_budget_available` — exhausted_budget_guard=NO, llm_provider_stub returns canned. ConversationPipeline.process_inbound completes turn. `BudgetGuard.check` invocada 1x con `agent_kind="sales_agent"`.
- `test_sales_agent_llm_call_raises_budget_exceeded_when_exhausted` — exhausted_budget_guard=YES (SA pool exhausted). `BudgetExceeded` raised. OutputManager NOT called (no message sent to lead). Outbox event `budget_exceeded` emitted (assert row in `domain_event_outbox`).
- `test_sales_agent_does_not_consume_others_pool` — exhausted Others pool, SA pool intact. `BudgetGuard.check` returns `allowed=True` (consumes SA pool only). Reservation invariant guard.
- `test_sales_agent_soft_warn_logs_structlog` — pool at 85%. `decision.soft_warn=True`. structlog `budget_soft_warn` emitted (assert via caplog).

**`tests/modules/sales_agent/integration/test_outbox_cutover.py` (NEW)**

Cases (with `USE_OUTBOX_PATTERN_SALES_AGENT=True` via monkeypatch):
- `test_payment_received_event_persists_to_outbox` — payment webhook publishes `PaymentReceivedEvent`. Assert row in `domain_event_outbox` with `module="sales_agent"`. Assert dispatcher worker (mocked dispatcher poll) picks up + invokes subscriber.
- `test_appointment_event_idempotency_via_natural_key` — emit same event 2x with same `idempotency_key`. Assert exactly 1 row.
- `test_event_lost_when_pod_crash_simulated` — emit event inside session, session.rollback() simulates crash. Assert row NOT in outbox (rolled back too — atomic with caller transaction). NEW emit + commit → row persists.

**`tests/modules/copilot/integration/test_budget_guard_wiring.py` (NEW)** — análogo a sales_agent, agent_kind=`copilot`. Specific case:
- `test_copilot_402_returned_when_budget_exhausted` — copilot HTTP route `POST /api/v1/copilot/chat` con tenant Others pool exhausted → response.status_code == 402, body `{"detail": "budget_exhausted", "decision_id": "...", "pool": "others", "reason": "cycle_budget_exhausted"}`.
- `test_copilot_does_not_consume_sa_pool` — exhausted SA pool, Others pool intact. Copilot turn completes normalmente.

**`tests/modules/copilot/integration/test_outbox_cutover.py` (NEW)** — emit `CardEmittedEvent` + `RoutingDecidedEvent` + `ExtractionSectionCompletedEvent`. Assert outbox rows + dispatcher pickup.

**`tests/modules/brand/integration/test_budget_guard_wiring.py` (NEW)** — agent_kind=`brand`. Case:
- `test_brand_extraction_job_skipped_when_budget_exhausted` — ARQ job `arq_extract_brand_settings` runs with exhausted Others pool → job result `status="skipped_budget_exhausted"`, no LLM call made, brand_settings NOT updated.

**`tests/modules/brand/integration/test_outbox_cutover.py` (NEW)** — emit `BrandSectionUpdatedEvent` + `PersonalityProfileUpdatedEvent`. Assert outbox rows.

### 8.3 Layer B — Architecture gates (§9 detail)

Already covered. AST-based.

### 8.4 Coverage gates

- 13 gates `/test-backend` verde (existing).
- 4 NEW arch tests verde (BudgetGuard pre-LLM + No legacy direct EventBus + ratchet shrink-only).
- 8 NEW integration tests verde (Layer A).
- Pytest `--cov-fail-under=43` mantenido.

## 9. Architectural fitness gates — AST scan exact logic

### 9.1 `tests/architecture/test_budget_guard_pre_llm_call.py` (NEW)

**Goal:** every direct LLM invocation site in `modules/{sales_agent,copilot,brand}/` is **either** wrapped by `BudgetGuardingLLMService` / `BudgetGuardingChatModel` **or** in the explicit allowlist (e.g. tests, prompt cache warmup).

**AST scan logic:**

```python
import ast
from pathlib import Path

# Patterns considered "direct LLM call"
DIRECT_LLM_CALL_PATTERNS = {
    # (module_attr_path, attr_name) tuples
    ("LLMFactory", "get_service"),  # followed by .generate_response chain
    ("client", "chat"),               # client.chat.completions.create
    ("llm", "invoke"),                # llm.invoke(messages)
    ("llm", "ainvoke"),
    ("model", "ainvoke"),
}

# Allowlist: paths where direct LLM call is intentional and pre-wrapped upstream.
# Shrink-only: removing entries OK; adding requires PR justification in commit msg.
ALLOWED_DIRECT_LLM_CALL_FILES: frozenset[str] = frozenset({
    "src/shared/billing/application/llm_guards.py",  # the wrapper itself
    "src/shared/infrastructure/llm/factory.py",       # factory itself
    "src/shared/infrastructure/llm/router.py",        # router
    "src/shared/infrastructure/llm/providers/",        # provider impls (prefix match)
    "src/modules/copilot/infrastructure/llm/",         # copilot provider factory + classes
    "src/modules/sales_agent/observability/",          # callback handler internals
    # Test files always allowed
    "tests/",
})

def _is_allowed(file_path: str) -> bool:
    return any(file_path.startswith(p) or p in file_path for p in ALLOWED_DIRECT_LLM_CALL_FILES)


class LLMCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[str, int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Detect chains like LLMFactory.get_service().generate_response(...)
        # or client.chat.completions.create(...) or llm.invoke(...)
        chain = self._resolve_chain(node.func)
        if self._matches_direct_llm(chain):
            self.violations.append((self._chain_str(chain), node.lineno, ""))
        self.generic_visit(node)


def test_no_unwrapped_llm_calls_in_consumer_modules() -> None:
    """Every direct LLM call in consumer modules MUST be inside an allowed file."""
    consumer_paths = [
        "backend/src/modules/sales_agent/",
        "backend/src/modules/copilot/",
        "backend/src/modules/brand/",
    ]
    violations: list[str] = []
    for root in consumer_paths:
        for py_file in Path(root).rglob("*.py"):
            rel = str(py_file.relative_to("backend/"))
            if _is_allowed(rel):
                continue
            tree = ast.parse(py_file.read_text())
            visitor = LLMCallVisitor()
            visitor.visit(tree)
            for chain, lineno, _ in visitor.violations:
                violations.append(f"{rel}:{lineno} unwrapped LLM call: {chain}")
    assert not violations, "\n".join(violations)
```

**Allowlist starts large** (commit 2 — all current callsites included) y **shrinks** en commits 3, 5, 7 cuando builder migra cada módulo. Test arch fitness ratchet: `len(ALLOWED_DIRECT_LLM_CALL_FILES) <= LAST_KNOWN_COUNT` enforced via separate `test_allowlist_only_shrinks.py` (existing pattern from `architectural-fitness.md`).

### 9.2 `tests/architecture/test_no_legacy_event_bus_publish.py` (NEW)

**Goal:** zero `from src.shared.domain.events import EventBus` direct import in consumer modules. The unified path is `from src.shared.domain_events.outbox.application.event_bus_adapter import adapter_bus as EventBus`.

```python
import ast
from pathlib import Path

LEGACY_IMPORT_FROM = "src.shared.domain.events"
LEGACY_IMPORT_NAME = "EventBus"

# Files allowed to import the legacy class (e.g. the adapter itself, the legacy class definition file, tests).
ALLOWED_LEGACY_IMPORT_FILES: frozenset[str] = frozenset({
    "src/shared/domain/events.py",                                                    # definition
    "src/shared/domain_events/outbox/application/event_bus_adapter.py",                # adapter delegates
    "tests/",
    "src/shared/domain_events/legacy/",  # any future migration shim
})


class LegacyImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == LEGACY_IMPORT_FROM:
            for alias in node.names:
                if alias.name == LEGACY_IMPORT_NAME:
                    self.violations.append((node.lineno, alias.name))
        self.generic_visit(node)


def test_no_direct_legacy_event_bus_import_in_consumers() -> None:
    consumer_paths = [
        "backend/src/modules/sales_agent/",
        "backend/src/modules/copilot/",
        "backend/src/modules/brand/",
    ]
    violations: list[str] = []
    for root in consumer_paths:
        for py_file in Path(root).rglob("*.py"):
            rel = str(py_file.relative_to("backend/"))
            if any(p in rel for p in ALLOWED_LEGACY_IMPORT_FILES):
                continue
            tree = ast.parse(py_file.read_text())
            visitor = LegacyImportVisitor()
            visitor.visit(tree)
            for lineno, name in visitor.violations:
                violations.append(f"{rel}:{lineno} legacy import: {name}")
    assert not violations, "\n".join(violations)
```

**Allowlist:** at commit 2, includes `copilot/observability/recording/domain_subscribers.py` (line 120 dead code). Removed in commit 7. Allowlist shrink-only post-commit-7.

### 9.3 Existing gates that must keep passing

- `test_outbox_invariants.py` — events emit via `OutboxService` API contract (callbacks, idempotency).
- `test_budget_reservation_invariant.py` (PR-2) — property-based test that SA pool exhaust doesn't allow Others consumption and vice versa. PR-6 must NOT break.
- `test_compliance_used_by_channels.py` (PR-2) — TelegramChannelRouter consumes ComplianceService.
- `test_no_hardcoded_plan_prices.py` (PR-2) — no `'USD'` literals outside seed migration.
- `test_ddd_boundaries.py` (universal) — no cross-module imports except `shared/links/`.
- `test_copilot_anchors.py` (universal) — anchor budget 36/36.

## 10. Open questions for PM

**IDEAL: vacía.** Architect resolve internamente cuando es decisión técnica. Items abajo son **decisiones de scope/producto** que requieren PM:

1. **D27 extension — wrapper pattern (§4.1)** vs per-callsite parche literal (PR.md description). Architect recomienda wrapper. **Confirmar PM antes de commit 1.** Si PM rechaza wrapper → architect re-arquitectura a 14 callsites parche individual + arch test gate per-callsite (más deuda, peor mantenibilidad pero más visible). Default architect: **wrapper**.

2. **D28 drift — scope retire legacy (§7)**. PR.md "retire 20 emisores" interpretación: builder agrega allowlist al arch test con 22 callsites enumerados (todos pasan post-cutover), drop 1 dead import, verify cada `session=None` justificado. **Confirmar PM antes de commit 2** que este scope satisface el "retire legacy" del PR.md. Si PM quiere re-implementar 22 callsites a `OutboxService.enqueue` directo (bypass adapter) → CONTRACT requiere extensión, +12h trabajo, no recomendado (adapter es API estable).

3. **Brand BudgetGuard wiring scope** — PR.md dice "brand NO tiene LLM call directo (extraction usa shared LLM service que ya wired post-PR-6 copilot/sales_agent)". Architect verifica vía grep: brand SÍ tiene 7 callsites directos `LLMFactory.get_service().generate_response(...)` en `personality_service.py`, `voice_fidelity/grader.py`, `style_analyzer/nodes.py`. **Confirmar PM**: incluir wiring brand BudgetGuard (commits 7-8 incluyen) o diferir a PI-2 (drop brand wiring this PR). Default architect: **incluir** (cero deuda, brand budget runaway 1000 clientes posible si extracción masiva).

(Si PM responde rápido los 3 → CONTRACT cerrado. Si PM defiere → builder hace asumption explícita en IMPL-LOG.md.)

---

<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-6 architect done" para review. -->
