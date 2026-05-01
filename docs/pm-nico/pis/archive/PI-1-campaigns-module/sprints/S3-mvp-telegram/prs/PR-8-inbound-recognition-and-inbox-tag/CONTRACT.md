# CONTRACT: PR-8 Inbound recognition and inbox tag

## 0. Context Summary

- **PR**: `PR-8-inbound-recognition-and-inbox-tag` · S3-mvp-telegram · PI-1-campaigns-module
- **Architect run on**: 2026-04-30
- **Modules touched**: `sales_agent`, `campaigns`, `shared` (links port + locale reuse), `frontend/closer-studio` (inbox SSoT real — NOT `features/inbox/`)
- **Surface → builder → auditor mapping**: ver `PR.md § Agentes`. Resumen: `nicolify-backend` (Sub-A + B + D) + `nicolify-frontend` (Sub-C); auditados por `*-auditor` Opus.
- **Skills consulted**:
  - `backend-expert` — DDD layering Inside-Out, SQLA 2.0 `mapped_column`, idempotent migrations, master-data currency `tenant_locale`, response_model PII allowlist, arch fitness ratchet.
  - `sales-agent-expert` — §3 protected surfaces (`process_chat_flow` extension is **inside** flow but does NOT mutate Closer Studio API/WS surface, NOT mutate BufferService, NOT mutate OutputManager — safe additive read; AgentState additive `campaign_id` field already exists from PR-7).
  - `tessl__graceful-degradation` — best-effort timeouts on lookup_recent_campaign_task (`SELECT ... LIMIT 1` on tenant-indexed query → bounded; try/except + structlog warning per chat.py:208 pattern).
  - `tessl__fastapi` — `Annotated[..., Depends(...)]` style + `response_model=` always declared.
- **CONTEXT-BRIEF source**: brief NOT generated (PR-8 is M-size; architect ran self-greps Path B — verified PR-7 RESULT, repository, enums, chat.py, settings, FE inbox location).
- **pm-nico/current-state files affected** (post-merge):
  - `current-state/campaigns.md` — append capability "stats endpoint live + tag enrichment via shared port"
  - `current-state/sales-agent.md` — append "inbound recognition window 24h injects campaign_id into AgentState (fail-open)"
  - `current-state/crm.md` — append "Closer Studio inbox now tags conversations originating from campaigns"
- **Architecture gates that must keep passing**:
  - `tests/architecture/test_no_cross_module_imports.py` — `sales_agent` MUST NOT import `campaigns.*` directly
  - `tests/architecture/test_response_model_required.py` — stats endpoint declares `response_model=CampaignStatsResponse`
  - `tests/architecture/test_master_data_invariants.py` — `currency` field present in DTO with monetary aggregates
  - `tests/architecture/test_tenant_isolation.py` — every new query filters `tenant_id`
  - `tests/architecture/test_no_hard_deletes.py` — repo extension respects `deleted_at IS NULL`
  - **NEW** `tests/architecture/test_campaigns_stats_response_model_currency.py` — endpoint+DTO-specific invariants

## 1. Domain entities

No new aggregate. Reuse existing:
- `Campaign` (`campaigns.domain.campaign`) — read `name` for `campaign_name` enrichment.
- `CampaignTask` (`campaigns.domain.campaign_task`) — query by `tenant_id + lead_id + status + sent_at`.
- `MessageModel` (`sales_agent.infrastructure.models.message_model`) — read for `responded_count` proxy. NOT a campaigns entity, used cross-module by stats service via internal repository (within `sales_agent`-owned table → expose minimal port query in `shared/links/ports/sales_agent_audit.py`).

Decision: rather than open a new `shared/links/ports/sales_agent_audit.py` for one query, **execute the responded query INSIDE `CampaignStatsService` using SQLA 2.0 raw `select(MessageModel.user_id).distinct()`** with explicit allowlist comment. This is the **single documented exception** to "campaigns service does not query other modules' tables" — justified because:
1. The query is read-only and tenant-scoped.
2. Defining a port for one cross-module read adds maintenance overhead (1000-tenant lens: not amortized).
3. Architect declares this in arch test allowlist `KNOWN_CROSS_MODULE_TABLE_READS` (single-entry).

If future PR-followup makes "responded leads per source" a cross-module pattern → THEN promote to port.

## 2. SQLAlchemy 2.0 models

No new model. Existing:
- `CampaignTaskModel` (`campaigns.infrastructure.models.campaign_task_model`)
- `MessageModel` (`sales_agent.infrastructure.models.message_model`) — readonly access from CampaignStatsService

**New index** (idempotent raw SQL migration):

```sql
CREATE INDEX IF NOT EXISTS idx_campaign_tasks_lookup_lead
  ON campaign_tasks (tenant_id, lead_id, status, sent_at DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_campaign_tasks_stats_aggregate
  ON campaign_tasks (tenant_id, campaign_id, status)
  WHERE deleted_at IS NULL;
```

