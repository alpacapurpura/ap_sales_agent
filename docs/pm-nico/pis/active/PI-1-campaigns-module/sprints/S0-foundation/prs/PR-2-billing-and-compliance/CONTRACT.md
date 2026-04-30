# CONTRACT — PR-2-billing-and-compliance

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builder consume este archivo. Sin frontend (Streamlit admin only).
>
> Sesión: 2026-04-29 — architect post-PR-1 (PASS). Sesión 2 (2026-04-29): re-architect post PM decisions Q1-Q10 — **Q2/Q3/Q4/Q5/Q6 elevados a production-grade** ("cero deuda técnica, miles clientes pronto"). Skills consultados: `copilot-expert` (cost recording invariants + budget gating ref agregada al skill), `sales-agent-expert` (reservación 50% + tier pricing + outbound gating ref agregada al skill), `metrics-expert` (`mv_daily_llm_cost_per_tenant_v2` reuse), `backend-expert` (admin panel registry + master-data + currency-handling). Tessl: `pii-sanitisation`, `graceful-degradation`.
>
> Reglas duras: `tenant-isolation.md`, `backend-ddd.md`, `backend-migrations.md`, `architectural-fitness.md`, `master-data.md`, `currency-handling.md`, `admin-panel.md`. **PR-1 primitivas disponibles**: outbox + `@idempotent` + `agent_kind="campaign"` registrado.

## 0. Context summary

| Campo | Valor |
|---|---|
| Modules touched | `shared/billing/` (NUEVO), `shared/compliance/` (NUEVO), `admin/modules/billing.py` + `admin/pages/planes-billing.py` (NUEVO), migration 110, **NEW post-PM**: `lead_opt_ins` (compliance — Q2), `mv_refresh_log` (billing observability — Q4), `leads.country` ALTER (compliance — Q3), `plan_config.is_default` field + partial unique index (billing — Q6), Redis pub/sub channel `cache_invalidate:*` (billing — Q5) |
| Skills consulted | copilot-expert / sales-agent-expert / metrics-expert / backend-expert. **Skills updated post-PM**: `copilot-expert` (budget gating reference), `sales-agent-expert` (budget + outbound gating reference) |
| pm-nico/current-state files | `iam.md` (plan tiers cap), `copilot.md` (BudgetGuard exposed), `sales-agent.md` (50% reservation invariant + outbound rate limiter exposed), `campaigns.md` (RateLimiter+ComplianceService exposed), `crm.md` (`leads.country` field added — Q3) |
| Architecture gates | `test_outbox_invariants.py` (sin cambios), `test_admin_panel.py` (page registry), nuevos: `test_budget_reservation_invariant.py`, `test_compliance_used_by_channels.py`, `test_no_hardcoded_plan_prices.py`, `test_lead_opt_ins_invariants.py` (Q2), `test_mv_refresh_log_freshness.py` (Q4), `test_plan_config_one_default.py` (Q6) |
| Out of scope (PR-2) | wiring copilot/sales_agent/channels (S2), trial expiration worker (S2), real billing Stripe/MP (post PI-1), data migration `tenant_billing_config` legacy (S2 worker), `lead.country` UI surface (S2 — backfill column hoy, UI editor S2) |

**Decisión arquitectónica clave**: PR-2 expone APIs **sin migrar consumers**. `tenant_billing_config` legacy queda intacta. `PlanService.get_effective` cae a legacy si `tenant_subscription IS NULL` (compat shim). Esto preserva behavior copilot/cost_alert hoy y permite cutover incremental S2.

## 1. Domain entities

Todas viven en `backend/src/shared/billing/domain/` y `shared/compliance/domain/`. Pure Python (no framework). Pydantic v2 frozen donde aplica.

### 1.1 PlanConfig (Value Object)

```python
# shared/billing/domain/plan.py
from __future__ import annotations
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class PlanConfig(BaseModel):
    """Catalog row → in-memory VO. Globalmente compartido (no per-tenant)."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    plan_id: str = Field(..., min_length=2, max_length=32)              # 'free' | 'basic' | 'intermediate' | 'advanced' | 'ultra'
    display_name: str = Field(..., min_length=1, max_length=64)
    llm_budget_total_usd: Decimal = Field(..., gt=Decimal(0), max_digits=10, decimal_places=2)
    sales_agent_reserved_pct: Decimal = Field(default=Decimal("0.50"), ge=Decimal(0), le=Decimal(1), max_digits=4, decimal_places=3)
    max_outbound_msg_per_day: int | None = Field(default=None, ge=0)    # None == unlimited (subject to budget)
    max_campaigns_active: int | None = Field(default=None, ge=0)
    max_segment_size: int | None = Field(default=None, ge=0)
    max_contacts_total: int | None = Field(default=None, ge=0)
    features: dict[str, bool] = Field(default_factory=dict)             # e.g. {"event_campaigns": True}
    is_active: bool = True
    is_default: bool = False                                            # PM Q6: exactly-one-default invariant (partial unique idx in DB)

    @property
    def sa_pool_usd(self) -> Decimal:
        """SA reserved pool for the cycle (USD)."""
        return (self.llm_budget_total_usd * self.sales_agent_reserved_pct).quantize(Decimal("0.01"))

    @property
    def others_pool_usd(self) -> Decimal:
        """Non-SA pool (copilot + future agents)."""
        return (self.llm_budget_total_usd - self.sa_pool_usd).quantize(Decimal("0.01"))
```

**Currency policy:** todos los planes son **USD por design** (Chris cobra en USD). `llm_budget_total_usd` no incluye campo `currency` — el sufijo del nombre es el contrato. Documentado en docstring + `test_no_hardcoded_plan_prices.py` enforza no leaks `'USD'` literal fuera de migration seed. NO vamos a `master-data.md` `currency` per-tenant override aquí: el budget es operacional Nicolify (no facturable user-facing). El display tenant-locale ocurrirá en S2 cuando wire UI tenant-facing.

### 1.2 TenantSubscription (Entity)

```python
# shared/billing/domain/subscription.py
from __future__ import annotations
import datetime as dt
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class TenantSubscription(BaseModel):
    """1:1 tenant ↔ plan + per-tenant overrides."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    tenant_id: UUID
    plan_id: str = Field(..., min_length=2, max_length=32)
    cycle_anchor_day: int = Field(default=1, ge=1, le=28)               # día 29-31 ambiguous para meses cortos
    custom_overrides: dict[str, Any] = Field(default_factory=dict)      # {"llm_budget_total_usd": 50, "max_outbound_msg_per_day": 5000}
    trial_ends_at: dt.datetime | None = None                            # UTC. NULL == no trial. Auto-expire worker en S2.
    activated_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
```

**Master-data**: `cycle_anchor_day` semantics → día del mes UTC en que se reinicia ciclo. Para mes con menos días que anchor (ej. anchor=29 en feb), reusa `compute_cycle_start_py` (existente en `shared/agent_observability/reporting/cycle_window.py`). PR-2 hereda DEFAULT_ANCHOR_DAY=25 vía `get_effective` con fallback. Constraint `cycle_anchor_day BETWEEN 1 AND 28` evita ambigüedad.

### 1.3 BudgetDecision (Value Object)

```python
# shared/billing/domain/budget_decision.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class BudgetDecision:
    allowed: bool
    pool: str                     # "sales_agent" | "others"
    spent_usd: Decimal            # cycle-to-date
    cap_usd: Decimal              # bucket cap for this call
    soft_warn: bool = False       # ≥80% pool consumed, still allowed
    reason: str | None = None     # "cycle_budget_exhausted" | "mv_stale_soft_cap" | None
    decision_id: str | None = None  # uuid for trace correlation (optional)
```

### 1.4 ChannelBlacklistEntry (Entity)

```python
# shared/compliance/domain/blacklist_entry.py
from __future__ import annotations
import datetime as dt
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ChannelBlacklistEntry(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    tenant_id: UUID
    channel: str = Field(..., min_length=1, max_length=32)              # "whatsapp" | "telegram" | "instagram" | "tiktok" | "email" | ...
    identifier: str = Field(..., min_length=1, max_length=255)          # phone, email, channel_user_id (NORMALIZED to E.164/lowercased)
    reason: str | None = Field(default=None, max_length=255)
    created_by_user_id: UUID | None = None
    created_at: dt.datetime
    deleted_at: dt.datetime | None = None
```

### 1.5 CheckResult (Value Object — compliance)

```python
# shared/compliance/domain/check_result.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class CheckResult:
    allowed: bool
    failed_policy: str | None = None    # "waba_24h" | "opt_in" | "blacklist" | "country_block" | None
    reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)  # last_inbound_at, opt_in_source, country_iso, etc.
```

### 1.6 LeadOptIn (Entity — PM decision Q2)

**Decision Q2**: tabla dedicada AHORA (no stub). Rationale Chris: implicit consent (messages.role='user') es heurístico frágil; explicit timestamps + source + GDPR/LGPD audit trail = production-grade.

```python
# shared/compliance/domain/lead_opt_in.py
from __future__ import annotations
import datetime as dt
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

OptInSource = Literal["webhook", "manual", "imported", "inferred_message"]

class LeadOptIn(BaseModel):
    """Per-channel opt-in / opt-out audit trail with explicit timestamps."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    tenant_id: UUID
    lead_id: UUID
    channel: str = Field(..., min_length=1, max_length=32)        # whatsapp | telegram | instagram | tiktok | email | ...
    opted_in_at: dt.datetime | None = None                         # UTC. NULL == never opted-in
    opted_out_at: dt.datetime | None = None                        # UTC. NULL == not opted-out
    source: OptInSource                                            # provenance for audit
    evidence: dict[str, Any] = Field(default_factory=dict)         # webhook_event_id, message_id, importer_batch, etc.
    created_at: dt.datetime
    updated_at: dt.datetime

    @property
    def is_active_opt_in(self) -> bool:
        """Lead is opted-in iff opted_in_at NOT NULL AND opted_out_at IS NULL."""
        return self.opted_in_at is not None and self.opted_out_at is None
```

### 1.7 MVRefreshLog (Entity — PM decision Q4)

**Decision Q4**: tabla dedicada AHORA. Rationale Chris: `pg_stat_user_tables.last_vacuum` ≠ last refresh real, frágil. Dedicated log = exact freshness signal + status + duration metric.

