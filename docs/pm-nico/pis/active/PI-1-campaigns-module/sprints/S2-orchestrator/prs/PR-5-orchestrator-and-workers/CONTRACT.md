# CONTRACT — PR-5-orchestrator-and-workers

> Owner: `nicolify-architect`. SSoT pre-implementación.
> Status: **READY for builder**. Zero open questions (decisiones D15-D22 cementadas con framing 1000 clientes — todas confirmadas tras auditar schema vivo PR-3+PR-4).
> Sesión: 2026-04-30 — architect post-S1 SHIPPED. Skills consultados: `backend-expert` (DDD inside-out + master-data + arch-fitness), `tessl__graceful-degradation` (timeouts 5-10s, circuit breaker per-dependency, retry exponencial backoff con jitter, fallback obligatorio), `tessl__pytest-api-testing` (ARQ ctx fixture pattern, httpx mock, transaction rollback per-test).
>
> Reglas duras: `tenant-isolation.md`, `backend-ddd.md`, `backend-migrations.md`, `architectural-fitness.md`, `master-data.md`, `data-reliability.md`, `tdd-mandatory.md`, `pii-sanitisation.md` (Tessl), `parallel-safety.md` regla M8 (extend `workers/settings.py`, no destroy).

---

## 0. Context summary

| Campo | Valor |
|---|---|
| PR ID | PR-5-orchestrator-and-workers |
| PI / Sprint | PI-1-campaigns-module / S2-orchestrator |
| Modules tocados (write) | `modules/campaigns/{application,infrastructure,workers,api}/` (extend), `alembic/versions/113_campaigns_audit_log.py` (NEW), `backend/src/workers/settings.py` (MOD: append fns + crons), `tests/modules/campaigns/{application,infrastructure,workers,integration,api}/` (NEW + MOD), `tests/architecture/test_campaigns_*.py` (4 NEW) |
| Modules tocados (read-only) | PR-3 domain (`Campaign`, `CampaignStep`, `CampaignTask`, `Segment`, `SegmentFilter`, `ChannelRouter` Protocol), PR-3 infra (repos + models), PR-4 services (`CampaignService.launch` MOD), S0 shared (`OutboxService`, `@idempotent` + `RedisIdempotencyStore`, `PlanService`, `BudgetGuard`, `OutboundRateLimiter`, `ComplianceService`, `sanitize_payload`), `core.database.{redis_client, SessionLocal}`, `iam/api/dependencies.py` (no change) |
| Skills consulted | `backend-expert` (DDD ports + Pydantic v2 + arch-fitness ratchet shrink-only), `tessl__graceful-degradation` (CB iron-rule: every external call gets timeout + fallback; per-dependency isolation), `tessl__pytest-api-testing` (ARQ ctx fixture, httpx mock pattern, transaction rollback) |
| pm-nico/current-state files post-merge | `current-state/campaigns.md` — sección "S2 SHIPPED" con capability "orchestrator real + 4 ARQ workers + ChannelRouter Telegram + circuit breaker per (channel, tenant_id) + audit log retention 90d", lineage commits PR-5, removed STUB note de `launch()` |
| Architecture gates verde | PR-3 (4 frozen) + PR-4 (4 frozen) + global (`test_ddd_boundaries.py` 22 frozen, `test_outbox_invariants.py`, `test_master_data_compliance.py`, `test_currency_consistency.py`, `test_no_new_copilot_module_imports.py`, `test_api_contracts.py` con `redirect_slashes=False`, `test_folder_naming.py`, `test_domain_purity.py`) |
| Architecture gates **nuevos** (4) | `test_campaigns_orchestrator_idempotent.py`, `test_campaigns_workers_registered.py`, `test_channel_router_registry_invariants.py`, `test_campaigns_audit_log_retention.py` |

**Riesgo principal:** primer pipeline outbound real con external API hit (Telegram). Mitigación: timeouts duros + per-(channel,tenant_id) circuit breaker Redis-backed + per-tenant rate limiter + per-task idempotency (S0.2) + cross-task idempotency (`UNIQUE(tenant_id, idempotency_key)` heredado PR-3) + audit log dedicado con retention 90d.

**Out of scope CONTRACT (cementados PR.md):**
- WhatsApp/Email/IG DM ChannelRouter impls → PI-2
- sales_agent OutboundOrchestrator wiring → S3
- Inbound reply recognition → S3
- BudgetGuard wiring (LLM call sites copilot/sales_agent) → PR-6 (PR-5 NO invoca LLM)
- FE → post PI-1
- Real Telegram API hitting (mock httpx en tests; dev-app smoke con bot test)
- DLQ infra dedicada (status=`failed` + audit row alcanza día 1)
- Per-tenant ARQ pool isolation (queue named global alcanza)

---

## 1. Module surface (DDD inside-out + paths exactos)

### 1.1 NEW files (PR-5)

```
backend/src/modules/campaigns/
├── application/
│   ├── services/
│   │   ├── orchestrator.py                     ← NEW CampaignOrchestrator
│   │   └── audit_log_service.py                ← NEW AuditLogService
│   └── dtos/
│       └── audit_log_dtos.py                   ← NEW AuditLogEntryDTO + dispatch result
├── infrastructure/
│   ├── channels/
│   │   ├── __init__.py                         ← NEW (re-export registry + Telegram)
│   │   ├── registry.py                         ← NEW ChannelRouterRegistry singleton
│   │   ├── telegram.py                         ← NEW TelegramChannelRouter
│   │   ├── shared.py                           ← NEW dispatch helpers (locale fmt, retry/backoff)
│   │   └── errors.py                           ← NEW channel-error hierarchy (Retryable/Fatal/RateLimited)
│   ├── resilience/
│   │   ├── __init__.py                         ← NEW (re-export CircuitBreaker)
│   │   ├── circuit_breaker.py                  ← NEW asyncio Redis-backed CB
│   │   └── errors.py                           ← NEW CircuitBreakerOpenError
│   ├── models/
│   │   └── campaign_audit_model.py             ← NEW SQLA campaign_audit
│   └── repositories/
│       └── audit_log_repo_impl.py              ← NEW SQLA repo impl
├── domain/
│   └── audit_log.py                            ← NEW AuditLogEvent (domain VO + enum) + AuditLogRepository ABC
└── workers/
    ├── __init__.py                             ← NEW
    ├── execution_task.py                       ← NEW run_campaign_execution_task
    ├── scheduler_tick.py                       ← NEW run_campaign_scheduler_tick
    ├── segment_refresh_tick.py                 ← NEW run_segment_refresh_tick
    └── audit_retention_task.py                 ← NEW purge_old_campaigns_audit

backend/alembic/versions/
└── 113_campaigns_audit_log.py                  ← NEW (raw SQL idempotente)

backend/src/workers/settings.py                  ← MOD: append 4 fns + 3 crons (regla M8 extend)
```

### 1.2 MOD files (PR-5)

```
backend/src/modules/campaigns/
├── application/services/campaign_service.py    ← MOD launch() llama orchestrator (PR-4 stub → real)
├── api/_service_factories.py                   ← MOD agregar get_campaign_orchestrator + get_audit_log_service
└── api/routers/campaigns_router.py             ← MOD launch endpoint sigue mismo response_model; comportamiento real
```

### 1.3 Layer ownership + import policy

| Layer | Owns | Allowed imports |
|---|---|---|
| `domain/audit_log.py` | AuditLogEvent VO + enum + AuditLogRepository ABC | stdlib + Pydantic + project enums (puro) |
| `domain/channel_router.py` (heredado PR-3) | `ChannelRouter` Protocol + `ChannelSendResult` VO | stdlib + Pydantic |
| `infrastructure/channels/*` | TelegramChannelRouter + Registry + dispatch helpers + errors | `domain/channel_router.py`, `application/services/audit_log_service.py` (DI), `shared/idempotency`, `shared/billing.rate_limiter`, `shared/compliance`, `infrastructure/resilience/circuit_breaker`, `httpx`, `structlog` |
| `infrastructure/resilience/*` | CircuitBreaker + errors | `core.database.redis_client`, `structlog`, stdlib (asyncio) |
| `infrastructure/repositories/audit_log_repo_impl.py` | SQLA writes/queries `campaign_audit` | `domain/audit_log.py`, `infrastructure/models/campaign_audit_model.py`, `shared/agent_observability/recording/sanitization.sanitize_payload` |
| `application/services/orchestrator.py` | `CampaignOrchestrator.launch()` | `domain/*`, `infrastructure/repositories/*` (via DI), `shared/idempotency.@idempotent`, `shared/domain_events/outbox/OutboxService`, `application/services/segment_service`, `application/services/audit_log_service`, ARQ pool (enqueue_job), `structlog` |
| `application/services/audit_log_service.py` | `AuditLogService.record(...)` (sanitize + persist) | `domain/audit_log.py`, `infrastructure/repositories/audit_log_repo_impl` (via DI), `shared/.../sanitize_payload` |
| `workers/*` | ARQ entry points | `application/services/*`, `infrastructure/channels/*`, `core.database.SessionLocal`, repos via factories, `shared/links/ports/crm_repos` (para resolve `lead.telegram_id`), `structlog` |

