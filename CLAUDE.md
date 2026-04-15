# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Nicolify** — Multitenant SaaS (AaaS) automating marketing/sales for creators, professionals and small businesses.
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

| Action | Command | What it runs |
|---|---|---|
| **Backend full** | `/test-backend` | Lint + format + 10 arch tests + unit tests + jscpd + interrogate + pip-audit |
| **Frontend full** | `/test-frontend` | TSC + ESLint (60+) + Vitest + jscpd + knip + madge + npm audit |
| **Full CI** | `/test-all` | Backend + Frontend + E2E smoke + migration test |
| Start dev | `/dev-up` | `docker compose up -d` |
| Run migration | `/migrate <msg>` | Alembic inside Docker |
| Explore module | `/explore-module <name>` | DDD structure inspection |
| Review PR | `/review-pr` | Diff analysis vs main |
| Single backend test | — | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |
| Single frontend test | — | `cd frontend && npx vitest run src/features/{domain}/` |
| E2E smoke (native) | — | `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` |

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
- **E2E:** always Playwright.

### CI/CD (`.github/workflows/deploy-prod.yml`)

Push to `main` triggers: quality-gates (lint+test) → security-scan (Trivy) → push images to GHCR (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`).

### ETL Extraction Contract

**Single source of truth for what the analytics ETL extracts.** Before answering any question about ETL providers, where data comes from, when extractions run, or where data lands, consult these files:

| File | What it contains |
|---|---|
| `backend/src/modules/analytics/domain/extraction_contract.py` | Python dataclasses with the canonical contract: provider name, code location, auth, API endpoints, channels emitted, metrics per channel, schedule, storage tables, known issues. Editable. |
| `docs/etl/extraction-contract.md` | Auto-generated Markdown rendering of the same contract. **Do not edit by hand.** Regenerate with `cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py`. |
| `backend/tests/architecture/test_extraction_contract.py` | Architecture test (48 cases) that fails if the contract drifts from reality: provider classes don't match, registered providers without contract entries, catalog metrics not in contract, generated doc out of date, etc. |

**When you change a provider:** update the contract entry, regenerate the doc, run the test. The test runs as part of `make arch-test` and `/test-all`.

**When you ask "what does the ETL extract for X?":** read `docs/etl/extraction-contract.md` first — it has the answer without needing to read provider source code.

## Native Dev Tools (WSL) — MANDATORY

> **Why:** Docker volume mounts (`/app`) always point to the main repo clone. When running
> parallel agents with git worktrees, the container sees stale code from the wrong worktree.
> Native tools read the actual filesystem path, making them reliable for multiagent workflows.

**CRITICAL RULE: NEVER use `docker exec` for lint, tests, or type-checking. Always run natively.**

### Backend (Python)

**virtualenv:** `backend/.venv` (Python 3.12, ruff, pytest, pytest-cov, factory-boy, faker)

| Task | Native command (run from repo root) |
|---|---|
| Lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Format check | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| All tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Architecture tests | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Tests with coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| Single module | `cd backend && .venv/bin/pytest tests/modules/{module}/ -v` |
| Security audit | `cd backend && .venv/bin/pip-audit --strict --desc` |

### Frontend (Node.js)

**node_modules:** `frontend/node_modules` (vitest, tsc, next, eslint)

| Task | Native command (run from repo root) |
|---|---|
| Type check | `cd frontend && npx tsc --noEmit` |
| Lint | `cd frontend && npx eslint src/` |
| All tests | `cd frontend && npx vitest run` |
| Tests with coverage | `cd frontend && npx vitest run --coverage` |
| Single feature | `cd frontend && npx vitest run src/features/{domain}/` |
| Security audit | `cd frontend && npm audit --audit-level=high` |

### Docker ONLY for:
- Runtime services: `docker compose up -d`
- Migrations: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`
- Logs: `docker logs visionarias_brain_dev --tail 100`
- Migration verification on fresh DB

### PROHIBITED (never do this):
```
docker exec -t visionarias_brain_dev bash -c "ruff ..."
docker exec -t visionarias_brain_dev bash -c "pytest ..."
docker exec -t visionarias_client_dev npx tsc ...
docker exec -t visionarias_client_dev npx vitest ...
docker exec -t visionarias_client_dev npx eslint ...
docker run --rm ... ruff|pytest|tsc|vitest ...
```

## Critical Rules

1. **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2. **Native-First Testing:** Lint, tests, type-checks run natively in WSL — never inside Docker. Docker volume mounts point to main repo clone, not worktrees.
3. **Tenant Isolation:** ALL queries filter by `X-Tenant-ID`. See `.claude/rules/tenant-isolation.md`.
4. **Backend DDD:** Inside-Out layers, no cross-module imports (except copilot). See `.claude/rules/backend-ddd.md`.
5. **Frontend FSD:** Server Components by default, no deep feature imports (except copilot). See `.claude/rules/frontend-fsd.md`.
6. **Migrations:** Must be idempotent (raw SQL with `IF NOT EXISTS`). See `.claude/rules/backend-migrations.md`.
7. **PII:** Every endpoint MUST declare `response_model=`. PII fields must be masked or justified (loaded via `@AGENTS.md` → Tessl rules).
8. **Git:** Conventional Commits, never force push main. See `.claude/rules/git-safety.md`.
9. **Debugging:** Docker diagnostics + common error patterns. See `.claude/rules/debugging.md`.
10. **Copilot:** Schema introspection, module registry, route-based tools. See `.claude/rules/copilot-resilience.md`.
11. **Spanish text:** Todo texto visible al usuario en español DEBE llevar tildes y eñes correctas (`días` no `dias`, `Campaña` no `Campana`, `Inversión` no `Inversion`). Verificar antes de commitear. See `.claude/rules/spanish-text.md`.
12. **Mejora continua:** Cualquier problema de proceso, test frágil, patrón incorrecto, o aprendizaje detectado durante ejecución → agregarlo como `[] descripción corta` en `docs/mejoras-proceso/to-do.md` (crear si no existe). Sin verbosidad, solo el hallazgo concreto.
13. **TDD Obligatorio:** Tests PRIMERO, implementación DESPUÉS. Sin excepciones. Features: test por capa antes de implementar. Bugs: test de regresión antes del fix. Existente sin tests: cubrir primero, luego modificar. See `.claude/rules/tdd-mandatory.md`.
14. **ETL Extraction Contract:** Antes de responder cualquier pregunta sobre el ETL/analytics, leer `docs/etl/extraction-contract.md` PRIMERO. Antes de modificar cualquier cosa en `backend/src/modules/analytics/`, leer la regla completa. Después de cualquier cambio que toque providers, pipeline, scheduler, workers o catálogo: actualizar `extraction_contract.py`, regenerar el markdown con `make extraction-contract`, correr `pytest tests/architecture/test_extraction_contract.py`. Sin excepciones. See `.claude/rules/etl-extraction-contract.md`.
15. **Data Reliability:** After modifying any Growth Studio file (provider, service, DTO, frontend component), run the corresponding verification layer. See `.claude/rules/data-reliability.md`.
16. **Frontend Quality:** 0 ESLint errors, 1063 tests, 20% coverage threshold. No new errors. Fast scan: `cd frontend && ./node_modules/.bin/eslint src/ --cache --cache-location .eslintcache`. See `.claude/rules/frontend-quality.md`.
17. **Backend Quality:** Ruff 70+ rules, 0 errors, 7 arch fitness gates, 43% coverage. No new violations. See `.claude/rules/backend-quality.md`.

## Product Vision

For functional decisions allways: `docs/domains/vision/product-vision.md`.

@AGENTS.md
