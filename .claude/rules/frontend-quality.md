---
globs: "frontend/**/*.{ts,tsx,mjs,mts}"
description: ESLint thresholds, TypeScript strict, Vitest coverage, complexity limits
---
# Frontend Quality
Last verified: 2026-04-15

## ESLint: 0 errors, ~4924 warnings
Config: `frontend/eslint.config.mjs`. 60+ rules. Plugins: sonarjs, boundaries, react-perf, prettier.

### Error rules (block build)

| Rule | Value |
|------|-------|
| `sonarjs/cognitive-complexity` | 15 |
| `max-depth` | 4 |
| `max-params` | 4 |
| `no-debugger`, `no-eval`, `no-implied-eval`, `no-var` | error |
| `no-alert`, `no-empty`, `prefer-const` | error |
| `@typescript-eslint/no-explicit-any` | error |
| `@typescript-eslint/no-floating-promises` | error |
| `@typescript-eslint/no-misused-promises` | error* |
| `@typescript-eslint/no-var-requires`, `no-require-imports` | error |
| `react-hooks/rules-of-hooks` | error |
| `boundaries/dependencies` | error (0 violations) |

*JSX exception: `checksVoidReturn: { attributes: false, arguments: false }` — prevents 148 false errors on React event handlers (onClick, onSubmit). Without this, every async handler flags.

### Warn rules (visible, not blocking)

| Rule | Value |
|------|-------|
| `max-lines` | 350 (skipBlankLines/Comments) |
| `max-lines-per-function` | 100 |
| `max-nested-callbacks` | 4 |
| `complexity` | 20 |
| `no-console` | warn (allow: warn, error) |
| `@typescript-eslint/no-unsafe-*` (5 rules) | warn |
| `react-perf/jsx-no-new-*` (4 rules) | warn |
| `sonarjs/*` (15 rules) | warn |
| `import/order`, `import/no-cycle` | warn |

Test/mock files: type-checking disabled, max-lines off, no-explicit-any → warn.

## TypeScript: strict mode, 0 errors

## Vitest: 1063 tests, 20% threshold
Actual: 25%/21%/22%/25% (stmts/branches/funcs/lines). Config: `frontend/vitest.config.mts`.

## Fast scan
```bash
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
```

## Known issues
- 2 circular deps: `offer-shell.tsx` ↔ `offer-shell-header-row*.tsx`. Fix: extract hooks to `offer-shell-context.ts`.
- Knip: `npx knip` — many false positives (barrel spreads, Next.js routes, devDeps in config files).
- Madge: `npx madge --circular src/ --extensions ts,tsx`

## FSD boundaries
See `.claude/rules/frontend-fsd.md`.

## Notas para Agentes
- NO disable ESLint rules without justification comment
- `// eslint-disable-next-line` only with explanation
- Many violations in file → refactor, not disable
- Imports ordered: external → internal → relative → types