**Import forbidden (arch ratchet 22 frozen):**
- `campaigns/` → `copilot/` ❌
- `campaigns/` → `sales_agent/` ❌ (S3 wirea inverso vía port)
- `campaigns/` → `crm/` directo ❌ → use `shared/links/ports/crm_repos.py`
- `domain/` → `infrastructure/` o `application/` ❌
- `infrastructure/channels/telegram.py` → `application/services/orchestrator.py` ❌ (un solo sentido: orch consume canal vía `ChannelRouter` Protocol)

---

## 2. Domain interfaces / Protocols

### 2.1 `ChannelRouterRegistry` (`infrastructure/channels/registry.py`)

```python
from __future__ import annotations
from threading import Lock
from src.modules.campaigns.domain.channel_router import ChannelRouter

class ChannelRouterRegistry:
    """Singleton registry of channel implementations.

    Thread-safe per-process. Multi-pod: cada pod construye su propio registry
    en startup (`register_default_channels()`); estado in-memory es estable.
    Test fixture borra registry entre tests (autouse fixture en conftest.py).
    """

    _instance: "ChannelRouterRegistry | None" = None
    _lock = Lock()

    def __new__(cls) -> "ChannelRouterRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._routers = {}  # type: ignore[attr-defined]
        return cls._instance

    def register(self, channel: str, router: ChannelRouter) -> None:
        """Register router for channel slug. Replace silently if re-registered."""
        if not isinstance(router, ChannelRouter):
            raise TypeError(f"router for {channel!r} debe implementar ChannelRouter Protocol")
        self._routers[channel] = router

    def get(self, channel: str) -> ChannelRouter:
        """Return router for channel. Raises KeyError if unregistered."""
        try:
            return self._routers[channel]
        except KeyError as exc:
            raise KeyError(f"channel {channel!r} no registrado en ChannelRouterRegistry") from exc

    def has(self, channel: str) -> bool:
        return channel in self._routers

    def reset(self) -> None:
        """Test-only — clears registry. Production code MUST NOT call."""
        self._routers.clear()


def register_default_channels(*, telegram_token_provider) -> None:  # noqa: ANN001 — DI
    """Wired en `WorkerSettings.on_startup` y `main.py` startup hook.

    `telegram_token_provider` = async callable resolving (tenant_id) -> bot_token.
    Tenant tiene 1 bot Telegram propio (resolución vía connections module S3+).
    Para PR-5 dev-app: env `TELEGRAM_BOT_TOKEN` global fallback (test smoke).
    """
    from src.modules.campaigns.infrastructure.channels.telegram import TelegramChannelRouter
    registry = ChannelRouterRegistry()
    registry.register("telegram", TelegramChannelRouter(token_provider=telegram_token_provider))
```

**Razón 1000 clientes:** registry por proceso (no Redis-backed) porque (a) la membresía cambia solo en deploys (no runtime), (b) Redis lookup en hot-path = +5ms innecesario. Multi-pod safe porque cada pod hace mismo bootstrap. Alternativa rechazada: registry distribuida → complejidad sin beneficio.

### 2.2 `CircuitBreaker` interface (`infrastructure/resilience/circuit_breaker.py`)

```python
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Awaitable, Callable, TypeVar
from uuid import UUID

T = TypeVar("T")

class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig:
    """Tunable per-dependency. Defaults via env (CAMPAIGNS_CB_*)."""
    fail_threshold: int = 5         # CAMPAIGNS_CB_FAIL_THRESHOLD
    open_duration_seconds: int = 60 # CAMPAIGNS_CB_OPEN_DURATION_SECONDS
    half_open_probes: int = 1       # CAMPAIGNS_CB_HALF_OPEN_PROBES
    rolling_window_seconds: int = 60 # rolling failure count window

class CircuitBreaker:
    """Asyncio Redis-backed per-(channel, tenant_id) breaker.

    State machine spec (production-grade SoTA per tessl__graceful-degradation):
    - CLOSED: calls pass through. Failures increment counter (rolling 60s window).
      When counter >= fail_threshold → transition OPEN, set opened_at = now.
    - OPEN: calls FAIL FAST (raise CircuitBreakerOpenError). After open_duration_seconds
      from opened_at → transition HALF_OPEN, reset probes_in_flight = 0.
    - HALF_OPEN: allow up to half_open_probes concurrent calls. While probing:
        * probe success → CLOSED, reset failure counter.
        * probe failure → back to OPEN, reset opened_at = now.
        * Any further call beyond probe quota while still HALF_OPEN → fail fast.

    Atomicity: all transitions use Redis Lua script `cb:transition` para evitar
    race entre pods (Lua = single execution context Redis side).

    Per-(channel, tenant_id) isolation: un Telegram fail tenant-A no afecta tenant-B.
    Razón 1000 clientes: tenant noisy neighbor no degrada todo el pool.
    """

    def __init__(
        self,
        *,
        channel: str,
        tenant_id: UUID,
        redis_client: Any,
        config: CircuitBreakerConfig,
    ) -> None: ...

    async def call(self, fn: Callable[..., Awaitable[T]], /, *args, **kwargs) -> T:
        """Execute fn under CB protection.

        Raises:
        - CircuitBreakerOpenError: state==OPEN o HALF_OPEN sin slot probe disponible.
        - cualquier excepción levantada por fn (tras registrar fail).
        """

    @property
    async def state(self) -> CircuitState:
        """Read current state (from Redis). Best-effort: fail → assume CLOSED."""

    async def force_open(self) -> None:
        """Test-only / ops escape hatch — manualmente abrir el breaker."""

    async def reset(self) -> None:
        """Test-only — clear all CB state for this (channel, tenant_id)."""
```

**Redis keys schema (multi-pod safe):**

| Key | Type | TTL | Purpose |
|---|---|---|---|
| `cb:campaigns:{channel}:{tenant_id}:state` | STRING (`closed`/`open`/`half_open`) | 0 (manual) | Current state |
| `cb:campaigns:{channel}:{tenant_id}:failures` | sorted set (timestamp:uuid score=ts) | rolling_window_seconds + 5s | Rolling failure events |
| `cb:campaigns:{channel}:{tenant_id}:opened_at` | STRING (epoch float) | 0 | When state→OPEN transition (drives HALF_OPEN time) |
| `cb:campaigns:{channel}:{tenant_id}:probes_in_flight` | counter (INT) | open_duration_seconds * 2 | Concurrent probes during HALF_OPEN |

**Lua script `cb:transition` (atomic state change):**
```
KEYS = [state_key, opened_at_key, probes_key, failures_key]
ARGV = [now_epoch, fail_threshold, open_duration_seconds, rolling_window_seconds, half_open_probes, action]
return new_state, allowed (1|0)
```

**Errors hierarchy (`infrastructure/resilience/errors.py` + `infrastructure/channels/errors.py`):**

```python
# resilience/errors.py
class CircuitBreakerOpenError(Exception):
    """Raised when CB short-circuits before fn execution."""
    def __init__(self, channel: str, tenant_id: UUID, retry_after_seconds: float) -> None:
        super().__init__(f"circuit open for {channel} tenant={tenant_id} retry_after={retry_after_seconds:.0f}s")
        self.channel = channel
        self.tenant_id = tenant_id
        self.retry_after_seconds = retry_after_seconds

# channels/errors.py
class ChannelError(Exception):
    """Base for channel-layer errors."""
    error_code: str = "unknown"

class ChannelRetryableError(ChannelError):
    """Transient (5xx, network, 429). CB counts as failure. Worker retry."""
    error_code = "retryable"

class ChannelRateLimitedError(ChannelRetryableError):
    """429 from provider. Includes optional retry_after_seconds."""
    error_code = "rate_limited"
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds

class ChannelFatalError(ChannelError):
    """4xx (excepto 429), invalid recipient, blocked by user. Mark task FAILED no retry."""
    error_code = "fatal"

class ChannelComplianceBlocked(ChannelFatalError):
    """ComplianceService denied. Mark task SKIPPED no retry."""
    error_code = "compliance_blocked"

class ChannelTenantRateExceeded(ChannelRetryableError):
    """OutboundRateLimiter denied. Reschedule next scheduler tick (no CB hit — tenant gate, no provider issue)."""
    error_code = "tenant_rate_exceeded"
```

**Razón split error hierarchy:** la lógica de retry en el worker MUST distinguir transient (CB-counted) de fatal (no retry) de tenant-gate (reschedule sin CB hit). Sin esa separación, un opt-out fatal contaría hacia el threshold del CB y abriría el breaker para el resto de tenants — anti-1000-clientes. Alternativa rechazada (single ChannelError): UI no puede explicar "¿por qué falló?" + worker no sabe si retry.

### 2.3 `AuditLogService` interface (`application/services/audit_log_service.py`)

