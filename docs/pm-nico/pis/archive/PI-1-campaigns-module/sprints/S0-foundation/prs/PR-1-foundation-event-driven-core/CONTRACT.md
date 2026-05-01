# CONTRACT — PR-1-foundation-event-driven-core

> Owner: `nicolify-architect`. SSoT pre-implementación. Solo backend (sin FE — infra cross-cutting). Builder consume este archivo + sigue TDD inside-out por sub-deliverable.
> Status: **READY for builder — PM decisions Q1-Q6 resolved**. Última actualización 2026-04-29 (post-PM resolution).

## 0. Context summary

| Campo | Valor |
|---|---|
| PR ID | PR-1-foundation-event-driven-core |
| PI / Sprint | PI-1-campaigns-module / S0-foundation |
| Modules tocados (write) | `shared/domain_events/outbox/` (nuevo) · `shared/idempotency/` (nuevo) · `modules/campaigns/observability/` (nuevo) · `shared/domain/events.py` (deprecation shim) · `workers/settings.py` (worker registration + cron) · `core/config.py` (env vars) |
| Modules tocados (read-only, sin cambio API pública) | `modules/sales_agent/`, `modules/copilot/`, `modules/brand/` (los 3 emisores migran via `EventBusAdapter` con flags OFF default — cero breaking change PR-1) |
| Skills consultadas | `copilot-expert` (idempotency ad-hoc actual extraction_card_flow.py:68-77 debe migrar limpio), `sales-agent-expert` (§3 protected surfaces — webhook adapters + tool emitters), `brand-expert` (after-commit dispatch invariante — brand_summary regen depende), `backend-expert` (DDD Inside-Out, migration idempotency, arch fitness) |
| pm-nico/current-state files updates post-merge | `campaigns.md` (capability "observability spec registered" nueva) · `sales_agent.md` (línea "outbox migration ready, flag OFF default") · `copilot.md` (idem) · `brand.md` (idem) |
| Architecture gates que deben seguir verdes | `tests/architecture/test_no_new_copilot_module_imports.py` (ratchet 22 frozen — cero cambio) · `test_sales_agent_tenant_isolation.py` · `test_sales_agent_observability_invariants.py` · `test_copilot_*_invariants.py` · `test_folder_naming.py` · DDD boundary tests (cero import cross-module nuevo). Allowlists shrink only |
| Architecture gates nuevos (allowlist ratchet inicial) | `test_outbox_invariants.py` (sin allowlist — toda query `domain_event_outbox` filtra `tenant_id`) · `test_idempotency_used_at_webhooks.py` (allowlist inicial = call sites legacy hoy sin idempotencia, poblada por builder tras `grep -rn "@router.post.*webhooks"`) |

**Riesgo principal:** 38 call sites `EventBus.publish()` (verificado por architect via `grep -rn "EventBus\.publish"`, excluyendo self-references en `events.py` y comments). Mitigación = feature flags OFF default + adapter con **single API** que internamente rutea sync/async (decisión Q4 PM). PR-1 ship cero cutover. Cutover incremental por módulo emisor (Q2 PM resolved — orden: sales_agent → copilot → brand → resto).

**Sub-deliverable adicional (PM decisión Q3): cleanup oportunista `extraction_card_flow.py:68-77`.** Migración del Redis SETEX ad-hoc al `@idempotent` decorator INCLUIDA en PR-1 (zero deuda técnica policy de Chris). Detalle § 4.D.

**Out of scope CONTRACT (decisiones diferidas):**
- DLQ + circuit breaker (S2)
- Backfill eventos in-memory pre-existentes (no aplica — outbox arranca vacía)
- ARQ worker dedicado fuera dispatcher (S2 `CampaignExecutionWorker`)
- Streamlit admin /outbox (no necesario — observabilidad via `*_trace_event` + `domain_event_outbox` queries directas)
- Migrar 38 sites legacy a `AsyncSession` (catastrófico — ver Q4 architect rationale § 1.A.5)

---

## 1. Sub-deliverable A — Outbox pattern

### 1.A.1 Domain entity (Python, pure, no SQLA)

```python
# backend/src/shared/domain_events/outbox/domain/event.py
"""Re-export DomainEvent + typed events from legacy path. Single SSoT."""
# Mueve `DomainEvent` + 14 typed events desde shared/domain/events.py acá.
# Path legacy queda como shim re-export (anti-rotura tests existentes).
```

```python
# backend/src/shared/domain_events/outbox/domain/outbox_entry.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class OutboxStatus(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"  # max_retries exceeded — manual ops


@dataclass(slots=True)
class OutboxEntry:
    """Domain entity. No framework deps. Persisted via OutboxRepository."""

    id: UUID
    tenant_id: UUID
    event_name: str
    payload: dict[str, Any]
    idempotency_key: str  # NUNCA None. Default = f"{event_name}:{uuid4()}" si caller no provee
    status: OutboxStatus
    retry_count: int
    last_error: str | None
    created_at: datetime
    dispatched_at: datetime | None

    @classmethod
    def from_event(
        cls,
        event: DomainEvent,
        idempotency_key: str | None = None,
    ) -> "OutboxEntry":
        return cls(
            id=uuid4(),
            tenant_id=event.tenant_id,
            event_name=event.event_name,
            payload=event.payload,
            idempotency_key=idempotency_key or f"{event.event_name}:{uuid4()}",
            status=OutboxStatus.PENDING,
            retry_count=0,
            last_error=None,
            created_at=datetime.now(UTC),
            dispatched_at=None,
        )
```

**Invariantes:**
- `tenant_id` NEVER NULL (toda query filtra).
- `idempotency_key` unique con `tenant_id` (dedupe at-least-once → exactly-once efectivo).
- `status` solo transita PENDING → DISPATCHED o PENDING → FAILED.
- Sin soft-delete (tabla operacional, retention via worker — diferido S2).

### 1.A.2 SQLAlchemy 2.0 model

```python
# backend/src/shared/domain_events/outbox/infrastructure/models.py
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Integer, Text, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class DomainEventOutboxModel(Base):
    """Persistent outbox for cross-module domain events (S0.1 PI-1)."""

    __tablename__ = "domain_event_outbox"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_outbox_tenant_idem"),
        Index("ix_outbox_pending", "status", "created_at"),  # dispatcher claim
        Index("ix_outbox_tenant_created", "tenant_id", "created_at"),  # ops/audit
    )
```

**Naming convention:** tabla `domain_event_outbox` (NO prefijo `shared_`. Es cross-module por diseño — `shared/` no es un módulo de negocio).

### 1.A.3 Repository interface (async, tenant-scoped)

```python
# backend/src/shared/domain_events/outbox/infrastructure/repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain_events.outbox.domain.outbox_entry import OutboxEntry, OutboxStatus


class OutboxRepository(ABC):
    """Async, tenant-scoped. Toda operación filtra tenant_id."""

    @abstractmethod
    async def append(self, entry: OutboxEntry, *, session: AsyncSession) -> None:
        """Insert dentro de la transacción del session pasado.

        Caller responsable de commit. ON CONFLICT (tenant_id, idempotency_key)
        → log warning + skip (idempotency dedupe).
        """

    @abstractmethod
    async def claim_pending(
        self,
        *,
        batch_size: int,
        session: AsyncSession,
    ) -> Sequence[OutboxEntry]:
        """SELECT ... FOR UPDATE SKIP LOCKED.

        Cross-tenant read (worker scope). Returns entries con status=pending
        ordenadas por created_at ASC. Batch_size ≤ 100 (default 50).
        """

    @abstractmethod
    async def mark_dispatched(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Update status=dispatched + dispatched_at=now. Tenant-scoped."""

    @abstractmethod
    async def mark_failed(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        error: str,
        session: AsyncSession,
    ) -> None:
        """Increment retry_count + set last_error.

        Si retry_count >= MAX_RETRIES (5) → status=failed (manual ops).
        Si <= MAX_RETRIES → keep status=pending (re-queue).
        """

    @abstractmethod
    async def get_by_id(
        self,
        entry_id: UUID,
        tenant_id: UUID,  # MANDATORY (regla tenant-isolation)
        *,
        session: AsyncSession,
    ) -> OutboxEntry | None: ...
```

**Implementación concreta:** `OutboxRepositoryImpl(OutboxRepository)` en `infrastructure/repository.py`.

### 1.A.4 Application service — `OutboxService.enqueue()`

```python
# backend/src/shared/domain_events/outbox/application/outbox_service.py
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.domain_events.outbox.domain.event import DomainEvent
from src.shared.domain_events.outbox.domain.outbox_entry import OutboxEntry
from src.shared.domain_events.outbox.infrastructure.repository import OutboxRepository


class OutboxService:
    """SSoT enqueue API. Builder + adapter consumen este path."""

    def __init__(self, repo: OutboxRepository) -> None:
        self._repo = repo

    async def enqueue(
        self,
        event: DomainEvent,
        *,
        session: AsyncSession,
        idempotency_key: str | None = None,
    ) -> None:
        """Insert outbox entry dentro de la transacción del session pasado.

        Comportamiento:
        - **Always requires session.** Sin session → ValueError. Filosofía:
          el outbox solo tiene sentido transaccional. Para fire-and-forget
          (sin DB context), publisher debe usar EventBusAdapter modo "legacy"
          (in-memory direct dispatch).
        - Idempotency:
          - Si caller pasa `idempotency_key` y colisiona (tenant_id, key)
            → log structlog warning + skip (no error). At-least-once
            con dedupe → exactly-once efectivo.
          - Si caller no pasa key → autogen `f"{event.event_name}:{uuid4()}"`
            (no dedupe protection, pero permite ops que no pueden inferir natural key).
        - Caller responsable de `await session.commit()`. OutboxService NO
          commitea (respeta unit-of-work del caller).

        NUNCA dispara handlers in-memory (eso lo hace OutboxDispatcher en otro proceso).
        """
        entry = OutboxEntry.from_event(event, idempotency_key=idempotency_key)
        await self._repo.append(entry, session=session)
```

