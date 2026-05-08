# T-3 Impl Log — growth-studio-folder-parity

**Ticket:** T-3 — Phase 3 4-tier rename break-and-fix atomic
**Owner:** claude-sonnet (builder-frontend)
**Assigned at:** 2026-05-08T20:30:00Z
**Estimate:** 2h
**Acceptance validators:** fe_typecheck, fe_lint_growth, fe_arch_fitness_full, integration_e2e_growth_smoke (DEFERRED — Playwright service paused)
**Depends on:** T-2 (DONE — commit 566d1d28)

## Plan

Atomic git mv tier0-* → pages/tiers/0-summary.ts. R9 git mv puro commit FIRST, expansion second commit.

- MOVE existing `tier0-*.ts` file content → `frontend/src/features/growth-studio/pages/tiers/0-summary.ts` (single git mv preserving history)
- WRAPPER re-exports: `pages/tiers/{1-overview,2-group-detail,3-stage}.ts` re-export from existing locations (deprecation 1 ciclo). Existing files marked `@deprecated` jsdoc.
- Update consumers: search-replace imports `tier0-*` → `pages/tiers/0-summary`
- Atomic 2-commit pattern: (1) `git mv` puro, (2) re-exports + consumers update

PLAYWRIGHT NOTE: `integration_e2e_growth_smoke` validator DEFERRED to T-8.

TDD RED→GREEN. Loop hasta validators GREEN o cap_reached.

## Iteration log

### Iter 1 — 2026-05-07

#### Skills consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Always-on — runtime quality checklist, FSD-Lite, arch fitness | Confirmed R9 atomic 2-commit pattern; `pages/tiers/` exemption is legitimate arch decision (AD5), not allowlist addition |
| `tessl__react-patterns` | Always-on | Pure refactor, no new component surfaces |
| `tessl__shadcn-ui` | Always-on | No new Shadcn components in T-3 |
| `tessl__tailwind` | Always-on | No styling changes |
| `metrics-expert` | Touching `features/growth-studio/` — 4-tier loading contract | Confirmed tier naming: tier0=bowtie summary, tier1=overview cache, tier2=group-detail cache, tier3=stage DB; break-and-fix (no shim) for tier0 per AD5 |

#### Findings

**Naming discrepancy resolved:** Ticket deliverables (06-tickets.yaml) said `0-summary.ts` (no `tier` prefix). Authoritative gates (`folder-parity-canonical-files.test.ts` + `03-arch-fe.md`) both specify `tier0-summary.ts`. Decision: follow tests and arch spec.

**Tier0 source location:** `components/metrics-dashboard/hooks/use-stage-summaries.ts`
Export: `useStageSummaries`. Consumer: `layout.tsx`.

**Tiers 1-3 source hooks:** already canonical in `hooks/`:
- `hooks/use-stage-overview.ts` → `useStageOverview`
- `hooks/use-group-detail.ts` → `useGroupDetail`
- `hooks/use-stage-detail.ts` → 8 stage hooks + `useStageTimeSeries`

#### Commit 1 (253e9ef1) — pure git mv

```bash
git mv frontend/src/features/growth-studio/components/metrics-dashboard/hooks/use-stage-summaries.ts \
        frontend/src/features/growth-studio/pages/tiers/tier0-summary.ts
```

No content edits in Commit 1. Preserves full blame/history.

#### Arch fitness issue + fix

`test-hook-location.test.ts` failed:
```
NEW hook location violations:
features/growth-studio/pages/tiers/tier0-summary.ts
```

Cause: `pages/tiers/` not in exemption list. Fix: added `if (parentDir === "tiers") continue;` — legitimate dir exemption (like `store/`), NOT an allowlist addition. Ratchet-safe because AD5 defines `pages/tiers/` as canonical location for 4-tier loading hooks.

#### Commit 2 (34221dfc) — re-exports + consumer updates

- `tier0-summary.ts`: fixed relative imports (`../../../` → `../../`), renamed export `useStageSummaries` → `useTier0Summary`
- Created `tier1-overview.ts`, `tier2-group-detail.ts`, `tier3-stage.ts` as wrapper re-exports with `@deprecated` jsdoc (1-ciclo deprecation per AD5)
- `layout.tsx`: updated consumer import and usage
- `test-hook-location.test.ts`: added `tiers/` dir exemption (arch-justified per AD5)

#### Validator results

| Validator | Result | Notes |
|---|---|---|
| `fe_typecheck` | PASS | 0 tsc errors |
| `fe_lint_growth` | PASS | 0 eslint errors; 1186 warnings all pre-existing |
| `fe_arch_fitness_full` | PASS | 51/51 tests (25 test files) |
| Canonical files test | PASS | 18/18 (tier0-tier3 all present, correct exports) |
| Growth-studio full suite | PASS | 645 tests |
| `integration_e2e_growth_smoke` | DEFERRED | RAM constraint per task spec → T-8 |

**Verdict: DONE. Pushing commits 253e9ef1 + 34221dfc.**
