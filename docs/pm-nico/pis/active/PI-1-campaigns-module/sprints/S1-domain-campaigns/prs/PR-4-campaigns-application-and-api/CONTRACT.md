# CONTRACT — PR-4-campaigns-application-and-api

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builder consume este archivo + sigue TDD por capa (application → api). Sin frontend (post PI-1).
> Status: **READY for builder**. Zero open questions (decisiones tomadas con framing 1000 clientes, cero deuda técnica).
> Sesión: 2026-04-29 — architect post-PR-3 (PASS, domain + repos shipped). Skills consultados: `backend-expert` (DDD inside-out + Pydantic v2 + response_model + master-data + arch-fitness), `copilot-expert` (anchor budget gating refleja `agent_kind="campaign"` Others pool — wire diferido S2), `sales-agent-expert` (anchor outbound gating sin regresión), `metrics-expert` (port `mv_daily_llm_cost_per_tenant_v2` UNION-ALL ya cubre `campaign_llm_call`, sin acción).
>
> Reglas duras: `tenant-isolation.md`, `backend-ddd.md`, `backend-migrations.md`, `architectural-fitness.md`, `master-data.md`, `currency-handling.md`, `tdd-mandatory.md`, `pii-sanitisation.md` (Tessl). PR-3 + S0 primitivas DISPONIBLES (`OutboxService`, `@idempotent`, `PlanService`, `BudgetGuard`, `OutboundRateLimiter`, `ComplianceService`, `mv_refresh_log`).

## 0. Context summary

| Campo | Valor |
|---|---|
| PR ID | PR-4-campaigns-application-and-api |
| PI / Sprint | PI-1-campaigns-module / S1-domain-campaigns |
| Modules tocados (write) | `modules/campaigns/application/` (NUEVO completo), `modules/campaigns/api/` (NUEVO completo), `shared/links/ports/campaigns.py` (NUEVO), `alembic/versions/112_campaigns_templates_seed.py` (NUEVO), `main.py` (MOD: include_router x3), `tests/modules/campaigns/{application,api}/` (NUEVOS), `tests/architecture/test_campaigns_*.py` (4 NUEVOS) |
| Modules tocados (read-only) | PR-3 domain + repos (`modules/campaigns/{domain,infrastructure}/`), S0 shared (`shared/{billing,compliance,domain_events,idempotency,links/ports/{crm,offer,brand,tenant_profile}}`), `iam/api/dependencies.py` (`get_tenant_context`, `get_current_user`), `core/database.py` (sessions) |
| Skills consulted | `backend-expert` (DDD inside-out, master-data, arch-fitness, currency-handling), `copilot-expert` (anchor budget gating ref OK — wire diferido S2), `sales-agent-expert` (anchor outbound gating ref OK — wire diferido S3), `metrics-expert` (MV registry-based UNION-ALL ya cubre `campaign_llm_call`, sin acción), `tessl/fastapi/pii-sanitisation` (response_model mandatorio, allowlist enforcement) |
| pm-nico/current-state files updates post-merge | `current-state/campaigns.md` — sección "Capacidades actuales" agregar capability "Application services + REST API + 5 templates seed shipped" con lineage PR-4 + bump fila Decisiones D6-D14 |
| Architecture gates que deben seguir verdes | `test_ddd_boundaries.py`, `test_outbox_invariants.py`, `test_no_new_copilot_module_imports.py` (ratchet 22 frozen), `test_sales_agent_tenant_isolation.py`, `test_folder_naming.py`, `test_api_contracts.py` (response_model + redirect_slashes=False), `test_master_data_compliance.py`, `test_currency_consistency.py`, `test_domain_purity.py` + 4 PR-3 (`test_campaigns_tenant_isolation.py`, `test_campaign_fsm_invariants.py`, `test_segment_filter_pydantic_validated.py`, `test_campaign_task_idx_workers.py`) |
| Architecture gates nuevos | `test_campaigns_api_response_model.py` (sin allowlist), `test_campaigns_pagination_default.py` (sin allowlist), `test_campaigns_fsm_service_layer.py` (sin allowlist), `test_segment_resolve_sql_filtering.py` (sin allowlist) |

**Riesgo principal:** primera capa expuesta vía HTTP en `campaigns/`. Mitigación: TDD por capa estricto (services RED-first → API RED-first) + 4 arch fitness tests RED-first + cache pattern reuso de `PlanService` (cementado PR-2) + service-layer FSM delegación enforced via arch test.

**Out of scope CONTRACT:**
- Cualquier ChannelRouter impl (Telegram/WhatsApp/Email) → S2
- Cualquier worker / orchestrator / scheduler ARQ → S2
- Real `launch()` end-to-end (segment resolve → task insert → enqueue) → S2 (PR-4 = STUB)
- Cualquier sales_agent OutboundOrchestrator wiring → S3
- Cualquier FE → post PI-1
- Cualquier copilot subagent / tools → PI-2
- Bulk operations (`POST /campaigns/bulk-cancel`, etc.)
- Wiring `BudgetGuard.check` / `OutboundRateLimiter.check` / `ComplianceService.check` en send path (worker S2)

---

## 1. Domain entities (sin cambio — heredadas PR-3)

PR-4 NO modifica entidades domain. Consume las shipped en PR-3:
- `Campaign` (aggregate root + FSM matrix `_FSM_TRANSITIONS` + `transition_allowed` classmethod).
- `CampaignStep` (DAG + `next_step_ids: list[UUID]` + polymorphic `step_config`).
- `CampaignTask` (NO touched in PR-4 — solo creación es S2 worker; PR-4 expone read-only stats si applica vía `count_by_campaign_status` repo method).
- `Segment` + `SegmentSnapshot` + `SegmentFilter` (PredefinedSegmentFilter v1 strict).
- `CampaignTemplate` (placeholder schema + `template_body JSONB`).
- 11 domain events declarados.

Si `nicolify-backend` necesita extender entities → STOP, escalar a architect (no es scope PR-4).

---

## 2. SQLAlchemy 2.0 models (sin cambio — heredados PR-3)

PR-4 NO crea ni modifica modelos SQLA. Solo consume `CampaignModel`, `CampaignStepModel`, `CampaignTaskModel`, `SegmentModel`, `SegmentSnapshotModel`, `CampaignTemplateModel` cementados en migration 111.

Migration nueva 112 = SOLO seed `campaign_template` (5 INSERTs). Sin DDL.

---

## 3. Pydantic v2 DTOs (`application/dtos/`)

Todos viven en `backend/src/modules/campaigns/application/dtos/`. **`model_config = ConfigDict(from_attributes=True, extra="forbid")`** mandatorio. Sin `Any`. Sin raw dicts en response. PII allowlist via `response_model=` enforcement (regla `pii-sanitisation.md`).

### 3.1 Pagination (`pagination.py`)

```python
from __future__ import annotations
from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated wrapper. Used by all list endpoints. limit/offset enforced at API layer."""

    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total_count: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)
    has_more: bool
```

### 3.2 Campaign DTOs (`campaign_dtos.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Annotated, Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType


class CampaignCreate(BaseModel):
    """POST /api/v1/campaigns/ request body."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    campaign_type: CampaignType
    segment_id: UUID | None = None
    channel_priority: list[str] = Field(default_factory=list, max_length=10)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    created_by_source: Literal["api", "copilot", "manual", "scheduler"] = "api"


class CampaignUpdate(BaseModel):
    """PATCH /api/v1/campaigns/{id} request body. Only DRAFT campaigns updatable.

    Service rejects with 409 Conflict if status != DRAFT.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    segment_id: UUID | None = None
    channel_priority: list[str] | None = Field(default=None, max_length=10)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None
    config: dict[str, Any] | None = None


class CampaignScheduleRequest(BaseModel):
    """POST /api/v1/campaigns/{id}/schedule body."""
    model_config = ConfigDict(extra="forbid")

    scheduled_for: dt.datetime  # UTC; service converts naive→UTC reject; FE sends ISO with offset


class CampaignCancelRequest(BaseModel):
    """POST /api/v1/campaigns/{id}/cancel body (optional reason)."""
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)


class CampaignResponse(BaseModel):
    """Full campaign read shape. PII allowlist."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    campaign_type: CampaignType
    status: CampaignStatus
    segment_id: UUID | None
    segment_snapshot_id: UUID | None
    channel_priority: list[str]
    offer_id: UUID | None
    brand_summary_id: UUID | None
    config: dict[str, Any]
    scheduled_at: dt.datetime | None
    launched_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_by_user_id: UUID | None
    created_by_source: str
    created_at: dt.datetime
    updated_at: dt.datetime


class CampaignLaunchResponse(BaseModel):
    """STUB notice — S2 wires real execution."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    campaign: CampaignResponse
    notice: str = Field(
        default=(
            "STUB launch: campaña marcada como running y evento "
            "campaigns.campaign.launched emitido vía outbox. La ejecución real "
            "(resolve segment + envío via ChannelRouter) la implementa el "
            "CampaignExecutionWorker en S2."
        ),
        description="Aviso explícito al integrador. NO toca este texto sin actualizar arch test.",
    )


CampaignStatusFilter = Annotated[
    list[CampaignStatus] | None,
    Field(default=None, description="Filtra por status. Multi-select."),
]
CampaignTypeFilter = Annotated[
    list[CampaignType] | None,
    Field(default=None, description="Filtra por type. Multi-select."),
]
CampaignSortBy = Literal["created_at_desc", "created_at_asc", "scheduled_at_desc", "scheduled_at_asc", "name_asc"]
```

### 3.3 CampaignStep DTOs (`campaign_step_dtos.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import StepType


class CampaignStepCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_type: StepType
    step_index: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_ids: list[UUID] = Field(default_factory=list)
    step_config: dict[str, Any] = Field(default_factory=dict)


class CampaignStepUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_index: int | None = Field(default=None, ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_ids: list[UUID] | None = None
    step_config: dict[str, Any] | None = None


class CampaignStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    step_type: StepType
    step_index: int
    label: str | None
    next_step_ids: list[UUID]
    step_config: dict[str, Any]
    created_at: dt.datetime
    updated_at: dt.datetime
```

### 3.4 Segment DTOs (`segment_dtos.py`)

```python
from __future__ import annotations
import datetime as dt
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter


class SegmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: PredefinedSegmentFilter


class SegmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    filter_dsl: PredefinedSegmentFilter | None = None


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    segment_type: SegmentType
    filter_dsl: PredefinedSegmentFilter
    estimated_size: int | None
    last_calculated_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


class SegmentResolveRequest(BaseModel):
    """POST /api/v1/segments/{id}/resolve body."""
    model_config = ConfigDict(extra="forbid")

    at: dt.datetime | None = Field(default=None, description="Punto en tiempo UTC. Default = now.")
    limit: int = Field(default=10_000, ge=1, le=100_000, description="Cap returned lead_ids; 100K hard cap.")


class SegmentResolveResponse(BaseModel):
    """Returned UUIDs (NO PII). emails/phones masked en evidence si aparecen."""
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    segment_id: UUID
    at: dt.datetime
    lead_count: int
    lead_ids: list[UUID]
    truncated: bool = False  # True si lead_count > limit
    # NO incluimos emails/phones — solo UUIDs (no PII intrínseca).


class SegmentSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    segment_id: UUID
    snapshotted_at: dt.datetime
    lead_count: int
    # lead_ids deliberately omitted from response (potentially huge); fetch via dedicated endpoint S2 if needed.


class SegmentEstimateSizeResponse(BaseModel):
    """GET /api/v1/segments/{id}/estimate-size — quick count via cached query."""
    model_config = ConfigDict(extra="forbid")

    segment_id: UUID
    estimated_size: int
    cached_at: dt.datetime
    cache_hit: bool
```

### 3.5 CampaignTemplate DTOs (`campaign_template_dtos.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import CampaignType


class CampaignTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID | None  # NULL = global Nicolify-provided
    slug: str
    name: str
    description: str
    campaign_type: CampaignType
    template_body: dict[str, Any]
    recommended_segment_slugs: list[str]
    tags: list[str]
    version: int
    created_at: dt.datetime
    updated_at: dt.datetime


class CampaignCreateFromTemplate(BaseModel):
    """POST /api/v1/templates/{id}/clone body."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="Nombre de la nueva campaña instanciada.")
    segment_id: UUID
    offer_id: UUID | None = None
    scheduled_for: dt.datetime | None = Field(
        default=None,
        description="Si se provee, la campaña queda en SCHEDULED post-clone. Si NULL, queda en DRAFT.",
    )
    description: str | None = Field(default=None, max_length=2000)
    config_overrides: dict[str, Any] = Field(default_factory=dict, description="Merge sobre template_body.config.")
```

**Template body JSONB schema (validador interno service layer):**

```python
# application/services/campaign_template_service.py — internal helper Pydantic model.
class CampaignTemplateBody(BaseModel):
    """Validador del template_body JSONB. NO expuesto en response (solo dict[str, Any] al integrador)."""
    model_config = ConfigDict(extra="forbid")

    description_internal: str | None = None
    suggested_channel_priority: list[str] = Field(default_factory=list)
    config_defaults: dict[str, Any] = Field(default_factory=dict)
    steps: list["CampaignTemplateStepBody"]


class CampaignTemplateStepBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_type: StepType
    step_index: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=128)
    next_step_indexes: list[int] = Field(default_factory=list, description="Índices ref a otros steps (no UUIDs — instanciados en clone).")
    step_config: dict[str, Any] = Field(default_factory=dict)
```

`clone_to_campaign` resuelve `next_step_indexes` → `next_step_ids: list[UUID]` al instanciar (mapping index→generated UUID).

---

## 4. API routes

Todas montan en `/api/v1/{campaigns|segments|templates}/...`. **Bearer + X-Tenant-ID required en TODA ruta** (Depends `get_current_user` + `get_tenant_context`). `redirect_slashes=False` heredado de `main.py` (ya cementado, arch test enforce).

| Method | Path | Auth | Request DTO | response_model | Status codes | Description |
|---|---|---|---|---|---|---|
| POST | `/api/v1/campaigns/` | Bearer + X-Tenant-ID | `CampaignCreate` | `CampaignResponse` | 201 / 400 / 401 / 402 / 409 | Create DRAFT campaign. Valida `max_campaigns_active` (PlanService). 402 si excede plan. 409 si name duplicate. Idempotency-Key opt-in. Emite `CampaignCreated` via outbox. |
| GET | `/api/v1/campaigns/` | idem | — | `PaginatedResponse[CampaignResponse]` | 200 / 401 | List paginated `?status=&type=&limit=20&offset=0&sort_by=created_at_desc`. Cache 30s in-mem + Redis pub/sub invalidation. |
| GET | `/api/v1/campaigns/{id}` | idem | — | `CampaignResponse` | 200 / 401 / 404 | Get one. |
| PATCH | `/api/v1/campaigns/{id}` | idem | `CampaignUpdate` | `CampaignResponse` | 200 / 401 / 404 / 409 | Update. 409 si status != DRAFT. Emite `CampaignUpdated` (no en domain events PR-3 list — se agrega como subscriber-side log only; ver §5). |
| DELETE | `/api/v1/campaigns/{id}` | idem | — | — (204) | 204 / 401 / 404 / 409 | Soft delete. 409 NO se rechaza por status (cancel implícito si running/paused). Si running/paused → cancel transition primero + soft delete. Emite `CampaignCanceled`. |
| POST | `/api/v1/campaigns/{id}/schedule` | idem | `CampaignScheduleRequest` | `CampaignResponse` | 200 / 401 / 404 / 409 | DRAFT → SCHEDULED. Valida segment_id NOT NULL. AGENT_CONVERSATION valida offer_id NOT NULL. Emite `CampaignScheduled`. |
| POST | `/api/v1/campaigns/{id}/launch` | idem | — | `CampaignLaunchResponse` | 200 / 401 / 404 / 409 | SCHEDULED → RUNNING **STUB**. Marca `launched_at` + emite `CampaignLaunched`. Notice explícito en response. |
| POST | `/api/v1/campaigns/{id}/pause` | idem | — | `CampaignResponse` | 200 / 401 / 404 / 409 | RUNNING → PAUSED. Idempotente: PAUSED → PAUSED = 200 silent. Emite `CampaignPaused`. |
| POST | `/api/v1/campaigns/{id}/resume` | idem | — | `CampaignResponse` | 200 / 401 / 404 / 409 | PAUSED → RUNNING. Idempotente: RUNNING → RUNNING = 200 silent. Emite `CampaignLaunched` (re-launch semantic). |
| POST | `/api/v1/campaigns/{id}/complete` | idem | — | `CampaignResponse` | 200 / 401 / 404 / 409 | RUNNING → COMPLETED (terminal). Emite `CampaignCompleted`. |
| POST | `/api/v1/campaigns/{id}/cancel` | idem | `CampaignCancelRequest` | `CampaignResponse` | 200 / 401 / 404 / 409 | * → CANCELED (terminal). Emite `CampaignCanceled` con `reason`. |
| POST | `/api/v1/campaigns/{id}/steps/` | idem | `CampaignStepCreate` | `CampaignStepResponse` | 201 / 401 / 404 / 409 | Add step. 409 si campaign.status != DRAFT. Emite `CampaignStepAdded`. |
| PATCH | `/api/v1/campaigns/{id}/steps/{step_id}` | idem | `CampaignStepUpdate` | `CampaignStepResponse` | 200 / 401 / 404 / 409 | Update step. 409 si campaign.status != DRAFT. Emite `CampaignStepUpdated`. |
| DELETE | `/api/v1/campaigns/{id}/steps/{step_id}` | idem | — | — (204) | 204 / 401 / 404 / 409 | Soft delete step. 409 si campaign.status != DRAFT. |
| GET | `/api/v1/segments/` | idem | — | `PaginatedResponse[SegmentResponse]` | 200 / 401 | List paginated. |
| POST | `/api/v1/segments/` | idem | `SegmentCreate` | `SegmentResponse` | 201 / 400 / 401 / 409 | Create. 409 si name dup en tenant alive. Emite `SegmentCreated`. |
| GET | `/api/v1/segments/{id}` | idem | — | `SegmentResponse` | 200 / 401 / 404 | Get one. |
| PATCH | `/api/v1/segments/{id}` | idem | `SegmentUpdate` | `SegmentResponse` | 200 / 401 / 404 / 409 | Update. Invalida `estimate_size` cache. |
| DELETE | `/api/v1/segments/{id}` | idem | — | — (204) | 204 / 401 / 404 | Soft delete. |
| POST | `/api/v1/segments/{id}/resolve` | idem | `SegmentResolveRequest` | `SegmentResolveResponse` | 200 / 401 / 404 | Lazy resolve. SQL-side filtering escalable. Cap `limit` 100K. Returns `truncated=True` si excede. |
| GET | `/api/v1/segments/{id}/estimate-size` | idem | — | `SegmentEstimateSizeResponse` | 200 / 401 / 404 | Cached count 5min. |
| POST | `/api/v1/segments/{id}/snapshot` | idem | — | `SegmentSnapshotResponse` | 201 / 401 / 404 | Materialize. Emite `SegmentSnapshotted`. NO idempotente (cada snapshot punto en tiempo distinto). |
| GET | `/api/v1/templates/` | idem | — | `list[CampaignTemplateResponse]` | 200 / 401 | UNION globals + tenant. Cache 5min. NO paginated (catálogo pequeño). |
| GET | `/api/v1/templates/{id}` | idem | — | `CampaignTemplateResponse` | 200 / 401 / 404 | Single template (global o tenant). |
| POST | `/api/v1/templates/{id}/clone` | idem | `CampaignCreateFromTemplate` | `CampaignResponse` | 201 / 400 / 401 / 404 / 409 | Clone → Campaign + Steps en TX. Idempotency-Key opt-in. |

**Header behavior:**
- `Authorization: Bearer <clerk_token>` — required (`get_current_user`).
- `X-Tenant-ID: <uuid|slug>` — required (`get_tenant_context`).
- `Idempotency-Key: <uuid>` — opcional. Cuando presente, decorator `@idempotent` cachea respuesta 24h.
- `Content-Type: application/json` — required en POST/PATCH.

**Error envelope (heredado convención):** `{"detail": str}` para 4xx/5xx (FastAPI default + structlog log).

---

## 5. Application services (`application/services/`)

### 5.1 `CampaignService` — `application/services/campaign_service.py`

```python
from __future__ import annotations
import datetime as dt
from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

import structlog
from cachetools import TTLCache
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.application.dtos.campaign_dtos import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignSortBy,
)
from src.modules.campaigns.application.dtos.pagination import PaginatedResponse
from src.modules.campaigns.application.services.cache import CacheBackend
from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType
from src.modules.campaigns.domain.events import (
    CampaignCreated, CampaignScheduled, CampaignLaunched,
    CampaignPaused, CampaignCompleted, CampaignCanceled,
)
from src.modules.campaigns.domain.repositories import (
    CampaignRepository, CampaignStepRepository, SegmentRepository,
)
from src.shared.billing.application.plan_service import PlanService
from src.shared.domain.master_data import utc_now
from src.shared.domain_events.outbox.application.outbox_service import OutboxService

logger = structlog.get_logger(__name__)


class CampaignServiceError(Exception):
    """Base for application errors mapped at API layer to HTTP codes."""

class CampaignNotFoundError(CampaignServiceError): pass
class CampaignDuplicateNameError(CampaignServiceError): pass
class CampaignInvalidTransitionError(CampaignServiceError): pass
class CampaignNotEditableError(CampaignServiceError): pass
class CampaignPlanLimitExceededError(CampaignServiceError): pass
class CampaignInvariantError(CampaignServiceError): pass


class CampaignService:
    """CRUD + lifecycle FSM for Campaign aggregate.

    Invariants:
    - Tenant-scoped on every operation.
    - FSM transitions delegated to Campaign.transition_allowed() (PR-3 cementado).
      Service NEVER duplicates the FSM dict (arch test enforce).
    - Each FSM transition emits exactly one domain event via OutboxService.
    - List endpoint cached 30s per (tenant_id, filters_hash) with Redis pub/sub
      invalidation cross-instance (mirror PlanService PR-2 pattern).
    - max_campaigns_active per plan validated pre-create via PlanService.
    """

    LIST_CACHE_TTL = 30  # seconds
    LIST_CACHE_MAX_ENTRIES = 4_096  # ~50KB / 1000 tenants

    def __init__(
        self,
        *,
        repo: CampaignRepository,
        step_repo: CampaignStepRepository,
        segment_repo: SegmentRepository,
        plan_service: PlanService,
        outbox_service: OutboxService,
        cache: CacheBackend,
    ) -> None:
        self._repo = repo
        self._step_repo = step_repo
        self._segment_repo = segment_repo
        self._plan_service = plan_service
        self._outbox_service = outbox_service
        self._cache = cache

    async def create(
        self, tenant_id: UUID, dto: CampaignCreate, *,
        session: AsyncSession, user_id: UUID | None = None,
    ) -> Campaign:
        """Create DRAFT campaign.

        Raises:
        - CampaignPlanLimitExceededError → 402
        - CampaignDuplicateNameError → 409
        """
        # 1. Plan limit check
        plan = await self._plan_service.get_effective(tenant_id)
        if plan.max_campaigns_active is not None:
            current = await self._repo.list_by_tenant(
                tenant_id, session=session, limit=1, offset=0,
                status_filter=[CampaignStatus.DRAFT, CampaignStatus.SCHEDULED, CampaignStatus.RUNNING, CampaignStatus.PAUSED],
            )
            # Replace by count_by_tenant_active in repo if list is heavy — see §6 repo extension proposal.
            count_active = await self._repo.count_active(tenant_id, session=session)  # NEW repo method (see §6)
            if count_active >= plan.max_campaigns_active:
                raise CampaignPlanLimitExceededError(
                    f"plan {plan.plan_id} cap {plan.max_campaigns_active} alcanzado",
                )
        # 2. Validate segment if provided
        if dto.segment_id is not None:
            seg = await self._segment_repo.get_by_id(dto.segment_id, tenant_id, session=session)
            if seg is None:
                raise CampaignServiceError("segment_id no encontrado")
        # 3. Persist
        now = utc_now()
        campaign = Campaign(
            id=uuid4(),
            tenant_id=tenant_id,
            name=dto.name,
            description=dto.description,
            campaign_type=dto.campaign_type,
            status=CampaignStatus.DRAFT,
            segment_id=dto.segment_id,
            channel_priority=dto.channel_priority,
            offer_id=dto.offer_id,
            brand_summary_id=dto.brand_summary_id,
            config=dto.config,
            created_by_user_id=user_id,
            created_by_source=dto.created_by_source,
            created_at=now,
            updated_at=now,
        )
        try:
            await self._repo.append(campaign, session=session)
        except Exception as exc:  # IntegrityError unique idx
            if "uq_campaign" in str(exc).lower() or "duplicate" in str(exc).lower():
                raise CampaignDuplicateNameError(dto.name) from exc
            raise
        # 4. Emit event via outbox (transactional — caller commits session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignCreated(tenant_id=tenant_id, campaign_id=campaign.id, occurred_at=now),
            session=session,
        )
        # 5. Invalidate cache
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return campaign

    async def get(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> Campaign:
        c = await self._repo.get_by_id(campaign_id, tenant_id, session=session)
        if c is None or c.deleted_at is not None:
            raise CampaignNotFoundError(str(campaign_id))
        return c

    async def list(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        status_filter: Sequence[CampaignStatus] | None = None,
        type_filter: Sequence[CampaignType] | None = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: CampaignSortBy = "created_at_desc",
    ) -> PaginatedResponse[CampaignResponse]:
        """Paginated list with filters. Cached 30s.

        limit hard-capped at 100 (API layer enforces; service double-checks).
        """
        if not (1 <= limit <= 100):
            raise CampaignServiceError("limit fuera de rango [1, 100]")
        if offset < 0:
            raise CampaignServiceError("offset negativo")
        cache_key = f"campaigns:list:{tenant_id}:{_filters_hash(status_filter, type_filter, limit, offset, sort_by)}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        items = await self._repo.list_by_tenant(
            tenant_id, session=session, limit=limit, offset=offset,
            status_filter=status_filter,
            # type_filter + sort_by → repo extension §6
        )
        total = await self._repo.count_by_tenant(
            tenant_id, session=session, status_filter=status_filter,
        )  # NEW repo method §6
        response = PaginatedResponse[CampaignResponse](
            items=[CampaignResponse.model_validate(c) for c in items],
            total_count=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )
        await self._cache.set(cache_key, response, ttl=self.LIST_CACHE_TTL)
        return response

    async def update(
        self, tenant_id: UUID, campaign_id: UUID, dto: CampaignUpdate,
        *, session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status != CampaignStatus.DRAFT:
            raise CampaignNotEditableError(f"campaign en {c.status.value} no editable")
        # Apply partial update (Pydantic update copy)
        updated = c.model_copy(update={
            **dto.model_dump(exclude_unset=True),
            "updated_at": utc_now(),
        })
        await self._repo.update(updated, session=session)
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        # No domain event for "updated" in PR-3 list (intentional — observability layer
        # tracks via repo logger). Subscribers que necesiten update events lo agregan
        # post-PI-1 con migration aditiva.
        return updated

    async def delete(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> None:
        """Soft delete. If running/paused → emit CampaignCanceled first."""
        c = await self.get(tenant_id, campaign_id, session=session)
        now = utc_now()
        if c.status in (CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.SCHEDULED):
            # Implicit cancel — preserve audit trail
            await self._outbox_service.enqueue_async_from_sync_caller(
                CampaignCanceled(
                    tenant_id=tenant_id, campaign_id=campaign_id,
                    occurred_at=now, canceled_at=now, reason="implicit_delete",
                ),
                session=session,
            )
        await self._repo.soft_delete(campaign_id, tenant_id, session=session)
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")

    # ── FSM transitions ────────────────────────────────────────────────────

    async def schedule(
        self, tenant_id: UUID, campaign_id: UUID, scheduled_for: dt.datetime,
        *, session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        self._enforce_transition(c, CampaignStatus.SCHEDULED)
        # Pre-flight invariants (Campaign model_validator will enforce)
        if c.segment_id is None:
            raise CampaignInvariantError("schedule requiere segment_id")
        if c.campaign_type == CampaignType.AGENT_CONVERSATION and c.offer_id is None:
            raise CampaignInvariantError("AGENT_CONVERSATION requiere offer_id")
        if scheduled_for.tzinfo is None:
            raise CampaignServiceError("scheduled_for debe ser timezone-aware (UTC)")
        now = utc_now()
        updated = c.model_copy(update={
            "status": CampaignStatus.SCHEDULED,
            "scheduled_at": scheduled_for,
            "updated_at": now,
        })
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignScheduled(
                tenant_id=tenant_id, campaign_id=campaign_id,
                occurred_at=now, scheduled_at=scheduled_for,
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    async def launch(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> Campaign:
        """STUB launch. Marks RUNNING + emits event. S2 wires real execution."""
        c = await self.get(tenant_id, campaign_id, session=session)
        # Idempotent: if already RUNNING, return current
        if c.status == CampaignStatus.RUNNING:
            logger.info("campaign_launch_idempotent_noop", tenant_id=str(tenant_id), campaign_id=str(campaign_id))
            return c
        self._enforce_transition(c, CampaignStatus.RUNNING)
        now = utc_now()
        updated = c.model_copy(update={
            "status": CampaignStatus.RUNNING,
            "launched_at": now if c.launched_at is None else c.launched_at,
            "updated_at": now,
        })
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignLaunched(
                tenant_id=tenant_id, campaign_id=campaign_id,
                occurred_at=now, launched_at=updated.launched_at,
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    async def pause(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.PAUSED:
            return c  # idempotent
        self._enforce_transition(c, CampaignStatus.PAUSED)
        now = utc_now()
        updated = c.model_copy(update={"status": CampaignStatus.PAUSED, "updated_at": now})
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignPaused(tenant_id=tenant_id, campaign_id=campaign_id, occurred_at=now),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    async def resume(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.RUNNING:
            return c
        self._enforce_transition(c, CampaignStatus.RUNNING)
        now = utc_now()
        updated = c.model_copy(update={"status": CampaignStatus.RUNNING, "updated_at": now})
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignLaunched(  # re-launch semantic
                tenant_id=tenant_id, campaign_id=campaign_id,
                occurred_at=now, launched_at=updated.launched_at or now,
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    async def complete(
        self, tenant_id: UUID, campaign_id: UUID, *, session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        self._enforce_transition(c, CampaignStatus.COMPLETED)
        now = utc_now()
        updated = c.model_copy(update={
            "status": CampaignStatus.COMPLETED, "completed_at": now, "updated_at": now,
        })
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignCompleted(tenant_id=tenant_id, campaign_id=campaign_id, occurred_at=now, completed_at=now),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    async def cancel(
        self, tenant_id: UUID, campaign_id: UUID, *, reason: str | None = None,
        session: AsyncSession,
    ) -> Campaign:
        c = await self.get(tenant_id, campaign_id, session=session)
        if c.status == CampaignStatus.CANCELED:
            return c  # idempotent
        self._enforce_transition(c, CampaignStatus.CANCELED)
        now = utc_now()
        updated = c.model_copy(update={
            "status": CampaignStatus.CANCELED, "completed_at": now, "updated_at": now,
        })
        await self._repo.update(updated, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            CampaignCanceled(
                tenant_id=tenant_id, campaign_id=campaign_id,
                occurred_at=now, canceled_at=now, reason=reason,
            ),
            session=session,
        )
        await self._cache.invalidate_pattern(f"campaigns:list:{tenant_id}:*")
        return updated

    # ── Step CRUD (cohesionado en CampaignService) ─────────────────────────

    async def add_step(
        self, tenant_id: UUID, campaign_id: UUID, dto: CampaignStepCreate,
        *, session: AsyncSession,
    ) -> CampaignStep: ...  # impl: validates campaign.status==DRAFT, builds CampaignStep, persists, emits CampaignStepAdded

    async def update_step(
        self, tenant_id: UUID, campaign_id: UUID, step_id: UUID, dto: CampaignStepUpdate,
        *, session: AsyncSession,
    ) -> CampaignStep: ...

    async def delete_step(
        self, tenant_id: UUID, campaign_id: UUID, step_id: UUID,
        *, session: AsyncSession,
    ) -> None: ...

    # ── FSM helper (delegates to domain SSoT) ──────────────────────────────

    @staticmethod
    def _enforce_transition(c: Campaign, to_status: CampaignStatus) -> None:
        """Delegates to Campaign.transition_allowed (PR-3 cementado).

        Service NEVER hardcodes the FSM dict — arch test enforce.
        """
        if not Campaign.transition_allowed(c.status, to_status):
            raise CampaignInvalidTransitionError(
                f"transición {c.status.value} → {to_status.value} no permitida",
            )


def _filters_hash(
    status_filter, type_filter, limit, offset, sort_by,
) -> str:
    """Stable hash for cache key. Order-invariant for sequences."""
    parts = []
    parts.append("|".join(sorted(s.value for s in status_filter)) if status_filter else "")
    parts.append("|".join(sorted(t.value for t in type_filter)) if type_filter else "")
    parts.append(str(limit))
    parts.append(str(offset))
    parts.append(sort_by)
    return ":".join(parts)
```

### 5.2 `SegmentService` — `application/services/segment_service.py`

```python
class SegmentNotFoundError(Exception): pass
class SegmentDuplicateNameError(Exception): pass


class SegmentService:
    """CRUD + lazy resolve + estimate_size + opt-in snapshot.

    Production-grade: resolve() compiles SegmentFilter → SQL WHERE clauses
    (NEVER loads leads in Python). estimate_size cached 5min.
    """

    ESTIMATE_CACHE_TTL = 300  # 5 min

    def __init__(
        self,
        *,
        repo: SegmentRepository,
        snapshot_repo: SegmentSnapshotRepository,
        lead_query_port: LeadQueryPort,        # see §5.4 — implemented by crm adapter
        filter_evaluator: SegmentFilterEvaluator,
        outbox_service: OutboxService,
        cache: CacheBackend,
    ) -> None: ...

    async def create(
        self, tenant_id: UUID, dto: SegmentCreate, *, session: AsyncSession,
    ) -> Segment: ...

    async def update(
        self, tenant_id: UUID, segment_id: UUID, dto: SegmentUpdate,
        *, session: AsyncSession,
    ) -> Segment: ...

    async def get(
        self, tenant_id: UUID, segment_id: UUID, *, session: AsyncSession,
    ) -> Segment: ...

    async def list(
        self, tenant_id: UUID, *, session: AsyncSession, limit: int = 20, offset: int = 0,
    ) -> PaginatedResponse[SegmentResponse]: ...

    async def delete(
        self, tenant_id: UUID, segment_id: UUID, *, session: AsyncSession,
    ) -> None: ...

    async def resolve(
        self, tenant_id: UUID, segment_id: UUID,
        *, at: dt.datetime | None = None, limit: int = 10_000,
        session: AsyncSession,
    ) -> tuple[list[UUID], int, bool]:
        """SQL-side filtering. NEVER loads leads in Python.

        Returns:
            (lead_ids, lead_count, truncated)
            truncated=True if total exceeds limit (caller decides snapshot vs paginated walk).
        """
        seg = await self.get(tenant_id, segment_id, session=session)
        # 1. Compile filter_dsl → SQL predicate (pure function)
        predicate = self._filter_evaluator.to_sql_predicate(seg.filter_dsl, tenant_id=tenant_id, at=at)
        # 2. Delegate to LeadQueryPort (implemented by crm adapter — paginated batches if huge)
        lead_ids, total = await self._lead_query_port.list_lead_ids_matching(
            tenant_id=tenant_id, predicate=predicate, limit=limit, session=session,
        )
        return lead_ids, total, total > limit

    async def estimate_size(
        self, tenant_id: UUID, segment_id: UUID, *, session: AsyncSession,
    ) -> tuple[int, dt.datetime, bool]:
        """Cached count. Returns (estimated_size, cached_at, cache_hit)."""
        cache_key = f"segments:estimate:{tenant_id}:{segment_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached["size"], cached["at"], True
        seg = await self.get(tenant_id, segment_id, session=session)
        predicate = self._filter_evaluator.to_sql_predicate(seg.filter_dsl, tenant_id=tenant_id)
        size = await self._lead_query_port.count_leads_matching(
            tenant_id=tenant_id, predicate=predicate, session=session,
        )
        now = utc_now()
        await self._cache.set(cache_key, {"size": size, "at": now}, ttl=self.ESTIMATE_CACHE_TTL)
        # Persist hint on segment (optional — async best-effort)
        await self._repo.update(
            seg.model_copy(update={"estimated_size": size, "last_calculated_at": now}),
            session=session,
        )
        return size, now, False

    async def snapshot(
        self, tenant_id: UUID, segment_id: UUID, *, session: AsyncSession,
        max_lead_ids: int = 100_000,
    ) -> SegmentSnapshot:
        """Materialize. Emits SegmentSnapshotted event."""
        lead_ids, total, truncated = await self.resolve(
            tenant_id, segment_id, limit=max_lead_ids, session=session,
        )
        if truncated:
            logger.warning(
                "segment_snapshot_truncated",
                tenant_id=str(tenant_id), segment_id=str(segment_id),
                total=total, cap=max_lead_ids,
            )
        now = utc_now()
        snap = SegmentSnapshot(
            id=uuid4(),
            tenant_id=tenant_id,
            segment_id=segment_id,
            snapshotted_at=now,
            lead_ids=lead_ids,
            lead_count=len(lead_ids),
            created_at=now,
        )
        await self._snapshot_repo.append(snap, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            SegmentSnapshotted(
                tenant_id=tenant_id, segment_id=segment_id, snapshot_id=snap.id,
                lead_count=snap.lead_count, occurred_at=now,
            ),
            session=session,
        )
        return snap
```

### 5.3 `SegmentFilterEvaluator` — `application/services/segment_filter_evaluator.py`

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, ColumnElement, Boolean
from sqlalchemy.dialects.postgresql import JSONB

from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter
from src.modules.campaigns.domain.enums import SegmentFilterCombinator
from src.shared.infrastructure.models.crm import LeadModel  # READ-only consumption


class SegmentFilterEvaluator:
    """Pure-function compiler: PredefinedSegmentFilter → SQLA ColumnElement.

    SSoT for segment-filter semantics. SQL-side (production-grade 1000 clientes)
    + in-memory (testing).

    NEVER loads leads in Python. NEVER constructs SQL strings (uses SQLA expressions only).
    """

    def to_sql_predicate(
        self,
        filter_dsl: PredefinedSegmentFilter,
        *,
        tenant_id: UUID,
        at: dt.datetime | None = None,
    ) -> ColumnElement[Boolean]:
        """Compose SQL WHERE predicate. Caller appends LeadModel.tenant_id == tenant_id.

        Combinator semantics:
        - filter_dsl.combinator == ALL → AND across all non-None fields
        - filter_dsl.combinator == ANY → OR across all non-None fields
        """
        clauses: list[ColumnElement[Boolean]] = []

        if filter_dsl.lifecycle_stage:
            clauses.append(LeadModel.lifecycle_stage.in_(filter_dsl.lifecycle_stage))
        if filter_dsl.temperature:
            clauses.append(LeadModel.temperature.in_(filter_dsl.temperature))
        if filter_dsl.score_range:
            sr = filter_dsl.score_range
            if sr.fit_score_min is not None:
                clauses.append(LeadModel.fit_score >= sr.fit_score_min)
            if sr.fit_score_max is not None:
                clauses.append(LeadModel.fit_score <= sr.fit_score_max)
            if sr.intent_score_min is not None:
                clauses.append(LeadModel.intent_score >= sr.intent_score_min)
            if sr.intent_score_max is not None:
                clauses.append(LeadModel.intent_score <= sr.intent_score_max)
        if filter_dsl.source:
            clauses.append(LeadModel.source.in_(filter_dsl.source))
        if filter_dsl.country:
            # ISO 3166-1 alpha-2 lowercase invariant (PR-2 ALTER + PR-3 SegmentFilter D4)
            clauses.append(LeadModel.country.in_([c.lower() for c in filter_dsl.country]))
        if filter_dsl.created_at_range:
            cr = filter_dsl.created_at_range
            if cr.gte is not None:
                clauses.append(LeadModel.created_at >= cr.gte)
            if cr.lte is not None:
                clauses.append(LeadModel.created_at <= cr.lte)
        if filter_dsl.last_interaction_at_range:
            lr = filter_dsl.last_interaction_at_range
            if lr.gte is not None:
                clauses.append(LeadModel.last_interaction_at >= lr.gte)
            if lr.lte is not None:
                clauses.append(LeadModel.last_interaction_at <= lr.lte)
        if filter_dsl.tags:
            tf = filter_dsl.tags
            if tf.tags:
                # leads.tags is JSONB array; use ?| (any) and ?& (all) operators
                if tf.mode == "any":
                    clauses.append(LeadModel.tags.op("?|")(tf.tags))
                else:  # "all"
                    clauses.append(LeadModel.tags.op("?&")(tf.tags))
        if filter_dsl.is_blacklisted is not None:
            clauses.append(LeadModel.is_blacklisted == filter_dsl.is_blacklisted)
        if filter_dsl.has_channel_id:
            # Each channel_identifier name maps to a column on leads (telegram_id, whatsapp_id, ...)
            channel_clauses = []
            for ch in filter_dsl.has_channel_id:
                col = getattr(LeadModel, ch, None)
                if col is None:
                    raise ValueError(f"channel column {ch} no existe en LeadModel")
                channel_clauses.append(col.is_not(None))
            clauses.append(or_(*channel_clauses) if len(channel_clauses) > 1 else channel_clauses[0])

        if not clauses:
            # Empty filter — match nothing (safer default than match-all)
            from sqlalchemy import false
            return false()

        if filter_dsl.combinator == SegmentFilterCombinator.ANY:
            return or_(*clauses)
        return and_(*clauses)

    def evaluate_one(
        self,
        filter_dsl: PredefinedSegmentFilter,
        lead: dict[str, Any],
    ) -> bool:
        """In-memory eval (tests + edge cases). lead is dict-like LeadModel snapshot."""
        # ... mirror semantics above using Python operators
        ...
```

**`LeadModel.country` invariant:** PR-2 ALTER agregó column. Si arch test falla porque `LeadModel.country` no existe en SSoT crm, builder STOP y escala (deuda PR-2 sin cerrar).

### 5.4 `LeadQueryPort` — `application/ports/lead_query_port.py`

```python
from __future__ import annotations
from typing import Protocol
from uuid import UUID

from sqlalchemy import ColumnElement, Boolean
from sqlalchemy.ext.asyncio import AsyncSession


class LeadQueryPort(Protocol):
    """Port consumed by SegmentService. Implementation in shared/links/ports/crm
    adapter (crm module owns LeadModel storage). Protocol keeps DDD boundaries.
    """

    async def list_lead_ids_matching(
        self,
        *,
        tenant_id: UUID,
        predicate: ColumnElement[Boolean],  # opaque SQLA expression from SegmentFilterEvaluator
        limit: int,
        session: AsyncSession,
    ) -> tuple[list[UUID], int]:
        """Returns (lead_ids ordered by id, total_count). Internal pagination
        if total > limit (caller receives capped lead_ids + true total).
        """
        ...

    async def count_leads_matching(
        self,
        *,
        tenant_id: UUID,
        predicate: ColumnElement[Boolean],
        session: AsyncSession,
    ) -> int: ...
```

**Concrete adapter** vive en `shared/links/ports/crm.py` (NEW addition — see §6 cross-module ports).

### 5.5 `CampaignTemplateService` — `application/services/campaign_template_service.py`

```python
class CampaignTemplateService:
    """CRUD globals (cross-tenant read) + tenant-scoped + clone_to_campaign transactional."""

    LIST_CACHE_TTL = 300  # 5min

    async def list_available(
        self, tenant_id: UUID, *, session: AsyncSession,
    ) -> list[CampaignTemplate]:
        """Returns globals UNION tenant-scoped. Cached 5min."""
        cache_key = f"templates:available:{tenant_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        templates = await self._repo.list_for_tenant(tenant_id, session=session)
        await self._cache.set(cache_key, templates, ttl=self.LIST_CACHE_TTL)
        return templates

    async def get(
        self, tenant_id: UUID, template_id: UUID, *, session: AsyncSession,
    ) -> CampaignTemplate:
        """Lookup tenant-scoped first; if NULL, lookup globals."""
        ...

    async def clone_to_campaign(
        self, tenant_id: UUID, template_id: UUID, dto: CampaignCreateFromTemplate,
        *, session: AsyncSession, user_id: UUID | None = None,
    ) -> Campaign:
        """Atomic clone: instantiate Campaign + N CampaignSteps in single TX.

        Body validation:
        - parses template.template_body → CampaignTemplateBody (Pydantic strict)
        - resolves next_step_indexes → next_step_ids: list[UUID]
        - applies dto.config_overrides on top of template body config_defaults

        If dto.scheduled_for provided → calls schedule() inline post-create.
        """
        # 1. Load template
        tpl = await self.get(tenant_id, template_id, session=session)
        body = CampaignTemplateBody.model_validate(tpl.template_body)
        # 2. Build Campaign
        merged_config = {**body.config_defaults, **dto.config_overrides}
        campaign = await self._campaign_service.create(
            tenant_id,
            CampaignCreate(
                name=dto.name,
                description=dto.description,
                campaign_type=tpl.campaign_type,
                segment_id=dto.segment_id,
                channel_priority=body.suggested_channel_priority,
                offer_id=dto.offer_id,
                config=merged_config,
                created_by_source="api",
            ),
            session=session,
            user_id=user_id,
        )
        # 3. Build steps with index→UUID mapping
        index_to_id: dict[int, UUID] = {s.step_index: uuid4() for s in body.steps}
        for step_body in body.steps:
            step_id = index_to_id[step_body.step_index]
            next_ids = [index_to_id[idx] for idx in step_body.next_step_indexes]
            await self._campaign_service.add_step(
                tenant_id, campaign.id,
                CampaignStepCreate(
                    step_type=step_body.step_type,
                    step_index=step_body.step_index,
                    label=step_body.label,
                    next_step_ids=next_ids,
                    step_config=step_body.step_config,
                ),
                session=session,
            )
        # 4. Optional schedule
        if dto.scheduled_for is not None:
            campaign = await self._campaign_service.schedule(
                tenant_id, campaign.id, dto.scheduled_for, session=session,
            )
        return campaign
```

### 5.6 `CacheBackend` — `application/services/cache.py`

```python
from __future__ import annotations
from typing import Any, Protocol


class CacheBackend(Protocol):
    """Abstraction over in-memory TTL + Redis pub/sub invalidation.

    Concrete impl mirrors PlanService.subscribe_cache_invalidations cementado PR-2:
    - cachetools.TTLCache for hot reads
    - Redis pubsub channel "cache_invalidate:campaigns:{tenant_id}" for cross-instance
    """

    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, *, ttl: int) -> None: ...
    async def invalidate(self, key: str) -> None: ...
    async def invalidate_pattern(self, pattern: str) -> None: ...
    async def subscribe_invalidations(self) -> None:
        """Long-running task. Started at app boot via lifespan."""
```

Concrete impl `_TTLCacheWithRedis` reuses the exact pattern in `PlanService` (PR-2 §6 — Redis pub/sub channel `cache_invalidate:*`). Builder MUST grep `PlanService.subscribe_cache_invalidations` to mirror behavior 1:1 (no copy-paste; extract shared `RedisInvalidatedTTLCache` if duplication >2 sites — DRY threshold).

---

## 6. Repository extensions (back-port to PR-3 surface)

PR-4 needs 2 NEW methods on `CampaignRepository` (PR-3 declared minimal API). These are **additive** — no breaking change. Builder adds to `domain/repositories.py` ABC + impl in `infrastructure/repositories/campaign_repository_impl.py`.

```python
# Add to CampaignRepository ABC + impl:

async def count_active(
    self, tenant_id: UUID, *, session: AsyncSession,
) -> int:
    """Count campaigns NOT in (completed, canceled, deleted). Used by plan limit check.

    SQL: SELECT COUNT(*) FROM campaign
         WHERE tenant_id = :t
         AND status IN ('draft','scheduled','running','paused')
         AND deleted_at IS NULL
    """
    ...

async def count_by_tenant(
    self, tenant_id: UUID, *, session: AsyncSession,
    status_filter: Sequence[CampaignStatus] | None = None,
) -> int:
    """COUNT(*) for paginated list endpoint. Tenant-scoped + soft-delete-aware."""
    ...
```

Plus extension on `list_by_tenant`:

```python
# Extend CampaignRepository.list_by_tenant signature (additive kwargs — backwards compat):
async def list_by_tenant(
    self, tenant_id: UUID, *, session: AsyncSession,
    limit: int = 50, offset: int = 0,
    status_filter: Sequence[CampaignStatus] | None = None,
    type_filter: Sequence[CampaignType] | None = None,    # NEW
    sort_by: str = "created_at_desc",                     # NEW
) -> Sequence[Campaign]: ...
```

**Cross-module port `shared/links/ports/crm.py` (NEW file):**

```python
"""Cross-module read port for CRM data. Consumed by campaigns SegmentService.

Module ownership: this file lives in shared/links/ports/ — anyone can read,
crm module implements. NEVER import LeadModel directly from another module.
"""

from __future__ import annotations
from typing import Protocol
from uuid import UUID

from sqlalchemy import ColumnElement, Boolean
from sqlalchemy.ext.asyncio import AsyncSession


class LeadQueryService(Protocol):
    async def list_lead_ids_matching(
        self, *, tenant_id: UUID, predicate: ColumnElement[Boolean],
        limit: int, session: AsyncSession,
    ) -> tuple[list[UUID], int]: ...

    async def count_leads_matching(
        self, *, tenant_id: UUID, predicate: ColumnElement[Boolean],
        session: AsyncSession,
    ) -> int: ...


def get_lead_query_service() -> LeadQueryService:
    """Factory. Returns crm-module impl. Lazy import to avoid circular."""
    from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl
    return LeadQueryServiceImpl()
```

**Cross-module port `shared/links/ports/campaigns.py` (NEW file):**

```python
"""Cross-module read port for campaigns. Consumed by copilot subagent (PI-2)
and CRM Hub (S4). Exposes service factories without leaking internals.
"""

from __future__ import annotations
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class CampaignReadOnlyPort(Protocol):
    async def get_campaign_summary(
        self, *, tenant_id: UUID, campaign_id: UUID, session: AsyncSession,
    ) -> dict | None:
        """Returns dict shape compatible with CampaignResponse fields (read-only).
        Decouples consumers from domain entity churn.
        """


def get_campaign_read_port() -> CampaignReadOnlyPort:
    """Lazy factory. PI-2 commercial_director subagent consumes via this."""
    from src.modules.campaigns.application.services.campaign_read_adapter import (
        CampaignReadAdapter,
    )
    return CampaignReadAdapter()
```

---

## 7. DB schema — Migration 112 (`alembic/versions/112_campaigns_templates_seed.py`)

Idempotente raw SQL `INSERT ... ON CONFLICT DO NOTHING`. `down_revision="111_campaigns_domain"`.

```python
"""campaigns_templates_seed.

PI-1 S1 PR-4 — seed 5 global templates.
Idempotente raw SQL (regla backend-migrations.md).
"""

import json
import uuid as uuid_mod

from alembic import op

revision = "112_campaigns_templates_seed"
down_revision = "111_campaigns_domain"
branch_labels = None
depends_on = None


# Template body schemas — versioned in sync with CampaignTemplateBody Pydantic.
# Slugs use kebab-case; arch test enforces ^[a-z0-9_-]+$.
TEMPLATES = [
    {
        "slug": "welcome",
        "name": "Bienvenida (3 pasos)",
        "description": (
            "Recibe a un lead nuevo con un mensaje de bienvenida + un seguimiento "
            "24h después invitando a la primera acción."
        ),
        "campaign_type": "agent_conversation",
        "tags": ["onboarding", "lead-nurture"],
        "recommended_segment_slugs": ["new-leads-7d"],
        "body": {
            "description_internal": "Welcome flow 3 steps for new leads.",
            "suggested_channel_priority": ["telegram", "whatsapp", "email"],
            "config_defaults": {
                "agent_instructions": "Sé cálido y breve. Pregunta por su objetivo principal.",
            },
            "steps": [
                {
                    "step_type": "send_message", "step_index": 0,
                    "label": "Mensaje de bienvenida",
                    "next_step_indexes": [1],
                    "step_config": {"template_slug": "welcome-1", "agent_instructions": None},
                },
                {
                    "step_type": "wait_delay", "step_index": 1,
                    "label": "Esperar 24h",
                    "next_step_indexes": [2],
                    "step_config": {"delay_seconds": 86400},
                },
                {
                    "step_type": "send_message", "step_index": 2,
                    "label": "Seguimiento día 2",
                    "next_step_indexes": [],
                    "step_config": {"template_slug": "welcome-2", "agent_instructions": None},
                },
            ],
        },
    },
    {
        "slug": "launch-4day",
        "name": "Lanzamiento 4 días",
        "description": (
            "Secuencia de 4 días para anunciar un lanzamiento. Día 1 anuncio, día 2 prueba "
            "social, día 3 objeciones, día 4 cierre con escasez."
        ),
        "campaign_type": "agent_conversation",
        "tags": ["launch", "high-intent"],
        "recommended_segment_slugs": ["warm-mqls", "engaged-30d"],
        "body": {
            "description_internal": "4-day launch sequence with daily messages.",
            "suggested_channel_priority": ["whatsapp", "telegram", "email"],
            "config_defaults": {
                "agent_instructions": "Adapta el mensaje al fit/intent del lead. Cierra fuerte el día 4.",
            },
            "steps": [
                {"step_type": "send_message", "step_index": 0, "label": "Día 1 anuncio",
                 "next_step_indexes": [1], "step_config": {"template_slug": "launch-d1"}},
                {"step_type": "wait_delay", "step_index": 1, "label": "Esperar 24h",
                 "next_step_indexes": [2], "step_config": {"delay_seconds": 86400}},
                {"step_type": "send_message", "step_index": 2, "label": "Día 2 prueba social",
                 "next_step_indexes": [3], "step_config": {"template_slug": "launch-d2"}},
                {"step_type": "wait_delay", "step_index": 3, "label": "Esperar 24h",
                 "next_step_indexes": [4], "step_config": {"delay_seconds": 86400}},
                {"step_type": "send_message", "step_index": 4, "label": "Día 3 objeciones",
                 "next_step_indexes": [5], "step_config": {"template_slug": "launch-d3"}},
                {"step_type": "wait_delay", "step_index": 5, "label": "Esperar 24h",
                 "next_step_indexes": [6], "step_config": {"delay_seconds": 86400}},
                {"step_type": "send_message", "step_index": 6, "label": "Día 4 cierre",
                 "next_step_indexes": [], "step_config": {"template_slug": "launch-d4"}},
            ],
        },
    },
    {
        "slug": "webinar",
        "name": "Webinar (pre + post)",
        "description": (
            "Acompaña al asistente de un webinar antes y después: confirmación previa "
            "+ seguimiento post-evento con la grabación + CTA."
        ),
        "campaign_type": "event_trigger",
        "tags": ["webinar", "event"],
        "recommended_segment_slugs": ["webinar-registrants"],
        "body": {
            "description_internal": "Pre + post webinar sequence anchored to event date.",
            "suggested_channel_priority": ["email", "whatsapp", "telegram"],
            "config_defaults": {
                "anchor_event_date": None,  # tenant fills via clone dto.config_overrides
                "timezone": "America/Lima",
            },
            "steps": [
                {"step_type": "send_message", "step_index": 0, "label": "Confirmación pre-webinar",
                 "next_step_indexes": [1], "step_config": {"template_slug": "webinar-pre"}},
                {"step_type": "wait_delay", "step_index": 1,
                 "label": "Esperar hasta evento (TBD vía config.anchor_event_date)",
                 "next_step_indexes": [2],
                 "step_config": {"delay_seconds": 0, "wait_until_anchor": True}},
                {"step_type": "send_message", "step_index": 2, "label": "Post-webinar grabación + CTA",
                 "next_step_indexes": [], "step_config": {"template_slug": "webinar-post"}},
            ],
        },
    },
    {
        "slug": "cold-reactivation",
        "name": "Reactivación de leads fríos",
        "description": (
            "Reengancha a leads sin interacción por 60+ días. Si responden, marca como warm. "
            "Si no responden en 3 días, marca como archive."
        ),
        "campaign_type": "agent_conversation",
        "tags": ["reactivation", "cold"],
        "recommended_segment_slugs": ["cold-90d"],
        "body": {
            "description_internal": "Cold lead reactivation 2-step.",
            "suggested_channel_priority": ["whatsapp", "telegram", "email"],
            "config_defaults": {
                "agent_instructions": "Sé breve, sin presión. Pregunta si su contexto cambió.",
            },
            "steps": [
                {"step_type": "send_message", "step_index": 0, "label": "Reengancho",
                 "next_step_indexes": [1], "step_config": {"template_slug": "reactivation-1"}},
                {"step_type": "wait_delay", "step_index": 1, "label": "Esperar 3 días",
                 "next_step_indexes": [2], "step_config": {"delay_seconds": 259200}},
                {"step_type": "branch_on_condition", "step_index": 2, "label": "¿Respondió?",
                 "next_step_indexes": [],  # branches resuelven en runtime via condition + step_config
                 "step_config": {"condition": "lead.last_inbound_at >= campaign.launched_at"}},
            ],
        },
    },
    {
        "slug": "post-purchase",
        "name": "Post-compra (3 pasos)",
        "description": (
            "Acompaña al cliente post-compra: gracias inmediato, follow-up de uso 7 días "
            "después, y oferta upsell día 14."
        ),
        "campaign_type": "agent_conversation",
        "tags": ["customer-journey", "upsell"],
        "recommended_segment_slugs": ["customers-7d"],
        "body": {
            "description_internal": "Post-purchase 3-step sequence.",
            "suggested_channel_priority": ["whatsapp", "telegram", "email"],
            "config_defaults": {
                "agent_instructions": "Sé caluroso. Refuerza la decisión. El upsell es secundario.",
            },
            "steps": [
                {"step_type": "send_message", "step_index": 0, "label": "Agradecimiento",
                 "next_step_indexes": [1], "step_config": {"template_slug": "post-purchase-thanks"}},
                {"step_type": "wait_delay", "step_index": 1, "label": "Esperar 7 días",
                 "next_step_indexes": [2], "step_config": {"delay_seconds": 604800}},
                {"step_type": "send_message", "step_index": 2, "label": "Follow-up de uso",
                 "next_step_indexes": [3], "step_config": {"template_slug": "post-purchase-followup"}},
                {"step_type": "wait_delay", "step_index": 3, "label": "Esperar 7 días",
                 "next_step_indexes": [4], "step_config": {"delay_seconds": 604800}},
                {"step_type": "send_message", "step_index": 4, "label": "Upsell suave",
                 "next_step_indexes": [], "step_config": {"template_slug": "post-purchase-upsell"}},
            ],
        },
    },
]


def upgrade() -> None:
    # Idempotent INSERT — partial unique idx (slug WHERE tenant_id IS NULL) ya creado en migration 111.
    # Fixed UUIDs derivados de uuid5(NAMESPACE_DNS, "nicolify.template:" + slug) — reproducibles cross-env.
    NS = uuid_mod.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # NAMESPACE_DNS
    for tpl in TEMPLATES:
        tpl_id = str(uuid_mod.uuid5(NS, f"nicolify.template:{tpl['slug']}"))
        body_json = json.dumps(tpl["body"]).replace("'", "''")
        tags_json = json.dumps(tpl["tags"]).replace("'", "''")
        segs_json = json.dumps(tpl["recommended_segment_slugs"]).replace("'", "''")
        op.execute(f"""
            INSERT INTO campaign_template (
                id, tenant_id, slug, name, description, campaign_type,
                template_body, recommended_segment_slugs, tags, version,
                created_at, updated_at
            ) VALUES (
                '{tpl_id}'::uuid,
                NULL,
                '{tpl["slug"]}',
                '{tpl["name"].replace("'", "''")}',
                '{tpl["description"].replace("'", "''")}',
                '{tpl["campaign_type"]}',
                '{body_json}'::jsonb,
                '{segs_json}'::jsonb,
                '{tags_json}'::jsonb,
                1,
                NOW(),
                NOW()
            )
            ON CONFLICT DO NOTHING;
        """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM campaign_template WHERE tenant_id IS NULL AND slug IN (
            'welcome', 'launch-4day', 'webinar', 'cold-reactivation', 'post-purchase'
        );
    """)
