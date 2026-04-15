# Code Audit Commands
Last verified: 2026-04-15

## Duplication (jscpd)
```bash
# Frontend (threshold 5%)
npx jscpd frontend/src/ --threshold 5
# Backend
npx jscpd backend/src/ --threshold 5
# Both + HTML report
npx jscpd frontend/src/ backend/src/ --reporters html --output .jscpd-report/
```
Config: `.jscpd.json` at repo root. Excludes: tests, ui/, migrations, node_modules.

Baseline (2026-04-15): Frontend 4.52% (338 clones), Backend 3.63% (205 clones).

## Dead code (knip)
```bash
cd frontend && npx knip
```
Config: `frontend/knip.config.ts`. Explicit entry points (Next.js pages). Known false positives for barrel spreads and devDeps.

## Circular imports (madge)
```bash
cd frontend && npx madge --circular src/ --extensions ts,tsx
```
Known: 2 cycles in offer-studio (offer-shell ↔ header-row files).

## File naming (eslint-plugin-check-file)
Enforced via ESLint (`warn`):
- Components (.tsx): PascalCase
- API/types/utils/config (.ts): kebab-case
- Hooks (.ts): camelCase (useXxx)
- Folders: kebab-case

## JSDoc (eslint-plugin-jsdoc)
Enforced via ESLint (`warn`): exported functions + classes need JSDoc.

## Docstring coverage — backend (interrogate)
```bash
cd backend && .venv/bin/interrogate -vv src/modules/ src/shared/
```
Config: `pyproject.toml [tool.interrogate]`. Excludes: tests, alembic, scripts, admin.

## Full audit
```bash
make audit-quality  # or run individually:
npx jscpd frontend/src/ backend/src/ --threshold 5
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd frontend && npx tsc --noEmit
cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
cd frontend && npx vitest run
```
