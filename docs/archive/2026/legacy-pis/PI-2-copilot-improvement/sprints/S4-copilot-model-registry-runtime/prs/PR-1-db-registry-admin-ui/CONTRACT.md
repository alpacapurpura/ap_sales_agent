# CONTRACT — PR-1-db-registry-admin-ui

> Owner: `nicolify-architect`. Single source of truth pre-implementación.
> Backend builder consume este archivo. Auditor enforce contra este archivo.
>
> **Mandate del PR:** convertir LLM model selection en runtime hot-swap (<60s sin deploy) via tabla `llm_role_binding` SSoT runtime + admin Streamlit `/admin/llm-models` CRUD + `LLMConfigService.resolve(role, tenant_id)` con cache 60s + Redis pub/sub invalidation. **NO breaking change** consumers de `Settings.get_model` (14 hits identificados).
>
> Date-aware research stamp: **2026-04-30** — research stack confirma (a) `cachetools.TTLCache` 7.0.6 NO thread-safe pero asyncio single-thread OK, (b) Redis pub/sub pattern ya cementado en `shared/billing/plan_service.py` y `modules/campaigns/.../cache.py` — **EXTEND** no NEW, (c) LiteLLM `/model/new` admin API soporta `model_info` custom metadata vía `extra="allow"` Pydantic (BETA, GitHub #21855 not exposed in `GET /v1/models`).

---

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR ID | PR-1-db-registry-admin-ui |
| Sprint | S4-copilot-model-registry-runtime |
| PI | PI-2-copilot-improvement |
| Tipo | infra (DB registry + admin UI + service layer) |
| Esfuerzo | L (~14 archivos cohesivos) |
| Modules touched | `shared/infrastructure/llm/`, `shared/admin/`, `core/config.py`, `workers/`, `alembic/` |
| Skills consultadas | `backend-expert` (admin-panel rule), `copilot-expert` (consumer compatibility — zero-touch), `sales-agent-expert` (§3 NOT TOUCHED) |
| pm-nico/current-state files affected | `current-state/copilot.md` — append cap "LLM model registry runtime hot-swap" |
| Architecture gates running against | `tests/architecture/test_admin_panel.py`, `tests/architecture/test_llm_routing_ssot.py` (4 tests), `tests/architecture/test_field_contract_platform.py` (no impact), `tests/admin/test_admin_contract.py`, `tests/admin/test_admin_smoke.py` |

---

## 1. Existing systems audit (NO NEW LAYER rule — architect-mandatory)

### Audit cross-module ejecutado

```bash
# 1. Settings consumers (14 hits — todos en src/shared/infrastructure/llm/)
grep -rn "settings\.get_model\|settings\.get_provider_for_role" backend/src/
# → backend/src/shared/infrastructure/llm/providers/litellm.py (5 hits)
# → backend/src/shared/infrastructure/llm/router.py (2 hits)
# → backend/src/shared/infrastructure/llm/providers/openai.py (3 hits)
# → backend/src/shared/infrastructure/llm/providers/_openai_compat.py (2 hits)
# → backend/src/shared/infrastructure/llm/providers/kimi.py (1 hit)
# Cero consumers en modules/{copilot,sales_agent,*} — todo dispatch via LiteLLMService que llama Settings.get_model

# 2. Redis pub/sub pattern existente
grep -rn "redis.*publish\|redis.*subscribe\|Redis()" backend/src/
# → src/shared/billing/application/plan_service.py: PUBSUB_PROD pattern (lines 162, 198, 280-318)
# → src/modules/campaigns/application/services/cache.py: SimpleTTLCache + subscribe_invalidations (PROTOCOL CacheBackend ya extracted)

# 3. Workers ARQ register
ls backend/src/workers/
# → settings.py (WorkerSettings.functions + cron list — 21 cron entries)
grep -n "cron(" backend/src/workers/settings.py | wc -l
# → 21

# 4. Admin Streamlit registry
cat backend/src/admin/app.py | grep "PageSpec(slug="
# → 22 entries existentes; pattern: 1 PageSpec + 1 pages/<slug>.py + 1 modules/<name>.py::render_<name>()
# → llm-virtual-keys.py + modules/llm_virtual_keys.py::render_llm_virtual_keys() ya cementado S3 PR-2

# 5. Migration latest
ls backend/alembic/versions/ | grep "^11" | sort
# → 110, 111, 112, 113, 114, 115, 116 → next = 117

# 6. LiteLLM admin API
# → POST /model/new acepta model_info {} con extra="allow" Pydantic; custom field "role" persiste pero NO surface via GET /v1/models (BETA, GH #21855)

# 7. Cachetools availability
grep -rn "from cachetools" backend/src/
# → src/shared/infrastructure/cache/ (already used in extraction services)
# → cachetools ya in pyproject.toml deps
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| **A. Settings.get_model + get_provider_for_role** | `src/core/config.py:77-104` | `ModelRole` (enums.py:24) + `AI_MODEL_<ROLE>` env vars | — | — | **active** SSoT runtime hoy |
| **B. LiteLLMService dispatch** | `src/shared/infrastructure/llm/providers/litellm.py` | consume Settings.get_model | router.py | LiteLLM Proxy | **active** S3 PR-2 shipped |
| **C. PlanService cache + Redis pub/sub** | `src/shared/billing/application/plan_service.py` | `CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL` | `subscribe_cache_invalidations()` task | redis.from_url client | **active** PR-2 cementado — pattern reusable |
| **D. SimpleTTLCache + CacheBackend Protocol** | `src/modules/campaigns/application/services/cache.py:46-156` | TTL dict + `PUBSUB_CHANNEL_PREFIX` | `subscribe_invalidations()` task | redis client passed by DI | **active** PI-1 S2 PR-5 — pattern reusable |
| **E. Admin Streamlit registry** | `src/admin/app.py:71-93` | `PageSpec` dataclass | `_build_pages()` derives `st.Page` | — | **active** 22 PageSpecs |
| **F. LiteLLM `/model/new` admin API** | external `visionarias_litellm:4000` | `model_info` JSONB extra=allow | LiteLLM Prisma `LiteLLM_ProxyModelTable` | — | **active** but BETA, role metadata NOT discoverable via `GET /v1/models` (GH #21855) |
| **G. ARQ worker scheduler** | `src/workers/settings.py` | WorkerSettings.functions (28 entries) | cron list (21 entries) | — | **active** ARQ pool |
| **H. model_pricing_snapshot table** | `alembic/versions/075_copilot_observability_rebuild.py:128-158` | `(provider, model, valid_from, valid_to)` | — | — | **active** SSoT inmutable billing |

### Decisión por sistema

- **Sistema A (`Settings.get_model`)**: **EXTEND con fallback chain**. Wrap actual lookup con `LLMConfigService.resolve(role)` → si DB binding active existe → return DB; else → return env var (legacy fallback). **Cero breaking change** los 14 consumers — siguen llamando `settings.get_model(role)` y reciben string model name. **Justificación**: pre-existing API, audit confirma ZERO cross-module consumers fuera de `shared/infrastructure/llm/`. Path: `src/core/config.py::Settings.get_model` retains signature, body delega a service.
- **Sistema B (`LiteLLMService`)**: **SIN CAMBIOS**. Sigue llamando `settings.get_model(role)`. Recibe string model name resolved (DB-first o env-fallback transparently). NO tocar S3 PR-2 surface §3-protected.
- **Sistema C (`PlanService` Redis pub/sub)**: **EXTEND pattern, NEW channel**. Usar mismo pub/sub mechanism (redis_client DI + subscribe_cache_invalidations task pattern), pero canal NUEVO `cache_invalidate:llm_role_binding`. NO duplicar service logic — copiar pattern, no codepath. **Justificación**: SSoT pub/sub pattern cementado, replicar es estándar consistency.
- **Sistema D (`SimpleTTLCache` + `CacheBackend` Protocol)**: **REUSE Protocol**. `LLMConfigService` consume mismo `CacheBackend` Protocol (port). Concreto = nueva subclass `LLMConfigCache` que extiende SimpleTTLCache con `PUBSUB_CHANNEL_PREFIX = "cache_invalidate:llm_role_binding"`. **Justificación**: Protocol port ya extracted, `cachetools.TTLCache` no thread-safe pero OK para asyncio single-thread (research stack confirmed).
- **Sistema E (Admin Streamlit registry)**: **EXTEND con 1 PageSpec + 1 page wrapper + 1 module**. Path: `pages/llm-models.py` + `modules/llm_models.py::render_llm_models()`. Slug `llm-models` (no colisión con existente `llm-virtual-keys`). NO cross-module imports excepto `_shared.py`.
- **Sistema F (LiteLLM `/model/new`)**: **NOT replace — solo complementario opcional S4 PR-2**. PR-1 NO consume. Razón: (1) BETA + GH #21855 abierto, role metadata no discoverable via GET, (2) LiteLLM no entiende semántica Nicolify (NANO/FAST/REASONING/AGENT/VISION/EMBEDDING) — mapping `role → litellm_model_alias` debe ser SSoT Nicolify, (3) custom metadata via `extra="allow"` no garantiza forward-compat (BerriAI puede flip default). **Decisión central PM-PR**: tabla custom `llm_role_binding` Nicolify SSoT runtime + LiteLLM consume `model` field como wire-name passthrough. Cero acoplamiento al producto BerriAI.
- **Sistema G (ARQ worker scheduler)**: **EXTEND `WorkerSettings.functions` con 1 entry**. NO new worker file; pub/sub subscriber correrá en main API process via `lifespan` event (mismo pattern PlanService). NO cron entry — pub/sub es event-driven, no scheduled.
- **Sistema H (`model_pricing_snapshot`)**: **NOT TOUCHED en PR-1**. Table SSoT inmutable preservada (S3 PR-2 cementó D-CROSS-4). PR-1 nuevo `llm_role_binding.model` field MUST referenciar `(provider, model)` tuple que existe en `model_pricing_snapshot WHERE valid_to IS NULL` (FK lógica enforced via app-layer validation, no DB FK porque `valid_from` parte de PK, eviting CASCADE issues — ver §9).

### Bloque "Por qué los existentes no sirven" para sistema NEW (`llm_role_binding` + `LLMConfigService`)

**Razón #1: Hot-swap requiere DB SSoT runtime.** `Settings` Pydantic es immutable post-instantiation (`backend/src/core/config.py:31-34`). Cambio env var = redeploy. A 1000+ tenants × frecuencia cambio modelo (LLM landscape: GPT-4o deprecated feb-2026, Claude Opus 4 deprecated jun-2026, DeepSeek V5 expected H2-2026), redeploy/cambio = riesgo inaceptable.

**Razón #2: LiteLLM `LiteLLM_ProxyModelTable` no entiende roles Nicolify.** Tabla Prisma-managed BerriAI almacena `(model_name, litellm_params, model_info JSONB)`. Field `model_info.role` es BETA, NO discoverable via `GET /v1/models`, dependent en `extra="allow"` Pydantic que BerriAI puede deprecar en futuras versions. Mapping `ModelRole → wire_name` MUST ser SSoT Nicolify. Audit cross-module confirma (`backend/src/core/enums.py:24` `ModelRole` 6 values) — semántica de negocio Nicolify, no infra externa.

**Razón #3: Audit trail inmutable es no-negociable.** `LiteLLM_AuditLog` table existe pero (a) gestionada Prisma (no Alembic), (b) BerriAI puede deprecar schema, (c) no tiene tenant context Nicolify. `llm_config_audit` Nicolify-owned garantiza compliance + billing audit trail bajo control.

**Razón #4: Per-tenant override S4 PR-2.** Schema `llm_role_binding` define `tenant_id NULL` (global) — extensible a S4 PR-2 GrowthBook integration con `tenant_llm_override` table (defer, no shipped en PR-1). Tabla custom permite this; LiteLLM Proxy NO (virtual keys = budget caps, not model selection).

**Criterio escala 1000+ tenants:**
- Hot-swap modelo a roleX: 1 admin click → 1 UPDATE SQL → pub/sub broadcast → cache invalidation cross-pod <60s. SQL execution <5ms (indexed), cache miss adds <5ms (single SELECT WHERE role=X AND is_active=TRUE). Net latency overhead vs hot-path LLM call (200-2000ms): negligible.
- Audit trail: 1 INSERT immutable per change. ~10 changes/month max realistic = 120 rows/year × 1000 tenants = 120k rows/year. Cero performance concern.
- Cero deuda técnica: tabla custom Nicolify desacopla 100% de BerriAI lifecycle. Si LiteLLM Proxy elimina `model_info.role` en v2.0, Nicolify zero impact.

---

## 2. Domain entities (nuevas)

### 2.1 `LLMRoleBinding` — runtime SSoT per role

```python
# src/shared/infrastructure/llm/domain/role_binding.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.core.enums import AIProvider, ModelRole


@dataclass(frozen=True, slots=True)
class LLMRoleBinding:
    """Immutable VO. Single active row per (role, tenant_id NULL global).

    Persisted shape: row in llm_role_binding table.

    Invariants (DB partial unique index enforces):
    - At most 1 row WHERE role=X AND tenant_id IS NULL AND is_active=TRUE.
    - At most 1 row WHERE role=X AND tenant_id=Y AND is_active=TRUE (per-tenant; defer S4 PR-2).
    - `model` MUST exist in `model_pricing_snapshot WHERE valid_to IS NULL`
      (validated at app-layer via LLMConfigService.activate, NOT DB FK —
      see §9 migration notes). PR-1 enforces global-only (tenant_id IS NULL).
    """

    id: UUID
    role: ModelRole
    provider: AIProvider
    model: str  # wire-name as known to LiteLLM Proxy (e.g., "deepseek-v4-flash")
    is_active: bool
    config: dict[str, Any]  # JSONB: temperature, max_tokens, top_p, etc.
    eval_score: Decimal | None  # populated when S5 eval-gate ships
    notes: str | None
    created_at: datetime
    created_by: str | None
    activated_at: datetime | None
    deactivated_at: datetime | None
    tenant_id: UUID | None = None  # NULL = global default; per-tenant defer S4 PR-2
```

### 2.2 `LLMConfigAudit` — append-only audit row

```python
# src/shared/infrastructure/llm/domain/audit.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

AuditAction = Literal["create", "activate", "deactivate", "update_config", "test_ping", "rollback"]


@dataclass(frozen=True, slots=True)
class LLMConfigAuditEntry:
    """Append-only audit. Persisted as row in llm_config_audit."""

    id: UUID
    actor: str  # admin user (Clerk user_id or "system" for migrations)
    action: AuditAction
    role: str  # ModelRole.value
    tenant_id: UUID | None
    before: dict[str, Any] | None  # previous state JSONB (None on create)
    after: dict[str, Any] | None  # new state JSONB (None on rollback to detached)
    reason: str | None
    created_at: datetime
```

### 2.3 `ResolvedModel` — service result (DTO interno, no persistence)

```python
# src/shared/infrastructure/llm/domain/resolved.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal

from src.core.enums import AIProvider

ResolveSource = Literal["db_binding", "env_fallback", "cache_hit"]


@dataclass(frozen=True, slots=True)
class ResolvedModel:
    """In-memory result of LLMConfigService.resolve(role).

    Returned to callers (Settings.get_model wrap, future per-tenant resolvers).
    Not persisted.
    """

    provider: AIProvider
    model: str
    config: dict[str, Any]  # merged: binding.config or {}
    source: ResolveSource
    binding_id: str | None  # UUID str, NULL when source=env_fallback
```

---

## 3. SQLAlchemy 2.0 Models

### 3.1 `LLMRoleBindingModel`

```python
# src/shared/infrastructure/llm/infrastructure/models.py
from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.shared.utils.datetime import utc_now


class Base(DeclarativeBase):  # use existing src/core/database.py Base; this is illustrative
    pass


class LLMRoleBindingModel(Base):
    __tablename__ = "llm_role_binding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    eval_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # B-tree composite index for hot-path resolve queries
        Index("ix_llm_role_binding_role_tenant_active", "role", "tenant_id", "is_active"),
    )
