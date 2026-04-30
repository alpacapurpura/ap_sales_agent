# CONTRACT — PR-1-voice-media-hardening

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builder consume este archivo. Streamlit admin extiende panel existente — no hay frontend Next.js.
>
> Updated 2026-04-29 — aplicadas 5 PM answers (ver §16).
>
> Skills consultados:
> - **copilot-expert** — invariantes módulo (resilience: best-effort observability; observability: traces honestas; arquitectura inmutable F0-F11). Decisión clave: **NO crear nuevo módulo**. Usar `core/rate_limit.py` ya existente como base + extender con scope `copilot-voice` + override per-tenant. Esto preserva ratchet `copilot → otros módulos` (22 frozen) y respeta DDD (tenant_limits vive en `copilot/infrastructure/repositories/`).
> - **backend-expert** — DDD inside-out, SQLA 2.0 async-first, Pydantic v2, migraciones idempotentes raw SQL.
> - **offer-expert/sales-agent-expert/brand-expert/metrics-expert** — N/A (PR no toca ninguno de esos módulos).

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR ID | PR-1-voice-media-hardening |
| PI/Sprint | PI-2-copilot-improvement / S1-copilot-maintenance-batch |
| Modules touched | `core/`, `shared/idempotency/` (none), `modules/copilot/api/`, `modules/copilot/infrastructure/`, `admin/` |
| pm-nico/current-state files | `docs/pm-nico/current-state/copilot.md` — append capability "Rate limit voice + per-tenant media/voice limits" |
| Architecture gates relevantes | `tests/architecture/test_admin_panel.py`, `test_api_contracts.py` (response_model), `test_no_new_copilot_module_imports.py` (ratchet 22), `test_copilot_anchors.py` (cap 36), `test_ddd_boundaries.py`, `test_conventions.py` |

**Decisión arquitectónica raíz:** la PR.md proponía `shared/rate_limit/` nuevo. Tras inspección, **`backend/src/core/rate_limit.py` ya implementa Redis sliding window con `check_rate_limit(user_id, scope, max_requests, window_seconds)`** y se usa hoy en `copilot/api/chat.py`. No hay justificación para duplicar en `shared/`. **CONTRACT extiende `core/rate_limit.py`** con (a) parametrización por env vía `Settings`, (b) resolver per-tenant que combina default env + override DB. Esto preserva DRY, evita boundary nuevo y mantiene el helper como SSoT cross-módulo.

## 1. Domain Entities

```python
# backend/src/modules/copilot/domain/tenant_limits.py — NEW
"""Per-tenant overrides for copilot rate limits + media size caps."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class CopilotTenantLimits:
    """Aggregate root: tenant-scoped overrides for copilot voice/media limits.

    Invariants:
    - tenant_id mandatory (1:1 con Tenant; row optional — None overrides = use env defaults).
    - voice_rpm_override > 0 si está presente (sentinel None = no override).
    - media_max_bytes_override > 0 si está presente.
    - deleted_at None mientras vivo (soft-delete only).
    """
    tenant_id: UUID                           # FK lógico → tenants.id (1:1 partial unique)
    voice_rpm_override: int | None            # requests/min para /voice/upload-and-transcribe (None → env default)
    media_max_bytes_override: int | None      # bytes para /media/upload + /voice/upload-and-transcribe (None → env default)
    updated_at: datetime
    updated_by_user_id: UUID | None           # admin que tocó override (audit)
    deleted_at: datetime | None
```

**Invariantes runtime (enforce en domain factory):**
- `voice_rpm_override` ∈ `[1, 1000]` ó `None`. Cap 1000 protege contra typo admin (rps storm Whisper).
- `media_max_bytes_override` ∈ `[1 MiB, 100 MiB]` ó `None`. Cap superior 100 MiB = estándar SaaS (Slack/Notion/Intercom) para microempresarios. Editable a futuro vía `plan_id` slot (otro PI con planes per-tenant Pro/Enterprise puede subir el cap).
- `tenant_id` REQUIRED (no fabricable sin FK).

## 2. SQLAlchemy 2.0 Models

```python
# backend/src/modules/copilot/infrastructure/models/tenant_limits_model.py — NEW
"""SQLAlchemy 2.0 model for copilot per-tenant limit overrides."""
import uuid
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotTenantLimitsModel(Base):
    """Per-tenant overrides for copilot rate limits + media caps."""

    __tablename__ = "copilot_tenant_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True, unique=True,
    )
    voice_rpm_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_max_bytes_override: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
```

