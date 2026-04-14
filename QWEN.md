# Nicolify (Visionarias Brain) — QWEN Context

## Project Overview

**Nicolify** is a multitenant SaaS platform (Agent-as-a-Service) that automates marketing and sales for content creators. AI agents replace an entire sales team — from brand capture through lead qualification to payment collection.

**Stack:**
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, LangGraph, Qdrant (RAG), Redis, structlog, arq (async workers)
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui, Clerk (auth), TanStack React Query, Sentry, Zod, Zustand, Framer Motion, VisX, Recharts
- **Infrastructure:** Docker Compose, PostgreSQL 15, Redis 7, Qdrant v1.7.3, Traefik (reverse proxy), Cloudflare Tunnel
- **CI/CD:** GitHub Actions (lint → test → Trivy scan → GHCR → SSH deploy)

**Architecture Pattern:** Modular Monolith with DDD (Inside-Out) + Feature-Sliced Design (frontend)

---

## Quick Start

### Prerequisites
- Python 3.11+ with virtualenv support
- Node.js 18+ with npm
- Docker & Docker Compose
- WSL2 (for native testing)

### First-Time Setup
```bash
make setup          # Create data directories with correct permissions
```

### Start Development Environment
```bash
make dev            # Start core services (API, frontend, Postgres, Redis, Qdrant)
make dev-extended   # Start all services (includes admin, scheduler, worker)
```

Access points:
- **Backend API:** `http://localhost:8000` (Swagger: `/docs`)
- **Frontend:** `http://localhost:3000`
- **Storybook:** `http://localhost:6006`
- **Admin Dashboard:** `http://localhost:8502` (extended profile only)

### Stop Environment
```bash
make stop           # Stop all containers
make stop-dev       # Stop dev containers only
make stop-prod      # Stop prod containers only
```

---

## Key Commands

### Backend (Python/FastAPI)

> **MANDATORY:** All lint, tests, and type-checking run **NATIVELY in WSL** — never inside Docker. Docker is only for runtime services and migrations.

| Task | Command |
|------|---------|
| Lint | `make ruff` or `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Format check | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| All tests | `make pytest` or `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Architecture tests | `make arch-test` or `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Tests with coverage | `make pytest-cov` or `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| Single module tests | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |
| Security audit | `make audit-backend` or `cd backend && .venv/bin/pip-audit --strict --desc` |
| Run migration | `make migrate` or `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"` |
| Regenerate ETL contract doc | `make extraction-contract` |

### Frontend (Next.js/React)

| Task | Command |
|------|---------|
| Type check | `make tsc` or `cd frontend && npx tsc --noEmit` |
| Lint | `cd frontend && npx eslint src/` |
| Lint + fix | `cd frontend && npx eslint src/ --fix` |
| All tests | `make vitest` or `cd frontend && npx vitest run` |
| Tests with coverage | `make vitest-cov` or `cd frontend && npx vitest run --coverage` |
| Single feature tests | `cd frontend && npx vitest run src/features/{domain}/` |
| Security audit | `make audit-frontend` or `cd frontend && npm audit --audit-level=high` |
| Install package | `make install-front p=pkgname` |

### Full CI Pipeline
```bash
# Full CI: backend lint+tests, then frontend types+lint+tests
# (equivalent to /test-all command)
make ruff && make pytest && make tsc && cd frontend && npx eslint src/ && make vitest
```

### E2E Testing (Playwright)
```bash
make e2e              # Full E2E suite in Docker
make e2e-smoke        # Smoke tests only
make e2e-ui           # Playwright UI mode (port 9323)
make e2e-report       # View test report (port 9324)
make e2e-native-smoke # Native E2E smoke tests (WSL)
```

### Data Reliability Verification (4-Layer Protocol)
```bash
make verify-meta      # Full Meta provider verification (ETL + probe + pipeline + UI)
make verify-etl       # ETL extraction verification
make verify-pipeline  # Pipeline verification tests
make verify-ui        # UI verification tests
```

### Shopify Configuration
```bash
make shopify-config-dev     # Switch to dev configuration
make shopify-config-prod    # Switch to prod configuration
make shopify-config-status  # Show active config details
```

### Docker Management
```bash
make fix-permissions  # Fix file ownership issues (Docker -> Host)
make tooling-up       # Start frontend/backend tooling containers
make tooling-down     # Stop tooling containers
make test-mode        # Stop non-essential containers to free RAM for tests
make dev-mode         # Restore all containers after test-mode
make stats-core       # Show resource usage for core containers
```

---

## Project Structure

