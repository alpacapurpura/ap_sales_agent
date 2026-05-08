# T-4 Impl Log — growth-studio-folder-parity

**Ticket:** T-4 — Phase 4 Legacy purge config/+context/+__mocks__/ + VR replacement
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T21:00:00Z
**Estimate:** 3h
**Acceptance validators:** scenario_3_visual_bowtie_pixel_perfect, visual_bowtie_pixel_perfect_e2e (Playwright DEFERRED), fe_typecheck, fe_lint_growth
**Depends on:** T-3 (DONE — commit 253e9ef1 / 34221dfc / 7266a973)
**Cross-story dependency:** story-1::T-8 (VR helpers shipped) — NOT YET LANDED.

## Plan

Migrate legacy folders, delete entire dirs, defer Playwright VR replacement until story 1 T-8 lands.

- Step 0 GATE: grep cross-codebase config/ consumers
- MIGRATE config/ content → lib/registries/ (atomic find-replace mismo commit)
- MIGRATE context/ content → growth-studio/store/sync-store.ts (zustand local) + hooks/ si aplica
- MIGRATE __mocks__/ → __tests__/__mocks__/ (update 9 dynamic-import consumers en stage-detail-api.ts)
- DELETE growth-studio/config/, context/, __mocks__/ (entire folders)
- VR REPLACEMENT GATE: si story 1 T-8 NOT LANDED → keep legacy `__tests__/visual-regression-drawer-bowtie.test.tsx`; defer e2e/visual/growth-studio-bowtie.spec.ts to follow-up commit cuando T-8 merge.

PLAYWRIGHT NOTE: visual_bowtie_pixel_perfect_e2e DEFERRED to T-8 verification phase (Playwright service paused).

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### iter-1 — Full execution

**Skills consulted:**

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, ESLint config, arch fitness ratchet | Canonical paths: `lib/` for display registries, `store/` for context migration, `__tests__/__mocks__/` for mock data |
| `tessl__react-patterns` | Provider pattern validation | GrowthSyncProvider pattern retained (React Context, not Zustand — mutation-based state) |
| `tessl__nextjs-app-router-modularization` | layout.tsx import update | Server/Client boundary unchanged |
| `metrics-expert` | channel-stage-map supersession, canonical slugs | CHANNEL_STAGE_MAP superseded by lib/registries/channel-registry.ts getStageForChannel() |

**Step 0 GATE — Consumer grep:**

config/ consumers:
- `ChannelRowMetrics.tsx` → `config/channel-display-registry`
- `ChannelRow.tsx` → `config/channel-display-registry`
- `AttractionTrendChart.tsx` → `config/channel-chart-config`
- `config/__tests__/` (internal — migrated/rewritten)

context/ consumers:
- `SyncProgressDialog.tsx` → `context/growth-sync-context`
- `AttractionCaptureDetail.tsx` → `context/growth-sync-context`
- `layout.tsx` → `context/growth-sync-context`

__mocks__/ consumers:
- `stage-detail-api.ts` → 9× dynamic `import("../__mocks__/metrics-mock-data")`

**VR gate check:** `frontend/e2e/visual/growth-studio-bowtie.spec.ts` → NOT_EXISTS. Story-1 T-8 not yet landed → keep legacy VR test, defer Playwright VR.

**Migration decisions:**
- `config/channel-display-registry.ts` → `lib/channel-display-registry.ts` (verbatim)
- `config/channel-stage-map.ts` → SUPERSEDED by lib/registries/channel-registry.ts; no migration; test rewritten
- `config/channel-chart-config.ts` → PASS-THROUGH ELIMINATED; AttractionTrendChart imports direct from `@/lib/constants/channel-colors`
- `config/dashboard-sections.ts` → `lib/dashboard-sections.ts` (verbatim; 0 external consumers)
- `context/growth-sync-context.tsx` → `store/growth-sync-store.tsx` (.tsx for JSX content; same interface)
- `__mocks__/metrics-mock-data.ts` → `__tests__/__mocks__/metrics-mock-data.ts` (relative types path updated: `../` → `../../`)
- `stage-detail-api.ts` 9 dynamic imports updated; prettier auto-fixed line length

**Validators result:**
- `fe_typecheck`: 0 errors
- `fe_lint_growth`: 0 errors (1189 pre-existing warnings, baseline stable)
- `scenario_3_visual_bowtie_pixel_perfect` (vitest VR): 6/6 PASS
- Growth-studio __tests__ suite: 73/73 PASS (7 files)
- Architecture fitness: 51/51 PASS (25 files)

**State:** PUSHED — GREEN all validators.
