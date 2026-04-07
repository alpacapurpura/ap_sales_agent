---
globs: "**/*"
description: Native-first dev tools + Docker for runtime services only
---

# Docker-First (Runtime) + Native-First (Dev Tools)

**CRITICAL: Lint, tests, and type-checking run NATIVELY in WSL — never inside Docker.**
**Docker is for runtime services (FastAPI, DB, Redis, Qdrant) and migrations only.**

## Why Native?

Docker volume mounts (`/app`) point to the main repo clone. When agents work in git worktrees
(`isolation: "worktree"`), `docker exec` runs against stale code from the wrong directory.
Native tools read the actual filesystem, making them correct in all contexts.

## Native Dev Tools

### Backend (Python)

| Action | Command |
|---|---|
| Backend lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Backend format check | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| All backend tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Architecture tests | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Tests with coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| Single module | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |
| Security audit | `cd backend && .venv/bin/pip-audit --strict --desc` |

### Frontend (Node.js)

| Action | Command |
|---|---|
| Frontend types | `cd frontend && npx tsc --noEmit` |
| Frontend lint | `cd frontend && npx eslint src/` |
| Frontend tests | `cd frontend && npx vitest run` |
| Tests with coverage | `cd frontend && npx vitest run --coverage` |
| Single feature | `cd frontend && npx vitest run src/features/{domain}/` |
| Security audit | `cd frontend && npm audit --audit-level=high` |

## Docker (Runtime Only)

| Action | Command |
|---|---|
| Start dev | `docker compose up -d` |
| Backend shell | `docker exec -it visionarias_brain_dev bash` |
| Frontend shell | `docker exec -it visionarias_client_dev bash` |
| Migrations | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` |

## PROHIBITED — Never Do This

```
docker exec ... ruff|pytest|tsc|vitest|eslint|npm run test ...
```

## Makefile Shortcuts

| Target | What it does |
|---|---|
| `make dev` | Start core services |
| `make pytest args="..."` | Backend tests native |
| `make vitest args="..."` | Frontend tests native |
| `make lint` | Run ruff + eslint natively |
| `make ruff` | Backend lint only (native) |
| `make tsc` | Frontend type check (native) |
| `make arch-test` | Architecture fitness tests (native) |
| `make install-front p=pkg` | Install npm package in Docker |

## Notes
- Use `--no-cache` with ruff to avoid `.ruff_cache/` permission errors
- Vitest config: `frontend/vitest.config.mts` (happy-dom environment)
- Pytest config: `backend/pyproject.toml` [tool.pytest] (asyncio_mode=auto)
- Tests using SQLite in-memory (`db` fixture) work natively without PostgreSQL
