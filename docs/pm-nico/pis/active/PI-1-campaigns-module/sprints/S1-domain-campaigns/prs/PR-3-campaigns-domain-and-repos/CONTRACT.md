# CONTRACT — PR-3-campaigns-domain-and-repos

> Owner: `nicolify-architect`. SSoT pre-implementación. Solo backend (data plane). Builder consume este archivo + sigue TDD inside-out por capa.
> Status: **READY for builder**. Zero open questions (decisiones tomadas con framing 1000 clientes, cero deuda técnica).
> Sesión: 2026-04-29 — architect post-S0 cierre. Skills consultados: `backend-expert` (DDD inside-out + master-data + currency-handling + arch-fitness), `copilot-expert` (cost recording invariants — wire diferido S2), `sales-agent-expert` (outbound gating invariants — wire diferido S3), `metrics-expert` (port `mv_daily_llm_cost_per_tenant_v2` ya consume `agent_kind="campaign"` desde PR-1, sin cambio).

## 0. Context summary

| Campo | Valor |
|---|---|
| PR ID | PR-3-campaigns-domain-and-repos |
| PI / Sprint | PI-1-campaigns-module / S1-domain-campaigns |
| Modules tocados (write) | `modules/campaigns/domain/` (NUEVO completo), `modules/campaigns/infrastructure/{models,repositories}/` (NUEVO completo), `alembic/versions/111_campaigns_domain.py` (NUEVO), `tests/modules/campaigns/{domain,infrastructure}/` (NUEVO), `tests/architecture/test_campaigns_*.py` (4 NUEVOS) |
| Modules tocados (read-only) | `shared/domain_events/outbox/domain/event.py` (importar `DomainEvent` base), `shared/domain/base_entity.py` (importar `Base` SQLA + `BaseEntity` Pydantic), `shared/links/ports/{crm,offer,brand}.py` (declaramos dependency Protocol — no impl), `modules/campaigns/observability/` (existente PR-1, sin cambio) |
| Skills consulted | `backend-expert` (Inside-Out, master-data, arch-fitness, currency-handling), `copilot-expert` (gating ref skill OK — wire diferido S2), `sales-agent-expert` (gating ref skill OK — wire diferido S3), `metrics-expert` (MV registry-based UNION-ALL ya cubre `campaign_llm_call`, sin acción) |
| pm-nico/current-state files updates post-merge | `current-state/campaigns.md` — sección "Capacidades actuales (post PR-3 S1)" agregar capability "Domain entities + repos + tablas DDL shipped" con lineage PR-3 |
| Architecture gates que deben seguir verdes | `test_ddd_boundaries.py` (sin import cross-module nuevo), `test_outbox_invariants.py` (sin cambio), `test_no_new_copilot_module_imports.py` (ratchet 22 frozen — cero cambio), `test_sales_agent_tenant_isolation.py` (sin cambio), `test_folder_naming.py`, `test_api_contracts.py`, `test_master_data_compliance.py`, `test_currency_consistency.py`, `test_domain_purity.py` |
| Architecture gates nuevos | `test_campaigns_tenant_isolation.py` (sin allowlist excepto `claim_pending_for_worker` + `cross_tenant_aggregate_count_for_global_metrics_only` documentado), `test_campaign_fsm_invariants.py` (sin allowlist), `test_segment_filter_pydantic_validated.py` (sin allowlist), `test_campaign_task_idx_workers.py` (sin allowlist) |

**Riesgo principal:** primera vez que el módulo `campaigns/` toca DDL (post-observability PR-1). Mitigación: TDD por capa estricto + clone-DB migration test + 4 arch fitness tests RED-first.

**Out of scope CONTRACT:**
- Cualquier service en `application/` (PR-4)
- Cualquier API endpoint en `api/` (PR-4)
- Cualquier DTO Pydantic request-response (PR-4)
- Cualquier ChannelRouter impl (S2)
- Cualquier worker / orchestrator (S2)
- Cualquier sales_agent OutboundOrchestrator (S3)
- Cualquier FE (post PI-1)
- Cualquier seed CampaignTemplate (PR-4)
- Wiring BudgetGuard / OutboundRateLimiter / ComplianceService (S2 worker)
- Snapshot creation logic (PR-4 service / S2 orchestrator decide cuándo crear snapshot)

---

## 1. Domain entities (Pydantic v2 puras, no framework deps)

Todas viven en `backend/src/modules/campaigns/domain/`. Pure Python — sin SQLAlchemy, sin FastAPI, sin Redis. Subclassean `BaseEntity` (Pydantic v2 base) o son standalone Pydantic v2 con `model_config = ConfigDict(...)`.

### 1.1 Enums (`domain/enums.py`)

```python
from __future__ import annotations
from enum import StrEnum


class CampaignType(StrEnum):
    """High-level campaign archetype. Drives orchestrator routing in S2."""
    AGENT_CONVERSATION = "agent_conversation"   # Sales Agent outbound 1:1 (S3 MVP 1)
    EMAIL_DRIP = "email_drip"                    # MailerLite group → automation (PI-2)
    EMAIL_BROADCAST = "email_broadcast"          # One-shot email to segment (PI-2)
    EVENT_TRIGGER = "event_trigger"              # Multi-canal anclado a fecha (PI-3)
    PUSH_NOTIFICATION = "push_notification"      # OneSignal (PI-4)
    RETARGETING_EXPORT = "retargeting_export"    # CRM → Meta Ads audience (PI-3)


class CampaignStatus(StrEnum):
    """FSM states for Campaign lifecycle. See _FSM_TRANSITIONS in campaign.py."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"  # terminal
    CANCELED = "canceled"    # terminal


class StepType(StrEnum):
    """Polymorphic CampaignStep kinds. Each maps to a Pydantic step_config schema."""
    SEND_MESSAGE = "send_message"
    WAIT_DELAY = "wait_delay"
    BRANCH_ON_CONDITION = "branch_on_condition"
    CALL_SUBAGENT_BRIEF = "call_subagent_brief"  # invokes sales_agent OutboundOrchestrator (S3)
    MARK_COMPLETE = "mark_complete"


class TaskStatus(StrEnum):
    """CampaignTask lifecycle states."""
    PENDING = "pending"        # awaiting scheduler
    SCHEDULED = "scheduled"    # scheduled_at set, awaiting worker poll
    DISPATCHED = "dispatched"  # claimed by worker, in-flight
    SENT = "sent"              # message handed off to channel
    FAILED = "failed"          # exhausted retries / fatal error
    SKIPPED = "skipped"        # compliance/rate/budget gate refused
    BOUNCED = "bounced"        # channel returned hard bounce


class SegmentType(StrEnum):
    """Segment resolution mode."""
    DYNAMIC = "dynamic"  # filter resolved on-demand
    STATIC = "static"    # snapshot at create time


class SegmentFilterCombinator(StrEnum):
    """Top-level filter logic combinator."""
    ALL = "all"  # AND
    ANY = "any"  # OR
```