```python
# shared/billing/domain/mv_refresh_log.py
from __future__ import annotations
import datetime as dt
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

RefreshStatus = Literal["ok", "error", "skipped"]

class MVRefreshLog(BaseModel):
    """One row per MATERIALIZED VIEW refresh attempt. Cron job + freshness probe consumer.

    Global table (no tenant_id) — refresh state is operational infra, not tenant data.
    Allowlist exception in tenant-isolation arch test documented at impl time.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    mv_name: str = Field(..., min_length=1, max_length=64)         # 'mv_daily_llm_cost_per_tenant_v2', etc.
    refreshed_at: dt.datetime                                      # UTC. server_default NOW()
    refresh_duration_ms: int | None = Field(default=None, ge=0)
    rows_affected: int | None = Field(default=None, ge=0)
    status: RefreshStatus = "ok"
```

## 2. SQLAlchemy 2.0 models

Todas en `backend/src/shared/billing/infrastructure/models/` y `shared/compliance/infrastructure/models/`. **`mapped_column()` SQLA 2.0**, table prefix por capability (`plan_config`, `tenant_subscription`, `channel_blacklist`).

### 2.1 plan_config

```python
# shared/billing/infrastructure/models/plan_config_model.py
from __future__ import annotations
import datetime as dt
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, Boolean, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base

class PlanConfigModel(Base):
    __tablename__ = "plan_config"

    plan_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_budget_total_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sales_agent_reserved_pct: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=Decimal("0.50"))
    max_outbound_msg_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_campaigns_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_segment_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_contacts_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # PM Q6
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("llm_budget_total_usd > 0", name="ck_plan_config_budget_positive"),
        CheckConstraint("sales_agent_reserved_pct >= 0 AND sales_agent_reserved_pct <= 1", name="ck_plan_config_sa_pct_range"),
        CheckConstraint("max_outbound_msg_per_day IS NULL OR max_outbound_msg_per_day >= 0", name="ck_plan_config_outbound_nonneg"),
        # NOTE: partial unique index `uq_plan_config_one_default` (is_default WHERE is_default=TRUE)
        # created via raw SQL in migration (SQLA 2.0 doesn't surface partial UNIQUE cleanly here).
    )
```

**PM Q6 invariant (exactly-one-default)**:
- Partial unique index in DB: `CREATE UNIQUE INDEX uq_plan_config_one_default ON plan_config (is_default) WHERE is_default = TRUE`.
- Streamlit admin toggle MUST be atomic transaction: `UPDATE plan_config SET is_default = FALSE WHERE is_default = TRUE; UPDATE plan_config SET is_default = TRUE WHERE plan_id = :new_default;` wrapped in `BEGIN/COMMIT`.
- Seed: row `plan_id='free'` ships with `is_default=TRUE`; others FALSE.
- Fallback chain runtime: `PlanService.get_default_plan()` queries `WHERE is_default=TRUE LIMIT 1` (cached 5min); if DB unavailable → `Settings.BILLING_DEFAULT_PLAN_ID` env var (default `"free"`); fail-fast if neither resolves on first hit.

**Note**: `plan_config` is a **global catalog** (no `tenant_id`). Allowed exception en `tenant-isolation.md` — PR-2 documenta en migration comment + `test_outbox_invariants.py` ya existente arch test no aplica (mira `*_llm_call`/`*_trace_event` patterns). Si el ratchet `test_tenant_isolation.py` existe, agregar `plan_config` a allowlist con justificación.

### 2.2 tenant_subscription

```python
# shared/billing/infrastructure/models/tenant_subscription_model.py
from __future__ import annotations
import datetime as dt
from uuid import UUID
from sqlalchemy import String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base

class TenantSubscriptionModel(Base):
    __tablename__ = "tenant_subscription"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(32), ForeignKey("plan_config.plan_id"), nullable=False)
    cycle_anchor_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    custom_overrides: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    trial_ends_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("cycle_anchor_day BETWEEN 1 AND 28", name="ck_tenant_subscription_anchor_range"),
        Index("ix_tenant_subscription_plan_id", "plan_id"),
        Index("ix_tenant_subscription_active", "tenant_id", postgresql_where="deleted_at IS NULL"),
    )
```

### 2.3 channel_blacklist

```python
# shared/compliance/infrastructure/models/channel_blacklist_model.py
from __future__ import annotations
import datetime as dt
import uuid as uuid_mod
from uuid import UUID
from sqlalchemy import String, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base

class ChannelBlacklistModel(Base):
    __tablename__ = "channel_blacklist"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "identifier", name="uq_channel_blacklist_tenant_channel_identifier"),
        Index("ix_channel_blacklist_lookup", "tenant_id", "channel", "identifier", postgresql_where="deleted_at IS NULL"),
    )
```

### 2.4 lead_opt_ins (PM Q2 — production-grade opt-in tracking)

```python
# shared/compliance/infrastructure/models/lead_opt_in_model.py
from __future__ import annotations
import datetime as dt
import uuid as uuid_mod
from uuid import UUID
from sqlalchemy import String, DateTime, UniqueConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base

class LeadOptInModel(Base):
    __tablename__ = "lead_opt_ins"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    opted_in_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opted_out_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False)   # webhook | manual | imported | inferred_message
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "lead_id", "channel", name="uq_lead_opt_ins_tenant_lead_channel"),
        Index("ix_lead_opt_ins_lookup", "tenant_id", "lead_id", "channel", "opted_in_at", "opted_out_at"),
    )
```

**Source enum semantics**:
- `webhook` — explicit consent from channel webhook (Meta/IG/Telegram opt-in event).
- `manual` — admin tagged via Streamlit / API.
- `imported` — CSV upload bulk import.
- `inferred_message` — backfill / one-shot heuristic from `messages.role='user'`. Lower trust, marked for audit.

### 2.5 mv_refresh_log (PM Q4 — exact MV freshness signal)

```python
# shared/billing/infrastructure/models/mv_refresh_log_model.py
from __future__ import annotations
import datetime as dt
import uuid as uuid_mod
from uuid import UUID
from sqlalchemy import String, Integer, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base

class MVRefreshLogModel(Base):
    """Global infra table (NO tenant_id). Documented allowlist exception in tenant-isolation arch test."""
    __tablename__ = "mv_refresh_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    mv_name: Mapped[str] = mapped_column(String(64), nullable=False)
    refreshed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    refresh_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rows_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")

    __table_args__ = (
        CheckConstraint("status IN ('ok', 'error', 'skipped')", name="ck_mv_refresh_log_status_enum"),
        Index("ix_mv_refresh_log_mv_name_recent", "mv_name", "refreshed_at"),  # DESC sort handled by query
    )
```

**Retention**: 90 days. Cron weekly: `DELETE FROM mv_refresh_log WHERE refreshed_at < NOW() - INTERVAL '90 days'`. Builder agrega ARQ task `mv_refresh_log_retention_task` siguiendo patrón existente `aggregate_refresh_task`.

### 2.6 leads.country ALTER (PM Q3 — country-block primary signal)

```python
# Migration adds nullable column. NO change to LeadModel domain entity beyond field add.
# Existing model lives in src/shared/infrastructure/models/crm.py (LeadModel) — just append:
#
#   country: Mapped[str | None] = mapped_column(String(2), nullable=True)
#
# ISO 3166-1 alpha-2 (e.g. "PE", "MX", "US"). Index for country-block lookups.
```

**Migration ALTER** (idempotent raw SQL):
```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS country VARCHAR(2);
CREATE INDEX IF NOT EXISTS ix_leads_country ON leads (tenant_id, country) WHERE country IS NOT NULL;
```

**Fallback chain** (`CountryBlockPolicy._resolve_country`): `lead.country` (preferred, explicit) → phone E.164 prefix lookup (heuristic, whatsapp/telegram only) → `None` (unknown — allowed by default per policy semantics).

## 3. Pydantic v2 DTOs

PR-2 **no expone API HTTP nuevos** (la única superficie es Streamlit + servicios DI). Pydantic VOs definidos en §1 cubren contratos in-memory. **No hay `response_model=`** porque no hay rutas HTTP nuevas. Si en S2 wire surgen endpoints (e.g. `GET /api/v1/billing/quota`), agregar DTOs allí.

## 4. API routes

**Ninguna ruta HTTP nueva en PR-2.** Los servicios se consumen via DI desde:
- (S2) copilot orchestrator pre-LLM-call → `BudgetGuard.check`
- (S2) sales_agent specialists → idem
- (S2) ChannelRouter → `ComplianceService.check`, `OutboundRateLimiter.check`
- (PR-2) Streamlit admin → `PlanService` + `TenantSubscriptionRepository` (sync session local Streamlit)

`X-Tenant-ID` no aplica directamente (no hay HTTP). Los servicios reciben `tenant_id: UUID` como parámetro required.

## 5. TypeScript types

**N/A** — PR-2 sin frontend Next.js. Streamlit es Python end-to-end.

## 6. Repository interfaces (ABC, async)

Todos en `shared/billing/infrastructure/` y `shared/compliance/infrastructure/`. `tenant_id` required en queries scoped (excepto `plan_config` que es global). Async-first.

```python
# shared/billing/domain/plan_repository.py (port)
from abc import ABC, abstractmethod
from src.shared.billing.domain.plan import PlanConfig

class PlanRepository(ABC):
    @abstractmethod
    async def get_by_id(self, plan_id: str) -> PlanConfig | None: ...

    @abstractmethod
    async def list_active(self) -> list[PlanConfig]: ...

    @abstractmethod
    async def upsert(self, plan: PlanConfig) -> PlanConfig: ...
```

```python
# shared/billing/domain/subscription_repository.py (port)
from abc import ABC, abstractmethod
from uuid import UUID
from src.shared.billing.domain.subscription import TenantSubscription

class TenantSubscriptionRepository(ABC):
    @abstractmethod
    async def get_by_tenant_id(self, tenant_id: UUID) -> TenantSubscription | None: ...

    @abstractmethod
    async def upsert(self, sub: TenantSubscription) -> TenantSubscription: ...

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID) -> None: ...
```

```python
# shared/compliance/domain/blacklist_repository.py (port)
from abc import ABC, abstractmethod
from uuid import UUID
from src.shared.compliance.domain.blacklist_entry import ChannelBlacklistEntry

class ChannelBlacklistRepository(ABC):
    @abstractmethod
    async def is_blacklisted(self, tenant_id: UUID, channel: str, identifier: str) -> bool: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID, channel: str | None = None) -> list[ChannelBlacklistEntry]: ...

    @abstractmethod
    async def upsert(self, entry: ChannelBlacklistEntry) -> ChannelBlacklistEntry: ...

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID, entry_id: UUID) -> None: ...
```