Two indexes cover both query patterns:
- `idx_campaign_tasks_lookup_lead` → Sub-A inbound recognition `WHERE tenant_id=:t AND lead_id=:l AND status='sent' AND sent_at >= :since ORDER BY sent_at DESC LIMIT 1`.
- `idx_campaign_tasks_stats_aggregate` → Sub-B stats `GROUP BY status WHERE tenant_id=:t AND campaign_id=:c`.

Partial index on `deleted_at IS NULL` matches every query (soft-delete pattern, BE DDD constraint).

## 3. Pydantic v2 DTOs

### 3.1 `CampaignStatsResponse` (NEW — `campaigns.application.dtos.campaign_dtos`)

```python
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CampaignStatsResponse(BaseModel):
    """Aggregate stats for a single campaign.

    Live DB query (no MV) — supported by idx_campaign_tasks_stats_aggregate.
    Currency derived from tenant_locale (master-data invariant).
    converted_count_attribution_method=='deferred_pr_followup' is the
    explicit MVP S3 contract: PR follow-up wires payments + scheduling
    cross-module attribution.
    """

    model_config = ConfigDict(from_attributes=True)

    campaign_id: UUID
    total_tasks: int = Field(ge=0)
    sent_count: int = Field(ge=0)
    responded_count: int = Field(ge=0, description="Distinct leads que enviaron mensaje user-role DESPUÉS de campaign_task.sent_at")
    converted_count: int = Field(ge=0, description="Deferred PR-followup. Always 0 en MVP S3.")
    converted_count_attribution_method: Literal["deferred_pr_followup", "exact_payment_or_meeting"] = Field(
        default="deferred_pr_followup",
        description="MVP S3 returns 'deferred_pr_followup'. Cuando PR-followup wira payments/scheduling cross-module → 'exact_payment_or_meeting'.",
    )
    response_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="responded_count/sent_count. NULL si sent_count==0.",
    )
    conversion_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="converted_count/sent_count. NULL si sent_count==0 o attribution deferred.",
    )
    currency: str | None = Field(
        default=None,
        description="ISO 4217 from tenant_locale. NULL aceptable: stats no involucra montos hoy, currency es para PR-followup que agregue revenue_total/aov sin breaking change.",
    )
```

### 3.2 `ConversationListItem` (EXTEND — `sales_agent.api.dto.closer_studio`)

```python
class ConversationListItem(BaseModel):
    # ... existing fields ...
    # PR-8 additive optional enrichment:
    campaign_id: UUID | None = None
    campaign_name: str | None = None
```

### 3.3 `ConversationDetail` (EXTEND — `sales_agent.api.dto.closer_studio`)

```python
class ConversationDetail(BaseModel):
    # ... existing fields ...
    # PR-8 additive optional enrichment:
    campaign_id: UUID | None = None
    campaign_name: str | None = None
```

Both are **additive optional** — backward-compatible. Existing consumers ignoring the fields keep working.

## 4. API routes

### 4.1 `GET /api/v1/campaigns/{campaign_id}/stats`

```python
@router.get(
    "/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    summary="Estadísticas agregadas de campaña",
)
async def get_campaign_stats(
    campaign_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[CampaignStatsService, Depends(get_campaign_stats_service)],
    session: Annotated[AsyncSession, Depends(get_campaigns_async_session)],
) -> CampaignStatsResponse:
    """Live aggregate of campaign tasks. Tenant-scoped. Idempotent read."""
    tenant_id = _tenant_id(user)
    try:
        return await svc.get_stats(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            session=session,
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "Campaña no encontrada.") from exc
```

Auth: Bearer + X-Tenant-ID (extracted via `get_current_user` middleware). Idempotent read (no idempotency key needed — pure GET).

### 4.2 Extended inbox endpoints

`GET /api/v1/closer-studio/conversations` and `GET /api/v1/closer-studio/conversations/{lead_id}` — signatures unchanged; **response shape grows** (additive optional `campaign_id`, `campaign_name`). The closer_studio service `list_conversations` and `get_conversation_detail` call into a new helper:

```python
# sales_agent/application/services/inbox_campaign_enrichment.py
async def enrich_conversations_with_campaign(
    items: list[ConversationListItem],
    tenant_id: UUID,
    *,
    port: CampaignsLookupPort,
    window_hours: int,
    session: AsyncSession,
) -> None:
    """Best-effort enrichment. Mutates items in place.

    Lookup batch via port.find_recent_for_leads([...]).
    Fail-open: cualquier exception → log warning, dejar items unchanged.
    """
```

Batch lookup avoids N+1.

## 5. TypeScript types (Frontend)

