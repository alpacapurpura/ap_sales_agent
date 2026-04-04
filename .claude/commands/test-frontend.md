Run frontend type checks, linting, unit tests with coverage, and E2E smoke inside Docker.

**IMPORTANT:** The frontend container (`visionarias_client_dev`) uses `target: dev` and has all deps.
Tools available: `npx tsc`, `npx next lint`, `npm run test` (vitest).

## Steps

Run these sequentially, reporting results after each step:

### 1. Type check (TypeScript)
```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
```

### 2. Lint (ESLint via Next.js)
```bash
docker exec -t visionarias_client_dev npx next lint
```

### 3. Unit tests with coverage (Vitest)
```bash
docker exec -t visionarias_client_dev npx vitest run --coverage
```
This runs `vitest run` with v8 coverage. Thresholds: **statements 20%, branches 15%, functions 15%, lines 20%**.

To run a specific test file:
```bash
docker exec -t visionarias_client_dev npx vitest run src/features/{domain}/
```

### 4. E2E Smoke Tests (Playwright)
```bash
make e2e-smoke
```
Runs `@smoke`-tagged Playwright specs against the running dev environment.
If containers are not running, this step will FAIL — run `make dev` first.

### 5. Report
Summarize:
- Types: pass/fail
- Lint: errors/warnings count
- Tests: pass/fail count
- Coverage: overall % and whether it meets thresholds (statements 20%, lines 20%)
- E2E Smoke: pass/fail count