```python
# shared/compliance/domain/opt_in_repository.py (port)
from abc import ABC, abstractmethod
from uuid import UUID
from src.shared.compliance.domain.lead_opt_in import LeadOptIn, OptInSource

class OptInRepository(ABC):
    """DB-backed port (PM Q2 — no longer stub). Reads `lead_opt_ins` table.

    Tenant-scoped: every method receives `tenant_id` (mandatory, including get_by_id).
    Soft-delete N/A — opt-out is tracked via `opted_out_at` timestamp (not deleted_at).
    """

    @abstractmethod
    async def has_active_opt_in(self, tenant_id: UUID, lead_id: UUID, channel: str) -> bool:
        """Returns True iff exists row with opted_in_at NOT NULL AND opted_out_at IS NULL."""
        ...

    @abstractmethod
    async def get(self, tenant_id: UUID, lead_id: UUID, channel: str) -> LeadOptIn | None: ...

    @abstractmethod
    async def upsert(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        opted_in_at: "dt.datetime | None",
        opted_out_at: "dt.datetime | None",
        source: OptInSource,
        evidence: dict,
    ) -> LeadOptIn:
        """ON CONFLICT (tenant_id, lead_id, channel) DO UPDATE SET ... — idempotent."""
        ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: UUID, channel: str | None = None, active_only: bool = True
    ) -> list[LeadOptIn]: ...
```

```python
# shared/billing/domain/mv_refresh_log_repository.py (port — PM Q4)
from abc import ABC, abstractmethod
import datetime as dt
from src.shared.billing.domain.mv_refresh_log import MVRefreshLog, RefreshStatus

class MVRefreshLogRepository(ABC):
    """Global table — NO tenant_id (operational infra)."""

    @abstractmethod
    async def record_refresh(
        self,
        mv_name: str,
        refresh_duration_ms: int | None,
        rows_affected: int | None,
        status: RefreshStatus,
    ) -> MVRefreshLog: ...

    @abstractmethod
    async def get_last_refresh(self, mv_name: str) -> MVRefreshLog | None:
        """ORDER BY refreshed_at DESC LIMIT 1 — used by BudgetGuard freshness probe."""
        ...

    @abstractmethod
    async def delete_older_than(self, cutoff: dt.datetime) -> int:
        """Retention worker (90d). Returns rows deleted."""
        ...
```

## 7. Application services

### 7.1 PlanService.get_effective + get_default_plan + cache invalidation pub/sub (PM Q5 + Q6)

```python
# shared/billing/application/plan_service.py
from __future__ import annotations
from decimal import Decimal
from uuid import UUID
import asyncio
import structlog
from src.shared.billing.domain.plan import PlanConfig
from src.shared.billing.domain.plan_repository import PlanRepository
from src.shared.billing.domain.subscription_repository import TenantSubscriptionRepository

logger = structlog.get_logger(__name__)

# PM Q5: cross-instance cache invalidation via Redis pub/sub. Multi-pod ready.
CACHE_INVALIDATE_PLAN_CONFIG_CHANNEL = "cache_invalidate:plan_config"
CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX = "cache_invalidate:tenant_subscription"  # :{tenant_id}
DEFAULT_PLAN_CACHE_TTL_SECONDS = 300  # 5min fallback when Redis pub/sub unavailable

class PlanService:
    """Resolve effective plan (catalog row + custom_overrides + legacy fallback).

    Cache strategy (PM Q5 — multi-pod ready):
    - In-memory `lru_cache`/`TTLCache` per pod, 5min TTL.
    - Cross-instance invalidation via Redis pub/sub channels:
        - `cache_invalidate:plan_config` — global (any plan_config row mutated).
        - `cache_invalidate:tenant_subscription:{tenant_id}` — per-tenant subscription mutated.
    - Subscriber background task starts with app startup (`subscribe_cache_invalidations`).
    - Soft-fail: Redis unavailable → log warning + 5min TTL is the eventual consistency
      ceiling (acceptable per PM decision: "best-effort eventual consistency").

    PM Q6: `get_default_plan` resolves via `is_default=TRUE` partial unique index.
    Fallback chain: DB → env var `BILLING_DEFAULT_PLAN_ID` → fail-fast if plan_id absent in catalog.
    """

    DEFAULT_PLAN_ID_ENV = "BILLING_DEFAULT_PLAN_ID"   # Settings field, default 'free'

    def __init__(
        self,
        plan_repo: PlanRepository,
        subscription_repo: TenantSubscriptionRepository,
        legacy_billing_repo: "TenantBillingConfigRepository",
        redis_client,
        cache_ttl_seconds: int = DEFAULT_PLAN_CACHE_TTL_SECONDS,
    ) -> None:
        self._plan_repo = plan_repo
        self._sub_repo = subscription_repo
        self._legacy_repo = legacy_billing_repo
        self._redis = redis_client
        self._cache_ttl = cache_ttl_seconds
        # Per-tenant effective-plan cache. Key=tenant_id; Value=(PlanConfig, expires_at_unix).
        self._tenant_cache: dict[UUID, tuple[PlanConfig, float]] = {}
        # Default plan cache: single slot. Key='_default'; Value=(PlanConfig, expires_at_unix).
        self._default_cache: tuple[PlanConfig, float] | None = None
        self._subscriber_task: asyncio.Task | None = None

    async def get_effective(self, tenant_id: UUID) -> PlanConfig:
        """Return effective plan: subscription.plan + custom_overrides merged.

        Resolution chain:
        1. Cache hit (TTL) → return.
        2. `tenant_subscription` exists → `plan_config` row + `custom_overrides` JSONB merge → cache → return.
        3. `tenant_subscription` IS NULL but `tenant_billing_config` (legacy) exists →
           translate to in-memory PlanConfig (no DB write), use default plan as base
           + apply legacy `flat_fee_amount` / `cost_alert_threshold_usd` to overrides.
        4. Neither exists → fallback to `get_default_plan()`.

        Logs `billing_plan_fallback` event when path 3 or 4 used (visibility for S2 cutover).
        """
        ...

    async def get_default_plan(self) -> PlanConfig:
        """PM Q6: resolve default plan.

        1. Cache hit (5min TTL) → return.
        2. Query `SELECT * FROM plan_config WHERE is_default = TRUE LIMIT 1` (partial unique idx).
        3. If not found → fallback Settings.BILLING_DEFAULT_PLAN_ID env var → re-query by plan_id.
        4. If still not found → raise `BillingDefaultPlanMissingError` (fail-fast on first hit).
        """
        ...

    async def update_plan(self, plan: PlanConfig) -> PlanConfig:
        """Streamlit admin save path. Atomic when toggling is_default (PM Q6 invariant).

        If plan.is_default == True:
            BEGIN;
              UPDATE plan_config SET is_default = FALSE WHERE is_default = TRUE;
              UPDATE plan_config SET ... is_default = TRUE WHERE plan_id = :plan_id;
            COMMIT;

        Then: Redis PUBLISH `cache_invalidate:plan_config` (no payload — full bust).
        Soft-fail: Redis unavailable → structlog.warn, rely on TTL.
        """
        ...

    async def update_subscription(self, tenant_id: UUID, ...) -> None:
        """Streamlit admin save tenant_subscription. Publishes per-tenant invalidation."""
        # ... DB write ...
        try:
            await self._redis.publish(
                f"{CACHE_INVALIDATE_TENANT_SUBSCRIPTION_CHANNEL_PREFIX}:{tenant_id}",
                "",
            )
        except Exception as exc:  # noqa: BLE001 — soft-fail per Q5
            logger.warning(
                "plan_service_invalidate_publish_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )

    async def invalidate_cache(self, tenant_id: UUID) -> None:
        """Local cache eviction. Called by subscriber on incoming pub/sub event."""
        self._tenant_cache.pop(tenant_id, None)

    async def invalidate_default_cache(self) -> None:
        """Local default-plan cache eviction. Called by subscriber on plan_config pub/sub event."""
        self._default_cache = None
        # Optionally bust all tenant caches if `is_default` change can affect fallback path
        self._tenant_cache.clear()

    async def subscribe_cache_invalidations(self) -> None:
        """Background task started at app startup. Consumes Redis pub/sub channels.

        Subscribes to:
            - `cache_invalidate:plan_config` → invalidate_default_cache + clear tenant_cache.
            - `cache_invalidate:tenant_subscription:*` → per-tenant invalidate_cache.

        Soft-fail: if Redis disconnects, retries with backoff. structlog.warn each retry.
        Cancellation handled via `CancelledError` on app shutdown.
        """
        ...
```

**Redis pub/sub semantics (PM Q5)**:

| Trigger | Channel | Subscriber action |
|---|---|---|
| Streamlit admin updates a `plan_config` row (price / outbound cap / is_default toggle) | `cache_invalidate:plan_config` | All pods clear `_default_cache` + clear all `_tenant_cache` (default may flow to fallback path) |
| Streamlit admin updates `tenant_subscription` row (plan change / custom_overrides) | `cache_invalidate:tenant_subscription:{tenant_id}` | All pods evict that tenant's cache entry |
| Redis unavailable | (publish soft-fail logged) | Local TTL (5min) bounds eventual-consistency window |

**Cache backend choice**: `cachetools.TTLCache(maxsize=4096, ttl=300)` for `_tenant_cache`. 4096 capacity safely covers projected tenant count for next 12 months (cost: ~10MB RAM). Default-plan cache is a single slot.

### 7.2 BudgetGuard.check

