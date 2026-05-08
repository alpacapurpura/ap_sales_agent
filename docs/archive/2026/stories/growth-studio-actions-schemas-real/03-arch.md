# 03-arch.md — Growth Studio Real Actions + Real Schemas (2B) — consolidated

> Owner: `/architect` (Opus 4.7). Sub-architects spawned in parallel:
> `/architect-be`, `/architect-fe`, `/architect-agentic`. This file is the
> consolidated single source of truth for the build phase.

---
story_id: growth-studio-actions-schemas-real
arch_version: 1
last_modified: 2026-05-08T00:00:00Z
spec_ratified: 2026-05-07T04:15:00Z
links:
  spec: "01-spec.md"
  outcome: "../../outcomes/growth-copilot-layout-unification.md"
  story_2a_done: "../growth-studio-folder-parity/03-arch.md"
  story_1_done: "../app-shell-sidebar-copilot-decoupling/03-arch.md"
  brand_actions_pattern: "../../../../frontend/src/features/brand-studio/actions/registry.ts"
  copilot_tools_existing: "../../../../backend/src/modules/copilot/application/tools/analytics_tools.py"
rules:
  - .claude/rules/tenant-isolation.md
  - .claude/rules/backend-ddd.md
  - .claude/rules/anti-duplication.md
  - .claude/rules/tdd-mandatory.md
  - .claude/rules/copilot-resilience.md
  - .claude/rules/copilot-observability.md
  - .claude/rules/currency-handling.md
  - .claude/rules/master-data.md
  - .claude/rules/spanish-text.md
  - .claude/rules/etl-extraction-contract.md
  - .claude/rules/data-reliability.md
  - .claude/rules/architectural-fitness.md
---

## 0 · Surface → builder → auditor mapping

| Surface | Builder | Auditor | Skill input |
|---|---|---|---|
| `backend/src/modules/copilot/application/tools/analytics_tools.py` (REPLACE legacy) | `builder-agentic` (Opus 4.7) | `auditor-agentic` (Opus 4.7) | `copilot-expert` |
| `backend/src/modules/copilot/application/tools/__init__.py` (registration) | `builder-agentic` (Opus 4.7) | `auditor-agentic` (Opus 4.7) | `copilot-expert` |
| `backend/src/modules/copilot/observability/eval/goldens/route_tool_selection.json` (golden update) | `builder-agentic` (Opus 4.7) | `auditor-agentic` (Opus 4.7) | `copilot-expert` |
| `backend/src/modules/analytics/api/metrics.py` (rate-limit endpoint reuse + `/catalog` — already exists, **NO CHANGE in 2B**) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | `metrics-expert` |
| `backend/src/modules/analytics/application/services/etl_refresh_guard.py` (NEW thin guard wrapping `OutboundRateLimiter` for ETL) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | `metrics-expert` + `tessl__graceful-degradation` |
| `backend/tests/modules/copilot/application/tools/test_analytics_tools_*.py` (NEW) | `builder-agentic` (Opus 4.7) | `auditor-agentic` (Opus 4.7) | `copilot-expert` |
| `frontend/src/features/growth-studio/actions/{StageMetricsAction,ChannelOverviewAction,ETLRefreshAction,ETLRateLimitedAction,ETLConfirmAction}.tsx` + `actions/registry.ts` + `actions/index.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | `frontend-expert` |
| `frontend/src/features/growth-studio/schemas/{stage-filter-params,channel-config,kpi-selection,tier-loading}.schema.ts` + `schemas/index.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | `frontend-expert` + `metrics-expert` |
| `frontend/src/features/growth-studio/actions/__tests__/*` + `schemas/__tests__/*` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) | `frontend-expert` |
| `backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py` (cross-stack contract) | `builder-backend` (Sonnet) | `auditor-backend` (Opus) | `metrics-expert` |

**capability YAML files affected (post-merge updates required):**
`docs/product/capabilities/analytics/growth-studio-copilot-actions.yaml` (NEW — promote from refining → done at merge) + narrative refresh in `docs/product/modules/analytics.md` § "Copilot integration".

**Architecture gates that must keep passing:**
`backend/tests/architecture/test_no_new_copilot_module_imports.py`,
`test_copilot_anchors.py`, `test_copilot_provider_compliance.py`,
`test_extraction_contract.py`, `test_no_legacy_eventbus_mock_when_outbox_on.py`,
`frontend/src/__tests__/architecture/test-studio-structure-parity.test.ts`,
`test-shell-copilot-offset.test.ts`.

## 1 · Existing systems audit (NO NEW LAYER rule)

### Source of evidence

- [ ] CONTEXT-BRIEF.md § 7 + § 8 — **NOT generated for this story** (no `CONTEXT-BRIEF.md` in story dir; story is small enough that `/architect` self-ran greps Path B)
- [x] Self-run greps (Path B fallback)

### Audit cross-module ejecutado

