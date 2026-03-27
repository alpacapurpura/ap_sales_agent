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
      components/
      hooks/
      utils/
      types/
  lib/           # Utilities, API client, design system registry
```

## Constraints
- Server Components by default; add `"use client"` only when needed (hooks, event handlers)
- React Query (`@tanstack/react-query`) for all data fetching
- React Hook Form + Zod for form validation
- No deep imports: features cannot import from other features
- No default exports (except Next.js pages)
- No `any` type — use `unknown` + type guards
- Tailwind CSS + `cn()` utility for styling
- `fetchClient` auto-injects `X-Tenant-ID` — always use it for API calls
