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
