# 05-guidelines.md — Growth Studio Real Actions + Real Schemas (2B)

> Owner: `/architect`. Patterns required + forbidden + skills/rules to load + files in scope.
> Builders MUST read this BEFORE touching code. Auditors verify compliance.

---
story_id: growth-studio-actions-schemas-real
arch_version: 1
last_modified: 2026-05-08T00:00:00Z
links:
  spec: "01-spec.md"
  arch: "03-arch.md"
  validators: "04-validators.yaml"
  tickets: "06-tickets.yaml"
---

## 1 · Skills + rules to load (per ticket)

| Ticket | Skills (read first) | Rules (always-on) |
|---|---|---|
| T-1 (BE 3 tools + DTOs + EtlRefreshGuard) | `metrics-expert`, `backend-expert`, `tessl__graceful-degradation`, `tessl__fastapi`, `copilot-expert` | tenant-isolation, backend-ddd, anti-duplication, tdd-mandatory, copilot-resilience, copilot-observability, currency-handling, master-data, etl-extraction-contract, data-reliability, hotfix-repro-mandatory (N/A), pii-sanitisation |
| T-2 (FE 4 zod schemas + 5 action components + registry) | `frontend-expert`, `metrics-expert` (read schema endpoint shape) | frontend-fsd, frontend-quality, form-runtime-array (N/A but check), spanish-text, currency-handling, master-data, tdd-mandatory, anti-duplication |
| T-3 (Copilot tool registration + golden update) — AGENTIC Opus required | `copilot-expert`, `tessl__langgraph` | copilot-resilience, copilot-observability, anti-duplication, sales-agent-brand-voice (N/A but voice) |
| T-4 (Eval goldens + voice fidelity) — AGENTIC Opus required | `copilot-expert`, `sales-agent-expert` (voice grader pattern reuse) | spanish-text, copilot-observability, tdd-mandatory |
| T-5 (Cross-stack BE↔FE schema alignment arch test) | `backend-expert`, `frontend-expert` | architectural-fitness, tdd-mandatory |
| T-6 (Playwright smoke regression) | `playwright-expert`, `frontend-expert` | e2e-testing |
| T-7 (Verify full suite + bundle delta) | `backend-expert`, `frontend-expert` | architectural-fitness, debugging |

## 2 · Files in scope (NEW + MODIFIED)

### NEW

```
backend/src/modules/copilot/application/tools/_analytics_inputs.py            T-1
backend/src/modules/analytics/application/services/etl_refresh_guard.py        T-1

backend/tests/modules/copilot/application/tools/test_analytics_tools_stage.py        T-1
backend/tests/modules/copilot/application/tools/test_analytics_tools_channel.py      T-1
backend/tests/modules/copilot/application/tools/test_analytics_tools_tier_loading.py T-1
backend/tests/modules/copilot/application/tools/test_analytics_tools_security.py     T-1
backend/tests/modules/copilot/application/tools/test_etl_refresh_tool.py             T-1
backend/tests/modules/copilot/application/tools/test_analytics_tools_observability.py T-1
backend/tests/modules/analytics/application/services/test_etl_refresh_guard.py        T-1

frontend/src/features/growth-studio/schemas/stage-filter-params.schema.ts     T-2
frontend/src/features/growth-studio/schemas/channel-config.schema.ts          T-2
frontend/src/features/growth-studio/schemas/kpi-selection.schema.ts           T-2
frontend/src/features/growth-studio/schemas/tier-loading.schema.ts            T-2
frontend/src/features/growth-studio/schemas/index.ts                          T-2
frontend/src/features/growth-studio/schemas/__tests__/stage-filter-params.test.ts          T-2
frontend/src/features/growth-studio/schemas/__tests__/channel-config.test.ts               T-2
frontend/src/features/growth-studio/schemas/__tests__/kpi-selection.test.ts                T-2
frontend/src/features/growth-studio/schemas/__tests__/tier-loading.test.ts                 T-2
frontend/src/features/growth-studio/schemas/__tests__/stage-filter-params-security.test.ts T-2

frontend/src/features/growth-studio/actions/StageMetricsAction.tsx            T-2
frontend/src/features/growth-studio/actions/ChannelOverviewAction.tsx         T-2
frontend/src/features/growth-studio/actions/ETLRefreshAction.tsx              T-2
frontend/src/features/growth-studio/actions/ETLRateLimitedAction.tsx          T-2
frontend/src/features/growth-studio/actions/ETLConfirmAction.tsx              T-2
frontend/src/features/growth-studio/actions/registry.ts                       T-2
frontend/src/features/growth-studio/actions/index.ts                          T-2
frontend/src/features/growth-studio/actions/__tests__/{5 components}.test.tsx T-2
frontend/src/features/growth-studio/actions/__tests__/StageMetricsAction-large-volume.test.tsx T-2

backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py       T-5
frontend/scripts/export-zod-schemas.ts                                         T-5

backend/tests/quality/golden/growth_studio_actions/stage-query-happy.json     T-4
backend/tests/quality/golden/growth_studio_actions/etl-refresh-confirm.json   T-4
backend/tests/quality/golden/growth_studio_actions/etl-refresh-rate-limited.json T-4

frontend/e2e/visual/growth-studio-actions.spec.ts                              T-6  (visual project)
```

