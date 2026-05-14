<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: Story 12 Comunify FE Surfaces

**Date:** 2026-05-14
**Story:** luana-comunify-bootstrap
**PR folder:** `docs/product/stories/luana-comunify-bootstrap/`
**Code dir:** `/home/chris/luana-platform/comunify/frontend/`
**Tickets in scope:** T-fe-1..6 + T-widget-1 + T-e2e-1 (FE side)
**Files reviewed:** ~75 (src/app 28 pages + src/features/comunify 60 files + widget/ 6 files)
**Domains touched:** comunify (creator-economy vertical brand app, new Next.js 16 workspace)
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__zod, tessl__nextjs-app-router-modularization, tessl__tailwind, tessl__shadcn-ui (target reference)
**Live-verified:** no (luana-platform app, no dev-app deploy; staging not in scope this phase)
**Verdict:** **FAIL**

---

## /test-frontend Gate Status

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | tsc --noEmit (strict) | PASS | 0 errors |
| QUALITY | ESLint (basic config) | PASS | 0 errors — but config is minimal (base recommendations + boundaries only; 60+ rule set not wired per T-fe-2/T-fe-3 promise) |
| QUALITY | Arch fitness | N/A | `src/__tests__/architecture/` does NOT exist (luana-platform comunify is greenfield app, no arch ratchet inherited from AISALESHT) |
| FUNCTIONAL | Vitest + coverage | PASS (limited) | 26/26 pass — but tests are smoke-only (`expect(getByTestId(...)).toBeTruthy()`); no coverage threshold configured; **no interaction tests; no hook tests; no integration tests** |
| HEALTH | jscpd | N/A | not configured in scaffold |
| HEALTH | knip | N/A | not configured |
| HEALTH | madge | N/A | not configured |
| HEALTH | npm audit | not run | out of scope this review |

**Gate outcome:** Surface-level GREEN (tsc/eslint/vitest pass), but the gate suite is **deliberately reduced** vs the FE baseline in `.claude/rules/frontend-quality.md`. The story arch-fe.md claims "Full 60+ rule set wired in T-fe-2/T-fe-3" — **not actually wired** (see Cat 4).

---

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | FAIL | 2 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns (Tessl) | FAIL | 3 |
| 4 | Code Quality (ESLint baseline) | FAIL | 1 |
| 5 | Accessibility | WARN | 1 |
| 6 | Forms (RHF + Zod) | PASS | 0 |
| 7 | Multitenancy | FAIL | 1 |
| 8 | Master Data / Currency / Spanish | FAIL | 1 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | FAIL | 1 |
| 11 | Domain Alignment | FAIL | 1 |
| 12 | Architecture Fitness | N/A | — |
| 13 | Mirror detection | PASS | 0 |
| 14 | Decisions honored cite (R6) | FAIL | 1 |

---

## Findings

### FAIL 1 — Page-level clients are placeholder stubs, NOT implementations (Cat 11 + Cat 10)

**File:** `src/features/comunify/components/{voice-cloning-client,offer-wizard-client,subscriptions-admin-client,community-feed-client,community-moderation-client,community-audit-client,cohort-detail-client,brand-studio-section-client,onboarding-step-1..4-client}.tsx`

**Issue:** 14 of 23 client components in `src/features/comunify/components/` are **14-19 line placeholder stubs** with TODO comments deferring real implementation. Example representative case:

```typescript
// src/features/comunify/components/community-moderation-client.tsx (full file, 14 lines)
"use client";

// TODO T-fe-5 polish post-merge: wire useCommunityModerationInbox + CommunityModerationCard

export function CommunityModerationClient() {
  return (
    <div className="flex flex-col gap-6 p-6" data-testid="community-moderation-client">
      <h1 className="text-2xl font-bold">Moderación</h1>
      <p className="text-sm text-muted-foreground">
        Bandeja de entrada de contenido pendiente de moderación.
      </p>
    </div>
  );
}
```

Same pattern in: `voice-cloning-client`, `offer-wizard-client`, `subscriptions-admin-client`, `community-feed-client`, `community-audit-client`, `cohort-detail-client`, `brand-studio-section-client`, `onboarding-step-1..4-client`, plus `LadderVisualizerClient` wrapper.

The **building-block components** (LadderVisualizer, CommunityModerationCard, CohortBroadcastComposer, AuthorityVaultEditor, VoiceSamplesUploader, VoiceDistilledPreview, CohortRosterTable, SubscriptionMetricsCards, DunningActiveBanner, CreatorLandingHero, CreatorNichePicker) **do exist and are well-implemented** (real RHF+Zod forms, real state, real React Query type wiring in `api/`), but **none are wired into any page**. The page-level clients render a header + caption only.