```

### 3.2 `LLMConfigAuditModel`

```python
class LLMConfigAuditModel(Base):
    __tablename__ = "llm_config_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
```

**`tenant_id` exception note:** `llm_role_binding` allows `tenant_id IS NULL` (global default — exactly equivalent to legacy `.env` default). PR-1 ships ONLY global rows (`tenant_id=NULL`). Per-tenant override defer S4 PR-2 (GrowthBook). This is the SAME exception pattern as `model_pricing_snapshot` (alembic 075) and `plan_config` (alembic 110) — global catalogs with documented allowlist exception in arch tests.

---

## 4. Pydantic v2 DTOs

### 4.1 Admin-internal DTOs (no public API; consumed only by Streamlit module + service tests)

```python
# src/shared/infrastructure/llm/dtos.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.enums import AIProvider, ModelRole


class LLMRoleBindingCreate(BaseModel):
    """Streamlit form payload for creating new (inactive) binding."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    role: ModelRole
    provider: AIProvider
    model: str = Field(min_length=1, max_length=128)
    config: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=1000)
    created_by: str = Field(min_length=1, max_length=128)


class LLMRoleBindingResponse(BaseModel):
    """Read DTO for admin display."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: ModelRole
    provider: AIProvider
    model: str
    is_active: bool
    tenant_id: UUID | None
    config: dict[str, Any]
    eval_score: Decimal | None
    notes: str | None
    created_at: datetime
    created_by: str | None
    activated_at: datetime | None
    deactivated_at: datetime | None