```python
from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.campaigns.domain.audit_log import AuditEventType, AuditLogEvent

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.modules.campaigns.domain.audit_log import AuditLogRepository

class AuditLogService:
    """Sanitize + persist audit rows. Best-effort (try/except + structlog warning)."""

    def __init__(self, repo: AuditLogRepository) -> None: ...

    async def record(
        self,
        *,
        tenant_id: UUID,
        event_type: AuditEventType,
        actor: str,                          # "orchestrator" | "execution_worker" | "scheduler" | "api" | "system"
        campaign_id: UUID | None = None,
        campaign_task_id: UUID | None = None,
        payload: dict | None = None,         # sanitize_payload aplica antes de persist
        session: AsyncSession,
    ) -> None:
        """INSERT row. Sanitiza PII en payload via shared sanitize_payload.

        NEVER raise: si DB error → log warning + swallow. Audit log es best-effort
        per copilot-observability pattern. Caller decide tx commit.
        """
```

### 2.4 `CampaignOrchestrator` interface (`application/services/orchestrator.py`)

```python
from __future__ import annotations
from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from src.modules.campaigns.domain.campaign import Campaign

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

class OrchestratorError(Exception): ...
class OrchestratorCampaignNotLaunchableError(OrchestratorError): ...   # 409
class OrchestratorSegmentEmptyError(OrchestratorError): ...           # 422
class OrchestratorMissingStepsError(OrchestratorError): ...           # 422

class CampaignOrchestrator:
    """Real launch() — replaces PR-4 STUB.

    Idempotency contract: launch(campaign_id) is idempotent within
    LAUNCH_IDEMPOTENCY_TTL_SECONDS=600 via @idempotent decorator on the
    public method. Re-launch within window → cached projection {id, status,
    external_id=tasks_count}. Re-launch after TTL: orchestrator detects
    Campaign.status == RUNNING and returns no-op (additional layer of safety).

    Atomicity contract: per-launch operation runs inside SINGLE
    `async with session.begin()` block (D22):
      1. Lock Campaign row (SELECT FOR UPDATE).
      2. Validate state (status==SCHEDULED or DRAFT-direct-launch via FSM check).
      3. Resolve segment → snapshot_id (auto-snapshot if STATIC + no fresh snapshot).
      4. Generate CampaignTask rows (DAG walk by step_index ordering; only
         step_index=0 / no-incoming-edges roots scheduled at launched_at;
         downstream steps wait for parent task SENT to enqueue — out of scope
         PR-5; only ROOT steps generate tasks now).
      5. INSERT batch via repo.append_many (ON CONFLICT DO NOTHING dedup).
      6. Transition Campaign DRAFT|SCHEDULED → RUNNING via Campaign.transition_allowed.
      7. Emit CampaignLaunched + CampaignTasksGenerated outbox events.
      8. Commit (caller delegates).
      9. POST-COMMIT: enqueue ARQ jobs for each task with scheduled_at <= utc_now()
         (delayed tasks rely on scheduler_tick).

    Steps 4-6 in the same TX guarantees no orphan tasks if commit fails.
    Step 9 is post-commit (best-effort; if pod crashes between commit and
    enqueue, scheduler_tick picks up at next minute boundary — backstop).
    """

    LAUNCH_IDEMPOTENCY_TTL_SECONDS = 600  # 10min — typical retry/UI doubleclick window

    def __init__(
        self,
        *,
        campaign_repo: "CampaignRepository",
        step_repo: "CampaignStepRepository",
        task_repo: "CampaignTaskRepository",
        segment_service: "SegmentService",
        outbox_service: "OutboxService",
        audit_log_service: "AuditLogService",
        arq_pool_provider,                   # async () -> ArqRedis (lazy, multi-pod)
        execution_queue_name: str = "arq:campaigns_execution",
    ) -> None: ...

    async def launch(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: "AsyncSession",
    ) -> "OrchestratorLaunchResult":
        """Public entry. Decorated with @idempotent.

        @idempotent(
            namespace="campaigns:launch",
            key_fn=lambda *, tenant_id, campaign_id, **_: f"{tenant_id}:{campaign_id}",
            ttl=LAUNCH_IDEMPOTENCY_TTL_SECONDS,
        )

        Raises:
        - OrchestratorCampaignNotLaunchableError → 409
        - OrchestratorSegmentEmptyError → 422 (segment resolves to 0 leads)
        - OrchestratorMissingStepsError → 422 (campaign has no roots)
        """
```

**Razón rechazo "every-step generates tasks at launch" (D22 confirmado tras audit DAG schema vivo):** PR-3 cementó `CampaignStep.next_step_ids: list[UUID]` + `CampaignTask.step_id` polymorphic. Generar TODOS los tasks (incluso descendientes) al launch implica resolver DAG up-front. Pero descendientes dependen de outcome del parent (BRANCH_ON_CONDITION) o delay (WAIT_DELAY) — calculable solo en runtime. PR-5 genera SOLO root tasks. Cuando un task SENT, su sucesor task se genera por handler dedicado (S3 wireá esto vía OutboundOrchestrator + future worker). PR-5 stub: si step.step_type == SEND_MESSAGE y step_index == 0 → task. Suficiente para MVP Telegram 1-step. Documentado explícito en docstring.

---

## 3. SQLA models concretos — `campaign_audit`

### 3.1 Domain VO + enum (`domain/audit_log.py`)

```python
from __future__ import annotations
from enum import StrEnum

class AuditEventType(StrEnum):
    CAMPAIGN_LAUNCHED = "campaign_launched"
    TASKS_GENERATED = "tasks_generated"
    TASK_DISPATCHED = "task_dispatched"
    TASK_SENT = "task_sent"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_CLOSED = "circuit_closed"
    COMPLIANCE_BLOCKED = "compliance_blocked"
    RATE_LIMITED = "rate_limited"

# Pure VO (frozen, slots) — written via repo, read via repo.
@dataclass(frozen=True, slots=True)
class AuditLogEvent:
    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    campaign_task_id: UUID | None
    event_type: AuditEventType
    actor: str
    payload: dict
    created_at: dt.datetime

class AuditLogRepository(ABC):
    @abstractmethod
    async def append(self, evt: AuditLogEvent, *, session: AsyncSession) -> None: ...
    @abstractmethod
    async def list_by_campaign(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession,
        limit: int = 100, offset: int = 0,
    ) -> Sequence[AuditLogEvent]: ...
    @abstractmethod
    async def purge_older_than(
        self, *, cutoff: dt.datetime, batch_size: int = 5_000, session: AsyncSession,
    ) -> int:
        """Cross-tenant by design (worker scope retention).
        Documented allowlist entry in test_campaigns_tenant_isolation.py.
        Returns rows deleted in single batch (caller iterates until 0)."""
```

### 3.2 SQLA model (`infrastructure/models/campaign_audit_model.py`)

```python
from __future__ import annotations
import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base

class CampaignAuditModel(Base):
    """Audit log row. Append-only. Retention 90d via worker."""

    __tablename__ = "campaign_audit"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    campaign_task_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        # "todos los eventos de esta campaña" hot path
        Index("ix_campaign_audit_tenant_campaign_created", "tenant_id", "campaign_id", "created_at"),
        # retention purge hot path
        Index("ix_campaign_audit_created", "created_at"),
        # debug: buscar eventos por task específica
        Index("ix_campaign_audit_task", "campaign_task_id"),
    )
```

**Decisiones cementadas:**
- NO `deleted_at`: audit log es append-only + retention worker hace HARD DELETE bounded. Soft-delete sobre 100K rows/día sería tabla insostenible. Single arch exception documentada en allowlist `test_no_hard_deletes` (entry: `campaign_audit` purge worker).
- `campaign_id` nullable: eventos sistémicos (CB transitions) no atan a campaign específico.
- `payload` JSONB obligatorio (default `{}`) — sanitize_payload-d antes de insert.
- Sin FK constraint a `campaign(id)`: campaign puede ser soft-deleted pero audit log persiste. JOIN por id-en-aplicación.

---

## 4. Pydantic v2 DTOs

### 4.1 `application/dtos/audit_log_dtos.py`

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.audit_log import AuditEventType

