Run backend quality gates + functional tests + health checks natively in WSL.
This is the DEFINITIVE backend verification command. ALL 12 steps must pass before committing.

**CRITICAL:** All tools run from `backend/.venv/bin/`. NEVER use `docker exec` for lint/tests/type-check.

## Execution: run ALL steps sequentially. Every step blocks. Report after each.

### Step 1: Verify tools
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff --version && .venv/bin/pytest --version && .venv/bin/mypy --version && .venv/bin/interrogate --version
```
If missing: `.venv/bin/pip install -r requirements-dev.txt`

### Step 2: Postgres pre-flight (gates steps 7-9)
```bash
docker ps --format '{{.Names}}' | grep -qx visionarias_postgres && echo "POSTGRES_UP=1" || echo "POSTGRES_UP=0"
docker ps --format '{{.Names}}' | grep -qx visionarias_brain_dev && echo "BRAIN_UP=1" || echo "BRAIN_UP=0"
```
Both up → run steps 7/8/9. Either down → SKIP 7/8/9 with WARNING (not a fail). Suggest user run `/dev-up` for full coverage.

---

## QUALITY GATES (blockers — 0 errors required)

### Step 3: Lint (ruff check, 40+ rule families)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ tests/ --no-cache
```
Must be `All checks passed!`. Includes McCabe `max-complexity = 12`. If fails: fix violations. Use `--fix` only if user approves.

### Step 4: Format check (ruff format)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check src/ tests/
```
Must show 0 files to reformat. If fails: `.venv/bin/ruff format src/ tests/`.

### Step 5: Static type check (mypy strict on domain layer)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/mypy \
    -p src.shared.domain \
    -p src.modules.iam.domain \
    -p src.modules.sales_agent.domain \
    -p src.modules.brand.domain \
    -p src.modules.copilot.domain \
    -p src.modules.offer.domain \
    -p src.modules.analytics.domain \
    -p src.modules.crm.domain
```
Strict mode globally; per-file overrides in `pyproject.toml [tool.mypy]` allowlist (ratchet — shrinks only).
Must report `Success: no issues found`. New domain errors = fix or add to overrides with justification.

### Step 6: Architecture fitness tests (78 gates)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
```
Enforces: DDD boundaries, API contracts (`response_model=`), no hard deletes, SA 2.0 syntax, currency from source,
ETL contract sync, master data (UTC + ISO 4217), Meta invariants, snake_case naming, DDD folder structure,
domain purity (no SQLAlchemy in domain), `redirect_slashes=False`, PII sanitization, brand-voice SSoT,
admin panel registry parity, copilot subagent isolation, sales-agent prompts. ALL must pass.

---

## FUNCTIONAL TESTS (blockers)

### Step 7: Unit + coverage (modules + shared, 43% min)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q --tb=short
```
Threshold: **43%** (`fail_under` in `pyproject.toml`). NO `-x` — full universe of failures reported.
Random order (pytest-randomly) + 30s timeout (pytest-timeout). All tests pass + coverage ≥ 43%.

### Step 8: Verify-marker tests — data reliability Layers 1/2 (IF Postgres up)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest -m verify --override-ini="addopts=" -v
```
Skip with WARNING if Postgres down (Step 2 = `POSTGRES_UP=0`).
Validates: provider source vs official_metrics (Layer 1), official_metrics vs DTOs (Layer 2).
See `.claude/rules/data-reliability.md`. Failure = data pipeline regression — investigate.

### Step 9: Integration-marker tests (IF Postgres up)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest -m integration --override-ini="addopts=" -v
```
Skip with WARNING if Postgres down. Live integration tests (real DB, OAuth flows, providers).

### Step 10: Migration idempotency on schema clone (IF Postgres up)
```bash
cd /home/chris/AISALESHT/backend && bash scripts/verify_migration_idempotency.sh
```
Wraps the 5-step protocol from `.claude/rules/backend-migrations.md`:
create `migration_test` DB → dump schema → stamp head → re-run `alembic upgrade head` (must be no-op).
Skip with WARNING if Postgres or brain container down. Failure = non-idempotent migration — fix before push to main.

---

## HEALTH GATES (blockers in strict mode)

### Step 11: Code duplication (jscpd, threshold 5%)
```bash
cd /home/chris/AISALESHT && npx jscpd backend/src/ --threshold 5 --reporters console
```
Baseline: 2.94% (322 clones). Threshold 5% blocks regression with margin. Failure → refactor duplicates before commit.

### Step 12: Docstring coverage (interrogate, fail-under 85)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/interrogate -vv src/modules/ src/shared/
```
Threshold: **85%** (declared in `[tool.interrogate]`). Current actual ~92.6%.
Failure = new public API without docstrings. Add Google-style docstring or refactor.

### Step 13: Security audit (CVE allowlist wrapper)
```bash
cd /home/chris/AISALESHT/backend && bash scripts/audit_security.sh
```
Runs `pip-audit --strict` with explicit allowlist of 14 documented CVEs (no fix available or accepted risk).
ANY new CVE outside allowlist = exit 1 = blocker. Fix: upgrade package OR add ID to allowlist with justification.

---

## REPORT

Summarize as table:

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS/FAIL | ruff/pytest/mypy/interrogate versions |
| 2 | Postgres pre-flight | UP/DOWN | gates steps 8/9/10 |
| 3 | Lint (ruff) | PASS/FAIL | 0 errors required, McCabe 12 |
| 4 | Format (ruff) | PASS/FAIL | 0 files to reformat |
| 5 | Type check (mypy) | PASS/FAIL | strict on domain (8 modules) |
| 6 | Arch fitness (78) | PASS/FAIL | DDD + invariants |
| 7 | Tests + coverage | PASS/FAIL | XX% (min 43%) |
| 8 | Verify marker | PASS/FAIL/SKIP | data-reliability Layers 1/2 |
| 9 | Integration | PASS/FAIL/SKIP | live DB tests |
| 10 | Migration idempotency | PASS/FAIL/SKIP | schema-clone re-upgrade is no-op |
| 11 | Duplication (jscpd) | PASS/FAIL | <5% required |
| 12 | Docstrings (interrogate) | XX% | ≥85% required |
| 13 | Security (CVEs) | PASS/FAIL | new CVEs outside allowlist |

**If all 13 gates PASS (skipped 8/9/10 acceptable if Postgres down):** "Backend OK — safe to commit."
**If any gate FAILS:** list failure with file:line. NO commit until fixed.
**Reminder:** `/test-backend` is necessary, not sufficient. Before push to `main`: also run `make ci-parity` (Docker, see CLAUDE.md rule 2).