```python
# shared/billing/application/budget_guard.py
from __future__ import annotations
from decimal import Decimal
from uuid import UUID
import datetime as dt
import structlog
from src.shared.billing.domain.budget_decision import BudgetDecision
from src.shared.billing.application.plan_service import PlanService

logger = structlog.get_logger(__name__)

# Reads from `mv_daily_llm_cost_per_tenant_v2` (existing MV from migration 079).
# Schema: (agent_kind, tenant_id, occurred_on, call_count, turn_count, cost_usd, cost_tenant_currency, tenant_currency, error_count).
# Agent kinds today: 'copilot', 'sales_agent', 'campaign' (registered PR-1 Sub-C).
# MV refresh: hourly via aggregate_refresh_task (CONCURRENTLY) — INSERTs row to `mv_refresh_log` post-refresh (PM Q4).
# When MV stale > 1h (per `mv_refresh_log` last entry) → graceful degradation soft cap @ 105% (D11).
MV_STALENESS_TOLERANCE_SECONDS = 3600
SOFT_CAP_OVER_FACTOR = Decimal("1.05")
SOFT_WARN_PCT = Decimal("0.80")
MV_NAME = "mv_daily_llm_cost_per_tenant_v2"

class BudgetGuard:
    """Gate proactivo pre-LLM-call. Reservación 50% sales_agent invariant ENFORCED."""

    def __init__(
        self,
        plan_service: PlanService,
        cycle_service: "BillingCycleService",   # existing shared/agent_observability/reporting
        cost_aggregator: "CrossAgentCostAggregator",  # existing shared/agent_observability/reporting/cost_aggregator
        mv_refresh_log_repo: "MVRefreshLogRepository",  # PM Q4: dedicated freshness signal
        decision_cache_ttl_seconds: int = 300,
    ) -> None:
        self._plan_service = plan_service
        self._cycle_service = cycle_service
        self._cost_aggregator = cost_aggregator
        self._mv_refresh_log_repo = mv_refresh_log_repo
        self._cache: dict[tuple[UUID, str], tuple[BudgetDecision, float]] = {}
        self._cache_ttl = decision_cache_ttl_seconds

    async def _is_mv_stale(self) -> bool:
        """PM Q4: query `mv_refresh_log` for last refresh timestamp of `MV_NAME`.

        Returns True if last_refresh older than MV_STALENESS_TOLERANCE_SECONDS or absent.
        Soft-fail: if query errors → log warning + return True (assume stale, apply soft cap).
        """
        try:
            last = await self._mv_refresh_log_repo.get_last_refresh(MV_NAME)
        except Exception as exc:  # noqa: BLE001
            logger.warning("budget_guard_mv_freshness_probe_failed", error=str(exc))
            return True
        if last is None or last.status != "ok":
            return True
        age_seconds = (dt.datetime.now(dt.timezone.utc) - last.refreshed_at).total_seconds()
        return age_seconds > MV_STALENESS_TOLERANCE_SECONDS

    async def check(
        self,
        tenant_id: UUID,
        agent_kind: str,            # "sales_agent" | "copilot" | "campaign" | future
        estimated_cost_usd: Decimal,
    ) -> BudgetDecision:
        """Decide if this LLM call can proceed.

        Logic (in order):

        1. Resolve effective plan (cached). Compute SA pool / Others pool.
        2. Determine bucket: agent_kind == 'sales_agent' → SA pool; else → Others pool.
           **INVARIANT**: copilot exhausto NO consume SA pool aunque SA tenga budget.
           Hard separation by bucket assignment. Test arch property-based enforce.
        3. Cache hit (5min) → return cached BudgetDecision.
        4. Probe MV freshness:
            a. Fresh (< 1h ago) → query `mv_daily_llm_cost_per_tenant_v2` summed over current cycle.
            b. Stale (≥ 1h ago) → log warning + apply SOFT_CAP_OVER_FACTOR (1.05) on cap.
               Reason: MV behind = no real-time signal. Better admit 5% overrun than block sales.
        5. Compute new_total = spent + estimated_cost_usd.
        6. Decide:
            - new_total >= effective_cap → BudgetDecision(allowed=False, reason='cycle_budget_exhausted').
            - new_total >= cap * 0.80 → BudgetDecision(allowed=True, soft_warn=True).
            - else → BudgetDecision(allowed=True).
        7. Cache the decision (key = tenant_id + agent_kind, TTL 5min).

        Returns
        -------
        BudgetDecision with `pool` reflecting which bucket was consulted, `spent_usd`/`cap_usd`
        for trace correlation, and `decision_id` for downstream alert correlation.

        Notes
        -----
        - Best-effort: if MV query fails → log error + return `allowed=True` (fail-open).
          Rationale: blocking ALL agents because MV is unreachable would halt product.
          Trade-off accepted explicitly per `tessl__graceful-degradation`.
        - tenant_id MANDATORY (no `get_by_id` shortcut).
        """
```

**Reservación invariant (architectural enforcement):**

| Escenario | sales_agent call | copilot call |
|---|---|---|
| SA pool 50% libre, Others pool 0% libre | ✅ allowed (SA bucket) | ❌ blocked (Others bucket exhausted) |
| SA pool 0% libre, Others pool 50% libre | ❌ blocked (SA bucket exhausted) | ✅ allowed (Others bucket) |

`test_budget_reservation_invariant.py` (Hypothesis property-based): genera N planes × N spend distributions × ambos agent_kinds, verifica que copilot **nunca** retorna `allowed=True` cuando `spent_others >= cap_others` aunque `spent_sa < cap_sa`. Y vice versa.

### 7.3 OutboundRateLimiter.check

```python
# shared/billing/application/rate_limiter.py
from __future__ import annotations
from uuid import UUID
import time
import structlog
from src.shared.billing.application.plan_service import PlanService

logger = structlog.get_logger(__name__)

class OutboundRateLimiter:
    """Sliding window Redis. Antispam complementario a BudgetGuard."""

    KEY_TEMPLATE = "rate_limit:outbound:{tenant_id}"
    DEFAULT_WINDOW_SECONDS = 86400   # 24h. Configurable post-MVP via plan feature flag.

    def __init__(self, redis_client, plan_service: PlanService) -> None:
        self._redis = redis_client
        self._plan_service = plan_service

    async def check(self, tenant_id: UUID) -> bool:
        """Return True if outbound msg allowed. Increments counter on True.

        Implementation (atomic via Redis pipeline):
        1. plan = await plan_service.get_effective(tenant_id).
        2. If plan.max_outbound_msg_per_day IS NULL → return True (unlimited subject to budget).
        3. Sliding window:
            now = time.time()
            cutoff = now - WINDOW_SECONDS
            ZREMRANGEBYSCORE key 0 cutoff      # purge old entries
            ZCARD key                          # current count
            if count < limit:
                ZADD key now uuid4            # member must be unique (uuid for idempotency on retry)
                EXPIRE key WINDOW_SECONDS
                return True
            else:
                return False
        4. Soft-fail: if Redis unavailable → log warning + return True (per tessl__graceful-degradation).
           Rationale: blocking outbound on Redis outage = product halt; budget cap still gates LLM cost.
        """
```

### 7.4 ComplianceService.check

```python
# shared/compliance/application/compliance_service.py
from __future__ import annotations
from typing import Protocol
from uuid import UUID
import structlog
from src.shared.compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)

class CompliancePolicy(Protocol):
    """Each policy returns CheckResult. Service short-circuits on first allowed=False."""
    name: str
    async def evaluate(self, *, tenant_id: UUID, lead_id: UUID, channel: str, identifier: str, campaign_id: UUID | None) -> CheckResult: ...

class ComplianceService:
    """Policy chain orchestrator. Order: WABA24h → OptIn → Blacklist → CountryBlock.

    Short-circuits on first FAIL. Structured logging at each step for audit trail.
    Sub-100ms p95 target (Redis-cached lookups + indexed queries).
    """

    def __init__(self, policies: list[CompliancePolicy]) -> None:
        self._policies = policies   # ordered list; injection composition root decides order

    async def check(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Run policy chain. Return first FAIL or final PASS."""
        for policy in self._policies:
            result = await policy.evaluate(
                tenant_id=tenant_id, lead_id=lead_id, channel=channel,
                identifier=identifier, campaign_id=campaign_id,
            )
            if not result.allowed:
                logger.info(
                    "compliance_check_failed",
                    tenant_id=str(tenant_id), policy=policy.name,
                    failed_policy=result.failed_policy, reason=result.reason,
                )
                return result
        return CheckResult(allowed=True)
```

**Policy implementations** (en `shared/compliance/domain/policies/`):

| Policy | Trigger condition | Evidence captured |
|---|---|---|
| `WABA24hPolicy` | `channel == "whatsapp"` only. Query `messages` WHERE `user_id == lead_id AND tenant_id == tenant_id AND role == 'user' AND created_at > now() - INTERVAL '24h'` (existing schema). PASS if last inbound user msg < 24h ago. Outside window + sin template_id en campaign metadata → FAIL `failed_policy='waba_24h'`. | `last_inbound_at`, `hours_since_inbound` |
| `OptInPolicy` | All channels. **PM Q2 production-grade**: PASS iff `lead_opt_ins` row exists with `opted_in_at NOT NULL AND opted_out_at IS NULL` for `(tenant_id, lead_id, channel)`. FAIL otherwise. Migration backfills from `messages.role='user'` (last 30d) with `source='inferred_message'` — those rows lower trust but unblock day-1 production traffic. | `opt_in_source`, `opt_in_id`, `opted_in_at` |
| `BlacklistPolicy` | All channels. Query `channel_blacklist` WHERE `tenant_id == tenant_id AND channel == channel AND identifier == normalized(identifier) AND deleted_at IS NULL`. FAIL si match. | `blacklist_entry_id`, `reason` |
| `CountryBlockPolicy` | All channels. **PM Q3 production-grade**: resolves country via fallback chain `lead.country` (preferred — explicit ISO 3166-1 alpha-2) → phone E.164 prefix lookup (heuristic, whatsapp/telegram only) → `None` (allowed by default). Reads env `COMPLIANCE_DEFAULT_COUNTRY_BLOCK_LIST` (CSV alpha-2; default `""` empty). FAIL if resolved country in blocklist. **PR-2 lista vacía default** → effectively no-op until Chris activates (e.g. `"CU,IR,KP,SY"`). | `country_iso`, `country_source` (`lead_field` \| `phone_prefix` \| `unknown`), `block_list_source` |

**Evidence schema**: cada policy retorna evidence JSONB. Campaign auditor en S2 persiste `compliance_check_log` (no en PR-2). PR-2 solo retorna in-memory `CheckResult`.

## 8. Agentic surfaces

**N/A** — PR-2 no toca LangGraph/StateGraph/tools/prompts. Es infra capa primitivas. Wire a copilot/sales_agent agentic graphs ocurre en S2.