```bash
# 1. Search global config for analytics tools
grep -rln "ANALYTICS_TOOLS\|get_funnel_metrics\|get_stage_metrics" backend/src/ backend/tests/
# Result:
#   - backend/src/modules/copilot/application/tools/analytics_tools.py  (legacy tool)
#   - backend/src/modules/copilot/application/tools/registry.py         (consumes ANALYTICS_TOOLS)
#   - backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json (golden)

# 2. Search shared abstractions for rate limiting
grep -rln "RateLimiter\|rate_limit" backend/src/shared/billing/
# Result:
#   - backend/src/shared/billing/application/rate_limiter.py  → OutboundRateLimiter (Redis sliding window)

# 3. Search analytics module for refresh / catalog endpoints
grep -n "refresh_channel_metrics\|get_metric_catalog\|get_stage_overview\|get_channel_dashboard" backend/src/modules/analytics/api/metrics.py
# Result (all already exist — REUSE, NO NEW endpoints):
#   - line 771: refresh_channel_metrics  (with 15-min cooldown)
#   - line 832: get_metric_catalog       (returns full METRIC_CATALOG)
#   - line 309: get_stage_overview       (tier-1 endpoint)
#   - line 866: get_channel_dashboard    (per-channel dashboard)

# 4. Search FE registries for SSoT
grep -rn "STAGE_REGISTRY\|CHANNEL_REGISTRY\|DASHBOARD_REGISTRY" frontend/src/features/growth-studio/lib/registries/
# Result: 3 frozen registries exist (Story 2A T-1 shipped)

# 5. Search FE actions/schemas placeholders
ls frontend/src/features/growth-studio/{actions,schemas}/
# Result: both empty (Story 2A T-7 commit 828bb3dc shipped .gitkeep, then T-8 verify)
#         → 2B can begin populating these folders
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `analytics_tools.py::get_funnel_metrics` | `backend/src/modules/copilot/application/tools/analytics_tools.py:17` | active legacy (≤8000 token return; sales-table aggregation only; no stage/channel filter) | **REPLACE per spec Q6** — atomic migration in same PR (caller audit confirmed: only 2 callers — analytics_tools.py self + golden route_tool_selection.json) |
| `OutboundRateLimiter` (Redis sliding window 24h) | `backend/src/shared/billing/application/rate_limiter.py` | active | **EXTEND via composition** — wrap with thin `etl_refresh_guard.py` per-tenant per-channel 1-hour window (NOT 24h). Reuses Redis pipeline pattern + fail-open soft-degrade. NO new Redis layer. |
| `BudgetGuard` (LLM cost gate) | `backend/src/shared/billing/application/budget_guard.py` | active | **REUSE** — already invoked by copilot orchestrator pre-LLM-call (PI-1 S0 PR-2). 2B tools inherit budget gating automatically; no extra wiring. |
| `refresh_channel_metrics` endpoint | `backend/src/modules/analytics/api/metrics.py:771` | active | **REUSE** — `trigger_etl_refresh` tool calls this endpoint. NO new endpoint needed. |
| `get_metric_catalog` endpoint | `backend/src/modules/analytics/api/metrics.py:832` | active | **REUSE** — `kpi-selection.schema.ts` runtime fetch consumes this endpoint via React Query. NO new endpoint, NO new mirror constants. |
| `get_stage_overview` endpoint (Tier 1) | `backend/src/modules/analytics/api/metrics.py:309` | active | **REUSE** — `get_stage_metrics` tool calls Tier-1 first; cascades to Tier 2/3 if more detail needed. |
| `get_group_detail` endpoint (Tier 2) | `backend/src/modules/analytics/api/metrics.py:340` | active | **REUSE** — Tier 2 fallback for cardinality-aware queries. |
| `get_channel_dashboard` endpoint | `backend/src/modules/analytics/api/metrics.py:866` | active | **REUSE** — `get_channel_overview` tool calls this endpoint. |
| FE `STAGE_REGISTRY` + `CHANNEL_REGISTRY` + `DASHBOARD_REGISTRY` | `frontend/src/features/growth-studio/lib/registries/*.ts` | active (2A shipped) | **CONSUME** — schemas + actions read from these registries. NO new mirror. |
| FE `useTenantLocale()` hook | `frontend/src/hooks/use-tenant-locale.ts` | active | **CONSUME** — currency + timezone for KPI display. NO new locale mirror. |
| FE `formatMoney()` / `formatTenantDate*()` | `frontend/src/lib/format/*` | active | **CONSUME** — KPI cell display. |
| FE `fetchClient` (auto X-Tenant-ID) | `frontend/src/lib/api/fetchClient.ts` | active | **CONSUME** — every action uses fetchClient, NEVER raw `fetch()`. |
| FE `actions/registry.ts` pattern (brand/offer-studio) | `frontend/src/features/{brand,offer}-studio/actions/registry.ts` | active | **MIRROR PATTERN** (not data) — same shape: `bootstrapGrowthStudioActions()` + idempotent registerAction + side-effect import from `schemas/index.ts`. |

### Decisión por sistema (resumen)

- **Legacy `get_funnel_metrics`**: REPLACE (atomic migration; deprecated marker arch test; removal post 1 ciclo).
- **`OutboundRateLimiter` for ETL**: EXTEND via composition. New file `etl_refresh_guard.py` wraps it with a 1-hour window keyed by `(tenant_id, channel_slug)`. NO new Redis abstraction. (Anti-duplication compliance: it's 1 consumer for 1 use case — no need to lift to `shared/`.)
- **All BE analytics endpoints**: REUSE — tools compose existing endpoints (anti-duplication).
- **FE format helpers, locale hook, fetchClient**: CONSUME (anti-duplication).
- **Action registry pattern**: MIRROR PATTERN, NOT DATA — coherent with cross-studio, but each studio owns its own keys.

NO NEW LAYER PROPOSED. Total new files: 5 BE (tools split + guard + tests) + 9 FE (5 actions + 4 schemas + index/registry) + 1 contract test.

## 2 · BE design (full detail per `/architect-be`)

### 2.1 Tool replacement plan (`get_funnel_metrics` → 3 NEW tools)

The single legacy `get_funnel_metrics` tool returned a flat sales-aggregated text. Per spec Q6, REPLACE with three precise tools that compose existing analytics endpoints (no new endpoints):

| New tool | Args | Returns | Underlying call |
|---|---|---|---|
| `get_stage_metrics(stage, channel?, period?)` | `stage: Stage` (enum 5 stages), `channel: ChannelSlug \| None`, `period: Literal["7d","30d","90d"] = "30d"` | JSON: `{ stage_name, period, kpis: [{slug, value, currency?, change_pct}], channel_breakdown, tier_used, truncated, ui_action }` | Cascade: `get_stage_overview(stage,period)` (Tier 1) → if `channel` → filter response → if cardinality > 10k rows → optional Tier 3 with `truncated=true` |
| `get_channel_overview(channel)` | `channel: ChannelSlug` (5 canonical) | JSON: `{ channel_name, dashboard_kpis: [...], period, ui_action }` | `get_channel_dashboard(channel_slug)` |
| `trigger_etl_refresh(channel, confirmed=False)` | `channel: ChannelSlug`, `confirmed: bool = False` | JSON success: `{ status: "queued"\|"requires_confirmation", run_id?, current_count, limit, retry_after_seconds? }` | `etl_refresh_guard.check(...)` (NEW) → on allow → `refresh_channel_metrics(channel_slug)` endpoint |

**Stage enum (matches FE `STAGE_REGISTRY`):** `attraction` (atraccion-captura), `nurture` (nutricion-oportunidad), `sales` (ventas), `adoption` (adopcion), `evangelization` (expansion-evangelizacion). Spec scenario 1 used `"adopcion"` (Spanish slug); BE accepts both English (`FunnelStage` enum already in metrics.py) and Spanish FE slug — service layer maps via `STAGE_SLUG_MAP`.

**Channel enum (matches FE `CHANNEL_REGISTRY`):** `meta-ads`, `yt-organic`, `email-nurture`, `ig-organic`, `website-total`. Pydantic input model rejects others with structured error.

### 2.2 Pydantic v2 input schemas (BE = SSoT mirror of FE zod)

```python
# backend/src/modules/copilot/application/tools/_analytics_inputs.py  (NEW)
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

StagePeriod = Literal["7d", "30d", "90d"]
StageSlug = Literal[
    "atraccion-captura", "nutricion-oportunidad", "ventas",
    "adopcion", "expansion-evangelizacion",
]
ChannelSlug = Literal[
    "meta-ads", "yt-organic", "email-nurture", "ig-organic", "website-total",
]

class StageFilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stage: StageSlug
    channel: ChannelSlug | None = None
    period: StagePeriod = "30d"

class ChannelOverviewParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ChannelSlug

class TriggerEtlRefreshParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: ChannelSlug
    confirmed: bool = False
```

**Adversarial defense:** `Literal[...]` stage + channel = path injection (`"../../etc/passwd"`) and XSS (`"<script>"`) rejected at parse time → tool returns `{ "error": "invalid_input", "details": ... }` (Spanish neutro). `extra="forbid"` blocks payload-key smuggling (e.g. `tenant_override`).

### 2.3 ETL refresh guard (composition over OutboundRateLimiter)

```python
# backend/src/modules/analytics/application/services/etl_refresh_guard.py  (NEW)
from __future__ import annotations
import time, uuid, structlog
from uuid import UUID
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger(__name__)

class EtlRefreshGuard:
    """Per-tenant per-channel ETL refresh sliding window guard.

    Invariants:
    - Limit: 3 refreshes / 1-hour window (hardcoded default per spec Q1).
    - Override: only via DB seed `analytics_channel_config.etl_rate_limit_per_hour` (no UI).
    - Confirmation: when current_count > 1 (i.e. user already refreshed once
      this hour), tool returns requires_confirmation=True (per spec Q4).
    - Soft-fail: Redis unavailable → fail-open (log warning, allow).
    """

    KEY_TEMPLATE = "etl_refresh:{tenant_id}:{channel}"
    WINDOW_SECONDS = 3600   # 1 hour
    DEFAULT_LIMIT = 3
    CONFIRM_THRESHOLD = 1   # > 1 refresh in window → require confirm

    def __init__(self, redis_client: object, channel_config_repo: object) -> None:
        self._redis = redis_client
        self._config = channel_config_repo

    async def check(
        self, tenant_id: UUID, channel_slug: str, *, confirmed: bool
    ) -> "GuardDecision":
        limit = await self._config.get_limit(tenant_id, channel_slug) or self.DEFAULT_LIMIT
        key = self.KEY_TEMPLATE.format(tenant_id=str(tenant_id), channel=channel_slug)
        now = time.time()
        cutoff = now - self.WINDOW_SECONDS
        try:
            pipeline = self._redis.pipeline()
            pipeline.zremrangebyscore(key, 0, cutoff)
            pipeline.zcard(key)
            results = await pipeline.execute()
            current_count = results[1]

            if current_count >= limit:
                # rate limit exceeded
                oldest_score = await self._redis.zrange(key, 0, 0, withscores=True)
                retry_after = int(self.WINDOW_SECONDS - (now - oldest_score[0][1])) if oldest_score else self.WINDOW_SECONDS
                return GuardDecision(allowed=False, current_count=current_count, limit=limit, retry_after_seconds=retry_after)

            if current_count > self.CONFIRM_THRESHOLD and not confirmed:
                return GuardDecision(
                    allowed=False, requires_confirmation=True,
                    current_count=current_count, limit=limit,
                )

            # accept + record
            member = str(uuid.uuid4())
            add_pipeline = self._redis.pipeline()
            add_pipeline.zadd(key, {member: now})
            add_pipeline.expire(key, self.WINDOW_SECONDS)
            await add_pipeline.execute()
            return GuardDecision(allowed=True, current_count=current_count + 1, limit=limit)
        except Exception as exc:  # noqa: BLE001 — fail-open per tessl__graceful-degradation
            logger.warning("etl_refresh_guard_redis_unavailable_fail_open",
                           tenant_id=str(tenant_id), channel=channel_slug, error=str(exc))
            return GuardDecision(allowed=True, current_count=0, limit=limit, soft_fail=True)
```

`GuardDecision` is a frozen dataclass returned to the tool layer. The tool serializes it to JSON for the agent.

### 2.4 Tenant isolation

Every tool reads `tenant_id` from `src.core.context.get_tenant_id()` (set by `X-Tenant-ID` middleware). **Adversarial scenario 4 defense:** even if the LLM smuggles `tenant_id` in the tool call payload, `extra="forbid"` rejects it. Tools NEVER trust caller-supplied tenant.

### 2.5 No DB migrations

`analytics_channel_config` table for `etl_rate_limit_per_hour` per spec Q1 — **lazy bootstrap**: if table absent, `EtlRefreshGuard._config.get_limit()` returns `None` and DEFAULT_LIMIT (3) applies. Story 2B does NOT introduce DDL — defer table to a future story when admin UI for overrides is built. (Documented in 06-tickets `out_of_scope`.)

### 2.6 Tools already participate in copilot observability + budget guard

Because the new tools register via the same `ANALYTICS_TOOLS` group (see § 4 below), they automatically benefit from:
- `copilot_trace_event` recorder (best-effort try/except in callback handler)
- `copilot_llm_call` recording with cost_usd / cache_creation / cache_read
- `BudgetGuard.check(agent_kind="copilot")` pre-LLM-call (PI-1 S0 PR-2 wiring)

No extra observability code in tool body — handled by the orchestrator's callback handler.

## 3 · FE design (full detail per `/architect-fe`)

### 3.1 Files NEW (Phase 2B)

```
frontend/src/features/growth-studio/
├── actions/                                         # populate (post 2A T-7 .gitkeep)
│   ├── StageMetricsAction.tsx                       # NEW
│   ├── ChannelOverviewAction.tsx                    # NEW
│   ├── ETLRefreshAction.tsx                         # NEW
│   ├── ETLRateLimitedAction.tsx                     # NEW (spec scenario 2)
│   ├── ETLConfirmAction.tsx                         # NEW (spec Q4 confirm flow)
│   ├── registry.ts                                  # NEW (mirror brand-studio pattern)
│   ├── index.ts                                     # NEW (barrel export)
│   └── __tests__/
│       ├── StageMetricsAction.test.tsx              # NEW (RED first)
│       ├── ChannelOverviewAction.test.tsx           # NEW
│       ├── ETLRefreshAction.test.tsx                # NEW
│       ├── ETLRateLimitedAction.test.tsx            # NEW
│       ├── ETLConfirmAction.test.tsx                # NEW
│       └── StageMetricsAction-large-volume.test.tsx # NEW (spec scenario 3)
└── schemas/
    ├── stage-filter-params.schema.ts                # NEW
    ├── channel-config.schema.ts                     # NEW
    ├── kpi-selection.schema.ts                      # NEW (runtime fetch /catalog)
    ├── tier-loading.schema.ts                       # NEW
    ├── index.ts                                     # NEW (barrel + side-effect import registry)
    └── __tests__/
        ├── stage-filter-params.test.ts              # NEW (RED first)
        ├── channel-config.test.ts                   # NEW
        ├── kpi-selection.test.ts                    # NEW
        ├── tier-loading.test.ts                     # NEW
        └── stage-filter-params-security.test.ts     # NEW (spec scenario 4)
```

### 3.2 Zod schemas (FE = SSoT mirror of BE Pydantic)

```typescript
// frontend/src/features/growth-studio/schemas/stage-filter-params.schema.ts
import { z } from "zod";
import { STAGE_REGISTRY } from "../lib/registries/stage-registry";
import { CHANNEL_REGISTRY } from "../lib/registries/channel-registry";

const STAGE_SLUGS = STAGE_REGISTRY.map((s) => s.slug) as [string, ...string[]];
const CHANNEL_SLUGS = CHANNEL_REGISTRY.map((c) => c.slug) as [string, ...string[]];

export const stageFilterParamsSchema = z
  .object({
    stage: z.enum(STAGE_SLUGS),
    channel: z.enum(CHANNEL_SLUGS).optional(),
    period: z.enum(["7d", "30d", "90d"]).default("30d"),
  })
  .strict();   // forbid extra keys (mirror Pydantic ConfigDict(extra="forbid"))

export type StageFilterParams = z.infer<typeof stageFilterParamsSchema>;
```

```typescript
// frontend/src/features/growth-studio/schemas/channel-config.schema.ts
import { z } from "zod";
import { CHANNEL_REGISTRY } from "../lib/registries/channel-registry";

const CHANNEL_SLUGS = CHANNEL_REGISTRY.map((c) => c.slug) as [string, ...string[]];

export const channelConfigSchema = z
  .object({
    slug: z.enum(CHANNEL_SLUGS),
    dashboard: z.string().regex(/^[a-z0-9-]+$/),
    kpis: z.array(z.string()).min(1),
    color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
    etl_rate_limit_per_hour: z.number().int().min(1).max(20).default(3),
  })
  .strict();

export type ChannelConfig = z.infer<typeof channelConfigSchema>;
```

```typescript
// frontend/src/features/growth-studio/schemas/kpi-selection.schema.ts
import { z } from "zod";

// Runtime fetch /api/v1/analytics/metrics/catalog → no FE-side mirror constants.
export const metricCatalogEntrySchema = z.object({
  name: z.string(),
  display_name: z.string(),
  unit: z.enum(["count", "currency", "percentage", "ratio", "seconds", "json"]),
  aggregation: z.enum(["additive", "weighted_average", "derived", "non_aggregable", "snapshot"]),
  is_unique_metric: z.boolean(),
  higher_is_better: z.boolean(),
  providers: z.array(z.string()),
});

export const metricCatalogResponseSchema = z.object({
  metrics: z.array(metricCatalogEntrySchema),
  count: z.number().int().min(0),
});

export const kpiSelectionSchema = z
  .object({
    selected_kpis: z.array(z.string()).min(1).max(10),
  })
  .strict();

export type MetricCatalogEntry = z.infer<typeof metricCatalogEntrySchema>;
export type KpiSelection = z.infer<typeof kpiSelectionSchema>;
```

```typescript
// frontend/src/features/growth-studio/schemas/tier-loading.schema.ts
import { z } from "zod";

export const tierResponseSchema = z
  .object({
    tier: z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3)]),
    size_hint: z.enum(["small", "medium", "large"]),
    truncated: z.boolean().default(false),
    row_count: z.number().int().min(0),
    payload: z.unknown(),     // tier-specific (DTOs validated separately)
  })
  .strict();

export type TierResponse = z.infer<typeof tierResponseSchema>;
```

`schemas/index.ts` re-exports schemas + **side-effect imports `../actions/registry.ts`** (mirror brand-studio pattern):

```typescript
// frontend/src/features/growth-studio/schemas/index.ts
import "../actions/registry";   // side-effect: bootstrap action registry
export { stageFilterParamsSchema, type StageFilterParams } from "./stage-filter-params.schema";
export { channelConfigSchema, type ChannelConfig } from "./channel-config.schema";
export { kpiSelectionSchema, metricCatalogResponseSchema, type MetricCatalogEntry } from "./kpi-selection.schema";
export { tierResponseSchema, type TierResponse } from "./tier-loading.schema";
```

### 3.3 Action components (5 React files)

Each action is a Client Component (`"use client"`), receives `payload` as props from copilot SSE block, consumes:
- `useTenantLocale()` for currency + timezone
- `formatMoney(value, currency)` for monetary KPIs
- `formatTenantDate*()` for any date display
- `fetchClient` (NEVER raw fetch) for any imperative call (only ETLRefreshAction needs this for confirm-step second tool call; primary data arrives via SSE payload)

Component shape (representative):

```typescript
// frontend/src/features/growth-studio/actions/StageMetricsAction.tsx
"use client";
import { useTenantLocale } from "@/hooks/use-tenant-locale";
import { formatMoney } from "@/lib/format/money";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import type { ActionComponentProps } from "@/lib/form-runtime/actions";

interface StageMetricsPayload {
  stage_name: string;
  period: string;
  kpis: Array<{ slug: string; value: number; currency?: string; change_pct?: number }>;
  channel_breakdown?: Array<{ channel: string; value: number }>;
  tier_used: 0 | 1 | 2 | 3;
  truncated: boolean;
}

export function StageMetricsAction({ payload }: ActionComponentProps<StageMetricsPayload>) {
  const { currency: tenantCurrency } = useTenantLocale();
  return (
    <Card aria-label={`Métricas de ${payload.stage_name}`}>
      <CardHeader>
        <h3>{payload.stage_name}</h3>
        <p>Período: {payload.period}</p>
      </CardHeader>
      <CardContent>
        <ul>
          {payload.kpis.map((k) => (
            <li key={k.slug}>
              <span>{k.slug}</span>:&nbsp;
              <span>{formatMoney(k.value, k.currency ?? tenantCurrency)}</span>
              {k.change_pct !== undefined && <span>&nbsp;({k.change_pct > 0 ? "+" : ""}{k.change_pct}%)</span>}
            </li>
          ))}
        </ul>
        {payload.truncated && (
          <p role="alert">
            Datos parciales — pedí un filtro más estrecho para detalle completo.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

The other 4 actions follow the same skeleton. Spanish neutro user-facing strings (no voseo).

### 3.4 Action registry

```typescript
// frontend/src/features/growth-studio/actions/registry.ts
import { hasAction, registerAction, type ActionComponent } from "@/lib/form-runtime/actions";
import { StageMetricsAction } from "./StageMetricsAction";
import { ChannelOverviewAction } from "./ChannelOverviewAction";
import { ETLRefreshAction } from "./ETLRefreshAction";
import { ETLRateLimitedAction } from "./ETLRateLimitedAction";
import { ETLConfirmAction } from "./ETLConfirmAction";

export const GROWTH_STUDIO_ACTION_KEYS = [
  "growth.stage-metrics",
  "growth.channel-overview",
  "growth.etl-refresh",
  "growth.etl-rate-limited",
  "growth.etl-confirm",
] as const;

export type GrowthStudioActionKey = (typeof GROWTH_STUDIO_ACTION_KEYS)[number];

const REGISTRY_ENTRIES: Readonly<Record<GrowthStudioActionKey, ActionComponent>> = {
  "growth.stage-metrics": StageMetricsAction as unknown as ActionComponent,
  "growth.channel-overview": ChannelOverviewAction as unknown as ActionComponent,
  "growth.etl-refresh": ETLRefreshAction as unknown as ActionComponent,
  "growth.etl-rate-limited": ETLRateLimitedAction as unknown as ActionComponent,
  "growth.etl-confirm": ETLConfirmAction as unknown as ActionComponent,
};

export function bootstrapGrowthStudioActions(): void {
  for (const key of GROWTH_STUDIO_ACTION_KEYS) {
    if (hasAction(key)) continue;
    registerAction(key, REGISTRY_ENTRIES[key]);
  }
}

bootstrapGrowthStudioActions();
```

### 3.5 Cross-cutting

| Concern | Implementation |
|---|---|
| Tenant isolation | `fetchClient` injects X-Tenant-ID; actions never construct URLs from user input |
| Currency | `formatMoney(value, payload.currency ?? tenantLocale.currency)` (per `.claude/rules/currency-handling.md`) |
| Locale / timezone | `useTenantLocale()` + `formatTenantDate*()` (per `.claude/rules/master-data.md`) |
| Spanish neutro | tuteo, tildes, ñ; voseo glosary respected (lint regex hook) |
| A11y | `aria-label` on cards; `role="alert"` on rate-limited / confirm copy; Tab order via natural source order |
| Mobile | viewport ≥ 375px verified by visual regression |
| Bundle | actions are async-loadable via copilot SSE block renderer; no eager import in non-chat routes |

## 4 · Agentic design (full detail per `/architect-agentic`)

### 4.1 Tool registration in `ANALYTICS_TOOLS` group

The 3 new tools REPLACE `get_funnel_metrics` in the `ANALYTICS_TOOLS` list:

```python
# backend/src/modules/copilot/application/tools/analytics_tools.py  (REWRITE)
from langchain_core.tools import tool
from src.modules.copilot.application.tools._analytics_inputs import (
    StageFilterParams, ChannelOverviewParams, TriggerEtlRefreshParams,
)

@tool(args_schema=StageFilterParams)
def get_stage_metrics(stage: str, channel: str | None = None, period: str = "30d") -> str:
    """Consulta métricas de un stage específico del funnel con filtros opcionales.
    Args: stage (atraccion-captura | nutricion-oportunidad | ventas | adopcion |
                 expansion-evangelizacion), channel (opcional, slug canónico),
          period (7d | 30d | 90d, default 30d).
    """
    # ... implementation calling get_stage_overview / get_group_detail ...

@tool(args_schema=ChannelOverviewParams)
def get_channel_overview(channel: str) -> str:
    """Resumen de un canal específico (Meta Ads, YouTube, Email, etc.)."""
    # ... implementation calling get_channel_dashboard ...

@tool(args_schema=TriggerEtlRefreshParams)
def trigger_etl_refresh(channel: str, confirmed: bool = False) -> str:
    """Dispara una nueva extracción ETL para el canal indicado.
    Confirmación requerida si ya hubo refrescos en la última hora."""
    # ... implementation calling EtlRefreshGuard + refresh_channel_metrics ...

ANALYTICS_TOOLS = [get_stage_metrics, get_channel_overview, trigger_etl_refresh]
```

`get_funnel_metrics` is **removed in the same commit** (atomic per spec Q6 + caller audit confirmed only 2 references).

### 4.2 Tool group + ROUTE_TOOL_MAP (NO CHANGE)

`ANALYTICS_TOOLS` already lives in `_BASE_TOOL_GROUPS["analytics"]` and `growth-studio` route already includes `"analytics"` group. Result: tools auto-discovered without touching registry.py.

### 4.3 Eval golden update

`backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json` lists `get_funnel_metrics` for `growth-studio` route. Update with the 3 new tool names + run `UPDATE_GOLDEN=1 .venv/bin/pytest tests/modules/copilot/golden/ -q`. Diff must be reviewed by builder-agentic; commit with intentional `feat(copilot): replace get_funnel_metrics with 3 stage-specific tools` message.

### 4.4 Spanish neutro voice fidelity (eval goldens NEW)

3 new agentic eval scenarios under `backend/tests/quality/golden/growth_studio_actions/`:

| Golden | Prompt | Expected | Voice grader |
|---|---|---|---|
| `stage-query-happy.json` | "¿cómo va mi adopción los últimos 30 días?" | tool call `get_stage_metrics(stage="adopcion", period="30d")` + `<StageMetricsAction>` block | Spanish neutro, NO voseo, length cap respected |
| `etl-refresh-confirm.json` | "refrescá Meta Ads de nuevo" (after 1 prior refresh same hour) | tool call `trigger_etl_refresh(channel="meta-ads", confirmed=False)` returns `requires_confirmation=true` → agent renders `<ETLConfirmAction>` with copy "Ya disparaste un refresh este lapso. ¿Confirmás otro?" | Spanish neutro, polite confirm copy |
| `etl-refresh-rate-limited.json` | "refrescá Meta Ads" (after 5 prior refreshes) | tool call `trigger_etl_refresh(channel="meta-ads")` returns `error="rate_limit_exceeded"` → agent renders `<ETLRateLimitedAction>` with "No puedo refrescar ahora. Ya disparaste 5 refreshes este lapso (límite 3/hora). Próximo intento en ~31 min." | Spanish neutro, no retry loop |

Run via `RUN_LLM_JUDGE=1 pytest tests/quality/golden/growth_studio_actions/ -q` (NANO judge). Threshold: `grader_score >= 0.85`. Stub default for fast feedback in dev.

### 4.5 Cost / latency budget per tool

| Tool | Token budget (single call) | p95 latency | cost target |
|---|---|---|---|
| `get_stage_metrics` (Tier 1 cache hit) | input ≤ 6k, output ≤ 1k | < 800ms | < $0.05/turn |
| `get_stage_metrics` (Tier 3 cold) | input ≤ 6k, output ≤ 2k | < 2.5s | < $0.10/turn |
| `get_channel_overview` | input ≤ 5k, output ≤ 1k | < 700ms | < $0.04/turn |
| `trigger_etl_refresh` | input ≤ 4k, output ≤ 500 | < 300ms (Redis) | < $0.02/turn |
| **Session aggregate (4 calls)** | — | — | **< $0.50/session** (per spec NFR) |

Recorded via existing `copilot_llm_call` table (no new code).

### 4.6 No new LangGraph state shape

The 3 tools consume the existing copilot supervisor graph (`build_deep_agent_graph`) — they are leaves under the existing `tool_executor` node. NO new `State` keys, NO new edges, NO new subagents. (Anti-duplication: tools live in the existing analytics group.)

### 4.7 R23 owner_eligibility

All AGENTIC tickets (T-1, T-3, T-4) `production_code: true` → **Opus 4.7 required**. Sonnet/opencode banned. Tests-only tickets (T-5 alignment test) `production_code: false` → Sonnet OK.

## 5 · Cross-stack contract test (BE Pydantic ↔ FE zod alignment)

`backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py` (NEW). Reads:
- BE `_analytics_inputs.py::StageFilterParams.model_json_schema()`
- FE `frontend/src/features/growth-studio/schemas/stage-filter-params.schema.ts` (parsed via JSON-schema export — zod schema serialized via `z.toJSONSchema(stageFilterParamsSchema)` written to a generated artifact at lint time)

**Implementation note for builder-frontend**: add a `npm run schema:export` script that emits `frontend/dist/growth-studio-zod-schemas.json` consumed by the BE arch test. Asserts shape equivalence: required fields, allowed values per enum, `extra="forbid"` ↔ `.strict()`.

If alignment drifts → arch test FAILS → builds fail.

## 6 · Default-flip audit (R12 anti-default-flip-audit)

This story does **NOT** flip any feature flag default. Section 9.5 of the contract template marks: `[x] No aplica — CONTRACT no flipea defaults side-effect`.

## 7 · Migration plan (atomic in single PR)

1. **Phase A — RED tests first** (T-1 BE, T-2 FE):
   - Write Pydantic input schemas + tool RED tests (BE)
   - Write zod schemas + RED unit tests (FE)
   - Cross-stack contract test RED (T-5) — fails because tools don't exist
2. **Phase B — GREEN BE** (T-1 cont.): implement 3 tools + EtlRefreshGuard. Tests pass.
3. **Phase C — GREEN FE** (T-2 cont.): implement 5 actions + registry. Schema tests pass.
4. **Phase D — Agentic registration + golden update** (T-3): wire tools in `ANALYTICS_TOOLS`, regenerate golden (`UPDATE_GOLDEN=1`), `get_funnel_metrics` deleted in same commit.
5. **Phase E — Eval goldens** (T-4): add 3 quality goldens; verify with `RUN_LLM_JUDGE=0` stub default.
6. **Phase F — Cross-stack contract test verification** (T-5): GREEN.
7. **Phase G — Playwright smoke regression** (T-6): re-run growth-studio smoke; ensure 2A behavior preserved + new actions render in chat E2E test.
8. **Phase H — Verify full suite + bundle delta** (T-7): full BE + FE suite + arch fitness + bundle Δ ≤ 5%.

## 8 · Coordination cross-story

| Coordination | Status | Resolution |
|---|---|---|
| Story 2A `actions/`+`schemas/` placeholders | **DONE** (commit `828bb3dc` shipped `.gitkeep`) | 2B replaces `.gitkeep` with real files |
| Story 1 shell allowlists scope-keyed | **DONE** (commit `bb8683b3`) | 2B reuses `KNOWN_VIOLATIONS_GROWTH = new Set()` (drained by 2A T-5) |
| Story 1 VR helpers shared | **DONE** | 2B Playwright smoke (T-6) reuses 2A VR baselines |

## 9 · Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Golden update introduces routing regression | medium | Builder runs full `tests/modules/copilot/golden/` suite + manual `UPDATE_GOLDEN=1` review. Eval scenario 1 (stage-query-happy.json) covers routing decision. |
| `EtlRefreshGuard` Redis fail-open masks legit rate-limit bug | low | Structlog warning + emit `etl_refresh_guard_redis_unavailable_fail_open` metric; ops alert thresholds (Prometheus query, out of scope this story). |
| BE tools cascade Tier 1→3 explodes p95 on cold cache | medium | Tier 3 timeout = 5s with graceful fallback to Tier 2 + `truncated=true` (per spec scenario 3). |
| Action registry collision with existing form-runtime keys | low | Namespaced keys `growth.*` (no overlap with `brand.*` or `offer.*`). Idempotent `hasAction()` check. |
| Adversarial input bypasses Literal enum | low | `extra="forbid"` + `strict()` mirror; arch test §5 enforces. Scenario 4 covers 4 attacks. |

## 10 · Capability + module narrative updates (post-merge, R32 + R33)

`docs/product/capabilities/analytics/growth-studio-copilot-actions.yaml` (NEW):
```yaml
capability_id: growth-studio-copilot-actions
name: "Growth Studio — Acciones del Copilot"
status: shipped     # at merge
shipped_at: <merge_date>
modules: [analytics, copilot]
stories: [growth-studio-actions-schemas-real]
description: |
  El copilot puede consultar KPIs por stage / canal y disparar refrescos ETL ad-hoc
  (con rate limit 3/hora + confirmación obligatoria si > 1 refresh en la última hora).
  3 tools reemplazan get_funnel_metrics legacy.
acceptance_evidence:
  - "backend/tests/modules/copilot/application/tools/test_analytics_tools_*.py"
  - "frontend/src/features/growth-studio/{actions,schemas}/__tests__/*"
  - "backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py"
  - "backend/tests/quality/golden/growth_studio_actions/*.json"
```

`docs/product/modules/analytics.md` § Copilot integration: add 1 paragraph (Spanish neutro) describing the 3 actions + 4 schemas + cost target. PM closes capability promotion at merge.

## 11 · Hand off

state: refined → **ready** (post `04-validators` + `05-guidelines` + `06-tickets` cierre — this commit).
next: `/dev-team` toma T-1 (Conv 2 autonomous build). 7 tickets ordered. Sequential build (BLOCKED hasta 2A done — confirmed done 2026-05-07 commit `1e517b09`).

## 12 · Research notes (DATE-AWARE)

Architect run on **2026-05-08** (date captured via `date -u +%Y-%m-%d`).

Sources consulted:
- LangChain `@tool` decorator with Pydantic args_schema — `https://docs.langchain.com/oss/python/langchain/` accessed 2026-05-08. Confirms `args_schema=PydanticModel` for input validation at tool dispatch time; `extra="forbid"` rejects payload-key smuggling. Used for adversarial scenario 4 defense.
- LangGraph 2.0 `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` — already in use by copilot orchestrator; no new checkpointer needed for this story.
- Anthropic prompt caching — N/A (no new system prompt slot for this story; tools live in existing `analytics` group inside slot 3 `tools_hint`).
- Redis sorted-set sliding window pattern — confirmed via `OutboundRateLimiter` existing implementation (PR-2 / PI-1 S0). EXTEND via composition (anti-duplication).
- zod `.strict()` ↔ Pydantic `extra="forbid"` parity — confirmed via zod docs accessed 2026-05-08.

Knowledge cutoff disclosure: Opus 4.7 cutoff = Jan 2026. All patterns referenced are pre-cutoff and stable in the codebase. No live WebSearch needed for this story (no novel external integrations).

## 13 · Open questions (none — all 8 ratified by Chris 2026-05-07)

(Ratification log preserved in `01-spec.md` § Ratification log Q1-Q8.)
