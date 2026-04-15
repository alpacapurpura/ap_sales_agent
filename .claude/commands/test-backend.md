Run backend quality gates + functional tests + health checks natively in WSL.
This is the DEFINITIVE backend verification command. All steps must pass before committing.

**CRITICAL:** All tools run from `backend/.venv/bin/`. NEVER use `docker exec` for lint/tests.

## Execution: run ALL steps sequentially. Stop on first BLOCKER failure.

### Step 1: Verify tools
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff --version && .venv/bin/pytest --version && .venv/bin/interrogate --version
```
If missing: `.venv/bin/pip install -r requirements-dev.txt`

---

## QUALITY GATES (blockers — 0 errors required)

### Step 2: Lint (ruff check)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ tests/ --no-cache
```
Must be `All checks passed!`. If not: fix violations. Use `--fix` only if user approves.

### Step 3: Format check (ruff format)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/ruff format --check src/ tests/
```
Must show 0 files to reformat. If fails: `.venv/bin/ruff format src/ tests/`

### Step 4: Architecture fitness tests (10 gates)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
```
Enforces: DDD boundaries, API contracts (response_model), no hard deletes, SA 2.0 syntax,
currency from source, ETL contract sync, master data rules, Meta invariants,
**snake_case file naming, DDD folder structure, domain purity (no SQLAlchemy in domain)**.
ALL must pass. Failure = structural regression — fix before proceeding.

---

## FUNCTIONAL TESTS (blockers)

### Step 5: Unit + integration tests with coverage
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short
```
Coverage threshold: **43%** (enforced by pyproject.toml `fail_under`).
Tests run with pytest-randomly (catches hidden order dependencies) and pytest-timeout (30s kill).

---

## HEALTH CHECKS (informational — report but don't block)

### Step 6: Code duplication (jscpd)
```bash
cd /home/chris/AISALESHT && npx jscpd backend/src/ --threshold 5 --reporters console
```
Baseline: 3.63% (205 clones). If >5%: **flag as WARNING** — new duplication introduced.
If >8%: **flag as CRITICAL** — significant copy-paste detected, must refactor.

### Step 7: Docstring coverage (interrogate)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/interrogate -vv src/modules/ src/shared/ --fail-under=0
```
Report coverage %. Trend should go UP over time. If a module drops significantly: flag it.

### Step 8: Security audit (pip-audit)
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/pip-audit --strict --desc
```
Checks Python dependencies for known CVEs. Report any findings with severity.

---

## REPORT

Summarize as table:

| Gate | Step | Result | Details |
|------|------|--------|---------|
| QUALITY | Lint (ruff) | PASS/FAIL | 0 errors required |
| QUALITY | Format (ruff) | PASS/FAIL | 0 files to reformat |
| QUALITY | Arch fitness (10 tests) | PASS/FAIL | DDD + naming + purity |
| FUNCTIONAL | Tests (N passed) | PASS/FAIL | coverage: XX% (min 43%) |
| HEALTH | Duplication (jscpd) | X.XX% | baseline 3.63%, warn >5% |
| HEALTH | Docstrings (interrogate) | XX% | trend should increase |
| HEALTH | Security (pip-audit) | PASS/FAIL | N vulnerabilities |

**If all QUALITY + FUNCTIONAL pass:** "Backend OK — safe to commit."
**If any QUALITY or FUNCTIONAL fail:** list failures with file:line. Fix before committing.
**If HEALTH checks degrade:** warn user, suggest fixes, but don't block.