**Indices:**
- `ix_copilot_tenant_limits_tenant_id` UNIQUE (idempotente vía `WHERE deleted_at IS NULL` partial unique en migración).

**Notas:**
- `BigInteger` para `media_max_bytes_override` (25 MB cabe en Integer pero proteger ante caps futuros >2 GB).
- 1:1 con tenant — fila opcional. Ausencia = "usa env default".
- `tenant_id` indexado y unique parcial vía SQL (no `unique=True` en columna porque debe convivir con soft-delete).

### 2.b Audit log (Q2 — tabla separada append-only)

```python
# backend/src/modules/copilot/infrastructure/models/tenant_limits_audit_model.py — NEW
"""Append-only audit trail para cambios en copilot_tenant_limits."""
import uuid
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotTenantLimitsAuditModel(Base):
    """Append-only — cada upsert/delete en copilot_tenant_limits inserta una row aquí.

    Q2 decisión architect: tabla separada (no inflar copilot_tenant_limits con write churn).
    Facilita queries históricas por tenant + audit humano (Chris audita).
    """

    __tablename__ = "copilot_tenant_limits_audit"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # "upsert" | "soft_delete"
    voice_rpm_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voice_rpm_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_max_bytes_before: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    media_max_bytes_after: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True,
    )
```

**Indices audit:**
- `ix_copilot_tenant_limits_audit_tenant_id` — query por tenant.
- `ix_copilot_tenant_limits_audit_changed_at` — review cronológico.

**Append-only contract:**
- Repo `upsert()` y `soft_delete()` insertan row en audit DENTRO de la misma transacción (atómico).
- Sin UPDATE/DELETE sobre la tabla audit — solo INSERT (enforce vía revoke privileges en prod opcional, hoy convención).
- Retention: ilimitada en PR-1 (low write rate — overrides cambian <1/mes/tenant según PM Q2). Política retention queda como slot futuro si volume crece.


## 3. Pydantic v2 DTOs

```python
# backend/src/modules/copilot/api/tenant_limits_dto.py — NEW (admin-only, no se expone al copilot UI)
"""DTOs para CRUD de per-tenant limit overrides desde Streamlit admin."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CopilotTenantLimitsResponse(BaseModel):
    """Response — overrides actuales de un tenant. Fields opcionales = sin override."""
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    voice_rpm_override: int | None = Field(None, ge=1, le=1000)
    media_max_bytes_override: int | None = Field(None, ge=1_048_576, le=104_857_600)  # 1 MiB .. 100 MiB (Q4 — cap industria SaaS estándar microempresarios)
    updated_at: datetime
    updated_by_user_id: UUID | None = None


class CopilotTenantLimitsUpsertRequest(BaseModel):
    """Upsert — None en un campo limpia el override (vuelve a env default)."""
    model_config = ConfigDict(from_attributes=True)

    voice_rpm_override: int | None = Field(None, ge=1, le=1000)
    media_max_bytes_override: int | None = Field(None, ge=1_048_576, le=104_857_600)  # 1 MiB .. 100 MiB


class EffectiveLimitsResponse(BaseModel):
    """Response read-only — limites efectivos (override OR env default).

    Consumido por endpoints media/voice via service interno (no admin).
    """
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    voice_rpm: int                     # efectivo (override OR settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN)
    voice_window_seconds: int          # constante 60 hoy (sliding window minute)
    media_max_bytes: int               # efectivo (override OR settings.COPILOT_MEDIA_MAX_BYTES)
    voice_rpm_is_override: bool        # true si proviene de DB; false si env default
    media_max_bytes_is_override: bool
```

**PII allowlist:** ningún field PII. `updated_by_user_id` es UUID interno admin Nicolify, no expuesto a tenants.

## 4. API Routes

**No hay rutas REST nuevas para tenants** (admin Streamlit habla directo al servicio, no via HTTP). Los endpoints existentes voice/media solo se modifican (config dinámica, mismo response_model).

| Method | Path | Auth | Request DTO | response_model | Cambio |
|---|---|---|---|---|---|
| POST | `/api/v1/copilot/voice/upload-and-transcribe` | Bearer + X-Tenant-ID | `multipart/form-data` (audio file) | `VoiceUploadAndTranscribeResponse` (existing) | + rate limit `copilot-voice` con effective_voice_rpm + max_bytes via effective_media_max_bytes |
| ~~POST~~ | ~~`/api/v1/copilot/voice/transcribe`~~ | — | — | — | **REMOVED en este PR (Q1)** — endpoint legacy STT-only sin upload. Cliente pequeño (pocos tenants), barato corregir ahora. Single endpoint `voice/upload-and-transcribe` cubre todo el use-case (atomic upload + transcribe). |
| POST | `/api/v1/copilot/media/upload` | Bearer + X-Tenant-ID | `multipart/form-data` + form fields | `MediaUploadResponse` (existing) | max_bytes via effective_media_max_bytes + rate limit `copilot-media-upload` (Q5 — protege compute BE; storage R2 amortizado, no impacta) |