**Decisión D1 (architect, refinada post-Q4):** `OutboxService` expone DOS métodos públicos: `enqueue_sync(event, *, session: Session, ...)` y `enqueue_async_from_sync_caller(event, *, session: AsyncSession, ...)`. Ambos requieren session mandatorio (sin session = ValueError). Caller con problema "no tengo DB context" debe usar adapter en modo legacy (immediate in-memory dispatch via flag OFF). Esto preserva la garantía atomicidad DB write + outbox INSERT.

El método 1.A.4 mostrado arriba (`async def enqueue(...)`) es **internal helper** para shared logic — NO se llama directamente. Builder implementa los 2 métodos públicos delegando a un constructor interno común que arma `OutboxEntry.from_event(...)` y delega al repo apropiado.

### 1.A.5 EventBusAdapter — compat layer 38 call sites (single-API, Q4 PM resolved)

```python
# backend/src/shared/domain_events/outbox/application/event_bus_adapter.py
from __future__ import annotations
from typing import Any
from src.core.config import settings
from src.shared.domain_events.outbox.application.outbox_service import OutboxService
from src.shared.domain_events.outbox.domain.event import DomainEvent
from src.shared.domain.events import EventBus as LegacyEventBus  # in-memory dispatcher


class EventBusAdapter:
    """Compat shim. EXPORTED como `EventBus` desde shared/domain/events.py shim.

    Reemplaza llamadas legacy `EventBus.publish(event, session=...)` en 38 sites
    SIN tocar call sites. **Single API** (Q4 PM resolved). Comportamiento
    controlado por feature flag por *módulo emisor*.

    ## Q4 PM decision — single-API path (zero deuda técnica)

    PM (Chris) instructed: zero technical debt, no dual API. Architect evaluated:

    **Opción A (rechazada):** Migrate ALL 38 call sites a `AsyncSession`/`publish_async`.
    Counted: 38 sites distribuidos en brand (5), social_proof (12), crm (1), copilot
    (8), sales_agent (8), connections (2), scheduling (1), offer (2). De los cuales
    >75% usan `Session` (sync) — verificado por grep `from sqlalchemy.orm import Session`
    en social_proof/* (todos sync), brand/api/* (todos sync), crm/* (sync). Migrar
    a async = catastrophic rewrite (~half codebase). Out-of-scope PR-1.

    **Opción B (elegida) — single-API con sync→async bridge interno:**
    - **Public surface:** SOLO `publish(event, session=None, *, module=None, idempotency_key=None)`.
      Sync method, retorna `None`. Identical signature to legacy `EventBus.publish`.
    - **Internal routing:** flag OFF → legacy in-memory dispatch (zero change).
      Flag ON → bridge interno: `_enqueue_via_sync_bridge(event, session, ...)` ejecuta
      el outbox INSERT via la misma `Session` sync que pasó el caller (psycopg2-binary
      driver — ver `requirements-runtime.txt:psycopg2-binary==2.9.9`).
    - **Bridge mechanism:** `OutboxRepositoryImpl` expone DOS métodos `append`:
      `append_sync(entry, *, session: Session)` y `append_async(entry, *, session: AsyncSession)`.
      Adapter detecta `isinstance(session, AsyncSession)` y delega al método correcto.
      Misma transacción del caller, after-commit hook (idéntico semantic legacy bus
      después-commit dispatch).
    - **Async sites futuros:** caller pasa `AsyncSession` → adapter rutea a `append_async`.
      Sin signature dual. Mismo `publish()`.
    - **NO `publish_async`.** Single signature. Sites async usan `publish()` desde
      contexto async (Python permite llamar método sync — adapter NO `await` outbox call,
      el INSERT ocurre dentro del session sync/async pasado).

    ## Bridge atomicity guarantee

    Outbox INSERT y after-commit dispatch USAN la misma session/transacción del caller.
    Si caller hace `session.commit()`, INSERT outbox se commitea atómicamente con el
    write principal. Después del commit, ARQ dispatcher (otro proceso, otro session)
    claim_pending lo recoge. `EventBus.publish` NUNCA hace commit propio.

    Trade-off documentado: si flag ON + caller olvida commit → outbox row nunca persiste
    (rolled back con la transacción del caller). Esto es CORRECTO — outbox es solo
    tan durable como el write principal del caller. Atomicity > best-effort.

    ## Flag mechanism (D5 sin cambio post-Q4)

    Env var via Pydantic Settings (NO tabla `feature_flags`):
    - USE_OUTBOX_PATTERN_SALES_AGENT (default "0")
    - USE_OUTBOX_PATTERN_COPILOT     (default "0")
    - USE_OUTBOX_PATTERN_BRAND       (default "0")
    - USE_OUTBOX_PATTERN_DEFAULT     (default "0")

    PR-1 ship TODAS OFF. Cutover Q2 = 1 PR per módulo (sales_agent → copilot → brand).
    """

    def __init__(self, outbox_service: OutboxService | None = None) -> None:
        # Singleton-style — instanciado UNA vez en startup wiring
        self._outbox = outbox_service

    @staticmethod
    def subscribe(event_name: str, handler: Any) -> None:  # noqa: ANN401
        """Backwards-compat — delega a in-memory bus. Subscribers in-memory
        siguen funcionando para call sites con flag OFF."""
        LegacyEventBus.subscribe(event_name, handler)

    def publish(
        self,
        event: DomainEvent,
        session: Any | None = None,  # noqa: ANN401 (sync OR async session OR None)
        *,
        module: str | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        """Single API publish. Identical signature al legacy `EventBus.publish`.

        Behavior matrix:
        | flag ON  | session         | path                                              |
        |----------|-----------------|---------------------------------------------------|
        | no       | any             | LegacyEventBus.publish (zero change)              |
        | yes      | sync Session    | _enqueue_via_sync_bridge (INSERT via sync session)|
        | yes      | AsyncSession    | _enqueue_via_async_bridge (INSERT via async session)|
        | yes      | None            | log warning + LegacyEventBus.publish (no DB ctx) |

        Caller responsable de commit. After-commit hook (existente legacy bus pattern)
        se preserva: outbox INSERT NO dispara handlers in-memory. Dispatcher worker
        (otro proceso) hace ese trabajo.
        """
        if not self._is_outbox_enabled(module):
            LegacyEventBus.publish(event, session=session)
            return

        # Flag ON path
        if session is None:
            # Sin DB context — outbox sin sentido. Fallback in-memory + warn.
            import structlog
            structlog.get_logger(__name__).warning(
                "outbox_skip_no_session",
                event_name=event.event_name,
                module=module,
            )
            LegacyEventBus.publish(event, session=None)
            return

        assert self._outbox is not None
        if _is_async_session(session):
            # Async path — caller en contexto async. NO podemos `await` desde sync method.
            # Solución: caller debe estar en contexto async ya, así que adapter delega
            # via `asyncio.get_event_loop().create_task(...)` SI hay loop, sino raise.
            # Sites async hoy = 0 (verificado architect). PR-1 ship sin async sites
            # — esta rama ejecuta solo cuando builder/PR siguiente migre el primer site.
            self._outbox.enqueue_async_from_sync_caller(
                event,
                session=session,
                idempotency_key=idempotency_key,
            )
            return

        # Sync path — Session legacy (psycopg2). 75%+ de los 38 sites caen acá.
        self._outbox.enqueue_sync(
            event,
            session=session,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _is_outbox_enabled(module: str | None) -> bool:
        if module is None:
            return settings.USE_OUTBOX_PATTERN_DEFAULT
        flag_attr = f"USE_OUTBOX_PATTERN_{module.upper()}"
        return getattr(settings, flag_attr, settings.USE_OUTBOX_PATTERN_DEFAULT)


def _is_async_session(session: Any) -> bool:  # noqa: ANN401
    from sqlalchemy.ext.asyncio import AsyncSession
    return isinstance(session, AsyncSession)
```

**Decisión D5 (architect — flag mechanism, sin cambio post-Q4):** Env var via Pydantic Settings, NO tabla `feature_flags`. Pattern consistente con `RUN_LLM_JUDGE`, `COPILOT_RECURSION_LIMIT`.

**Decisión D6 (architect — single-API + dual internal bridge, RESOLVED Q4):** call sites legacy preservan signature exacta `publish(event, session=)`. NO `publish_async`. Adapter internamente detecta sync vs async session y delega a `OutboxRepositoryImpl.append_sync()` o `.append_async()`. Beneficio: cero refactor en 38 sites. Migración a async es **opcional** y per-site (cuando se requiera por otro motivo, no por outbox).

