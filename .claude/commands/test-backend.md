Run backend lint and tests inside Docker.

**IMPORTANT:** All tools (pytest, ruff) are in the container's `/opt/venv/bin/` (on PATH).
If `ruff` or `pytest` is not found, the container was built with `target: final` instead of `target: dev`.
Fix: change `docker-compose.yml` api_dev build target to `dev`, then `docker compose up -d --build api_dev`.

## Steps

Run these sequentially, reporting results after each step:

### 1. Verify tools exist
```bash
docker exec -t visionarias_brain_dev bash -c "which pytest && which ruff"
```
If either is missing, STOP and tell the user to rebuild with `target: dev`.

### 2. Lint (ruff)
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"
```
Use `--no-cache` to avoid permission issues with `.ruff_cache/`.
If the user wants auto-fix: add `--fix` flag.

### 3. Unit tests (pytest)
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```
- `-x`: stop on first failure
- `-q`: quiet output
- `--tb=short`: compact tracebacks

To run a specific module's tests:
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/{module}/ -v"
```

### 4. Report
Summarize: lint pass/fail, tests pass/fail count, any errors.