**Decisión diferida #1 (PR.md) — Resuelta Q5:** Rate limit per-tenant también para `/media/upload`.
**Resolución (2026-04-29):** **SÍ en este PR.** Bucket separado `copilot-media-upload` (default 30 RPM > voice porque cost = solo upload, no LLM). Reusa `core/rate_limit.py::check_rate_limit(scope="copilot-media-upload", ...)`. Storage backend R2 ya existe (delegado a `AssetsService.upload_asset` — `media.py:5,184`); el rate limit protege compute BE (multipart parsing + AI metadata pipeline + R2 PUT), independiente del storage backend. `_MAX_FILE_BYTES` cap dinámico via `effective_media_max_bytes` permanece independiente del rate limit.

**Decisión diferida #2 (PR.md):** ¿`copilot_voice_rate_limit_hits` a Prometheus o solo structlog?
**Resolución:** **structlog only en este PR.** Hoy no hay `prometheus_client` en stack copilot — métricas viven en `copilot_trace_event` + `copilot_llm_call`. Emitir structlog warning `event="copilot_voice_rate_limit_hit"` con `tenant_id`, `user_id`, `current_count`, `limit`, `retry_after`. Streamlit `/trazas` y queries SQL ad-hoc cubren observabilidad. Prometheus = scope futuro PI dedicado.

**Status codes nuevos en endpoints existentes:**
- `429 Too Many Requests` cuando voice rate limit excedido. Header `Retry-After: <seconds>`. Body JSON con `detail` español neutro: `"Demasiadas transcripciones. Espera N segundos."`
- `413 Payload Too Large` ya existente — solo cambia el cap dinámico (env / override).

## 5. TypeScript Types (Frontend)

**N/A — no hay frontend Next.js en este PR.** El admin es Streamlit (Python). Si en futuro se exponen efectivos al copilot UI, agregar `EffectiveLimits` mirror en `frontend/src/features/copilot/types/`.

## 6. Repository Interfaces

```python
# backend/src/modules/copilot/infrastructure/repositories/tenant_limits_repository.py — NEW
"""Async repo para per-tenant copilot limit overrides."""
from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID

from src.modules.copilot.domain.tenant_limits import CopilotTenantLimits


class CopilotTenantLimitsRepository(ABC):
    """Port — every method tenant_id-scoped (regla tenant-isolation.md)."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> CopilotTenantLimits | None:
        """Devuelve overrides del tenant o None si no hay fila (tenant usa defaults env)."""

    @abstractmethod
    async def upsert(
        self,
        tenant_id: UUID,
        *,
        voice_rpm_override: int | None,
        media_max_bytes_override: int | None,
        updated_by_user_id: UUID | None,
    ) -> CopilotTenantLimits:
        """Insert-or-update. None en un campo limpia el override (DB NULL).

        Q2: Atomic — escribe row en `copilot_tenant_limits_audit` con action='upsert'
        DENTRO de la misma transacción, capturando before/after values.
        """

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID, *, deleted_by_user_id: UUID | None = None) -> None:
        """Marca deleted_at — el tenant vuelve a env defaults sin perder audit trail.

        Q2: Atomic — escribe row en `copilot_tenant_limits_audit` con action='soft_delete'.
        """

    @abstractmethod
    async def list_overrides(self, *, limit: int = 100, offset: int = 0) -> list[CopilotTenantLimits]:
        """Listado admin — paginado. Filtro deleted_at IS NULL implícito."""
```

**Sync wrapper** (Streamlit es sync):
- Repo SQLA 2.0 async (`AsyncSession`) es la implementación canónica.
- Streamlit consume vía service sync wrapper que usa `SessionLocal` (mismo patrón `tenants.py:14-19`). NO duplicar lógica — el wrapper sólo hace `asyncio.run(repo.method(...))` o usa `Session` paralelo. Builder elige (preferencia: `Session` síncrono dedicado para Streamlit, dejando `AsyncSession` para uso runtime via ports si emerge).