**Decisión D7 (architect — module detection):** publishers pasan `module="sales_agent"|"copilot"|"brand"` kwarg explícito en flip de flag. Call sites legacy SIN module kwarg → fallback `USE_OUTBOX_PATTERN_DEFAULT` (= OFF). Cuando builder flippea flag (Q2 cutover), agrega `module=` al call site (1 línea por site).

**Decisión D6.1 (architect — `OutboxService` dual entry point):** `OutboxService` expone:
- `enqueue_sync(event, *, session: Session, idempotency_key=None) -> None` — para 75%+ sites sync.
- `enqueue_async_from_sync_caller(event, *, session: AsyncSession, idempotency_key=None) -> None` — schedule INSERT via `asyncio.get_event_loop().create_task` (caller already en async ctx).
- (NO public `enqueue` async genérico — atomicity surface más controlada con dual entry).

`OutboxRepositoryImpl` mirror: `append_sync` (uses `Session.execute`) + `append_async` (uses `await AsyncSession.execute`). Misma SQL.

### 1.A.6 OutboxDispatcher — ARQ worker

```python
# backend/src/shared/domain_events/outbox/infrastructure/dispatcher.py
"""Outbox dispatcher worker.

Decisión D8 (architect, RESOLVED Q1 PM): ARQ worker con cron 1-second
(`second={0,1,2,...,59}` — 60 ticks/min). Latency p99 ~1.5s entre commit y dispatch.

## Q1 PM resolution: industry standard + sin deuda + low latency

PM (Chris) instructed: state-of-the-art Apr 2026 for outbox+ARQ stack. Architect
evaluated **3 paths**:

### Path A — Pure cron 1s (ELEGIDA)
- ARQ scheduler: `cron(dispatch_outbox, second=set(range(60)))` (1 tick/sec).
- Latency: p50 0.5s, p99 1.5s, peak 2s.
- Stack consistency 100%: ARQ ya usado para 22+ tasks (retention/cost_alerts/scheduler/
  quality_eval). No new infra. No new dep.
- Cost: 60 SELECT queries/min/worker. Index `ix_outbox_pending` (partial WHERE status='pending')
  → cuando outbox empty, query <1ms. Negligible Postgres load.
- Multi-worker safe: `FOR UPDATE SKIP LOCKED` (Postgres 16+).
- Failure recovery: dispatcher dies mid-batch → uncommitted rows reclaimed next tick.

### Path B — Postgres LISTEN/NOTIFY (DESCARTADA — no zero-debt)
Industry research (2026) confirma LISTEN/NOTIFY es state-of-the-art para REAL-TIME
push semantics, PERO con caveats:
- **Driver dependency:** asyncpg requerido (psycopg2 sync no soporta LISTEN bien
  en async event loop). Codebase usa `psycopg2-binary==2.9.9` (sync) — agregar
  asyncpg = NEW infra dependency = NOT zero-debt (introduce dual-driver complexity).
- **NON-DURABLE signaling:** Postgres docs explícito + industry consensus 2026
  (ThinhDA/asyncpg-listen) — LISTEN/NOTIFY notifications are LOST si listener
  desconectado al momento NOTIFY. Cannot replace polling como SSoT durability.
- **Hybrid pattern (LISTEN + cron safety net):** state-of-the-art real es híbrido,
  no pure LISTEN. Pero hybrid = 2 codepaths = más superficie de tests + más complejidad
  para PR-1.
- **PG side limits:** NOTIFY locks `pg_notify` queue at session-level → en escenarios
  high-throughput puede degradar. Para nuestro volume (eventos esporádicos) overkill.

Conclusión: **LISTEN/NOTIFY = future PR cuando migremos a asyncpg como driver
unificado** (proyecto separado, scope grande). PR-1 cron 1s = decisión zero-debt.

### Path C — In-process scheduler dentro FastAPI app (DESCARTADA)
- Acoplaría dispatcher al lifecycle de api process.
- Multi-pod = N dispatchers concurrent = race en SKIP LOCKED safe pero overhead.
- Pierde escalabilidad ARQ (worker pool dedicado).

## Path A details

Razones específicas:
- Stack consistency total. Cero new dep. Cero new pattern.
- 1s latency cubre TODOS los use cases identificados:
  - extraction nav pill (FE espera "instantaneous"): 1s OK (FE ya tolera streaming SSE delays >500ms).
  - brand_summary regen (60s debounce existente): 1s irrelevante.
  - schedule_payment_followup: timing horario (no segundos).
  - personality_profile cache invalidation: 1s OK (cache miss en next turn).
- Zero-debt path. Si futuro necesita p99 <100ms, migración a LISTEN/NOTIFY = proyecto
  separado con asyncpg driver migration (no acumula deuda en PR-1).

Cost guard: 60 ticks/min/worker, query partial-index <1ms cuando empty → ~0.06s CPU/min/worker
de dispatcher overhead. Negligible vs ETL/scheduler load actual.

Pseudo-code (NO implementación — builder escribe):

async def dispatch_outbox(ctx: dict) -> None:
    db_factory = ctx["db_factory"]
    async with db_factory() as session:
        repo = OutboxRepositoryImpl(session)
        entries = await repo.claim_pending(batch_size=50, session=session)
        for entry in entries:
            try:
                # Reconstruct DomainEvent + dispatch via in-memory bus
                event = _entry_to_event(entry)
                LegacyEventBus._dispatch(event)  # in-process subscribers
                await repo.mark_dispatched(entry.id, entry.tenant_id, session=session)
            except Exception as e:
                # Exponential backoff: retry_count contributes to next attempt
                # delay (PR-2 si timing matters). PR-1 retry inmediato next batch.
                await repo.mark_failed(entry.id, entry.tenant_id, error=str(e)[:500], session=session)
        await session.commit()
"""
```

**Claim semantics:** `SELECT ... FROM domain_event_outbox WHERE status='pending' ORDER BY created_at ASC LIMIT :batch_size FOR UPDATE SKIP LOCKED`. Multiple worker instances seguros — ningún claim duplicado.

**Retry policy:**
- max_retries = 5 (env var `OUTBOX_MAX_RETRIES`, default 5).
- Exponential backoff DIFERIDO a PR-2 (PR-1 retry inmediato next cron tick = 1s — falló a falló <1s sostenido es rare; si ocurre, S2 introduce backoff).
- Después max_retries → `status='failed'`. PR-1 = manual ops (`UPDATE ... SET status='pending'` manual). DLQ S2.

**Worker registration en `backend/src/workers/settings.py`:**
- Add `dispatch_outbox` a `WorkerSettings.functions` + `SchedulerSettings.functions`.
- Add cron en `SchedulerSettings.cron_jobs`: `cron(dispatch_outbox, second=set(range(60)))` (1 tick/segundo, 60 ticks/min).

### 1.A.7 Migration 109 — outbox + campaign observability

```python
# backend/alembic/versions/109_add_domain_event_outbox_and_campaign_observability.py
"""Outbox table + campaign observability tables (PI-1 S0 PR-1).

Idempotente raw SQL `IF NOT EXISTS` (regla backend-migrations.md).

Revision ID: 109_add_domain_event_outbox_and_campaign_observability
Revises: 082_sales_agent_workflow_metric  # ⚠️ verificar head antes commit
Create Date: 2026-04-29
"""
from alembic import op

revision = "109_add_domain_event_outbox_and_campaign_observability"
down_revision = "082_sales_agent_workflow_metric"  # builder verifica head actual
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── domain_event_outbox ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS domain_event_outbox (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            event_name VARCHAR(128) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key VARCHAR(256) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            dispatched_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_tenant_idem
        ON domain_event_outbox (tenant_id, idempotency_key)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_outbox_pending
        ON domain_event_outbox (status, created_at)
        WHERE status = 'pending'
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_outbox_tenant_created
        ON domain_event_outbox (tenant_id, created_at DESC)
    """)

    # ── campaign_llm_call ───────────────────────────────────────────────
    # Mirror semántico sales_agent_llm_call (078_*.py) + has_lead_id=True.
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_llm_call (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            role VARCHAR(32) NOT NULL,
            provider VARCHAR(32) NOT NULL,
            model_requested VARCHAR(128) NOT NULL,
            model_responded VARCHAR(128) NOT NULL,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            cached_read_tokens INTEGER NOT NULL DEFAULT 0,
            cached_write_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            pricing_version_id UUID NOT NULL,
            input_unit_cost_usd NUMERIC(14,12) NOT NULL,
            output_unit_cost_usd NUMERIC(14,12) NOT NULL,
            cached_read_unit_cost_usd NUMERIC(14,12) NOT NULL DEFAULT 0,
            cost_usd NUMERIC(16,10) NOT NULL,
            tenant_currency CHAR(3),
            fx_rate_to_tenant NUMERIC(16,8),
            fx_rate_source VARCHAR(32),
            cost_tenant_currency NUMERIC(16,8),
            started_at TIMESTAMPTZ NOT NULL,
            duration_ms INTEGER NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            error_type VARCHAR(64),
            occurred_on DATE GENERATED ALWAYS AS ((started_at AT TIME ZONE 'UTC')::date) STORED,
            occurred_year_month VARCHAR(7) GENERATED ALWAYS AS (
                EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')::INT::TEXT
                || '-'
                || LPAD(EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')
            ) STORED
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_tenant_day
        ON campaign_llm_call (tenant_id, occurred_on)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_lead
        ON campaign_llm_call (tenant_id, lead_id, started_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_turn
        ON campaign_llm_call (turn_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_tenant_model_day
        ON campaign_llm_call (tenant_id, model_responded, occurred_on)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_errors
        ON campaign_llm_call (tenant_id, started_at DESC)
        WHERE status = 'error'
    """)

    # ── campaign_trace_event ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_trace_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            event_type VARCHAR(32) NOT NULL,
            name VARCHAR(128),
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            duration_ms INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_lead
        ON campaign_trace_event (tenant_id, lead_id, created_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_turn
        ON campaign_trace_event (turn_id, created_at)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_tenant_time
        ON campaign_trace_event (tenant_id, created_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_errors
        ON campaign_trace_event (tenant_id, created_at DESC)
        WHERE status = 'error'
    """)


def downgrade() -> None:
    """Explicit NO-OP — outbox + observability data is operational, never dropped."""
```