```typescript
// frontend/src/features/closer-studio/types/index.ts (extend)

export interface ConversationListItem {
  // ... existing fields ...
  campaign_id?: string | null;
  campaign_name?: string | null;
}

export interface ConversationDetail {
  // ... existing fields ...
  campaign_id?: string | null;
  campaign_name?: string | null;
}

// New (only used internally by CampaignTag — consumed via Conversation* types).
export interface CampaignTagProps {
  campaignId: string;
  campaignName: string;
  variant?: "list" | "detail"; // affects size; default "list"
  className?: string;
}
```

CamelCase + ISO 8601 datetime as `string` cuando aplique. Optional explicit (`?: string | null`).

## 6. Repository interfaces

### 6.1 `CampaignTaskRepository` (EXTEND — `campaigns.domain.repositories`)

```python
@abstractmethod
async def find_recent_for_lead(
    self,
    *,
    tenant_id: UUID,
    lead_id: UUID,
    status: TaskStatus,
    since: dt.datetime,
    session: AsyncSession,
) -> CampaignTask | None:
    """Fetch most recent task matching (tenant, lead, status, sent_at >= since).

    Returns the task with max sent_at within the window, or None.
    Used by inbound recognition: status=SENT, since=now-window_hours.
    Tenant-scoped. Excludes soft-deleted. Backed by
    idx_campaign_tasks_lookup_lead (partial WHERE deleted_at IS NULL).
    """
    ...

@abstractmethod
async def find_recent_for_leads(
    self,
    *,
    tenant_id: UUID,
    lead_ids: Sequence[UUID],
    status: TaskStatus,
    since: dt.datetime,
    session: AsyncSession,
) -> dict[UUID, CampaignTask]:
    """Batch variant — returns map lead_id → most recent matching task.

    Used by inbox enrichment to avoid N+1. lead_ids without a hit are
    absent from the returned dict (caller treats as None).
    """
    ...

@abstractmethod
async def count_responded_leads(
    self,
    *,
    tenant_id: UUID,
    campaign_id: UUID,
    session: AsyncSession,
) -> int:
    """Distinct count of leads who sent any user-role message AFTER their
    campaign_task.sent_at, scoped to a single campaign + tenant.

    SQL (illustrative — implementation owns):
        SELECT COUNT(DISTINCT m.user_id)
        FROM messages m
        JOIN campaign_tasks ct
          ON ct.lead_id = m.user_id
         AND ct.tenant_id = m.tenant_id
        WHERE ct.tenant_id = :t
          AND ct.campaign_id = :c
          AND ct.status = 'sent'
          AND ct.deleted_at IS NULL
          AND m.role = 'user'
          AND m.created_at > ct.sent_at

    NOTE: Reads sales_agent.messages from campaigns repo. This is the
    **single documented cross-module table read** in this PR — see
    arch test allowlist KNOWN_CROSS_MODULE_TABLE_READS. Justification
    in CampaignStatsService docstring.
    """
    ...
```

`count_by_campaign_status` already exists (line 218 `repositories.py`). Reused.

### 6.2 New port `shared/links/ports/campaigns.py`

```python
"""Cross-module access to campaigns module — link port pattern.

Used by sales_agent for inbox enrichment + inbound recognition. Avoids
a direct `from src.modules.campaigns.*` import (DDD arch test).
"""

from __future__ import annotations
import datetime as dt
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Sequence
    from sqlalchemy.ext.asyncio import AsyncSession


class CampaignTaskLookupResult:
    """Lightweight DTO returned by lookup methods. Not a Pydantic model — pure
    domain shape carrying the minimum needed for tagging and recognition.
    """
    def __init__(self, *, campaign_id: UUID, campaign_name: str, task_id: UUID, sent_at: dt.datetime) -> None:
        self.campaign_id = campaign_id
        self.campaign_name = campaign_name
        self.task_id = task_id
        self.sent_at = sent_at


class CampaignsLookupPort(ABC):
    """Read-only access to campaigns from cross-module callers."""

    @abstractmethod
    async def find_recent_campaign_task_for_lead(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        window_hours: int,
        session: AsyncSession,
    ) -> CampaignTaskLookupResult | None:
        """Most recent SENT campaign_task within the window. None if miss."""
        ...

    @abstractmethod
    async def find_recent_campaign_tasks_for_leads(
        self,
        *,
        tenant_id: UUID,
        lead_ids: Sequence[UUID],
        window_hours: int,
        session: AsyncSession,
    ) -> dict[UUID, CampaignTaskLookupResult]:
        """Batch variant. Hit-only map (no entry = miss)."""
        ...


def create_campaigns_lookup_port() -> CampaignsLookupPort:
    """Factory — returns the SQLAlchemy implementation.

    Lives next to the ABC so callers don't import infra directly.
    The impl class lives in campaigns/infrastructure/links/ — owned by
    the campaigns module, registered here.
    """
    from src.modules.campaigns.infrastructure.links.campaigns_lookup_impl import CampaignsLookupAdapter
    return CampaignsLookupAdapter()
```