**SSoT runtime — `CopilotLimitsResolver` (application service):**

```python
# backend/src/modules/copilot/application/services/limits_resolver.py — NEW
"""Resuelve limites efectivos: override DB > env default."""
from uuid import UUID
from src.core.config import settings
from src.modules.copilot.domain.tenant_limits import CopilotTenantLimits
from src.modules.copilot.infrastructure.repositories.tenant_limits_repository import (
    CopilotTenantLimitsRepository,
)


class CopilotLimitsResolver:
    """Aplica regla: per-tenant override > env default."""

    def __init__(self, repo: CopilotTenantLimitsRepository) -> None:
        self._repo = repo

    async def get_effective(self, tenant_id: UUID) -> "EffectiveLimits":
        override = await self._repo.get_by_tenant(tenant_id)
        return EffectiveLimits(
            tenant_id=tenant_id,
            voice_rpm=(override.voice_rpm_override if override and override.voice_rpm_override else settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN),
            voice_window_seconds=60,
            media_max_bytes=(override.media_max_bytes_override if override and override.media_max_bytes_override else settings.COPILOT_MEDIA_MAX_BYTES),
            voice_rpm_is_override=bool(override and override.voice_rpm_override),
            media_max_bytes_is_override=bool(override and override.media_max_bytes_override),
        )
```

`EffectiveLimits` = dataclass interno (no DTO Pydantic — `EffectiveLimitsResponse` es API contract DTO; el dataclass interno simplifica caching futuro).

## 7. Application Services

**`CopilotLimitsResolver`** (arriba). Una operación: `get_effective(tenant_id)`. Sin transacciones (read-only). Caching: ninguno en PR-1 (Redis/in-memory cache = optimización futura si hot path revela latencia >5ms).

**Endpoints media/voice consumen el resolver vía dependency:**

```python
# backend/src/modules/copilot/api/dependencies.py — extender (existente o NEW si no hay)
from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

async def get_limits_resolver(
    db: Annotated[Session, Depends(get_db)],
) -> CopilotLimitsResolver:
    """DI: instancia repo sync-wrapped + resolver. NUNCA cachear cross-request."""
    from src.modules.copilot.infrastructure.repositories.tenant_limits_repository import (
        SyncCopilotTenantLimitsRepository,
    )
    return CopilotLimitsResolver(SyncCopilotTenantLimitsRepository(db))
```

**Hook en endpoints — flow:**

**Voice flow (`voice_upload_and_transcribe`):**
1. Recibe request → resolve `EffectiveLimits` por `tenant_id`.
2. Antes de leer body: `check_rate_limit(user_id=str(current_user.id), scope="copilot-voice", max_requests=limits.voice_rpm, window_seconds=60)`.
3. Si pasa: read body. Si `len(body) > limits.media_max_bytes`: raise `HTTPException(413, detail=...)`.
4. Continúa pipeline existente (Whisper transcribe + asset persist).
5. **Si `429`:** structlog `logger.warning("copilot_voice_rate_limit_hit", tenant_id=..., user_id=..., effective_rpm=..., is_override=...)`.

**Media upload flow (`upload_media`):**
1. Recibe request → resolve `EffectiveLimits` por `tenant_id`.
2. Antes de leer body: `check_rate_limit(user_id=str(current_user.id), scope="copilot-media-upload", max_requests=settings.COPILOT_MEDIA_UPLOAD_RATE_LIMIT_PER_MIN, window_seconds=60)`. Q5: hoy NO override per-tenant para media RPM (suficiente con default 30; agregar columna `media_upload_rpm_override` queda como out-of-scope, slot futuro).
3. Si pasa: read body. Si `len(body) > limits.media_max_bytes`: raise `HTTPException(413, detail=...)`.
4. Continúa pipeline existente (delegate to `AssetsService.upload_asset` → R2 + AI metadata).
5. **Si `429`:** structlog `logger.warning("copilot_media_upload_rate_limit_hit", tenant_id=..., user_id=..., effective_rpm=..., is_override=...)`.

**Legacy endpoint removal (Q1) — `voice/transcribe`:**
- `voice.py:45` `@router.post("/transcribe")` BORRADO completo. Imports muertos (`WhisperTranscriber` directo) limpiar si dejan de tener consumer.
- Ningún FE llama a este endpoint hoy (verificar `frontend/` con `grep -r "voice/transcribe"` antes de borrar — builder responsabilidad).
- Tests legacy del endpoint (`test_voice_transcribe_legacy.py` si existe) → BORRAR junto al endpoint.
- Decisión registrada en `decisions.md` PI-2.