```
AISALESHT/
├── backend/                    # FastAPI backend (Python 3.11)
│   ├── src/
│   │   ├── main.py             # Entry point — mounts all module routers
│   │   ├── core/               # Core infrastructure (config, database, security, sentry)
│   │   ├── shared/             # Cross-module infrastructure (Inside-Out)
│   │   │   ├── domain/         # Base entities, value objects
│   │   │   ├── application/    # Shared services
│   │   │   ├── infrastructure/ # Shared repos, LLM factory, event bus
│   │   │   └── links/          # Inter-module communication
│   │   ├── modules/            # 15 bounded contexts (DDD)
│   │   ├── admin/              # Streamlit admin dashboard
│   │   ├── workers/            # Arq worker settings
│   │   ├── scripts/            # Utility scripts
│   │   └── tests/              # Source-level tests
│   ├── alembic/                # Database migrations
│   └── tests/                  # Test suite (architecture, modules, shared, integration)
│
├── frontend/                   # Next.js 16 frontend
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   │   ├── (main)/         # Authenticated dashboard routes
│   │   │   └── (landing)/      # Public landing pages
│   │   ├── features/           # Feature-Sliced Design (domain-grouped)
│   │   ├── components/         # Shared + UI components
│   │   ├── lib/                # Utilities (API client, design system)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── stories/            # Storybook stories
│   │   └── test/               # Test utilities
│   ├── e2e/                    # Playwright E2E tests
│   └── playwright/             # Playwright configuration
│
├── shopify_app/                # Shopify app configuration
├── workers/                    # Cloudflare Workers (Sentry-to-Slack alerts)
├── client_simulator/           # WhatsApp client simulation tool
├── infrastructure/             # Cloud infrastructure configs
├── docs/                       # Documentation (domains, guides, runbooks, specs)
├── scripts/                    # Root-level utility scripts
└── data/                       # Docker volume mounts (postgres, redis, qdrant)
```

---

## Module Registry (Backend DDD)

Each module follows the DDD Inside-Out pattern:
```
modules/{name}/
  domain/         # Models, value objects, repo interfaces. No framework imports.
  infrastructure/ # SQLAlchemy repos, external API clients.
  application/    # Services, use cases, orchestration.
  api/            # FastAPI routes + Pydantic DTOs. Thin — delegates to application.
```

| Module | Purpose |
|--------|---------|
| `iam` | Clerk-based auth, tenant resolution, session management |
| `brand` | Brand identity capture via web scraping, reverse engineering, guided forms |
| `offer` | Offer Ladder builder — products, pricing, archetypes, psychology, blueprints |
| `landing` | Auto-generated landing pages from brand + offer data |
| `sales_agent` | Autonomous AI SDR — pre-qualifies leads, handles objections, schedules, closes |
| `copilot` | In-app AI assistant for configuration, form auto-completion, guided procedures |
| `crm` | CDP — contacts, journey events, sales pipeline tracking, lifecycle scoring |
| `scheduling` | Appointment booking with Google Calendar sync and public booking links |
| `analytics` | ETL pipeline (12+ providers), Bowtie funnel visualization, metric catalog |
| `connections` | External platform integrations (Meta, Shopify, Google, payment, email, messaging) |
| `assets` | AI-generated marketing assets (copies, flyers, images) with R2 storage |
| `tenant_domains` | Custom domain management via Cloudflare Custom Hostnames API |
| `commercial_calendar` | Commercial event calendar — system-wide holidays + tenant-specific promotions |
| `advertising` | Placeholder — ad data lives in analytics ETL |
| `social_media` | Placeholder — social reading in connections channels |

**Infrastructure:** `core/` (config, database, sentry, security) and `shared/` (inter-module links, channel ABCs, LLM factory, event bus, model registry)

---

## Frontend Features (FSD)

Each feature follows this structure:
```
features/{domain}/
  api/         # React Query hooks, API adapters
  components/
  hooks/
  config/
  context/
  types/
  utils/
  index.ts
```

Key features: `brand`, `offer-studio`, `sales`, `copilot`, `connections`, `growth-studio`, `audit`, `admin`, `settings`, `tenant`, `tenant_domains`, `closer-studio`

---

## Critical Development Rules

### 1. Native-First Testing (MANDATORY)
**NEVER use `docker exec` for lint, tests, or type-checking.** Docker volume mounts (`/app`) always point to the main repo clone. When running parallel agents with git worktrees, the container sees stale code from the wrong worktree. Native tools read the actual filesystem path, making them reliable for multi-agent workflows.

**PROHIBITED:**
```bash
docker exec -t visionarias_brain_dev bash -c "ruff ..."
docker exec -t visionarias_brain_dev bash -c "pytest ..."
docker exec -t visionarias_client_dev npx tsc ...
docker exec -t visionarias_client_dev npx vitest ...
docker exec -t visionarias_client_dev npx eslint ...
docker run --rm ... ruff|pytest|tsc|vitest ...
```

