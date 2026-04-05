# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Nicolify** — Multitenant SaaS (AaaS) automating marketing/sales for creators.
**Stack:** FastAPI (Async/SQLAlchemy 2.0), Next.js 16 (App Router/FSD), Clerk (Auth), Qdrant (RAG).
**Pattern:** Modular Monolith (DDD) + Docker-First.

## Core Domains

| Studio | Purpose | Modules |
| :--- | :--- | :--- |
| **Brand/Offer** | Identity capture & Offer Ladder builder | `brand`, `offer` |
| **Assets** | Auto-gen Landing Pages/Copies | `landing`, `assets` |
| **Growth** | Funnel diagram & Analytics | `analytics`, `advertising`, `social_media` |
| **Sales** | AI SDR (chat/close/schedule) & Ops Hub | `sales_agent`, `scheduling` |
| **Config** | External integrations (Meta, Shopify, etc.) | `connections` |
| **Supporting** | Auth, contacts, shared infra | `iam`, `crm`, `core`, `shared` |

Unsure about a domain? Read `docs/domains/INDEX.md` first (15 domain docs).

## Commands

**Lint, tests, and type-checking run NATIVELY in WSL — never inside Docker.**
**Docker is only for runtime services (FastAPI, DB, Redis, Qdrant) and migrations (Alembic).**

| Action | Skill / Make | Native command |
|---|---|---|
| Start dev | `/dev-up` or `make dev` | `docker compose up -d` |
| Start extended (admin, worker) | `make dev-extended` | `docker compose --profile extended up -d` |
| Backend lint | `/test-backend` or `make ruff` | `cd backend && .venv/bin/ruff check src/ --no-cache` |
| Backend tests | `/test-backend` or `make pytest` | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Arch tests | `make arch-test` | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Single backend test | `make pytest args="-k test_name"` | `cd backend && .venv/bin/pytest tests/modules/brand/ -x -q` |
| Frontend types | `/test-frontend` or `make tsc` | `cd frontend && npx tsc --noEmit` |
| Frontend lint | `/test-frontend` | `cd frontend && npx next lint` |
| Frontend tests | `/test-frontend` or `make vitest` | `cd frontend && npx vitest run` |
| Full CI | `/test-all` | Backend lint+tests, then frontend types+lint+tests |
| Run migration | `/migrate <msg>` | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` |
| Explore module | `/explore-module <name>` | — |
| Review PR | `/review-pr` | — |
| Install npm pkg | `make install-front p=pkg` | — |
| Fix Docker perms | `make fix-permissions` | — |
| E2E smoke | `make e2e-smoke` | `docker compose --profile e2e run --rm e2e_runner npx playwright test --grep @smoke` |
| E2E full | `make e2e` | `docker compose --profile e2e run --rm e2e_runner npx playwright test` |

### Docker Containers

| Container | Service | Port |
|---|---|---|
| `visionarias_brain_dev` | FastAPI (uvicorn --reload) | 8000 |
| `visionarias_client_dev` | Next.js dev server | 3000 |
| `visionarias_admin_dev` | Streamlit admin (extended profile) | 8502 |
| `visionarias_postgres` | PostgreSQL 15 | 5432 |

## Architecture

### Backend (`backend/src/`)

16 bounded contexts in `modules/`, each following DDD Inside-Out:

```
modules/{name}/
  domain/         # Models, value objects, repo interfaces. No framework imports.
  infrastructure/ # SQLAlchemy repos, external API clients.
  application/    # Services, use cases, orchestration.
  api/            # FastAPI routes + Pydantic DTOs. Thin — delegates to application.
```

Entry point: `main.py` imports each module's router and mounts at `/api/v1/{module}/`.
Shared infrastructure: `shared/` (base entities, event bus, model registry) and `core/` (config, database, security).

### Frontend (`frontend/src/`)

Feature-Sliced Design Lite (domain-grouped, not traditional FSD layers):

```
app/              # Next.js App Router pages (thin — delegate to features)
  (main)/         # Authenticated dashboard routes
  (landing)/      # Public landing pages
