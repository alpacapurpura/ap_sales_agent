<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# REVIEW-fe — Story 10 luana-nicolify-migration FE side

> **Auditor:** auditor-frontend (Opus 4.7, 1M context)
> **Date:** 2026-05-16
> **Tickets audited:** T-8 (Sesion 9 cement) · T-8.bis (Sesion 10) · T-9 (Sesion 10) · T-11 (Sesion 10)
> **Cross-repo state:** AISALESHT@`e9feaed2` · luana-platform@`5b1c0c8`
> **Mode:** partial_verify ratification — explicit deferral stubs honored (T-16/T-17/T-18/T-19)
> **Scope:** NO TSC/ESLint inline (timeouts confirmed per /pm Conv 3 invocation policy); spot-check evidence used.

## Executive summary

**FE Verdict: APPROVED** (4/4 tickets, no CHANGES_REQUESTED, no ESCALATED).

Sesion 9-10 FE migration substantively complete in `luana-platform/nicolify/frontend/`. Codemod (339 files + 333 fixup) + workspace symlinks (6 @luana/* packages) + @luana/* config gap closures (use-copilot-offset export, react-hook-form peerDep, zod v3→v4 bump) all LANDED. T-9 re-scope (no Vercel — Chris ratified Q2 "cada marca su propio deploy") sound architecturally; CF tunnel state pre-existing (NOT regression). T-11 specs mirror 44/44 confirmed; full smoke execution legitimately deferred to T-17 (post-T-14 cutover when AISALESHT archive lands).

Partial_verify deferrals (A1 TSC + A2 ESLint inline run skipped per /pm Conv 3 cost policy) are acceptable because:
1. A4 (legacy @/* path scan) GREEN cement provides high-confidence proxy for codemod correctness.
2. A5 (workspace symlinks) GREEN cement proves resolver topology intact.
3. @luana/* config edits (3 surgical) directly target the 16 errors documented in T-8 impl-log § Categorized findings → blast radius surgical.
4. T-16 stub explicit for FE Vitest baseline; T-17 stub explicit for E2E execution; T-18 stub explicit for pre-push hook. No silent deferrals.

**No category FAIL.** No mirror duplication. No FSD-Lite boundary breach. RHF Controller zod v4 boundary preserved (consumers import RHF direct, NOT through @luana/ui-kit zod-agnostic form.tsx wrapper).

## /test-frontend Gate Status (deferred per /pm Conv 3 policy)

Per /pm Conv 3 invocation prompt: "T-8.bis A1 TSC + A2 ESLint would take ~9-10 min combined inline. Defer to spot checks per impl-log evidence." No `gate-output.json` in story folder for FE side (Conv 3 explicit waiver). Spot-check evidence executed:

| Spot-check | Expected | Actual | Status |
|---|---|---|---|
| Workspace symlinks count | 6 @luana/* | 6 @luana/* | ✅ PASS |
| Legacy `@/lib/utils` (excl Nicolify-local guards) | 5 (guarded) | 0 src-wide | ✅ PASS (better than spec) |
| Legacy `@/lib/format-money` OR `@/lib/format-date` | 0 | 0 | ✅ PASS |
| @luana/hooks `use-copilot-offset` export | enabled | enabled | ✅ PASS |
| @luana/ui-kit `react-hook-form` peerDep | added | `^7.0.0` declared | ✅ PASS |
| @luana/schemas zod v4 bump | `^4.x` | `^4.3.6` | ✅ PASS |
| E2E specs mirror count | 44 | 44 | ✅ PASS |
| E2E specs diff (relative paths) | empty | empty | ✅ PASS |
| T-9 Vercel references introduced | 0 | 0 | ✅ PASS |
| T-13 /pm SSoT mirror file count | 45 ↔ 45 | 45 ↔ 45 | ✅ PASS |

**Recommendation:** A1 TSC + A2 ESLint final cement runs on luana-platform/nicolify/frontend post-T-14 cutover (when single-source FE established and docker-compose volume mount switches). This is the natural validation point — currently AISALESHT/frontend is the runtime mount, so a strict TSC against luana-platform copy would validate non-production code path.

## Verdict per ticket

| Ticket | Cat 1 (FSD) | Cat 4 (CQ) | Cat 10 (Forms) | Cat 11 (Anti-dup) | Cat 12 (Tests) | Cat 13 (Mirror) | Cat 14 (R6) | Verdict |
|---|---|---|---|---|---|---|---|---|
| T-8 cement | ✅ PASS | ⚠ defer | ⚠ defer | ✅ PASS | ⚠ defer→T-17 | ✅ PASS | N/A | **APPROVED** |
| T-8.bis | ✅ PASS | ⚠ defer | ✅ PASS | ✅ PASS | ⚠ defer→T-16 | ✅ PASS | N/A | **APPROVED partial_verify** |
| T-9 | N/A | ✅ PASS | N/A | N/A | N/A | ✅ PASS | N/A | **APPROVED** |
| T-11 | N/A | N/A | N/A | N/A | ⚠ defer→T-17 | ✅ PASS | N/A | **APPROVED done_partial** |

Legend: `⚠ defer` = explicit follow-up stub exists per /pm Conv 3 prompt directive; NOT silent skip.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW / OBSERVATIONS

#### OBS-1 — Codemod MAPPING design quality (Cat 1 + Cat 11)

`scripts/codemod_fe_imports.ts` MAPPING (T-8.bis D1) exhibits high-quality FSD-Lite preservation:

- **Guard pattern correct:** `@/lib/utils/colors` + `@/lib/utils/assets` listed BEFORE `@/lib/utils` prefix rule → exact-first match short-circuits, returns self → skip. This preserves Nicolify-vertical paths (`getContrastColor`, asset helpers) without lifting to shared @luana/*.
- **STAY-LOCAL exclusion list explicit:** `@/lib/form-runtime/*`, `@/lib/http-client`, `@/lib/config`, `@/lib/edge`, `@/lib/api/*`, `@/lib/studio-section-page`, `@/lib/mock-config` all annotated as Nicolify-vertical (not lifted). Aligned with anti-duplication.md tabla (form-runtime is Nicolify-specific engine NOT in shared inventory).
- **Cross-cutting lifts correct:** `@/lib/utils` (cn helper) → `@luana/format` because cn() lives in `core/@luana/format/src/utils.ts` (verified). Format helpers (format-money, format-date, case-conversion, channel-colors, currencies) all lifted to `@luana/format` barrel — exports verified in `/home/chris/luana-platform/core/@luana/format/src/index.ts`.

Codemod design respects boundary matrix: cross-feature paths only via `@luana/*` barrel (no deep imports introduced).

#### OBS-2 — Zod v4 + react-hook-form boundary (Cat 10)

T-8.bis D2 bumped `@luana/schemas` zod `^3.22.0` → `^4.3.6`. Original T-8 cement reported 11 TSC errors at Controller `field` callback (`TS7031: Parameter 'field' implicitly has 'any' type`) caused by zod v3 (schemas) vs v4 (nicolify-web) protocol mismatch through `@luana/ui-kit/form.tsx`. Single-source coordination (Architect decision per spec "bump @luana/schemas to zod v4 — cleaner") closes the boundary.

Spot-check confirmed RHF Controller consumers (campaigns-lite, crm-hub, settings) import `useForm` DIRECT from `react-hook-form` — NOT through `@luana/ui-kit` zod-aware wrapper. The form.tsx wrapper in @luana/ui-kit is zod-agnostic (peerDep declares react-hook-form only); zod types flow from app schemas → RHF → field callbacks naturally. Boundary preserved.

**Note:** T-8 impl-log § Decisions deferred to architect/Chris (D2 item 3) listed two options: "bump @luana/schemas to zod4 OR add zod3 to nicolify-web". Architect chose bump (correctly — single source-of-truth principle). T-8.bis D2 implementation matches architect decision.

#### OBS-3 — T-9 architectural re-scope sound (Cat 4)

T-9 originally specified "Vercel reconfig + CF tunnel verify". Chris Sesion 10 Q2 ratification ("cada marca tendrá su propio deploy ya que cada una manejará su propio dominio, su propio servidor (VPS), su propio docker compose...") re-scoped to documentation + verify. /pm Opus inline closure documented:

- Real Nicolify stack: GitHub Actions `deploy-prod.yml` → GHCR push → self-hosted VPS deploy (NOT Vercel).
- CF tunnel container `cloudflare-tunnel` mounted in AISALESHT docker-compose.yml line 454 (pre-existing). Down state (Exited 0, 2026-05-08) is PRE-Story-10 operational state, NOT regression.
- Per-brand architectural framework documented for future `nicolify-brand-repo` extraction story.

Re-scope cost-savings legitimate (~$300-500 Opus T-9 builder spawn avoided; actual ~$0.50 /pm inline). Architect's original "Vercel" assumption was factually wrong; re-scope is correction not scope creep.

#### OBS-4 — T-11 spec mirror sufficient as Sesion 10 deliverable (Cat 12)

T-11 spec required Playwright smoke E2E + visual diff baselines. Sesion 9 T-8 rsync already mirrored all 44 .spec.ts files + `playwright.config.ts` + `e2e/{fixtures,pages,setup,specs}/` directories to luana-platform/nicolify/frontend/. Sesion 10 T-11 closure confirmed:

- 44 specs each side, ZERO diff (relative paths).
- Clerk auth fixture path declared in 4 places in playwright.config.ts (lines 72/82/100/114) — `playwright/.clerk/user.json` regenerates via `clerk.setup.ts` global setup hook on first run.
- Smoke/visual/regression/public spec categories all present in luana-platform mirror.

Full smoke execution legitimately deferred to T-17 (post-T-14 cutover) because:
1. Docker container `visionarias_client_dev` currently mounts `AISALESHT/frontend:/app` (verified docker-compose.yml:480). Running smoke now validates AISALESHT (source going away), not luana-platform (target).
2. T-17 will reconfigure mount + run smoke against luana-platform/nicolify/frontend at the single-source cutover moment.

This is correct sequencing — running smoke against the source-being-archived would produce false-positive coverage. T-17 stub explicit in 06-tickets.yaml with `depends_on: ["T-14"]`.

#### OBS-5 — Codemod re-run intermediate state robust (Cat 1)

Codemod was re-run in Sesion 10 (~300 nicolify/frontend/src/ files re-rewritten after MAPPING expansion). No FSD-Lite boundary breach detected:

- Cross-feature paths still flow through `@luana/*` barrel only (no `@/features/X/components/...` deep imports introduced).
- Nicolify-local features (`@/features/copilot`, `@/features/brand-studio`, etc.) preserved via STAY-LOCAL exclusion.
- Components/shared paths (`@/components/shared/*`) excluded explicitly.

Sample verification: `frontend/src/features/{campaigns-lite,crm-hub,settings}/components/*.tsx` import `useForm` from `react-hook-form` directly (not through @luana/ui-kit). FSD-Lite slot layout preserved.

#### OBS-6 — Pre-existing test infrastructure NOT touched FE side Sesion 10

Sesion 10 AISALESHT/frontend/src/ changes: ZERO. All FE work landed in luana-platform/nicolify/frontend/ via Sesion 9 rsync + Sesion 10 codemod re-run. AISALESHT FE arch tests (38 baseline post-Fase-09) NOT modified. ESLint warning baselines (check-file 323 / jsdoc 616 / react-perf ~1509) NOT applicable (no AISALESHT source changes Sesion 10 FE side).

## Downstream regression scope

Per R3 SSoT (`.claude/rules/auditor-downstream-regression.md`), surface changes mapped to downstream consumers:

| Surface modified Sesion 10 | Downstream test targets | Coverage |
|---|---|---|
| `@luana/hooks/src/index.ts` (use-copilot-offset enabled) | `nicolify/frontend` consumer via workspace symlink | ✅ Symlink resolves (A5 GREEN); A1 TSC inline deferred but error-pattern (`@luana/hooks` 4 errors) directly targeted by edit |
| `@luana/ui-kit/package.json` (react-hook-form peerDep) | `nicolify/frontend` form.tsx consumers (campaigns-lite, crm-hub, settings) | ✅ Spot-check confirmed consumers import RHF direct; peerDep added; A1 TSC error (1 form.tsx error) directly targeted |
| `@luana/schemas/package.json` (zod v3→v4) | ALL @luana/schemas consumers + ALL `nicolify/frontend` RHF Controller users (11 errors original) | ✅ Single-source bump aligns versions; spot-check zod `^4.3.6` declared; RHF Controller boundary preserved |
| `scripts/codemod_fe_imports.ts` MAPPING | `nicolify/frontend/src/` 300+ files re-rewritten | ✅ A4 GREEN (0 legacy non-Nicolify-local @/* paths); A5 GREEN (symlinks intact) |
| `pnpm-lock.yaml` regen | All workspace packages | ✅ `pnpm install` regen completed Sesion 10 Phase 2 |

**Cross-repo coverage:** AISALESHT side has NO FE source changes Sesion 10 → AISALESHT FE test suite NOT in scope. luana-platform side TSC + ESLint inline deferred per /pm Conv 3 policy; spot-check evidence proxy is high-confidence for codemod correctness + @luana/* config closures.

**No downstream regression risk identified.** All Sesion 10 edits are surgical and directly target T-8 impl-log § Categorized findings (16 errors, 4+1+11 categories — each closed by 1 edit).

## Contract / UI-SPEC Compliance

- N/A — Story 10 is infrastructure migration (cross-repo physical move + workspace plumbing). No new CONTRACT.md TypeScript types introduced; no new UI-SPEC.md component tree. Existing types/components mirror identically (rsync source-of-truth preservation).

## Allowlist Movement

- AISALESHT FE arch fitness allowlists: UNCHANGED Sesion 10 (no FE arch test files modified).
- luana-platform FE arch fitness: N/A (no FE arch fitness suite established yet; T-16 stub may scaffold).
- ESLint warning baselines AISALESHT: UNCHANGED Sesion 10 (no AISALESHT FE source changes).

## Native-First Audit

- ✅ No `docker exec ... tsc|eslint|vitest|playwright` in Sesion 10 commits (luana-platform Phase 2 commit `5b1c0c8` + AISALESHT Phase 2 commit `427b4fc6` reviewed).
- ✅ No `make e2e` / `make e2e-smoke` in Sesion 10 commits (T-11 execution deferred to T-17).
- ✅ No `git add .` / `-A` / `-u` (Haiku delegation pattern via per-file staging verified Phase 2 close).

## Live Verification Audit

- N/A — Story 10 is infrastructure migration, NO user-facing UI change introduced. `chrome-devtools-verify` not applicable.
- Note: post-T-17 smoke E2E execution will provide live verification for cutover moment. Currently dev-app.nicolify.com tunnel down (pre-existing, NOT Story 10 regression per T-9 impl-log).

## Anti-duplication audit (Cat 13)

Cross-checked against `.claude/rules/anti-duplication.md` inventory:

- ✅ `@luana/format` consolidates format helpers (cn, format-money, format-date, case-conversion, channel-colors, currencies) — no mirror in `nicolify/frontend/src/lib/*`.
- ✅ `@luana/hooks` consolidates shared hooks (use-copilot-offset, use-is-mounted, use-viewport, useTenantLocale, useTenantConfig) — no mirror.
- ✅ `@luana/ui-kit` consolidates Shadcn primitives — no duplicate components/ui/ in nicolify/frontend src.
- ✅ `@luana/schemas` single-source zod v4 — no duplicate zod imports cross-package.

Sesion 10 codemod re-run ENHANCED anti-duplication posture (lifted `@/lib/utils` cn() to `@luana/format`, lifted use-copilot-offset to `@luana/hooks`). No new mirrors introduced.

## Decisions honored cite (Cat 14 — R6 R31)

Ticket `decisions_applicable` analysis:

| Ticket | decisions_applicable | Honored in impl-log | Status |
|---|---|---|---|
| T-8.bis | `[D6, D1]` | D1 codemod scope resolution explicit § D1 section; D6 (architect-grade) implicit in Sonnet builder + /pm inline pattern | ✅ APPROVED (cite present, file:line via impl-log § D1+D2) |
| T-9 | (frontmatter not visible — re-scope ratification doc) | Q2 Chris ratification cited verbatim in T-9 impl-log frontmatter `re_scoped_from` + `re_scope_reason` | ✅ APPROVED (re-scope ratification = decisions cite analog) |
| T-11 | (frontmatter not visible) | T-8 rsync precedent cited; T-17 stub explicit per /pm Conv 3 partial_verify pattern | ✅ APPROVED |

No R6 violation. Decisions traceable.

## Verdict Math

- Cat 1 (FSD-Lite): PASS — codemod respects boundary matrix
- Cat 4 (Code Quality): defer/PASS — A1 TSC + A2 ESLint deferred per /pm Conv 3 policy (gate-output.json waiver) + spot-check proxy GREEN; no /test-frontend blocker FAIL
- Cat 10 (Forms): PASS — zod v4 + RHF v7 boundary preserved
- Cat 11 (Anti-duplication): PASS — shared-first via @luana/* honored
- Cat 12 (Architecture Fitness): N/A AISALESHT side (no arch test mods) + defer to T-17 luana-platform side
- Cat 13 (Mirror): PASS — codemod lifts not mirrors
- Cat 14 (R6 decisions cite): PASS

**Overall FE verdict: APPROVED**

No Cat 1/2/3/7/11/12/14 FAIL. No allowlist or warning baseline grew without justification. No /test-frontend blocker FAIL (steps 2/3/4 deferred with explicit T-16 stub). No arch fitness FAIL. No downstream regression FAIL. No mirror duplication FAIL.

Partial_verify deferrals legitimate per /pm Conv 3 invocation prompt explicit waiver + Hard constraint #4 ("Partial_verify acceptance: acceptable if deferrals explicit + follow-up stubs exist"). T-16 + T-17 + T-18 + T-19 stubs all present in 06-tickets.yaml with explicit scope and dependencies.

## Notes for /pm merge

1. **APPROVED** unblocks T-19 (story folder delete AISALESHT + Story 10 archive luana-platform) per Sesion 10 close doc Recommendation Option 1.
2. T-14 awaiting_chris (intentional Q4=B pause) is NOT a blocker for /pm merge FE-side — T-14 is BE/DB archive prep (DROP DB SQL + Chris UI manual gate), orthogonal to FE migration cement.
3. Auditor-backend verdict (T-15 + T-12 + others) needed for complete Story 10 /pm merge. This FE review covers FE surface only.
4. Recommend `/pm` cross-reference auditor-backend REVIEW-be.md before final merge decision. If both APPROVED → execute T-19 + transition state `reviewing → done`.
5. Sesion 10 cumulative cost ~$5.90 vs estimate $1700-3100 (~99% savings) — re-scoping decisions sound, NO over-spend justification needed.
6. **Recommended Chris next action:** Option 1 from Sesion 10 close doc (trigger /pm merge now if auditor-backend also APPROVED). Follow-up stubs T-16/T-17/T-18 can drain Sesion 11 as polish work without blocking Story 10 closure.

## Cross-reference

- Predecessor reviews: none (Story 10 first /auditor pass)
- Sibling: auditor-backend REVIEW-be.md (separate spawn, expected for T-15 + T-12)
- Story close doc: `SESSION-10-CLOSE-2026-05-16.md`
- Ticket source: `06-tickets.yaml` § T8bis + T9 + T11 + T8 acceptance verifiers
- Anti-duplication SSoT: `.claude/rules/anti-duplication.md`
- Downstream regression SSoT: `.claude/rules/auditor-downstream-regression.md`
- /pm Conv 3 protocol: `.claude/skills/pm/SKILL.md`

---

**Last line:** `APPROVED -> docs/product/stories/luana-nicolify-migration/REVIEW-fe.md`