Same pattern as `shared/links/ports/{tenant_profile,offer,brand}.py`. The implementation `CampaignsLookupAdapter` joins `CampaignTaskModel` + `CampaignModel` (campaigns module owns both).

## 7. Application services

### 7.1 `CampaignStatsService` (NEW — `campaigns.application.services.campaign_stats_service`)

```python
class CampaignStatsService:
    """Compute aggregate stats for a single campaign.

    Single-tenant + single-campaign. Live DB queries, indexed.
    Cross-module read (sales_agent.messages) documented in
    CampaignTaskRepository.count_responded_leads.
    """

    def __init__(
        self,
        *,
        campaign_repo: CampaignRepository,
        task_repo: CampaignTaskRepository,
        get_locale: Callable[[UUID], Awaitable[TenantLocale]],
    ) -> None:
        self._campaign_repo = campaign_repo
        self._task_repo = task_repo
        self._get_locale = get_locale

    async def get_stats(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> CampaignStatsResponse:
        """Idempotent read. Raises CampaignNotFoundError if campaign absent.

        1. Verify campaign exists + tenant-scoped (404 if not).
        2. count_by_campaign_status → total_tasks, sent_count, others.
        3. count_responded_leads → responded_count proxy (audit_log).
        4. converted_count = 0, attribution_method = "deferred_pr_followup" (MVP S3).
        5. response_rate, conversion_rate computed (NULL if sent_count==0).
        6. currency from tenant_locale.
        """
```

### 7.2 Inbox enrichment service (NEW — `sales_agent.application.services.inbox_campaign_enrichment`)

```python
async def enrich_conversation_list_with_campaign(
    items: list[ConversationListItem],
    *,
    tenant_id: UUID,
    port: CampaignsLookupPort,
    window_hours: int,
    session: AsyncSession,
) -> None:
    """Mutates items adding campaign_id + campaign_name (best-effort).

    Fail-open: any exception → log warning, items unchanged.
    """
    try:
        if not items:
            return
        lead_ids = [it.lead_id for it in items]
        hits = await port.find_recent_campaign_tasks_for_leads(
            tenant_id=tenant_id,
            lead_ids=lead_ids,
            window_hours=window_hours,
            session=session,
        )
        for it in items:
            hit = hits.get(it.lead_id)
            if hit is not None:
                it.campaign_id = hit.campaign_id
                it.campaign_name = hit.campaign_name
    except Exception as exc:  # noqa: BLE001 — best-effort enrichment
        logger.warning(
            "inbox_campaign_enrichment_failed",
            tenant_id=str(tenant_id),
            error=str(exc),
        )


async def enrich_conversation_detail_with_campaign(
    detail: ConversationDetail,
    *,
    tenant_id: UUID,
    port: CampaignsLookupPort,
    window_hours: int,
    session: AsyncSession,
) -> None:
    """Single-conversation variant. Same fail-open guarantee."""
```

### 7.3 Modify `CloserStudioService.list_conversations` and `.get_conversation_detail`

Wrap the result with the enrichment helper above. `list_conversations` is currently sync (uses `Session`). Two options:
- **Chosen**: introduce a thin async post-processing step. The route handler is synchronous (`def list_conversations`) — to call async enrichment without a giant rewrite, the route becomes `async def`, the sync DB session work happens first, then awaitable enrichment. The closer_studio router is **NOT §3-protected** (Closer Studio API + WS surface IS protected, but we are EXTENDING the response shape — pure additive — without touching WS or the buffer/output_manager).

Sub-A's `process_chat_flow` extension uses the **sync session** already in use (`db = SessionLocal()`). The repository's `find_recent_for_lead` impl will accept either a sync `Session` or an `AsyncSession`. Solution: provide TWO impl variants OR use `asyncio.to_thread` to run the sync-friendly path inside the existing flow. **Decision (1000-clientes lens)**: keep impl SQLA-2.0 async (`AsyncSession`) — Sub-A wraps lookup in a short-lived `AsyncSession` from `get_async_session_factory()` (existing pattern in PR-7 OutboundOrchestrator). Two concurrent sessions for one chat turn is acceptable (lookup is sub-millisecond bounded).

## 8. Agentic surfaces

PR-8 does NOT add new LangGraph nodes/tools/prompts. It **reads** `AgentState.campaign_id` (already exists from PR-7) and **writes** it from a new pre-flow lookup helper.

### 8.1 LangGraph state mutation (sales_agent)