```

**Test idempotency clone DB (regla `backend-migrations.md`):**

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 111_campaigns_domain && POSTGRES_DB=migration_test alembic upgrade head'
# Re-run a second time to verify idempotency (ON CONFLICT DO NOTHING).
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -d migration_test -c \
  "SELECT COUNT(*) FROM campaign_template WHERE tenant_id IS NULL;" # = 5
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

---

## 8. Eventos / outbox (PR-4 wires emission)

PR-3 declared 14 events. PR-4 wires emission via `OutboxService.enqueue_async_from_sync_caller(event, session=...)`:

| Event name | Producer (PR-4) | Trigger |
|---|---|---|
| `campaigns.campaign.created` | `CampaignService.create` | POST `/campaigns/` |
| `campaigns.campaign.scheduled` | `CampaignService.schedule` | POST `/campaigns/{id}/schedule` |
| `campaigns.campaign.launched` | `CampaignService.launch` + `resume` | POST `/campaigns/{id}/launch` o `/resume` |
| `campaigns.campaign.paused` | `CampaignService.pause` | POST `/campaigns/{id}/pause` |
| `campaigns.campaign.completed` | `CampaignService.complete` | POST `/campaigns/{id}/complete` |
| `campaigns.campaign.canceled` | `CampaignService.cancel` + `delete` (implícito) | POST `/campaigns/{id}/cancel` o DELETE |
| `campaigns.step.added` | `CampaignService.add_step` | POST `/campaigns/{id}/steps/` |
| `campaigns.step.updated` | `CampaignService.update_step` | PATCH `/campaigns/{id}/steps/{step_id}` |
| `campaigns.task.queued` | NOT emitted PR-4 (no task creation) | S2 |
| `campaigns.task.dispatched` | S2 |
| `campaigns.task.sent` | S2 |
| `campaigns.task.failed` | S2 |
| `campaigns.segment.created` | `SegmentService.create` | POST `/segments/` |
| `campaigns.segment.snapshotted` | `SegmentService.snapshot` | POST `/segments/{id}/snapshot` |

**Default flag `USE_OUTBOX_PATTERN_CAMPAIGNS=false`** — PR-4 emite via `OutboxService` API; cuando flag OFF, in-memory subscriber path (legacy) ejecuta. Cuando ON (PR pendiente), outbox dispatcher lo procesa async. PR-4 NO toca el flag default (S2 lo activa cuando hay subscribers reales).

---

## 9. Retry / idempotency policy

### Idempotency-Key (HTTP header)

`POST /campaigns/`, `POST /templates/{id}/clone` aceptan header `Idempotency-Key: <uuid>` opt-in. Decorator `@idempotent(key_fn=lambda req: f"campaigns:create:{tenant_id}:{req.headers['Idempotency-Key']}", ttl_seconds=86400)` usa `shared/idempotency/` (PR-1 cementado). Sin header → POST normal.

### Natural-key idempotency

- `POST /segments/` — UNIQUE `(tenant_id, name)` partial idx en DB. Service catchea IntegrityError → re-raise `SegmentDuplicateNameError` → 409.
- `POST /campaigns/{id}/{transition}` — domain FSM idempotency (re-pause de paused = no-op silent return current).
- `POST /campaigns/{id}/launch` — re-launch de RUNNING = no-op silent (ver `CampaignService.launch`).

### Retry policy

PR-4 NO implementa retry workers. `CampaignTask.attempt_count` + `last_error` son schema (PR-3) para S2.

---

## 10. Tenant isolation

- `tenant_id` MANDATORY en cada operación service + cada call repo (heredado PR-3).
- API layer: `Depends(get_tenant_context)` extrae `X-Tenant-ID` header → setea contextvar + valida user pertenece a tenant. Service receives `tenant_id: UUID` explícito (no contextvar implícito — testabilidad).
- `CampaignTemplateRepository.list_globals()` → UNICA cross-tenant lookup intencional. Documentado en PR-3 §10 + arch test allowlist `CROSS_TENANT_ALLOWED_METHODS`.
- Cross-module reads (CRM leads para resolve segment, offers para validar offer_id) via `shared/links/ports/{crm,offer}.py` solo. Cero JOIN cross-module. Cero import directo de modelos otros modules.
- Arch test PR-3 `test_campaigns_tenant_isolation.py` ya enforce — no se relaja.

---

## 11. Observability

- structlog en cada service method. Campos clave: `tenant_id`, `entity_type`, `entity_id`, `operation`, `status_transition` (si aplica), `cache_hit` (cuando relevante).

```python
logger.info(
    "campaign_service_create",
    tenant_id=str(tenant_id), campaign_id=str(campaign.id),
    campaign_type=campaign.campaign_type.value, source=dto.created_by_source,
)
logger.info(
    "campaign_service_transition",
    tenant_id=str(tenant_id), campaign_id=str(c.id),
    from_status=c.status.value, to_status=updated.status.value,
    event_emitted="campaigns.campaign.scheduled",
)
logger.info(
    "segment_service_resolve",
    tenant_id=str(tenant_id), segment_id=str(segment_id),
    lead_count=total, truncated=truncated, duration_ms=elapsed_ms,
)
```

- **Trace events / LLM cost recording** — diferido S2 (cuando worker invoca LLM via specialist agent).
- **PII** — `last_error` raw 2000-char cap (DDL); service NO almacena en logs structlog (regla `pii-sanitisation.md`). Si llega a `CampaignTask` (vía S2), sanitize via `sanitize_payload(...)` antes de persist.

### Anchor budget gating (`copilot-expert` + `sales-agent-expert` confirmación)

PR-4 NO wirea `BudgetGuard.check` en launch path. Confirmaciones:
- `copilot-expert` skill: PR-4 NO consume `BudgetGuard.check(agent_kind="campaign")` — wire vive en `CampaignExecutionWorker` (S2) cuando worker invoca LLM via specialist agent. Bucket "Others" pool reservado + invariante 50% SA preservado.
- `sales-agent-expert` skill: PR-4 NO toca §3 protected surfaces (Closer Studio, BufferService, OutputManager). `OutboundOrchestrator` paralelo (S3) wirea outbound rate limit + budget gate antes del entry point send.

`PlanService.get_effective` SÍ se consume en `CampaignService.create` para enforcer `max_campaigns_active` cap pre-create (no es budget LLM — es plan limit estructural).

---

## 12. Cross-cutting concerns

- **Tenant isolation** — §10. Cada query, sin excepciones (excepto allowlist heredada PR-3).
- **Currency** — N/A en PR-4. Sin monetary fields en DTOs. (cost LLM lives en `campaign_llm_call` PR-1 + worker S2.) `test_currency_consistency.py` arch test pasa por ausencia.
- **Master data** — `DateTime(timezone=True)` heredado PR-3. Service usa `utc_now()` siempre (`shared/domain/master_data.py`). FE post PI-1 consume con `useTenantLocale()`. `CampaignTemplateBody.config_defaults.timezone` (string IANA, e.g. `"America/Lima"`) es hint para `EVENT_TRIGGER` anchor — service NO interpreta, lo pasa al worker S2.
- **Spanish neutro LATAM** — DTO descriptions, template `name` y `description`, error messages user-facing en español sin voseo. Docstrings + class names en inglés (convención código). Validar via `.claude/rules/spanish-text.md` checklist.
- **PII** — `response_model=` mandatory en TODA ruta (regla `pii-sanitisation.md`):
  - `CampaignResponse`: `created_by_user_id` UUID OK (no PII), config dict podría carry email/phone — service layer **MUST** sanitize antes de persist via `sanitize_payload` cuando origen sea webhook/copilot. Builder agrega test `test_campaign_config_no_pii_leak`.
  - `SegmentResolveResponse.lead_ids`: solo UUIDs, no PII.
  - `last_error` en `CampaignTaskModel`: cap 2000 chars + sanitization S2.
- **Native-first dev** — lint/tests/type-check `cd backend && .venv/bin/{ruff,pytest,mypy}`. Migration test via `docker exec ... alembic upgrade` only.

---

## 13. Architecture fitness impact

### Tests existentes que deben seguir verde (sin cambio en allowlist):

- `test_ddd_boundaries.py` — PR-4 NO importa otros modules directamente (solo via `shared/links/ports/`).
- `test_outbox_invariants.py` — PR-4 wirea emission via `OutboxService` API (sin tocar internals).
- `test_no_new_copilot_module_imports.py` (ratchet 22 frozen, sin cambio).
- `test_sales_agent_tenant_isolation.py` (sin cambio).
- `test_folder_naming.py` — `campaigns/{application,api}/` válido.
- `test_api_contracts.py` — `response_model=` + `redirect_slashes=False` enforced (ya cementado main.py).
- `test_master_data_compliance.py` — DTO datetime fields heredados PR-3 (DateTime timezone-aware via SQLA).
- `test_currency_consistency.py` — N/A.
- `test_domain_purity.py` — `application/services/` puede importar SQLA (sí). `domain/` NO (ya cementado PR-3).

### Tests PR-3 que deben seguir verde:

- `test_campaigns_tenant_isolation.py` — PR-4 add path `application/services/campaign_service.py` al scan; `count_active`, `count_by_tenant` reciben `tenant_id` (assert).
- `test_campaign_fsm_invariants.py` — sin cambio.
- `test_segment_filter_pydantic_validated.py` — sin cambio.
- `test_campaign_task_idx_workers.py` — sin cambio.

### Tests nuevos (allowlist shrink-only):

#### `test_campaigns_api_response_model.py`

```python
"""Toda ruta /api/v1/{campaigns,segments,templates}/* declara response_model=.

Regla pii-sanitisation.md: response_model actúa como allowlist de fields.
Sin response_model = PII leak garantizado en algún momento.
"""

