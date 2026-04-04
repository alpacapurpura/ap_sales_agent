Run full CI suite (backend + frontend + E2E smoke) inside Docker. Mirrors the `quality-gates` job in `.github/workflows/deploy-prod.yml`.

**IMPORTANT:** Backend container must be built with `target: dev` (not `final`) to have pytest/ruff.
If tools are missing, fix `docker-compose.yml` api_dev target and rebuild.

## Steps

### 0. Pre-flight: verify tools
```bash
docker exec -t visionarias_brain_dev bash -c "which pytest && which ruff" && docker exec -t visionarias_client_dev sh -c "npx vitest --version"
```
If anything fails, STOP and report the fix needed.

### 1. Backend lint (ruff)
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"
```

### 2. Backend tests with coverage (pytest)
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest --cov=src/modules --cov=src/shared --cov-report=term -x -q --tb=short"
```
Note the overall coverage % from the output. Threshold: **60%** (CI will fail below this).

### 3. Frontend types (tsc)
```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
```

### 4. Frontend lint (ESLint)
```bash
docker exec -t visionarias_client_dev npx next lint
```

### 5. Frontend tests with coverage (vitest)
```bash
docker exec -t visionarias_client_dev npx vitest run --coverage
```
Note the overall coverage % from the output. Thresholds: **statements 20%, branches 15%, functions 15%, lines 20%**.

### 6. E2E Smoke Tests (Playwright)
```bash
make e2e-smoke
```
This runs `@smoke`-tagged Playwright tests against the running dev environment.
If containers are not running, this step will FAIL — the dev must run `make dev` first.

### 7. Migration verification (fresh DB)
Creates a temporary database and runs ALL migrations from scratch to verify they're correct and idempotent.
```bash
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_test;"
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec -t visionarias_brain_dev bash -c "cd /app && DATABASE_URL=postgresql://postgres:postgres@postgres:5432/migration_test alembic upgrade head"
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
If `alembic upgrade head` fails on the fresh DB, there is a broken or non-idempotent migration. Fix it before deploying.

### 8. Summary
Report a table:

| Step | Result | Coverage |
|---|---|---|
| Backend lint | PASS/FAIL | — |
| Backend tests | X passed | XX% (min 60%) |
| Frontend types | PASS/FAIL | — |
| Frontend lint | PASS/FAIL (N warnings) | — |
| Frontend tests | X passed | XX% (min 20%) |
| E2E Smoke | X passed | — |
| Migrations (fresh DB) | PASS/FAIL | — |

If all pass: "CI suite PASS — safe to deploy."
If any fail: list failures with file:line references.