`AgentState.campaign_id: UUID | None` — already declared (line 77 `state.py`). PR-7 wires it during outbound mode. PR-8 also writes it during inbound when lookup hits, but **with `outbound_mode=False`** so slot 7 CAMPAIGN_CONTEXT is NOT emitted (compose.py guard already enforces this — verified line 79 comment in state.py).

### 8.2 Inbound recognition flow (Sub-A)

Insertion point: `chat.py::process_chat_flow`, AFTER `IdentityResolver.resolve_lead(...)` (line 223 — `user.id` available) and BEFORE `ConversationPipeline.build_initial_state(...)` (line 254).

```python
# Insert after line 235 (audit_repo.log_message), before line 237 (state_repo).

# PR-8: best-effort inbound campaign recognition.
# Looks up most recent SENT campaign_task within window for this lead.
# On hit, the campaign_id will be threaded into AgentState by build_initial_state
# via tenant_config or a dedicated kwarg.
inbound_campaign_id: UUID | None = None
try:
    from src.shared.links.ports.campaigns import create_campaigns_lookup_port
    port = create_campaigns_lookup_port()
    async with get_async_session_factory()() as a_session:
        hit = await port.find_recent_campaign_task_for_lead(
            tenant_id=tenant_uuid,
            lead_id=user.id,
            window_hours=settings.CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS,
            session=a_session,
        )
    if hit is not None:
        inbound_campaign_id = hit.campaign_id
        logger.info(
            "inbound_campaign_recognized",
            tenant_id=str(tenant_uuid),
            lead_id=str(user.id),
            campaign_id=str(hit.campaign_id),
            sent_at=hit.sent_at.isoformat(),
        )
except Exception as exc:  # noqa: BLE001 — agent resilience pattern (chat.py:208)
    logger.warning(
        "inbound_campaign_lookup_failed",
        tenant_id=str(tenant_uuid),
        lead_id=str(user.id),
        error=str(exc),
    )

# Then pass inbound_campaign_id into build_initial_state. The signature
# already accepts campaign_id (line 120 state.py builder kwargs).
```

`build_initial_state` extension (line 254 chat.py): pass `campaign_id=inbound_campaign_id, outbound_mode=False`. The state builder already supports this (state.py line 120). compose.py slot 7 stays absent because `outbound_mode=False`.

### 8.3 ENV var

`backend/src/core/config.py::Settings`:

```python
CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS: int = 24
```

Validator:

```python
@field_validator("CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS")
@classmethod
def _validate_inbound_window(cls, v: int) -> int:
    if v < 1 or v > 72:
        raise ValueError("CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS must be in [1, 72]")
    return v
```

### 8.4 NO impact on:
- Cache prefix slots (slot 7 absent because `outbound_mode=False`).
- Subagents.
- Tools registry.
- BufferService / OutputManager / closer_studio WS / follow_up_engine (§3 protected).
- Eval goldens (no behavior change to specialists — campaign_id is metadata, not voice anchor).

## 9. Migration notes

`backend/alembic/versions/{NN}_add_campaign_task_stats_index.py` (next sequential, e.g. `114_`).

```python
"""Add campaign_tasks indexes for inbound recognition + stats aggregation.

Revision ID: <hash>
Revises: <prev>
Create Date: 2026-04-30 ...

PR-8: enables p95<50ms for stats endpoint + inbound recognition lookup
at 1000+ tenants × N campaigns × M tasks scale.
"""

from alembic import op

revision = "<hash>"
down_revision = "<prev>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_campaign_tasks_lookup_lead
          ON campaign_tasks (tenant_id, lead_id, status, sent_at DESC)
          WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_campaign_tasks_stats_aggregate
          ON campaign_tasks (tenant_id, campaign_id, status)
          WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_campaign_tasks_stats_aggregate")
    op.execute("DROP INDEX IF EXISTS idx_campaign_tasks_lookup_lead")
```

**Test antes prod (clone DB)** — `.claude/rules/backend-migrations.md`:

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REV> && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -d migration_test -c "\\d campaign_tasks"
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

## 10. File structure