### 1.2 Campaign aggregate root (`domain/campaign.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.campaigns.domain.enums import CampaignStatus, CampaignType


# FSM transitions matrix — single source of truth for arch test introspection.
_FSM_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset({CampaignStatus.SCHEDULED, CampaignStatus.CANCELED}),
    CampaignStatus.SCHEDULED: frozenset({CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.CANCELED}),
    CampaignStatus.RUNNING: frozenset({CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELED}),
    CampaignStatus.PAUSED: frozenset({CampaignStatus.RUNNING, CampaignStatus.CANCELED}),
    CampaignStatus.COMPLETED: frozenset(),  # terminal
    CampaignStatus.CANCELED: frozenset(),   # terminal
}


class Campaign(BaseModel):
    """Aggregate root. Persists Campaign lifecycle.

    Invariants:
    - tenant_id NEVER None
    - deleted_at None unless soft-deleted
    - status DRAFT default; transitions enforced via _FSM_TRANSITIONS
    - scheduled_at NOT NULL when status >= SCHEDULED (model_validator)
    - launched_at NOT NULL when status >= RUNNING (set by service PR-4)
    - completed_at NOT NULL when status in (COMPLETED, CANCELED)
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    # Type + state
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT

    # Targeting
    segment_id: UUID | None = None  # may be None for ad-hoc broadcast (future)
    segment_snapshot_id: UUID | None = None  # set when launched if audience locking enabled (S2)

    # Channel routing — priority list, first available wins (S2 ChannelRouter consumes)
    channel_priority: list[str] = Field(default_factory=list)  # ["telegram", "whatsapp", "email"]

    # FK (UUID string only — no cross-module SQL JOIN; resolution via shared/links/ports/* in service PR-4)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None  # optional pin to specific brand voice version (PI-2)

    # Type-specific config (validated by service layer PR-4 via type-specific Pydantic model)
    config: dict[str, Any] = Field(default_factory=dict)
    # AGENT_CONVERSATION: {"agent_instructions": str, "tone_override": str | None}
    # EMAIL_DRIP: {"mailerlite_group_slug": str}
    # EMAIL_BROADCAST: {"mailerlite_campaign_id": str}
    # EVENT_TRIGGER: {"anchor_event_date": iso8601, "timezone": str}
    # PUSH_NOTIFICATION: {"onesignal_template_id": str}
    # RETARGETING_EXPORT: {"meta_audience_id": str}

    # Scheduling — UTC always (regla master-data.md)
    scheduled_at: dt.datetime | None = None
    launched_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None

    # Provenance
    created_by_user_id: UUID | None = None
    created_by_source: str = Field(default="api")  # "api" | "copilot" | "manual" | "scheduler"

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None

    @model_validator(mode="after")
    def _validate_status_invariants(self) -> "Campaign":
        if self.status in (CampaignStatus.SCHEDULED, CampaignStatus.RUNNING, CampaignStatus.PAUSED) and self.scheduled_at is None:
            raise ValueError(f"scheduled_at required when status={self.status.value}")
        if self.status == CampaignStatus.RUNNING and self.launched_at is None:
            raise ValueError("launched_at required when status=running")
        if self.status in (CampaignStatus.COMPLETED, CampaignStatus.CANCELED) and self.completed_at is None:
            raise ValueError(f"completed_at required when status={self.status.value}")
        if self.status >= CampaignStatus.SCHEDULED and self.campaign_type == CampaignType.AGENT_CONVERSATION:
            # AGENT_CONVERSATION requires an offer reference (sales_agent uses offer context)
            if self.offer_id is None:
                raise ValueError("offer_id required for AGENT_CONVERSATION campaigns from SCHEDULED onward")
        return self

    @classmethod
    def transition_allowed(cls, from_status: CampaignStatus, to_status: CampaignStatus) -> bool:
        """Pure check. Service layer PR-4 calls this before persist."""
        return to_status in _FSM_TRANSITIONS[from_status]
```

**Invariantes domain-level:**
- `tenant_id` MANDATORY.
- `deleted_at` MANDATORY soft delete column.
- FSM transitions exposed via classmethod for service consumption + arch test introspection.
- `model_config = ConfigDict(extra="forbid")` — domain rejects unknown fields strictly.
- `created_by_source` whitelist (`api|copilot|manual|scheduler`) is service-validated PR-4 (no Enum here — keeps domain tolerant to new sources without migration).

### 1.3 CampaignStep (`domain/campaign_step.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.campaigns.domain.enums import StepType


class CampaignStep(BaseModel):
    """Polymorphic step within a Campaign DAG.

    DAG structure: each step has next_step_ids (list[UUID]) for branching.
    PR-3 stores list[UUID] in JSONB. service PR-4 / orchestrator S2 walks the DAG.

    step_config Pydantic schemas validated per step_type by service layer (PR-4) —
    domain stores raw dict; service layer dispatches to the right Pydantic model.

    Invariants enforced here:
    - next_step_ids cannot contain self.id (no self-loop)
    - step_index ≥ 0 (display ordering hint, not topology)
    - tenant_id required; redundant with campaign.tenant_id but enforces row-level isolation
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID

    step_type: StepType
    step_index: int = Field(..., ge=0)  # display ordering hint
    label: str | None = Field(default=None, max_length=128)

    # DAG topology
    next_step_ids: list[UUID] = Field(default_factory=list)  # branching support

    # Polymorphic per step_type (validated by service layer PR-4)
    step_config: dict[str, Any] = Field(default_factory=dict)
    # SEND_MESSAGE: {"template_slug": str, "agent_instructions": str | None, "channel_override": str | None}
    # WAIT_DELAY: {"delay_seconds": int}
    # BRANCH_ON_CONDITION: {"condition": str, "true_next_step_id": UUID, "false_next_step_id": UUID}
    # CALL_SUBAGENT_BRIEF: {"agent_kind": "sales_agent", "brief": str}
    # MARK_COMPLETE: {}

    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None

    @model_validator(mode="after")
    def _no_self_loop(self) -> "CampaignStep":
        if self.id in self.next_step_ids:
            raise ValueError("CampaignStep cannot reference itself in next_step_ids")
        return self
```

### 1.4 CampaignTask (`domain/campaign_task.py`)

```python
from __future__ import annotations
import datetime as dt
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import TaskStatus