### MODIFIED

```
backend/src/modules/copilot/application/tools/analytics_tools.py              T-1, T-3 (rewrite — replace get_funnel_metrics)
backend/src/modules/copilot/application/tools/__init__.py                     T-3 (no-op if it stays bare; touch only if registry import path changes)
backend/tests/modules/copilot/golden/snapshots/route_tool_selection.json      T-3 (UPDATE_GOLDEN=1)
frontend/src/features/growth-studio/README.md                                 T-7 (un-pending Story 2B note)
docs/product/capabilities/analytics/growth-studio-copilot-actions.yaml         T-7 / merge (capability promote → shipped)
docs/product/modules/analytics.md                                              T-7 / merge (capability listing auto-refreshes via marker; narrative paragraph optional)
```

### DELETED at T-3 commit

```
(in same file rewrite)  get_funnel_metrics function    backend/src/modules/copilot/application/tools/analytics_tools.py
```

## 3 · Patterns required

### 3.1 BE — Pydantic v2 input + LangChain `@tool(args_schema=…)`

```python
@tool(args_schema=StageFilterParams)
def get_stage_metrics(stage: str, channel: str | None = None, period: str = "30d") -> str:
    """Bilingual docstring (Spanish neutro + English keywords for LLM)."""
    tenant_id = get_tenant_id()                # from src.core.context
    if not tenant_id:
        return json.dumps({"error": "no_tenant_context"})
    # Use existing stage service composing tier-1 endpoint
    # Wrap in try/except — never raise to LLM
```

### 3.2 BE — `EtlRefreshGuard` composition over `OutboundRateLimiter`

Sliding window keyed `etl_refresh:{tenant_id}:{channel}`, 1-hour window, default 3/window. Confirmation threshold 1. **Soft-fail Redis** per `tessl__graceful-degradation` (fail-open + structlog warning).

### 3.3 BE — Tenant isolation everywhere

```python
tenant_id = get_tenant_id()              # X-Tenant-ID middleware
if not tenant_id:
    return json.dumps({"error": "no_tenant_context"})
# all queries filter by tenant_id; NEVER trust caller payload
```

### 3.4 FE — Action component shape

- `"use client"` directive at top
- Imports `useTenantLocale` for currency/timezone
- Imports `formatMoney` / `formatTenantDate*` for display
- Receives `payload` typed via `ActionComponentProps<T>`
- `aria-label` on Card; `role="alert"` on rate-limited / confirm
- Spanish neutro user-facing strings (tuteo, no voseo)
- NO inline `fetch()` — use `fetchClient` if imperative call needed (only ETLConfirmAction)

### 3.5 FE — Zod schema mirrors BE Pydantic

- `.strict()` ↔ Pydantic `extra="forbid"`
- `z.enum(STAGE_REGISTRY.map((s)=>s.slug))` consumes 2A SSoT, never hardcode
- Adversarial defense: regex on string fields; enum on slugs

### 3.6 FE — Action registry pattern (mirror brand-studio)

- Idempotent `bootstrapGrowthStudioActions()`
- `hasAction(key)` check before registerAction
- Side-effect import from `schemas/index.ts`
- Keys namespaced `growth.*`

### 3.7 Agentic — Tool registration

- Tool added to `ANALYTICS_TOOLS` list (existing group)
- `_BASE_TOOL_GROUPS["analytics"]` already includes `ANALYTICS_TOOLS` — NO change
- `growth-studio` route already maps to `["analytics", ...]` — NO change
- Golden update via `UPDATE_GOLDEN=1` after change

### 3.8 TDD — RED first per ticket

