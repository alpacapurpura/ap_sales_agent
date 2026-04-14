# Frontend Quality — Execution Tracker

**Started:** 2026-04-13
**Status:** Phase 1A COMPLETE ✅
**Current Phase:** Phase 1A — ESLint Setup (non-breaking rules) DONE

---

## Quick Resume for Next Agent

**What we're doing:** Upgrading frontend ESLint from ~10 rules to ~60+ rules, matching backend's ruff rigor (50+ rule sets).

**Key files to read first:**
1. `frontend/eslint.config.mjs` — new ESLint config with 60+ rules
2. `frontend/prettier.config.mjs` — Prettier config (Phase 2 prep)
3. `docs/mejoras-proceso/frontend-quality-improvements.md` — full proposal with all phases detailed

**What's done:** Phase 1A COMPLETE. 0 errors, ~12000 warnings across entire src/. TypeScript passes.

**What's next:** Phase 1B — switch key rules from warn → error (no-explicit-any, no-floating-promises, no-misused-promises).

**Critical rules:**
- Run lint/tests NATIVELY in WSL — never in Docker
- `cd frontend && npx <command>` for all frontend operations
- Each phase must pass lint + tests before moving to next

**Phase 1A Results:**
- Baseline: 13 warnings with old config
- After upgrade: 0 errors, ~12000 warnings (all Phase 1A non-breaking)
- TypeScript: ✅ passes with 0 errors
- Plugins installed: 12 new devDependencies
- Auto-fix applied: Prettier formatting (CRLF→LF), import ordering
- Manual fix: 1 `require()` → proper import in test file

---

## Phase Checklist

### ✅ Phase 1A: ESLint Setup (non-breaking rules)
**Status:** COMPLETE ✅

