# T-fe-FOLLOWUP-POSTMERGE — Comunify FE Deferred Polish Items

**Created:** 2026-05-14  
**Origin:** REVIEW-fe.md audit iter 1 — items deferred from self-fix scope (non-blocking for merge, post-merge polish)  
**Story:** luana-comunify-bootstrap  

---

## Deferred Items (6)

### 1. Page stubs — full UI implementation

**REVIEW-fe.md Cat 11** — 14 page stubs exist under `src/app/` returning empty `<div>` placeholders. These are correct scaffolding: spec calls for phased delivery where pages are wired after BE validators pass.

**Action:** implement per-page UI after merge, following UI-SPEC.md section mapping. Priority order:
1. `/brand-studio` (onboarding entry point)
2. `/ladder` (offer ladder visualizer, partial component already done)
3. `/community` (feed + moderation)
4. `/subscriptions` (creator revenue view)
5. Remaining (voice-cloning, analytics, settings)

**Owner:** FE sprint post-merge.

---

### 2. Error boundaries — route-level wrapping

**REVIEW-fe.md Cat 3** — No `ErrorBoundary` at route level. Current async UI has React Query error states but no React class error boundary to catch render-phase exceptions.

**Action:** wrap each page layout in `src/app/[handle]/layout.tsx` with an `ErrorBoundary` component from `react-error-boundary`. Add `error.tsx` Next.js error file per route segment.

**Pattern:**
```tsx
// src/app/[handle]/error.tsx
"use client";
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div role="alert" className="flex flex-col gap-4 p-6">
      <p className="text-destructive">Ocurrió un error inesperado.</p>
      <button onClick={reset}>Reintentar</button>
    </div>
  );
}
```

---

### 3. ESLint 60+ rules — full wiring

**REVIEW-fe.md Cat 4** — `eslint.config.mjs` has basic rules but not the full 60+ rule set required by frontend-quality.md (sonarjs/cognitive-complexity, boundaries/dependencies, react-perf, etc.).

**Action:** align `eslint.config.mjs` with AISALESHT's `frontend/eslint.config.mjs` as reference. Key additions:
- `eslint-plugin-sonarjs` (cognitive-complexity ≤15, no-duplicate-string)
- `eslint-plugin-boundaries` (FSD dependency matrix)
- `eslint-plugin-react-perf` (no-inline-styles, no-jsx-spread)
- `@typescript-eslint/no-explicit-any` as error
- `@typescript-eslint/no-floating-promises` as error

Install: `npm install -D eslint-plugin-sonarjs eslint-plugin-boundaries eslint-plugin-react-perf`

---

### 4. Barrel index.ts — feature exports

**REVIEW-fe.md Cat 1** — No `index.ts` barrel at `src/features/comunify/index.ts`. Cross-component imports use deep paths.

**Action:** create `src/features/comunify/index.ts` exporting public surface:
```typescript
// Public API of the comunify feature
export * from "./api/query-keys";
export * from "./hooks/use-tenant-creator";
export type * from "./types/comunify.types";
export type * from "./types/ladder.types";
export type * from "./types/subscription.types";
// ... other public types
```

Named exports only — no default exports.

---

### 5. Coverage threshold — vitest config

**REVIEW-fe.md Cat 10** — `vitest.config.ts` has no `coverage.thresholds`. Tests are smoke-only (26 tests, ~40% coverage on covered files but overall low due to page stubs).

**Action:** after page implementations land, add:
```typescript
coverage: {
  thresholds: {
    statements: 20,
    branches: 20,
    functions: 20,
    lines: 20,
  },
}
```

Threshold enforcement deferred until page stubs are implemented (otherwise 14 empty pages tank line coverage unfairly).

---

### 6. Architecture decisions — cite in 03-arch-fe.md

**REVIEW-fe.md Cat 14** — `03-arch-fe.md` lacks explicit citations for:
- Why `useTenantId()` uses `organization?.id ?? user?.id` priority
- Why `comunifyFetch` is a custom wrapper (not AISALESHT's `fetchClient`)  
- Why page stubs are intentional scaffolding (phased delivery)
- Why `useSubscribe` is public-endpoint (no auth guard)

**Action:** append "Architecture Decisions" section to `03-arch-fe.md` with these 4 decision records (ADR-lite format: context + decision + rationale).

---

## Summary

| # | Item | Blocking merge? | Est. effort |
|---|---|---|---|
| 1 | Page stub UI implementation | No | L (per-page sprint) |
| 2 | Error boundaries | No | S (1h) |
| 3 | ESLint 60+ wiring | No | S (2h) |
| 4 | Barrel index.ts | No | XS (30min) |
| 5 | Coverage thresholds | No | XS (10min, after pages done) |
| 6 | Decisions cite in 03-arch-fe.md | No | XS (30min) |

All items deferred with PM awareness. None are security or correctness issues (those were fixed in iter 1 self-fix).
