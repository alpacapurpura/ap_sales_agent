---
ticket: T-fe-4
story: luana-vitalia-bootstrap
started: 2026-05-14
author: builder-frontend (Sonnet 4.6)
---

# T-fe-4 Impl Log — 5 Interactive Client Components + Integration Tests

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `tessl__react-patterns` | All async components need loading/error/empty states + ARIA | Applied: `aria-busy`, `aria-invalid`, `aria-live="polite"`, `aria-atomic`, `role="alert"`, `role="status"`, skeleton loading, error banners, empty CTA |
| `tessl__nextjs-app-router-modularization` | D9 pattern: pages = Server Components, interactivity = `*Client.tsx` | Applied: all 5 components have `"use client"` directive, no SSR logic inside |
| `tessl__zod` | Form validation per-step without react-hook-form (not installed) | Applied: `offerWizardStep{1-5}Schema.safeParse()` + `clinicProfileSchema.safeParse()` for validation on step advance |
| `tessl__tailwind` | All styling | Applied: `cn()` utility, no inline `style={{}}`, responsive classes |
| `tessl__vitest` | Integration test patterns without `@testing-library/react` | Applied: pure logic tests (dynamic imports as `Record<string, unknown>`, schema parse, timing mocks, microcopy checks) |

## Context

T-fe-3 result: 7 components + microcopy SSoT — GREEN.
T-fe-2 result: 22 hooks but brand studio section hooks were MISSING (not in `api/` dir).
T-widget-1 was running parallel, touching `vitalia/frontend/widget/` only — disjoint per protocol.

## Discoveries

1. No `react-hook-form` or `@testing-library/react` installed in the main vitalia frontend.
   Integration tests must be pure logic (same pattern as T-fe-3 unit tests).

2. Brand studio hooks `use-brand-studio-sections.ts` + `use-brand-studio-section-patch.ts`
   were referenced in `03-arch-fe.md §4.1` but NOT created in T-fe-2 (only 22 hooks created).
   Created as part of T-fe-4.

3. T-widget-1 installed `@testing-library/react` in `widget/node_modules/` — vitest picked up
   `widget/node_modules/@testing-library/jest-dom/types/__tests__/` causing 8 failures in full run.
   Fixed: added `widget/**` to vitest.config.ts `exclude` array. Widget is a separate sub-package
   with its own `vitest.config.ts`.

4. Dynamic imports of `"use client"` components in tests typed as `never` under
   `moduleResolution: "bundler"` in some contexts → used `as Record<string, unknown>` cast
   in all test files for type safety (pattern matches T-fe-3 unit tests).

5. Functions coverage was 10.52% initially (below 20% threshold) because integration tests
   didn't call `vitaliaQueryKeys.*()` factory functions or `cn()`. Added targeted tests
   to cover query-keys factory functions and cn() utility.

## TDD RED → GREEN

RED confirmed before writing components:
- All 3 integration test files failed on import with "Failed to resolve import"
- Confirmed via `npx vitest run tests/integration/...` — 3 failed, no tests collected

GREEN after implementing:
- 175/175 tests pass
- Coverage: 99%+ stmts/branches, 42% funcs (threshold 20%), 99%+ lines

## Files Created

### New API hooks
- `src/features/vitalia/api/use-brand-studio-sections.ts` — GET brand studio sections list
- `src/features/vitalia/api/use-brand-studio-section-patch.ts` — PATCH per section_type

### New Client Components
- `src/features/vitalia/components/onboarding-step-1-client.tsx` — clinic profile form
- `src/features/vitalia/components/onboarding-step-2-client.tsx` — plan tier selection
- `src/features/vitalia/components/onboarding-step-3-client.tsx` — offer wizard launch bridge
- `src/features/vitalia/components/brand-studio-section-client.tsx` — 4-section autosave
- `src/features/vitalia/components/offer-wizard-client.tsx` — 5-step offer wizard

### New Integration Tests
- `tests/integration/onboarding-wizard-flow.test.ts` — A1 (41 tests)
- `tests/integration/brand-studio-autosave.test.ts` — A2 (11 tests)
- `tests/integration/offer-wizard-flow.test.ts` — A3 (22 tests + cn/query-keys coverage)

### Modified
- `src/features/vitalia/index.ts` — +15 new named exports (5 components + 2 hooks + 8 types + AUTOSAVE_DEBOUNCE_MS)
- `src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` — +5 component files to voseo scanner
- `vitest.config.ts` — `exclude: widget/**` to isolate sub-package tests

## Autosave Implementation

`AUTOSAVE_DEBOUNCE_MS = 500` exported constant.
`useRef` to hold pending `setTimeout`. `useCallback(triggerAutosave, [patchSection])` for stable ref.
Pattern: onChange → setSectionData → triggerAutosave (clears previous ref, sets new 500ms timeout).
On timeout: `patchSection(payload)` → setAutosaveStatus("saved") / setAutosaveStatus("error").

## Accessibility Applied

- `aria-busy` on loading/submitting states
- `aria-invalid` + `aria-describedby` on error fields
- `aria-live="polite"` + `aria-atomic="true"` on step content areas
- `aria-current="step"` on active wizard step
- `aria-current="page"` on active Brand Studio section tab
- `role="radiogroup"` on plan tier + clinic type pickers
- `role="alert"` on error messages
- `role="status"` on autosave badge
- `sr-only` inputs for radio button pairs (visual label + hidden input pattern)
