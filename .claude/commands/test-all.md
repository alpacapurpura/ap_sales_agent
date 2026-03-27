Run full CI suite (backend + frontend) inside Docker. Mirrors the `quality-gates` job in `.github/workflows/deploy-prod.yml`.

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

### 2. Backend tests (pytest)
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```

### 3. Frontend types (tsc)
```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
```

### 4. Frontend lint (ESLint)
```bash
docker exec -t visionarias_client_dev npx next lint
```

### 5. Frontend tests (vitest)
```bash
docker exec -t visionarias_client_dev npm run test
```

### 6. Summary
Report a table:

| Step | Result |
|---|---|
| Backend lint | PASS/FAIL |
| Backend tests | X passed, Y failed |
| Frontend types | PASS/FAIL |
| Frontend lint | PASS/FAIL (N warnings) |
| Frontend tests | X passed, Y failed |

If all pass: "CI suite PASS — safe to commit."
If any fail: list failures with file:line references.