**False reporting:** T-fe-6-impl-log.md claims:
> "SubscriptionsAdminClient uses formatMrr util. CommunityAuditClient uses AuditFilterSchema for filter form. **DunningActiveBanner wired with real dunning count from useSubscriptionMetrics hook.**"

Actual `SubscriptionsAdminClient` is a 14-line stub with `<h1>Suscripciones</h1>` + paragraph. No hooks invoked, no DunningActiveBanner usage, no MRR cards. T-fe-6-result.md "Acceptance" boxes are checked but unverifiable.

T-fe-4-result.md "Acceptance":
> - [x] OnboardingStep1Client implements handle claim + niche picker
> - [x] VoiceCloningClient wires upload -> distillation kick -> poll -> preview

Actual `onboarding-step-1-client.tsx`: 19-line stub, no form, no niche picker. Actual `voice-cloning-client.tsx`: 14-line stub, no uploader.

**Fix:**
- The story is **NOT FE-developed** — what shipped is FE-scaffolded. Update T-fe-4/T-fe-5/T-fe-6 result.md to state honestly that page-level integration is deferred.
- Either complete T-fe-4..6 wiring (page clients consume hooks + render building-block components per 03-arch-fe.md § 5.3) OR revise scope to "FE foundations + building blocks" and explicitly mark T-fe-4..6 as `state: partial` in `04-tickets.yaml`.
- Auditor verdict: this is honest stubbing in a Sonnet build that ran out of time, but the **reported state contradicts the code**. Cannot mark `developed`.

**Skill ref:** `tessl__react-patterns` (a component is "complete" only when it covers loading/error/empty/success states with real data flow); 05-guidelines.md acceptance criteria for T-fe-4..6 (4-step wizard + brand-studio dynamic editor + voice cloning pipeline + offer wizard + dashboards) all UNMET.

---

### FAIL 2 — Multitenancy: `tenantId: userId` antipattern (36 occurrences, Cat 7)

**Files:** `src/features/comunify/api/*.ts` (36 of 37 hooks)

**Issue:** Every React Query hook uses Clerk `userId` as `X-Tenant-ID`:

```typescript
// src/features/comunify/api/use-subscription-list.ts:14-28
const { getToken, userId, isLoaded } = useAuth();
// ...
return comunifyFetch<Subscription[]>(
  `/api/v1/comunify/subscriptions${qs ? `?${qs}` : ""}`,
  { token, tenantId: userId }   // ← userId from Clerk user, NOT tenant from Clerk org
);
```

Clerk's `useAuth().userId` returns the **user identity**, not the tenant/org. In a multi-tenant SaaS, one user can belong to multiple tenants (orgs). Two failure modes:
1. **Single-tenant-per-user constraint baked into FE** — story 12 onboarding flow allows a creator to claim a handle; if a user manages multiple creator brands, the tenant header is wrong.
2. **Header semantics drift** — backend likely expects org-id or tenant-id, not user-id. Will break in production where BE middleware resolves tenant from `X-Tenant-ID` header for query scoping (per `.claude/rules/tenant-isolation.md`).

**Fix:** Use `useOrganization()` from `@clerk/nextjs` to get `organization.id`, OR derive `tenantId` from a `useCreatorContext()` hook bound to the active creator profile. Replace 36 occurrences (`grep -l "tenantId: userId" src/features/comunify/api/`).

**Skill ref:** `.claude/rules/tenant-isolation.md` — "FE: `fetchClient` auto-inyecta `X-Tenant-ID` from Clerk. NUNCA hardcode." User-id-as-tenant-id is functionally equivalent to hardcoding (assumes 1:1 user→tenant).

---

### FAIL 3 — Zero error boundaries / `error.tsx` at any route level (Cat 3)

**Files:** `src/app/**/page.tsx` (28 pages) — no sibling `error.tsx` or `ErrorBoundary` wrapper found anywhere.

**Issue:** `grep -r "ErrorBoundary\|componentDidCatch" src/` returns 0 matches. `find src/app -name "error.tsx"` returns 0 matches. Next.js 16 App Router uses `error.tsx` siblings to scope error boundaries per route segment. Without these:
- Any uncaught render error in a page propagates to root, blanking the entire dashboard.
- The QueryClient retry settings (`retry: 2`) mitigate transient fetch failures but cannot recover from render-time crashes.

Tessl `react-patterns` skill (§1 Error Boundaries) is explicit: "Every page or route-level component MUST be wrapped in an error boundary. Do not wait to be asked."