class AuditLogEntryDTO(BaseModel):
    """Read shape. PII allowlist (sanitized in repo write — no raw PII enters payload)."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    campaign_task_id: UUID | None
    event_type: AuditEventType
    actor: str = Field(..., max_length=50)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime
```

### 4.2 `application/services/orchestrator.py` — result DTO

```python
class OrchestratorLaunchResult(BaseModel):
    """Returned by CampaignOrchestrator.launch + serialized by @idempotent cache.

    `id` + `status` + `external_id` projected by @idempotent (matches projector
    in shared/idempotency/application/decorator.py). external_id holds tasks_count
    so re-launch within TTL returns same value.
    """
    model_config = ConfigDict(extra="forbid")

    id: UUID                       # campaign_id (used by @idempotent projection)
    status: str                    # "running" | "noop_already_running"
    external_id: str               # str(tasks_generated_count) — fits projection contract
    tasks_generated: int = Field(ge=0)
    snapshot_id: UUID | None
    launched_at: dt.datetime
```

### 4.3 `infrastructure/channels/shared.py` — dispatch result

```python
@dataclass(frozen=True, slots=True)
class ChannelDispatchResult:
    """Internal — bridge between TelegramChannelRouter.send and worker layer.
    Maps 1:1 to PR-3 ChannelSendResult VO; this dataclass adds error_class
    so worker can decide retry vs fatal vs skip without isinstance gymnastics.
    """
    success: bool
    channel: str
    external_message_id: str | None
    error_code: str | None
    error_message: str | None
    error_class: Literal["retryable", "rate_limited", "tenant_rate_exceeded", "fatal", "compliance_blocked"] | None
    retry_after_seconds: float | None  # honored by worker if rate_limited
```

### 4.4 `application/dtos/campaign_dtos.py` (existente — MOD)

`CampaignLaunchResponse` ya existe en PR-4 con `notice` field STUB. PR-5 MOD: cambia `notice` default text para reflejar real launch:

```python
class CampaignLaunchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    campaign: CampaignResponse
    tasks_generated: int = Field(ge=0, description="Cantidad de CampaignTask creadas para roots del DAG.")
    notice: str = Field(
        default=(
            "Lanzamiento ejecutado. Tasks raíz creadas y dispatch en cola via "
            "ChannelRouterRegistry. Audit log: GET /campaigns/{id}/audit (futuro post-PI-1)."
        ),
    )
```

`response_model=CampaignLaunchResponse` permanece (regla `pii-sanitisation`). Arch test `test_campaigns_api_response_model.py` no requiere update porque ya valida la presencia de response_model.

---

## 5. Migration 113 — schema raw SQL

### 5.1 Path

```
backend/alembic/versions/113_campaigns_audit_log.py
```

### 5.2 Contenido (pseudo-SQL exacto que el builder debe escribir)

```python
"""campaigns audit log — campaign_audit table + indices.

PI-1 S2 PR-5 orchestrator-and-workers.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md.
NO ALTER existing tables. ZERO conflict potencial.

Revision ID: 113_campaigns_audit_log
Revises: 112_campaigns_domain
Create Date: 2026-04-30
"""
from alembic import op

revision = "113_campaigns_audit_log"
down_revision = "112_campaigns_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_audit (
            id                  UUID            PRIMARY KEY,
            tenant_id           UUID            NOT NULL,
            campaign_id         UUID            NULL,
            campaign_task_id    UUID            NULL,
            event_type          VARCHAR(50)     NOT NULL,
            actor               VARCHAR(50)     NOT NULL,
            payload             JSONB           NOT NULL DEFAULT '{}'::jsonb,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_campaign_audit_actor_nonempty CHECK (length(actor) > 0),
            CONSTRAINT ck_campaign_audit_event_type_nonempty CHECK (length(event_type) > 0)
        )
    """)
    # Hot path: "todos los eventos de esta campaña ordenados desc"
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_tenant_campaign_created
            ON campaign_audit (tenant_id, campaign_id, created_at DESC)
            WHERE campaign_id IS NOT NULL
    """)
    # Hot path: retention purge (worker scans by created_at globally)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_created
            ON campaign_audit (created_at)
    """)
    # Debug: eventos por task específica
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_task
            ON campaign_audit (campaign_task_id)
            WHERE campaign_task_id IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_task")
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_created")
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_tenant_campaign_created")
    op.execute("DROP TABLE IF EXISTS campaign_audit")
```

**Razón partial indexes vs full:** ix_campaign_audit_tenant_campaign_created skipea filas sistémicas (CB events sin campaign_id) en el index — más pequeño + faster. ix_campaign_audit_task idem para events sin task.

**Test idempotente clone-DB obligatorio (regla `backend-migrations.md`):**
```bash
docker exec visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 112_campaigns_domain && POSTGRES_DB=migration_test alembic upgrade head && POSTGRES_DB=migration_test alembic upgrade head'
docker exec visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

**Razón rechazo `op.create_table()`:** SA 2.0.27 broken `sa.Enum(create_type=True)` + non-idempotent re-runs en prod. Raw SQL es el SSoT cementado del codebase.

---

## 6. ARQ functions concretos

### 6.1 Topology — queue named `arq:campaigns_execution` + global default queue

| Function | Queue | Trigger | Cron | max_jobs | max_tries | job_timeout | Idempotente? |
|---|---|---|---|---|---|---|---|
| `run_campaign_execution_task(ctx, campaign_task_id: str)` | `arq:campaigns_execution` | enqueue (orchestrator post-commit + scheduler_tick) | — | — (heredado) | 5 | 60s | sí (idempotency_key per task; dedup en `IdempotencyStore` per-send) |
| `run_campaign_scheduler_tick(ctx)` | default | cron | `minute={5,15,25,35,45,55}` | — | 1 | 30s | sí (claim_pending_for_worker + status check) |
| `run_segment_refresh_tick(ctx)` | default | cron | `minute={10}` (cada hora) | — | 1 | 120s | sí (verifica freshness) |
| `purge_old_campaigns_audit(ctx)` | default | cron | `hour=4, minute=30` | — | 1 | 600s | sí (delete WHERE created_at < cutoff) |

**Razón cron offset minute={5,15,25,35,45,55} para scheduler_tick:** `analytics.run_tick_scheduler` ocupa `minute=set(range(60))` (cada minuto). Para evitar pile-up DB connection contention, campaigns scheduler usa subset de 6 minutos disjuntos. Trade-off: latencia scheduling máxima 10s (acept para 1000 clientes; sub-minuto = sobre-ingeniería).

**Razón segment_refresh cada hora vs cada 15min:** PR.md sugiere cada 15min. Tras audit del schema vivo (`Segment.last_calculated_at` + `SegmentSnapshot` immutable) y patrón de uso (campaigns RUNNING con segments STATIC → snapshot creado en orchestrator.launch; segments DYNAMIC ya re-resolve cada lectura), refresh masivo cada 15min = sobreingeniería para 1000 clientes (60K snapshots/día). Cada hora cubre el caso real: "STATIC segment con tenant que hizo append de leads y quiere refresh sin re-launch". Tunable env `CAMPAIGNS_SEGMENT_REFRESH_MINUTES=60`. Documented decision diferida con override.

### 6.2 `run_campaign_execution_task(ctx, campaign_task_id)` (`workers/execution_task.py`)

```python
"""ARQ entry — process single CampaignTask.

Args via ARQ enqueue: campaign_task_id (str UUID).

Algorithm:
1. Open AsyncSession; SELECT FOR UPDATE the task row (single-row, no SKIP LOCKED
   because the orchestrator already routed by id; we just need exclusivity
   against parallel retry).
2. If status != 'pending'/'scheduled' → noop (race / already processed).
3. Resolve lead.telegram_id via shared/links/ports/crm_repos.get_customer_repository.
   If no telegram_id → mark task SKIPPED, audit `task_skipped` reason="no_channel_id".
4. ChannelRouterRegistry.get("telegram").send(...) wrapped in CB.call.
5. Map ChannelDispatchResult.error_class → action:
   - success=True → mark_sent + audit task_sent + outbox CampaignTaskSent.
   - retryable → re-raise to ARQ for backoff retry; CB counts.
   - rate_limited → re-raise + return retry_after_seconds (ARQ honors via job retry delay).
   - tenant_rate_exceeded → mark task back to 'pending' with scheduled_at += 5min;
     audit `rate_limited`; do NOT re-raise (no CB hit).
   - compliance_blocked → mark_skipped + audit `compliance_blocked`; do NOT re-raise.
   - fatal → mark_failed + audit `task_failed`; do NOT re-raise (terminal).
6. Commit. Best-effort: any exception in audit_log writes never aborts the main tx.

CRITICAL: every external call (CRM lookup, Telegram POST) is wrapped with a
timeout. Telegram POST: 10s (env `TELEGRAM_API_TIMEOUT_SECONDS`). CRM lookup:
5s (default per graceful-degradation). NO bare async calls.

Job retries (ARQ `max_tries=5`): exponential backoff 60s × 2^attempt
capped at 1h (D17). Configured via WorkerSettings.retry_jobs_callable
(architect note: ARQ default uses retry_after_seconds from raised exception
when present — ChannelRateLimitedError honors that).
"""

async def run_campaign_execution_task(ctx: dict, campaign_task_id: str) -> dict[str, str]:
    """Returns {"id": task_id, "status": final_status, "external_id": external_msg_id_or_empty}."""
```

**Idempotency-Key Telegram dispatch (D18):** TelegramChannelRouter.send uses `IdempotencyStore.set_if_not_exists` con key `f"telegram-send:{campaign_task_id}"` ANTES del POST. Si key ya existe → return cached ChannelDispatchResult (re-encoded de stored projection). TTL 24h. Razón: ARQ retry post-success-pre-task-update no duplica msg.

**Razón rechazo "claim_pending_for_worker" en execution_task:** PR-3 cementó `claim_pending_for_worker` para CROSS-TENANT batch processing (worker-scope FOR UPDATE SKIP LOCKED). PR-5 invierte la responsabilidad: scheduler_tick hace claim_pending_for_worker (UNICO sitio de uso), enqueue ARQ por task_id, execution_task procesa UNA task. Ventaja: ARQ pool (max_jobs=20) decide concurrencia, no SQL lock contention. Cementa la decisión D16 de queue dedicada.

