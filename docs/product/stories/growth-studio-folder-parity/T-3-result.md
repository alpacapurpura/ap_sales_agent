# T-3 Result — Phase 3: 4-Tier Rename Break-and-Fix Atomic

**Story:** growth-studio-folder-parity
**Ticket:** T-3
**State:** pushed
**Date:** 2026-05-07

## Commits

| # | SHA | Description |
|---|---|---|
| Commit 1 (Phase 3a) | `253e9ef1` | `refactor(growth-studio): rename tier0 to pages/tiers/tier0-summary.ts (T-3 Phase 3a — git mv puro)` |
| Commit 2 (Phase 3b) | `34221dfc` | `refactor(growth-studio): rewire tier wrappers + consumer imports (T-3 Phase 3b)` |

## Files changed

| File | Change |
|---|---|
| `frontend/src/features/growth-studio/components/metrics-dashboard/hooks/use-stage-summaries.ts` | MOVED (git mv) |
| `frontend/src/features/growth-studio/pages/tiers/tier0-summary.ts` | NEW (moved + imports fixed + export renamed) |
| `frontend/src/features/growth-studio/pages/tiers/tier1-overview.ts` | NEW (wrapper re-export) |
| `frontend/src/features/growth-studio/pages/tiers/tier2-group-detail.ts` | NEW (wrapper re-export) |
| `frontend/src/features/growth-studio/pages/tiers/tier3-stage.ts` | NEW (wrapper re-export, 9 hooks) |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/growth-studio/layout.tsx` | Consumer import updated |
| `frontend/src/__tests__/architecture/test-hook-location.test.ts` | Added `tiers/` dir exemption per AD5 |

## Validator results

| Validator | Result |
|---|---|
| `fe_typecheck` | PASS (0 tsc errors) |
| `fe_lint_growth` | PASS (0 eslint errors) |
| `fe_arch_fitness_full` | PASS (51/51 tests) |
| Canonical files (18/18) | PASS |
| Growth-studio full suite (645) | PASS |
| `integration_e2e_growth_smoke` | DEFERRED → T-8 (RAM constraint) |

## Key decisions

- **Naming:** `tier0-summary.ts` (with `tier` prefix) per authoritative test gate, overriding ticket deliverable text `0-summary.ts`
- **Arch test exemption:** Added `tiers/` dir to hook-location exemption list (AD5-justified, not allowlist growth)
- **Break-and-fix:** No legacy shim for `useStageSummaries` — consumers update to `useTier0Summary` directly per AD5 contract
- **Tiers 1-3:** Wrapper re-exports with `@deprecated` jsdoc for 1-ciclo deprecation window
