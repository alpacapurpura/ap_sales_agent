# T-fe-1 Impl Log — Next.js 16 App Router scaffolding

## Ticket
**T-fe-1** — Next.js 16 App Router scaffolding + routes structure  
**Story** — luana-vitalia-bootstrap  
**Date** — 2026-05-14  
**Builder** — builder-frontend (Sonnet 4.6)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, ESLint config patterns | Applied boundary matrix from rules/frontend-fsd.md — app→all, features→shared/lib/ui, shared→ui/lib |
| `tessl__react-patterns` | Error boundaries, Server-first, accessible markup | Server Components default (no `"use client"`), semantic HTML `<section aria-label>`, Spanish neutro h1 headings |
| `tessl__nextjs-app-router-modularization` | Next.js 16 async params, page/layout Server Component boundaries | `params: Promise<{ id: string }>` pattern applied to all dynamic routes; `generateMetadata` async |
| `tessl__tailwind` | Token references, no inline style | Tailwind utilities only, vitalia brand tokens via CSS vars in `tailwind.config.ts` |

## Files Created / Modified

### New route skeleton pages (21 total)
- `src/app/(auth)/sign-in/page.tsx` — Clerk sign-in placeholder
- `src/app/(auth)/sign-up/page.tsx` — Clerk sign-up placeholder
- `src/app/onboarding/layout.tsx` — onboarding layout with progress bar placeholder
- `src/app/onboarding/step-1/page.tsx` — clínica info step
- `src/app/onboarding/step-2/page.tsx` — horario step
- `src/app/onboarding/step-3/page.tsx` — confirmación step
- `src/app/(dashboard)/layout.tsx` — sidebar + header placeholders
- `src/app/(dashboard)/page.tsx` — dashboard home
- `src/app/(dashboard)/brand-studio/page.tsx` — brand studio index
- `src/app/(dashboard)/brand-studio/[section]/page.tsx` — dynamic section (async params)
- `src/app/(dashboard)/offers/page.tsx` — offers list
- `src/app/(dashboard)/offers/new/page.tsx` — new offer wizard placeholder
- `src/app/(dashboard)/offers/[id]/page.tsx` — offer detail (async params)
- `src/app/(dashboard)/bookings/page.tsx` — bookings calendar
- `src/app/(dashboard)/bookings/[id]/page.tsx` — booking detail (async params)
- `src/app/(dashboard)/treatments/page.tsx` — treatments list
- `src/app/(dashboard)/treatments/[id]/page.tsx` — treatment detail (async params)
- `src/app/(dashboard)/treatments/[id]/followup/page.tsx` — treatment followup (async params)
- `src/app/(dashboard)/patients/page.tsx` — patients list
- `src/app/(dashboard)/patients/[id]/page.tsx` — patient detail (async params)
- `src/app/(dashboard)/appointments/page.tsx` — appointments calendar
- `src/app/(dashboard)/medical-compliance/page.tsx` — medical compliance dashboard
- `src/app/public/[clinic-slug]/page.tsx` — public clinic profile (async params)
- `src/app/public/[clinic-slug]/booking/page.tsx` — public booking form (async params)

### Modified files
- `src/app/layout.tsx` — updated metadata, body className, TODO for T-fe-2 providers
- `tsconfig.json` — added `"types": ["vitest/globals", "node"]`, `.next/types/**/*.ts` include, excluded `e2e/**` and `playwright.config.ts`
- `eslint.config.mjs` — replaced with FSD-Lite boundaries config using eslint-plugin-boundaries v6 `boundaries/dependencies` rule
- `tailwind.config.ts` — added `src/features/**`, `widget/src/**` content paths, vitalia brand color tokens
- `package.json` — added dev deps: `@eslint/js`, `@types/node`, `@types/react`, `@types/react-dom`, `eslint`, `eslint-config-next`, `eslint-plugin-boundaries`, `globals`, `tailwindcss`, `typescript-eslint`

## Decisions

**D1: eslint-plugin-boundaries v6 API** — migrated from deprecated `boundaries/element-types` (v5 selector syntax) to `boundaries/dependencies` with object selectors `{ from: { type: "..." }, allow: { to: { type: [...] } } }`. Eliminated all deprecation warnings.

**D2: Vitest globals in tsconfig** — added `"vitest/globals"` to `types` array to resolve `describe`/`it`/`expect` TypeScript errors in existing smoke test file.

**D3: playwright.config.ts excluded from tsconfig** — added to `exclude` to prevent `Cannot find module '@playwright/test'` since playwright is not installed in vitalia yet (installed at monorepo root).

**D4: @luana/ui-kit not installed** — arch spec references `@luana/ui` and `@luana/shared` but neither is installed in vitalia yet. T-fe-1 skeleton pages avoid importing these. T-fe-2+ will add package references.

**D5: Spanish neutro tuteo** — all h1/label/aria-label strings use tuteo: "Selecciona", "Define", "prefieres" — no voseo.

## Validators

| Validator | Command | Result |
|---|---|---|
| V-NF-3 tsc --noEmit | `npx tsc --noEmit` | PASS (0 errors) |
| V-NF-4 eslint src/ | `npx eslint src/ --cache --cache-location .eslintcache` | PASS (0 errors, 0 warnings) |