**Idempotency en upserts admin:** `tenant_id` natural key + `updated_at` server-side stamp. Streamlit no necesita header idempotency (UI single-user).

## 8. Agentic Surfaces

**N/A — no se toca LangGraph, tools, prompts, ni `copilot_trace_event`.** El rate limiter es API-edge concern. **Invariantes copilot-expert respetadas:**

- ✅ Ratchet `copilot → módulo` 22 imports frozen — NO se agrega import cross-módulo nuevo.
- ✅ Cap `[COPILOT-*]` anchors 36/36 — NO se agregan anchors.
- ✅ Best-effort observability: rate-limit fallo Redis = `logger.exception` + allow request (preserva F8 patrón).
- ✅ Trazas honestas: si una request es rechazada con 429, se NO emite `turn_start`/`turn_end` (no se construyó turn). Solo structlog warning. Esto es correcto — el turn no existió.
- ✅ Sin LLM calls nuevos en hot path (rate limit es 1 RTT Redis, ~1ms p99).

## 9. Migration Notes

**Archivo:** `backend/alembic/versions/{YYYYMMDD}_HHMM_copilot_tenant_limits.py` (timestamp builder elige).

```python
"""copilot_tenant_limits — per-tenant rate limit + media cap overrides."""
from alembic import op

revision = "copilot_tenant_limits_001"
down_revision = "<HEAD_AT_BUILD_TIME>"  # builder fija
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabla principal
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_tenant_limits (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            voice_rpm_override INTEGER,
            media_max_bytes_override BIGINT,
            updated_by_user_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_voice_rpm_positive CHECK (voice_rpm_override IS NULL OR voice_rpm_override > 0),
            CONSTRAINT chk_media_max_bytes_positive CHECK (media_max_bytes_override IS NULL OR media_max_bytes_override > 0),
            CONSTRAINT chk_media_max_bytes_upper CHECK (media_max_bytes_override IS NULL OR media_max_bytes_override <= 104857600)  -- 100 MiB cap (Q4)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_copilot_tenant_limits_tenant_alive
        ON copilot_tenant_limits (tenant_id)
        WHERE deleted_at IS NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_updated_at
        ON copilot_tenant_limits (updated_at);
    """)

    # Tabla audit append-only (Q2)
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_tenant_limits_audit (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            action VARCHAR(16) NOT NULL,
            voice_rpm_before INTEGER,
            voice_rpm_after INTEGER,
            media_max_bytes_before BIGINT,
            media_max_bytes_after BIGINT,
            changed_by_user_id UUID,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_action_enum CHECK (action IN ('upsert','soft_delete'))
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_audit_tenant_id
        ON copilot_tenant_limits_audit (tenant_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_tenant_limits_audit_changed_at
        ON copilot_tenant_limits_audit (changed_at);
    """)
    # NOTA: Drop legacy /voice/transcribe (Q1) NO requiere migración DB —
    # endpoint sin tabla propia. Solo borrar handler + tests + imports muertos.


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS copilot_tenant_limits_audit;")
    op.execute("DROP TABLE IF EXISTS copilot_tenant_limits;")
```

**Test prod-clone obligatorio antes deploy:**

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REV> && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

**Backfill:** zero rows initial — table arranca vacía, todos los tenants usan env defaults. Listo en RESULT.md.

## 10. File Structure

