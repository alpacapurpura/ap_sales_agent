---
name: frontend-expert
description: Expert in Next.js App Router, Feature-Sliced Design, and shadcn/ui. Use for creating scalable, high-performance UI components with best practices for 2025.
---

# Frontend Expert Skill

## 1. Core Philosophy & Architecture

**"Integrate, Don't Destroy"**
- **Read First**: Before editing ANY file, you MUST read its full content to understand existing logic, exports, and dependencies.
- **Incremental Changes**: Make small, safe changes.

**Feature-Sliced Design (FSD) 2.0 (Simplified)**
- **Structure**:
  - `src/app`: Routes & Layouts only (Server Components).
  - `src/features`: Business logic (components, hooks, types).
  - `src/components`: Global UI (shadcn primitives, shared layouts).
  - `src/lib`: Utilities & API clients.
- **Reference**: See [fsd-cheatsheet.md](references/fsd-cheatsheet.md) for strict import rules.

## 2. Documentation Standards (AI-First)
**CRITICAL**: All code must be documented to be readable by OTHER AI agents.
- **Context over Content**: Explain *why* a component exists, not just what it does.
- **Constraints**: Explicitly state limitations (e.g., "Must be Client Component").
- **Reference**: See [ai-documentation.md](references/ai-documentation.md) for templates.

## 3. Technology Stack Standards
- **Framework**: Next.js 14+ (App Router).
- **Styling**: Tailwind CSS + shadcn/ui.
  - Use `cn()` for class merging.
  - **Mobile-First**: Base styles for mobile, `md:`/`lg:` for desktop.
- **State Management**:
  - **Server**: Server Actions for mutations, React Query for hydration.
  - **Client**: `useState`/`useReducer` for local UI state.
- **Forms**: `react-hook-form` + `zod`.
- **API & Auth**:
  - **Pattern**: Explicit Token Injection.
  - **Client**: Use `@/lib/http-client`.
  - **Reference**: See [api-standards.md](references/api-standards.md).

## 4. Implementation Guidelines

### A. Feature Creation (Automated)
Use the included script to scaffold new features correctly:
```bash
python3 .trae/skills/frontend-expert/scripts/scaffold_feature.py <feature-name>
```

### B. Component Structure (Container/Presenter)
- **Smart Container**: Handles logic/hooks (`useBrandSettings`).
- **Dumb Presenter**: UI-only, receives data/callbacks props.
- **Template**: Use `assets/templates/component.tsx` as a starting point.

### C. Shadcn UI Workflow
- Do not reinvent the wheel. Use Shadcn primitives (`@/components/ui/...`).
- **Immutability**: Do NOT modify `components/ui/*` internals unless critical.
- **Installation**: `npx shadcn@latest add [component]` (sync with Docker).

### D. Clean Code & Type Safety
- **Strict Types**: No `any`. Share types via `features/[name]/types`.
- **Zod Single Source**: Infer types from Zod schemas: `type FormValues = z.infer<typeof schema>`.

### E. Domain Specific Rules
- **Offer Metadata**: NEVER hardcode Offer Type labels or descriptions. ALWAYS use `OFFER_TYPE_METADATA` from `@/features/offer-studio/types/offer-metadata` to ensure business logic consistency (e.g., "Recurso Gratuito" instead of raw enum values).

## 5. Execution Protocol
1.  **Analyze**: Read file + imports. Identify Feature context.
2.  **Plan**: Check `package.json` for deps. Design for Server/Client split.
3.  **Execute**:
    - **New Feature**: Run `scaffold_feature.py`.
    - **New Component**: Copy `assets/templates/component.tsx`.
    - **Logic**: Implement hooks in `features/[name]/hooks`.
4.  **Document**: Add AI-Context comments to all new exports.
5.  **Verify**: Check import paths (no `../../`), types, and Mobile responsiveness.