**Trace event invariants preserved**:
- `copilot_trace_event` schema sin cambios. PR-2 NO escribe trazas (servicios stateless).
- `mv_daily_llm_cost_per_tenant_v2` schema preservado (BudgetGuard solo SELECT, no DDL).
- `agent_kind="campaign"` registry (PR-1 Sub-C) intacto. `BudgetGuard.check(agent_kind="campaign")` rutea al **Others bucket** (no es sales_agent).

**Pricing invariants** (consultados con `copilot-expert` + `sales-agent-expert`):
- `model_pricing_snapshot` schema sin cambios. PR-2 NO modifica `pricing/resolver.py` ni LiteLLM sync.
- Tier pricing >200k tokens (Kimi K2.6, sales-agent-expert §3) **fuera de PR-2 scope**. Si `estimated_cost_usd` viene tier-aware (caller lo computa) → BudgetGuard solo agrega; no recomputa tiers.
- Cache prefix slot 5 BRAND_VOICE (sales_agent SSoT) **no afectado** — BudgetGuard lee cycle spend agregado, no per-call breakdown.

## 9. Migration notes

`backend/alembic/versions/110_add_billing_and_compliance.py`. Idempotent raw SQL `IF NOT EXISTS`. Down migration drops tables/indexes `IF EXISTS`. **Dependencies head**: derive from `make alembic-current` post-PR-1 merge (083+084+085). Architect propone `down_revision = "085_copilot_tenant_limits"` — **builder verifica head al implementar** (parallel sessions PI-2/PI-4 podrían adelantar; merge head si conflict).

```python
"""PR-2: billing primitives + compliance production-grade (post PM decisions Q1-Q10).

Adds:
  - plan_config (5 rows seed) + is_default partial unique index (PM Q6)
  - tenant_subscription (1:1 tenant ↔ plan, custom_overrides JSONB)
  - channel_blacklist (tenant + channel + identifier, soft delete)
  - lead_opt_ins (PM Q2 — explicit per-channel consent audit trail)
  - mv_refresh_log (PM Q4 — exact MV freshness signal, 90d retention)
  - leads.country column (PM Q3 — primary signal for CountryBlockPolicy)

Compat: tenant_billing_config legacy NOT touched. PlanService.get_effective
falls back to legacy when tenant_subscription IS NULL (S2 migrates data).

Idempotent: every CREATE / ALTER / INSERT uses IF NOT EXISTS / ON CONFLICT.
Re-running upgrade() is a no-op.
"""

revision = "110_add_billing_and_compliance"
down_revision = "085_copilot_tenant_limits"  # PM Q9: builder runs `make alembic-current` pre-implement
                                             # and merges head if conflict (Alembic merge-heads pattern)

def upgrade() -> None:
    # 1. plan_config (catalog) — PM Q6: is_default field + partial unique idx
    op.execute("""
        CREATE TABLE IF NOT EXISTS plan_config (
            plan_id VARCHAR(32) PRIMARY KEY,
            display_name VARCHAR(64) NOT NULL,
            llm_budget_total_usd NUMERIC(10,2) NOT NULL,
            sales_agent_reserved_pct NUMERIC(4,3) NOT NULL DEFAULT 0.50,
            max_outbound_msg_per_day INTEGER,
            max_campaigns_active INTEGER,
            max_segment_size INTEGER,
            max_contacts_total INTEGER,
            features JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_plan_config_budget_positive CHECK (llm_budget_total_usd > 0),
            CONSTRAINT ck_plan_config_sa_pct_range CHECK (sales_agent_reserved_pct >= 0 AND sales_agent_reserved_pct <= 1),
            CONSTRAINT ck_plan_config_outbound_nonneg CHECK (max_outbound_msg_per_day IS NULL OR max_outbound_msg_per_day >= 0)
        )
    """)
    # PM Q6: ALTER for re-runs (table existed without is_default in prior migration drafts).
    op.execute("ALTER TABLE plan_config ADD COLUMN IF NOT EXISTS is_default BOOLEAN NOT NULL DEFAULT FALSE")
    # PM Q6: partial unique index — exactly 1 row with is_default=TRUE.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_config_one_default
        ON plan_config (is_default) WHERE is_default = TRUE
    """)

    # 2. Seed 5 planes (idempotente). Numeric values **only here** (test_no_hardcoded_plan_prices.py allowlist).
    # PM Q8: outbound caps editable post-deploy via Streamlit admin (1 UPDATE row, 0 migration).
    # PM Q6: 'free' ships as default (is_default=TRUE).
    op.execute("""
        INSERT INTO plan_config (plan_id, display_name, llm_budget_total_usd, sales_agent_reserved_pct, max_outbound_msg_per_day, max_campaigns_active, max_segment_size, max_contacts_total, is_default)
        VALUES
            ('free',         'Free',         5.00,  0.50,  100,   1,  100,   500,    TRUE),
            ('basic',        'Básico',       15.00, 0.50,  500,   3,  500,   2500,   FALSE),
            ('intermediate', 'Intermedio',   30.00, 0.50,  2000,  10, 2000,  10000,  FALSE),
            ('advanced',     'Avanzado',     45.00, 0.50,  5000,  25, 5000,  25000,  FALSE),
            ('ultra',        'Ultra',        95.00, 0.50,  20000, 100, 20000, 100000, FALSE)
        ON CONFLICT (plan_id) DO NOTHING
    """)

    # 3. tenant_subscription
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_subscription (
            tenant_id UUID PRIMARY KEY,
            plan_id VARCHAR(32) NOT NULL REFERENCES plan_config(plan_id),
            cycle_anchor_day INTEGER NOT NULL DEFAULT 1,
            custom_overrides JSONB NOT NULL DEFAULT '{}'::jsonb,
            trial_ends_at TIMESTAMPTZ,
            activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ,
            CONSTRAINT ck_tenant_subscription_anchor_range CHECK (cycle_anchor_day BETWEEN 1 AND 28)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_subscription_plan_id ON tenant_subscription (plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_subscription_active ON tenant_subscription (tenant_id) WHERE deleted_at IS NULL")

    # 4. channel_blacklist
    op.execute("""
        CREATE TABLE IF NOT EXISTS channel_blacklist (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            channel VARCHAR(32) NOT NULL,
            identifier VARCHAR(255) NOT NULL,
            reason VARCHAR(255),
            created_by_user_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        ALTER TABLE channel_blacklist
        ADD CONSTRAINT IF NOT EXISTS uq_channel_blacklist_tenant_channel_identifier
        UNIQUE (tenant_id, channel, identifier)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_channel_blacklist_lookup
        ON channel_blacklist (tenant_id, channel, identifier)
        WHERE deleted_at IS NULL
    """)

    # 5. lead_opt_ins (PM Q2 — production-grade per-channel consent audit trail)
    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_opt_ins (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL REFERENCES leads(id),
            channel VARCHAR(32) NOT NULL,
            opted_in_at TIMESTAMPTZ,
            opted_out_at TIMESTAMPTZ,
            source VARCHAR(24) NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        ALTER TABLE lead_opt_ins
        ADD CONSTRAINT IF NOT EXISTS uq_lead_opt_ins_tenant_lead_channel
        UNIQUE (tenant_id, lead_id, channel)
    """)
    op.execute("""
        ALTER TABLE lead_opt_ins
        ADD CONSTRAINT IF NOT EXISTS ck_lead_opt_ins_source_enum
        CHECK (source IN ('webhook', 'manual', 'imported', 'inferred_message'))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lead_opt_ins_lookup
        ON lead_opt_ins (tenant_id, lead_id, channel, opted_in_at, opted_out_at)
    """)

    # 5b. PM Q2: backfill from messages.role='user' last 30d (idempotent ON CONFLICT DO NOTHING).
    # One-shot; subsequent runs short-circuit because row already exists.
    # `messages` table schema reference: tenant_id + user_id (lead_id) + channel + role + created_at.
    op.execute("""
        INSERT INTO lead_opt_ins (id, tenant_id, lead_id, channel, opted_in_at, opted_out_at, source, evidence)
        SELECT DISTINCT ON (m.tenant_id, m.user_id, m.channel)
               gen_random_uuid(),
               m.tenant_id,
               m.user_id,
               m.channel,
               MIN(m.created_at) OVER (PARTITION BY m.tenant_id, m.user_id, m.channel),
               NULL,
               'inferred_message',
               jsonb_build_object('backfill_at', NOW(), 'lookback_days', 30)
        FROM messages m
        WHERE m.role = 'user'
          AND m.created_at >= NOW() - INTERVAL '30 days'
        ON CONFLICT (tenant_id, lead_id, channel) DO NOTHING
    """)

    # 6. mv_refresh_log (PM Q4 — exact freshness signal, 90d retention via cron)
    op.execute("""
        CREATE TABLE IF NOT EXISTS mv_refresh_log (
            id UUID PRIMARY KEY,
            mv_name VARCHAR(64) NOT NULL,
            refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            refresh_duration_ms INTEGER,
            rows_affected INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            CONSTRAINT ck_mv_refresh_log_status_enum CHECK (status IN ('ok', 'error', 'skipped'))
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mv_refresh_log_mv_name_recent
        ON mv_refresh_log (mv_name, refreshed_at)
    """)

    # 7. leads.country (PM Q3 — primary CountryBlockPolicy signal)
    op.execute("ALTER TABLE leads ADD COLUMN IF NOT EXISTS country VARCHAR(2)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_leads_country
        ON leads (tenant_id, country) WHERE country IS NOT NULL
    """)

    # NOTE: PR-2 does NOT seed tenant_subscription rows. Compat shim in PlanService.get_effective
    # falls back to default plan (PM Q6 is_default=TRUE row) when subscription is NULL.
    # S2 worker backfills existing tenants reading tenant_billing_config.

def downgrade() -> None:
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS country")
    op.execute("DROP TABLE IF EXISTS mv_refresh_log CASCADE")
    op.execute("DROP TABLE IF EXISTS lead_opt_ins CASCADE")
    op.execute("DROP TABLE IF EXISTS channel_blacklist CASCADE")
    op.execute("DROP TABLE IF EXISTS tenant_subscription CASCADE")
    op.execute("DROP TABLE IF EXISTS plan_config CASCADE")
```

**Prod-clone test command** (per `backend-migrations.md`):

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp 085_copilot_tenant_limits && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'  # 2nd run = no-op (idempotency)
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

## 10. File structure

**New files** (DDD layers):