```
backend/
├── src/
│   ├── core/
│   │   ├── config.py                                              [MODIFIED — +2 settings]
│   │   └── rate_limit.py                                          [UNCHANGED — reusado]
│   ├── modules/
│   │   └── copilot/
│   │       ├── domain/
│   │       │   └── tenant_limits.py                               [NEW]
│   │       ├── infrastructure/
│   │       │   ├── models/
│   │       │   │   ├── tenant_limits_model.py                     [NEW]
│   │       │   │   └── tenant_limits_audit_model.py               [NEW — Q2 audit append-only]
│   │       │   └── repositories/
│   │       │       └── tenant_limits_repository.py                [NEW — ABC + Async + Sync impls]
│   │       ├── application/
│   │       │   └── services/
│   │       │       └── limits_resolver.py                         [NEW]
│   │       └── api/
│   │           ├── dependencies.py                                [NEW or MODIFIED — get_limits_resolver]
│   │           ├── tenant_limits_dto.py                           [NEW]
│   │           ├── voice.py                                       [MODIFIED — rate limit + dynamic cap]
│   │           └── media.py                                       [MODIFIED — dynamic cap]
│   └── admin/
│       ├── app.py                                                 [MODIFIED — +PageSpec("copilot-limits")]
│       ├── pages/
│       │   └── copilot-limits.py                                  [NEW — wrapper]
│       └── modules/
│           └── copilot_limits.py                                  [NEW — render_copilot_limits_view]
├── alembic/versions/
│   └── {ts}_copilot_tenant_limits.py                              [NEW]
├── tests/
│   ├── modules/copilot/
│   │   ├── test_voice_rate_limit.py                               [NEW]
│   │   ├── test_voice_rate_limit_per_tenant_override.py           [NEW]
│   │   ├── test_media_max_bytes_env.py                            [NEW]
│   │   ├── test_media_max_bytes_per_tenant_override.py            [NEW]
│   │   ├── test_media_db_roundtrip.py                             [NEW — fixture db_session real]
│   │   ├── test_tenant_limits_repository.py                       [NEW]
│   │   └── test_limits_resolver.py                                [NEW]
│   ├── admin/
│   │   └── test_copilot_limits_smoke.py                           [NEW — render no-op smoke]
│   └── architecture/
│       └── test_admin_panel.py                                    [validates new page registered]
```

**Frontend Next.js:** sin cambios.

**Total LOC esperado** (aprox, sin tests): ~280 LOC nuevas + ~40 LOC modificadas. Cabe en 1 sesión builder.

## 11. Cross-Cutting Concerns

### Tenant isolation
- `CopilotTenantLimitsModel.tenant_id` mandatory. Repo `get_by_tenant(tenant_id)` filtra por `tenant_id` + `deleted_at IS NULL`. NO existe `get_by_id(id)` sin tenant — el natural key es `tenant_id` 1:1.
- Endpoints media/voice ya usan `get_current_user` (Bearer + X-Tenant-ID). Resolver hereda contexto.
- Streamlit admin **sí lee cross-tenant** (Chris audit) — usa `_shared.render_tenant_selector` existente.

### Currency / master-data
- `media_max_bytes_override` es bytes (BigInteger), no monetary. No aplica `currency`.
- `updated_at` `DateTime(timezone=True)` UTC siempre (regla `master-data.md`).

### PII
- DTO response no contiene PII (UUIDs + ints + datetimes).
- `updated_by_user_id` es UUID admin Nicolify, no exfiltrable a tenants (admin-only surface).
- structlog warnings con `tenant_id` + `user_id` (UUID) — sin email/phone.

### Spanish neutro LatAm
- `HTTPException` detail en español neutro (sin voseo): `"Demasiadas transcripciones. Espera N segundos."`, `"El audio excede el tamaño máximo de N MB."`
- Streamlit labels: `"Tenant"`, `"Voice RPM (override)"`, `"Media max bytes (override)"`, `"Limpiar override"`, `"Guardar"` — sin voseo.
- Logs internos en inglés (no aplica regla `spanish-text.md`).

### Native-first dev
- Tests via `cd backend && .venv/bin/pytest ...` — NUNCA `docker exec ruff/pytest`.
- Migration test prod-clone es la única excepción Docker (reglada en `.claude/rules/backend-migrations.md`).

### Idempotencia
- POST upsert via Streamlit → `tenant_id` natural key. Re-submit con mismo payload no crea fila duplicada (UNIQUE partial constraint).
- POST `/voice/upload-and-transcribe`: NO idempotente (audio único). Rate limit es la protección.

### Settings nuevas en `core/config.py`

```python
# ── Copilot media + voice limits (PI-2 S1 PR-1) ───────────────────────
COPILOT_MEDIA_MAX_BYTES: int = 25 * 1024 * 1024              # 25 MiB default — aplica a /media/upload + /voice/upload-and-transcribe
COPILOT_VOICE_RATE_LIMIT_PER_MIN: int = 6                    # requests/min default por user_id en scope "copilot-voice" (Q3 — margen seguridad cost: Whisper $0.006/min, audio max ~10 MiB ≈ 10 min → 6 RPM/tenant cap ~$0.36/min/tenant. Microempresarios no transcriben en ráfaga.)
    COPILOT_MEDIA_UPLOAD_RATE_LIMIT_PER_MIN: int = 30            # requests/min default por user_id en scope "copilot-media-upload" (Q5 — protección compute BE, costo solo upload sin LLM)
```

`extra = "ignore"` ya en Config — no rompe envs sin estas vars.

## 12. Architecture Fitness Impact