**ALLOWED Docker usage:**
- Runtime services: `docker compose up -d`
- Migrations: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`
- Logs: `docker logs visionarias_brain_dev --tail 100`
- Migration verification on fresh DB

### 2. TDD Obligatorio
Tests PRIMERO, implementación DESPUÉS. Sin excepciones.
- Feature nuevo → tests por capa antes de implementar
- Bug fix → test de regresión que reproduce el bug ANTES del fix
- Refactor → tests pasan antes y después
- Feature existente sin tests → escribir tests del comportamiento ACTUAL primero, luego cambiar

### 3. Tenant Isolation
ALL queries MUST filter by `X-Tenant-ID` header (injected from Clerk session). The `fetchClient` in frontend auto-injects this header.

### 4. Backend DDD Inside-Out
- `domain` → `infrastructure` → `application` → `api`
- No cross-module imports (except `copilot`, which is allowed to read from other modules)
- Domain layer must NOT import from any framework (no FastAPI, no SQLAlchemy)

### 5. Frontend FSD
- Server Components by default
- No deep feature imports (except `copilot`)
- Thin `app/` pages that delegate to `features/`

### 6. Migrations
Must be idempotent — raw SQL with `IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, etc.

### 7. PII Sanitisation
Every FastAPI endpoint MUST declare `response_model=` with a Pydantic model. PII fields in response models must be masked or justified with a code comment.

### 8. Git Safety
- Conventional Commits format for all commit messages
- NEVER force push to `main`
- Run lint + tests before committing

### 9. Spanish Text
All user-visible Spanish text MUST have proper accents and ñ (`días` not `dias`, `Campaña` not `Campana`, `Inversión` not `Inversion`).

### 10. ETL Extraction Contract
Before modifying anything in `backend/src/modules/analytics/`:
1. Read `docs/etl/extraction-contract.md` first
2. Update `extraction_contract.py`
3. Regenerate doc: `make extraction-contract`
4. Run tests: `cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q`

### 11. Data Reliability
After modifying any Growth Studio file (provider, service, DTO, frontend component), run the 4-layer verification protocol (`make verify-meta`).

### 12. Continuous Improvement
Any process issue, fragile test, incorrect pattern, or learning detected during execution → add as `[] short description` to `docs/mejoras-proceso/to-do.md`.

### 13. Soft Deletes Only
Use `deleted_at` column — never hard delete records.

---

## Testing Strategy

| Layer | Framework | Location | Notes |
|-------|-----------|----------|-------|
| Unit (Backend) | pytest (asyncio_mode=auto) | `backend/tests/modules/{module}/` | Fixtures in per-module `conftest.py` |
| Unit (Frontend) | Vitest (happy-dom) | `*.test.ts` colocated with features or in `__tests__/` dirs | |
| Architecture | pytest | `backend/tests/architecture/` | DDD layer checks, ETL contract, dependency graph |
| E2E Smoke | Playwright | `frontend/e2e/specs/smoke/` | Runs on every PR |
| E2E Regression | Playwright | `frontend/e2e/specs/regression/` | Runs before release |
| E2E Full | Playwright | `frontend/e2e/` | Runs in CI pipeline |
| Verification | pytest + Playwright | `backend/tests/verification/`, `frontend/e2e/` | 4-layer data reliability protocol |

---

## Docker Containers (Development)

| Container | Service | Port | Profile |
|-----------|---------|------|---------|
| `visionarias_brain_dev` | FastAPI (uvicorn --reload) | 8000 | core |
| `visionarias_client_dev` | Next.js (Turbopack) | 3000, 6006 | core |
| `visionarias_postgres` | PostgreSQL 15 | 5432 | core |
| `visionarias_redis` | Redis 7 | 6379 | core |
| `visionarias_qdrant` | Qdrant v1.7.3 | 6333, 6334 | core |
| `visionarias_admin_dev` | Streamlit admin | 8502 | extended/admin |
| `visionarias_scheduler` | Arq scheduler | — | extended/etl |
| `visionarias_worker` | Arq worker | — | extended/etl |
| `frontend_tooling` | Frontend build tools | — | tooling |
| `backend_tooling` | Backend build tools | — | tooling |
| `visionarias_e2e_runner` | Playwright E2E | — | e2e |
| `cloudflare-tunnel` | Cloudflare tunnel | — | core |

---

## CI/CD Pipeline