class LLMConfigAuditResponse(BaseModel):
    """Read DTO for audit log table display."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor: str
    action: str
    role: str
    tenant_id: UUID | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    reason: str | None
    created_at: datetime


class TestPingResult(BaseModel):
    """Result of admin "Test ping" button — single LLM call sample.

    Best-effort: failure does not raise — populates `success=False` + `error_message`.
    """

    model_config = ConfigDict(from_attributes=True)

    success: bool
    latency_ms: int
    cost_usd: Decimal | None
    sample_response: str | None  # first 200 chars LLM output
    error_message: str | None
    tokens_in: int | None
    tokens_out: int | None
```

**PII compliance (`pii-sanitisation.md`):** No PII fields in any of these DTOs. `actor` may contain Clerk user_id (UUID, opaque). `created_by` similar. NO email/phone/PII patterns.

---

## 5. API Routes

**No public HTTP routes exposed.** PR-1 admin surface is **Streamlit-only** (rule `admin-panel.md`). LLMConfigService is consumed by `Settings.get_model` wrap (in-process, not HTTP).

**Rationale:** consumer surface = backend internal. Adding REST endpoint would create attack surface (model swap = security-sensitive ops). Streamlit admin panel sits behind separate auth perimeter (`visionarias_admin_dev:8502` not exposed publicly).

If future need arises (CLI tool, ops automation), expose via `/api/v1/admin/llm-models/` with Bearer + `X-Tenant-ID` (admin role check). **Out of scope PR-1.**

---

## 6. TypeScript Types (Frontend)

**Zero frontend impact in PR-1.** No `frontend/src/` changes. Only Streamlit admin (Python).

If future tenant-self-service surface (S4 PR-2+) → mirror `LLMRoleBindingResponse` to camelCase TS in `frontend/src/features/admin/types/llm-config.ts`. **Out of scope PR-1.**

---

## 7. Repository Interfaces

```python
# src/shared/infrastructure/llm/domain/repositories.py
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.domain.audit import LLMConfigAuditEntry
from src.shared.infrastructure.llm.domain.role_binding import LLMRoleBinding


class LLMRoleBindingRepository(ABC):
    """Async port. tenant_id mandatory (None=global per §3 exception)."""

    @abstractmethod
    async def get_active_for_role(
        self, role: ModelRole, tenant_id: UUID | None = None
    ) -> LLMRoleBinding | None:
        """Return active binding (1 row max, partial UNIQUE enforces)."""

    @abstractmethod
    async def list_all(
        self, role: ModelRole | None = None, tenant_id: UUID | None = None
    ) -> list[LLMRoleBinding]:
        """List bindings (active + inactive) for admin display."""

    @abstractmethod
    async def get_by_id(
        self, binding_id: UUID, tenant_id: UUID | None = None
    ) -> LLMRoleBinding | None:
        """Lookup by id. tenant_id filter MANDATORY (None=global rows only)."""

    @abstractmethod
    async def create(self, binding: LLMRoleBinding) -> LLMRoleBinding:
        """Insert NEW inactive binding."""

    @abstractmethod
    async def activate(
        self, binding_id: UUID, actor: str, reason: str | None = None
    ) -> LLMRoleBinding:
        """Atomic transaction: deactivate prior active binding for same (role, tenant_id),
        activate this one, INSERT audit row. Returns activated binding.

        Raises BindingNotFound if id missing, AlreadyActive if no-op."""

    @abstractmethod
    async def deactivate(
        self, binding_id: UUID, actor: str, reason: str | None = None
    ) -> LLMRoleBinding:
        """Set is_active=FALSE + INSERT audit row. Idempotent (no-op if already inactive)."""


class LLMConfigAuditRepository(ABC):
    @abstractmethod
    async def append(self, entry: LLMConfigAuditEntry) -> None:
        """Append-only INSERT. Best-effort (try/except + structlog warning per
        copilot-observability.md — observability writes never block parent op)."""

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> list[LLMConfigAuditEntry]:
        """Reverse chronological. Admin UI display."""
```

---

## 8. Application Services

### 8.1 `LLMConfigService` — SSoT runtime resolver

```python
# src/shared/infrastructure/llm/application/config_service.py
from __future__ import annotations
import asyncio
from typing import Any
from uuid import UUID

import structlog

from src.core.config import Settings  # legacy fallback ONLY
from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.domain.repositories import (
    LLMConfigAuditRepository,
    LLMRoleBindingRepository,
)
from src.shared.infrastructure.llm.domain.resolved import ResolvedModel

logger = structlog.get_logger(__name__)

# Channel name follows PlanService convention (cache_invalidate:<topic>).
CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL = "cache_invalidate:llm_role_binding"
DEFAULT_CACHE_TTL_SECONDS = 60  # research-base; <1ms hot path with cache hit


class LLMConfigService:
    """Resolve (role, tenant_id) → ResolvedModel.

    Resolution chain (priority order):
    1. In-memory cache hit (60s TTL).
    2. DB binding active for (role, tenant_id) → cache + return.
    3. DB binding active for (role, tenant_id=NULL) — global default → cache + return.
       (PR-1: only step 3 effectively used; tenant_id always NULL.)
    4. .env fallback via Settings.get_model — legacy degraded mode.

    Cache invalidation:
    - Local mutation (activate/deactivate) → publish Redis pub/sub.
    - Subscriber (long-running task in main API process via lifespan) listens →
      flush local cache.
    - Pattern mirrors PlanService.subscribe_cache_invalidations (S0 PR-2 cementado).

    Failure modes (graceful degradation per tessl__graceful-degradation rule):
    - DB unreachable → return ResolvedModel from .env fallback (source="env_fallback")
      + structlog warning. Backend keeps serving turns.
    - Redis pub/sub unavailable → cache TTL still expires (60s). Soft-fail.
    """

    def __init__(
        self,
        binding_repo: LLMRoleBindingRepository,
        audit_repo: LLMConfigAuditRepository,
        settings: Settings,
        redis_client: Any | None = None,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    ) -> None:
        self._binding_repo = binding_repo
        self._audit_repo = audit_repo
        self._settings = settings
        self._redis = redis_client
        self._cache_ttl = cache_ttl_seconds
        # Key=f"{role}:{tenant_id_or_global}"; Value=(ResolvedModel, expires_at_unix).
        self._cache: dict[str, tuple[ResolvedModel, float]] = {}
        self._subscriber_task: asyncio.Task[None] | None = None

    async def resolve(
        self, role: ModelRole, tenant_id: UUID | None = None
    ) -> ResolvedModel:
        """Hot path. Asyncio single-thread = no lock needed
        (cachetools.TTLCache research confirmed — see decision D-3)."""
        import time

        cache_key = f"{role.value}:{tenant_id or 'global'}"
        now = time.monotonic()

        cached = self._cache.get(cache_key)
        if cached is not None:
            resolved, expires_at = cached
            if now < expires_at:
                # Return new VO with source=cache_hit for observability
                return ResolvedModel(
                    provider=resolved.provider,
                    model=resolved.model,
                    config=resolved.config,
                    source="cache_hit",
                    binding_id=resolved.binding_id,
                )

        # Try DB binding (PR-1: only global tenant_id=NULL)
        try:
            binding = await self._binding_repo.get_active_for_role(role, tenant_id=None)
            if binding is not None:
                resolved = ResolvedModel(
                    provider=binding.provider,
                    model=binding.model,
                    config=binding.config,
                    source="db_binding",
                    binding_id=str(binding.id),
                )
                self._cache[cache_key] = (resolved, now + self._cache_ttl)
                return resolved
        except Exception as exc:  # noqa: BLE001 — graceful degradation
            logger.warning(
                "llm_config_db_unreachable_falling_back_to_env",
                role=role.value,
                error=str(exc),
            )

        # Legacy .env fallback (source of truth pre-PR-1)
        resolved = ResolvedModel(
            provider=self._settings.get_provider_for_role(role),
            model=self._settings.AI_MODEL_NANO if role == ModelRole.NANO else (
                self._settings.AI_MODEL_REASONING if role == ModelRole.REASONING else (
                    self._settings.AI_MODEL_FAST if role == ModelRole.FAST else (
                        self._settings.AI_MODEL_VISION if role == ModelRole.VISION else (
                            self._settings.AI_MODEL_AGENT if role == ModelRole.AGENT else
                            self._settings.AI_MODEL_EMBEDDING
                        )
                    )
                )
            ),
            config={},
            source="env_fallback",
            binding_id=None,
        )
        self._cache[cache_key] = (resolved, now + self._cache_ttl)
        return resolved

    async def activate(
        self, binding_id: UUID, actor: str, reason: str | None = None
    ) -> ResolvedModel:
        """Admin Streamlit "Activate" button entry point.

        Atomic via repo.activate (single transaction):
        1. UPDATE deactivate prior active binding for same (role, tenant_id).
        2. UPDATE activate this one (set activated_at).
        3. INSERT audit row (action="activate").
        4. Publish Redis pub/sub invalidation.

        Returns ResolvedModel post-swap.
        Idempotent: AlreadyActive raises (caller decides retry policy).
        """
        binding = await self._binding_repo.activate(binding_id, actor=actor, reason=reason)
        await self._publish_invalidation()
        return ResolvedModel(
            provider=binding.provider,
            model=binding.model,
            config=binding.config,
            source="db_binding",
            binding_id=str(binding.id),
        )

    async def deactivate(
        self, binding_id: UUID, actor: str, reason: str | None = None
    ) -> None:
        """Admin "Deactivate" button. Idempotent."""
        await self._binding_repo.deactivate(binding_id, actor=actor, reason=reason)
        await self._publish_invalidation()

    async def invalidate_cache(self) -> None:
        """Local mutation OR subscriber callback. Flushes ALL cache slots.

        Granular per-role invalidation possible but PR-1 ships full flush
        (≤6 cache keys global; cost negligible).
        """
        self._cache.clear()

    async def _publish_invalidation(self) -> None:
        """Soft-fail per tessl__graceful-degradation rule."""
        if self._redis is None:
            return
        try:
            await self._redis.publish(CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL, "")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "llm_config_invalidate_publish_failed",
                channel=CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL,
                error=str(exc),
            )

    async def subscribe_cache_invalidations(self) -> None:
        """Long-running task. Started at app boot via FastAPI lifespan.

        Pattern mirrors PlanService.subscribe_cache_invalidations (PR-2 cementado).
        Soft-fail: Redis disconnects → retry with exponential backoff.
        """
        if self._redis is None:
            logger.info("llm_config_pubsub_skipped_no_redis")
            return
        backoff = 1.0
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(CACHE_INVALIDATE_LLM_ROLE_BINDING_CHANNEL)
                logger.info("llm_config_pubsub_subscribed")
                backoff = 1.0
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await self.invalidate_cache()
            except asyncio.CancelledError:
                logger.info("llm_config_pubsub_cancelled")
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "llm_config_pubsub_error_retrying",
                    error=str(exc),
                    backoff_seconds=backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    async def test_ping(
        self, provider: AIProvider, model: str
    ) -> "TestPingResult":  # forward ref — see DTOs §4
        """Admin UI "Test ping" button. Single LLM call sample.

        Strategy: bypass LLMConfigService chain entirely — direct adapter call.
        Returns latency + cost (resolved from model_pricing_snapshot) + sample text.

        Best-effort: any exception → success=False + error_message populated.

        DEFER concrete implementation to builder. Stub here to lock contract.
        """
        ...  # builder implements
```

### 8.2 `Settings.get_model` wrap — backwards compat

```python
# src/core/config.py — modified (NO breaking change to 14 callers)

class Settings(BaseSettings):
    # ... existing fields ...

    def get_model(self, role: ModelRole) -> str:
        """Resolve role to wire model name.

        DB-FIRST resolution: queries LLMConfigService.resolve which short-circuits
        on cache hit. Falls back to .env (legacy) if DB unreachable.

        D-1 architect: keep signature str-returning (NOT ResolvedModel) to avoid
        14-call refactor. Service injection via module singleton (lazy).

        Performance budget: <5ms p99 (cache hit <1ms, miss <5ms single-row SELECT
        on indexed (role, tenant_id, is_active)).
        """
        from src.shared.infrastructure.llm.application.config_service import (
            get_llm_config_service,  # singleton accessor
        )
        service = get_llm_config_service()
        if service is None:
            # boot ordering: service not yet initialized → legacy path
            return self._get_model_from_env(role)
        # Sync wrapper around async resolve (cache hit fast path is sync-safe)
        # If cache miss + DB call needed → falls through to env fallback in
        # service (graceful degradation), so no event loop blocking.
        return service.resolve_sync_cached_only(role).model

    def _get_model_from_env(self, role: ModelRole) -> str:
        """Pre-PR-1 logic preserved verbatim."""
        _map = {
            ModelRole.NANO: self.AI_MODEL_NANO,
            ModelRole.REASONING: self.AI_MODEL_REASONING,
            # ... unchanged
        }
        return _map[role]
```

**D-2 architect — sync resolution path:** `Settings.get_model` is called from sync code paths (Pydantic computed fields, OpenAI SDK init). `LLMConfigService.resolve` is async. Solution: service exposes `resolve_sync_cached_only(role)` which **only checks in-memory cache** (no DB I/O); on miss returns env fallback. Async `resolve(role)` populates cache via subscriber pattern. Trade-off: first call after invalidation gets env value (≤60s window); cache fills async via lazy populate worker (S5 hardening if needed). Acceptable for PR-1 — model swap propagation is `<60s` per acceptance criterion.

### 8.3 Repositories (concrete)

```python
# src/shared/infrastructure/llm/infrastructure/role_binding_repository.py

class SqlAlchemyLLMRoleBindingRepository(LLMRoleBindingRepository):
    """SA 2.0 async impl. Uses select(Model).where() — never session.query()."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def activate(self, binding_id: UUID, actor: str, reason: str | None = None) -> LLMRoleBinding:
        """Single transaction:
        1. SELECT target binding (FOR UPDATE).
        2. UPDATE prior active binding for same role → is_active=FALSE, deactivated_at=now().
        3. UPDATE target → is_active=TRUE, activated_at=now().
        4. INSERT audit row.
        5. Commit.

        Raises BindingNotFound, AlreadyActive.
        """
        ...