### 6.3 `run_campaign_scheduler_tick(ctx)` (`workers/scheduler_tick.py`)

```python
"""ARQ cron — promote scheduled campaigns + claim pending tasks.

Algorithm:
1. Open AsyncSession.
2. PHASE A — promote scheduled campaigns:
   a. SELECT campaigns WHERE status='scheduled' AND scheduled_at <= now()
      LIMIT 100 (cross-tenant — worker scope, allowlist already includes this).
   b. For each: invoke CampaignOrchestrator.launch(tenant_id, campaign_id).
      @idempotent makes re-tick safe within TTL.
3. PHASE B — claim pending CampaignTasks:
   a. CampaignTaskRepository.claim_pending_for_worker(tenant_id=None,
      scheduled_before=now(), batch_size=100).
   b. For each claimed task → ARQ enqueue_job(
         "run_campaign_execution_task", str(task.id),
         _queue_name="arq:campaigns_execution"
      ).
4. Commit. Heartbeat: redis_cache.setex("campaigns:scheduler:last_tick", 600, "1")
   (parallels analytics scheduler heartbeat).

Bounded by LIMIT 100 each phase: 1000 clientes × ~10 campaigns avg = 10k campaigns;
6 ticks/hour × 100 = 600 promotions/hour cap. Sufficient (real new launches per hour
across 1000 tenants ~10-100). For task claim: 100 × 6 = 600/hour throughput per tick.
At 1000 clientes the bottleneck is ARQ pool (max_jobs=20) not the tick.

If a phase takes >25s (timeout warning), structlog warning + abort phase B; next
tick picks up. job_timeout=30s hard ceiling.
"""

async def run_campaign_scheduler_tick(ctx: dict) -> dict[str, int]:
    """Returns {"promoted": int, "tasks_enqueued": int}."""
```

**Razón claim_pending_for_worker reuso:** PR-3 ya cementa esta cross-tenant exception (allowlist en `test_campaigns_tenant_isolation.py`). Llamarla aquí NO requiere allowlist adicional. Documenta en docstring del scheduler.

### 6.4 `run_segment_refresh_tick(ctx)` (`workers/segment_refresh_tick.py`)

```python
"""ARQ cron — refresh STATIC segments linked to RUNNING campaigns.

Scope intencionalmente narrow (D26 nuevo, decisión architect tras audit):
- Solo segments STATIC con campaign linked en status RUNNING.
- Solo segments con (now - last_calculated_at) > REFRESH_THRESHOLD_MINUTES (default 60).
- Cap 50 segments por tick (avoid CPU spike).

Algorithm:
1. SELECT segment.id, tenant_id FROM segment s
   JOIN campaign c ON c.segment_id = s.id
   WHERE s.segment_type='static'
     AND s.deleted_at IS NULL
     AND c.deleted_at IS NULL
     AND c.status='running'
     AND (s.last_calculated_at IS NULL OR s.last_calculated_at < now() - INTERVAL '60 minutes')
   LIMIT 50.
2. For each → SegmentService.snapshot(tenant_id, segment_id).
3. Each snapshot is its own AsyncSession transaction (failure of one segment
   does not block others — best-effort batch).
4. Audit log NO emitted per-segment (volume noise; covered by SegmentSnapshotted
   outbox event already emitted by SegmentService.snapshot).

Cross-tenant SELECT — allowlist documented in docstring. Tenant isolation
preserved INSIDE the loop (each SegmentService.snapshot call scoped to
tenant_id from the row).
"""

async def run_segment_refresh_tick(ctx: dict) -> dict[str, int]:
    """Returns {"refreshed": int, "errors": int}."""
```

### 6.5 `purge_old_campaigns_audit(ctx)` (`workers/audit_retention_task.py`)

```python
"""ARQ cron — daily 04:30 UTC. Hard delete audit rows older than retention.

Env: CAMPAIGNS_AUDIT_RETENTION_DAYS=90 (default). Min 7d. Max 365d (sanity).

Bounded delete: WHERE created_at < cutoff LIMIT 5000, loop until rowcount=0
or job_timeout (10min). Bounded by ix_campaign_audit_created index — cheap.
"""

async def purge_old_campaigns_audit(ctx: dict) -> dict[str, int]:
    """Returns {"deleted": int, "batches": int}."""
```

### 6.6 `backend/src/workers/settings.py` MOD (extend, regla M8)

Builder MUST:
1. **Read current file before editing.**
2. **APPEND** imports + functions list + cron_jobs entries. **NEVER** remove existing entries.
3. WorkerSettings.functions: agregar `run_campaign_execution_task`, `run_campaign_scheduler_tick`, `run_segment_refresh_tick`, `purge_old_campaigns_audit` al final de la lista.
4. SchedulerSettings.functions: idem (ARQ requiere mirror según comentario L127).
5. SchedulerSettings.cron_jobs: agregar 3 entries:
   - `cron(run_campaign_scheduler_tick, minute={5, 15, 25, 35, 45, 55})`
   - `cron(run_segment_refresh_tick, minute={10})`
   - `cron(purge_old_campaigns_audit, hour=4, minute=30)`
6. **Bootstrap channels en `WorkerSettings.on_startup`:**
   ```python
   from src.modules.campaigns.infrastructure.channels.registry import register_default_channels
   from src.modules.campaigns.infrastructure.channels.token_provider import env_telegram_token_provider
   register_default_channels(telegram_token_provider=env_telegram_token_provider)
   ```
7. **Same in `SchedulerSettings.on_startup`** (scheduler may invoke orchestrator → orchestrator uses registry).
8. NO modificar `max_jobs=10` global; queue named `arq:campaigns_execution` se configura via env `CAMPAIGNS_EXECUTION_QUEUE_NAME` consumida por orchestrator.enqueue_job y por future split deploy `CampaignsWorkerSettings` (out of scope PR-5 — tracked en IMPL-LOG).

**Razón solo append, no remove (regla M8 + parallel-safety):** otra sesión paralela (PI-2) PUEDE estar agregando workers a `settings.py`. Builder reads file first via Read tool, identifies "S2 campaigns workers" section to append, never removes anything. Conflict push → STOP escalate Chris (regla M5).

---

## 7. Circuit breaker semantics — full state machine spec

### 7.1 State diagram (textual)

```
                     ┌──────────────────────┐
                     │       CLOSED         │
                     │ (calls pass through) │
                     │ (count failures rolling 60s)
                     └──────────┬───────────┘
                                │ failures >= fail_threshold
                                ▼
                     ┌──────────────────────┐
                     │        OPEN          │
                     │  (calls fail-fast)   │
                     │  (raise CircuitBreakerOpenError)
                     │  (audit `circuit_opened`)
                     └──────────┬───────────┘
                                │ now - opened_at >= open_duration_seconds
                                ▼
                     ┌──────────────────────┐
                     │     HALF_OPEN        │
                     │ (allow N probes)     │
                     └──────┬─────────┬─────┘
                            │         │
              probe success │         │ probe failure
                            │         │
                            ▼         ▼
                  CLOSED (audit `circuit_closed`)   OPEN (re-open, audit `circuit_opened`)
```

### 7.2 Env vars (defaults)

| Env | Default | Range válido | Razón |
|---|---|---|---|
| `CAMPAIGNS_CB_FAIL_THRESHOLD` | 5 | 1..50 | 5 fails en rolling 60s = signal real falla provider, no flake puntual |
| `CAMPAIGNS_CB_OPEN_DURATION_SECONDS` | 60 | 10..600 | 60s = la mayoría de outages parciales API resuelven en ese rango |
| `CAMPAIGNS_CB_HALF_OPEN_PROBES` | 1 | 1..5 | 1 probe es suficiente; >1 introduce thundering herd |
| `CAMPAIGNS_CB_ROLLING_WINDOW_SECONDS` | 60 | 30..600 | Match open_duration |
| `TELEGRAM_API_TIMEOUT_SECONDS` | 10 | 1..60 | Telegram p99 < 5s; 10s = factor 2 safety |

### 7.3 Per-(channel, tenant_id) isolation INVARIANT

Property-based test (Hypothesis) en `test_circuit_breaker.py` verifica:
- `await cb_telegram_tenant_A.force_open()` → `cb_telegram_tenant_B.state == CLOSED`.
- `await cb_telegram_tenant_A.force_open()` → `cb_whatsapp_tenant_A.state == CLOSED` (future PI-2 prep).

Razón 1000 clientes: tenant noisy (bot bloqueado, token expirado) NO degrada otros 999.

### 7.4 Error class → CB hit decision (recap)

| Error class | CB counts? | Worker action |
|---|---|---|
| `retryable` (5xx, network) | sí | re-raise → ARQ retry exp backoff |
| `rate_limited` (Telegram 429) | sí | re-raise + retry_after_seconds → ARQ honors |
| `tenant_rate_exceeded` (OutboundRateLimiter) | **no** | reschedule task; no CB hit (es gate cliente, no provider) |
| `compliance_blocked` (ComplianceService) | **no** | mark_skipped; no CB hit |
| `fatal` (4xx invalid recipient) | **no** | mark_failed; no CB hit |