**Tests que correrán contra esta PR:**

| Test | Expectativa |
|---|---|
| `test_admin_panel.py::test_admin_pages_match_registry` | + `copilot-limits` en PAGE_SPECS y `pages/copilot-limits.py` |
| `test_admin_panel.py::test_admin_modules_have_render_function` | + `modules/copilot_limits.py` con `render_copilot_limits_view()` |
| `test_api_contracts.py` | endpoints voice/media siguen con `response_model=` (DTOs ya existentes inmutados) |
| `test_no_new_copilot_module_imports.py` | ratchet 22 frozen — NO se agregan imports `copilot → otro_módulo` |
| `test_copilot_anchors.py` | cap 36 — NO se agregan anchors `[COPILOT-*]` |
| `test_ddd_boundaries.py` | `copilot/domain/` imports puros (sin SQLAlchemy/FastAPI). `domain/tenant_limits.py` NEW debe respetarlo |
| `test_conventions.py` | `mapped_column` SA 2.0, no `Column()` legacy |
| `test_master_data_compliance.py` (si existe) | `DateTime(timezone=True)`, server_default `now()` |

**Allowlist updates:** ninguna. Allowlists shrink only — esta PR no introduce violación nueva.

**Test nuevo agregar a arch suite (opcional, builder evalúa):** `tests/architecture/test_copilot_limits_settings.py` — verifica `Settings` expone `COPILOT_MEDIA_MAX_BYTES` y `COPILOT_VOICE_RATE_LIMIT_PER_MIN` con types correctos. Bajo costo, alta protección contra regression.

## 13. pm-nico/current-state Updates Required

`docs/pm-nico/current-state/copilot.md`:

- Sección **"Capacidades actuales"** → append: `- Rate limit voice + per-tenant media/voice limits (admin Streamlit)`.
- Sección **"PIs históricos"** → append fila: `| PI-2 S1 | Voice/media hardening | 2026-04-{date} |` (PM completa al cerrar).
- Sección **"Decisiones producto vinculadas"** → append: `| 2026-04 | Per-tenant media/voice limits via Streamlit admin (no tenant-facing UI) | Protección quota Whisper + control gradual upgrade Pro tier |`.

PM ejecuta el update al cerrar el PR (post-merge).

## 14. Test Surfaces (TDD-mandatory)

**Orden RED-first por capa (obligatorio TDD):**

### Domain layer
- `test_tenant_limits_invariants.py` — invariants: rpm > 0, bytes > 0, sentinels None permitidos.

### Infrastructure layer
- `test_tenant_limits_repository.py` — async `get_by_tenant`, `upsert`, `soft_delete`, `list_overrides`. Fixture `db_session` async real (postgres docker).
- `test_tenant_limits_audit_repository.py` — Q2: cada `upsert` y `soft_delete` produce row audit atómica con before/after correctos. RED test: row audit count == operations count.
- `test_tenant_limits_model_migration.py` (opcional, lite) — migration aplica clean en sqlite-in-memory o snapshot SQL.

### Application layer
- `test_limits_resolver.py` — 4 casos: (a) sin override → env defaults; (b) override voice solo → voice override + media default; (c) override media solo; (d) ambos.

### API layer (integración HTTP + DB real per PR.md req)
- `test_voice_rate_limit.py` — 7 reqs/min con default 6 → req 7 retorna 429 + estructura JSON detail + header `Retry-After`. (Q3: default 6 RPM.)
- `test_voice_rate_limit_per_tenant_override.py` — tenant con override 20 → req 7 PASA, req 21 falla.
- `test_media_upload_rate_limit.py` — Q5: 31 reqs/min en `/media/upload` con default 30 → req 31 retorna 429. Bucket `copilot-media-upload` distinto de `copilot-voice` (verificar contadores aislados).
- `test_media_max_bytes_env.py` — env `COPILOT_MEDIA_MAX_BYTES=10485760` (10 MB) → upload 11 MB falla 413.
- `test_media_max_bytes_per_tenant_override.py` — tenant con override 50 MB → upload 30 MB pasa pese a env 10 MB. Cap upper enforce: override 200 MB → repo rechaza (DTO `le=104_857_600`, DB `chk_media_max_bytes_upper`). Q4.
- `test_media_db_roundtrip.py` — POST `/media/upload` → fixture `db_session` real (no MagicMock) → assert `assets` row + asset persistido + retorno DTO con UUID consultable. **Cubre req PR.md "≥1 test integración DB real"**.
- `test_voice_legacy_endpoint_removed.py` — Q1: GET/POST `/api/v1/copilot/voice/transcribe` retorna 404 (route no registrada). Imports `voice.py` no contienen `@router.post("/transcribe")`.