**Verificación builder antes del commit (regla `backend-migrations.md`):**
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 082_sales_agent_workflow_metric && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

### 1.A.8 Legacy shim (anti-rotura tests existentes)

```python
# backend/src/shared/domain/events.py  (después PR-1)
"""DEPRECATED path. Re-export desde shared/domain_events/outbox/domain/event.py.

Mantiene API pública (DomainEvent, EventBus, typed events) para 41 call sites.
Tests existentes (test_event_bus.py, test_*_event_handlers.py) NO rompen.

Cutover real: cuando flag USE_OUTBOX_PATTERN_<MODULE>=1 en módulo, EventBus
actúa como EventBusAdapter (delega a outbox). Cuando OFF, comportamiento legacy.

Plan retiro shim: post-S2 cuando todos call sites migrados.
"""
from src.shared.domain_events.outbox.domain.event import (  # noqa: F401
    DomainEvent,
    SaleCompletedEvent,
    ChurnEvent,
    LeadCapturedEvent,
    ExtractionSectionCompletedEvent,
    ExtractionJobCompletedEvent,
    BrandSectionUpdatedEvent,
    PersonalityProfileUpdatedEvent,
    AppointmentEvent,
    BookingLinkCreatedEvent,
    BookingMissedEvent,
    PaymentLinkCreatedEvent,
    PaymentReceivedEvent,
    AccessGrantedEvent,
    CHANNEL_TYPE_TO_CAPTURE_SLUG,
)
from src.shared.domain_events.outbox.application.event_bus_adapter import (  # noqa: F401
    EventBusAdapter as EventBus,  # alias backwards-compat
)
```

---

## 2. Sub-deliverable B — IdempotencyStore

### 2.B.1 Domain VO

```python
# backend/src/shared/idempotency/domain/key.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """Value Object — clave dedupe Redis-backed.

    Format storage Redis: f"idem:{namespace}:{key}".
    """

    namespace: str  # ej. "webhook:manychat", "webhook:meta", "tool:create_payment_link"
    key: str        # natural key del request (ej. webhook signature, tool deterministic input hash)
    ttl_seconds: int = 86400  # 24h default

    @property
    def storage_key(self) -> str:
        return f"idem:{self.namespace}:{self.key}"

    def __post_init__(self) -> None:
        if not self.namespace or ":" in self.namespace:
            raise ValueError("namespace requerido y no contiene ':'")
        if not self.key:
            raise ValueError("key requerido")
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds > 0")
```

### 2.B.2 Infrastructure — Redis store

```python
# backend/src/shared/idempotency/infrastructure/redis_store.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


class IdempotencyStore(ABC):
    @abstractmethod
    async def claim(self, key: "IdempotencyKey") -> bool: ...
    """Atomic SETNX with TTL. Returns True si claim exitoso (first call),
    False si key ya existe (repeated call → use cached_result)."""

    @abstractmethod
    async def cached_result(self, key: "IdempotencyKey") -> dict[str, Any] | None: ...
    """Returns cached payload si previously stored. None si no hay."""

    @abstractmethod
    async def store_result(
        self,
        key: "IdempotencyKey",
        result: dict[str, Any],
    ) -> None: ...
    """Persiste resultado mínimo (id + status) para repeats. NO full payload."""


class RedisIdempotencyStore(IdempotencyStore):
    """Redis-backed. Soft-fail si Redis unavailable (regla R5)."""

    def __init__(self, redis_client: Any) -> None:  # noqa: ANN401
        self._redis = redis_client

    async def claim(self, key: "IdempotencyKey") -> bool:
        if self._redis is None:
            logger.warning("idempotency_redis_unavailable_softfail", namespace=key.namespace)
            return True  # permitir ejecución, log warning
        # SET NX EX → atomic claim
        result = self._redis.set(key.storage_key, "1", nx=True, ex=key.ttl_seconds)
        return bool(result)

    async def cached_result(self, key: "IdempotencyKey") -> dict[str, Any] | None:
        if self._redis is None:
            return None
        raw = self._redis.get(f"{key.storage_key}:result")
        if not raw:
            return None
        import json
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    async def store_result(
        self,
        key: "IdempotencyKey",
        result: dict[str, Any],
    ) -> None:
        if self._redis is None:
            return
        import json
        self._redis.setex(
            f"{key.storage_key}:result",
            key.ttl_seconds,
            json.dumps(result),
        )
```

**Decisión D9 (architect — soft-fail Redis):** si Redis unavailable → log warning + permitir ejecución (better double-process que pérdida). Trade-off documentado. Aplica regla `tessl/graceful-degradation`.

**Decisión D10 (architect — cached result shape):** solo `{"id": str, "status": str}` (≤256 bytes). NO full webhook payload. Webhooks duplicados solo necesitan saber "ya procesé esto, devolveme el id". Full payload replay = anti-pattern.

### 2.B.3 Application — `@idempotent` decorator

```python
# backend/src/shared/idempotency/application/decorator.py
from __future__ import annotations
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar
import structlog

from src.shared.idempotency.domain.key import IdempotencyKey
from src.shared.idempotency.infrastructure.redis_store import IdempotencyStore

P = ParamSpec("P")
R = TypeVar("R")
logger = structlog.get_logger(__name__)


def idempotent(
    *,
    namespace: str,
    key_fn: Callable[..., str],
    ttl: int = 86400,
    store_factory: Callable[[], IdempotencyStore] | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator. Usage:

        @idempotent(
            namespace="webhook:manychat",
            key_fn=lambda req: req.headers.get("X-Signature", ""),
            ttl=86400,
        )
        async def manychat_webhook(req: Request) -> dict: ...

    Behavior:
    - First call: claim succeeds → execute func → store result → return
    - Repeat call (key matches): claim fails → return cached_result if any
    - Cached result missing (TTL expired between claim and result store):
      log warning + execute again (double-process aceptable)
    - Redis down: log warning + execute (soft-fail).

    NUNCA muta el contract de la función decorada.
    """
    def deco(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Resolve store (lazy — DI for tests)
            store = (store_factory or _default_store_factory)()
            raw_key = key_fn(*args, **kwargs)
            if not raw_key:
                logger.warning(
                    "idempotency_empty_key_skip",
                    namespace=namespace,
                    func=func.__name__,
                )
                return await func(*args, **kwargs)

            ikey = IdempotencyKey(namespace=namespace, key=raw_key, ttl_seconds=ttl)
            claimed = await store.claim(ikey)
            if not claimed:
                cached = await store.cached_result(ikey)
                if cached is not None:
                    logger.info(
                        "idempotency_cache_hit",
                        namespace=namespace,
                        func=func.__name__,
                    )
                    return cached  # type: ignore[return-value]
                # claim conflict but no cached → race condition, execute (soft-fail)
                logger.warning(
                    "idempotency_claim_lost_no_cache",
                    namespace=namespace,
                    func=func.__name__,
                )

            result = await func(*args, **kwargs)

            # Store minimal projection (id + status). Caller responsable
            # devolver dict serializable.
            if isinstance(result, dict):
                projected = {
                    k: result[k]
                    for k in ("id", "status", "external_id")
                    if k in result
                }
                if projected:
                    await store.store_result(ikey, projected)
            return result
        return wrapper
    return deco


def _default_store_factory() -> IdempotencyStore:
    from src.core.database import redis_client
    return RedisIdempotencyStore(redis_client)
```

**Decisión D11 (architect — projected result, no full payload):** stored result = subset `{id, status, external_id}`. Razones (alineado D10):
- Webhooks externos no necesitan replay full body, solo saber "id ya procesado".
- Tamaño Redis controlado (≤256 bytes/key).
- Evita PII leak en Redis (full payload puede contener email/phone).

### 2.B.4 Service helper (lock-and-execute alternativa imperativa)