**Razón rechazo "all errors count as CB":** mezclar tenant gates con provider failures haría que un tenant exhausto rate-limit abriera el breaker globalmente para todos los demás tenants (mismo channel, distinto cb-key... actually distinto cb-key porque per-tenant; pero la regla debe ser semánticamente clara). Mejor: solo provider-side failures count.

---

## 8. TelegramChannelRouter API surface

### 8.1 Class signature (`infrastructure/channels/telegram.py`)

```python
from __future__ import annotations
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import UUID

import httpx
import structlog

from src.modules.campaigns.domain.channel_router import ChannelRouter, ChannelSendResult
from src.modules.campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked, ChannelFatalError, ChannelRateLimitedError,
    ChannelRetryableError, ChannelTenantRateExceeded,
)
from src.modules.campaigns.infrastructure.channels.shared import (
    ChannelDispatchResult, format_message_for_tenant_locale, telegram_idempotency_key,
)
from src.modules.campaigns.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from src.shared.compliance.application.compliance_service import ComplianceService
from src.shared.idempotency.application.service import IdempotencyService
from src.shared.idempotency.domain.key import IdempotencyKey
from src.shared.billing.application.rate_limiter import OutboundRateLimiter

if TYPE_CHECKING:
    from src.shared.links.ports.crm_repos import ...  # type-only

logger = structlog.get_logger(__name__)


class TelegramChannelRouter(ChannelRouter):
    """Telegram Bot API outbound dispatch.

    Pre-send pipeline (ORDER MATTERS):
      1. select_channel → confirm lead has telegram_id (if not → return None earlier).
      2. ComplianceService.check → if denied → raise ChannelComplianceBlocked.
      3. OutboundRateLimiter.check → if denied → raise ChannelTenantRateExceeded.
      4. IdempotencyService.with_dedupe(key=telegram-send:{task_id}, fn=...)
         → fn is the CB-protected POST.
      5. CircuitBreaker.call(post_to_telegram).
      6. Map httpx response → ChannelDispatchResult / raise channel error class.

    httpx config:
      - timeout=httpx.Timeout(10.0, connect=5.0) — env CAMPAIGNS_HTTPX_TIMEOUT.
      - retries=0 (CB + ARQ handle retry semantics).
      - Default headers: {"User-Agent": "Nicolify-Campaigns/1.0"}.
      - Connection pool reused via module-level singleton AsyncClient (await close on shutdown).

    Idempotency-Key strategy (D18):
      key = f"telegram-send:{campaign_task_id}"
      ttl = 86400 (24h)
      stored projection: {"id": task_id, "status": "sent"|"fatal", "external_id": telegram_msg_id}
    """

    def __init__(
        self,
        *,
        token_provider: Callable[[UUID], Awaitable[str]],
        compliance_service: ComplianceService | None = None,  # injected at runtime
        outbound_rate_limiter: OutboundRateLimiter | None = None,
        idempotency_service: IdempotencyService | None = None,
        circuit_breaker_factory: Callable[[str, UUID], CircuitBreaker] | None = None,
        httpx_client: httpx.AsyncClient | None = None,
        api_base: str = "https://api.telegram.org",
    ) -> None: ...

    async def select_channel(
        self, tenant_id: UUID, lead_id: UUID, priority: list[str],
    ) -> str | None:
        """Return "telegram" if "telegram" in priority AND lead.telegram_id present."""

    async def send(
        self, tenant_id: UUID, lead_id: UUID, channel: str, content: dict,
        *, idempotency_key: str,
    ) -> ChannelSendResult:
        """Send single message. content = {
            "chat_id": str,        # Telegram chat id (=lead.telegram_id)
            "text": str,           # final body, locale-formatted
            "parse_mode": "HTML"|"MarkdownV2"|None,
            "disable_notification": bool,
        }"""
```

### 8.2 Master-data formatting (`shared.py::format_message_for_tenant_locale`)

```python
async def format_message_for_tenant_locale(
    *,
    tenant_id: UUID,
    template_text: str,                  # may contain {{date_iso}}, {{amount_usd}} placeholders
    placeholders: dict[str, Any],
) -> str:
    """Apply tenant locale to formatted text.

    - {{date_iso}} → formatTenantDate-style "DD/MM/YYYY HH:mm <tz>" via TenantLocale.timezone
    - {{amount_*}} → build_money_display(amount, currency=TenantLocale.currency)
    - Other placeholders pass-through.

    Resolves TenantLocale via ports (lazy import, no cross-module DDD violation):
        from src.shared.links.ports.tenant_profile import get_tenant_locale_port
    """
```

**Razón explícita:** Telegram message body con fechas/montos DEBE respetar locale tenant (regla `master-data.md` + `currency-handling.md`). Sin esto un tenant PE recibe mensaje con fechas formato US — anti-1000-clientes (tenants LATAM). Fallback `TenantLocale.default()` si lookup falla (no aborta send).

### 8.3 Httpx client lifecycle

- Module-level singleton `_HTTPX_CLIENT: httpx.AsyncClient | None = None` lazy-init en primer uso.
- `WorkerSettings.on_shutdown` MUST close it (extend hook).
- Connection pool size: default httpx (100). At 1000 clientes con 20 max_jobs = max 20 concurrent connections — within pool.

---

## 9. Decisiones D15-D22 confirmadas (post-audit schema vivo)

| # | Decisión | Veredicto post-audit | Notas |
|---|---|---|---|
| D15 | Custom asyncio CB Redis-backed (no pybreaker/aiobreaker) | **CONFIRMADA** | Schema vivo: `core.database.redis_client` ya disponible. Patrón mirror de `OutboundRateLimiter` Redis — coherente. |
| D16 | Queue named `arq:campaigns_execution` + global default | **CONFIRMADA** + ajuste | Schema vivo: `WorkerSettings.functions` tiene 22 fns existentes. Append seguro. NO crear `CampaignsWorkerSettings` separado en PR-5 (deploy split = future commit, doc en IMPL-LOG). Queue name vía `_queue_name` arg de `enqueue_job`. |
| D17 | ARQ exp backoff 60s × 2^retry max 5 retries | **CONFIRMADA** | Schema vivo: PR existing workers usan `max_tries=5` global (settings.py L84). PR-5 hereda. |
| D18 | Application-side idempotency Telegram via IdempotencyStore | **CONFIRMADA** | Schema vivo: `RedisIdempotencyStore` + `@idempotent` decorator + `IdempotencyService.with_dedupe` ya disponibles. Pattern documented. |
| D19 | 90d retention + cron 04:30 UTC | **CONFIRMADA** | Schema vivo: mirror `purge_expired_trace_rows` que corre 04:00 UTC. PR-5 usa 04:30 para no stackear. |
| D20 | Webhook bidireccional Telegram → S3 | **CONFIRMADA** | Out of scope PR-5. |
| D21 | PR-6 cutover secuencial (no paralelo) | **CONFIRMADA** | Out of scope PR-5. |
| D22 | Single TX `async with session.begin()` para launch() | **CONFIRMADA** + refinada | Schema vivo: `task_repo.append_many` ON CONFLICT DO NOTHING ya implementado. Atomicidad cubierta. **Refinamiento:** PR-5 genera SOLO root steps (step_index==0) tasks en launch. Descendientes generated post-success en future commit (S3+). Documented en orchestrator docstring. |

**Drift detectado vs PR.md y resolución:**

1. **PR.md menciona 11 events; events.py tiene 14 (incluye SegmentCreated, SegmentSnapshotted, CampaignTaskQueued).** Resolución: PR-5 emite `CampaignTasksGenerated` como **NUEVO event** (no en PR-3) — agregarlo en `domain/events.py`. Builder MUST add this event class siguiendo template `_CampaignEventBase`. Audit gate: event name `campaigns.campaign.tasks_generated`. NO ROMPE arch tests existentes (frozen es lista shrink-only).
2. **PR.md menciona CampaignAuditModel + retención 90d. Schema vivo NO tiene `campaign_audit` (correcto: PR-5 lo crea).** Resolución: migration 113.
3. **PR.md menciona `campaigns_audit` (plural). Patrón cementado de tablas single-noun (e.g. `campaign_task`, `campaign`).** Resolución: nombre tabla = `campaign_audit` (singular). Aligned con codebase pattern.
4. **PR.md menciona `run_campaign_scheduler_tick` con `minute={5,15,25,35,45,55}`. Confirmed.**
5. **PR.md menciona `OutboxRepositoryImpl` (singular).** Schema vivo: `OutboxService.enqueue_async_from_sync_caller(event, *, session)`. Confirmed signature.
6. **PR.md asume `CampaignTask.idempotency_key` schema. Schema vivo confirma `idempotency_key: Mapped[str], UniqueConstraint("tenant_id", "idempotency_key")`. Builder reusa esto sin crear nuevo schema.**

---

