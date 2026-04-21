# CLAUDE.md

Guidance for Claude Code in this repo.

## Project

**Nicolify** — Multitenant SaaS (AaaS). Automate marketing/sales for creators, pros, small biz.
**Stack:** FastAPI (Async/SQLA 2.0), Next.js 16 (App Router/FSD), Clerk, Qdrant.
**Pattern:** Modular Monolith (DDD) + Docker-First.

## Core Domains

| Studio | Modules |
|---|---|
| Brand/Offer | `brand`, `offer` |
| Assets | `landing`, `assets` |
| Growth | `analytics`, `advertising`, `social_media` |
| Sales | `sales_agent`, `scheduling` |
| Config | `connections` |
| Supporting | `iam`, `crm`, `core`, `shared` |

Unsure? Read `docs/domains/INDEX.md` (15 docs).

## Commands

**Lint/tests/type-check NATIVE WSL. NEVER Docker.**
**Docker: runtime + migrations only.**

| Action | Command |
|---|---|
| BE full | `/test-backend` — lint+format+arch+unit+jscpd+interrogate+pip-audit |
| FE full | `/test-frontend` — TSC+ESLint+Vitest+jscpd+knip+madge+npm audit |
| Full CI | `/test-all` — BE+FE+E2E smoke+migration |
| Dev up | `/dev-up` → `docker compose up -d` |
| Migration | `/migrate <msg>` |
| Explore mod | `/explore-module <name>` |
| Review PR | `/review-pr` |
| Single BE | `cd backend && .venv/bin/pytest tests/modules/{m}/ -v` |
| Single FE | `cd frontend && npx vitest run src/features/{d}/` |
| FE arch | `cd frontend && npx vitest run src/__tests__/architecture/` |
| E2E smoke | `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` |

### Docker Containers

| Container | Service | Port |
|---|---|---|
| `visionarias_brain_dev` | FastAPI uvicorn --reload | 8000 |
| `visionarias_client_dev` | Next.js dev | 3000 |
| `visionarias_admin_dev` | Streamlit admin | 8502 |
| `visionarias_postgres` | Postgres 15 | 5432 |

## Architecture

### Backend (`backend/src/`)

16 contexts in `modules/`. DDD Inside-Out:

```
modules/{name}/
  domain/         # Models, VOs, repo interfaces. No framework imports.
  infrastructure/ # SQLA repos, external clients.
  application/    # Services, use cases.
  api/            # FastAPI routes + Pydantic DTOs. Thin.
```

`main.py` mounts modules at `/api/v1/{module}/`.
`shared/` (base entities, event bus, registry), `core/` (config, DB, security).

### Frontend (`frontend/src/`)

FSD-Lite (domain-grouped):

```
app/                # Next.js App Router (thin)
  (main)/           # Auth routes
  (landing)/        # Public
components/
  ui/               # Shadcn primitives (auto-gen, don't edit)
  shared/           # Cross-feature layout
features/{domain}/  # components/, hooks/, api/, types/, utils/
lib/                # API client, design tokens, utils
```

`fetchClient` (in `lib/`) auto-injects `X-Tenant-ID` from Clerk. Always use.

### Testing

- BE: pytest (asyncio_mode=auto). `backend/tests/modules/{m}/`. Per-module `conftest.py`.
- FE: Vitest (happy-dom). `*.test.ts` colocated or `__tests__/`.
- E2E: Playwright.

### CI/CD (`.github/workflows/deploy-prod.yml`)

