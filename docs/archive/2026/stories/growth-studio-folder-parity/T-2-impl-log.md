# T-2 Impl Log — growth-studio-folder-parity

**Ticket:** T-2 — Phase 2 Factory dispatchers + sections + routes thin delegate
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T00:45:00Z
**Estimate:** 3h
**Acceptance validators:** scenario_1_canonical_files_unit, integration_e2e_growth_smoke (DEFERRED — Playwright service paused), fe_typecheck, fe_lint_growth
**Depends on:** T-1 (DONE — commit 9343fd61 + cabf4983)

## Plan

Factory dispatchers + sections pages + Server Component thin delegate routes.

- NEW `frontend/src/features/growth-studio/pages/stage-slugs.ts` + `StageDispatcher.tsx`
- NEW `frontend/src/features/growth-studio/pages/channel-slugs.ts` + `ChannelDispatcher.tsx`
- NEW `frontend/src/features/growth-studio/pages/sections/{atraccion-captura,nutricion-oportunidad,ventas,adopcion,expansion-evangelizacion}-page.tsx` (5 files)
- MODIFY `frontend/src/app/(main)/[tenantId]/(dashboard)/growth-studio/page.tsx` + `[stage]/page.tsx` — Server Component delgado import StageDispatcher
- Tests `StageDispatcher.test.tsx` + `ChannelDispatcher.test.tsx` (vitest unit)

PLAYWRIGHT NOTE: `integration_e2e_growth_smoke` validator requires Playwright. Service PAUSED (Chris RAM constraint). Builder defers Playwright validator to T-8 (verification phase) bundled run. Mark in iteration_log.

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iter 1 — TDD RED phase (builder a8cfefe0dd444a8ee, claude-sonnet)

**RED tests written first:**
- `src/features/growth-studio/__tests__/StageDispatcher.test.tsx` (6 tests — render correct section per stage slug)
- `src/features/growth-studio/__tests__/ChannelDispatcher.test.tsx` (7 tests — lazy load correct dashboard per channel)

Tests fail with import errors (Dispatcher files don't exist yet) → RED confirmed.

### Iter 1 — GREEN phase

**Files written:**
- `src/features/growth-studio/pages/stage-slugs.ts` — re-export StageSlug + STAGE_REGISTRY accessors
- `src/features/growth-studio/pages/channel-slugs.ts` — re-export ChannelSlug + CHANNEL_REGISTRY accessors
- `src/features/growth-studio/pages/StageDispatcher.tsx` — Client Component switch render section por stage slug, lazy import sections
- `src/features/growth-studio/pages/ChannelDispatcher.tsx` — Client Component lazy load via DASHBOARD_COMPONENT_MAP
- `src/features/growth-studio/pages/sections/atraccion-captura-page.tsx`
- `src/features/growth-studio/pages/sections/nutricion-oportunidad-page.tsx`
- `src/features/growth-studio/pages/sections/ventas-page.tsx`
- `src/features/growth-studio/pages/sections/adopcion-page.tsx`
- `src/features/growth-studio/pages/sections/expansion-evangelizacion-page.tsx`

**Routes thin Server Component delegate (11 files modified):**
- `app/(main)/[tenantId]/(dashboard)/growth-studio/{atraccion-captura,nutricion-oportunidad,ventas,adopcion,expansion-evangelizacion}/page.tsx` — delega `<StageDispatcher slug="..." />`
- `app/(main)/[tenantId]/(dashboard)/growth-studio/{stage}/[channelSlug]/page.tsx` (5 files) — delega `<ChannelDispatcher .../>`
- `app/(main)/[tenantId]/(dashboard)/growth-studio/channel/[channelSlug]/page.tsx` — channel dispatcher generic

### Iter 1 — Builder cap reached (mid-cleanup)

Builder agent cap_reached at 116k tokens / 1237s duration mid lint cleanup. NO blocked, NO sentinel — just timeout. Orchestrator (Opus runtime) takes over closure.

### Iter 2 — Orchestrator closure (manual)

**Issue identified:** Arch fitness `test-feature-structure.test.ts` flagged `features/growth-studio/pages` non-canonical (KNOWN_NONSTANDARD allowlist not updated for growth-studio). Pre-existing brand-studio + offer-studio + settings allowlisted; growth-studio missing.

**Fix applied:** added `"growth-studio": ["schemas", "actions", "pages"]` to KNOWN_NONSTANDARD with justification comment (factory propia adapter mode, ratificado Chris 2026-05-07). Pattern matches brand/offer convention.

### Iter 2 — Validator results (final)

| Validator | Status | Notes |
|---|---|---|
| `fe_typecheck` (`tsc --noEmit`) | PASS — 0 errors | |
| `fe_lint_growth` (`eslint src/features/growth-studio/`) | PASS — 0 errors, 1186 warnings (pre-existing, no `--max-warnings 0` flag) | |
| `scenario_1_canonical_files_unit` (StageDispatcher + ChannelDispatcher + folder-parity) | PASS — 31/31 tests | 6 + 7 + 18 |
| `fe_arch_fitness_full` (25 files / 51 tests) | PASS — 51/51 | post allowlist update |
| `integration_e2e_growth_smoke` (Playwright) | DEFERRED | Playwright service paused — bundled to T-8 verification |

### Playwright deferral

- `integration_e2e_growth_smoke` validator (5 stage routes Playwright smoke) — DEFERRED to T-8 verification phase.
- Reason: Playwright service paused (Chris RAM constraint).
- T-8 runs validator bundled with all `visual_*_e2e` validators when service resumes.
- Acceptance closure: 4 of 4 non-Playwright validators GREEN; 1 of 1 Playwright validator deferred → flagged for T-8 closure.

### Cap reached note (informational, not a block)

Builder agent (a8cfefe0dd444a8ee) hit cap mid-prettier/eslint loop after passing all functional + arch validators. Orchestrator manually verified state + applied trivial allowlist fix. No re-spawn required. Total iter for ticket: 2 (1 builder + 1 orchestrator closure).