import importlib
import inspect
from fastapi.routing import APIRoute

KNOWN_NO_RESPONSE_MODEL: frozenset[str] = frozenset()  # SHRINK ONLY

def test_all_campaigns_api_routes_declare_response_model():
    for module_name in ("campaigns", "segments", "templates"):
        mod = importlib.import_module(f"src.modules.campaigns.api.{module_name}")
        router = mod.router
        for route in router.routes:
            if not isinstance(route, APIRoute):
                continue
            # 204 No Content endpoints exempt (DELETE)
            if 204 in route.responses or route.status_code == 204:
                continue
            assert route.response_model is not None, (
                f"{route.path} ({route.methods}) sin response_model — viola pii-sanitisation"
            )
```

#### `test_campaigns_pagination_default.py`

```python
"""list endpoints requieren limit query param con le=100 constraint.

Production-grade 1000 clientes: list sin pagination colapsa.
"""

import inspect
from fastapi import APIRouter
import src.modules.campaigns.api.campaigns as campaigns_api
import src.modules.campaigns.api.segments as segments_api

LIST_ROUTE_PATTERNS = ["GET /api/v1/campaigns/", "GET /api/v1/segments/"]

def test_list_endpoints_enforce_limit():
    for module in (campaigns_api, segments_api):
        for route in module.router.routes:
            if "GET" in route.methods and route.path in ("/", ""):
                # Verify limit Query param exists with le=100
                sig = inspect.signature(route.endpoint)
                limit_param = sig.parameters.get("limit")
                assert limit_param is not None, f"{route.path} list sin parámetro limit"
                # Inspect Query metadata for le=100 (simplified — actual via Field metadata)
                # ...
