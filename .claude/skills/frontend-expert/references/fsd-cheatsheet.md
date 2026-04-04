# Feature-Based Architecture (FSD-Inspired) Cheatsheet

> **Constraints:** `.claude/rules/frontend-fsd.md` (auto-loaded). This file provides extended context and examples.

This project uses a pragmactic Feature-Based architecture inspired by FSD principles, but without strict layers like widgets/entities unless necessary.

## 1. Directory Structure

### `src/features/` (The Core)
Everything related to a specific business domain lives here.
**Rule**: If you delete `src/features/{domain}`, the {domain} functionality should completely disappear, but the app should still build (minus the specific routes).

Structure:
```
src/features/{domain}/
├── components/       # UI Components specific to this feature
├── hooks/           # Logic & State
├── types/           # Domain Interfaces & Zod Schemas
├── utils/           # Helper functions
└── index.ts         # PUBLIC API (Barrel File)
```

**Note:** We do NOT strictly enforce `entities` or `widgets` layers. Logic should be kept within the `feature` unless it is genuinely shared across multiple features (in which case, refactor to `shared` or a common feature).

### `src/components/` (The Shared)
- **`ui/`**: Shadcn primitives (Button, Input). **DO NOT MODIFY** logic here.
- **`shared/`**: Global layout components (Sidebar, Navbar, Footer) used across multiple features.

### `src/app/` (The Router)
Minimal logic. Responsible only for:
1.  Routing (Folders = URLs)
2.  Layouts (`layout.tsx`)
3.  Metadata (`page.tsx`)
4.  Data Fetching (Server Components) -> Passing data to Feature Components.

## 2. The "Public API" Rule
Cross-feature imports are restricted.

**✅ Correct:**
`import { BrandCard } from "@/features/brand";` (Importing from the barrel file)

**❌ Incorrect:**
`import { BrandCard } from "@/features/brand/components/brand-card";` (Deep import violation)

**Why?**
Deep imports couple your code to the internal structure of another module. The `index.ts` acts as a contract.

## 3. Workflow for New Features
1.  **Create Directory**: `src/features/<name>`
2.  **Scaffold**: Create `components`, `hooks`, `types`.
3.  **Export**: Expose only the necessary components/hooks in `index.ts`.
4.  **Route**: Create `src/app/(dashboard)/<name>/page.tsx` and use the exported components.
