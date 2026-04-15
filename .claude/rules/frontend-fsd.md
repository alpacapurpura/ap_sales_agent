---
globs: "frontend/src/**/*.{ts,tsx}"
description: Feature-Sliced Design rules for frontend code
---

# Frontend FSD Rules
Last verified: 2026-04-15

## Architecture (FSD-Lite)
```
frontend/src/
  app/           # Next.js App Router pages (thin — delegate to features)
  components/
    ui/          # Shadcn UI primitives (auto-generated, don't edit)
    shared/      # Cross-feature layout (sidebar, header)
  features/
    {domain}/    # Feature slices: api/, components/, hooks/, config/, context/, types/, utils/
  lib/           # Utilities, API client, design system registry
  hooks/         # Global hooks (use-debounce, etc.)
```

## Boundary Matrix (enforced: `boundaries/dependencies: error`, 0 violations)

| From \ To | feature | feature:own | shared | ui | lib | util | hooks | providers |
|-----------|---------|-------------|--------|----|-----|------|-------|-----------|
| **app** | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ |
| **feature** | — | own only | ✅ | — | ✅ | ✅ | — | — |
| **feature:own** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| **shared** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| **lib** | — | — | — | — | — | ✅ | — | — |

### Pragmatic exceptions (deliberate)
- `feature:own` imports `feature` (any root) — sub-components need parent context.
- `shared` imports `feature`/`feature:own` — sidebar/tenant-switcher need settings hooks.
- `boundaries/no-unknown: "off"` — ESLint ignores prevent `ui/**` from registering as elements.

### Element types
`app` (src/app/*), `feature` (src/features/*), `feature:own` (src/features/*/**), `shared` (src/components/shared/*), `ui` (src/components/ui/*), `lib` (src/lib/*), `util` (src/lib/utils/*), `hooks` (src/hooks/*), `providers` (src/components/providers/*).

## Constraints
- Server Components by default; `"use client"` only when needed
- React Query for all data fetching
- React Hook Form + Zod for forms
- No `any` — use `unknown` + type guards
- No default exports (except Next.js pages)
- Tailwind CSS + `cn()` for styling
- `fetchClient` auto-injects `X-Tenant-ID`

## Cross-Feature Imports
- **Default: forbidden.** Features cannot import from other features.
- **Allowed:** `copilot` exports may be imported by any feature (infra-like concern).
- Shared types/components → `components/shared/` or `lib/`.
