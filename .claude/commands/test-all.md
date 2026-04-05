Run full CI suite (backend + frontend + E2E smoke) natively. Mirrors the `quality-gates` job in `.github/workflows/deploy-prod.yml`.

**IMPORTANT:** Backend tools are in `backend/.venv/bin/`. Frontend tools are in `frontend/node_modules/.bin/`.
If tools are missing, install dev dependencies first.

## Steps

### 0. Pre-flight: verify tools
```bash
cd backend && .venv/bin/ruff --version && .venv/bin/pytest --version && cd ../frontend && npx vitest --version
```
If anything fails, STOP and report the fix needed.

### 1. Backend lint (ruff check)
```bash
cd backend && .venv/bin/ruff check src/ --no-cache
```

### 2. Backend format check (ruff format)
```bash
cd backend && .venv/bin/ruff format --check src/
```
Verifies formatting without modifying files. If this fails, run `ruff format src/` to fix.

### 3. Backend architectural fitness tests
```bash
cd backend && .venv/bin/pytest tests/architecture/ -v
```
Validates DDD boundaries, API contracts, and coding conventions. If this fails,
a structural rule was violated — fix before continuing with unit tests.

### 4. Backend tests with coverage (pytest)
```bash
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term -x -q --tb=short
```
Note the overall coverage % from the output. Threshold: **60%** (CI will fail below this).

### 5. Backend security audit (pip-audit)
```bash
cd backend && .venv/bin/pip-audit --strict --desc
```
Checks Python dependencies for known CVEs. `--strict` fails on ANY vulnerability.

### 6. Frontend types (tsc)
```bash
cd frontend && npx tsc --noEmit
```

### 7. Frontend lint (ESLint)
```bash
cd frontend && npx next lint
```

### 8. Frontend tests with coverage (vitest)
```bash
cd frontend && npx vitest run --coverage
```
Note the overall coverage % from the output. Thresholds: **statements 20%, branches 15%, functions 15%, lines 20%**.

### 9. Frontend security audit (npm audit)
```bash
cd frontend && npm audit --audit-level=high
```
Checks NPM dependencies for known vulnerabilities (HIGH and CRITICAL severity).

### 10. E2E Smoke Tests (Playwright)
```bash
make e2e-smoke
```
This runs `@smoke`-tagged Playwright tests against the running dev environment.
If containers are not running, this step will FAIL — the dev must run `make dev` first.

### 11. Migration verification (fresh DB)
Creates a temporary database and runs ALL migrations from scratch to verify they're correct and idempotent.
```bash
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_test;"
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec -t visionarias_brain_dev bash -c "cd /app && DATABASE_URL=postgresql://postgres:postgres@postgres:5432/migration_test alembic upgrade head"
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
If `alembic upgrade head` fails on the fresh DB, there is a broken or non-idempotent migration. Fix it before deploying.

### 12. Summary
Report a table:

| Step | Result | Coverage |
|---|---|---|
| Backend lint (ruff check) | PASS/FAIL | — |
| Backend format (ruff format) | PASS/FAIL | — |
| Arch fitness | PASS/FAIL (5 tests) | — |
| Backend tests | X passed | XX% (min 60%) |
| Backend security (pip-audit) | PASS/FAIL (N vulns) | — |
| Frontend types (tsc) | PASS/FAIL | — |
| Frontend lint (ESLint) | PASS/FAIL (N warnings) | — |
| Frontend tests | X passed | XX% (min 20%) |
| Frontend security (npm audit) | PASS/FAIL (N vulns) | — |
| E2E Smoke | X passed | — |
| Migrations (fresh DB) | PASS/FAIL | — |

If all pass: "CI suite PASS — safe to deploy."
If any fail: list failures with file:line references.
