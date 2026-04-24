---
globs: "frontend/src/**/*.{ts,tsx}"
description: Feature-Sliced Design rules for frontend code
---

# Frontend FSD Rules
Last verified: 2026-04-15

## Architecture (FSD-Lite)
```
frontend/src/
  app/           # Next.js App Router (thin)
  components/
    ui/          # Shadcn primitives (auto-gen, don't edit)
    shared/      # Cross-feature layout
  features/
    {domain}/    # api/, components/, hooks/, config/, context/, types/, utils/
  lib/           # Utils, API client, design tokens
  hooks/         # Global hooks (use-debounce, etc.)
```

## Boundary Matrix (enforced `boundaries/dependencies: error`, 0 violations)

| From \ To | feature | feature:own | shared | ui | lib | util | hooks | providers |
|---|---|---|---|---|---|---|---|---|
| **app** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **feature** | — | own only | ✅ | — | ✅ | ✅ | — | — |
| **feature:own** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| **shared** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| **lib** | — | — | — | — | — | ✅ | — | — |

### Pragmatic exceptions
- `feature:own` imports `feature` (any root) — sub-components need parent context
- `shared` imports `feature`/`feature:own` — sidebar/tenant-switcher need settings hooks
- `boundaries/no-unknown: "off"` — ESLint ignores prevent `ui/**` registering elements

### Element types
`app` (src/app/*), `feature` (src/features/*), `feature:own` (src/features/*/**), `shared` (src/components/shared/*), `ui` (src/components/ui/*), `lib` (src/lib/*), `util` (src/lib/utils/*), `hooks` (src/hooks/*), `providers` (src/components/providers/*).

## Constraints
- Server Components default; `"use client"` only si needed
- React Query para data fetching
- React Hook Form + Zod para forms
- No `any` — use `unknown` + type guards
- No default exports (except Next.js pages)
- Tailwind + `cn()` para styling
- `fetchClient` auto-injects `X-Tenant-ID`

## Cross-Feature Imports
- **Default: forbidden.** Features no importan de otras features.
- **Allowed:** `copilot` exports importable por cualquier feature (infra-like).
- Shared types/components → `components/shared/` o `lib/`.

## Studio section pages (brand, offer, futuros studios con form-runtime)

Patrón homologado con lazy-loading real per-section via `next/dynamic`:

```
features/{studio}-studio/pages/
  section-slugs.ts            ← server-safe: SLUGS[] + is{Studio}StudioSection(slug)
  SectionDispatcher.tsx       ← "use client", mapa next/dynamic per slug
  sections/
    {slug}-page.tsx           ← named export, importa SOLO su schema
```

Contrato:
- **Server route** (`app/.../[section]/page.tsx`): importa solo
  `section-slugs.ts` (server-safe gate). Valida slug, delega al
  `SectionDispatcher` client con props. Nunca importa schemas ni
  componentes `"use client"`.
- **SectionDispatcher.tsx**: `"use client"`. Bootstrap side-effect del
  action registry. Cada entry del mapa es
  `dynamic(() => import("./sections/X-page").then(m => ({ default: m.XPage })))`.
- **sections/*-page.tsx**: named export (no `export default` — respeta
  `test-no-default-exports`). Importa su schema individual desde
  `schemas/{slug}.schema.ts`, NO el barrel `schemas/index.ts`.
- **Factory opcional** (offer-studio usa `create-offer-section-page.tsx`
  por guard de edition-scope + save handler memoizado).
- **Shared primitives** en `src/lib/studio-section-page/`:
  `SectionPage` (wrapper presentacional), `SectionPageLoading`
  (fallback de `next/dynamic`).

Prohibido:
- `section-pages.tsx` (monolítico) o `section-page-map.ts` con imports
  estáticos de componentes de sección.
- Side-effect `import "@/features/{studio}/actions/registry"` en el
  barrel de schemas — debe vivir en `SectionDispatcher.tsx`.
- Importar otra sección dentro de un `*-page.tsx` (rompe chunk
  isolation de Turbopack).

Arch tests que enforzan:
- `test-studio-sections-lazy-loading.test.ts`
- `test-studio-structure-parity.test.ts`
