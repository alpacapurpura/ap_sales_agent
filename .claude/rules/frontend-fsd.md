---
globs: "frontend/src/**/*.{ts,tsx}"
description: Feature-Sliced Design rules for frontend code
---

# Frontend FSD Rules

## Architecture (FSD-Lite)
```
frontend/src/
  app/           # Next.js App Router pages (thin — delegate to features)
  components/
    ui/          # Shadcn UI primitives (auto-generated, don't edit)
    shared/      # Cross-feature layout components (sidebar, header)
  features/
    {domain}/    # Feature slices (brand/, offer/, copilot/, etc.)
      api/       # React Query hooks, API adapters
      components/
      hooks/
      config/    # Feature-specific configuration
      context/   # React Context providers (if needed)
      types/
      utils/
  lib/           # Utilities, API client, design system registry
```

## Constraints
- Server Components by default; add `"use client"` only when needed (hooks, event handlers)
- React Query (`@tanstack/react-query`) for all data fetching
- React Hook Form + Zod for form validation
- No `any` type — use `unknown` + type guards
- No default exports (except Next.js pages)
- Tailwind CSS + `cn()` utility for styling
- `fetchClient` auto-injects `X-Tenant-ID` — always use it for API calls

## Cross-Feature Imports
- **Default: forbidden.** Features cannot import from other features.
- **Allowed exceptions:** `copilot` exports (`WithCopilot`, `useCopilotFieldSync`) may be imported by any feature — it's an infra-like concern for AI form enhancement.
- If you need shared types or components across features, move them to `components/shared/` or `lib/`.
