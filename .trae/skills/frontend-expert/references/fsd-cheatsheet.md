# Feature-Sliced Design (FSD) Cheatsheet

This project uses a simplified version of FSD adapted for Next.js App Router.

## 1. Directory Structure

### `src/features/` (The Core)
Everything related to a specific business domain lives here.
**Rule**: If you delete `src/features/brand`, the "Brand" functionality should completely disappear, but the app should still build (minus the specific routes).

Structure:
```
src/features/brand/
├── components/       # UI Components specific to Brand
│   ├── brand-form.tsx
│   └── avatar-uploader.tsx
├── hooks/           # Logic & State
│   ├── use-brand.ts
│   └── use-brand-mutations.ts
├── types/           # Domain Interfaces & Zod Schemas
│   └── index.ts
└── index.ts         # PUBLIC API (Barrel File)
```

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
