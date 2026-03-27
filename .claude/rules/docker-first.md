---
globs: "**/*"
description: All execution must happen inside Docker containers
---

# Docker-First

**CRITICAL: Never run pytest, ruff, alembic, npm, npx, or python directly on the host.**

## Container Setup

| Container | Image Target | Has Dev Tools |
|---|---|---|
| `visionarias_brain_dev` | `dev` | pytest, ruff, alembic |
| `visionarias_client_dev` | `dev` | vitest, tsc, next lint |

**If pytest/ruff are missing:** The backend was built with `target: final` instead of `target: dev`.
Fix: `docker-compose.yml` → api_dev → `target: dev`, then `docker compose up -d --build api_dev`.

## Command Reference

| Action | Command |
|---|---|
| Start dev | `docker compose up -d` |
| Backend shell | `docker exec -it visionarias_brain_dev bash` |
| Frontend shell | `docker exec -it visionarias_client_dev bash` |
| Backend lint | `docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"` |
| Backend tests | `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"` |
| Frontend types | `docker exec -t visionarias_client_dev npx tsc --noEmit` |
| Frontend lint | `docker exec -t visionarias_client_dev npx next lint` |
| Frontend tests | `docker exec -t visionarias_client_dev npm run test` |
| Migrations | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` |

## Notes
- Use `--no-cache` with ruff to avoid `.ruff_cache/` permission errors
- Use `bash -c "cd /app && ..."` for backend commands (ensures correct working directory)
- Frontend commands work with direct `npx`/`npm` (node_modules is a Docker volume)
- Vitest config: `frontend/vitest.config.mts` (happy-dom environment)
- Pytest config: `backend/pyproject.toml` [tool.pytest] (asyncio_mode=auto)