```
backend/src/shared/billing/                                                  NEW
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── plan.py                              # PlanConfig VO (incl. is_default — Q6)
│   ├── subscription.py                      # TenantSubscription
│   ├── budget_decision.py                   # BudgetDecision
│   ├── mv_refresh_log.py                    # NEW Q4: MVRefreshLog VO
│   ├── plan_repository.py                   # PlanRepository ABC
│   ├── subscription_repository.py           # TenantSubscriptionRepository ABC
│   └── mv_refresh_log_repository.py         # NEW Q4: MVRefreshLogRepository ABC
├── infrastructure/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── plan_config_model.py             # incl. is_default + partial unique idx
│   │   ├── tenant_subscription_model.py
│   │   └── mv_refresh_log_model.py          # NEW Q4
│   ├── plan_repository_impl.py              # SQLAlchemy 2.0 async impl
│   ├── subscription_repository_impl.py
│   ├── mv_refresh_log_repository_impl.py    # NEW Q4
│   └── cache_invalidation_subscriber.py     # NEW Q5: Redis pub/sub subscriber bg task
└── application/
    ├── __init__.py
    ├── plan_service.py                      # incl. get_default_plan, update_plan, pub/sub publish
    ├── budget_guard.py                      # uses MVRefreshLogRepository (Q4)
    └── rate_limiter.py                      # OutboundRateLimiter

backend/src/shared/compliance/                                               NEW
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── check_result.py
│   ├── blacklist_entry.py
│   ├── blacklist_repository.py              # ABC
│   ├── lead_opt_in.py                       # NEW Q2: LeadOptIn VO + OptInSource enum
│   ├── opt_in_repository.py                 # ABC (DB-backed; no longer stub — Q2)
│   └── policies/
│       ├── __init__.py
│       ├── waba_24h_policy.py
│       ├── opt_in_policy.py                 # consumes OptInRepository (Q2 DB-backed)
│       ├── blacklist_policy.py
│       └── country_block_policy.py          # uses lead.country preferred (Q3)
├── infrastructure/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── channel_blacklist_model.py
│   │   └── lead_opt_in_model.py             # NEW Q2
│   ├── blacklist_repository_impl.py
│   └── opt_in_repository_impl.py            # SQLAlchemy 2.0 async impl (Q2)
└── application/
    ├── __init__.py
    └── compliance_service.py

backend/src/shared/infrastructure/models/crm.py                               MODIFIED  (LeadModel + country column — Q3)
backend/src/shared/billing/workers/                                           NEW
├── __init__.py
├── mv_refresh_recorder_task.py              # ARQ task: post mv refresh, INSERT mv_refresh_log row (Q4)
└── mv_refresh_log_retention_task.py         # ARQ weekly: DELETE older than 90d (Q4)

backend/src/admin/modules/billing.py                                          NEW   (Streamlit module — render_billing())
backend/src/admin/pages/planes-billing.py                                     NEW   (PageSpec wrapper, calls render_billing())
backend/src/admin/app.py                                                      MODIFIED (append PageSpec(slug='planes-billing', ...))

backend/alembic/versions/110_add_billing_and_compliance.py                    NEW
```

**Test files**:

```
backend/tests/shared/billing/
├── test_plan_config_vo.py                   # incl. is_default invariant (Q6)
├── test_plan_repository.py
├── test_subscription_repository.py
├── test_mv_refresh_log_repository.py        # NEW Q4
├── test_plan_service.py                     # incl. get_default_plan + pub/sub invalidation (Q5/Q6)
├── test_budget_guard.py                     # 10 cases (added _is_mv_stale via mv_refresh_log)
├── test_rate_limiter.py
└── test_cache_invalidation_subscriber.py    # NEW Q5: pub/sub subscriber background task

backend/tests/shared/compliance/
├── test_waba_24h_policy.py
├── test_opt_in_policy.py                    # DB-backed (Q2 — fixtures lead_opt_ins rows)
├── test_blacklist_policy.py
├── test_country_block_policy.py             # incl. lead.country preferred + phone fallback (Q3)
├── test_compliance_service.py               # policy chain orchestration
├── test_lead_opt_in_repository.py           # NEW Q2
└── test_lead_opt_ins_backfill.py            # NEW Q2: migration backfill from messages

backend/tests/architecture/
├── test_budget_reservation_invariant.py     # Hypothesis property-based
├── test_compliance_used_by_channels.py      # allowlist ratchet (empty initial; channel senders future require)
├── test_no_hardcoded_plan_prices.py         # grep 5\.00|15\.00|... outside migration seed
├── test_lead_opt_ins_invariants.py          # NEW Q2: tenant_id required, unique(tenant,lead,channel)
├── test_mv_refresh_log_freshness.py         # NEW Q4: BudgetGuard MUST consume mv_refresh_log (not pg_stat_user_tables)
└── test_plan_config_one_default.py          # NEW Q6: exactly-one-default partial unique idx exists in DB schema

backend/tests/admin/
└── test_billing_page_smoke.py               # Streamlit page loads + render_billing() exposed
```

**`KNOWN_STRUCTURE_EXCEPTIONS` impact** (`tests/architecture/test_folder_naming.py`): `shared/billing/` + `shared/compliance/` cumplen DDD layer naming (`domain/infrastructure/application/`) — no exception needed. Builder valida en RED.

## 11. Cross-cutting concerns

| Concern | Aplicación PR-2 |
|---|---|
| **Tenant isolation** | `tenant_subscription`, `channel_blacklist`: query siempre filtra `tenant_id`. Repos exigen `tenant_id` param required (incl. lookups). `plan_config` global catalog — exception documentada en migration comment + `test_outbox_invariants.py` no aplica (busca `*_llm_call/*_trace_event`). |
| **Currency** | `llm_budget_total_usd` — USD por design (Chris cobra en USD). DTOs **NO** incluyen `currency: str` field — el sufijo del nombre lo declara. Documentado en VO docstring. `test_no_hardcoded_plan_prices.py` enforza no leak `'USD'` literal. |
| **Master data** | `DateTime(timezone=True)` en todos columnas timestamp. `cycle_anchor_day` UTC. `trial_ends_at` UTC. Reusa `compute_cycle_start_py` (existente). NUNCA `datetime.utcnow()`. |
| **Spanish neutro LatAm** | Streamlit `display_name` planes en español neutro (`Free`, `Básico`, `Intermedio`, `Avanzado`, `Ultra`). Streamlit form labels + tooltips: español neutro tuteo (sin voseo). `.claude/rules/spanish-text.md` aplica. |
| **PII** | `channel_blacklist.identifier` puede contener phone/email. **NO endpoint API** expone field; solo Streamlit (admin-only). No `response_model=` requerido (sin HTTP). Si en S2 wire a `/api/v1/billing/blacklist`, el response_model debe mascarar identifier (e.g. `j***@example.com`). |
| **Native-first dev** | Builder usa `cd backend && .venv/bin/{ruff,pytest,mypy}` — NUNCA `docker exec`. Migration test prod-clone es la única excepción (Postgres only-in-Docker). |
| **Soft deletes** | `tenant_subscription.deleted_at`, `channel_blacklist.deleted_at`. `plan_config` no soft-delete porque catalog (5 rows fijas) — `is_active=False` reemplaza. |
| **Idempotency (PR-1)** | `IdempotencyStore` (PR-1) **NO consumido en PR-2** core services (BudgetGuard/ComplianceService/RateLimiter son read-mostly). **PM Q1 confirmed**: opt-in webhook HTTP handler difiere a S2 (PR-2 no introduce ruta HTTP nueva). Backfill SQL en migration es idempotent via `ON CONFLICT DO NOTHING`. |
| **Outbox (PR-1)** | PR-2 servicios NO emiten domain events. Streamlit admin save de `plan_config` o `tenant_subscription` invalida cache via Redis pub/sub directo (PM Q5) — sin outbox path porque la invalidación es best-effort eventual-consistency, no audit-critical. |
| **Graceful degradation** | BudgetGuard MV-stale (queried via `mv_refresh_log`, PM Q4) → soft cap 105%. Redis unavailable → RateLimiter fail-open + PlanService cache invalidation soft-fail (relies on TTL). Per `tessl__graceful-degradation`. Documentado en docstrings + tests. |
| **Cache invalidation (PM Q5)** | Cross-instance via Redis pub/sub. Channels: `cache_invalidate:plan_config` (catalog mutation) + `cache_invalidate:tenant_subscription:{tenant_id}` (per-tenant). Subscriber background task at app startup. Soft-fail to TTL (5min). Documented in §7.1 PlanService. |
| **PII evidence (Q2/Q3)** | `lead_opt_ins.evidence` JSONB MAY contain `webhook_event_id` / `message_id` — operational metadata, no raw PII. `leads.country` is ISO 3166-1 alpha-2 (NOT identifier-grade PII). No new `response_model=` masking required because PR-2 ships zero HTTP routes; S2 surfaces will gate via `response_model=` per pii-sanitisation tile. |

## 12. Architectural fitness impact

### Gates that run against this change

| Gate | File | Expected behavior |
|---|---|---|
| Folder naming | `tests/architecture/test_folder_naming.py` | `shared/billing/` + `shared/compliance/` cumplen `domain/infrastructure/application/` — sin exception nueva |
| Admin panel registry | `tests/architecture/test_admin_panel.py` | `pages/planes-billing.py` ↔ PageSpec(slug='planes-billing') match |
| DDD imports | `tests/architecture/test_no_cross_module_imports.py` (or equivalent) | `shared/billing` y `shared/compliance` solo importan `shared/`. No imports de `modules/*`. |
| Tenant isolation | existing arch tests | `tenant_subscription`, `channel_blacklist` repos filtran `tenant_id` siempre |
| Migration idempotency | clone DB test (manual cmd) | 2nd `alembic upgrade head` = no-op |

### NEW gates introduced by PR-2

1. **`test_budget_reservation_invariant.py`** — Hypothesis property-based:
   - Inputs: `PlanConfig` (random budget 1-200 USD, random `sa_pct` 0-1), `spent_sa` ∈ [0, 2*cap_sa], `spent_others` ∈ [0, 2*cap_others], `agent_kind` ∈ {sales_agent, copilot, campaign}.
   - Property: `BudgetGuard.check(agent_kind="copilot", ...)` retorna `allowed=False` siempre que `spent_others >= cap_others`, **independiente** de `spent_sa`.
   - Property: `BudgetGuard.check(agent_kind="sales_agent", ...)` retorna `allowed=False` siempre que `spent_sa >= cap_sa`, **independiente** de `spent_others`.
   - 200 examples min.

