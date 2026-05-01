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

## Git Workflow — INVIOLABLE

Multi-instancia Claude Code = mismo workdir, mismo branch, mismo filesystem. Cada sesión commitea SU propio trabajo. Mismo código compartido es OK — la probabilidad de colisión real (misma función, misma línea) es mínima cuando sesiones tocan módulos distintos.

**PROHIBIDO sin excepción:**
- `git pull` / `git fetch && merge` (sesiones se desincronizan; conflictos al push se resuelven manualmente)
- `git checkout -b <branch>` (feature branches)
- `git worktree add` (Chris perdió 1 semana con worktrees previos)
- `git push --force` / `git push -f` / `git push --force-with-lease`
- `git revert <commit>` sin aprobación explícita Chris
- `git reset --hard` sin aprobación
- `git add .` / `git add -A` / `git add -u` (puede agregar archivos de otra sesión sin querer)
- `git commit --no-verify` (skip hooks)
- Branches feature/release/hotfix (default = `development`; `main` solo prod)

**Obligatorio:**
- Trabajar en `development`. Si en `main` → `git checkout development`. Si otro branch → `git checkout development`.
- `git add <path>` por nombre — solo archivos relevantes a tu PR.
- Conflicto al `git push origin development` (non-fast-forward) → STOP, reportar Chris. NO `git pull`.

**Tocar archivos de otra sesión paralela — REGLA CHRIS (2026-04-29):**
- **Permitido** si entendés lo que el otro creó + extend/append (no replace, no borrar).
- Si necesitás modificar misma función que otra sesión también editó: ambos cambios deben coexistir lógicamente. Si tu cambio es para acción distinta (común), añade tu lógica sin remover la del otro.
- Si tu cambio rompe el del otro → STOP, reportar Chris (coordina manual).
- Subagentes builders/auditores reciben paths permitidos PRIMARIOS (su PR) + PERMISO LECTURA cualquier archivo + REGLA "extend, no destroy" sobre ajenos.

**Filosofía:** filesystem compartido + commit por nombre + entender antes tocar. Probabilidad real colisión = baja porque módulos distintos. Conflictos resolvibles con cabeza fría leyendo lo que otro hizo.

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
| 12 | Anti-duplication (shared abstractions) | `.claude/rules/anti-duplication.md` |

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