Push to `main` triggers (`.github/workflows/deploy-prod.yml`):
1. **Quality Gates:** Backend lint + tests, Frontend types + lint + tests
2. **Security Scan:** Trivy vulnerability scanning
3. **Build:** Push Docker images to GHCR (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`)
4. **Deploy:** SSH to VPS, pull images, run migrations
5. **Healthcheck:** API + frontend health verification
6. **Deploy Worker:** Cloudflare Worker deployment
7. **Notify Failure:** Slack alert on failure

---

## Code Style & Conventions

### Backend (Python)
- **Line length:** 120 characters
- **Imports:** Sorted by `isort` (via ruff `I` rules)
- **Type annotations:** Required in `src/` (via ruff `ANN` rules)
- **Docstrings:** Google convention (via ruff `D` rules)
- **Max cyclomatic complexity:** 15
- **No `print()` in production code** (use `structlog`)
- **Pydantic v2** patterns (model validators, field validators)
- **SQLAlchemy 2.0** async patterns (`select()`, `session.execute()`)

### Frontend (TypeScript)
- **Strict mode** enabled in `tsconfig.json`
- **ESLint** with Next.js recommended rules
- **Zod** for runtime validation
- **React Query** for server state (no manual fetch)
- **Server Components** by default (mark client components with `"use client"`)
- **shadcn/ui** for UI primitives (auto-generated, don't edit manually)

---

## Environment Variables

Key environment variables (defined in `.env` or `.env.prod`):

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL credentials |
| `DATABASE_URL` | SQLAlchemy connection string |
| `REDIS_URL` | Redis connection string |
| `QDRANT_URL` | Qdrant vector DB URL |
| `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk authentication |
| `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_APP_URL` | Shopify integration |
| `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_URL`, `INTERNAL_API_URL` | Frontend API routing |
| `API_DOMAIN`, `DASHBOARD_DOMAIN` | Traefik routing |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare Tunnel |
| `OPENAI_API_KEY` | LLM provider |
| `SENTRY_*` | Error tracking |
| `E2E_CLERK_*` | E2E testing credentials |

---

## Common Workflows

### Adding a New Feature
1. Create tests first (RED) — follow TDD rules
2. Implement domain layer (models, value objects)
3. Implement infrastructure layer (repositories, external clients)
4. Implement application layer (services, use cases)
5. Implement API layer (routes, DTOs) — thin, delegates to application
6. Run lint + tests (GREEN)
7. Refactor if needed
8. Update ETL contract if touching analytics
9. Run architecture tests

### Fixing a Bug
1. Write a regression test that reproduces the bug (RED)
2. Fix the bug (GREEN)
3. Run lint + tests to ensure no regressions
4. Add to `docs/mejoras-proceso/to-do.md` if it reveals a process issue

### Database Migration
1. Create Alembic migration: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic revision --autogenerate -m 'description'"`
2. Review generated SQL — ensure idempotent (`IF NOT EXISTS`, etc.)
3. Run migration: `make migrate`
4. Verify on fresh DB if possible

### Working on Analytics/ETL
1. Read `docs/etl/extraction-contract.md` first
2. Make changes to provider/service/pipeline
3. Update `extraction_contract.py`
4. Regenerate doc: `make extraction-contract`
5. Run tests: `cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q`
6. Run 4-layer verification: `make verify-meta`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied on files after Docker writes | `make fix-permissions` |
| Frontend won't rebuild | `make fix-front` or delete `frontend/node_modules` and `frontend/.next`, then `make dev` |
| Backend import errors | Ensure `.venv` is set up: `cd backend && python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` |
| Docker uses too much RAM | `make test-mode` to stop non-essential containers, `make dev-mode` to restore |
| Shopify app shows wrong config | `make shopify-config-status` to check, `make shopify-config-dev` or `make shopify-config-prod` to switch |
| E2E tests fail with auth errors | Regenerate Clerk testing token (done automatically by `make e2e`) |
| Traefik routing fails | Ensure external network exists: `docker network create web_gateway || true` |

---

## Additional Resources

- **Module docs:** `docs/domains/module_{name}.md` (15 domain docs)
- **Product vision:** `docs/domains/vision/product-vision.md`
- **ETL extraction contract:** `docs/etl/extraction-contract.md`
- **Architecture rules:** `.claude/rules/` (18 rule files)
- **Guides:** `docs/guides/` (14 files covering copilot, frontend, data flows, etc.)
- **Runbooks:** `docs/runbooks/` (Clerk JWT email claim, etc.)
- **Process improvements:** `docs/mejoras-proceso/to-do.md`

---

## Notes for AI Agents

- **DO NOT hallucinate** — read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
- **DO read the relevant module doc** before working on a feature.
- **DO follow the DDD layer structure** strictly — domain → infrastructure → application → api.
- **DO NOT skip tests** — TDD is mandatory, no exceptions.
- **DO use native tools** — never run lint/tests/type-checks inside Docker.
- **DO check the ETL contract** before touching analytics code.
- **DO verify Spanish text** has proper accents and ñ.
- **DO add process learnings** to `docs/mejoras-proceso/to-do.md`.