```

---

## 9. Migration Notes

### 9.1 Migration `117_llm_role_binding.py` (idempotent raw SQL)

```python
"""llm_role_binding + llm_config_audit.

PI-2 S4 PR-1 db-registry-admin-ui.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md rules.
Partial unique index for (role, tenant_id) where is_active=TRUE.

Revision ID: 117_llm_role_binding
Revises: 116_litellm_db_marker
Create Date: 2026-04-30
"""

from alembic import op

revision = "117_llm_role_binding"
down_revision = "116_litellm_db_marker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. llm_role_binding ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_role_binding (
            id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            role            VARCHAR(32)     NOT NULL,
            provider        VARCHAR(64)     NOT NULL,
            model           VARCHAR(128)    NOT NULL,
            is_active       BOOLEAN         NOT NULL DEFAULT FALSE,
            tenant_id       UUID            NULL,
            config          JSONB           NOT NULL DEFAULT '{}',
            eval_score      NUMERIC(5,4)    NULL,
            notes           TEXT            NULL,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            created_by      VARCHAR(128)    NULL,
            activated_at    TIMESTAMPTZ     NULL,
            deactivated_at  TIMESTAMPTZ     NULL,
            CONSTRAINT ck_llm_role_binding_role CHECK (
                role IN ('NANO','FAST','REASONING','AGENT','VISION','EMBEDDING')
            )
        )
    """)

    # Partial unique index — at most 1 active binding per (role, tenant_id_or_NULL)
    # NULL handled via COALESCE trick (Postgres treats NULL as distinct).
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_role_binding_active_per_role
            ON llm_role_binding (role, COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'))
            WHERE is_active = TRUE
    """)

    # Hot-path resolve index
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_role_binding_role_tenant_active
            ON llm_role_binding (role, tenant_id, is_active)
    """)

    # ── 2. llm_config_audit ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS llm_config_audit (
            id          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            actor       VARCHAR(128)    NOT NULL,
            action      VARCHAR(32)     NOT NULL,
            role        VARCHAR(32)     NOT NULL,
            tenant_id   UUID            NULL,
            before      JSONB           NULL,
            after       JSONB           NULL,
            reason      TEXT            NULL,
            created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_llm_config_audit_action CHECK (
                action IN ('create','activate','deactivate','update_config','test_ping','rollback')
            )
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_config_audit_role_created
            ON llm_config_audit (role, created_at DESC)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_llm_config_audit_tenant_created
            ON llm_config_audit (tenant_id, created_at DESC)
            WHERE tenant_id IS NOT NULL
    """)