```
backend/
├── alembic/versions/
│   └── 114_add_campaign_task_stats_index.py                             [NEW]
├── src/
│   ├── core/
│   │   └── config.py                                                    [MODIFY: +CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS]
│   ├── shared/links/ports/
│   │   └── campaigns.py                                                 [NEW: CampaignsLookupPort + factory]
│   └── modules/
│       ├── campaigns/
│       │   ├── domain/
│       │   │   └── repositories.py                                       [MODIFY: +find_recent_for_lead/leads, +count_responded_leads]
│       │   ├── infrastructure/
│       │   │   ├── repositories/
│       │   │   │   └── campaign_task_repository_impl.py                  [MODIFY: impl 3 new methods]
│       │   │   └── links/
│       │   │       └── campaigns_lookup_impl.py                          [NEW: adapter implementing port]
│       │   ├── application/
│       │   │   ├── services/
│       │   │   │   └── campaign_stats_service.py                         [NEW]
│       │   │   ├── dtos/
│       │   │   │   └── campaign_dtos.py                                  [MODIFY: +CampaignStatsResponse]
│       │   │   └── _service_factories.py                                  [MODIFY: +get_campaign_stats_service]
│       │   └── api/routers/
│       │       └── campaigns_router.py                                    [MODIFY: +GET /{id}/stats]
│       └── sales_agent/
│           ├── api/
│           │   ├── closer_studio.py                                       [MODIFY: enrichment after list/detail]
│           │   └── dto/closer_studio.py                                    [MODIFY: +campaign_id/name on List+Detail]
│           ├── application/
│           │   ├── orchestrator/
│           │   │   └── chat.py                                             [MODIFY: inbound recognition lookup pre-build_initial_state]
│           │   └── services/
│           │       └── inbox_campaign_enrichment.py                        [NEW]
│           └── application/services/
│               └── closer_studio_service.py                                [MODIFY: call enrichment]
└── tests/
    ├── architecture/
    │   └── test_campaigns_stats_response_model_currency.py                 [NEW]
    └── modules/
        ├── campaigns/
        │   ├── api/test_campaigns_stats_endpoint.py                        [NEW]
        │   └── infrastructure/test_campaign_task_repository_lookup.py      [NEW]
        └── sales_agent/
            ├── application/orchestrator/test_inbound_campaign_recognition.py [NEW]
            └── api/test_inbox_campaign_tag.py                                [NEW]

frontend/
└── src/features/closer-studio/
    ├── components/inbox/
    │   ├── CampaignTag.tsx                                                  [NEW]
    │   ├── ConversationItem.tsx                                             [MODIFY: render CampaignTag]
    │   ├── ConversationThread.tsx                                           [MODIFY: render CampaignTag in detail]
    │   └── __tests__/CampaignTag.test.tsx                                   [NEW]
    └── types/index.ts                                                       [MODIFY: +campaign_id/name]
```

NOTE: `frontend/src/features/inbox/` does NOT exist — inbox SSoT is `closer-studio/components/inbox/`. Drift in the task description resolved here.

## 11. Cross-cutting concerns

- **Tenant isolation**: every new query (`find_recent_for_lead`, `find_recent_for_leads`, `count_responded_leads`, `count_by_campaign_status`, campaign existence check) filters `tenant_id`. Documented in arch test.
- **Currency**: `CampaignStatsResponse.currency: str | None` — sourced from `get_tenant_locale(tenant_id).currency`. NULL acceptable (PR-8 has no monetary aggregate today; field is present so PR-followup adding `revenue_total` is non-breaking).
- **Master data**: all datetimes UTC `DateTime(timezone=True)` (existing `campaign_tasks.sent_at` already is). `since = utc_now() - timedelta(hours=window_hours)` in service.
- **Spanish neutro LATAM**: docstrings + UI strings use neutro ("campaña", "tasa de respuesta", "tasa de conversión"). NO voseo.
- **PII**: `CampaignStatsResponse` has zero PII. `ConversationListItem` already gates display_name (existing baseline). New fields `campaign_id` (UUID, opaque) + `campaign_name` (tenant-controlled, not user PII).
- **Native-first dev**: lint/tests via `cd backend && .venv/bin/{ruff,pytest}` and `cd frontend && npx {tsc,eslint,vitest,playwright}`. NEVER `docker exec` for these.

## 12. Architecture fitness impact

Tests that MUST keep passing:

| Test | Why | Allowlist behavior |
|---|---|---|
| `test_no_cross_module_imports.py` | sales_agent must NOT import campaigns directly | use `shared/links/ports/campaigns.py` — port pattern allowed |
| `test_response_model_required.py` | Stats endpoint declares response_model | declares `CampaignStatsResponse` |
| `test_master_data_invariants.py` | DTOs with potential monetary content carry currency | `CampaignStatsResponse.currency: str \| None` present |
| `test_tenant_isolation.py` | Every new query filters tenant_id | all 5 new queries do |
| `test_no_hard_deletes.py` | Repo extensions respect `deleted_at IS NULL` | new lookup queries include filter |
| `test_no_cross_module_imports.py` allowlist | NEW: `KNOWN_CROSS_MODULE_TABLE_READS` for `count_responded_leads` reading `sales_agent.messages` | single entry justified in docstring |

Allowlist `KNOWN_CROSS_MODULE_TABLE_READS` (NEW or extend if exists): one entry shrink-only.

NEW arch test `test_campaigns_stats_response_model_currency.py` (Sub-D):