class CampaignTask(BaseModel):
    """Atomic execution unit per (campaign, lead, step).

    Production-grade for 1000+ tenants. Worker queue performance critical:
    - Index partial WHERE status IN ('pending','scheduled') on (tenant_id, status, scheduled_at)
    - Index (tenant_id, campaign_id, status) for reporting
    - claim_pending_for_worker uses FOR UPDATE SKIP LOCKED (same pattern as outbox)

    Invariants:
    - tenant_id MANDATORY
    - lead_id MANDATORY (the recipient)
    - step_id MANDATORY for AGENT_CONVERSATION + EVENT_TRIGGER multi-step;
      can be None for single-step EMAIL_DRIP/RETARGETING (whole campaign = single step)
    - scheduled_at MANDATORY (worker polls by it)
    - status PENDING default
    - attempt_count ≥ 0
    - outbox_event_id NULL until DISPATCHED (then FK link to domain_event_outbox.id)
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    lead_id: UUID
    step_id: UUID | None = None  # None for single-step campaigns

    status: TaskStatus = TaskStatus.PENDING

    # Scheduling
    scheduled_at: dt.datetime  # MANDATORY — worker polls by this
    dispatched_at: dt.datetime | None = None
    sent_at: dt.datetime | None = None
    executed_at: dt.datetime | None = None  # final state timestamp (sent/failed/skipped/bounced)

    # Channel resolution at execution time (S2 ChannelRouter sets)
    channel_used: str | None = Field(default=None, max_length=32)
    external_message_id: str | None = Field(default=None, max_length=255)

    # Retry + error tracking
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = Field(default=None, max_length=2000)

    # Compliance check evidence (S2 ComplianceService.check result)
    compliance_check: dict | None = None  # {"failed_policy": "waba_24h", "reason": "...", "evidence": {...}}

    # Link to outbox (S2 wiring — for now schema accepts, NULL default)
    outbox_event_id: UUID | None = None

    # Idempotency natural key — service layer PR-4 generates as f"{campaign_id}:{lead_id}:{step_id or 'single'}"
    idempotency_key: str = Field(..., min_length=1, max_length=256)

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None  # soft delete (regla backend-ddd.md)
```

### 1.5 Segment + SegmentSnapshot (`domain/segment.py`)

```python
from __future__ import annotations
import datetime as dt
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment_filter import SegmentFilter


class Segment(BaseModel):
    """Lazy-resolved or static segment of leads. Filter persisted as JSONB.

    Resolution model (decided D3):
    - DYNAMIC default — service PR-4 SegmentService.resolve(at: datetime) → set[lead_id]
      computes by querying CRM via shared/links/ports/crm.py at runtime.
    - STATIC — pinned to a SegmentSnapshot (audience locked at create time / launch time).

    Invariants:
    - tenant_id MANDATORY
    - name UNIQUE per tenant (partial unique idx WHERE deleted_at IS NULL)
    - filter_dsl validated by Pydantic SegmentFilter (model_config extra="forbid")
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    segment_type: SegmentType = SegmentType.DYNAMIC
    filter_dsl: SegmentFilter

    # Service PR-4 populates after resolve()
    estimated_size: int | None = Field(default=None, ge=0)
    last_calculated_at: dt.datetime | None = None

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None


class SegmentSnapshot(BaseModel):
    """Materialized list of lead IDs for a Segment at a point in time.

    Created by:
    - SegmentService.snapshot(segment_id) (PR-4) — explicit user action
    - CampaignOrchestrator.launch (S2) — auto-snapshot when campaign transitions to running
      and segment_type=STATIC (audience locking).

    Invariants:
    - tenant_id MANDATORY
    - lead_ids may be empty (zero-resolved segment is valid)
    - snapshotted_at UTC mandatory
    - No soft delete here — snapshots are immutable; if obsolete, hard-delete via retention worker (S2)
      EXCEPT we keep deleted_at for audit per backend-ddd.md soft-delete invariant.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    segment_id: UUID
    snapshotted_at: dt.datetime
    lead_ids: list[UUID]
    lead_count: int = Field(..., ge=0)

    # Master data
    created_at: dt.datetime
    deleted_at: dt.datetime | None = None  # soft delete invariant respected
```

### 1.6 SegmentFilter DSL (`domain/segment_filter.py`)

Decisión D4 — minimal v1 + extensible-ready abstract base.

```python
from __future__ import annotations
import datetime as dt
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import SegmentFilterCombinator


# v1 catálogo — predefined fields only (cubre 100% segmentos catálogo FOUNDATION).
# vNext = ExpressiveSegmentFilter (full JSON-logic DSL) — out of scope post PI-1.

LifecycleStage = Literal["VISITOR", "SUBSCRIBER", "MQL", "SQL", "CUSTOMER", "CHURNED"]
LeadTemperature = Literal["COLD", "WARM", "HOT"]
ChannelIdentifier = Literal["telegram_id", "whatsapp_id", "instagram_id", "tiktok_id", "email"]


class ScoreRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fit_score_min: int | None = Field(default=None, ge=0, le=100)
    fit_score_max: int | None = Field(default=None, ge=0, le=100)
    intent_score_min: int | None = Field(default=None, ge=0, le=100)
    intent_score_max: int | None = Field(default=None, ge=0, le=100)


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gte: dt.datetime | None = None  # UTC
    lte: dt.datetime | None = None


class TagsFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["any", "all"] = "any"
    tags: list[str] = Field(default_factory=list)


class PredefinedSegmentFilter(BaseModel):
    """v1 catalog of predefined fields. extra='forbid' enforced by arch test.

    Combinator logic: combinator='all' ⇒ AND, 'any' ⇒ OR (top-level only).
    Nested groups (mixed AND/OR) NOT supported v1; tracked in PR.md decisiones diferidas.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    combinator: SegmentFilterCombinator = SegmentFilterCombinator.ALL

    lifecycle_stage: list[LifecycleStage] | None = None
    temperature: list[LeadTemperature] | None = None
    score_range: ScoreRange | None = None
    source: list[str] | None = None  # UTM source / channel_type
    country: list[str] | None = Field(default=None)  # ISO 3166-1 alpha-2 lowercase, e.g. ["pe", "mx"]
    created_at_range: DateRange | None = None
    last_interaction_at_range: DateRange | None = None
    tags: TagsFilter | None = None
    is_blacklisted: bool | None = None
    has_channel_id: list[ChannelIdentifier] | None = None


# Type alias used by Segment.filter_dsl. Future: Union[PredefinedSegmentFilter, ExpressiveSegmentFilter].
SegmentFilter = PredefinedSegmentFilter
```

**Arch test invariant** (`test_segment_filter_pydantic_validated.py`): every concrete `SegmentFilter*` model must declare `model_config = ConfigDict(extra="forbid")`. AST scan + assert.

### 1.7 ChannelRouter port + ChannelSendResult (`domain/channel_router.py`)

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ChannelSendResult:
    """Result of a single outbound channel send. Service consumers update CampaignTask."""
    success: bool
    channel: str
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ChannelRouter(Protocol):
    """Domain port. Pure interface — no impl in PR-3.

    Impl lives in S2 (Telegram first, then WhatsApp + Email + IG DM PI-2/3).
    Consumers: CampaignExecutionWorker (S2), OutboundOrchestrator (S3).

    Tenant isolation: all impls MUST validate tenant_id; the lead's tenant_id
    must match the campaign's tenant_id (service layer PR-4 enforces).

    Idempotency: idempotency_key MANDATORY — adapter dedupes external sends.
    """

    async def select_channel(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        priority: list[str],
    ) -> str | None:
        """Pick the first available channel from priority for this lead.

        Returns None if no priority channel available for the lead (skip/fail task).
        """
        ...

    async def send(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        content: dict,  # adapter-specific shape, validated downstream
        *,
        idempotency_key: str,
    ) -> ChannelSendResult:
        """Send a single message via the selected channel.

        Adapter MUST:
        - Apply idempotency_key dedup (use shared/idempotency/ decorator if external HTTP).
        - Call ComplianceService.check before send (S2 wiring).
        - Call OutboundRateLimiter.check before send (S2 wiring).
        - Apply tenant locale formatting (master-data.md).
        """
        ...
```