def downgrade() -> None:
    # Tables not droppable — they hold audit trail. NO-OP downgrade.
    pass
```

### 9.2 Migration `118_llm_role_binding_seed_from_env.py` (idempotent seed)

```python
"""Seed llm_role_binding from current .env values.

Idempotent: ON CONFLICT DO NOTHING (UNIQUE on partial active index).
Re-run safe — won't duplicate active rows.

Source actor: 'system-migration-118'.

Revision ID: 118_llm_role_binding_seed_from_env
Revises: 117_llm_role_binding
"""

# ↓ values match docs/domains/llm-routing.md "Modelos activos hoy 2026-04-30"
SEED_DATA = [
    ("NANO", "deepseek", "deepseek-v4-flash"),
    ("FAST", "deepseek", "deepseek-v4-flash"),
    ("REASONING", "deepseek", "deepseek-reasoner"),
    ("AGENT", "kimi", "kimi-k2.6"),
    ("VISION", "openai", "gpt-4o"),
    ("EMBEDDING", "openai", "text-embedding-3-large"),
]

def upgrade() -> None:
    for role, provider, model in SEED_DATA:
        op.execute(f"""
            INSERT INTO llm_role_binding (role, provider, model, is_active, tenant_id, created_by, activated_at)
            SELECT '{role}', '{provider}', '{model}', TRUE, NULL, 'system-migration-118', NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM llm_role_binding
                WHERE role = '{role}' AND tenant_id IS NULL AND is_active = TRUE
            )
        """)
        op.execute(f"""
            INSERT INTO llm_config_audit (actor, action, role, tenant_id, after, reason)
            SELECT 'system-migration-118', 'create', '{role}', NULL,
                   jsonb_build_object('provider', '{provider}', 'model', '{model}', 'is_active', TRUE),
                   'Seed from .env at S4 PR-1 deploy'
            WHERE EXISTS (
                SELECT 1 FROM llm_role_binding
                WHERE role = '{role}' AND tenant_id IS NULL AND is_active = TRUE
                  AND created_by = 'system-migration-118'
            ) AND NOT EXISTS (
                SELECT 1 FROM llm_config_audit
                WHERE actor = 'system-migration-118' AND role = '{role}' AND action = 'create'
            )
        """)