## 10. Test strategy — TDD layer order

### 10.1 RED-first per layer

| Layer | Test file | RED order |
|---|---|---|
| Domain (audit_log VO + enum) | `tests/modules/campaigns/domain/test_audit_log.py` | 1 |
| Infra repo (audit_log_repo) | `tests/modules/campaigns/infrastructure/test_audit_log_repo.py` | 2 |
| Infra resilience (CB) | `tests/modules/campaigns/infrastructure/test_circuit_breaker.py` | 3 (Hypothesis property-based state machine + per-key isolation) |
| Infra channel registry | `tests/modules/campaigns/infrastructure/test_channel_router_registry.py` | 4 |
| Infra channel telegram | `tests/modules/campaigns/infrastructure/test_telegram_channel_router.py` | 5 (httpx mock — see fixture below) |
| App orchestrator | `tests/modules/campaigns/application/test_orchestrator.py` | 6 |
| App orchestrator idempotency | `tests/modules/campaigns/application/test_orchestrator_idempotency.py` | 7 |
| App audit log service | `tests/modules/campaigns/application/test_audit_log_service.py` | 8 |
| Worker execution | `tests/modules/campaigns/workers/test_execution_task.py` | 9 |
| Worker scheduler tick | `tests/modules/campaigns/workers/test_scheduler_tick.py` | 10 |
| Worker segment refresh | `tests/modules/campaigns/workers/test_segment_refresh_tick.py` | 11 |
| Worker audit retention | `tests/modules/campaigns/workers/test_audit_retention_task.py` | 12 |
| API integration (launch real) | `tests/modules/campaigns/api/test_campaigns_launch_real.py` | 13 (MOD existing) |
| E2E smoke | `tests/modules/campaigns/integration/test_e2e_telegram_campaign_smoke.py` | 14 (sin mocks de service, política F-7) |

### 10.2 Fixtures necesarios (`tests/modules/campaigns/conftest.py`)

```python
# ARQ context fixture
@pytest.fixture
async def arq_ctx(async_session_factory, redis_client):
    return {
        "db_factory": async_session_factory,
        "redis": MockArqRedis(),     # records enqueue_job calls
        "redis_cache": redis_client,
    }

# httpx mock — respx usado por sales_agent tests
@pytest.fixture
def mock_telegram_api(respx_mock):
    """respx mock for api.telegram.org. Default: 200 ok with telegram_msg_id."""
    return respx_mock.post("https://api.telegram.org/.*sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {"message_id": 42}}),
    )

# CB Redis fake fixture
@pytest.fixture
def fake_redis_for_cb():
    """fakeredis.FakeAsyncRedis instance. Each test isolated."""
    import fakeredis.aioredis
    return fakeredis.aioredis.FakeRedis(decode_responses=False)

# Channel registry reset (autouse — prevents cross-test pollution)
@pytest.fixture(autouse=True)
def reset_channel_registry():
    from src.modules.campaigns.infrastructure.channels.registry import ChannelRouterRegistry
    yield
    ChannelRouterRegistry().reset()

# DB transaction rollback (autouse for fast tests)
@pytest.fixture
async def async_session(async_session_factory):
    async with async_session_factory() as session:
        yield session
        await session.rollback()  # never commit in unit tests
```

### 10.3 Integration test sin mocks de service (política F-7 PR-4)

`test_e2e_telegram_campaign_smoke.py`:
- Real `CampaignService`, `SegmentService`, `CampaignOrchestrator`, `TelegramChannelRouter` instances.
- ONLY mock: `respx_mock` para `https://api.telegram.org/.*` (NO real network call).
- Flow:
  1. Seed: tenant + lead con `telegram_id="-1001234567890"` + DRAFT campaign con 1 SEND_MESSAGE step + segment STATIC con 1 lead.
  2. POST `/api/v1/campaigns/{id}/schedule` (now+5s).
  3. Manually invoke `await run_campaign_scheduler_tick(arq_ctx)`.
  4. Assert: orchestrator invocado + 1 task creada con status=`pending`.
  5. Assert: 1 ARQ enqueue para `run_campaign_execution_task`.
  6. Manually invoke `await run_campaign_execution_task(arq_ctx, str(task_id))`.
  7. Assert: respx_mock recibió POST a `sendMessage` con body conteniendo locale-formatted text.
  8. Assert: `CampaignTask.status='sent'` + `external_message_id="42"` + audit rows: `task_dispatched`, `task_sent`.

---

## 11. Architectural fitness gates — 4 nuevos

### 11.1 `tests/architecture/test_campaigns_orchestrator_idempotent.py`

**AST scan logic:**
```python
"""Verify CampaignOrchestrator.launch is decorated with @idempotent.

Walks src/modules/campaigns/application/services/orchestrator.py.
Finds AsyncFunctionDef name='launch' inside ClassDef name='CampaignOrchestrator'.
Asserts the function has at least one decorator whose name resolves to
'idempotent' (Call.func.id == 'idempotent').

Ratchet: shrink-only allowlist EXEMPT_METHODS (initially empty). New
public orchestrator method that mutates state requires @idempotent OR
allowlist entry with justification.
"""
EXEMPT_METHODS: frozenset[str] = frozenset({})  # shrink-only
```

### 11.2 `tests/architecture/test_campaigns_workers_registered.py`

**AST scan logic:**
```python
"""Verify ARQ workers + crons registered in backend/src/workers/settings.py.

REQUIRED_FUNCTIONS = {
    "run_campaign_execution_task",
    "run_campaign_scheduler_tick",
    "run_segment_refresh_tick",
    "purge_old_campaigns_audit",
}
REQUIRED_CRON_FNS = {
    "run_campaign_scheduler_tick",
    "run_segment_refresh_tick",
    "purge_old_campaigns_audit",
}
1. Parse settings.py AST.
2. Find ClassDef WorkerSettings → assignment to 'functions' (list).
   Verify every REQUIRED_FUNCTIONS name appears as Name.id in the list.
3. Find ClassDef SchedulerSettings → assignment to 'cron_jobs' (list).
   Each list item is Call (cron(...)). First positional arg must be Name
   with id in REQUIRED_CRON_FNS — collect them, assert superset.

Ratchet: shrink-only KNOWN_MISSING (initially empty).
"""
```

### 11.3 `tests/architecture/test_channel_router_registry_invariants.py`

```python
"""Runtime registry contract.

1. `register_default_channels` MUST populate registry such that
   `registry.has("telegram")` is True after invocation (no bot token needed
   in test — token_provider stub).
2. The registered router MUST satisfy `isinstance(router, ChannelRouter)` —
   the runtime_checkable Protocol from PR-3.
3. `registry.get("nonexistent")` MUST raise KeyError.

This test imports the actual modules at runtime (not pure AST) — uses
the autouse reset fixture from conftest to avoid global state leak.
"""
```

### 11.4 `tests/architecture/test_campaigns_audit_log_retention.py`

```python
"""Verify retention worker exists + env-tunable + cron registered.

1. Module backend/src/modules/campaigns/workers/audit_retention_task.py
   MUST exist + define async function purge_old_campaigns_audit(ctx).
2. Function source MUST reference env var CAMPAIGNS_AUDIT_RETENTION_DAYS
   (literal string in source — verifies tunable contract).
3. Function source MUST contain literal CAMPAIGN_AUDIT_TABLE = 'campaign_audit'
   OR reference CampaignAuditModel.__tablename__.
4. Cron registration: parse settings.py AST, verify cron(purge_old_campaigns_audit, ...)
   exists in SchedulerSettings.cron_jobs.
"""
```

### 11.5 Existing gate updates

- `test_campaigns_tenant_isolation.py`: add `purge_older_than` to `CROSS_TENANT_ALLOWED_METHODS` (audit retention is cross-tenant by design — single allowlist entry, justified).
- `test_no_hard_deletes.py` (existing project gate): add `campaign_audit` table to allowlist exception (append-only + bounded retention pattern, mirror `copilot_trace_event`). Allowlist entry includes justification comment.

---

## 12. Cross-cutting concerns

### 12.1 Tenant isolation invariants

- Toda query SQLA en repos `audit_log_repo_impl.py` filtra `tenant_id` excepto `purge_older_than` (allowlist). Arch gate `test_campaigns_tenant_isolation.py` ya cubre via AST scan.
- `CampaignOrchestrator.launch(tenant_id=..., campaign_id=...)` — tenant_id arg MANDATORY. `_repo.get_by_id(campaign_id, tenant_id, session=...)` heredado PR-3.
- Worker `run_campaign_execution_task(ctx, campaign_task_id)`: deriva tenant_id de la task row (NO arg externo) — defensa en profundidad.
- Worker `run_campaign_scheduler_tick(ctx)`: cross-tenant batch claim (allowlist), pero invoca orchestrator/repo con tenant_id explicit per row.
- Circuit breaker key: `cb:campaigns:{channel}:{tenant_id}` — tenant_id en la clave, isolation natural.
- Audit log row: `tenant_id` NOT NULL (CHECK constraint enforced en migration).

### 12.2 Master-data formatting points

