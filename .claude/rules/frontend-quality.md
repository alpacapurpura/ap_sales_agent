---
globs: "frontend/**/*.{ts,tsx,mjs,mts}"
description: Stub — invoca frontend-expert skill
---

# Frontend Quality

- ESLint 0 errors. Config `frontend/eslint.config.mjs`. 60+ rules. Plugins: sonarjs, boundaries, react-perf, prettier.
- TypeScript strict, 0 errors.
- Vitest 1063+ tests, 20% coverage threshold (actual ~25%).
- 10 architecture fitness tests `src/__tests__/architecture/`. Ratchet allowlists shrink only.

Detalle (rules error/warn, per-file overrides, jscpd/knip/madge, FSD boundaries, arch tests list) en `frontend-expert` skill → `references/frontend-quality.md`.

**No-skip:** disable ESLint rule sin justification comment. `// eslint-disable-next-line` solo con explanation. Many violations → refactor, not disable.
