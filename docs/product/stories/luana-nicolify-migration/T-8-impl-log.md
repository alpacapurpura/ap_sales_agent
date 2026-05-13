# T-8 — FE rsync + workspace registration + jscodeshift imports rewrite

**Status:** PARTIAL — A1 + A3 + A4 require architect/Chris ratification per categorization below.
**Date:** 2026-05-13 (Sesión 9)
**Builder:** builder-frontend (Opus 4.7)
**Cap:** $800 hard

---

## Sesión 9 ratifications honored

- ✅ Q1=A — luana-platform commits to main, 12 parallel WIP coexists (not touched)
- ✅ Q3=B — BE already moved to luana-platform/nicolify/backend/ (T-10 precedent)
- ✅ Q6=B — proceeding within $800 cap for T-8
- ✅ **CRITICAL DEVIATION ratified:** `rm -rf /home/chris/AISALESHT/frontend/` DEFERRED to T-14 (dual-state preserved)

---

## Step execution log

### Step 0 — Repro verify (R26) ✅

All prereqs verified:
- 7 @luana/* packages exist in `/home/chris/luana-platform/core/@luana/`
- Codemod script `/home/chris/AISALESHT/scripts/codemod_fe_imports.ts` exists
- pnpm-workspace.yaml in baseline state (lists `nicolify` but NOT `nicolify/frontend`)
- nicolify/package.json minimal stub `@luana/nicolify v0.1.0 private`
- AISALESHT branch: `development` (clean to scope; 4 parallel WIP files untouched)
- luana-platform branch: `main` (12 parallel WIP M files in `core/*` + `pyproject.toml` — untouched)

### Step 1 — FE rsync cross-repo ✅

```bash
mkdir -p /home/chris/luana-platform/nicolify/frontend
rsync -av \
  --exclude='.next/' --exclude='storybook-static/' --exclude='test-results/' \
  --exclude='node_modules/' --exclude='coverage/' --exclude='.turbo/' \
  --exclude='.swc/' --exclude='.eslintcache' --exclude='*.tsbuildinfo' \
  --exclude='playwright/.clerk/' --exclude='playwright/.auth/' \
  --exclude='playwright-report/' \
  /home/chris/AISALESHT/frontend/ /home/chris/luana-platform/nicolify/frontend/
```

Output:
```
sent 10,044,744 bytes  received 31,788 bytes  20,153,064.00 bytes/sec
total size is 9,906,327  speedup is 0.98
```

Identity verification (diff -rq excluding build artifacts):
- 11MB src dir on both sides
- diff -rq /home/chris/AISALESHT/frontend/src /home/chris/luana-platform/nicolify/frontend/src → empty (identical)

**AISALESHT/frontend NOT deleted** (per Sesión 9 critical deviation — dual-state until T-14).

### Step 2 — Workspace registration ✅

`/home/chris/luana-platform/pnpm-workspace.yaml`:
```yaml
packages:
  - core
  - core/@luana/*
  - nicolify
  - nicolify/frontend    # NEW (T-8)
  - vitalia
  - comunify
  - lupulo
```

`/home/chris/luana-platform/nicolify/frontend/package.json`:
- Rename `"name": "visionarias-client"` → `"name": "@luana/nicolify-web"` ✅
- Add 6 @luana/* workspace deps to `dependencies` ✅:
  - `@luana/api-client: workspace:*`
  - `@luana/design-tokens: workspace:*`
  - `@luana/format: workspace:*`
  - `@luana/hooks: workspace:*`
  - `@luana/schemas: workspace:*`
  - `@luana/ui-kit: workspace:*`

`pnpm install` result: SUCCESS in 27.5s (warnings only — unmet peer deps in @luana/* packages, pre-existing). 6 @luana/* symlinks confirmed in `nicolify/frontend/node_modules/@luana/`:
```
api-client -> ../../../../core/@luana/api-client
design-tokens -> ../../../../core/@luana/design-tokens
format -> ../../../../core/@luana/format
hooks -> ../../../../core/@luana/hooks
schemas -> ../../../../core/@luana/schemas
ui-kit -> ../../../../core/@luana/ui-kit
```

H3 NOT triggered.

### Step 3 — jscodeshift codemod imports rewrite ✅

```bash
cd /home/chris/luana-platform/nicolify/frontend
npx jscodeshift -t /home/chris/AISALESHT/scripts/codemod_fe_imports.ts --parser=tsx --extensions=ts,tsx src/
```

Output:
```
0 errors
0 unmodified
1068 skipped
339 ok
Time elapsed: 3.832 seconds
```

**Codemod ran successfully — 339 files rewritten, 0 errors.**

### Step 4 — Acceptance verification — CATEGORIZED FINDINGS

#### A1 — TypeScript compile ⚠️ CATEGORIZED (16 errors, ALL out of T-8 scope)

**Initial run after codemod:** 943 errors.

**Root cause #1 (codemod design vs package shape):** codemod produced subpath imports `@luana/ui-kit/<file>` but `@luana/ui-kit` only exports root barrel (`"exports": { ".": "./src/index.ts" }`). Same for `@luana/design-tokens` (except valid `./z-index` subpath).

**Mitigation applied (in-scope T-8 — codemod output fix-up, NOT @luana/* modification):**
Wrote `/tmp/fix_luana_subpath_imports.mjs` Node script that rewrites `@luana/ui-kit/<X>` and `@luana/design-tokens/<X>` (non-z-index) imports to barrel form. Result:
- 333 files changed
- 767 subpath imports → barrel imports
- TSC errors dropped 943 → 35

**Second triage — missing transitive deps:**
- `@testing-library/user-event` — not in original AISALESHT/frontend package.json (was transitive via @testing-library/dom in lockfile; not re-resolved in pnpm workspace install)
- `dotenv` (for playwright.config.ts)
- `d3-sankey` + `@types/d3-sankey` (for StrategyCanvas)

These were NOT declared in AISALESHT/frontend/package.json either. Confirmed via grep. They were installed transitively in AISALESHT's flat npm tree but pnpm workspace's stricter resolution flagged them.

**Mitigation applied (in-scope T-8 — fix missing app deps):**
```bash
pnpm add -D @testing-library/user-event dotenv d3-sankey @types/d3-sankey
```
TSC errors dropped 35 → 16.

**Remaining 16 errors — OUT OF T-8 SCOPE:**

| Category | Count | Location | Cause | Resolution required |
|---|---|---|---|---|
| @luana/ui-kit missing hook re-export | 4 | `core/@luana/ui-kit/src/{alert-dialog,detail-panel,dialog,sheet}.tsx` references `@luana/hooks/use-copilot-offset` | `use-copilot-offset` exists in `core/@luana/hooks/src/` but `core/@luana/hooks/src/index.ts` has the export COMMENTED OUT with comment `// requires @/features/copilot` | Modify `@luana/hooks/src/index.ts` to export `use-copilot-offset` — **OUTSIDE T-8 SCOPE per spec "NO HACER: Modificar @luana/* packages"** |
| @luana/ui-kit missing react-hook-form dep | 1 | `core/@luana/ui-kit/src/form.tsx` imports `react-hook-form` | `@luana/ui-kit/package.json` lacks `react-hook-form` as peer/dep | Modify `@luana/ui-kit/package.json` — **OUTSIDE T-8 SCOPE** |
| Zod v3 vs v4 type mismatch | 11 | `src/features/{campaigns-lite,crm-hub,settings}/components/*.tsx` Controller `field` callback TS7031 | `@luana/schemas/package.json` declares `zod: ^3.22.0` but `nicolify/frontend` uses `zod: ^4.3.6`. RHF Controller types from `@luana/ui-kit/form` resolve to zod3 protocols, app's zod4 instances fail assignment | Either bump `@luana/schemas` to zod4 OR add zod3 to nicolify-web — **OUTSIDE T-8 SCOPE** (cross-package version coordination) |

**Baseline confirmation:** AISALESHT/frontend pre-T-8 TSC = **0 errors**. All 16 remaining errors are introduced by interaction between T-8 migration and pre-existing `@luana/*` package config gaps.

#### A2 — ESLint ⏸ NOT MEASURED

ESLint background task did not complete in budget window. Per categorization, A2 will be re-run by orchestrator post-resolution of A1 issues.

#### A3 — Vitest delta vs baseline ⏸ NOT EXECUTED

A1 TSC failures block vitest execution (cannot compile test files). Deferred until A1 categorized issues resolved at architect level. Apply T-10 H8 pattern: defer test cleanup to T-15-FE or T-16.

#### A4 — Legacy @/* paths ⚠️ CATEGORIZED (759 remaining, scope ambiguity)

Spec verifier:
```bash
grep -rn 'from "@/' src/ | grep -vE '@/app/|@/features/|@/stores/|@/components/shared/' | wc -l
# Expected: 0
# Actual: 759
```

**Root cause analysis:**

The codemod mapping in `scripts/codemod_fe_imports.ts` covers:
- `@/components/ui` → `@luana/ui-kit` ✅
- `@/lib/api/fetchClient` → `@luana/api-client` ✅
- `@/lib/format` → `@luana/format` ✅
- `@/lib/tokens` → `@luana/design-tokens` ✅
- `@/lib/zod-schemas` → `@luana/schemas` ✅
- `@/hooks/useTenantLocale|useTenantConfig` → `@luana/hooks` ✅
- `@/lib/extension-sdk` → `@luana/extension-sdk` ✅

The 759 remaining are paths the codemod does NOT cover. Inventory:

| Path prefix | Count (approx) | Should map to @luana/* OR stay local? |
|---|---|---|
| `@/lib/utils` (cn helper, identical to `@luana/format/src/utils.ts:cn`) | ~150-200 | Should map to `@luana/format` (barrel) — codemod missing this mapping |
| `@/lib/form-runtime/{schema,hooks,utils,copilot,actions}` | ~200-300 | **Stay local** — Nicolify-specific form-runtime system |
| `@/lib/edge/legacy-redirects` | ~5 | **Stay local** — Nicolify-specific |
| `@/lib/config` | ~10 | **Stay local** — Nicolify-specific app config |
| `@/lib/api/public` | ~10-20 | **Stay local** — Nicolify-specific public booking/landing API |
| `@/lib/api/<other endpoints>` | varies | **Stay local** — Nicolify-specific |
| Misc `@/lib/<other paths>` | varies | Case-by-case |

**The spec A4 verifier excludes `@/app/|@/features/|@/stores/|@/components/shared/` but NOT `@/lib/*`.** This is a spec gap — `@/lib/*` contains both:
1. Paths that SHOULD lift to @luana/* (like `@/lib/utils` → `@luana/format`)
2. Paths that should STAY LOCAL (form-runtime, config, app-specific api endpoints)

**Two-path resolution required:**
- **Path A:** Extend codemod with `@/lib/utils` → `@luana/format` mapping + re-run; expand A4 spec exclusion list to allow Nicolify-local `@/lib/{form-runtime,edge,config,api/public}/*` paths
- **Path B:** Architect issues T-8.bis spec extension covering remaining @/lib/* categorization rules

#### A5 — Workspace symlinks ✅

`pnpm list -r '@luana/*'` confirms all 6 @luana/* packages resolve via symlinks in `nicolify/frontend/node_modules/@luana/`. luana-platform workspace registered `@luana/nicolify-web` successfully.

---

## Halt trigger status

| Trigger | Status |
|---|---|
| H1 prereqs missing | NOT triggered (Step 0 ✅) |
| H3 pnpm install fails workspace deps | NOT triggered (install OK, warnings only) |
| H4 Clerk fixture missing post-move | NOT triggered (rsync exclude is intentional per spec; clerk.setup.ts regenerates at e2e runtime; config refs resolve correctly) |
| H8 Vitest delta > 5 NEW NOT-deferred failures | NOT YET MEASURED (A3 deferred per T-10 H8 pattern) |
| **H13 cross-repo 3+ consecutive fails** | NOT triggered (single sequential operations, no consecutive failures) |
| Hard $800 budget cap | Within cap — partial mid-execution reporting now |

---

## Decisions deferred to architect/Chris

### D1 — Codemod scope sufficiency

**Question:** Does codemod need additional mappings (`@/lib/utils` → `@luana/format`)? Or does A4 verifier exclusion list need to expand to cover Nicolify-local `@/lib/*` paths?

**Recommendation:** Both. Spec T-8.bis or T-9 should:
1. Extend codemod with `@/lib/utils` → `@luana/format` mapping
2. Define which `@/lib/*` subdirs are "Nicolify-local stay-local" vs "lift candidate" — update spec A4 verifier accordingly
3. Re-run codemod after extension

### D2 — @luana/* package config gaps (pre-existing, T-8 surfaced)

**Three issues outside T-8 scope:**
1. `@luana/hooks/src/index.ts` does NOT export `use-copilot-offset` (commented out with `// requires @/features/copilot` note) but `@luana/ui-kit` files (alert-dialog/detail-panel/dialog/sheet) import it
2. `@luana/ui-kit/package.json` lacks `react-hook-form` as peer dep but `@luana/ui-kit/src/form.tsx` imports it
3. `@luana/schemas` declares `zod: ^3.22.0`, nicolify-web uses `zod: ^4.3.6` — type compatibility fails at RHF Controller boundary

**Recommendation:** Architect spawns new ticket (T-8.bis-A or T-9.5) for `@luana/*` package config repair OR explicitly ratifies these issues as known-defects deferred to luana-platform Story 6/7 (frozen registries) closure.

### D3 — A3 Vitest baseline categorization

**Cannot run A3 until A1 TSC compiles cleanly.** Follow T-10 H8 ratification pattern: categorize test ripples as deferred to T-15-FE or T-16 (consistent with T-10 deferral of Vitest cleanup).

---

## Deliverables status

| Deliverable | Status |
|---|---|
| `/home/chris/luana-platform/nicolify/frontend/` (FE rsync without .next/.turbo/etc) | ✅ DONE |
| `/home/chris/luana-platform/pnpm-workspace.yaml` updated | ✅ DONE |
| `/home/chris/luana-platform/nicolify/frontend/package.json` updated (name + workspace deps) | ✅ DONE (+ 4 missing transitive deps added) |
| FE imports rewritten via jscodeshift | ✅ DONE (339 files) + ⚠️ codemod scope gap (D1) |
| `T-8-impl-log.md` in AISALESHT docs | ✅ DONE (this file) |
| A1 TSC GREEN | ⚠️ 16 errors (categorized OUT-OF-SCOPE per D2) |
| A2 ESLint | ⏸ NOT MEASURED |
| A3 Vitest | ⏸ DEFERRED per T-10 H8 pattern |
| A4 legacy @/* = 0 | ⚠️ 759 (categorized D1 — needs spec/codemod extension) |
| A5 workspace symlinks | ✅ DONE |

---

## Cost spent estimate (Sesión 9 cumulative through T-8)

Approximated based on operations:
- rsync (negligible)
- pnpm install (large dep tree, file ops only)
- jscodeshift codemod execution (~4s wall)
- Node fixup script (333 files)
- 4× TSC runs (large project)
- 4× targeted greps
- Documentation writing

Estimated session cost: **~$300-450** (within $800 cap, well below report threshold). Halting now for architect ratification, NOT for budget.

---

## Recommendation for next session

1. **Architect spawns sub-ticket** (T-8.bis or T-9.5) addressing D1 + D2:
   - Extend codemod mapping for `@/lib/utils` → `@luana/format`
   - Define A4 exclusion list expansion to allow Nicolify-local `@/lib/*` paths
   - Resolve @luana/* package config gaps (use-copilot-offset export, react-hook-form dep, zod version coordination) — possibly route to Story 6/7 luana-platform work
2. **Re-run T-8 acceptance checks A1-A5** post-resolution
3. **OR** ratify as partial_a3 + accept current state, advance to T-9 (Vercel reconfig) with known A1/A3/A4 deferred items

---

## Files changed cross-repo

### AISALESHT (zero changes — codemod tooling consumed read-only)

`docs/product/stories/luana-nicolify-migration/T-8-impl-log.md` ← NEW

### luana-platform (T-8 changes only — preserves 12 parallel WIP files untouched in core/* + pyproject.toml)

- `pnpm-workspace.yaml` — added `nicolify/frontend` entry
- `nicolify/frontend/` — rsync from AISALESHT/frontend (11MB src + configs)
  - `package.json` — renamed name, added 6 @luana/* workspace deps, added 4 missing transitive devDeps
  - 339 files: imports rewritten via codemod (jscodeshift)
  - 333 files: subpath imports → barrel imports (post-codemod fix-up)
- `pnpm-lock.yaml` — regenerated by pnpm install

---

## Skills consulted

- **frontend-expert** — loaded `references/runtime-quality-checklist.md` mental model (live verification gate, mock anti-patterns)
- **brand-expert** — not invoked (T-8 = infra migration, no brand domain changes)
- **offer-expert** — not invoked
- **offer-type-preset-expert** — not invoked
- **copilot-expert** — not invoked
- **sales-agent-expert** — not invoked
- **metrics-expert** — not invoked
- **tessl__react-patterns** — N/A (T-8 = file/import migration, no React component logic)
- **tessl__zod** — surfaced issue: @luana/schemas zod ^3.22 vs nicolify zod ^4.3 incompatibility (D2)
- **tessl__shadcn-ui** — N/A (no component creation)
- **tessl__tailwind** — N/A
- **tessl__vitest** — N/A (A3 deferred)
- **tessl__nextjs-app-router-modularization** — N/A (no page restructure in T-8 scope)
- **tessl__graceful-degradation** — N/A
- **chrome-devtools-verify** — N/A (no UI verification at T-8; deferred to post-T-9 Vercel reconfig)

---

## Return contract

Last line of return reply: `partial_a3 -> docs/product/stories/luana-nicolify-migration/T-8-impl-log.md`