```

### 9.3 Prod-clone test command (from `backend-migrations.md`)

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 116_litellm_db_marker && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

**MUST run before merge.** Test enforces: (a) no `op.create_table()` (use raw SQL), (b) partial UNIQUE index syntax Postgres-valid, (c) idempotent re-run = no duplicate seed rows.

### 9.4 FK to `model_pricing_snapshot` — DEFERRED, app-layer validation

**Decision D-4 architect:** NO DB FK between `llm_role_binding.(provider, model)` and `model_pricing_snapshot.(provider, model)`. Reasons:
1. `model_pricing_snapshot` PK is `(provider, model, valid_from)` — cannot FK partial composite.
2. Pricing rows are append-only with `valid_to` for closure — referencing closed pricing rows is meaningful (audit trail).
3. App-layer validation in `LLMConfigService.activate` checks: `EXISTS (SELECT 1 FROM model_pricing_snapshot WHERE provider=X AND model=Y AND valid_to IS NULL)` before activation. Raises `PricingNotConfiguredError` if missing — admin must add pricing snapshot first.

This pattern matches existing `copilot_llm_call.model` (no FK to snapshot) — observability rebuild D-7 (`docs/domains/llm-routing.md` Capa 4).

---

## 10. File Structure

```
backend/src/
├── core/
│   └── config.py                                                  (MODIFIED) wrap get_model with service
├── shared/infrastructure/llm/
│   ├── domain/
│   │   ├── role_binding.py                                        (NEW) LLMRoleBinding VO
│   │   ├── audit.py                                               (NEW) LLMConfigAuditEntry VO
│   │   ├── resolved.py                                            (NEW) ResolvedModel VO
│   │   ├── repositories.py                                        (NEW) Repo ABCs
│   │   └── exceptions.py                                          (NEW) BindingNotFound, AlreadyActive, PricingNotConfiguredError
│   ├── infrastructure/
│   │   ├── models.py                                              (NEW) SA 2.0 mapped_column
│   │   ├── role_binding_repository.py                             (NEW) Sqla impl
│   │   └── audit_repository.py                                    (NEW) Sqla impl
│   ├── application/
│   │   └── config_service.py                                      (NEW) LLMConfigService + singleton accessor + lifespan task
│   └── dtos.py                                                    (NEW) Pydantic v2 internal DTOs
├── admin/
│   ├── app.py                                                     (MODIFIED) +1 PageSpec slug=llm-models
│   ├── pages/
│   │   └── llm-models.py                                          (NEW) thin wrapper
│   └── modules/
│       └── llm_models.py                                          (NEW) render_llm_models() — 5 sections: list+create+activate+test_ping+audit_log
├── main.py                                                        (MODIFIED) +1 startup event for LLMConfigService.subscribe_cache_invalidations
└── workers/settings.py                                            (NOT MODIFIED — pub/sub runs in main API process, not worker pool)

backend/alembic/versions/
├── 117_llm_role_binding.py                                        (NEW) idempotent raw SQL
└── 118_llm_role_binding_seed_from_env.py                          (NEW) idempotent seed

backend/tests/
├── shared/infrastructure/llm/
│   ├── test_config_service_unit.py                                (NEW) cache hit/miss, env fallback, async resolve
│   ├── test_role_binding_repository.py                            (NEW) get_active, list, activate atomic, partial UNIQUE
│   ├── test_audit_repository.py                                   (NEW) append idempotent, list_recent
│   └── test_config_service_pubsub_integration.py                  (NEW) Redis mock, invalidation propagation
├── admin/
│   └── test_llm_models_page.py                                    (NEW) Streamlit AppTest smoke + CRUD form interactions
└── architecture/
    └── test_llm_routing_ssot.py                                   (NOT MODIFIED — allowlist still 0)
