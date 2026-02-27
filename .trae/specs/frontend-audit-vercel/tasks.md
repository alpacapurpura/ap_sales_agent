# Tasks

- [x] Task 1: Analyze Project Configuration & Structure
  - [ ] SubTask 1.1: Verify `next.config.mjs` for performance optimizations (e.g., bundle analyzer, image optimization).
  - [ ] SubTask 1.2: Check `package.json` for dependency bloat or outdated packages.
  - [ ] SubTask 1.3: Review `eslint` and `prettier` config for best practices.

- [x] Task 2: Audit for Critical Performance Issues (Priority 1 & 2)
  - [ ] SubTask 2.1: Scan for Waterfall patterns (nested `await`, serial fetches) in Server Components and API routes.
  - [ ] SubTask 2.2: Analyze Bundle Size (barrel files, large imports, dynamic imports for heavy components).

- [x] Task 3: Audit for Rendering & Data Fetching (Priority 3 & 4)
  - [ ] SubTask 3.1: Review Server Components for proper data fetching and caching (`React.cache`, `unstable_cache`).
  - [ ] SubTask 3.2: Review Client Components for efficient data fetching (SWR/TanStack Query vs `useEffect`).

- [x] Task 4: Audit for Re-renders & UX (Priority 5, 6, 7)
  - [ ] SubTask 4.1: Identify unnecessary re-renders (missing `memo`, unstable props/callbacks).
  - [ ] SubTask 4.2: Check Image optimization (`next/image` usage, sizing).
  - [ ] SubTask 4.3: Review CLS contributors (fonts, images without dimensions).

- [x] Task 5: Generate Audit Report
  - [ ] SubTask 5.1: Compile findings into `frontend/AUDIT_REPORT.md`.

- [x] Task 6: Apply Critical Fixes
  - [ ] SubTask 6.1: Fix identified Waterfall issues.
  - [ ] SubTask 6.2: Optimize critical Bundle Size issues (e.g., remove barrel file usage in hot paths).

# Task Dependencies
- Task 5 depends on Task 1, 2, 3, 4.
- Task 6 depends on Task 5.