### 1.8 CampaignTemplate (`domain/campaign_template.py`)

```python
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.domain.enums import CampaignType


class CampaignTemplate(BaseModel):
    """Reusable campaign blueprint. Globals (tenant_id NULL) + per-tenant.

    PR-3: schema only, table empty. PR-4 seedea 5 globals (welcome, launch-4day,
    webinar, cold-reactivation, post-purchase) via service layer.

    Invariants:
    - slug MANDATORY (natural key)
    - UNIQUE (tenant_id, slug) WHERE deleted_at IS NULL — supports both tenant-scoped
      and global (NULL tenant_id) via partial unique idx. NULL distinct semantics
      handled at SQL level: idx WHERE tenant_id IS NOT NULL AND deleted_at IS NULL
      + idx WHERE tenant_id IS NULL AND deleted_at IS NULL (two partial unique idx).
    - template_body JSONB validated per template_type by service PR-4
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID | None = None  # NULL = global Nicolify-provided
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1, max_length=2000)
    campaign_type: CampaignType
    template_body: dict[str, Any] = Field(default_factory=dict)  # populated by PR-4
    recommended_segment_slugs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)

    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
```

### 1.9 Domain events (`domain/events.py`)

11 eventos heredan `DomainEvent` (re-export desde `src.shared.domain_events.outbox.domain.event`). Cada evento incluye `tenant_id` MANDATORY y timestamp UTC. PR-3 declara los eventos; emit via outbox service ocurre en PR-4 service layer / S2 orchestrator.

```python
from __future__ import annotations
import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain_events.outbox.domain.event import DomainEvent


# Each event subclasses DomainEvent and declares an EVENT_NAME literal for routing.

class _CampaignEventBase(DomainEvent):
    """Shared shape: tenant_id, campaign_id, occurred_at UTC."""
    tenant_id: UUID
    campaign_id: UUID
    occurred_at: dt.datetime


class CampaignCreated(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.created"] = "campaigns.campaign.created"


class CampaignScheduled(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.scheduled"] = "campaigns.campaign.scheduled"
    scheduled_at: dt.datetime


class CampaignLaunched(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.launched"] = "campaigns.campaign.launched"
    launched_at: dt.datetime


class CampaignPaused(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.paused"] = "campaigns.campaign.paused"


class CampaignCompleted(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.completed"] = "campaigns.campaign.completed"
    completed_at: dt.datetime


class CampaignCanceled(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.campaign.canceled"] = "campaigns.campaign.canceled"
    canceled_at: dt.datetime
    reason: str | None = None


class CampaignStepAdded(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.step.added"] = "campaigns.step.added"
    step_id: UUID


class CampaignStepUpdated(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.step.updated"] = "campaigns.step.updated"
    step_id: UUID


class CampaignTaskQueued(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.task.queued"] = "campaigns.task.queued"
    task_id: UUID
    lead_id: UUID
    scheduled_at: dt.datetime


class CampaignTaskDispatched(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.task.dispatched"] = "campaigns.task.dispatched"
    task_id: UUID
    lead_id: UUID
    channel: str


class CampaignTaskSent(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.task.sent"] = "campaigns.task.sent"
    task_id: UUID
    lead_id: UUID
    channel: str
    external_message_id: str | None


class CampaignTaskFailed(_CampaignEventBase):
    EVENT_NAME: Literal["campaigns.task.failed"] = "campaigns.task.failed"
    task_id: UUID
    lead_id: UUID
    error_code: str
    error_message: str


class SegmentCreated(BaseModel):
    EVENT_NAME: Literal["campaigns.segment.created"] = "campaigns.segment.created"
    tenant_id: UUID
    segment_id: UUID
    occurred_at: dt.datetime


class SegmentSnapshotted(BaseModel):
    EVENT_NAME: Literal["campaigns.segment.snapshotted"] = "campaigns.segment.snapshotted"
    tenant_id: UUID
    segment_id: UUID
    snapshot_id: UUID
    lead_count: int
    occurred_at: dt.datetime
```

**Note**: `CampaignTaskQueued` is the most volume-heavy event (one per (campaign × lead × step) combination). Outbox-emit happens in PR-4 service layer / S2 worker — NOT in PR-3.

### 1.10 Repository interfaces (`domain/repositories.py`)

ABC async, tenant-scoped. Toda operación recibe `tenant_id` (incluido `get_by_id`).

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Sequence
import datetime as dt
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.campaign_step import CampaignStep
from src.modules.campaigns.domain.campaign_task import CampaignTask
from src.modules.campaigns.domain.campaign_template import CampaignTemplate
from src.modules.campaigns.domain.enums import CampaignStatus, TaskStatus
from src.modules.campaigns.domain.segment import Segment, SegmentSnapshot


