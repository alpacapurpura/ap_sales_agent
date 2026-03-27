Run frontend type checks, linting, and unit tests inside Docker.

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

### 3. Unit tests (Vitest)
```bash
docker exec -t visionarias_client_dev npm run test
```
This runs `vitest run` (single pass, no watch mode).

To run a specific test file:
```bash
docker exec -t visionarias_client_dev npx vitest run src/features/{domain}/
```

### 4. Report
Summarize: types pass/fail, lint errors/warnings count, test pass/fail count.