- T-1: BE Pydantic input schemas RED → tools RED → guard RED → GREEN
- T-2: FE zod schemas RED → 5 action components RED → registry RED → GREEN
- T-3: Eval golden update is INTENTIONAL (regenerate via UPDATE_GOLDEN, commit diff with intent message)
- T-4: 3 voice fidelity goldens RED (stub default returns score < 0.85) → GREEN with corrections
- T-5: Cross-stack alignment test RED until both T-1 + T-2 done

## 4 · Patterns FORBIDDEN

| Forbidden | Why | What to do instead |
|---|---|---|
| Hardcoded stage / channel slugs in actions / schemas | Drifts from 2A SSoT | Import `STAGE_REGISTRY.map((s)=>s.slug)` from `lib/registries/stage-registry.ts` |
| New Pydantic model files outside `_analytics_inputs.py` | Anti-duplication | Add to existing module |
| New rate limiter abstraction | `OutboundRateLimiter` exists | Compose via `EtlRefreshGuard` |
| New analytics endpoints | All needed endpoints exist | REUSE `refresh_channel_metrics`, `get_stage_overview`, `get_channel_dashboard`, `get_metric_catalog` |
| `fetch()` raw in action components | Bypasses tenant isolation | Use `fetchClient` |
| `formatMoney(value, "USD")` hardcoded | Currency drift | `formatMoney(value, payload.currency ?? tenantLocale.currency)` |
| `datetime.utcnow()` / `DateTime()` without timezone | Master-data violation | `utc_now()` + `DateTime(timezone=True)` |
| Voseo in Spanish UI strings | Latin neutro rule | tuteo glossary; lint regex catches |
| Default flag flips | Not in scope this story | N/A — verifier `default_flips_audited` marks "no aplica" |
| Cross-module imports outside `shared/links/` | DDD boundary | All cross-module via existing ports / endpoint composition |
| `get_funnel_metrics` calls in any new code | Legacy | REPLACED — atomic migration commit |
| New Redis abstraction layer | Anti-duplication | Reuse existing pipeline pattern |
| Mirror tenant data in tools (caller-supplied tenant_id) | Cross-tenant leak | Pydantic `extra="forbid"` rejects payload tenant_id; tools read from `get_tenant_id()` context |
| Skipping `RUN_LLM_JUDGE=1` for goldens before merge | Voice drift undetected | Stub default OK; ratchet at merge by Chris |
| `git add .` / `-A` / `-u` | Parallel sessions | Stage by name only |
| Touch files outside scope (especially `metrics-dashboard/**` invariants) | Story 2A scope leak | If path isn't in § 2 above, don't touch |

## 5 · Code-quality gates (must keep passing)

- BE coverage threshold ≥ 43%
- FE coverage threshold ≥ 20% (all categories)
- Ruff line-length 120, format with double quotes + spaces
- TS strict mode; `tsc --noEmit` 0 errors
- Arch fitness allowlists shrink only

## 6 · Reference paths (read on demand)

- Brand actions registry pattern (mirror): `frontend/src/features/brand-studio/actions/registry.ts`
- 2A SSoT registries (consume): `frontend/src/features/growth-studio/lib/registries/{stage,channel,dashboard}-registry.ts`
- Existing copilot tool registry pattern: `backend/src/modules/copilot/application/tools/registry.py`
- Existing analytics endpoints (compose): `backend/src/modules/analytics/api/metrics.py:309,340,771,832,866`
- Existing rate limiter (compose): `backend/src/shared/billing/application/rate_limiter.py`
- Existing eval goldens harness: `backend/tests/quality/golden/`
- BE/FE schema alignment example (template): N/A first of its kind for growth-studio — pattern lifted from `tessl__fastapi` docs (Pydantic JSON schema export)

## 7 · Anti-checklist before push

- [ ] All RED tests written FIRST (TDD)
- [ ] No hardcoded stage / channel slugs
- [ ] `EtlRefreshGuard` is the ONLY new rate-limit class; reuses Redis pipeline pattern
- [ ] `_analytics_inputs.py::*Params` use `extra="forbid"` and `Literal[...]` enums
- [ ] All FE action components use `useTenantLocale()` + `formatMoney` (no `'USD'`)
- [ ] All Spanish strings tuteo; voseo lint passes
- [ ] `get_funnel_metrics` deleted (grep clean)
- [ ] Golden updated with intentional commit message
- [ ] BE arch fitness all green
- [ ] FE arch fitness all green incl. `test-studio-structure-parity`
- [ ] Cross-stack alignment test green
- [ ] Bundle delta ≤ 5%
- [ ] capability YAML drafted (status=shipped at merge)
- [ ] No `.env*` / credentials staged
- [ ] No `git pull` / `--force` / `revert` without approval
