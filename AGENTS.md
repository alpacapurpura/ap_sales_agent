# AGENTS.md

**Nicolify** — Multitenant AaaS marketing/sales automation. FastAPI async + Next.js 16 FSD + Clerk + Postgres/Qdrant. Modular Monolith DDD + Docker-First.

## Agent Rules <!-- tessl-managed -->

@.tessl/RULES.md follow the [instructions](.tessl/RULES.md)

## Quick Commands

| Action | Command |
|---|---|
| Dev up | `make dev` (Docker) |
| BE full suite | `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/ruff format --check src/ tests/ && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts=" && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -x -q --tb=short` |
| FE full suite | `cd frontend && npx tsc --noEmit && npx eslint src/ --cache --cache-location .eslintcache && npx vitest run --coverage --reporter=default --reporter=json --outputFile=/tmp/vitest-coverage.json` |
| Full CI gate | `make ci-parity` (mandatory before `git push origin main`) |
| BE single module | `cd backend && .venv/bin/pytest tests/modules/{name}/ -v` |
| FE single feature | `cd frontend && npx vitest run src/features/{name}/` |
| Alembic migration | Generate + review + make idempotent (`IF NOT EXISTS`), then `docker exec visionarias_brain_dev alembic upgrade head` |
| E2E smoke | `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke` |
| ETL contract regen | `make extraction-contract` (required after touching analytics providers/scheduler/workers) |

## Native-First (mandatory)

**NEVER** run lint/tests/type-check inside Docker. Always native WSL:
- BE: `cd backend && .venv/bin/{ruff,pytest,pip-audit}` (venv 3.12)
- FE: `cd frontend && npx {tsc,eslint,vitest,playwright}`
- Docker only for: runtime (`make dev`), migrations (`docker exec visionarias_brain_dev alembic`), and `make ci-parity`.

## Architecture

**Backend** `backend/src/modules/{name}/{domain,infrastructure,application,api}/` — Inside-Out DDD. `main.py` mounts `/api/v1/{module}/`. `shared/` = events + entities + infra. `core/` = config + DB session.

**Frontend** `frontend/src/{app,components/{ui,shared},features/{domain},lib}/` — FSD-Lite. `fetchClient` auto-injects `X-Tenant-ID`.

**DB**: Alembic migrations must be **idempotent** (`IF NOT EXISTS` / `IF EXISTS`). Never `sa.Enum()` in `create_table`.

**Modules**: brand, offer, landing, sales_agent, copilot, crm, scheduling, analytics, connections, assets, tenant_domains, commercial_calendar, campaigns, iam, core, shared. Detail → `docs/domains/INDEX.md`.

## Git Workflow

Single branch = `development`. `main` = prod only. No feature branches, no worktrees, no `git pull`.

**Forbidden**: `git pull`, `git fetch && merge`, `git checkout -b`, `git worktree add`, `git push --force`, `git revert` (without approval), `git add .` / `git add -A`, `git commit --no-verify`.

**Required**: Work on `development`. `git add <path>` by exact file name. If `git push origin development` fails (non-fast-forward) → STOP, report. No `git pull`.

**Multi-session shared filesystem**: same branch, same workdir. Touch files from other sessions only for extend/append (never replace/delete). If changes would conflict → STOP.

## Skills (load when touching these modules)

| Module/Stack | Skill |
|---|---|
| `copilot/` | `copilot-expert` |
| `sales_agent/` | `sales-agent-expert` |
| `offer/` catalogs/presets | `offer-expert` / `offer-type-preset-expert` |
| `analytics/` ETL/metrics | `metrics-expert` |
| `brand/` identity/positioning | `brand-expert` |
| Backend quality, DDD, currency, arch fitness | `backend-expert` |
| Frontend quality, form runtime | `frontend-expert` |
| Git/PR/release | `git-manager` |
| Deploy to production | `pase-produccion` |
| E2E live verification | `chrome-devtools-verify` |
| Social content creation | `content-hunter` |
| ManyChat integration | `manychat-expert` |
| PM/SSoT functional | `pm` skill (SSoT: `docs/product/BACKLOG.md` + `docs/product/{outcomes,stories,ideas-pool.yaml}`) |
| User story (UI std) — Gherkin + wireframes inline | `po-ux` skill (NEW fusión `/po` + `/ux-ui`) |
| User story (service-only) — Gherkin pure | `po` skill |
| Agentic conversational flow | `ux-agentico` skill |
| Architecture + ready package (validators + guidelines + tickets) | `architect` skill |
| Autonomous build (Conv 2) | `dev-team` skill |
| Code review (Conv 3) | `auditor` skill |
| Backlog freshness (R33) | `scripts/generate_backlog.py` (auto via pre-commit hook Section 6) |
| Capability reconciliation (R32) | `scripts/reconcile_capabilities.py` |

## Quality Gates

- Lint → arch fitness → tests → coverage → CI parity. Stop on first failure.
- BE coverage threshold: 43%. FE coverage: 20% all categories.
- Ruff line-length: 120. Format: `ruff format --check` (double quotes, spaces).
- TypeScript: `tsc --noEmit` (strict).
- CI parity (`make ci-parity`) catches env/UTC/heap/build-context divergences that native runs miss. Mandatory pre-push-to-main.
- Pre-commit hook: ruff on staged `.py` files (native, backend venv).

## SSoT Guard (contract-guard hook)

Editing these files triggers a reminder to run their associated verification:
- `analytics/infrastructure/providers/` or `etl/` → run `make extraction-contract` + arch test
- `analytics/domain/metric_catalog.py` → verify catalog↔contract alignment
- `offer/domain/{archetype,value_level,format}_catalog.py` → bump `_CATALOG_VERSION` + run arch tests both stacks
- `analytics/application/services/channel_registry.py` → no duplicate STAGE_CHANNEL_MAP
- `copilot/domain/module_registry.py` → ModuleDescriptor entry required for new modules

## Key Constraints

- **Tenant isolation**: every query must filter by `tenant_id`. See `.claude/rules/tenant-isolation.md`.
- **PII sanitisation**: Tessl rule loaded via `@.tessl/RULES.md`. Response models must exclude PII.
- **Spanish neutro LatAm**: all user-facing text. Technical terms in English OK.
- **TDD mandatory**: tests before implementation.
- **Idempotent migrations**: every DDL statement must use `IF NOT EXISTS` / `IF EXISTS`.
- **BE venv path**: `backend/.venv/` (Python 3.12). Use `.venv/bin/pytest`, not system `pytest`.
- **E2E requires Clerk testing token**: `make e2e` auto-generates it. Native E2E needs `CLERK_TESTING_TOKEN` env var.