```python
# backend/src/shared/idempotency/application/service.py
"""Imperative API para sites que no pueden usar decorator (ej. tool dispatch)."""
from src.shared.idempotency.domain.key import IdempotencyKey
from src.shared.idempotency.infrastructure.redis_store import IdempotencyStore


class IdempotencyService:
    def __init__(self, store: IdempotencyStore) -> None:
        self._store = store

    async def with_dedupe(
        self,
        key: IdempotencyKey,
        func: "Callable[[], Awaitable[dict]]",
    ) -> dict:
        """Equivalente decorator pero ejecutable via DI/composition."""
        claimed = await self._store.claim(key)
        if not claimed:
            cached = await self._store.cached_result(key)
            if cached is not None:
                return cached
        result = await func()
        if isinstance(result, dict):
            projected = {k: result[k] for k in ("id", "status", "external_id") if k in result}
            if projected:
                await self._store.store_result(key, projected)
        return result
```

---

## 3. Sub-deliverable C — `agent_kind="campaign"` registration

### 3.C.1 Module bootstrap

```python
# backend/src/modules/campaigns/observability/__init__.py
"""Campaigns observability — placeholder spec registration (PI-1 S0 PR-1).

Registers agent_kind="campaign" en shared/agent_observability/registry.py.
Tablas campaign_llm_call + campaign_trace_event creadas en migration 109.

PR-1: solo registration. Callback handler + persisters = S2 (cuando
CampaignExecutionWorker invoque LLM real). Tablas vacías hasta entonces.
UNION-ALL view en mv_daily_llm_cost_per_tenant_v2 ya las contempla
automáticamente vía registry.
"""
from __future__ import annotations

from src.modules.campaigns.observability.persistence.models.llm_call_model import (
    CampaignLlmCallModel,
)
from src.shared.agent_observability.registry import (
    AgentObservabilitySpec,
    register_agent_observability,
)

register_agent_observability(
    AgentObservabilitySpec(
        agent_kind="campaign",
        llm_call_model=CampaignLlmCallModel,
        trace_event_table="campaign_trace_event",
        llm_call_table="campaign_llm_call",
        trace_retention_env_var="CAMPAIGN_TRACE_RETENTION_DAYS",
        llm_call_retention_env_var="CAMPAIGN_LLM_CALL_RETENTION_DAYS",
        trace_default_days=30,   # PR-1 retention bajo (campaigns aún sin uso prod)
        llm_call_default_days=90,  # PR-1 retention bajo (S2 evalúa subir)
        has_lead_id=True,  # campaign tasks per lead
    ),
)
```

### 3.C.2 SQLAlchemy model — `CampaignLlmCallModel`

```python
# backend/src/modules/campaigns/observability/persistence/models/llm_call_model.py
"""Mirror estructural de SalesAgentLlmCallModel (sales_agent/observability/.../llm_call_model.py).

Columnas idénticas — mismo schema. Solo cambia table_name.
PR-1 sin escrituras (placeholder); S2 wireup CampaignCallbackHandler.
"""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Integer, Numeric, DateTime, CHAR, Computed
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignLlmCallModel(Base):
    __tablename__ = "campaign_llm_call"

    # Schema exacto = sales_agent_llm_call (ver migration 078). Builder mirror.
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    turn_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    span_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    parent_span_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_requested: Mapped[str] = mapped_column(String(128), nullable=False)
    model_responded: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached_write_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasoning_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pricing_version_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    input_unit_cost_usd: Mapped = mapped_column(Numeric(14, 12), nullable=False)
    output_unit_cost_usd: Mapped = mapped_column(Numeric(14, 12), nullable=False)
    cached_read_unit_cost_usd: Mapped = mapped_column(Numeric(14, 12), nullable=False, default=0)
    cost_usd: Mapped = mapped_column(Numeric(16, 10), nullable=False)
    tenant_currency: Mapped[str | None] = mapped_column(CHAR(3))
    fx_rate_to_tenant: Mapped = mapped_column(Numeric(16, 8))
    fx_rate_source: Mapped[str | None] = mapped_column(String(32))
    cost_tenant_currency: Mapped = mapped_column(Numeric(16, 8))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")
    error_type: Mapped[str | None] = mapped_column(String(64))
    occurred_on: Mapped = mapped_column(
        Computed("(started_at AT TIME ZONE 'UTC')::date", persisted=True)
    )
    occurred_year_month: Mapped = mapped_column(String(7), Computed(
        "EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')::INT::TEXT || '-' || "
        "LPAD(EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')",
        persisted=True,
    ))
```

### 3.C.3 Bootstrap wiring

Add import al `src/shared/infrastructure/agent_observability_bootstrap.py`:

```python
# backend/src/shared/infrastructure/agent_observability_bootstrap.py
"""Cross-agent bootstrap. Importing this module registers all agent specs."""
import src.modules.copilot.observability  # noqa: F401
import src.modules.sales_agent.observability  # noqa: F401
import src.modules.campaigns.observability  # noqa: F401  ← PR-1 add
```

---

## 4. Sub-deliverable D — `extraction_card_flow.py` migration to `@idempotent` (Q3 PM resolved — IN-SCOPE PR-1)

**PM decision Q3:** Chris instructed zero-debt cleanup oportunista. Migración del Redis SETEX ad-hoc en `backend/src/modules/copilot/application/extraction_card_flow.py:68-77` al nuevo `@idempotent` decorator es **DENTRO de PR-1**.

### 4.D.1 Current state (lines 66-77)

```python
# CURRENT (ad-hoc Redis SETEX):
from src.core.database import redis_client

idempotency_key = f"extract_card:{job_id}:nav:{section_slug}"
if redis_client:
    if redis_client.get(idempotency_key):
        logger.debug(
            "nav_pill_duplicate_skipped",
            job_id=job_id,
            section_slug=section_slug,
        )
        return
    redis_client.setex(idempotency_key, 86400, "1")
```

Plus mirror pattern en `emit_extraction_summary_card()` (líneas ~235) con key `f"extract_card:{job_id}:summary"`.

### 4.D.2 Target migration

**Wrap ambas funciones (`emit_section_complete_pill`, `emit_extraction_summary_card`) con `@idempotent` decorator.** Eliminar el Redis SETEX manual. Behavior preservado byte-for-byte (mismo Redis backend, mismo TTL 86400, mismo key shape).

```python
# TARGET (decorator-based):
from src.shared.idempotency.application.decorator import idempotent

@idempotent(
    namespace="copilot:extract_card",
    key_fn=lambda *, job_id, section_slug, **_: f"nav:{job_id}:{section_slug}",
    ttl=86400,
)
def emit_section_complete_pill(
    *,
    db: object,
    tenant_id: UUID,
    conversation_id: UUID,
    job_id: str,
    section_slug: str,
    ...
) -> None:
    # Cuerpo SIN líneas 66-77. El decorator gestiona claim+cache.
    ...

@idempotent(
    namespace="copilot:extract_card",
    key_fn=lambda *, job_id, **_: f"summary:{job_id}",
    ttl=86400,
)
def emit_extraction_summary_card(...) -> None:
    ...
```

### 4.D.3 Safety verification (consulted `copilot-expert` skill)

`copilot-expert` SOP confirma:
- Funciones son **subscribers in-memory** del bus (callback-style). NO en hot path streaming.
- Idempotency hoy es Redis SETEX 24h TTL. Decorator preserva exact mismo backend (`RedisIdempotencyStore` usa mismo `redis_client` de `core.database`).
- Behavior change: NONE. Tests existentes (`tests/modules/copilot/test_extraction_card_flow.py` si existe, sino baseline goldens) deben pasar sin tocar.
- Trace recorder no afectado — funciones siguen emitiendo `CardEmitted` event al final (líneas 118-124).
- Spanish neutro — sin tocar copy user-facing (`page_label = f"✓ {section_label} lista · {fields_count} campos"` queda igual).

### 4.D.4 Migration steps (builder TDD-RED first)

1. **RED test:** `tests/modules/copilot/test_extraction_card_idempotency.py` (regression — duplicar call con mismo `job_id+section_slug` produce 1 sola emisión + 1 sola pill insertion).
2. Implementar §2 (IdempotencyStore + decorator). Sin esto el RED test no compila.
3. Modificar `extraction_card_flow.py:66-77` y `extraction_card_flow.py:~210-240` con decorators. Quitar SETEX manual.
4. Run regression suite: `cd backend && .venv/bin/pytest tests/modules/copilot/ -v`.
5. **Trace verification:** producir un evento `extraction_section_completed` 2x con mismo `job_id+section_slug` → 1 sola row en `copilot_trace_event` con `name='card_emitted'`. Sin esto, decorator está mal.

### 4.D.5 Allowlist impact

`test_idempotency_used_at_webhooks.py` allowlist es **only para webhooks** (`@router.post("/webhooks/...")`). Estas funciones NO son webhooks — son subscribers internos. NO entran al test allowlist (architect cross-checked § 7.3 + § 12).

**Sub-deliverable D commit message:** `refactor(copilot): migrate extraction_card_flow Redis SETEX → @idempotent decorator (PR-1 Q3)`. Stage solo `extraction_card_flow.py` + el test nuevo + el SSoT idempotency files.

---

## 5. API endpoints

**N/A** — PR-1 es infra cross-cutting. Cero endpoints API. (PR.md "Out of scope" + "Copilot-first checklist" confirman.)

---

## 6. TypeScript types (Frontend)

**N/A** — sin FE. (Sin UI, sin DTO consumido por FE en PR-1.)