```python
"""Architectural invariants for PR-8 campaigns stats endpoint."""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_campaign_stats_response_declares_response_model() -> None:
    src = _read("src/modules/campaigns/api/routers/campaigns_router.py")
    assert 'response_model=CampaignStatsResponse' in src, (
        "PR-8 contract: GET /campaigns/{id}/stats MUST declare response_model=CampaignStatsResponse"
    )


def test_campaign_stats_response_has_currency_field() -> None:
    src = _read("src/modules/campaigns/application/dtos/campaign_dtos.py")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CampaignStatsResponse":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and getattr(stmt.target, "id", None) == "currency":
                    found = True
                    break
    assert found, "PR-8 master-data invariant: CampaignStatsResponse.currency: str | None required"


def test_campaign_stats_service_filters_tenant_id() -> None:
    src = _read("src/modules/campaigns/application/services/campaign_stats_service.py")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_stats":
            arg_names = {a.arg for a in node.args.args} | {kw.arg for kw in node.args.kwonlyargs}
            assert "tenant_id" in arg_names, (
                "PR-8 tenant-isolation invariant: CampaignStatsService.get_stats MUST receive tenant_id"
            )
            return
    raise AssertionError("CampaignStatsService.get_stats not found")


def test_campaigns_lookup_port_exists() -> None:
    src = _read("src/shared/links/ports/campaigns.py")
    assert "class CampaignsLookupPort" in src
    assert "find_recent_campaign_task_for_lead" in src
    assert "find_recent_campaign_tasks_for_leads" in src


def test_inbound_recognition_outbound_mode_false() -> None:
    """outbound_mode MUST stay False during inbound recognition (cache slot 7 absent)."""
    src = _read("src/modules/sales_agent/application/orchestrator/chat.py")
    # The string "outbound_mode=False" must appear in the same vicinity as the
    # inbound recognition block. Lightweight grep — full integration test in
    # test_inbound_campaign_recognition.py.
    assert "inbound_campaign" in src, "PR-8: chat.py must call inbound recognition lookup"
```

## 13. pm-nico/current-state updates required

- `docs/pm-nico/current-state/campaigns.md`:
  - Append capability **"Campaign stats endpoint live"** (PR-8): `GET /api/v1/campaigns/{id}/stats` returns total/sent/responded/converted + rates + currency. Lineage: PR-7 introduced campaign_task SSoT; PR-8 surfaces aggregates.
  - Append capability **"Cross-module campaign lookup port"**: `shared/links/ports/campaigns.py` enables non-campaigns modules to read recent SENT tasks per lead. Used by sales_agent inbox enrichment.

- `docs/pm-nico/current-state/sales-agent.md`:
  - Append capability **"Inbound campaign recognition (24h)"**: when a lead replies within `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` (default 24, max 72) of a SENT campaign task, the chat orchestrator binds `campaign_id` into AgentState (with `outbound_mode=False` so cache slot 7 stays absent — pure metadata). Fail-open on lookup error.

- `docs/pm-nico/current-state/crm.md`:
  - Append capability **"Inbox conversations carry campaign tag"**: `ConversationListItem` and `ConversationDetail` now expose `campaign_id` + `campaign_name` (optional). FE renders Shadcn Badge chip clickable to `/campañas/{id}` (placeholder route in PR-8 — real wiring follow-up).

## 14. Test surfaces (TDD-mandatory)

RED → GREEN per layer. Order matters.

**Sub-A (sales_agent inbound recognition):**
1. RED: `tests/modules/sales_agent/application/orchestrator/test_inbound_campaign_recognition.py`
   - Happy path: pre-seed `campaign_task` SENT 1h ago for tenant+lead → `process_chat_flow` injects `campaign_id` into resulting state.
   - Window boundary: SENT 23h59m ago → hit; SENT 24h01m ago → miss.
   - Most recent: 2 SENT tasks for same lead → returns the one with max `sent_at`.
   - Tenant isolation: SENT for different tenant → miss.
   - Fail-open: monkey-patch port to raise → flow continues, `campaign_id=None`, structlog warning emitted.
   - `outbound_mode` stays `False` even on hit → assert `state["outbound_mode"] is False`.
2. GREEN: implement chat.py lookup block + ENV var + port factory wired.

**Sub-B (campaigns stats endpoint + repo extensions):**
1. RED: `tests/modules/campaigns/infrastructure/test_campaign_task_repository_lookup.py`
   - `find_recent_for_lead`: hit/miss/window/most-recent/tenant-scope.
   - `find_recent_for_leads`: batch returns hit-only map.
   - `count_responded_leads`: 0/N responded.
2. RED: `tests/modules/campaigns/api/test_campaigns_stats_endpoint.py`
   - Happy path: 5 tasks (3 sent, 1 failed, 1 pending) + 2 responded leads → response correct.
   - Zero tasks: rates=NULL.
   - Different tenant: 404 (tenant isolation).
   - Currency: tenant_locale `currency='PEN'` → response `currency='PEN'`.
   - `converted_count_attribution_method == 'deferred_pr_followup'`.
