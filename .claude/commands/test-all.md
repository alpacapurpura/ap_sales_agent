Run FULL quality suite (backend + frontend + migrations) natively.
This is the DEFINITIVE pre-commit/pre-deploy verification. Mirrors CI quality-gates.

**CRITICAL:** All tools run natively in WSL. NEVER `docker exec` for lint/tests.
Docker ONLY for: migrations test (Step 11).

**E2E:** NOT part of `/test-all`. Run separately with `/test-frontend` or the
native Playwright command when needed — E2E is too slow + flaky to gate every
pre-commit / pre-deploy run and blocks the quick iteration loop.

## Execution: run ALL steps sequentially. Stop on first BLOCKER failure.

### Step 0: Pre-flight
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff --version && .venv/bin/pytest --version && cd /home/chris/AISALESHT/frontend && npx vitest --version
```
If anything fails: install dependencies first.

---

## BACKEND QUALITY GATES (blockers)

### Step 1: Backend lint (ruff check)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ tests/ --no-cache
```

### Step 2: Backend format (ruff format)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check src/ tests/
```

### Step 3: Architecture fitness tests (10 gates)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
```
DDD boundaries + API contracts + conventions + currency + ETL contract + master data +
Meta invariants + **snake_case naming + DDD folder structure + domain purity**.

### Step 4: Backend tests with coverage
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short
```
Threshold: **43%**. pytest-randomly active (randomized order). pytest-timeout: 30s.

---

## FRONTEND QUALITY GATES (blockers)

### Step 5: TypeScript strict
```bash
cd /home/chris/AISALESHT/frontend && npx tsc --noEmit
```

### Step 6: ESLint (60+ rules)
```bash
cd /home/chris/AISALESHT/frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache
```
0 errors required. Count warnings for report.

### Step 7: Frontend tests with coverage
```bash
cd /home/chris/AISALESHT/frontend && npx vitest run --coverage
```
Thresholds: **all 20%** (statements, branches, functions, lines).

---

## HEALTH CHECKS (informational — report, don't block)

### Step 8: Code duplication — BOTH stacks
```bash
cd /home/chris/AISALESHT && npx jscpd frontend/src/ --threshold 5 --reporters console
cd /home/chris/AISALESHT && npx jscpd backend/src/ --threshold 5 --reporters console
```
Baselines: Frontend 4.52%, Backend 3.63%. Warn >5%, critical >8%.

### Step 9: Dead code + circular imports (frontend)
```bash
cd /home/chris/AISALESHT/frontend && npx knip 2>&1 | head -40
cd /home/chris/AISALESHT/frontend && npx madge --circular src/ --extensions ts,tsx
```
knip baseline: 63 unused (many false positives). madge baseline: 2 cycles.

### Step 10: Docstring coverage + security
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/interrogate -vv src/modules/ src/shared/ --fail-under=0
cd /home/chris/AISALESHT/backend && .venv/bin/pip-audit --strict --desc
cd /home/chris/AISALESHT/frontend && npm audit --audit-level=high
```

---

## MIGRATIONS (optional — run when deploying)

### Step 11: Migration verification (fresh DB)
```bash
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_test;"
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec -t visionarias_brain_dev bash -c "cd /app && DATABASE_URL=postgresql://postgres:postgres@postgres:5432/migration_test alembic upgrade head"
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
If fails: broken or non-idempotent migration.

---

## FINAL REPORT

| Gate | Step | Result | Details |
|------|------|--------|---------|
| **BACKEND** | | | |
| QUALITY | Lint (ruff) | PASS/FAIL | 0 errors |
| QUALITY | Format (ruff) | PASS/FAIL | 0 reformats |
| QUALITY | Arch fitness (10) | PASS/FAIL | DDD + naming + purity |
| FUNCTIONAL | Tests | PASS/FAIL (N) | coverage XX% (min 43%) |
| HEALTH | Duplication | X.XX% | baseline 3.63% |
| HEALTH | Docstrings | XX% | trend tracking |
| HEALTH | Security (pip-audit) | PASS/FAIL | N vulns |
| **FRONTEND** | | | |
| QUALITY | TypeScript (tsc) | PASS/FAIL | strict mode |
| QUALITY | ESLint (60+) | PASS/FAIL | 0 errors, N warnings |
| FUNCTIONAL | Tests | PASS/FAIL (N) | coverage XX% (min 20%) |
| HEALTH | Duplication | X.XX% | baseline 4.52% |
| HEALTH | Dead code (knip) | N unused | focus on NEW |
| HEALTH | Circulars (madge) | N cycles | baseline 2 |
| HEALTH | Security (npm) | PASS/FAIL | N vulns |
| **DEPLOY** | | | |
| MIGRATIONS | Fresh DB | PASS/FAIL/SKIP | if Docker available |

**All QUALITY + FUNCTIONAL pass:** "Full suite PASS — safe to deploy."
**Any fail:** list failures. Fix before deploying.
**HEALTH degraded:** warn user, track trend, suggest fixes.
