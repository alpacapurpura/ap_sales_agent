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

**All commands run inside Docker. Never run pytest, ruff, alembic, npm, or python on the host.**

| Action | Skill / Make | Raw Docker |
|---|---|---|
| Start dev | `/dev-up` or `make dev` | `docker compose up -d` |
| Start extended (admin, worker) | `make dev-extended` | `docker compose --profile extended up -d` |
| Backend lint | `/test-backend` or `make ruff` | `docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"` |
| Backend tests | `/test-backend` or `make pytest` | `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"` |
| Single backend test | `make pytest args="-k test_name"` | `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/brand/ -x -q"` |
| Frontend types | `/test-frontend` | `docker exec -t visionarias_client_dev npx tsc --noEmit` |
| Frontend lint | `/test-frontend` | `docker exec -t visionarias_client_dev npx next lint` |
| Frontend tests | `/test-frontend` or `make vitest` | `docker exec -t visionarias_client_dev npm run test` |
| Full CI | `/test-all` | Backend lint+tests, then frontend types+lint+tests |
| Run migration | `/migrate <msg>` | `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` |
| Explore module | `/explore-module <name>` | — |
| Review PR | `/review-pr` | — |
| Install npm pkg | `make install-front p=pkg` | — |
| Fix Docker perms | `make fix-permissions` | — |

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

## Critical Rules

1. **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2. **Docker-First:** All commands run inside Docker. See `.claude/rules/docker-first.md`.
3. **Tenant Isolation:** ALL queries filter by `X-Tenant-ID`. See `.claude/rules/tenant-isolation.md`.
4. **DDD Boundaries:** No cross-module imports. Use `shared/links/` for inter-module communication.
5. **Data:** Soft deletes only (`deleted_at`). SQLAlchemy 2.0 syntax (`select().where()`, never `session.query()`).
6. **Migrations:** Must be idempotent (raw SQL with `IF NOT EXISTS`). See `.claude/rules/backend-migrations.md`.
7. **PII:** Every endpoint MUST declare `response_model=`. See `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md`.
8. **Frontend:** Server Components by default. React Query for data. No `any` type. No deep feature imports.
9. **Logging:** `structlog` only — never `print()` or `logging`.

## Product Vision

For product decisions: `docs/vision/product-vision.md`.

@AGENTS.md