```

**Files: 11 NEW + 3 MODIFIED = 14 cohesive (matches "L scope ~12-15 archivos" PR.md).**

---

## 11. Cross-Cutting Concerns

### Tenant isolation
- `llm_role_binding.tenant_id NULL` global default — same exception pattern as `plan_config` (alembic 110), `model_pricing_snapshot` (alembic 075).
- PR-1 ships ONLY global rows. Per-tenant override defer S4 PR-2.
- `LLMRoleBindingRepository` methods all accept `tenant_id` param (defaults to None=global). Repo enforces `WHERE tenant_id IS NULL` for global resolution.
- Arch test `tests/architecture/test_master_data_baseline.py` already covers global table allowlist — **add `llm_role_binding` + `llm_config_audit` to that allowlist** with rationale comment.

### Currency
- `eval_score` is unitless decimal (0-1 range, expected). NOT a monetary field.
- `test_ping` returns `cost_usd: Decimal | None` — explicit USD because `model_pricing_snapshot` SSoT is USD per token (existing convention, D-CROSS-4 S3 PR-2).
- NO hardcoded `'USD'` Pydantic defaults in DTOs (allowlist-respecting).

### Master data
- All datetime columns: `TIMESTAMPTZ` Postgres + `DateTime(timezone=True)` SA 2.0.
- All `default=utc_now` (NOT `datetime.utcnow()`).
- Streamlit display: `_fmt_date()` helper from `llm_virtual_keys.py` pattern — UTC ISO formatted (admin context, no tenant locale).

### Spanish neutro LatAm
- Streamlit user-facing strings: tuteo, tildes, ñ, ¿/¡.
  - Title: "Modelos LLM" (not "Modelos LLM" as English).
  - Buttons: "Activar", "Desactivar", "Probar", "Eliminar".
  - Form labels: "Rol", "Proveedor", "Modelo", "Configuración (JSON)", "Notas".
  - Audit table headers: "Actor", "Acción", "Rol", "Antes", "Después", "Razón", "Cuándo".
- `notes` and `reason` user-input fields — no language enforcement (admin freeform).

### PII (`response_model=` mandate)
- No public HTTP routes (§5). PII rule N/A at API boundary.
- DTOs (§4) hold no PII. `actor` may contain Clerk user_id (UUID-shaped, non-PII per `pii-sanitisation.md`).
- Admin Streamlit display: NO user emails or names — just Clerk user_ids.

### Native-first dev
- All tests via `cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/admin/test_llm_models_page.py -v`.
- NEVER `docker exec ... pytest`.
- Lint: `cd backend && .venv/bin/ruff check src/shared/infrastructure/llm/ src/admin/modules/llm_models.py src/admin/pages/llm-models.py`.

---

## 12. Architecture Fitness Impact

### Gates running against this change

| Test | Path | Impact |
|---|---|---|
| `test_admin_panel.py::test_admin_pages_match_registry` | `tests/architecture/test_admin_panel.py` | New entry: `pages/llm-models.py` ↔ `PageSpec(slug='llm-models')`. |
| `test_admin_panel.py::test_admin_modules_have_render_function` | same | New `modules/llm_models.py::render_llm_models()`. |
| `test_admin_contract.py` | `tests/admin/test_admin_contract.py` | AST parse: 1 wrapper line, no cross-module imports beyond `_shared.py`. |
| `test_admin_smoke.py` | `tests/admin/test_admin_smoke.py` | Streamlit `AppTest` headless render must succeed. **Mock `llm_role_binding_repo` + `audit_repo` in `tests/admin/conftest.py`**. |
| `test_llm_routing_ssot.py` (4 tests) | `tests/architecture/test_llm_routing_ssot.py` | Allowlist `KNOWN_LEGACY_LLM_FILES = set()` UNCHANGED. New service files in `shared/infrastructure/llm/` — explicitly allowed location per `test_no_new_llm_factory_layers`. |
| `test_master_data_baseline.py` | `tests/architecture/test_master_data_baseline.py` | **EXTEND allowlist**: add `llm_role_binding` + `llm_config_audit` with rationale comment "global tenant_id NULL = LLM model registry runtime, defer per-tenant override S4 PR-2". |

### Allowlist updates expected (must shrink, never grow without justification)

- `KNOWN_LEGACY_LLM_FILES` → unchanged (still 0). NEW files in `shared/infrastructure/llm/` are explicitly the legitimate location per architecture rules.
- `MASTER_DATA_GLOBAL_TABLES_ALLOWLIST` → +2 entries (`llm_role_binding`, `llm_config_audit`) — JUSTIFIED as global LLM catalog, equivalent to existing `plan_config` + `model_pricing_snapshot`.
- NO other allowlist grows.

---

## 13. pm-nico/current-state Updates Required

`docs/pm-nico/current-state/copilot.md` — **append section "LLM model registry runtime hot-swap"** under "Capacidades activas hoy" with:
- Entry: "Admin puede swap modelo LLM (NANO/FAST/REASONING/AGENT/VISION/EMBEDDING) en runtime via Streamlit `/admin/llm-models` sin redeploy. Propagación cross-pod <60s. Rollback 1-click MTTR <30s. Audit trail inmutable en `llm_config_audit`."
- Surface link: `backend/src/admin/modules/llm_models.py`.
- User-facing impact: ZERO direct (admin-only). Indirecto = backend resilience to model deprecations + cost optimizations sin downtime user.

PR builder updates this file in same commit as feature merge (rule `pm-nico-ssot.md`).

---

## 14. Test Surfaces (TDD-mandatory)

**RED → GREEN per layer** (rule `tdd-mandatory.md`).

### Layer 1: Domain (RED first)
- `test_role_binding_vo.py` — VO immutability, validation (role enum membership).
- `test_audit_vo.py` — VO immutability, action enum.

### Layer 2: Infrastructure (RED next)
- `test_role_binding_repository.py`:
  - `test_get_active_for_role_returns_unique_global` — partial UNIQUE enforced.
  - `test_activate_atomic_deactivates_prior_and_creates_audit_row` — single transaction.
  - `test_activate_idempotent_no_op_when_already_active` — idempotency.
  - `test_get_by_id_returns_none_when_tenant_id_mismatch` — tenant isolation.
  - `test_create_inserts_with_is_active_false_default` — guard against accidental activation.
- `test_audit_repository.py`:
  - `test_append_idempotent_natural_key_dedup` — same (actor, action, role, created_at) NOT inserted twice.
  - `test_list_recent_reverse_chronological` — ordering.

### Layer 3: Application (RED next)
- `test_config_service_unit.py`:
  - `test_resolve_cache_hit_returns_source_cache_hit` — cache TTL behavior.
  - `test_resolve_cache_miss_queries_db_and_caches` — populate flow.
  - `test_resolve_db_unreachable_falls_back_to_env_settings` — graceful degradation.
  - `test_resolve_db_returns_none_falls_back_to_env_settings` — no binding configured.
  - `test_activate_publishes_invalidation_message` — Redis pub/sub call.
  - `test_activate_audit_row_appended` — audit trail.
  - `test_invalidate_cache_clears_all_slots` — flush behavior.
  - `test_subscribe_cache_invalidations_handles_redis_disconnect_with_backoff` — resilience.
- `test_settings_get_model_wrap_preserves_signature_and_returns_str` — backward compat (14-call surface).

### Layer 4: Admin Streamlit
- `test_llm_models_page.py`:
  - `test_render_llm_models_smoke` — `AppTest` headless render no exception (existing pattern from `test_admin_smoke.py`).
  - `test_create_binding_form_validates_provider_role_pairs` — form-level guard.
  - `test_activate_button_invokes_service_and_shows_success` — UX flow.
  - `test_audit_log_table_displays_last_50_entries` — query path.
  - `test_test_ping_button_shows_latency_and_cost` — integration test stub (mock provider call).

### Layer 5: Architecture
- `test_llm_routing_ssot.py` — already exists, MUST stay green (allowlist 0, new files in legit location).
- `test_admin_panel.py` — auto-validates new PageSpec.

### Layer 6: Migration prod-clone
- `make migration-test` (per `backend-migrations.md`) — verifies idempotent re-run + downgrade NO-OP doesn't crash.

**Tests target ≥6 NEW test files. Coverage gate `fail_under=43%` — NEW code MUST not regress.**

---

## 15. Research Notes

### Cachetools TTLCache thread safety (2026-04-30)
- **Source**: https://cachetools.readthedocs.io/en/stable/ (v7.0.6 stable)
- **Key takeaway**: TTLCache is NOT thread-safe by default. Asyncio single-thread = OK without explicit lock. Must use `threading.Lock()` if multi-threaded.
- **Why this matters PR-1**: `LLMConfigService` lives in async FastAPI process (uvicorn workers — single thread per worker). NO lock needed in service code (D-3).
- **GitHub issue 294 confirms** ongoing thread-safety discussion + `threading.Condition` adoption in `cachetools.func` decorators (irrelevant to manual TTL dict).

### Redis pub/sub cache invalidation pattern (2026-04-30)
- **Source**: https://redis.io/blog/redis-assisted-client-side-caching-in-python/ + https://medium.com/the-pandadoc-tech-blog/redis-client-side-cache-with-async-python-6228a0121a12
- **Key takeaway**: 2026 winning pattern = L1 (memory) + L2 (Redis pubsub broadcast). Latency target: invalidation propagation <100ms cross-instance via pub/sub.
- **Why this matters PR-1**: cement existing pattern from `PlanService.subscribe_cache_invalidations` (PR-2 cementado). Channel name follows convention (`cache_invalidate:<topic>`). Re-using same pattern = no new infra, leveraging proven resilience.
- **Decision D-3**: REUSE PlanService pattern verbatim (channel constant + lifespan task), NOT new abstraction.

### LiteLLM `/model/new` admin API metadata (2026-04-30)
- **Source**: https://docs.litellm.ai/docs/proxy/model_management + GitHub Issue #21855
- **Key takeaway**: `/model/new` accepts `model_info` JSONB extra=allow. Custom field `role` would persist but NOT discoverable via `GET /v1/models` (BETA limitation, GH #21855 still open Feb 2026).
- **Why this matters PR-1**: confirms decision **NEW** custom Nicolify table is correct. LiteLLM Proxy `model_info.role` is BETA + not discoverable + dependent on BerriAI Pydantic config. Coupling Nicolify business semantics (NANO/FAST/REASONING) to BerriAI BETA = unacceptable scale risk 1000+ tenants.

---

## 16. Open Questions for PM

1. **Q1 — `Settings.get_model` sync access pattern (D-2 critical)**: Architect proposes `resolve_sync_cached_only(role)` returning cache or env fallback (no DB I/O in sync path). Trade-off: first call after Redis invalidation gets stale env value for ≤60s window per pod. Acceptable per `<60s propagation` acceptance criterion in PR.md, but worth Chris confirmation. **Alternative**: refactor 14 call sites to async — out of L scope. **PM call**: confirm trade-off OR escalate to S4 PR-2 hardening with lazy populate worker.

2. **Q2 — `test_ping` button cost computation source**: For pre-promote validation, do we (a) call provider directly bypassing LiteLLM Proxy (network call to OpenAI/DeepSeek/Kimi from Streamlit container), or (b) call LiteLLM Proxy (internal Docker network only)? Option (b) is faster + reuses existing routing, but tests current LiteLLM dispatch instead of raw provider. Recommendation: **option (b)** — admin UI tests the actual dispatch path users will hit. **PM call**: confirm.

3. **Q3 — Per-tenant rows reachable via DB but rejected by service in PR-1**: If admin manually inserts `llm_role_binding` row with `tenant_id != NULL` directly in DB (bypassing UI), should `LLMConfigService.resolve(role, tenant_id=X)` honor it OR ignore until S4 PR-2 ships? Architect proposes: **ignore (return global)**, log warning. Defers S4 PR-2 work cleanly. **PM call**: confirm.

4. **Q4 — Eval score field populated when**: Schema includes `eval_score NUMERIC(5,4) NULL`. PR-1 leaves NULL on all rows (no eval gate yet — S5). Should admin UI surface "Eval Score: not run" warning before activation, or stay silent? Architect recommends: **show warning** "El gate de evaluación se activa en S5. Por ahora, el operador valida vía Test ping." **PM call**: confirm copy.

5. **Q5 — `_shared.py` admin helper for LLM repo factories**: Streamlit `render_llm_models` needs a SessionLocal-backed `LLMRoleBindingRepository` instance. Should factory live in `_shared.py` (precedent: `_get_all_tenants_cached`) or module-local? Architect recommends `_shared.py` with `@st.cache_resource` for singleton per Streamlit session. **PM call**: confirm.

6. **Q6 — `provider+model` combo validation against `model_pricing_snapshot`**: §9.4 architect proposes app-layer `EXISTS` check before activation, raising `PricingNotConfiguredError`. Should admin UI block activation OR allow with warning + INSERT placeholder pricing row? Architect recommends: **block** — pricing snapshot is non-negotiable per llm-routing.md "Reglas no-negociables #1". Operator must add pricing first via separate admin page (or future automation). **PM call**: confirm strict-block stance.

---

<!-- @pm: CONTRACT.md ready (architect-empowered). -->