| Punto | Acción |
|---|---|
| Telegram message body | `format_message_for_tenant_locale(tenant_id, template_text, placeholders)` — applies `formatTenantDate*` + `build_money_display` via `TenantLocale` from tenant_profile port. |
| Audit log `created_at` | `DateTime(timezone=True)` + `default NOW()` (migration). Server-side time = single source. |
| Worker `scheduled_before` | `utc_now()` from `src.shared.domain.datetime_utils`. NEVER `datetime.utcnow()` (regla `master-data.md`). |
| Idempotency-key TTL | 86400 seconds (24h). NO timezone — pure relative seconds. |

### 12.3 PII sanitization en audit JSONB

`AuditLogService.record(...)`:
```python
sanitized_payload = sanitize_payload(payload or {})  # shared/agent_observability/recording/sanitization
evt = AuditLogEvent(payload=sanitized_payload, ...)
await self._repo.append(evt, session=session)
```

`sanitize_payload` already redacts: emails, phone, IP, financial. PR-5 audits include lead identifiers — REDACT them by NOT storing raw `telegram_id` / `email` in payload. Conventions:
- Store `lead_id: UUID` (no PII).
- For Telegram external_message_id — safe (numeric, not PII).
- Compliance evidence: redacted by sanitize_payload (regexes catch).
- Error messages from external API (Telegram body) — pass through sanitize_payload (catches phones/emails embedded).

### 12.4 Spanish neutro LATAM (regla `spanish-text.md`)

- `event_type` enum values en inglés (cementado patrón observability `copilot_trace_event` event_type strings).
- Audit `actor` values en inglés (`"orchestrator"`, `"execution_worker"`, `"scheduler"`).
- Excepción intencional: el output sales_agent NO aplica regla (cementado). Pero campaigns NO emite output user-facing en este PR (Telegram message es content que viene del template — usuario provee el texto). Validation: `format_message_for_tenant_locale` NO añade strings hardcoded.
- Logs `structlog`: en inglés (regla rules `debugging.md`). Eventos: `campaign_orchestrator_launch_start`, `campaign_orchestrator_launch_complete`, `circuit_breaker_opened`, etc.

### 12.5 structlog event schemas (dictionary keys mandatory)

| Event | Required keys | Optional keys |
|---|---|---|
| `campaign_orchestrator_launch_start` | tenant_id, campaign_id, segment_id | snapshot_id |
| `campaign_orchestrator_launch_complete` | tenant_id, campaign_id, tasks_generated, duration_ms | — |
| `circuit_breaker_opened` | channel, tenant_id, fail_count, opened_at | — |
| `circuit_breaker_closed` | channel, tenant_id, closed_at | — |
| `campaign_execution_task_dispatch` | tenant_id, task_id, campaign_id, channel | — |
| `campaign_execution_task_sent` | tenant_id, task_id, external_message_id, duration_ms | — |
| `campaign_execution_task_failed` | tenant_id, task_id, error_class, error_code | retry_after_seconds |
| `audit_retention_purge_complete` | rows_deleted, batches | — |
| `segment_refresh_tick_complete` | refreshed, errors, duration_ms | — |

### 12.6 Native-first dev (regla CLAUDE.md)

Builder MUST run lint/tests native:
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/modules/campaigns/ tests/modules/campaigns/ tests/architecture/test_campaigns_*.py
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check src/modules/campaigns/ tests/modules/campaigns/
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/campaigns/ tests/architecture/test_campaigns_*.py -v
```

NEVER `docker exec ruff/pytest`.

---

## 13. Architectural fitness impact summary

### Allowlist updates expected (shrink-only invariant respected — adding allowlist entry requires justification)

| Test | Current allowlist | PR-5 change | Justification |
|---|---|---|---|
| `test_campaigns_tenant_isolation.py::CROSS_TENANT_ALLOWED_METHODS` | `{"claim_pending_for_worker", "list_globals"}` | **add `"purge_older_than"`** | Audit retention worker by design cross-tenant. Mirror pattern of `purge_expired_trace_rows`. Documented in repo docstring. |
| `test_no_hard_deletes.py` (project-wide) | `{copilot_trace_event purge, model_pricing_snapshot ttl, ...}` | **add `"campaign_audit purge_old_campaigns_audit"`** | Append-only audit log + bounded retention worker (mirror `copilot_trace_event`). |
| `test_campaigns_orchestrator_idempotent.py::EXEMPT_METHODS` | NEW (empty) | initial empty set | Future shrink-only. |
| `test_campaigns_workers_registered.py::KNOWN_MISSING` | NEW (empty) | initial empty set | Future shrink-only. |

### Frozen tests post-PR-5 (PR-3+PR-4+PR-5 = 12 campaigns gates)

PR-3 (4) + PR-4 (4) + PR-5 (4) = 12 dedicated campaigns arch gates.
Project-wide gates (DDD boundaries 22 frozen, response_model, master-data, currency, redirect_slashes, no copilot imports, etc.) remain unchanged in count — only allowlist entries update with justification.

---

## 14. pm-nico/current-state updates required

Post-merge, builder/PM updates `docs/pm-nico/current-state/campaigns.md`:

- **Modify section "S2 PENDIENTE":** rename to "S2 SHIPPED — Orchestrator + Workers + ChannelRouter Telegram".
- **Append entries:**
  - `CampaignOrchestrator.launch()` (real, replaces PR-4 STUB)
  - 4 ARQ workers: execution / scheduler_tick / segment_refresh_tick / audit_retention
  - ChannelRouter Telegram (TelegramChannelRouter implements ChannelRouter Protocol)
  - Circuit breaker per (channel, tenant_id) Redis-backed
  - ComplianceService + OutboundRateLimiter wired pre-send
  - Audit log dedicated table `campaign_audit` retention 90d
- **Modify section "Capacidades operables desde copilot":** column "PI-1 S3" para `campaign_launch` ya tiene foundation (orchestrator real); copilot tools wiring difer S3.
- **Modify Decisiones:** append D15-D22 entries.
- **Bump fila "Ultima actualizacion":** date PR-5 merge.

---

## 15. Open questions for PM

**(IDEAL: vacía) — auditoría producida cero gaps reales.**

Sin embargo, dejo flagueado un **drift de naming** detectado para confirmación rápida (no bloquea — builder puede asumir resolución default a menos que /pm intervenga):

- **Q (cosmética, default OK):** PR.md menciona tabla `campaigns_audit` (plural). Patrón cementado del codebase (12+ tablas) es singular: `campaign`, `campaign_step`, `campaign_task`, `segment`, `segment_snapshot`, `campaign_template`, `copilot_trace_event`, `sales_agent_trace_event`, etc. **Resolución default elegida: `campaign_audit` (singular)**. Si /pm prefiere plural por convención de "audit log", flag rápido — 1 línea cambio en migration + model. Sin respuesta = singular default.

Cero open questions reales. Architect confirma autonomía completa.

---

## 16. Research notes

### 16.1 Circuit breaker — state machine SoTA

**Source:** Tessl tile `tessl-labs/graceful-degradation` (vendored 2026-04-30 access). Key takeaways:
- Iron Rule: timeout + fallback siempre. Sin excepción.
- Per-dependency CB instance (no shared global).
- Default 5 fails / 30s reset. PR-5 amplía a 60s reset (Telegram outages típicos > 30s).
- HALF_OPEN single probe (no thundering herd).

**Why custom over libs:**
- `pybreaker` (sync only) → wrap async = anti-pattern.
- `aiobreaker` → abandoned 2021, no Redis backend.
- `purgatory` → curva learning + dep nuevo (regla pip-audit). Custom 80 LOC = lower risk + match patrón `OutboundRateLimiter` Redis-backed (cementado).

### 16.2 ARQ named queue routing

**Source:** ARQ docs (https://arq-docs.helpmanual.io/, retrieved 2026-04-30, version 0.26+). Key:
- `enqueue_job(fn_name, *args, _queue_name="...")` routes to specific queue.
- Worker reads queue from `WorkerSettings.queue_name` attribute (falls back to default if unset).
- Multi-queue same-process: not supported nativo en ARQ — requires `CampaignsWorkerSettings` separate process. PR-5 NO splits process (out of scope); flag for future deploy in IMPL-LOG.

### 16.3 Idempotency-Key over Telegram Bot API

**Source:** Telegram Bot API docs (https://core.telegram.org/bots/api, retrieved 2026-04-30). Key:
- Native Idempotency-Key NOT supported. Confirms D18 (application-side dedup).
- 429 returns `parameters.retry_after` field (seconds). PR-5 honors via `ChannelRateLimitedError.retry_after_seconds`.
- 30 msg/sec global rate limit, 1/sec per chat. PR-5 OutboundRateLimiter (per-tenant 24h sliding) is COMPLEMENTARY, not redundant.

### 16.4 SQLA 2.0 + pg_insert ON CONFLICT

**Source:** SQLAlchemy 2.0.x docs (already proven by PR-3 `task_repo.append_many`). PR-5 reuses verbatim — zero new pattern.

---

<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-5 architect done" para review. -->