components/
  ui/             # Shadcn UI primitives (auto-generated, don't edit)
  shared/         # Cross-feature layout (sidebar, header)
features/
  {domain}/       # Feature slices: components/, hooks/, api/, types/, utils/
lib/              # API client, design system registry, utilities
```

Key: `fetchClient` (in `lib/`) auto-injects `X-Tenant-ID` from Clerk session — always use it.

### Testing

- **Backend:** pytest (asyncio_mode=auto). Tests in `backend/tests/modules/{module}/`. Fixtures in per-module `conftest.py`.
- **Frontend:** Vitest (happy-dom). Tests as `*.test.ts` colocated with features or in `__tests__/` dirs.

### CI/CD (`.github/workflows/deploy-prod.yml`)

Push to `main` triggers: quality-gates (lint+test) → security-scan (Trivy) → push images to GHCR (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`).

## Native Dev Tools (WSL) — MANDATORY

> **Why:** Docker volume mounts (`/app`) always point to the main repo clone. When running
> parallel agents with git worktrees, the container sees stale code from the wrong worktree.
> Native tools read the actual filesystem path, making them reliable for multiagent workflows.

**CRITICAL RULE: NEVER use `docker exec` for lint, tests, or type-checking. Always run natively.**

### Backend (Python)

**virtualenv:** `backend/.venv` (Python 3.12, ruff, pytest, pytest-cov, factory-boy, faker)

| Task | Native command (run from repo root) |
|---|---|
| Lint | `cd backend && .venv/bin/ruff check src/ --no-cache` |
| Format check | `cd backend && .venv/bin/ruff format --check src/` |
| All tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Architecture tests | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Tests with coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| Single module | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |

### Frontend (Node.js)

**node_modules:** `frontend/node_modules` (vitest, tsc, next, eslint)

| Task | Native command (run from repo root) |
|---|---|
| Type check | `cd frontend && npx tsc --noEmit` |
| Lint | `cd frontend && npx next lint` |
| All tests | `cd frontend && npx vitest run` |
| Tests with coverage | `cd frontend && npx vitest run --coverage` |
| Single feature | `cd frontend && npx vitest run src/features/{domain}/` |

### Docker ONLY for:
- Runtime services: `docker compose up -d`
- Migrations: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`
- Logs: `docker logs visionarias_brain_dev --tail 100`
- E2E tests: `make e2e-smoke` (needs running services)
- Migration verification on fresh DB

### PROHIBITED (never do this):
```
docker exec -t visionarias_brain_dev bash -c "ruff ..."
docker exec -t visionarias_brain_dev bash -c "pytest ..."
docker exec -t visionarias_client_dev npx tsc ...
docker exec -t visionarias_client_dev npx vitest ...
docker exec -t visionarias_client_dev npx next lint ...
docker run --rm ... ruff|pytest|tsc|vitest ...
```

## Critical Rules

1. **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2. **Native-First Testing:** Lint, tests, type-checks run natively in WSL — never inside Docker. See `.claude/rules/docker-first.md`.
3. **Tenant Isolation:** ALL queries filter by `X-Tenant-ID`. See `.claude/rules/tenant-isolation.md`.
4. **Backend DDD:** Inside-Out layers, no cross-module imports (except copilot). See `.claude/rules/backend-ddd.md`.
5. **Frontend FSD:** Server Components by default, no deep feature imports (except copilot). See `.claude/rules/frontend-fsd.md`.
6. **Migrations:** Must be idempotent (raw SQL with `IF NOT EXISTS`). See `.claude/rules/backend-migrations.md`.
7. **PII:** Every endpoint MUST declare `response_model=`. PII fields must be masked or justified (loaded via `@AGENTS.md` → Tessl rules).
8. **Git:** Conventional Commits, never force push main. See `.claude/rules/git-safety.md`.
9. **Debugging:** Docker diagnostics + common error patterns. See `.claude/rules/debugging.md`.
10. **Copilot:** Schema introspection, module registry, route-based tools. See `.claude/rules/copilot-resilience.md`.

## Product Vision

For product decisions: `docs/domains/vision/product-vision.md`.

@AGENTS.md