class CampaignRepository(ABC):
    @abstractmethod
    async def append(self, campaign: Campaign, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def update(self, campaign: Campaign, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def get_by_id(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> Campaign | None: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status_filter: Sequence[CampaignStatus] | None = None,
    ) -> Sequence[Campaign]: ...

    @abstractmethod
    async def soft_delete(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> None: ...


class CampaignStepRepository(ABC):
    @abstractmethod
    async def append(self, step: CampaignStep, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def update(self, step: CampaignStep, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def get_by_id(
        self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> CampaignStep | None: ...

    @abstractmethod
    async def list_by_campaign(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> Sequence[CampaignStep]: ...

    @abstractmethod
    async def soft_delete(
        self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> None: ...


class CampaignTaskRepository(ABC):
    @abstractmethod
    async def append(self, task: CampaignTask, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def append_many(
        self, tasks: Sequence[CampaignTask], *, session: AsyncSession
    ) -> None:
        """Bulk insert. Service layer PR-4 / S2 orchestrator uses this when launching
        a campaign over a snapshot of N leads. INSERT ... ON CONFLICT (tenant_id,
        idempotency_key) DO NOTHING — at-least-once with dedup."""

    @abstractmethod
    async def get_by_id(
        self, task_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> CampaignTask | None: ...

    @abstractmethod
    async def claim_pending_for_worker(
        self,
        *,
        tenant_id: UUID | None,  # None for cross-tenant worker scope (FOR UPDATE SKIP LOCKED)
        scheduled_before: dt.datetime,
        batch_size: int = 50,
        session: AsyncSession,
    ) -> Sequence[CampaignTask]:
        """Cross-tenant capable for worker scope (S2). Documented as the ONLY
        cross-tenant exception — same pattern as outbox.claim_pending.

        SQL: SELECT ... WHERE status IN ('pending','scheduled') AND scheduled_at <= :before
              FOR UPDATE SKIP LOCKED LIMIT :batch_size

        Tenant-scoped variant (tenant_id provided) for ops/admin queries.
        """

    @abstractmethod
    async def mark_dispatched(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        outbox_event_id: UUID | None,
        session: AsyncSession,
    ) -> None: ...

    @abstractmethod
    async def mark_sent(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        external_message_id: str | None,
        channel_used: str,
        session: AsyncSession,
    ) -> None: ...

    @abstractmethod
    async def mark_failed(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        error_code: str,
        error_message: str,
        session: AsyncSession,
    ) -> None: ...

    @abstractmethod
    async def mark_skipped(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        reason: str,
        compliance_check: dict | None,
        session: AsyncSession,
    ) -> None: ...

    @abstractmethod
    async def count_by_campaign_status(
        self,
        campaign_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> dict[TaskStatus, int]:
        """For S3 GET /campaigns/{id}/stats. Returns count per status."""


class SegmentRepository(ABC):
    @abstractmethod
    async def append(self, segment: Segment, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def update(self, segment: Segment, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def get_by_id(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> Segment | None: ...

    @abstractmethod
    async def get_by_name(
        self, name: str, tenant_id: UUID, *, session: AsyncSession
    ) -> Segment | None: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Segment]: ...

    @abstractmethod
    async def soft_delete(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> None: ...


class SegmentSnapshotRepository(ABC):
    @abstractmethod
    async def append(self, snapshot: SegmentSnapshot, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def get_by_id(
        self, snapshot_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> SegmentSnapshot | None: ...

    @abstractmethod
    async def get_latest_for_segment(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> SegmentSnapshot | None: ...

    @abstractmethod
    async def list_by_segment(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession,
        limit: int = 10,
    ) -> Sequence[SegmentSnapshot]: ...


class CampaignTemplateRepository(ABC):
    @abstractmethod
    async def append(self, tpl: CampaignTemplate, *, session: AsyncSession) -> None: ...

    @abstractmethod
    async def get_by_id(
        self,
        tpl_id: UUID,
        tenant_id: UUID | None,  # None = lookup global only
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None: ...

    @abstractmethod
    async def get_by_slug(
        self,
        slug: str,
        tenant_id: UUID | None,  # None = lookup global only
        *,
        session: AsyncSession,
    ) -> CampaignTemplate | None: ...

    @abstractmethod
    async def list_globals(self, *, session: AsyncSession) -> Sequence[CampaignTemplate]: ...

    @abstractmethod
    async def list_for_tenant(
        self, tenant_id: UUID, *, session: AsyncSession,
    ) -> Sequence[CampaignTemplate]:
        """Returns globals UNION tenant-scoped. Service PR-4 uses this for "available templates" view."""
```

---

## 2. SQLAlchemy 2.0 models (`infrastructure/models/`)

`mapped_column()` syntax. `Base` from `src.shared.domain.base_entity`. `__tablename__` = `campaign_*` / `segment*` / `campaign_template`. Asynchronous-first.

### 2.1 CampaignModel (`campaign_model.py`)

```python
from __future__ import annotations
import datetime as dt
from uuid import UUID
from sqlalchemy import String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignModel(Base):
    __tablename__ = "campaign"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    campaign_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")

    segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    segment_snapshot_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    channel_priority: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    offer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    brand_summary_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    launched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by_source: Mapped[str] = mapped_column(String(32), nullable=False, default="api")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_campaign_tenant_status", "tenant_id", "status"),
        Index("ix_campaign_tenant_scheduled", "tenant_id", "scheduled_at"),
        Index("ix_campaign_tenant_created", "tenant_id", "created_at"),
        Index("ix_campaign_segment", "segment_id"),  # used by SegmentService.list_campaigns_for_segment (PR-4)
    )
```

### 2.2 CampaignStepModel (`campaign_step_model.py`)

```python
class CampaignStepModel(Base):
    __tablename__ = "campaign_step"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)

    next_step_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    step_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_campaign_step_tenant_campaign", "tenant_id", "campaign_id"),
    )
```

### 2.3 CampaignTaskModel (`campaign_task_model.py`) — performance crítico 1000 clientes

```python
from sqlalchemy import UniqueConstraint, Integer

class CampaignTaskModel(Base):
    __tablename__ = "campaign_task"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    step_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    scheduled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    channel_used: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    compliance_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    outbox_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_campaign_task_tenant_idem"),
        # Worker queue performance — partial idx (Postgres only — handled in raw SQL migration)
        # Index('ix_campaign_task_worker_queue', 'tenant_id', 'status', 'scheduled_at',
        #       postgresql_where=text("status IN ('pending','scheduled')")) — declared in migration raw SQL.
        Index("ix_campaign_task_tenant_campaign_status", "tenant_id", "campaign_id", "status"),
        Index("ix_campaign_task_lead", "lead_id"),
    )
```

### 2.4 SegmentModel + SegmentSnapshotModel

```python
class SegmentModel(Base):
    __tablename__ = "segment"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    segment_type: Mapped[str] = mapped_column(String(16), nullable=False, default="dynamic")
    filter_dsl: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    estimated_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_calculated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Partial unique idx WHERE deleted_at IS NULL declared in raw SQL migration.


class SegmentSnapshotModel(Base):
    __tablename__ = "segment_snapshot"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    segment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    snapshotted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lead_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    lead_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_segment_snapshot_tenant_segment_at", "tenant_id", "segment_id", "snapshotted_at"),
    )
```

### 2.5 CampaignTemplateModel

```python
class CampaignTemplateModel(Base):
    __tablename__ = "campaign_template"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # NULL = global
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(32), nullable=False)
    template_body: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recommended_segment_slugs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Two partial unique idx (tenant-scoped + global) declared in raw SQL migration.
```

---

## 3. API endpoints

**N/A para PR-3.** API layer es PR-4. Cero endpoint nuevo.

---

## 4. DB schema — Migration 111 (`alembic/versions/111_campaigns_domain.py`)

Idempotente raw SQL `IF NOT EXISTS`. `down_revision="110_billing_compliance_tables"`.

```python
"""campaigns_domain.

PI-1 S1 PR-3 — campaigns module data plane.
Tables: campaign, campaign_step, campaign_task, segment, segment_snapshot, campaign_template.
Idempotente raw SQL (regla backend-migrations.md).
"""

revision = "111_campaigns_domain"
down_revision = "110_billing_compliance_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── campaign ─────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(2000),
            campaign_type VARCHAR(32) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'draft',
            segment_id UUID,
            segment_snapshot_id UUID,
            channel_priority JSONB NOT NULL DEFAULT '[]'::jsonb,
            offer_id UUID,
            brand_summary_id UUID,
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            scheduled_at TIMESTAMPTZ,
            launched_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_by_user_id UUID,
            created_by_source VARCHAR(32) NOT NULL DEFAULT 'api',
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_campaign_status_values CHECK (
                status IN ('draft','scheduled','running','paused','completed','canceled')
            ),
            CONSTRAINT chk_campaign_type_values CHECK (
                campaign_type IN ('agent_conversation','email_drip','email_broadcast',
                                  'event_trigger','push_notification','retargeting_export')
            )
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_status ON campaign (tenant_id, status);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_scheduled ON campaign (tenant_id, scheduled_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_tenant_created ON campaign (tenant_id, created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_segment ON campaign (segment_id) WHERE segment_id IS NOT NULL;")

    # ── campaign_step ────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_step (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            campaign_id UUID NOT NULL,
            step_type VARCHAR(32) NOT NULL,
            step_index INT NOT NULL,
            label VARCHAR(128),
            next_step_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            step_config JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_step_type_values CHECK (
                step_type IN ('send_message','wait_delay','branch_on_condition',
                              'call_subagent_brief','mark_complete')
            ),
            CONSTRAINT chk_step_index_nonneg CHECK (step_index >= 0)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_step_tenant_campaign ON campaign_step (tenant_id, campaign_id);")

    # ── campaign_task (worker queue performance crítico) ─────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_task (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            campaign_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            step_id UUID,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            scheduled_at TIMESTAMPTZ NOT NULL,
            dispatched_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            executed_at TIMESTAMPTZ,
            channel_used VARCHAR(32),
            external_message_id VARCHAR(255),
            attempt_count INT NOT NULL DEFAULT 0,
            last_error VARCHAR(2000),
            compliance_check JSONB,
            outbox_event_id UUID,
            idempotency_key VARCHAR(256) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_task_status_values CHECK (
                status IN ('pending','scheduled','dispatched','sent','failed','skipped','bounced')
            ),
            CONSTRAINT chk_task_attempt_count_nonneg CHECK (attempt_count >= 0)
        );
    """)
    op.execute("""
        ALTER TABLE campaign_task DROP CONSTRAINT IF EXISTS uq_campaign_task_tenant_idem;
        ALTER TABLE campaign_task ADD CONSTRAINT uq_campaign_task_tenant_idem UNIQUE (tenant_id, idempotency_key);
    """)
    # Worker queue partial idx — performance crítico 1000 clientes (test arch enforce).
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_task_worker_queue
        ON campaign_task (tenant_id, status, scheduled_at)
        WHERE status IN ('pending','scheduled');
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_task_tenant_campaign_status
        ON campaign_task (tenant_id, campaign_id, status);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_campaign_task_lead ON campaign_task (lead_id);")

    # ── segment ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS segment (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            name VARCHAR(128) NOT NULL,
            description VARCHAR(1000),
            segment_type VARCHAR(16) NOT NULL DEFAULT 'dynamic',
            filter_dsl JSONB NOT NULL DEFAULT '{}'::jsonb,
            estimated_size INT,
            last_calculated_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_segment_type_values CHECK (segment_type IN ('dynamic','static')),
            CONSTRAINT chk_segment_estimated_size_nonneg CHECK (estimated_size IS NULL OR estimated_size >= 0)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_segment_tenant_name_alive
        ON segment (tenant_id, name) WHERE deleted_at IS NULL;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_segment_tenant_created ON segment (tenant_id, created_at);")

    # ── segment_snapshot ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS segment_snapshot (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            segment_id UUID NOT NULL,
            snapshotted_at TIMESTAMPTZ NOT NULL,
            lead_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            lead_count INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_snapshot_lead_count_nonneg CHECK (lead_count >= 0)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_segment_snapshot_tenant_segment_at
        ON segment_snapshot (tenant_id, segment_id, snapshotted_at DESC);
    """)

    # ── campaign_template (placeholder schema, populated PR-4) ───────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_template (
            id UUID PRIMARY KEY,
            tenant_id UUID,
            slug VARCHAR(64) NOT NULL,
            name VARCHAR(128) NOT NULL,
            description VARCHAR(2000) NOT NULL,
            campaign_type VARCHAR(32) NOT NULL,
            template_body JSONB NOT NULL DEFAULT '{}'::jsonb,
            recommended_segment_slugs JSONB NOT NULL DEFAULT '[]'::jsonb,
            tags JSONB NOT NULL DEFAULT '[]'::jsonb,
            version INT NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT chk_tpl_slug_format CHECK (slug ~ '^[a-z0-9_-]+$'),
            CONSTRAINT chk_tpl_version_pos CHECK (version >= 1),
            CONSTRAINT chk_tpl_type_values CHECK (
                campaign_type IN ('agent_conversation','email_drip','email_broadcast',
                                  'event_trigger','push_notification','retargeting_export')
            )
        );
    """)
    # Two partial unique idx — global vs tenant-scoped (NULL distinct semantics).
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_template_global_slug_alive
        ON campaign_template (slug) WHERE tenant_id IS NULL AND deleted_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_campaign_template_tenant_slug_alive
        ON campaign_template (tenant_id, slug) WHERE tenant_id IS NOT NULL AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    # Reverse drop. Idempotente.
    op.execute("DROP TABLE IF EXISTS campaign_template;")
    op.execute("DROP TABLE IF EXISTS segment_snapshot;")
    op.execute("DROP TABLE IF EXISTS segment;")
    op.execute("DROP TABLE IF EXISTS campaign_task;")
    op.execute("DROP TABLE IF EXISTS campaign_step;")
    op.execute("DROP TABLE IF EXISTS campaign;")
```

**Test idempotency clone DB (regla `backend-migrations.md`):**
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 110_billing_compliance_tables && POSTGRES_DB=migration_test alembic upgrade head'
# Re-run a second time to verify idempotency.
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic downgrade -1 && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

**No seed in PR-3.** Templates seed = PR-4. Optional default segment "all_active_leads" deferred to PR-4 service init (cleaner — service controls semantic).

---

## 5. Eventos / outbox

| Event name | Producer (eventual) | Consumer (eventual) | PR-3 emit? |
|---|---|---|---|
| `campaigns.campaign.created` | CampaignService.create (PR-4) | analytics, copilot subagent (PI-2) | NO — declared only |
| `campaigns.campaign.scheduled` | CampaignService.schedule (PR-4) | CampaignSchedulerWorker (S2) | NO |
| `campaigns.campaign.launched` | CampaignOrchestrator.launch (S2) | analytics, copilot, observability | NO |
| `campaigns.campaign.paused` | CampaignService.pause (PR-4) | observability | NO |
| `campaigns.campaign.completed` | CampaignOrchestrator.finalize (S2) | analytics | NO |
| `campaigns.campaign.canceled` | CampaignService.cancel (PR-4) | observability | NO |
| `campaigns.step.added` | CampaignService.add_step (PR-4) | observability | NO |
| `campaigns.step.updated` | CampaignService.update_step (PR-4) | observability | NO |
| `campaigns.task.queued` | CampaignOrchestrator (S2) | CampaignExecutionWorker (S2) | NO |
| `campaigns.task.dispatched` | CampaignExecutionWorker (S2) | observability | NO |
| `campaigns.task.sent` | ChannelRouter adapter (S2) | analytics, sales_agent (S3) | NO |
| `campaigns.task.failed` | CampaignExecutionWorker / adapter (S2) | observability, ops alert | NO |
| `campaigns.segment.created` | SegmentService.create (PR-4) | observability | NO |
| `campaigns.segment.snapshotted` | SegmentService.snapshot (PR-4) / S2 orchestrator | observability | NO |

PR-3 only declares the event classes. Emission via `OutboxService.enqueue_*` happens in PR-4 service layer.

---

## 6. Retry / idempotency policy

- **Idempotency keys** — `CampaignTask.idempotency_key` natural key:
  `f"task:{campaign_id}:{lead_id}:{step_id or 'single'}"` (service PR-4 generates).
  Persisted in DDL `UNIQUE (tenant_id, idempotency_key)`. Bulk inserts use `ON CONFLICT (tenant_id, idempotency_key) DO NOTHING`.
- **Retry policy** — defined in S2 worker (`CampaignExecutionWorker`). Domain stores `attempt_count` + `last_error`; max retries = 5 (recommended, not enforced here).
- **Circuit breaker** — S2 (out of scope per PI plan).

---

## 7. Tenant isolation

- `tenant_id` MANDATORY en `Campaign`, `CampaignStep`, `CampaignTask`, `Segment`, `SegmentSnapshot`. Optional `NULL` only in `CampaignTemplate.tenant_id` (global templates).
- Toda repository method recibe `tenant_id` explícito. Single documented exception: `CampaignTaskRepository.claim_pending_for_worker(tenant_id=None, ...)` — allowed for cross-tenant worker scope (FOR UPDATE SKIP LOCKED, mismo patrón outbox). Documentado en docstring + arch test allowlist.
- `CampaignTemplateRepository.list_globals()` permite `tenant_id=None` lookup (semánticamente correcto — globals son cross-tenant). Documentado en docstring + arch test allowlist.
- Cross-module reads de offers/brand/leads via `shared/links/ports/{offer,brand,crm}.py` solo. PR-3 declara dependency Protocol; impl en PR-4 service / S2 worker.
- Cero JOIN cross-module (regla `backend-ddd.md`).

---

## 8. Observability

- structlog en repos (sin print/logging). Campos clave per write: `tenant_id`, `entity_type`, `entity_id`, `operation`. Ejemplo:
  ```python
  logger.info("campaign_repository_append", tenant_id=str(c.tenant_id), campaign_id=str(c.id), status=c.status.value, campaign_type=c.campaign_type.value)
  ```
- Trace events via `agent_kind="campaign"` (registered PR-1) — wire in S2 worker, not PR-3.
- LLM cost recording via `CampaignLlmCallModel` (placeholder PR-1) — wire in S2 worker, not PR-3.

---

## 9. Cross-cutting concerns

- **Tenant isolation** — section 7. Every query.
- **Currency** — N/A en PR-3 (cero monetary fields). LLM cost lives in `campaign_llm_call` (registered PR-1, wiring S2).
- **Master data** — `created_at`/`updated_at`/`scheduled_at`/`launched_at`/`completed_at`/`dispatched_at`/`sent_at`/`executed_at`/`snapshotted_at`/`last_calculated_at` ALL `DateTime(timezone=True)`. Service PR-4 + worker S2 use `utc_now()` from `shared/domain/master_data.py`. Display layer (FE post PI-1) uses `useTenantLocale()` + `formatTenantDate*()`. `CampaignTemplate.template_body` may carry `timezone: str | None` for `EVENT_TRIGGER` anchor (validated PR-4).
- **Spanish neutro LATAM** — UI/labels not present PR-3. Docstrings + class names ENGLISH (code convention). Domain event names dot-snake_case (`campaigns.campaign.created`).
- **PII** — `CampaignTask.last_error` may carry user/lead identifiers if exception bubbles up. Builder MUST sanitize via `sanitize_payload(...)` from `shared/agent_observability/sanitization` before persist (S2 wiring; PR-3 stores raw, but cap 2000 chars in DDL prevents catastrophic leak).
- **Native-first dev** — lint/tests/type-check `cd backend && .venv/bin/{ruff,pytest,mypy}`. Migration test via `docker exec ... alembic upgrade` only (regla allowed).

---

## 10. Architecture fitness impact

### Tests existentes que deben seguir verde (sin cambio en allowlist):

- `test_ddd_boundaries.py` — PR-3 NO importa otros modules. Verify post-build.
- `test_outbox_invariants.py` — sin cambio.
- `test_no_new_copilot_module_imports.py` — ratchet 22 frozen, sin cambio.
- `test_sales_agent_tenant_isolation.py` — sin cambio.
- `test_folder_naming.py` — `campaigns/{domain,infrastructure,application,api}/` válido.
- `test_api_contracts.py` — N/A (no endpoints). Verify ratchet sin shrink no esperado.
- `test_master_data_compliance.py` — every `DateTime` column must include `timezone=True`. Verify campaigns models pass.
- `test_currency_consistency.py` — N/A (no monetary fields).
- `test_domain_purity.py` — domain modules NO importan SQLA / FastAPI.
- `test_ddd_boundaries.py` — campaigns no importa otros módulos directamente.

### Tests nuevos (allowlist shrink-only):

#### `test_campaigns_tenant_isolation.py`
AST scan de queries SQLA en `infrastructure/repositories/`. Toda `select(CampaignModel | CampaignStepModel | CampaignTaskModel | SegmentModel | SegmentSnapshotModel)` debe contener `Model.tenant_id == tenant_id` en `.where()`. Excepciones permitidas:

```python
CROSS_TENANT_ALLOWED_METHODS: frozenset[str] = frozenset({
    # FOR UPDATE SKIP LOCKED — worker-scope. Documented exception (mismo patrón outbox).
    "claim_pending_for_worker",
    # Globals lookup — campaign_template.tenant_id NULL semantic. Documented.
    "list_globals",
})
```

CampaignTemplateModel: `get_by_id(tenant_id=None)` allowed when caller is looking up globals (predicate must be `(tenant_id IS NULL OR tenant_id = :tenant_id)`).

#### `test_campaign_fsm_invariants.py`
Introspección `Campaign._FSM_TRANSITIONS`:
- Estados terminales (`COMPLETED`, `CANCELED`) tienen frozenset vacío.
- `DRAFT` puede ir a `SCHEDULED` o `CANCELED` solamente.
- `SCHEDULED` puede ir a `RUNNING`, `PAUSED`, `CANCELED`.
- `RUNNING ⇄ PAUSED` toggle.
- `RUNNING → COMPLETED | CANCELED` terminal paths.
- Property-based (Hypothesis): para cualquier `from_status`, ningún `to_status` no listado en matrix produce `transition_allowed=True`.

#### `test_segment_filter_pydantic_validated.py`
AST scan + introspect: cada `*SegmentFilter*` model declara `model_config = ConfigDict(extra="forbid")`. Scan files `domain/segment_filter.py`. Future `ExpressiveSegmentFilter` (vNext) deberá inherit la regla.

#### `test_campaign_task_idx_workers.py`
Lee `alembic/versions/111_campaigns_domain.py` y verifica:
- DDL contiene `CREATE INDEX IF NOT EXISTS ix_campaign_task_worker_queue` con `WHERE status IN ('pending','scheduled')`.
- DDL contiene `UNIQUE (tenant_id, idempotency_key)` constraint.
- DDL contiene `(tenant_id, status, scheduled_at)` column ordering.
- Performance test crítico 1000 clientes — sin estos índices, worker poll degrada O(N) en `campaign_task` table.

### Allowlists ratchet:
- `CROSS_TENANT_ALLOWED_METHODS` — 2 entries inicial. Shrink only.

---

## 11. pm-nico/current-state updates required

Post-merge, builder/PM update:

`docs/pm-nico/current-state/campaigns.md` — agregar fila a tabla "Capacidades actuales (post PR-1 S0)" → renombrar sección a "Capacidades actuales (post PR-3 S1)":

```markdown
| Domain entities + repos + tablas DDL | ✅ shipped (PR-3 S1) | Campaign / CampaignStep / CampaignTask / Segment / SegmentSnapshot / CampaignTemplate (placeholder schema) en `modules/campaigns/{domain,infrastructure}/`. Migration 111. 4 arch fitness tests. Sin services, sin endpoints, sin templates seed (eso es PR-4). |
```

Agregar fila Decisiones producto vinculadas:
- D18 (PR-3): Campaign FSM 6 estados (`draft`/`scheduled`/`running`/`paused`/`completed`/`canceled`); `running` reemplaza legacy `active` (FOUNDATION) — clarifica semántica.
- D19 (PR-3): CampaignStep DAG con `next_step_ids: list[UUID]` (no linked-list) — branching production-grade desde día 1.
- D20 (PR-3): SegmentFilter v1 minimal (10 predefined fields) + abstract base extensible-ready para vNext ExpressiveSegmentFilter post PI-1.
- D21 (PR-3): Segment lazy-resolved default + opcional SegmentSnapshot para audience locking en campaigns running.

---

## 12. Test surfaces (TDD-mandatory por capa, RED first)

### Layer A — Domain (pure Python, no DB)

1. `test_campaign_entity.py` — Pydantic invariants (`tenant_id` required, FSM model_validator, type-specific `config` dict, transition_allowed classmethod).
2. `test_campaign_fsm.py` — transitions matrix completness + reject inválidas (canceled→running, completed→running, draft→running sin scheduled).
3. `test_campaign_step_dag.py` — `next_step_ids` no self-loop, polymorphic step_config types acceptance.
4. `test_campaign_task.py` — invariants (idempotency_key required, attempt_count ≥0, scheduled_at required).
5. `test_segment.py` — invariants + filter_dsl Pydantic strict.
6. `test_segment_filter_dsl.py` — extra="forbid" enforce; reject unknown field; combinator only `all|any`; score_range bounds; country lowercase ISO; tags mode `any|all`. Property-based con Hypothesis.
7. `test_events.py` — 11 events serializan + deserializan correctamente; `tenant_id` MANDATORY en cada uno; EVENT_NAME literal correcto.

### Layer B — Infrastructure (DB-backed, AsyncSession + pytest-asyncio)

8. `test_campaign_repository.py` — CRUD async + tenant scoping + soft delete + pagination.
9. `test_campaign_step_repository.py` — CRUD + list_by_campaign + tenant scoping.
10. `test_campaign_task_repository.py` — CRUD + bulk append_many ON CONFLICT DO NOTHING + claim_pending_for_worker (FOR UPDATE SKIP LOCKED concurrency test) + state transitions (mark_dispatched/sent/failed/skipped) + count_by_campaign_status.
11. `test_segment_repository.py` — CRUD + UNIQUE (tenant_id, name) partial alive + soft delete unique behavior.
12. `test_segment_snapshot_repository.py` — CRUD + get_latest_for_segment + tenant scoping.
13. `test_campaign_template_repository.py` — CRUD + dual UNIQUE partial idx (global slug + tenant_id+slug) + list_globals + list_for_tenant (UNION semantics).

### Layer C — Architecture (introspection + AST scan)

14. `test_campaigns_tenant_isolation.py` — gate (described §10).
15. `test_campaign_fsm_invariants.py` — gate.
16. `test_segment_filter_pydantic_validated.py` — gate.
17. `test_campaign_task_idx_workers.py` — gate.

### Migration test

18. Idempotency clone-DB test per regla `backend-migrations.md`.

**No service/API tests** — esos son PR-4.

---

## 13. Research notes

No novel patterns introduced — PR-3 reuses established architecture:
- DDD Inside-Out (Nicolify codebase pattern; ref `backend-expert` skill).
- SQLAlchemy 2.0 async (Nicolify codebase; ref `shared/agent_observability/persistence/`, `shared/billing/infrastructure/`).
- Outbox pattern + idempotent migrations (Nicolify PR-1 cementado).
- FSM matrix introspection arch test (mismo patrón used in `test_workflow_compliance.py` for `Workflow` engine).
- Partial unique idx for soft-delete + tenant_id (Nicolify pattern: `segment` table mirrors what offer/brand do).
- DAG via `next_step_ids: list[UUID]` JSONB (Nicolify `Workflow` engine reuses this shape; ref copilot `workflow_metric.py`).

Production-grade decisions for 1000+ tenants validated against:
- Postgres partial index over JSONB column performance — see `mv_daily_llm_cost_per_tenant_v2` precedent.
- FOR UPDATE SKIP LOCKED worker queue pattern — ref outbox PR-1 + ARQ docs.

---

## 14. Open questions for PM

**ZERO open questions.**

Decisiones tomadas con framing "1000 clientes, cero deuda técnica":
- D1 — FSM 6 estados (`draft`/`scheduled`/`running`/`paused`/`completed`/`canceled`).
- D2 — CampaignStep DAG (`next_step_ids: list[UUID]`).
- D3 — Segment lazy default + opcional SegmentSnapshot.
- D4 — SegmentFilter v1 minimal + abstract base extensible.
- D5 — Templates rows DB con `template_body JSONB` (PR-4 seedea).

Diferimientos explícitos (no son open questions, son scope-cuts deliberadas):
- Service layer + API + DTOs → PR-4.
- ChannelRouter impl + workers + orchestrator → S2.
- sales_agent OutboundOrchestrator → S3.
- FE → post PI-1.
- ExpressiveSegmentFilter (full DSL) → post PI-1 (extensible-ready desde día 1 vía abstract base).
- SegmentFilter group nesting (mixed AND/OR) → post PI-1 (v1 top-level combinator cubre 100% catálogo FOUNDATION).

---

<!-- @pm: PR-3 PR.md + CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-3 architect done". -->