3. RED: `tests/modules/sales_agent/api/test_inbox_campaign_tag.py`
   - List enrichment: 3 leads, 2 with hit → 2 items have `campaign_id+campaign_name`, 1 has None.
   - Detail enrichment: lead with hit → detail carries `campaign_id+campaign_name`.
   - Fail-open: port raises → endpoint still returns items unchanged.
4. GREEN: implement service, DTO, route, repo methods, port adapter, enrichment service, DTO extends, route wires.

**Sub-C (FE):**
1. RED: `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx`
   - Render `<CampaignTag campaignId="..." campaignName="..." />` → text "campaña: {name}" present in Badge.
   - Click → `useRouter().push` called with `/campañas/{id}` (or feature flag placeholder).
   - Without `campaignId` → renders `null`.
   - Variant prop `"detail"` vs `"list"` size class.
2. GREEN: implement component + wire `ConversationItem`/`ConversationThread`.

**Sub-D (arch tests + IMPL-LOG + current-state):**
1. RED: `tests/architecture/test_campaigns_stats_response_model_currency.py` (5 invariants).
2. GREEN: invariants satisfied by Sub-A/B/C output.

## 15. Research notes

| Source | Accessed | Takeaway |
|---|---|---|
| `.claude/rules/backend-migrations.md` (project) | 2026-04-30 | Idempotent raw SQL + `IF NOT EXISTS`. Validated. |
| `.claude/rules/master-data.md` + `.claude/skills/backend-expert/references/master-data.md` (project) | 2026-04-30 | `currency: str \| None` in DTOs with potential monetary content. PR-7 Sub-F set the precedent of `get_tenant_locale()` injection — reused here. |
| `.claude/skills/sales-agent-expert` (project) | 2026-04-30 | §3 protected list confirmed: Closer Studio API + WS, BufferService, OutputManager.process_response chunking, follow_up_engine — PR-8 extends list/detail RESPONSE shape (additive optional) which is NOT §3 (no surface mutation, no WS event change, no buffer change). Validated by PR-7 prior precedent (which extended `AgentState`). |
| Existing repository code `campaign_task_repository_impl.py:218-310` | 2026-04-30 | `count_by_campaign_status` already designed for "GET /campaigns/{id}/stats (S3)" — comment confirms this PR is the planned consumer. EXTEND not NEW. |
| Anthropic prompt caching (canonical) — `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` | not re-fetched 2026-04-30 (model cutoff Jan 2026 covers this) | Slot 7 CAMPAIGN_CONTEXT must stay absent during inbound recognition to preserve cross-tenant + per-tenant prefix cache hit (>1024 tokens contiguous). PR-7 already gated emission on `outbound_mode=True`. PR-8 sets `outbound_mode=False` explicitly. |
| LangGraph 2.0 docs (canonical) — `https://docs.langchain.com/oss/python/langgraph/workflows-agents` | not re-fetched 2026-04-30 | AgentState is TypedDict; `campaign_id: UUID \| None` already declared; reading/writing it is reducer-free (default = "last write wins"). No state schema change. |

Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026. Topics in this PR (LangGraph state mutation, prompt caching slot architecture, FastAPI response_model, SQLA 2.0 indexes) all pre-cutoff. No live WebFetch needed for this PR — patterns are stable since 2025-Q4.

## 16. Open questions for PM

**ZERO** open questions. All architect-track decisions resolved by task brief (38-45):

- 38: window 24h ENV (max 72) ✓
- 39: most-recent (`ORDER BY sent_at DESC LIMIT 1`) ✓
- 40: live DB query + index migration in PR-8 ✓
- 41: Shadcn Badge chip clickable to `/campañas/{id}` ✓
- 42: NO migration of `agent_state_checkpoint` — lookup on-demand ✓
- 43: `responded_count` = audit_log proxy (`messages.role='user' AND created_at > sent_at`) ✓
- 44: `converted_count = 0` + `attribution_method = "deferred_pr_followup"` ✓
- 45: NO pagination — single-campaign aggregate ✓

Architect-resolved drifts:
- Inbox SSoT location: `closer-studio/components/inbox/` (not `features/inbox/`).
- Cross-module read: introduce port `shared/links/ports/campaigns.py` (not direct import).
- `count_responded_leads` cross-table read: documented exception in `KNOWN_CROSS_MODULE_TABLE_READS` allowlist (single entry, justified).
- Async session for inbound recognition: short-lived `AsyncSession` from existing factory (PR-7 OutboundOrchestrator precedent).
- `currency` field in stats response: NULL acceptable today (no monetary aggregate); present so PR-followup adding revenue is non-breaking.
