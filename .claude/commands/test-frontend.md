Run frontend type checks, linting, unit tests with coverage, and E2E smoke natively in WSL.

**IMPORTANT:** Frontend tools are in `frontend/node_modules/.bin/` (vitest, tsc, next, eslint).
If tools are missing, run `cd frontend && npm ci`.

## Steps

Run these sequentially, reporting results after each step:

### 1. Type check (TypeScript)
```bash
cd frontend && npx tsc --noEmit
```

### 2. Lint (ESLint via Next.js)
```bash
cd frontend && npx next lint
```

### 3. Unit tests with coverage (Vitest)
```bash
cd frontend && npx vitest run --coverage
```
This runs `vitest run` with v8 coverage. Thresholds: **statements 20%, branches 15%, functions 15%, lines 20%**.

To run a specific test file:
```bash
cd frontend && npx vitest run src/features/{domain}/
```

### 4. Security audit (npm audit)
```bash
cd frontend && npm audit --audit-level=high
```
Checks NPM dependencies for known vulnerabilities (HIGH and CRITICAL severity).

### 5. E2E Smoke Tests (Playwright)
```bash
make e2e-smoke
```
Runs `@smoke`-tagged Playwright specs against the running dev environment.
If containers are not running, this step will FAIL — run `make dev` first.

### 6. Report
Summarize:
- Types: pass/fail
- Lint: errors/warnings count
- Tests: pass/fail count
- Coverage: overall % and whether it meets thresholds (statements 20%, lines 20%)
- Security: pass/fail (N vulnerabilities)
- E2E Smoke: pass/fail count
