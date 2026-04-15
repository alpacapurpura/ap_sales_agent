# Frontend Technology Stack
Last verified: 2026-04-15

## Core
- Next.js 16.2.3 (App Router, React Server Components)
- React 19 (via Next.js 16)
- TypeScript (strict mode)

## UI & Styling
- Tailwind CSS v3.4+ (utility-first)
- Shadcn UI (Radix Primitives, `components/ui/`)
- Lucide React (icons)
- `cn()` = clsx + tailwind-merge

## Data & State
- TanStack Query v5 (primary data fetching — all API hooks)
- Zustand (client-side UI state where needed)
- nuqs (URL state management)
- React Hook Form + Zod (form validation)

## Auth & API
- Clerk (auth middleware, `X-Tenant-ID` injection)
- `fetchClient` (`lib/http-client.ts`) — auto-injects tenant header

## Testing
- Vitest + happy-dom (unit tests, 1063 tests, 20% coverage threshold)
- Playwright (E2E — smoke + regression suites)

## Code Quality
- ESLint (60+ rules: sonarjs, boundaries, react-perf, typescript-eslint, prettier)
- Prettier (format via eslint-plugin-prettier)
- knip (dead code detection)
- madge (circular dependency detection)

## Dev Tools
- eslint-plugin-boundaries v6 (FSD enforcement)
- eslint-plugin-sonarjs v4 (cognitive complexity)
- eslint-plugin-react-perf (inline prop warnings)
- prettier-plugin-tailwindcss (class sorting)
- @trivago/prettier-plugin-sort-imports
