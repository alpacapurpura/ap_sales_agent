---
story_id: growth-studio-actions-schemas-real
outcome: growth-copilot-layout-unification
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md
last_modified: 2026-05-07T04:15:00Z
next_action: "/architect orchestrator → produce ready package CON sub-architects /architect-be (3 BE tools NEW: get_stage_metrics REPLACE legacy + get_channel_overview + trigger_etl_refresh con confirmation flow + metric-catalog endpoint + RateLimiter reuse) + /architect-fe (3 action React components + 4 zod schemas + 2 SSoTs contract test) + /architect-agentic (copilot tool registration + legacy migration eval goldens). Sequential build: BLOCKED hasta 2A done."
ratified_by_chris: true
ratified_at: 2026-05-07T04:15:00Z
spawned_at: 2026-05-07T03:30:00Z
spawned_by: /po (sesión refining unification 2nd pass — split de growth-studio-architectural-parity)
parallel_safe: false
parallel_safe_with: []
blocked_reason: "Sequential dependency on growth-studio-folder-parity (2A) — factory dispatchers + folders must exist first."
blocked_by: ["growth-studio-folder-parity"]
audit_iterations: 0
hotfix_metadata:
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
---

# Story scope — Story 2B (real actions + real schemas)

**Tipo:** service-story (FE actions + zod schemas — sin UI change visible)
**Skill spec:** `/po`
**Module primario:** `analytics` (FE: `frontend/src/features/growth-studio/`)
**Module secundario:** `copilot` (consumer de las actions)

## Origin

Split decision (Chris ratified 2026-05-07): scope original de
`growth-studio-architectural-parity` excedía cap (≤10 tickets/story).
Refactor estructural (folders + factory + cleanup) y feature work (real
actions/schemas + ETL trigger + export) son fases distintas.

- Story 2A (`growth-studio-folder-parity`) — refactor estructural
- Story 2B (este file) — real actions + real schemas, sequential

## Scope 2B (qué SÍ entra)

### Real actions (4)

1. **`queryStageMetrics(stage, channel?, period?)`** — copilot tool call,
   retorna KPIs del stage (con filtro opcional canal + período).
2. **`queryChannelOverview(channel)`** — copilot tool call, retorna
   overview canal específico (YouTube/Mail/Meta/etc dashboard data).
3. **`triggerETLRefresh(channel)`** — copilot tool call, dispara
   re-extracción ETL para canal (con rate-limit + cost guard).
4. **`exportStageReport(stage, format)`** — copilot tool call, exporta
   reporte stage (formato PDF/CSV).

### Real zod schemas (4)

1. **`stage-filter-params.schema.ts`** — valida filtros (period, channel,
   group) en queries cross-stage.
2. **`channel-config.schema.ts`** — valida shape registry channel (slug,
   dashboard, kpis, color) — driver del registry SSoT.
3. **`kpi-selection.schema.ts`** — valida selección KPIs custom user
   (futura feature dashboard custom).
4. **`tier-loading.schema.ts`** — valida payload tier0/tier1/tier2/tier3
   endpoints (API contract validation runtime).

### Constraints adicionales

- Cada action MUST aparecer en copilot tool registry (`copilot-expert`
  skill territorio — coordinación)
- Cada schema MUST consumirse por al menos 1 caller real (no orphans)
- `triggerETLRefresh` necesita budget guard + rate limiter (riesgo cost)

## Scope 2B (qué NO entra)

- ❌ Folder parity / factory dispatchers — story 2A
- ❌ Legacy purge config/context/__mocks__ — story 2A
- ❌ Arch fitness extension — story 2A
- ❌ Visual changes — story 3 (parked)
- ❌ Nuevos endpoints BE — analytics module ya tiene endpoints; las
  actions consumen los existentes
- ❌ Custom dashboard UI per-tenant — feature futura

## Constraints heredados

- FSD-Lite: actions consumen `lib/api/*`, NO directamente `fetch`
- Tenant isolation en cada action (X-Tenant-ID via fetchClient)
- Currency handling: monetary KPIs respetan source currency (per
  `.claude/rules/currency-handling.md`)
- Master data: timezone tenant via `useTenantLocale` (per
  `.claude/rules/master-data.md`)
- Spanish neutro en messages user-facing (errors, confirmations)
- TDD obligatorio: zod schema tests RED antes implement; action contract
  tests RED antes implement
- Copilot tool registration MUST seguir patrón existente (`copilot-expert`
  skill `references/`)

## Open questions (pre-spec)

1. ¿`triggerETLRefresh` requiere confirmación user copilot agent o
   auto-trigger? (Cost implication.)
2. ¿`exportStageReport` server-side render PDF (heavy) vs client-side
   CSV (light)? Architect decide.
3. ¿KPI selection schema valida contra `metric_catalog` SSoT BE o FE
   tiene mirror constants? (`metrics-expert` skill territory.)
4. ¿Rate limit `triggerETLRefresh` per-tenant N/hour configurable o
   hardcoded?
5. ¿Schemas exportados como types TS (z.infer) o también como JSON
   schema runtime (RPC)?

## Bitácora

- 2026-05-07 03:30 — `/po` (sesión refining unification 2nd pass) creó
  folder + checkpoint.md (state=refining). Split de
  `growth-studio-architectural-parity` ratificado por Chris.
  Sequential dependency en 2A. Phase=PO_DRAFTING.

## Notas

- `parallel_safe: false` (depende de 2A entregar factory + folders)
- Arrancar refining 2B en paralelo a 2A es OK (spec ratification puede
  cerrar antes que 2A entregue código). BUILD de 2B sequential después
  de BUILD de 2A.
- Architect Opus 4.7 OBLIGATORIO (cross-module copilot ↔ analytics)
- Builder agentic OBLIGATORIO para copilot tool registration (Opus 4.7
  per R23 production_code=true en agentic surface)
