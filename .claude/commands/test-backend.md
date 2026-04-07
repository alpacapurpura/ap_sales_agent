Run backend lint and tests with coverage natively in WSL.

**IMPORTANT:** All tools (pytest, ruff) are in `backend/.venv/bin/`.
If `ruff` or `pytest` is not found, run: `cd backend && .venv/bin/pip install -r requirements-dev.txt`

## Steps

Run these sequentially, reporting results after each step:

### 1. Verify tools exist
```bash
cd backend && .venv/bin/ruff --version && .venv/bin/pytest --version
```
If either is missing, STOP and tell the user to install dev dependencies.

### 2. Lint (ruff check)
```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
```
Use `--no-cache` to avoid permission issues with `.ruff_cache/`.
**IMPORTANT:** Always lint `tests/` too — the pre-commit hook checks all staged files including tests.
If the user wants auto-fix: add `--fix` flag.

### 3. Format check (ruff format)
```bash
cd backend && .venv/bin/ruff format --check src/ tests/
```
Verifies code formatting without modifying files. If this fails, run `ruff format src/ tests/` to fix.

### 5. Architectural fitness tests
```bash
cd backend && .venv/bin/pytest tests/architecture/ -v
```
These validate DDD boundaries (no cross-module imports), API contracts (response_model present),
and coding conventions (no hard deletes, SA 2.0 syntax). Failures here mean a structural
regression — fix before proceeding.

### 6. Unit tests with coverage (pytest)
```bash
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short
```
- `-x`: stop on first failure
- `-q`: quiet output
- `--tb=short`: compact tracebacks
- `--cov-report=term-missing`: shows which lines are uncovered

To run a specific module's tests:
```bash
cd backend && .venv/bin/pytest tests/modules/{module}/ -v
```

### 7. Security audit (pip-audit)
```bash
cd backend && .venv/bin/pip-audit --strict --desc
```
Checks all Python dependencies for known vulnerabilities. `--strict` fails on ANY finding.
This mirrors CI exactly. If it finds issues, report them — do NOT skip.

### 8. Report
Summarize:

| Step | Result | Coverage |
|---|---|---|
| Lint (ruff check) | pass/fail | — |
| Format (ruff format) | pass/fail | — |
| Arch fitness | pass/fail (5 tests) | — |
| Tests | pass/fail count | XX% (min 60%) |
| Security (pip-audit) | pass/fail (N vulns) | — |

- If coverage is below 60%, list the modules with lowest coverage
- If pip-audit finds vulnerabilities, list them with severity
