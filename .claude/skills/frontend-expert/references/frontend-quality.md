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
|---|---|
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

*JSX exception: `checksVoidReturn: { attributes: false, arguments: false }` → prevents 148 false errors en React handlers (onClick, onSubmit). Sin esto, every async handler flags.

### Warn rules (visible, no block)

| Rule | Value |
|---|---|
| `max-lines` | 350 (skipBlank/Comments) |
| `max-lines-per-function` | 100 |
| `max-nested-callbacks` | 4 |
| `complexity` | 20 |
| `no-console` | warn (allow: warn, error) |
| `@typescript-eslint/no-unsafe-*` (5) | warn |
| `react-perf/jsx-no-new-*` (4) | warn |
| `sonarjs/*` (15) | warn |
| `import/order`, `import/no-cycle` | warn |

Test/mock files: type-check off, max-lines off, no-explicit-any → warn.

## TypeScript: strict mode, 0 errors

## Vitest: 1063 tests, 20% threshold
Actual: 25%/21%/22%/25% (stmts/branches/funcs/lines). Config: `frontend/vitest.config.mts`.

## Fast scan
```bash
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
```

## Code quality tools

| Tool | Command | Checks |
|---|---|---|
| jscpd | `npx jscpd frontend/src/ --threshold 5` | Dup (baseline 4.52%) |
| check-file | via ESLint (warn) | PascalCase components, kebab-case non-components |
| jsdoc | via ESLint (warn) | JSDoc on exported fns/classes |
| knip | `cd frontend && npx knip` | Dead code (`knip.config.ts`) |
| madge | `npx madge --circular src/ --extensions ts,tsx` | Circular imports |

## Known issues
- 2 circular deps: `offer-shell.tsx` ↔ `offer-shell-header-row*.tsx`. Fix: extract hooks → `offer-shell-context.ts`.
- knip false positives: barrel spreads, Next.js routes, devDeps en config files. Mitigated `knip.config.ts` entry points.
- 323 check-file warnings + 616 jsdoc warnings (warn mode, fix progressive).

## 10 Architecture Fitness Tests

Run: `cd frontend && npx vitest run src/__tests__/architecture/`

| Test | Enforces |
|---|---|
| `test-component-naming` | `.tsx` en components/ = PascalCase |
| `test-file-naming` | `.ts(x)` en hooks/api/types/utils/config/lib/context/store/services/ = kebab-case |
| `test-folder-naming` | Dirs under features/ = kebab-case |
| `test-hook-location` | `export function use[A-Z]` only hooks/ api/ Context store/ |
| `test-no-default-exports` | No `export default` en features/ |
| `test-no-duplicate-names` | No same component basename cross features |
| `test-feature-structure` | Top-level feature dirs = canonical names |
| `test-api-location` | `fetchClient` only en api/ |
| `test-studio-sections-lazy-loading` | brand/offer studios usan `next/dynamic` per section; Server routes solo importan section-slugs + dispatcher |
| `test-studio-structure-parity` | brand + offer mantienen misma estructura `pages/{section-slugs, SectionDispatcher, sections/}` |

**Ratchet:** `KNOWN_*` allowlists frozen 2026-04-15. Solo shrink. Fix: rename/move, update imports, `npx tsc --noEmit`, remove from allowlist.

## FSD boundaries
`.claude/rules/frontend-fsd.md`.

## Notas
- NO disable ESLint rules sin justificación comment
- `// eslint-disable-next-line` solo con explanation
- Many violations → refactor, not disable
- Imports order: external → internal → relative → types