2. **`test_compliance_used_by_channels.py`** — allowlist ratchet shrink-only:
   - Initial allowlist **empty** (no channels yet). Lists `src/modules/*/infrastructure/channels/*sender*.py` y `*outbound*.py` y `*router*.py` (S2 onwards).
   - When new channel sender added → must call `ComplianceService.check` before send. Test fails until added or to allowlist.
   - PR-2 ships with empty allowlist — gate passes today, enforced from S2.

3. **`test_no_hardcoded_plan_prices.py`** — grep regex:
   - Forbidden: `(5|15|30|45|95)\.00` literal in `src/**/*.py` outside `alembic/versions/110_add_billing_and_compliance.py`.
   - Forbidden: `"free"|"basic"|"intermediate"|"advanced"|"ultra"` plan_id literals outside `shared/billing/` + Streamlit + migration.

4. **`test_lead_opt_ins_invariants.py`** (PM Q2) — schema invariants:
   - `lead_opt_ins.tenant_id` IS NOT NULL.
   - `UNIQUE (tenant_id, lead_id, channel)` constraint exists.
   - `source` CHECK constraint enumerates `webhook | manual | imported | inferred_message`.
   - Repo methods all receive `tenant_id` as first required positional arg (introspection of ABC signature).

5. **`test_mv_refresh_log_freshness.py`** (PM Q4) — BudgetGuard MUST consume the new table:
   - AST scan of `BudgetGuard._is_mv_stale` body → MUST reference `MVRefreshLogRepository` / `mv_refresh_log`.
   - MUST NOT reference `pg_stat_user_tables` (forbidden after Q4 decision).
   - `mv_refresh_recorder_task` MUST be registered in ARQ workers list.

6. **`test_plan_config_one_default.py`** (PM Q6) — partial unique idx invariant:
   - Migration upgrade leaves DB with `pg_indexes` row matching `uq_plan_config_one_default` AND `indexdef LIKE '%WHERE is_default = true%'`.
   - Seed produces exactly 1 row with `is_default=TRUE`.
   - `PlanService.update_plan` toggling `is_default` to TRUE on a non-default row must atomically demote prior default (transaction test).

### Allowlist shrinkage expected

- `test_tenant_isolation.py`: PR-2 adds `plan_config` and `mv_refresh_log` to allowlist (global catalogs / operational infra, not tenant-scoped data) with inline justification per row. **PM Q10 confirmed** — builder runtime adds allowlist with comment `"plan_config: global catalog, not tenant-scoped"` and `"mv_refresh_log: operational infra, not tenant-scoped"`. Allowlist shrinks-only afterwards.
- No other allowlists shrink in this PR.

## 13. pm-nico/current-state updates required

Post-merge updates (PM responsibility per `pm-nico-ssot.md`):

| File | Section to append |
|---|---|
| `current-state/iam.md` | "Capacidades actuales" → "Plan tiers + tenant_subscription editable via Streamlit admin (5 planes USD: Free $5 / Básico $15 / Intermedio $30 / Avanzado $45 / Ultra $95). Per-tenant `custom_overrides` JSONB. **`is_default` partial unique index — exactly 1 default plan, atomic toggle (PM Q6).** Compat shim a `tenant_billing_config` legacy (S2 migra)." |
| `current-state/copilot.md` | "Capacidades actuales" → "BudgetGuard API exposed in `shared/billing/`. Copilot LLM cost gated by `BudgetGuard.check(agent_kind='copilot', ...)` con Others pool (NO consume SA reserved). Wiring orchestrator pre-LLM-call diferido a S2. Skill `copilot-expert` actualizado con referencia budget gating." |
| `current-state/sales-agent.md` | "Capacidades actuales" → "BudgetGuard reservación 50% sales_agent invariant exposed via `shared/billing/`. SA LLM cost gated by `BudgetGuard.check(agent_kind='sales_agent', ...)` con SA pool reservado. Outbound mensajes gated by `OutboundRateLimiter.check(tenant_id)` con cap `plan_config.max_outbound_msg_per_day` (Free 100/Básico 500/Intermedio 2000/Avanzado 5000/Ultra 20000 msg/día — editable Streamlit). Wiring specialists a S2. Skill `sales-agent-expert` actualizado con referencia budget+outbound gating." |
| `current-state/campaigns.md` | "Capacidades actuales" → "ComplianceService API (WABA-24h + **OptInPolicy DB-backed via `lead_opt_ins` table — Q2** + blacklist + **CountryBlockPolicy con `lead.country` preferred — Q3**) + OutboundRateLimiter API exposed in `shared/`. Wiring ChannelRouter a S2. Hoy sin campaign sender real." |
| `current-state/crm.md` | "Capacidades actuales" → "**`leads.country` field (ISO 3166-1 alpha-2) added — Q3** primary signal para CountryBlockPolicy. Hoy column nullable + index parcial; UI editor diferido S2. Backend reads via SQL hoy." |
| `decisions.md` PI-1 | append D18-D27: D18 (`plan_config` USD-only, no currency field) · D19 (compat shim PlanService.get_effective fallback `tenant_billing_config`) · D20 (MV stale → soft cap 105% via `mv_refresh_log` — Q4) · D21 (OptInPolicy DB-backed via `lead_opt_ins` table — Q2) · D22 (`lead.country` column added preferred over phone-prefix heuristic — Q3) · D23 (`mv_refresh_log` dedicated table replaces `pg_stat_user_tables` heuristic — Q4) · D24 (Redis pub/sub cross-instance cache invalidation + 5min TTL fallback — Q5) · D25 (`plan_config.is_default` partial unique idx — Q6) · D26 (Plan seed outbound caps editable inline via Streamlit admin — Q8) · D27 (Skills `copilot-expert` + `sales-agent-expert` updated with budget/outbound gating refs) |

## 14. Test surfaces (TDD-mandatory)

Cada capa RED-first.

### Layer 1: Domain (pure VOs)
- `test_plan_config_vo.py` — invariants: `llm_budget_total_usd > 0`, `sa_pct ∈ [0,1]`, `sa_pool_usd + others_pool_usd == llm_budget_total_usd` (Decimal precision), `is_default` field default FALSE (Q6).
- `test_subscription_vo.py` — `cycle_anchor_day ∈ [1,28]`, `custom_overrides` dict roundtrip.
- `test_budget_decision_vo.py` — frozen, allowed/soft_warn semantics.
- `test_check_result_vo.py` — frozen, evidence dict default.
- `test_channel_blacklist_entry_vo.py` — frozen, identifier normalization (caller responsibility documented).
- `test_lead_opt_in_vo.py` (Q2) — frozen, `is_active_opt_in` derived correctly, `source` enum literal honored.
- `test_mv_refresh_log_vo.py` (Q4) — frozen, `status` enum literal honored, defaults to `"ok"`.

### Layer 2: Infrastructure (repos + models)
- `test_plan_repository.py` — list_active filters `is_active=True`, upsert idempotente, `get_default()` returns the row with `is_default=TRUE` (Q6).
- `test_subscription_repository.py` — get_by_tenant_id filters `deleted_at IS NULL`, upsert merges `custom_overrides`, soft_delete sets `deleted_at`.
- `test_blacklist_repository.py` — `is_blacklisted` checks `deleted_at IS NULL`, `unique(tenant_id, channel, identifier)` enforced.
- `test_lead_opt_in_repository.py` (Q2) — `has_active_opt_in` returns False when `opted_out_at NOT NULL`, `upsert` ON CONFLICT updates timestamps idempotently, `list_by_tenant(active_only=True)` filters out opted_out + never-opted-in rows. Tenant isolation enforced (cross-tenant lookups return empty).
- `test_mv_refresh_log_repository.py` (Q4) — `record_refresh` writes row with status, `get_last_refresh(mv_name)` returns most recent ORDER BY refreshed_at DESC LIMIT 1, `delete_older_than(cutoff)` deletes correctly.
- `test_lead_opt_ins_backfill.py` (Q2) — migration backfill from `messages.role='user'` produces correct rows with `source='inferred_message'`, idempotent on re-run (ON CONFLICT DO NOTHING).
- `test_plan_config_one_default_db.py` (Q6) — DB partial unique index prevents two `is_default=TRUE` rows simultaneously (raises IntegrityError).
- Migration prod-clone idempotency (manual cmd documented §9).

### Layer 3: Application (services)
- `test_plan_service.py`:
  - subscription exists → return plan_config + custom_overrides merged.
  - subscription NULL + legacy exists → translate to PlanConfig in-memory.
  - subscription NULL + legacy NULL → fallback `get_default_plan()` (Q6).
  - `get_default_plan()` returns row with `is_default=TRUE` (Q6).
  - `get_default_plan()` falls back to `BILLING_DEFAULT_PLAN_ID` env var if DB query fails (Q6).
  - `get_default_plan()` raises `BillingDefaultPlanMissingError` if neither resolves (Q6 fail-fast).
  - cache hit (5min TTL) — no DB query.
  - `invalidate_cache` clears entry.
  - `update_plan(is_default=True)` atomically demotes prior default + promotes new (Q6).
  - `update_plan` publishes `cache_invalidate:plan_config` to Redis (Q5 — mock pub/sub).
  - `update_subscription` publishes `cache_invalidate:tenant_subscription:{tenant_id}` (Q5).
  - Subscriber callback evicts cache on incoming pub/sub message (Q5).
  - Redis publish failure → soft-fail with structlog warning, no exception raised (Q5).
- `test_budget_guard.py` (per PR.md §Tests requeridos + Q4 mv_refresh_log):
  - `test_sales_agent_call_within_pool_allowed`
  - `test_sales_agent_call_exhausts_sa_pool_blocked`
  - `test_copilot_call_within_others_pool_allowed`
  - `test_copilot_call_exhausts_others_pool_blocked`
  - **`test_copilot_exhausted_cannot_consume_sa_pool`** ← invariant CRÍTICO
  - `test_soft_warn_at_80pct`
  - `test_custom_override_per_tenant_respected`
  - `test_mv_stale_via_mv_refresh_log_applies_soft_cap_105pct` (Q4: probe via `mv_refresh_log.get_last_refresh`).
  - `test_mv_refresh_log_absent_or_status_error_treated_as_stale` (Q4).
  - `test_decision_cached_5min_no_db_requery`
  - `test_mv_query_failure_fail_open_logged_warn`
