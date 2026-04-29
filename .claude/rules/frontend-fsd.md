---
globs: "frontend/src/**/*.{ts,tsx}"
description: Frontend FSD-Lite
---

# Frontend FSD

```
frontend/src/
  app/                 # Next.js App Router (thin)
  components/{ui,shared}/
  features/{domain}/   # api/, components/, hooks/, config/, context/, types/, utils/
  lib/                 # API client, tokens, utils
  hooks/               # Global hooks
```

## Boundary matrix (`boundaries/dependencies: error`, 0 violations)

| From \ To | feature | feature:own | shared | ui | lib | util | hooks | providers |
|---|---|---|---|---|---|---|---|---|
| app | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| feature | — | own only | ✅ | — | ✅ | ✅ | — | — |
| feature:own | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| shared | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| lib | — | — | — | — | — | ✅ | — | — |

Excepciones: `feature:own` → `feature` (sub-components context). `shared` → `feature(:own)` (sidebar/tenant-switcher).

## Constraints
- Server Components default. `"use client"` solo cuando necesario.
- React Query (data fetch). RHF + Zod (forms). Tailwind + `cn()`.
- No `any` (`unknown` + type guards). No default exports (excepto Next pages).
- `fetchClient` auto-inyecta `X-Tenant-ID`.

## Cross-feature imports
Forbidden default. Excepción: `copilot` (infra-like). Shared → `components/shared/` o `lib/`.

## Studio section pages
Patrón lazy-loading per-section (brand-studio, offer-studio, futuros). Detalle + arch tests + factory pattern → `frontend-expert` skill (`references/studio-section-pages.md`).