```

#### `test_campaigns_fsm_service_layer.py`

```python
"""CampaignService NO duplica FSM lógica (delegate Campaign.transition_allowed).

AST scan: si encuentra dict literal con keys que matchean CampaignStatus values
fuera de Campaign._FSM_TRANSITIONS → fail.
"""

import ast
from pathlib import Path

CAMPAIGN_STATUS_VALUES = {"draft","scheduled","running","paused","completed","canceled"}

def test_service_layer_no_fsm_dict_duplication():
    service_path = Path("src/modules/campaigns/application/services/campaign_service.py")
    tree = ast.parse(service_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys_str = []
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys_str.append(k.value)
                elif isinstance(k, ast.Attribute):
                    keys_str.append(k.attr.lower())
            keys_set = set(keys_str)
            # If dict literal contains 3+ FSM status values → looks like duplicated matrix
            if len(keys_set & CAMPAIGN_STATUS_VALUES) >= 3:
                raise AssertionError(
                    f"campaign_service.py contiene dict que parece duplicar FSM matrix "
                    f"(keys: {sorted(keys_set & CAMPAIGN_STATUS_VALUES)}). "
                    f"Delegar a Campaign.transition_allowed() (PR-3 SSoT).",
                )
```

#### `test_segment_resolve_sql_filtering.py`

```python
"""SegmentService.resolve() usa SQL WHERE, no Python loop sobre leads.

AST scan: en resolve() function body NO debe aparecer `for X in leads:`
ni similares iter sobre lead collection (escalabilidad 1000 clientes × 10K leads).
"""

import ast
from pathlib import Path

def test_resolve_no_python_iter_over_leads():
    path = Path("src/modules/campaigns/application/services/segment_service.py")
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "resolve":
            for inner in ast.walk(node):
                if isinstance(inner, ast.For) and isinstance(inner.iter, ast.Name):
                    iter_name = inner.iter.id
                    if "lead" in iter_name.lower():
                        raise AssertionError(
                            f"SegmentService.resolve() contiene `for X in {iter_name}:` "
                            f"— leads se filtran SQL-side, no Python.",
                        )
```

### Allowlists ratchet:

- 4 nuevos arch tests SIN allowlist inicial. Shrink only — toda violación nueva = build fail.

---

## 14. pm-nico/current-state updates required

Post-merge, builder/PM update `docs/pm-nico/current-state/campaigns.md`:

1. **Sección "Domain layer shipped (PR-3 — 2026-04-29)"** — agregar fila:
   ```markdown
   | Application services + REST API + 5 templates seed | TBD-COMMIT | ✅ SHIPPED (PR-4 S1) |
   ```

2. **Sección "Capacidades actuales (post PR-1 S0)"** — renombrar a "Capacidades actuales (post PR-4 S1)" + agregar filas:
   ```markdown
   | Application services campaigns | ✅ shipped (PR-4 S1) | CampaignService (CRUD + FSM) + SegmentService (resolve + estimate + snapshot) + CampaignTemplateService (clone) en `modules/campaigns/application/`. Cache TTL 30s + Redis pub/sub invalidation cross-instance (mirror PlanService). |
   | API REST campaigns + segments + templates | ✅ shipped (PR-4 S1) | 23 endpoints `/api/v1/{campaigns,segments,templates}/*` con response_model mandatory, paginación enforced (limit≤100), Idempotency-Key opt-in. Bearer + X-Tenant-ID required. Sin FE todavía (post PI-1). |
   | 5 templates globales seed | ✅ shipped (PR-4 S1) | `welcome`, `launch-4day`, `webinar`, `cold-reactivation`, `post-purchase`. Disponibles via `GET /api/v1/templates/` + `POST /api/v1/templates/{id}/clone`. Editable en runtime (rows DB). |
   | `launch()` STUB | ⚠️ partial (PR-4) | Marca `launched_at` + emite `campaigns.campaign.launched` outbox event. Ejecución real (resolve segment + insert tasks + ChannelRouter send) la implementa S2 (`CampaignExecutionWorker` + `ChannelRouter Telegram v1`). |
   ```

3. **Sección "Decisiones producto vinculadas"** — agregar:
   - D6 (PR-4): FSM SSoT vive en domain (`Campaign.transition_allowed`); service delega — cero duplicación.
   - D7 (PR-4): `launch()` stub en S1; real orchestration en S2 (clean cut, scope-respecting).
   - D8 (PR-4): `SegmentService.resolve()` SQL-side (no Python loop) — production-grade 1000 clientes.
   - D9 (PR-4): Cache strategy in-memory TTLCache + Redis pub/sub invalidation (mirror PlanService PR-2).
   - D10 (PR-4): Templates seed via migration idempotente con UUIDs reproducibles (uuid5 NAMESPACE_DNS).
   - D11 (PR-4): CampaignStep CRUD nested under `/campaigns/{id}/steps/` (recurso jerarquizado).
   - D12 (PR-4): Snapshot creation user-explicit (PR-4); auto-snapshot al transition running con segment_type=STATIC = S2.
   - D13 (PR-4): Idempotency-Key opt-in en POST writes; natural-key dedup en segments.
   - D14 (PR-4): `BudgetGuard.check` en launch path = scope-cut explícito S2 (worker es quien invoca LLM).

---

## 15. Test surfaces (TDD-mandatory por capa, RED first)

### Layer A — Application services (pure Python + AsyncSession + mocks)

1. `test_campaign_service.py` — CRUD happy path + plan limit (`max_campaigns_active`) + duplicate name 409 + soft delete con event implícito.
2. `test_campaign_service_fsm.py` — todas las transitions válidas + reject inválidas (canceled→running, etc.) + idempotencia (re-pause/resume/launch silent) + 409 transitions inválidas. Property-based con Hypothesis sobre matrix.
3. `test_segment_service.py` — CRUD + resolve(at_time) cap + estimate_size cache miss/hit + snapshot con event.
4. `test_segment_filter_evaluator.py` — `to_sql_predicate(filter_dsl)` produce SQLA expression válida para cada combinator (ALL/ANY) + cada field (10 fields v1) + edge cases (empty filter → false). Inspect resulting expression via `compile(dialect=postgresql.dialect())`.
5. `test_campaign_template_service.py` — list_available globals + tenant + cache + clone_to_campaign transactional (rollback si step fail).
6. `test_cache.py` — TTLCache hit/miss + Redis pub/sub invalidation cross-instance (mock Redis pubsub via fakeredis).
7. `test_pagination.py` — `limit ≤ MAX` + offset + `total_count` + `has_more`.

### Layer B — API endpoints (httpx AsyncClient + pytest-asyncio)

8. `test_campaigns_api.py` — happy path (POST/GET/PATCH/DELETE) + 401 (sin Bearer) + 401 (sin X-Tenant-ID) + 404 (id ajeno) + 409 (status mismatch) + 402 (plan limit) + Idempotency-Key (replay = same response).
9. `test_segments_api.py` — happy path + resolve + snapshot + 409 dup name.
10. `test_templates_api.py` — list globals + clone happy path + 404 + atomicity (clone falla → rollback).
11. `test_api_response_model_coverage.py` — escanea router → toda ruta declara `response_model=` (excepto 204).

### Layer C — Architecture (introspection + AST scan)

12. `test_campaigns_api_response_model.py` — gate (descrito §13).
13. `test_campaigns_pagination_default.py` — gate.
14. `test_campaigns_fsm_service_layer.py` — gate.
15. `test_segment_resolve_sql_filtering.py` — gate.

### Migration

16. Idempotency clone-DB test + verify count `campaign_template WHERE tenant_id IS NULL` = 5 + slugs match.

### Integration (E2E lite, sin worker S2)

17. `test_campaigns_e2e_launch_stub.py` — POST campaign → POST steps × 3 → POST schedule → POST launch → SELECT desde `domain_event_outbox` verifica 4 eventos (`created`, `scheduled`, `launched`, 3× `step.added`) + Campaign.status=RUNNING + launched_at NOT NULL.

---

## 16. Research notes

No novel patterns introduced — PR-4 reusa arquitectura cementada:

- **DDD inside-out**: domain → infrastructure → application → api. Heredado Nicolify codebase (ref `backend-expert` skill `references/architecture-rules.md`). PR-3 cementó domain + infra; PR-4 monta application + api.
- **Pydantic v2 strict + `response_model`**: cementado Nicolify (`brand/api/`, `offer/api/`, `crm/api/leads.py`). Regla `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` enforce.
- **OutboxService event emission**: cementado PR-1 (`shared/domain_events/outbox/application/outbox_service.py` — `enqueue_async_from_sync_caller`).
- **Cache TTL + Redis pub/sub invalidation cross-instance**: cementado PR-2 (`PlanService.subscribe_cache_invalidations` + Redis channel `cache_invalidate:*`). PR-4 reusa el mismo patrón (DRY threshold = 2 consumers — PR-4 builder evalúa extracción a `shared/cache/redis_invalidated_ttl_cache.py` si duplicación clara).
- **`@idempotent` decorator**: cementado PR-1 (`shared/idempotency/application/decorator.py`). Opt-in via header `Idempotency-Key`.
- **`PlanService.get_effective` plan limit checks**: cementado PR-2.
- **`get_tenant_context` + `get_current_user` deps**: cementado `iam/api/dependencies.py` + `core/database.py`.
- **AsyncSession + SQLAlchemy 2.0 select(...)**: cementado en repos PR-3 + `shared/billing/infrastructure/`.
- **uuid5 deterministic seed UUIDs**: estándar Python stdlib; usado en migration 112 para reproducibilidad cross-env.

Production-grade decisions for 1000+ tenants validated against:
- SQL-side filtering vs Python loops (cementado patrón en `analytics/stage_services/` y `crm/`).
- Pagination obligatoria + `total_count` (estándar OpenAPI; ref `metrics-expert` skill — progressive loading).
- Cache TTL en list endpoints + invalidación cross-instance (mirror PlanService 1:1).

---

## 17. Open questions for PM

**ZERO open questions.**

Decisiones tomadas con framing Chris "1000 clientes, cero deuda técnica":

- **D6** — FSM SSoT vive en domain; service delega via `Campaign.transition_allowed()` (PR-3 SSoT). Arch test `test_campaigns_fsm_service_layer.py` enforce.
- **D7** — `launch()` STUB en PR-4 (marca `launched_at` + emite event); real orchestration S2.
- **D8** — `SegmentService.resolve()` SQL-side filtering via `SegmentFilterEvaluator.to_sql_predicate()`; arch test `test_segment_resolve_sql_filtering.py` enforce no-Python-loop.
- **D9** — Cache in-memory TTLCache + Redis pub/sub cross-instance (mirror `PlanService` PR-2).
- **D10** — Templates seed via migration idempotente con UUIDs reproducibles `uuid5(NAMESPACE_DNS, "nicolify.template:" + slug)`.
- **D11** — CampaignStep CRUD nested under `/campaigns/{id}/steps/` (resource hierarchy).
- **D12** — Snapshot creation user-explicit en PR-4; auto-snapshot S2.
- **D13** — Idempotency-Key opt-in (POST `/campaigns/`, POST `/templates/{id}/clone`); natural-key dedup en segments (UNIQUE name).
- **D14** — `BudgetGuard.check` en launch path = S2 (worker invoca LLM, no PR-4 launch stub).

Diferimientos explícitos (no son open questions, son scope-cuts deliberadas):

- Real orchestrator + workers + ChannelRouter → S2.
- sales_agent OutboundOrchestrator → S3.
- Marketing campaign subagent copilot tools → PI-2.
- FE UI → post PI-1.
- ExpressiveSegmentFilter (full DSL) + group nesting → post PI-1 (PR-3 abstract base extensible-ready).
- Endpoint `GET /campaigns/{id}/stats` → S3 (requiere CampaignTask data real).
- Bulk operations → post PI-1.

**Deuda detectada en codebase (NO bloqueante PR-4, anota en PI-1 `decisions.md`):**
- `crm/api/leads.py` usa sync `Session` (legacy) — PR-4 introduce `LeadQueryServiceImpl` async sin migrar legacy. Migración full sync → async crm = post PI-1.
- `LeadModel.country` agregado por PR-2; verificar que SQLA 2.0 mapping fue agregado al modelo (no solo migration ALTER) antes de PR-4 builder corra. Si no, primer commit PR-4 = `LeadModel.country: Mapped[str | None]` mapping (deuda PR-2 cierre).

---

<!-- @pm: PR-4 PR.md + CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-4 architect done". -->