Push `main` → quality-gates → Trivy → GHCR push (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`).

### ETL Extraction Contract

SSoT for ETL. Before ETL questions, read:

| File | Contains |
|---|---|
| `backend/src/modules/analytics/domain/extraction_contract.py` | Python dataclasses: provider, code, auth, endpoints, channels, metrics, schedule, tables, issues. Editable. |
| `docs/etl/extraction-contract.md` | Auto-gen MD. NEVER edit. Regen: `cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py`. |
| `backend/tests/architecture/test_extraction_contract.py` | 48 arch tests. Fail on drift. In `make arch-test`, `/test-all`. |

Change provider → update contract, regen doc, run test.

## Native Dev Tools (WSL) — MANDATORY

Docker mounts `/app` = main clone. Worktrees see stale. Native reads real FS.

**NEVER `docker exec` lint/tests/type-check. Always native.**

### Backend

venv: `backend/.venv` (3.12, ruff, pytest, pytest-cov, factory-boy, faker)

| Task | Command |
|---|---|
| Lint | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` |
| Format | `cd backend && .venv/bin/ruff format --check src/ tests/` |
| Tests | `cd backend && .venv/bin/pytest -x -q --tb=short` |
| Arch | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` |
| Coverage | `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| Single mod | `cd backend && .venv/bin/pytest tests/modules/{m}/ -v` |
| Security | `cd backend && .venv/bin/pip-audit --strict --desc` |

### Frontend

node_modules: `frontend/node_modules` (vitest, tsc, next, eslint)

| Task | Command |
|---|---|
| TSC | `cd frontend && npx tsc --noEmit` |
| Lint | `cd frontend && npx eslint src/` |
| Tests | `cd frontend && npx vitest run` |
| Coverage | `cd frontend && npx vitest run --coverage` |
| Single | `cd frontend && npx vitest run src/features/{d}/` |
| Security | `cd frontend && npm audit --audit-level=high` |

### Docker ONLY:
- Runtime: `docker compose up -d`
- Migrations: `docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"`
- Logs: `docker logs visionarias_brain_dev --tail 100`
- Fresh DB migration verify

### PROHIBITED:
```
docker exec ... ruff|pytest|tsc|vitest|eslint
docker run --rm ... ruff|pytest|tsc|vitest
```

## Critical Rules

1. **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess.
2. **Native-First:** Lint/tests/type-check NATIVE. Never Docker.
3. **Tenant Isolation:** ALL queries filter `X-Tenant-ID`. `.claude/rules/tenant-isolation.md`.
4. **BE DDD:** Inside-Out, no cross-module imports (except copilot). `.claude/rules/backend-ddd.md`.
5. **FE FSD:** Server Components default, no deep feature imports (except copilot). `.claude/rules/frontend-fsd.md`.
6. **Migrations:** Idempotent (raw SQL `IF NOT EXISTS`). `.claude/rules/backend-migrations.md`.
7. **PII:** Every endpoint MUST `response_model=`. PII masked/justified. Via `@AGENTS.md` → Tessl.
8. **Git:** Conventional Commits, no force push main. `.claude/rules/git-safety.md`.
9. **Debugging:** Docker diag + patterns. `.claude/rules/debugging.md`.
10. **Copilot:** Schema introspection, module registry, route-based tools. `.claude/rules/copilot-resilience.md`.
11. **Spanish neutro LatAm (sin voseo):** Todo user-facing español latinoamericano neutro. Tuteo `tú`, nunca `vos/tenés/podés/mirá/dejá`. Nicolify vende Latam — dejo argentino excluye MX/CO/PE/CL. Tildes/eñes correctas (`días`, `Campaña`). Aplica componentes, schemas (labels/hints/placeholders), catálogos backend user-facing, prompts LLM output visible, emails, notificaciones. Verificar antes commit. `.claude/rules/spanish-text.md`.
12. **Mejora continua:** Problema proceso/test frágil/patrón incorrecto/aprendizaje → `[] descripción` en `docs/mejoras-proceso/to-do.md`. Sin verbosidad.
13. **TDD Obligatorio:** Tests PRIMERO, implementación DESPUÉS. Sin excepciones. Features: test por capa antes. Bugs: test regresión antes fix. Existente sin tests: cubrir primero. `.claude/rules/tdd-mandatory.md`.
14. **ETL Contract:** Antes ETL/analytics: leer `docs/etl/extraction-contract.md`. Antes modificar `backend/src/modules/analytics/`: leer regla. Después cambio providers/pipeline/scheduler/workers/catálogo: update `extraction_contract.py`, regen MD `make extraction-contract`, correr arch test. Sin excepciones. `.claude/rules/etl-extraction-contract.md`.
15. **Data Reliability:** Cambio Growth Studio → verification layer. `.claude/rules/data-reliability.md`.
16. **FE Quality:** 0 ESLint errors, 1063 tests, 20% coverage. No nuevos errores. `.claude/rules/frontend-quality.md`.
17. **FE Arch Tests:** 8 fitness tests `src/__tests__/architecture/` — PascalCase components, kebab-case files/folders, hooks in hooks/, no default exports, no cross-feature dupes, canonical structure, fetchClient in api/. Ratchet (allowlists shrink only).
18. **BE Quality:** Ruff 70+ rules, 0 errors, 7 arch gates, 43% coverage. No nuevos. `.claude/rules/backend-quality.md`.
19. **Form-runtime Array:** Campos array ≤3 sub-fields → modo `cards`, ≥4 → modo `split`. Default automático por `itemSchema.fields.length`. Autosave on-change preservado. `.claude/rules/form-runtime-array.md`.

## Vision

Decisiones funcionales: `docs/domains/vision/product-vision.md`.

@AGENTS.md