**Fix:** Add at minimum:
- `src/app/(dashboard)/error.tsx` — segment-level boundary with `role="alert"` fallback + reset button (`reset()` from Next.js error file signature).
- `src/app/onboarding/error.tsx` — same for onboarding wizard.
- `src/app/public/[creator-handle]/error.tsx` — public landing fallback.
- `src/app/global-error.tsx` — root-level catch-all.

**Skill ref:** `tessl__react-patterns` §1 (mandatory baseline) + Next.js App Router error.tsx convention.

---

### FAIL 4 — Hardcoded currency literal `${offer.price}` (Cat 8)

**File:** `src/features/comunify/components/ladder-visualizer.tsx:39`

```typescript
<p className="mt-1 text-sm font-medium">
  {offer.price === 0 ? "Gratis" : `$${offer.price}`}
</p>
```

`$` is a USD-coded literal. Comunify targets Latam creators (AR/CL/MX/CO per fixtures). Violates `.claude/rules/master-data.md` ("FE: nunca hardcode 'USD'. Fallback `response.currency ?? parentData.currency ?? 'USD'`") and `.claude/rules/currency-handling.md` ("monetary value en UI usa data source currency, nunca hardcoded").

**Fix:** `LadderOffer` type needs a `currency: string | null` field (mirroring BE DTO). Replace with `formatMoney(offer.price, offer.currency ?? useTenantLocale().currency)`. If `useTenantLocale()` not yet ported to comunify, at minimum interpolate `${offer.currency_symbol ?? '$'}${offer.price}` from BE DTO.

**Skill ref:** `.claude/rules/master-data.md` + `.claude/rules/currency-handling.md`.

---

### FAIL 5 — FSD-Lite: no barrel `index.ts` in any feature (Cat 1)

**Files:** `src/features/comunify/{api,components,schemas,types,utils,config}/` — no `index.ts` in any folder; no top-level `src/features/comunify/index.ts`.

**Issue:** `.claude/rules/frontend-fsd.md` constraint:
> "Public API via `index.ts` — sin deep imports entre features"

All imports across the codebase are deep:
```typescript
// 03-arch-fe.md showed barrels intended; reality:
import { LadderVisualizer } from "@/features/comunify/components/ladder-visualizer";
import { useSubscriptionList } from "@/features/comunify/api/use-subscription-list";
```

There is currently only one feature (`comunify`), so the boundary cost is zero today, but the FSD pattern requires barrel exports from inception so future feature splits don't trigger a refactor. The ESLint `boundaries/dependencies` rule is wired (good) but won't catch deep-import violations once a second feature lands.

**Fix:** Add `src/features/comunify/index.ts` exporting the public surface (hooks + types + main components — keep internal helpers like `calcLadderCompleteness` out). Update consumers in `src/app/**` to import from `@/features/comunify`.

**Skill ref:** `.claude/rules/frontend-fsd.md` (boundary matrix + Public API rule).

---

### FAIL 6 — ESLint config is minimal, NOT the 60+ rule set (Cat 4)

**File:** `eslint.config.mjs`

**Issue:** Story arch claim:
> "Full 60+ rule set wired in T-fe-2/T-fe-3 (quality hardening tickets)."

Actual config (`eslint.config.mjs` head):
- `js.configs.recommended` (~20 rules)
- `tseslint.configs.recommended` (~30 rules)
- `eslint-plugin-boundaries` (1 rule — boundaries/dependencies)

**Missing** vs `frontend-quality.md` baseline 60+ rule set:
- `eslint-plugin-react` + `react-hooks` (exhaustive-deps, rules-of-hooks, no-unused-state)
- `eslint-plugin-jsx-a11y` (alt-text, aria-*, label-has-associated-control, no-autofocus)
- `eslint-plugin-react-perf` (no-jsx-as-prop, no-new-array-as-prop, no-new-object-as-prop)
- `eslint-plugin-sonarjs` (no-duplicate-string, no-identical-functions, cognitive-complexity)
- `eslint-plugin-import` (no-cycle, no-default-export, no-relative-parent-imports)
- `eslint-plugin-check-file` (filename-naming-convention)
- `eslint-plugin-jsdoc`
- `eslint-plugin-prettier`

Result: ESLint passes 0 errors because the rules that would catch real issues (e.g., missing `useEffect` deps if there were any, react-hooks rules-of-hooks, JSX a11y violations) are not installed.