---

## 7. Application Services — surface summary

| Service | API | Module | Test surface |
|---|---|---|---|
| `OutboxService.enqueue_sync(event, *, session: Session, idempotency_key)` | enqueue dentro tx sync, dedupe por (tenant, key) | `shared/domain_events/outbox/application/` | `test_outbox_service.py` (RED first) |
| `OutboxService.enqueue_async_from_sync_caller(event, *, session: AsyncSession, idempotency_key)` | enqueue dentro tx async (cuando se requiera) | `shared/domain_events/outbox/application/` | `test_outbox_service.py` |
| `EventBusAdapter.publish(event, session=None, *, module=None, idempotency_key=None)` | **SINGLE API.** Flag-routed: legacy in-mem vs outbox sync vs outbox async (Q4 PM) | `shared/domain_events/outbox/application/` | `test_event_bus_adapter.py` |
| `IdempotencyService.with_dedupe(key, func)` + `@idempotent` decorator | atomic SETNX + cached_result | `shared/idempotency/application/` | `test_decorator.py`, `test_idempotency_service.py` |
| `OutboxRepositoryImpl.append_sync` + `.append_async` | dual write methods (mismo SQL) + claim_pending (FOR UPDATE SKIP LOCKED) + mark_dispatched/failed + get_by_id (todos tenant-scoped) | `shared/domain_events/outbox/infrastructure/` | `test_outbox_repository.py` |
| `RedisIdempotencyStore` | claim/cached_result/store_result + soft-fail Redis-down | `shared/idempotency/infrastructure/` | `test_redis_store.py` |
| `dispatch_outbox` (ARQ task, **1 tick/segundo**) | claim batch → dispatch via legacy bus → mark dispatched/failed | `shared/domain_events/outbox/infrastructure/dispatcher.py` | `test_outbox_dispatcher.py` (kill+restart recovery scenario) |

---

## 8. Eventos / outbox flow

### 7.1 Eventos existentes que migran (sin cambio shape)

Los 14 typed events en `shared/domain/events.py` se mueven a `shared/domain_events/outbox/domain/event.py`. Shape NO cambia. Solo path. Tests de eventos pasan por re-export shim.

### 7.2 Producer/Consumer matrix (post-migración con flag ON)

| Event | Producer site | Consumer | Idempotency key strategy |
|---|---|---|---|
| `BrandSectionUpdatedEvent` | `brand_repository.py:85` | `regen_brand_summary` ARQ | `f"brand_section_updated:{tenant_id}:{occurred_at_minute}"` (debounce 60s — alineado regen worker existente) |
| `PaymentLinkCreatedEvent` | `sales_agent/.../payment/tools.py:165` | `schedule_payment_followup` | `f"payment_link_created:{external_id}"` (provider-issued, dedupe natural) |
| `PaymentReceivedEvent` | `sales_agent/.../payment/tools.py:369` + webhook | `auto_grant_on_paid` | `f"payment_received:{payment_id}"` |
| `BookingLinkCreatedEvent` | `sales_agent/.../scheduling/tools.py:136` | `schedule_booking_link_followup` | `f"booking_link_created:{tracking_id}"` |
| `ExtractionSectionCompletedEvent` | `copilot/.../extraction_card_flow.py:121` | nav pill emitter | `f"extract_section:{job_id}:{section_slug}"` (reemplaza ad-hoc Redis SETEX existente) |
| `ExtractionJobCompletedEvent` | `copilot/.../extraction_card_flow.py:235` | extraction_summary card | `f"extract_summary:{job_id}"` |
| `PersonalityProfileUpdatedEvent` | `personality_service.py:119` | sales_agent cache invalidation | `f"personality_updated:{profile_id}:{action}:{occurred_at_minute}"` |
| `AppointmentEvent`, `BookingMissedEvent`, `LeadCapturedEvent`, `SaleCompletedEvent`, `ChurnEvent`, `AccessGrantedEvent` | varios | varios | natural keys disponibles (ver create() de cada evento) |

**Decisión D12 (architect, refinada post-Q3):** PR-1 NO cambia 37 de los 38 call sites de `EventBus.publish` (siguen vía adapter compat shim, flag OFF default = comportamiento legacy intacto). **Excepción Q3:** `extraction_card_flow.py` 2 call sites NO de `EventBus.publish` sino de **idempotency Redis SETEX** se migran a `@idempotent` decorator (sub-deliverable § 4.D). Estrategia de idempotency_key per event documentada arriba sigue para que builder PR siguiente migre sites con keys deterministic + flippee flag por módulo.

### 7.3 Idempotency surfaces (webhooks externos)

| Webhook handler | Path | Idempotency key fn (sugerencia) | Status |
|---|---|---|---|
| `manychat_webhook` | `connections/api/marketing_webhooks.py` | `req.headers.get("X-Signature") or sha256(req.body)` | sin idempotencia HOY (R5 mitigación) |
| `meta_webhook` | `connections/api/marketing_webhooks.py` | Meta sends `entry[].id` natural key | sin idempotencia HOY |
| `mailerlite_webhook` | `connections/api/marketing_webhooks.py` | `event_id` from MailerLite payload | sin idempotencia HOY |
| `telegram_webhook` | `sales_agent/api/...` | `update_id` natural Telegram | sin idempotencia HOY |
| `payment_webhook` (mercadopago/stripe) | `sales_agent/api/payment_webhooks.py` | provider event `id` | sin idempotencia HOY |
| `scheduler_webhook` | `sales_agent/api/scheduler_webhooks.py` | provider event `id` | sin idempotencia HOY |
| `extraction_card` nav | `copilot/.../extraction_card_flow.py:68-77` | `f"extract_card:{job_id}:nav:{section_slug}"` | **MIGRA EN PR-1** (Q3 PM resolved — sub-deliverable § 4.D). Decorator-based, mismo Redis backend, mismo TTL |

**Allowlist test arch nuevo `test_idempotency_used_at_webhooks.py`:**
- AST scan: para cada `@router.post("/webhooks/...")` verifica `@idempotent` decorator presente.
- Allowlist inicial PR-1 = TODOS los call sites legacy (manychat/meta/mailerlite/telegram/payment/scheduler) — sin migración en PR-1, solo gate de no-regresión.
- Shrink only: PR siguiente migra uno-por-uno y elimina del allowlist.
- Builder pobla allowlist via `grep -rn "@router.post.*webhooks" backend/src/`.

---

## 9. Retry / idempotency policy

### Outbox retry
- Retry strategy: **inmediato next cron tick (10s)** en PR-1. Exponential backoff DIFERIDO PR-2.
- Max retries: 5 (env `OUTBOX_MAX_RETRIES`, default 5). Después → `status='failed'` (manual ops).
- DLQ: diferido S2.
- Last error: trunca a 500 chars en `last_error` column.

### Idempotency TTL
- Default: 86400s (24h). Env `IDEMPOTENCY_DEFAULT_TTL_SECONDS`.
- Per-namespace override: caller pasa `ttl=N` al decorator.
- Soft-fail Redis-down: log warning + execute (regla R5 mitigation).

### Circuit breaker
- N/A en PR-1. S2 cuando hay external API calls reales.

---

## 10. Tenant isolation

| Surface | Filter |
|---|---|
| `OutboxRepository.append` | requires entry.tenant_id NOT NULL |
| `OutboxRepository.claim_pending` | cross-tenant read **legítimo** (worker scope, marca pertenencia via entry.tenant_id en cada row claimed). Worker dispatch lookup tenant_id por entry — handlers in-memory pueden filtrar |
| `OutboxRepository.mark_dispatched/failed` | param `tenant_id` mandatorio (regla `tenant-isolation.md`) |
| `OutboxRepository.get_by_id` | `tenant_id` mandatorio param |
| `IdempotencyKey.namespace` | namespace patterns SHOULD include `tenant_id` cuando key no es naturalmente tenant-isolated. Ej. `f"webhook:manychat:{tenant_id}"` |
| `RedisIdempotencyStore` | Redis keyspace prefijado `idem:{namespace}:...`. Si namespace contiene tenant_id → tenant isolation natural |

**Architecture test gate `test_outbox_invariants.py`:** AST scan de `OutboxRepositoryImpl` verifica todo `select(DomainEventOutboxModel)` filtra `tenant_id` excepto `claim_pending` (allowlist explícito = 1 método).

---

## 11. Observability

### structlog campos clave
```python
# OutboxService.enqueue
logger.info("outbox_enqueued",
    tenant_id=str(event.tenant_id), event_name=event.event_name,
    idempotency_key=key, entry_id=str(entry.id))

# Conflict on idempotency_key
logger.warning("outbox_dedupe_skip",
    tenant_id=str(...), idempotency_key=key)

# Dispatcher
logger.info("outbox_dispatched", entry_id=..., event_name=..., duration_ms=...)
logger.warning("outbox_dispatch_retry", entry_id=..., retry_count=N, error=...)
logger.error("outbox_dispatch_failed_max_retries", entry_id=..., last_error=...)

# IdempotencyStore
logger.info("idempotency_cache_hit", namespace=..., func=...)
logger.warning("idempotency_redis_unavailable_softfail", namespace=...)
```

### Trace events emitted
PR-1: NINGUNO. campaign_trace_event tabla creada vacía. S2 wireup `CampaignCallbackHandler`.