### Admin layer
- `test_copilot_limits_smoke.py` — Streamlit `render_copilot_limits_view()` no crashea (smoke). Pattern existing `test_admin_smoke.py` si lo hay; sino mock `streamlit` minimal.

### Architecture
- `test_admin_panel.py` (existente) verifica registry + render fn (gates auto).

## 15. Research Notes

**Patrón rate-limit Redis sliding window** — ya cementado en `core/rate_limit.py` desde 2026-Q1, validado en producción para `copilot-chat`. NO se reinventa. Skill `copilot-expert` confirma: "best-effort observability — Redis fail = log warning + allow request" (F8 patrón). Esta PR hereda comportamiento.

**Per-tenant override dinámico** — patrón estándar SaaS (Stripe Customer-level rate limits, Auth0 per-tenant quotas). Implementación local: tabla 1:1 con tenant + resolver-with-fallback. No hay framework needed. Tested pattern en codebase: `tenant_profile` BC ya hace algo similar para `business_types`.

**Streamlit admin extension** — patrón cementado (`tenants.py` template). 19 pages existentes siguen el mismo template `pages/{slug}.py` (5 LOC) → `modules/{name}.py::render_*()`. Arch test `test_admin_panel.py` valida.

Sin patrón novel introduciéndose. Sin web search needed.

## 16. Resolved questions (2026-04-29)

PM respondió 5 open questions. Decisiones aplicadas en secciones correspondientes.

| # | Pregunta | Decisión final | Sección impactada |
|---|---|---|---|
| Q1 | Rate limit `/voice/transcribe` legacy | **Eliminar endpoint legacy completo en este PR.** Cliente pequeño = barato corregir ahora. Solo `/voice/upload-and-transcribe` con rate limit. Ningún endpoint legacy preservado. | §4 (rutas), §7 (flow), §10 (file structure: borrar handler), §14 (test regresión 404) |
| Q2 | Audit log: row `updated_at` vs tabla separada | **Tabla separada `copilot_tenant_limits_audit` (append-only).** Architect decide: facilita queries históricas + review humano + no contamina tabla principal con write churn. | §2.b (modelo audit), §6 (repo contract atomic), §9 (migration), §10 (file structure), §14 (test append-only invariant) |
| Q3 | Default voice RPM: 10 o 20 | **Default 6 RPM/tenant.** Más económico sin perder calidad. Cálculo: Whisper $0.006/min, audio max ~10 MiB ≈ 10 min → 6 RPM cap ~$0.36/min/tenant ($0.60 con 10 RPM, $1.20 con 20 RPM). Microempresarios no transcriben en ráfaga. Override per-tenant cubre Pro tier. | §3 (DTO), §11 (settings `COPILOT_VOICE_RATE_LIMIT_PER_MIN=6`), §14 (test 7 reqs → 429) |
| Q4 | Cap upper `media_max_bytes_override`: 500 MiB | **100 MiB.** Estándar SaaS microempresarios (Slack/Notion/Intercom). 500 MiB excesivo para tier base. Editable a futuro vía slot `plan_id` (otro PI con planes Pro/Enterprise suelta el cap). Documentado como CHECK constraint editable. | §1 (invariantes), §3 (DTO `le=104_857_600`), §9 (migration `chk_media_max_bytes_upper`) |
| Q5 | `/media/upload` rate limit en PR-1 o S2 | **PR-1 (este PR).** Bucket separado `copilot-media-upload` (default 30 RPM > voice porque cost = solo upload, no LLM). Reusa `core/rate_limit.py`. Storage R2 ya existe (`AssetsService.upload_asset`); rate limit protege compute BE (parsing + AI metadata + R2 PUT), independiente de storage. `_MAX_FILE_BYTES` cap dinámico permanece independiente del rate limit. | §4 (ruta `/media/upload` rate limit), §7 (media flow nuevo), §11 (`COPILOT_MEDIA_UPLOAD_RATE_LIMIT_PER_MIN=30`), §14 (test bucket aislado) |

**Decisión diferida #2 (Prometheus metric)** — sin cambio: structlog only en este PR. PM no respondió → mantener recomendación architect.

---

<!-- @pm: CONTRACT.md updated with PM answers. Próximo paso: ejecutar prompts/02-builder-start.md o /pm "PR-1 ready for builder". -->