- `test_rate_limiter.py`:
  - sliding window correctness (msg t=0 expires t=24h+1).
  - `max_outbound_msg_per_day=NULL` → unlimited.
  - concurrent inserts atomic (ZADD pipeline).
  - Redis unavailable → fail-open + structlog warning.
- `test_compliance_service.py`:
  - policy chain order respected.
  - short-circuit on first FAIL.
  - all PASS → final allowed=True.
  - structured logging per policy.
- `test_waba_24h_policy.py` — last inbound < 24h → PASS, > 24h → FAIL.
- `test_opt_in_policy.py` (Q2 DB-backed) — DB row with `opted_in_at NOT NULL AND opted_out_at IS NULL` → PASS; row with `opted_out_at NOT NULL` → FAIL; no row at all → FAIL; `source='inferred_message'` row still PASS but evidence flags lower trust.
- `test_blacklist_policy.py` — match by `(tenant_id, channel, identifier)`, soft-deleted excluded.
- `test_country_block_policy.py` (Q3) — env empty default → no-op pass; populated + `lead.country='CU'` → FAIL with `country_source='lead_field'`; `lead.country IS NULL` falls back to phone E.164 prefix heuristic (whatsapp/telegram only); identifier=email + `lead.country IS NULL` → `country_source='unknown'` → PASS (allow by default).

### Layer 4: Architecture (fitness gates)
- `test_budget_reservation_invariant.py` (Hypothesis 200 examples).
- `test_compliance_used_by_channels.py` (allowlist empty initial).
- `test_no_hardcoded_plan_prices.py` (regex grep).

### Layer 5: Admin smoke
- `test_billing_page_smoke.py`:
  - `pages/planes-billing.py` imports without error.
  - `modules/billing.py::render_billing` exists + callable.
  - `PAGE_SPECS` contains `slug='planes-billing'`.

### Layer 6: Integration (manual / `verify` marker)
- Streamlit operational (manual): start admin → navigate `/planes-billing` → edit Ultra row to $120 → save → verify `BudgetGuard.check` reflects new cap (cache invalidation works).

## 15. Research notes

State-of-the-art consultations 2026-04 (April):

| Topic | Source | Decision impact |
|---|---|---|
| Sliding-window rate limit Redis sorted set | [Redis docs ZADD/ZREMRANGEBYSCORE pattern](https://redis.io/docs/latest/develop/use/patterns/distributed-locks/) (accessed 2026-04-29) — canonical pattern, atomic via pipeline | Elegido Opción A (sliding window) sobre token bucket. Antispam default, accurate burst. |
| MV staleness graceful degradation | Industry pattern 2026: read-side cache TTL with stale-fallback (DDIA Ch. 10) | Soft cap 105% en MV stale > 1h evita producto halt; trade-off documentado. |
| Hypothesis property-based for invariants | [Hypothesis 6.x docs](https://hypothesis.readthedocs.io/) — strategy composition para Decimal + UUID | `test_budget_reservation_invariant.py` 200 examples cubre cuadrant fully. |
| Streamlit `st.navigation` registry pattern | Codebase precedent: `backend/src/admin/app.py` PAGE_SPECS — established 2026-Q1 | Reuso patrón, no innovation. |
| FastAPI redirect_slashes=False mandate | `.claude/rules/backend-ddd.md` + arch test enforcement | N/A PR-2 (sin HTTP nuevo). |

**Skill consultations** (decisions, not full content):
- **`copilot-expert`** (referenced via SKILL.md context): cost recording invariants — `model_pricing_snapshot` schema + `copilot_llm_call.cost_usd` columna tipada (NO JSONB legacy). PR-2 BudgetGuard solo SELECT `mv_daily_llm_cost_per_tenant_v2.cost_usd` agregado. Sin escrituras a observability tables.
- **`sales-agent-expert`** (referenced via SKILL.md context): tier pricing 200k tokens (Kimi K2.6) — calculator split en `TIER_THRESHOLD = 200_000` (S12 cementado). PR-2 acepta `estimated_cost_usd` pre-computed por caller; **no recomputa tiers** (no invade calculator §3-protected). Reservación 50% SA = §3 invariant — test arch property-based enforce.
- **`metrics-expert`** (referenced via SKILL.md context): `mv_daily_llm_cost_per_tenant_v2` schema (`agent_kind, tenant_id, occurred_on, cost_usd, ...`) — refresh hourly CONCURRENTLY via `aggregate_refresh_task`. BudgetGuard reusa MV (no DB query directa a `*_llm_call`). MV freshness probe: `pg_stat_user_tables.last_vacuum` o custom timestamp en `mv_refresh_log` (TBD builder — **Open Q5**).
- **`backend-expert`** (referenced via SKILL.md context): admin panel registry pattern (`PAGE_SPECS` + `pages/{slug}.py` + `modules/{name}.py::render_*()`) — contract+smoke tests obligatorios. Slug `planes-billing` (kebab-case match doc convention).

## 16. Decisions resolved by PM (audit trail Q1-Q10)

PM (Chris) priorizó **"lo más escalable, cero deuda técnica, miles clientes pronto"**. Decisiones cementadas 2026-04-29:

| # | Question | PM decision | Impact on contract |
|---|---|---|---|
| **Q1** | `IdempotencyStore` (PR-1) consumido por opt-in webhook handler — scope PR-2 o S2? | **✅ S2 confirmed** — PR-2 no introduce HTTP webhook nuevo. Sin deuda. | No new IdempotencyStore call sites in PR-2. Migration backfill SQL idempotent via `ON CONFLICT DO NOTHING`. |
| **Q2** | `OptInPolicy` stub vs tabla dedicada `lead_opt_ins` ahora? | **🔄 CHANGED — tabla `lead_opt_ins` AHORA, no stub.** Implicit consent (`messages.role='user'`) heurístico frágil; tabla dedicada con explicit timestamps + source + GDPR/LGPD audit trail = production-grade. | New entity §1.6 + model §2.4 + repo + migration backfill from messages last 30d (idempotent). New arch test `test_lead_opt_ins_invariants.py`. `OptInPolicy.check` now DB-backed. |
| **Q3** | `CountryBlockPolicy` — phone prefix solo o agregar `LeadModel.country`? | **🔄 CHANGED — `leads.country` column AHORA.** Phone prefix heurístico falla email-only / web channel. ISO 3166-1 alpha-2. Fallback chain: `lead.country` → phone E.164 prefix → unknown (allowed). | `leads.country` ALTER §2.6. `CountryBlockPolicy._resolve_country` chain documented. `pm-nico/current-state/crm.md` update required. |
| **Q4** | MV freshness probe — `pg_stat_user_tables` vs dedicated `mv_refresh_log` table? | **🔄 CHANGED — tabla `mv_refresh_log` dedicada AHORA.** `pg_stat_user_tables.last_vacuum` ≠ last refresh real, frágil. Cron INSERTs row post-refresh. 90d retention. | New entity §1.7 + model §2.5 + repo + workers (recorder + retention). `BudgetGuard._is_mv_stale` queries `mv_refresh_log.get_last_refresh`. Arch test `test_mv_refresh_log_freshness.py` enforces no `pg_stat_user_tables` reference. |
| **Q5** | Cache invalidation cross-instance — Redis pub/sub vs aceptar 5min TTL? | **🔄 CHANGED — Redis pub/sub AHORA + 5min TTL fallback.** Single replica hoy pero "miles clientes" → multi-pod garantizado. Soft-fail: Redis unavailable → log warn + TTL eventual consistency. | `PlanService.update_plan` + `update_subscription` publish to Redis channels. New file `cache_invalidation_subscriber.py` background task. New tests for pub/sub semantics. |
| **Q6** | `BILLING_DEFAULT_PLAN_ID` env vs hardcode in PlanService? | **🔄 CHANGED — `plan_config.is_default BOOLEAN` + partial unique idx + env var fallback safety.** DB authoritative; env is fail-safe. Atomic toggle in Streamlit. | `plan_config.is_default` field §1.1 + §2.1. Partial unique index `uq_plan_config_one_default`. `PlanService.get_default_plan()` resolves DB → env → fail-fast. Seed `'free'` ships `is_default=TRUE`. New arch test `test_plan_config_one_default.py`. |
| **Q7** | `test_compliance_used_by_channels.py` allowlist initial empty — when populated? | **✅ confirmed default** — vacía inicial, S2 PR ChannelRouter wire. | No PR-2 change. Test ships with empty allowlist. |
| **Q8** | Plan seed outbound limits — editables + skill update for cap consumers? | **✅ confirma editable** — outbound limits ya en `plan_config.max_outbound_msg_per_day` column → Streamlit edita inline (1 UPDATE row, 0 migration). Plus: skills `copilot-expert` + `sales-agent-expert` updated with budget/outbound gating refs. | Seed values: Free 100 / Básico 500 / Intermedio 2000 / Avanzado 5000 / Ultra 20000 msg/día (PM editable post-deploy). Skills updated (see §15 Skill consultations + companion skill files). |
| **Q9** | Migration head conflict (parallel sessions)? | **✅ builder runtime** — `make alembic-current` pre-implement, merge head si conflict (Alembic merge-heads pattern). | Migration §9 `down_revision = "085_copilot_tenant_limits"` proposed, builder verifies and merges if needed. |
| **Q10** | `plan_config` global catalog allowlist for tenant_isolation arch test? | **✅ builder runtime** — `plan_config` (and now `mv_refresh_log` per Q4) no tienen `tenant_id` (global catalog/operational infra). Builder agrega allowlist con justification inline. | §12 architectural fitness updated: allowlist additions for `plan_config` ("global catalog") + `mv_refresh_log` ("operational infra"). |

**Net delta vs prior architect draft**: 5 elevations to production-grade (Q2 / Q3 / Q4 / Q5 / Q6) — eliminadas 5 deudas técnicas que habrían surgido S2 (opt-in tabla, lead.country, mv_refresh_log, pub/sub, is_default). 3 confirmaciones de defaults (Q1 / Q7 / Q8 partial). 2 builder-runtime decisions (Q9 / Q10).

---

<!-- @pm: CONTRACT.md updated with PM decisions Q1-Q10 + skills updated. Ready for builder. -->