PR-1 emite **logs structlog** (cubre observability mínima). No `*_trace_event` rows aún (sin LLM calls campaigns yet).

---

## 12. Cross-cutting concerns

| Concern | Aplicación PR-1 |
|---|---|
| **Tenant isolation** | Cubierto §9. `claim_pending` único cross-tenant read (worker scope, allowlist arch) |
| **Currency** | N/A (sin monetary fields nuevos en outbox/idempotency. campaign_llm_call ya tiene tenant_currency mirror sales_agent) |
| **Master data** | `created_at`, `dispatched_at` con `DateTime(timezone=True)`. Store UTC siempre. Display N/A (sin UI) |
| **Spanish neutro** | N/A (sin UI strings, sin schemas user-facing). structlog logs internos quedan en EN |
| **PII** | `domain_event_outbox.payload` JSONB puede contener PII (lead_id, email en payload). Builder agrega `sanitize_payload` step en `OutboxService.enqueue` ANTES insert. Sigue patrón `recording/sanitization.py` (copilot/sales_agent). **Regla:** payload guardado ya viene sanitized del producer (recoge sales-agent §3 invariant). PR-1 NO crea sanitizer nuevo — confía en producers existentes |
| **Native-first dev** | builder ejecuta `cd backend && .venv/bin/{ruff,pytest}`. `make migration-test-clone` corre Docker (DB clone) pero NO pytest dentro container |
| **Idempotency on writes** | OUTBOX = SSoT exactly-once via `(tenant_id, idempotency_key)` unique constraint. Caller responsable de generar idempotency_key deterministic (D12) |

---

## 13. Architecture fitness impact

| Test | Tipo | Allowlist |
|---|---|---|
| `tests/architecture/test_outbox_invariants.py` | NEW | Sin allowlist. Toda escritura/lectura `domain_event_outbox` filtra `tenant_id` excepto método `claim_pending` (worker scope, allowlist explícito por nombre) |
| `tests/architecture/test_idempotency_used_at_webhooks.py` | NEW | Allowlist inicial = todos call sites legacy hoy sin idempotencia. Builder pobla via `grep -rn "@router.post.*webhooks" backend/src/`. Shrink only |
| `tests/architecture/test_no_new_copilot_module_imports.py` | EXISTENTE | Cero cambio (PR-1 NO importa copilot/) |
| `tests/architecture/test_no_new_sales_agent_module_imports.py` | EXISTENTE | Cero cambio |
| `tests/architecture/test_sales_agent_observability_invariants.py` | EXISTENTE | Cero cambio (mirror schema verificado por builder) |
| `tests/architecture/test_folder_naming.py` | EXISTENTE | Verificar `shared/domain_events/outbox/{domain,infrastructure,application}/` cumple naming |
| DDD layering test | EXISTENTE | Sin cross-module imports nuevos. `shared/domain_events/` consume solo `shared/domain/` (DomainEvent base) |

**Allowlists shrink only:** PR-1 SHIP cero shrink. PR siguientes shrink (al migrar webhooks de allowlist).

---

## 14. pm-nico/current-state updates required

| File | Sección | Cambio |
|---|---|---|
| `docs/pm-nico/current-state/campaigns.md` | "Capacidades actuales" | Add row "observability spec registered (`agent_kind=campaign`, tablas `campaign_llm_call`+`campaign_trace_event`) — sin escrituras hasta S2" |
| `docs/pm-nico/current-state/sales_agent.md` | bottom (nueva sección "Notas técnicas internas") | Add line "outbox migration ready, flag `USE_OUTBOX_PATTERN_SALES_AGENT` OFF default. Cutover en PR siguiente." |
| `docs/pm-nico/current-state/copilot.md` | idem | Add line idem (`USE_OUTBOX_PATTERN_COPILOT`). Plus: idempotency ad-hoc Redis SETEX en `extraction_card_flow.py:68-77` ahora consume `@idempotent` decorator (cleaner) |
| `docs/pm-nico/current-state/brand.md` | idem | Add line idem (`USE_OUTBOX_PATTERN_BRAND`). brand_summary regen debounce sigue funcionando — depends on after-commit dispatch (legacy path con flag OFF, outbox path con flag ON ambos preservan semántica) |

`/pm` actualiza estos files en cierre PR (regla `pm-nico-ssot.md`).

---

## 15. Test surfaces (TDD-mandatory)

Orden RED-first por capa. Cada sub-deliverable independiente.

### Outbox sub-deliverable
1. **Domain RED:** `tests/shared/domain_events/test_outbox_domain.py`
   - `OutboxEntry.from_event` produce status=PENDING, retry_count=0
   - `idempotency_key` autogen si caller no pasa
   - `OutboxStatus` enum transiciones legales
2. **Infra RED:** `tests/shared/domain_events/test_outbox_repository.py`
   - `append` + tenant filter en queries
   - `claim_pending` returns ordered by created_at
   - `claim_pending` SKIP LOCKED (test concurrent claim — 2 sessions)
   - `mark_dispatched` updates only own row + tenant scoped
   - `append` ON CONFLICT (tenant_id, idempotency_key) → log + skip (no error)
3. **Application RED:** `tests/shared/domain_events/test_outbox_service.py`
   - `enqueue` requires session (ValueError si None)
   - `enqueue` doesn't commit (caller responsibility)
   - duplicate key → warning log + skip
4. **Adapter RED:** `tests/shared/domain_events/test_event_bus_adapter.py`
   - flag OFF + sync session → legacy `EventBus.publish` path
   - flag ON + async session + module → enqueue outbox
   - flag ON + sync session → log warning + legacy fallback
   - `subscribe()` delega a legacy
5. **Dispatcher RED:** `tests/shared/domain_events/test_outbox_dispatcher.py`
   - claim pending → dispatch → mark_dispatched
   - exception → mark_failed + retry_count++
   - retry_count >= MAX → status=failed (no further claim)
   - **kill+restart recovery** scenario: `dispatched_at IS NULL` rows reclaimed después restart
6. **Migration test:** clone DB + alembic upgrade head idempotente (regla `backend-migrations.md`).

### Idempotency sub-deliverable
1. **Domain RED:** `tests/shared/idempotency/test_idempotency_key.py`
   - VO equality + hashable + storage_key format
   - validation errors (empty namespace/key, ttl ≤ 0)
2. **Infra RED:** `tests/shared/idempotency/test_redis_store.py`
   - `claim` returns True (first), False (second)
   - `cached_result` returns stored, None if missing
   - Redis None → soft-fail (claim returns True, log warning)
   - concurrent claim race: only one wins (using fakeredis)
3. **Decorator RED:** `tests/shared/idempotency/test_decorator.py`
   - first call executes func + stores result
   - repeat call returns cached_result
   - empty `key_fn` result → skip dedupe + log warning
   - claim conflict + no cache (TTL race) → execute + log warning

### Observability sub-deliverable
1. **Registration RED:** `tests/modules/campaigns/test_observability_registration.py`
   - `register_agent_observability` invocado con `agent_kind="campaign"`, `has_lead_id=True`
   - `agent_observability_registry()` returns campaign spec
   - `get_spec("campaign").trace_event_table == "campaign_trace_event"`

### Architecture sub-deliverable
1. **`tests/architecture/test_outbox_invariants.py`** (NEW)
   - AST scan: `OutboxRepositoryImpl.append/mark_dispatched/mark_failed/get_by_id` filtran `tenant_id`
   - `claim_pending` allowlisted explicit (worker scope)
2. **`tests/architecture/test_idempotency_used_at_webhooks.py`** (NEW)
   - AST scan: cada `@router.post("/webhooks/...")` tiene `@idempotent` decorator OR está en allowlist
   - Allowlist inicial poblada por builder

### Sub-deliverable D RED (Q3 — extraction_card migration)
1. **`tests/modules/copilot/test_extraction_card_idempotency.py`** (NEW)
   - `emit_section_complete_pill(...)` llamado 2x mismo `job_id+section_slug` → 1 sola pill insertion
   - `emit_extraction_summary_card(...)` llamado 2x mismo `job_id` → 1 sola card emisión
   - Verifica `copilot_trace_event` solo tiene 1 row `name='card_emitted'` por evento (post-decorator)
   - Verifica decorator namespace `copilot:extract_card` sobrevive Redis restart con TTL preservado

### Regression (no romper)
- `tests/shared/test_event_bus.py` (legacy) sigue verde — re-export shim mantiene API
- `tests/{brand,sales_agent,copilot,crm}/test_*_event_handlers.py` siguen verdes con flag OFF default
- `tests/modules/copilot/` baseline goldens (extraction goldens) siguen verdes post-Q3 migration
- `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` baseline ratchet sin growth

---

## 16. Research notes

Patterns aplicados — todos con precedente en codebase. **NO research externa nueva requerida.**