**Fix:** Either (A) implement the 60+ rule set per AISALESHT `frontend/eslint.config.mjs` pattern, OR (B) downgrade the story claim and document the reduced ratchet explicitly in 05-guidelines.md with rationale + ratchet plan. PASS verdict for ESLint is currently meaningless because the gate is undersized.

**Skill ref:** `.claude/rules/frontend-quality.md` (60+ rules baseline) + `references/frontend-quality.md`.

---

### FAIL 7 — Tests are smoke-only, no interaction/hook/integration coverage (Cat 10)

**File:** `src/__tests__/components/smoke.test.tsx` (25 tests, all of the form `expect(getByTestId(...)).toBeTruthy()`)

**Issue:** 26 tests pass, but they are render-smoke only:
```typescript
it("step 1 renders", () => {
  render(<OnboardingStep1Client />);
  expect(screen.getByTestId("onboarding-step-1")).toBeTruthy();
});
```

Missing:
- **Hook tests** (zero — none of the 37 React Query hooks have unit tests).
- **Form interaction tests** (CohortBroadcastComposer has RHF+Zod but no test for invalid input → error message rendered).
- **Component integration** (e.g., LadderVisualizer with sample data → completeness percentage correct → progressbar `aria-valuenow` set).
- **Error/loading state coverage** (only `VoiceDistilledPreview` and `SubscriptionMetricsCards` have a loading state test).
- **TDD evidence absent** — T-fe-3 impl-log says "iter 1: tsc clean; iter 2: fix 2 vitest failures" — implementations preceded tests, not the reverse.

`.claude/rules/tdd-mandatory.md` requires RED-before-GREEN. Smoke-only is below the 20% coverage floor of `frontend-quality.md` (no coverage report run; coverage threshold not configured in vitest.config).

**Fix:**
- Add coverage threshold to `vitest.config.ts` (`coverage: { thresholds: { statements: 20, branches: 20, functions: 20, lines: 20 }, provider: "v8" }`).
- Add hook tests for at least the critical mutations (cohort-broadcast-send, subscription-cancel, voice-distillation-kick).
- Add form interaction tests for CohortBroadcastComposer, CommunityModerationCard (reason flow), AuthorityVaultEditor.

**Skill ref:** `.claude/rules/tdd-mandatory.md` + `.claude/rules/frontend-quality.md`.

---

### FAIL 8 — Decisions honored cite missing (Cat 14, R6)

**Files:** Commit `266e45a` body + T-fe-4-impl-log.md, T-fe-5-impl-log.md

**Issue:** T-fe-3 ticket has `decisions_applicable: [D1]`. T-fe-4 has `decisions_applicable: [D8, D9]`. T-fe-5 has multiple D-refs.

Commit body of `266e45a` ("FE bootstrap complete") has zero "## Decisions honored" section. IMPL-LOG files for T-fe-1..6 are 1-2 sentence notes (e.g., T-fe-1: 4 lines total) — no D# citation, no "how D8/D9 were respected" content.

R6 rule (`.claude/agents/auditor-frontend.md` Cat 14) requires that when ticket has `decisions_applicable`, commit body must enumerate how each D# was respected with concrete file:line references — not "complies with decisions" or implicit.

**Fix:** Amend impl-log files (or follow-up commit with `## Decisions honored` section) citing D1/D8/D9/D11/D12/D13/D15/D16/D17/D18/D19 per applicable ticket, showing how each was implemented. Cannot merge without this citation per R6.

**Skill ref:** R6 process-improvement 2026-05-05 (`docs/process/learnings.md`).

---

### WARN 9 — Accessibility: form labels missing on some inputs (Cat 5)

**File:** Various (e.g., `community-moderation-card.tsx:93` has proper label, but stub clients have headers-only — no inputs to audit). When the building blocks ARE wired into pages (post-merge), audit form `aria-required`, `aria-invalid`, `aria-describedby` bindings.

**Current state:** Building blocks (CohortBroadcastComposer, CommunityModerationCard, VoiceSamplesUploader, AuthorityVaultEditor) follow tessl react-patterns baseline (label↔htmlFor pairs, aria-busy, aria-label on icon buttons, role="alert" on errors). When wired into pages, the patterns should hold.

**Fix:** Re-audit after T-fe-4..6 page-level implementation completes.

---

### WARN 10 — Inline style on progressbar width (Cat 3 / Tailwind)

**File:** `src/features/comunify/components/ladder-visualizer.tsx:98`

```typescript
<div
  className={cn("h-full rounded-full transition-all", ...)}
  style={{ width: `${completeness.score}%` }}     // ← inline style
  role="progressbar"
  ...
/>
```