- [x] Install plugins: `@typescript-eslint/eslint-plugin`, `eslint-plugin-sonarjs`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-plugin-import`, `eslint-plugin-boundaries`, `eslint-plugin-react-perf`, `prettier`, `eslint-config-prettier`, `eslint-plugin-prettier`, `globals`
- [x] Update `eslint.config.mjs` with Phase 1A rules (warn mode only)
- [x] Run `npx eslint src/ --fix` for auto-fix initial (Prettier + import order)
- [x] Run `npx eslint src/` to count remaining violations: **0 errors, ~12000 warnings**
- [x] TypeScript check: `npx tsc --noEmit` passes with 0 errors
- [x] Create `prettier.config.mjs` (Phase 2 prep)
- [x] Manual fix: removed `require()` in test file, downgraded error-level rules to warn
- [x] Update this tracker

### ⬜ Phase 1B: ESLint Strict Rules
**Status:** BLOCKED (requires 1A)

- [ ] Switch Phase 1A rules from `warn` → `error`
- [ ] Add TypeScript strict rules (`no-explicit-any`, `no-floating-promises`, `no-misused-promises`)
- [ ] Add SonarJS cognitive complexity rule
- [ ] Add max-lines, max-depth, max-params rules
- [ ] Fix manual violations (non-auto-fixable)
- [ ] Run lint + verify < 50 violations
- [ ] Update this tracker

### ⬜ Phase 2: Prettier Integration
**Status:** BLOCKED (requires 1A)

- [ ] Create `prettier.config.mjs`
- [ ] Install `@trivago/prettier-plugin-sort-imports`, `prettier-plugin-tailwindcss`
- [ ] Integrate Prettier + ESLint in `eslint.config.mjs`
- [ ] Update `lint-staged` in `package.json`
- [ ] Run `npx prettier --write "src/**/*.{ts,tsx}"`
- [ ] Verify lint-staged works: `npx lint-staged`
- [ ] Update this tracker

### ⬜ Phase 3: FSD Enforcement (194 deep imports)
**Status:** BLOCKED (requires 1A + boundaries working in warn mode)

- [ ] Activate `eslint-plugin-boundaries` in warn mode
- [ ] Catalog all deep imports (4+ `../` levels) — found 194
- [ ] Create barrel exports in feature roots (`features/{name}/index.ts`)
- [ ] Move shared types to `lib/types/`
- [ ] Move shared utils to `lib/utils/`
- [ ] Fix all violations to use `@/` aliases or barrel exports
- [ ] Switch boundaries to error mode
- [ ] Run lint + verify 0 FSD violations
- [ ] Update this tracker

### ⬜ Phase 4: Coverage Thresholds
**Status:** BLOCKED (requires stable lint)

- [ ] Set Milestone 1: 20% thresholds in `vitest.config.mts`
- [ ] Run `npx vitest run --coverage` to identify failing files
- [ ] Add tests for critical paths
- [ ] Verify CI passes at 20%
- [ ] Update tracker with current coverage %

### ⬜ Phase 5: Additional Tools
**Status:** BLOCKED (optional)

- [ ] Install and configure `knip` (dead code detection)
- [ ] Install and configure `madge` (circular imports)
- [ ] Run `npx knip` and fix findings
- [ ] Run `npx madge --circular src/` and fix circular imports
- [ ] Add both to CI pipeline

---

## Installed Dependencies

**Phase 1A: ALL INSTALLED ✅**

| Package | Version | Notes |
|---------|---------|-------|
| eslint-plugin-sonarjs | 4.0.2 | Latest |
| eslint-plugin-import | 2.32.0 | Latest |
| eslint-plugin-boundaries | 6.0.2 | Latest (uses `dependencies` rule, not deprecated `element-types`) |
| eslint-plugin-react-perf | 3.x | Latest |
| prettier | 3.8.2 | Latest |
| eslint-config-prettier | 10.x | Latest |
| eslint-plugin-prettier | 5.x | Latest |
| globals | 16.x | Latest |
| @trivago/prettier-plugin-sort-imports | 5.x | Latest |
| prettier-plugin-tailwindcss | 0.7.2 | Latest |

---

## Violations Log

**After each lint run, record the count:**

| Date | Phase | Command | Violations | Notes |
|------|-------|---------|------------|-------|
| 2026-04-13 | Baseline (old config) | `npx eslint src/` | 13 warnings | Only nextjs + storybook rules |
| 2026-04-13 | Phase 1A | `npx eslint src/app/` | 0 errors, 366 warnings | After full config upgrade |
| 2026-04-13 | Phase 1A | `npx eslint src/lib/` | 0 errors, 341 warnings | |
| 2026-04-13 | Phase 1A | `npx eslint src/features/brand/` | 0 errors, 2148 warnings | Largest feature module |
| 2026-04-13 | Phase 1A | `npx eslint src/features/` | 0 errors, 11661 warnings | All features combined |
| 2026-04-13 | Phase 1A | `npx tsc --noEmit` | 0 errors | TypeScript type check passes |
| | | | | |
| | | | | |

---

## Deep Imports Catalog (Phase 3)

**Found 194 deep imports (4+ `../` levels) in `offer-studio/` and `growth-studio/`.**

_To populate during Phase 3:_

| File | Import | Depth | Fix Strategy |
|------|--------|-------|--------------|
| | | | |

---

## Notes & Learnings

### Phase 1A Learnings

- **ESLint flat config + `eslint-config-next`**: Next.js config ya incluye `jsx-a11y` y `react-hooks` — no re-registrar plugins, solo override reglas
- **SonarJS v4**: Algunas reglas tienen nombres diferentes a la doc online. Ver reglas disponibles con `node -e "console.log(Object.keys(require('eslint-plugin-sonarjs').rules))"`
- **Boundaries v6**: Regla renombrada de `element-types` → `dependencies`. Sintaxis de reglas cambió: `from: { type: "..." }` + `allow: { to: { type: [...] } }`
- **TypeScript + ESLint**: `no-undef` debe desactivarse — TypeScript ya maneja esto. `no-unused-vars` delegado a `@typescript-eslint/no-unused-vars`
- **Prettier + ESLint**: Usar `eslint-plugin-prettier/recommended` como último plugin — auto-aplica prettier durante `--fix`
- **Performance**: ESLint con `project: true` (type-aware) es lento en primer run (~3 min full scan). Usar directorios específicos para checks rápidos
- **CRLF vs LF**: Archivos con CRLF generan warnings de prettier. `endOfLine: "lf"` en prettier config + `npx prettier --write` fixea todos
- **Test files + require()**: Vitest mocks a veces usan `require()`. Preferir imports normales cuando es posible
- **Import no-duplicates**: Muy común en código existente — warn primero, fix manual después
- **12 plugins nuevos** vs ~10 reglas anteriores → ahora **60+ reglas**

---

## Reference Commands

```bash
# ESLint
cd frontend && npx eslint src/                    # Check all
cd frontend && npx eslint src/ --fix              # Auto-fix
cd frontend && npx eslint src/ 2>&1 | wc -l       # Count violations

# Prettier
cd frontend && npx prettier --write "src/**/*.{ts,tsx}"

# TypeScript check
cd frontend && npx tsc --noEmit

# Tests
cd frontend && npx vitest run
cd frontend && npx vitest run --coverage

# Dead code
cd frontend && npx knip

# Circular imports
cd frontend && npx madge --circular src/

# Lint-staged (simulate pre-commit)
cd frontend && npx lint-staged
```