| Pattern | Source codebase | Fecha | Why over alternatives |
|---|---|---|---|
| Transactional outbox | Industry standard (microservicios). Aplicado mirror sales_agent dual-write reconciliation (082_*) | precedente — | Resuelve R5 (eventos perdidos post-commit). Alt = saga pattern (overkill PR-1) |
| `SELECT ... FOR UPDATE SKIP LOCKED` | Postgres pattern (16+) | — | Multi-worker safe sin race conditions. Alt = advisory locks (más complejo) |
| Redis SETNX + TTL | Ya usado `extraction_card_flow.py:77` | 2026-04-XX existente | Atómico, simple. Alt = Postgres tabla idempotency_keys (más latencia) |
| Pydantic BaseSettings env flags | Ya usado `RUN_LLM_JUDGE`, `COPILOT_RECURSION_LIMIT` | precedente — | Stack-consistent. Alt = tabla feature_flags (sobre-ingeniería PR-1) |
| Mirror schema observability | sales_agent_llm_call (078) + copilot_llm_call | 2026-04-28 | Cross-agent MV UNION-ALL ya parametrizado por registry — agregando campaign_* hereda automático |
| ARQ cron worker **1 tick/segundo** (Q1 resolved) | Stack actual (cost_alerts/retention/scheduler) | precedente — | Consistency + zero-debt. Alt LISTEN/NOTIFY descartada (requires asyncpg dep, codebase usa psycopg2-binary). Ver detalle § 1.A.6 D8 |
| Single-API adapter dual-bridge sync/async (Q4 resolved) | Pattern nuevo, ratifica decisión zero-debt | 2026-04-29 | Migrar 38 sites a `AsyncSession` = catastrófico (>75% sync). Single signature `publish(event, session)` preserva 38 sites intactos. Alt = dual API rejected (PM Chris) |

**External research realizada (Q1 dispatcher frequency):**

- **asyncpg-listen** (https://pypi.org/project/asyncpg-listen/) — accessed 2026-04-29. Industry-standard library para LISTEN/NOTIFY con asyncpg. Caveat: codebase usa psycopg2-binary (sync), agregar asyncpg = nueva infra dependency. NO zero-debt.
- **ThinhDA "Postgres as Message Bus"** (https://thinhdanggroup.github.io/postgres-as-a-message-bus/) — accessed 2026-04-29. Estado del arte 2026: LISTEN/NOTIFY es **best-effort, non-durable signaling** — NUNCA reemplaza polling, solo augments. Hybrid pattern (LISTEN + cron safety net) is industry standard, pero requires 2 codepaths = más superficie test PR-1.
- **PostgreSQL docs (psycopg3 async)** (https://www.psycopg.org/psycopg3/docs/advanced/async.html) — accessed 2026-04-29. psycopg3 supports async LISTEN nativamente, pero migración psycopg2 → psycopg3 = breaking change driver-wide. Out-of-scope PR-1.

**Key takeaway research:** Path A (cron 1s) es la decisión zero-debt para PR-1. LISTEN/NOTIFY es un proyecto futuro vinculado a migración driver async (asyncpg o psycopg3) — no acumula deuda en PR-1, solo defiere optimización (no necesidad).

**Skill consultations realizadas:**
- `copilot-expert`: Confirmó que migrar `extraction_card_flow.py:68-77` Redis SETEX ad-hoc al `@idempotent` decorator es ALCANZABLE en PR-1 (no rompe goldens, no cambia behavior — solo refactor surface). Mantiene comportamiento "diseñado por expertos". **Q3 resolved — IN-SCOPE PR-1.**
- `sales-agent-expert`: §3 protected surfaces (webhook adapters Telegram/WhatsApp/IG) NO se modifican en PR-1 — PR-1 solo agrega allowlist en `test_idempotency_used_at_webhooks.py`. Flag OFF default = cero behavior change. Tools/orchestrator NO tocados.
- `brand-expert`: brand_summary regen debounce DEPENDS on after-commit dispatch. Verificado: legacy path con flag OFF preserva semantic (after-commit hook); outbox path con flag ON también preserva (caller commit → dispatcher next tick → in-memory dispatch). **Latencia adicional outbox: ~1s** (cron tick post-Q1). Aceptable para regen worker (60s debounce ya existente).

---

## 17. Decisions resolved by PM (audit trail Q1-Q6, 2026-04-29)

| ID | Question | PM decision | Architect implementation |
|---|---|---|---|
| **Q1** | `dispatch_outbox` cron frequency PR-1 (10s vs 1s vs LISTEN/NOTIFY hybrid) | "Estándar industria + sin deuda técnica + low latency. Architect decide entre cron 1s vs LISTEN/NOTIFY (push, zero polling)." | **Cron 1s elegida** (Path A). LISTEN/NOTIFY descartada porque codebase usa `psycopg2-binary` (sync) y migrar a asyncpg = NEW dep (no zero-debt). LISTEN/NOTIFY también es non-durable per industry research 2026 — requiere hybrid + cron safety net = más codepaths PR-1. Cron 1s cubre TODOS los use cases (extraction nav pill, brand_summary 60s debounce, payment followup horario). Detalle § 1.A.6 D8 + § 16. |
| **Q2** | Cutover plan post-PR-1 | "Architect plan accepted. Post-PR-1 → 1 PR per módulo emisor (sales_agent, copilot, brand). NO bloquea PR-1." | **Orden propuesto:** (1) sales_agent (mayor ROI — 8 sites + cycle billing), (2) copilot (8 sites + extraction subscribers + brand_summary regen), (3) brand (5 sites + personality regen), (4) resto (social_proof, crm, scheduling, connections, offer — 17 sites). Cada PR per módulo = arch test ratchet shrink + flag flip + module kwarg agregado a sites. PR-1 ship cero cutover. |
| **Q3** | Migrar `extraction_card_flow.py:68-77` ad-hoc Redis SETEX → `@idempotent` decorator | "DENTRO de PR-1. Chris quiere zero deuda técnica. Cleanup oportunista total. CONTRACT debe documentar este sub-deliverable explícito." | **Sub-deliverable D § 4.D agregado.** Migra ambos sitios (`emit_section_complete_pill` líneas 66-77 + `emit_extraction_summary_card` ~210-240). Behavior preservado byte-for-byte. RED test nuevo `tests/modules/copilot/test_extraction_card_idempotency.py`. |
| **Q4** | Dual API publish/publish_async vs single API | "SIN dual API. Cueste lo que cueste, sin deuda técnica. Architect debe optar por opción más limpia arquitectónicamente. **Default: opción más limpia, sin compromisos.**" | **Opción B elegida — single-API con sync→async bridge interno** (zero refactor en 38 sites). Architect contó 38 call sites (`grep -rn "EventBus.publish"`), >75% usan `Session` (sync) — verificado en social_proof/* (12 sites todos sync), brand/api/* (sync), crm/* (sync). Migrar TODOS a `AsyncSession` = catastrófico (>50% codebase). Single API: `publish(event, session=None, *, module=None, idempotency_key=None)` (signature exacta legacy). Internal routing detecta `isinstance(session, AsyncSession)` y delega a `OutboxRepositoryImpl.append_sync` o `.append_async`. NO `publish_async`. NO dual signature. Detalle § 1.A.5 D6 + D6.1. |
| **Q5** | Allowlist arch test (PM da lista vs builder pobla) | "Builder pobla (TDD RED-first scaffolding)." | **Builder corre `grep -rn "@router.post.*webhooks" backend/src/`** + agrega allowlist inicial en commit RED-first. § 12 + § 8.3 sin cambio. |
| **Q6** | Retention defaults `agent_kind="campaign"` | "30d trace / 90d LLM calls aceptado." | **`CAMPAIGN_TRACE_RETENTION_DAYS=30`, `CAMPAIGN_LLM_CALL_RETENTION_DAYS=90`.** § 3.C.1 sin cambio. S2 evalúa subir cuando haya tráfico real. |

---

## 18. Implementation plan (post-PM resolution)

PR-1 incluye **4 sub-deliverables**:

1. **Sub-deliverable A — Outbox pattern.** Domain entity + SQLA model + repo (dual append_sync/append_async) + `OutboxService` (dual entry sync/async-from-sync) + `EventBusAdapter` single-API + dispatcher cron 1s + migration 109. § 1.
2. **Sub-deliverable B — IdempotencyStore.** VO + Redis store + `@idempotent` decorator + `IdempotencyService.with_dedupe`. § 2.
3. **Sub-deliverable C — `agent_kind="campaign"` registration.** Module bootstrap + `CampaignLlmCallModel` + tablas en migration 109. § 3.
4. **Sub-deliverable D — `extraction_card_flow.py` migration (Q3).** Wrap 2 emitters con `@idempotent` decorator. Eliminar SETEX manual. § 4.D.

Orden TDD-RED first dentro PR-1 (paralelizable D no — depende B):
- A.domain → A.infra → A.application → A.adapter → A.dispatcher (linear)
- B.domain → B.infra → B.application (linear)
- C.registration (independiente, paralelo a A/B)
- **D depende de B** (decorator existe). Después de B GREEN.

Architecture test allowlists (Q5 builder pobla):
- `test_outbox_invariants.py` — sin allowlist (toda escritura `domain_event_outbox` filtra `tenant_id` excepto `claim_pending` allowlisted explícito)
- `test_idempotency_used_at_webhooks.py` — allowlist inicial = todos webhooks legacy. Builder pobla via `grep -rn "@router.post.*webhooks" backend/src/`.

---

<!-- @pm: CONTRACT.md updated with PM decisions Q1-Q6. Ready for builder. -->