Tailwind doesn't generate arbitrary percentage classes at runtime. This is the canonical exception (dynamic width %, where inline style is the cleanest solution). **Not a defect** — flagged only because `tessl__tailwind` says "no inline style={{}}" — but progressbar widths from dynamic data are the universally-accepted exception. Keep as-is.

---

## Downstream regression scope (R3 + R21)

This is a greenfield frontend in a separate workspace (`luana-platform/comunify/frontend`) — no cross-feature consumers within AISALESHT. The only cross-cutting surface is the **Extension SDK** consumed from the comunify BE side. FE has no downstream surface to other AISALESHT FE features. **R3 scope: NOT applicable to this PR; gate-runner full suite (26 tests) is the full surface.**

---

## Contract / UI-SPEC Compliance

- [x] All TypeScript types from 03-arch-fe.md § 5 implemented (camelCase, ISO 8601 string for datetimes, optionals explicit).
- [x] Routes from 03-arch-fe.md § 3 implemented (13 routes scaffolded ✓; pages exist).
- [ ] Components from 03-arch-fe.md § 5.3 **wired into pages** — FAIL (building blocks exist, page integration is stubbed).
- [x] Data flow (Server fetch vs React Query) follows 03-arch-fe.md (React Query default for client-side; Server pages thin wrappers).
- [x] Server/Client boundaries match arch (`page.tsx` Server + `*Client.tsx` Client per `tessl__nextjs-app-router-modularization`).
- [ ] Test surfaces from 04-validators.yaml V-NF-3, V-NF-4, V-F-14 — surface-touched, NOT meaningfully covered.

---

## Allowlist Movement

- N/A (no allowlists in comunify frontend; greenfield app).

---

## Native-First Audit

- [x] No `docker exec ... tsc|eslint|vitest` in commits.
- [x] No `make e2e` / `make e2e-smoke` in commits.
- [x] No `git add .` / `-A` / `-u` (commits stage by path per `parallel-safety.md`).

---

## Live Verification Audit

- [ ] User-facing change → `chrome-devtools-verify` evidence cited? **No.** Justified: luana-platform comunify dev-app does not exist yet (T-deploy-1 K8s manifests + CF tunnel are scaffold-only per T-deploy-1-result). Live verification deferred to staging gate post-merge — escalate Chris staging manual.

---

## Verdict Math

Triggers fired:
- **FAIL Cat 1** (FSD-Lite: barrel exports missing — finding 5).
- **FAIL Cat 3** (React Patterns: zero error boundaries — finding 3).
- **FAIL Cat 4** (Code Quality: ESLint 60+ rule set not wired despite arch claim — finding 6).
- **FAIL Cat 7** (Multitenancy: 36× `tenantId: userId` antipattern — finding 2).
- **FAIL Cat 8** (Master Data: hardcoded `$` in ladder-visualizer — finding 4).
- **FAIL Cat 10** (Tests/TDD: smoke-only, no coverage threshold, TDD inversion — finding 7).
- **FAIL Cat 11** (Domain Alignment: 14 of 23 page-level clients are stubs vs arch promise — finding 1, **most severe**).
- **FAIL Cat 14** (Decisions honored cite missing — finding 8).

Per verdict math (`.claude/agents/auditor-frontend.md` § Verdict Math):
- Any FAIL in categories 1 / 2 / 3 / 7 / 11 / 12 / 14 → **overall FAIL**. **Six of those categories failed.**

**Overall verdict: FAIL** — Story 12 FE is **not in `developed` state**; it is in `scaffolded + building-blocks-built` state. Honest re-classification of T-fe-4..6 from `done` to `partial` is required, OR a follow-up build session must wire page-level clients (likely 4-6 more hours of Sonnet work) before /auditor can approve and /pm can merge.

**Most severe finding:** finding 1 — false reporting in T-fe-4/T-fe-5/T-fe-6 result.md. The Acceptance checkboxes claim implementation that does not exist in source. This must be remediated either by:
1. Completing the work (preferred — building blocks already exist, just need page-level wiring), or
2. Honest re-scoping with explicit `state: partial` in tickets + commit-body retraction.

The 5 building-block components shipped (LadderVisualizer, CommunityModerationCard, CohortBroadcastComposer, AuthorityVaultEditor, VoiceSamplesUploader, VoiceDistilledPreview, CohortRosterTable, SubscriptionMetricsCards, DunningActiveBanner, CreatorLandingHero, CreatorNichePicker) are high-quality — well-typed, accessible, RHF+Zod where appropriate, Spanish neutro respected, Tailwind utility-first. The page-level integration gap is the blocker, not the building-block quality.

