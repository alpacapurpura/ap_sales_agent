# CLAUDE.md

**Nicolify** — Multitenant SaaS (AaaS) marketing/sales automation. FastAPI async + Next.js 16 FSD + Clerk + Postgres/Qdrant. Modular Monolith DDD + Docker-First.

## Modules

Brand/Offer: `brand`, `offer` · Assets: `landing`, `assets` · Growth: `analytics`, `advertising`, `social_media` · Sales: `sales_agent`, `scheduling` · Config: `connections` · Support: `iam`, `crm`, `core`, `shared`, `copilot` · Detalle → `docs/domains/INDEX.md`.

## Commands

| | |
|---|---|
| BE full | `/test-backend` |
| FE full | `/test-frontend` |
| Full CI | `/test-all` |
| Dev up | `/dev-up` |
| Migration | `/migrate <msg>` |
| Single BE | `cd backend && .venv/bin/pytest tests/modules/{m}/ -v` |
| Single FE | `cd frontend && npx vitest run src/features/{d}/` |
| E2E smoke | `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` |

Docker containers: `visionarias_brain_dev:8000` · `visionarias_client_dev:3000` · `visionarias_admin_dev:8502` · `visionarias_postgres:5432`.

## Native-First (mandatory)

Lint/tests/type-check **NATIVE WSL siempre**. Docker = runtime + migrations + ci-parity gate. `docker exec ... ruff|pytest|tsc|vitest|eslint` PROHIBIDO.

- BE: `cd backend && .venv/bin/{ruff|pytest|pip-audit}` (venv 3.12)
- FE: `cd frontend && npx {tsc|eslint|vitest|playwright}`
- CI-parity gate antes `git push origin main`: `make ci-parity` (5 deploys fallidos 2026-04-27 sin esto). `/pase-produccion` lo enforza.

## Architecture

**BE** `backend/src/modules/{name}/{domain,infrastructure,application,api}/` (Inside-Out). `main.py` mounts `/api/v1/{module}/`. `shared/` events+entities, `core/` config+DB.

**FE** `frontend/src/{app,components/{ui,shared},features/{domain},lib,hooks}/`. FSD-Lite. `fetchClient` auto-injects `X-Tenant-ID`.

**CI/CD** `.github/workflows/deploy-prod.yml`. Push `main` → quality-gates → Trivy → GHCR `ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`.

## Critical Rules

Rules siempre cargadas (universales):

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `docs/domains/INDEX.md` antes coding |
| 2 | Tenant isolation | `.claude/rules/tenant-isolation.md` |
| 3 | BE DDD | `.claude/rules/backend-ddd.md` |
| 4 | FE FSD | `.claude/rules/frontend-fsd.md` |
| 5 | Migrations idempotentes | `.claude/rules/backend-migrations.md` |
| 6 | Git/Conventional Commits | `.claude/rules/git-safety.md` |
| 7 | Parallel safety (multi-instancia) | `.claude/rules/parallel-safety.md` |
| 8 | TDD obligatorio | `.claude/rules/tdd-mandatory.md` |
| 9 | Debugging | `.claude/rules/debugging.md` |
| 10 | Spanish neutro LatAm | `.claude/rules/spanish-text.md` |
| 11 | PII (`response_model=`) | `@AGENTS.md` → Tessl pii-sanitisation |

Rules condicionales (stub apunta a skill — invocar el skill carga detalle):

| Tocas | Skill | Stub |
|---|---|---|
| `modules/copilot/` | `copilot-expert` | `rules/copilot-resilience.md`, `rules/copilot-observability.md` |
| `modules/sales_agent/` | `sales-agent-expert` | `rules/sales-agent-brand-voice.md` |
| `modules/offer/` catalogs | `offer-expert` / `offer-type-preset-expert` | `rules/offer-catalogs.md` |
| `modules/analytics/` ETL | `metrics-expert` | `rules/etl-extraction-contract.md`, `rules/analytics-metrics.md`, `rules/data-reliability.md` |
| Backend quality/master-data/currency/arch-fitness | `backend-expert` | `rules/{backend-quality,master-data,currency-handling,architectural-fitness}.md` |
| Frontend quality/form-runtime | `frontend-expert` / `brand-expert` | `rules/{frontend-quality,form-runtime-array}.md` |
| Streamlit admin | `backend-expert` | `rules/admin-panel.md` |
| E2E Playwright | (none — usa `/test-all`) | `rules/e2e-testing.md` |
| PM/SSoT funcional | `pm` skill | `rules/pm-nico-ssot.md` |

## Vision

`docs/domains/vision/product-vision.md`.

@AGENTS.md
