# Stack Tecnológico de Nicolify

Listado exhaustivo de tecnologías, metodologías y herramientas usadas en el proyecto, agrupadas por disciplina.

Última verificación: 2026-04-17.

---

## 1. Arquitectura de Software

### 1.1 Paradigmas y estilos arquitectónicos
- **Modular Monolith**: una sola aplicación desplegable con límites claros entre módulos (bounded contexts).
- **Domain-Driven Design (DDD)** en backend, aplicado en capas *Inside-Out*: `domain` → `infrastructure` → `application` → `api`.
- **Feature-Sliced Design Lite (FSD)** en frontend: slices por dominio (`features/{domain}/`), no por capa técnica.
- **Multitenant SaaS (AaaS — Agents as a Service)**: aislamiento por `tenant_id` en toda operación de datos.
- **Event-driven interno**: `shared/events/event_bus` para comunicación entre módulos cuando no se permite import directo.
- **Ports & Adapters (Hexagonal)**: repositorios definidos como interfaces en `domain/`, implementados en `infrastructure/`.
- **CQRS-lite**: separación parcial de lectura (overview/group_detail) vs. escritura (stage services) en Analytics.
- **Progressive loading tiers** (Growth Studio): Tier 0 resumen → Tier 1 overview → Tier 2 grupo → Tier 3 detalle (solo este consulta DB).
- **Pipeline ETL declarativo** con *extraction contract* como single source of truth.

### 1.2 Bounded Contexts (16 módulos backend)
- **Brand/Offer Studio**: `brand`, `offer`.
- **Assets**: `landing`, `assets`.
- **Growth**: `analytics`, `advertising`, `social_media`.
- **Sales**: `sales_agent`, `scheduling`, `commercial_calendar`.
- **Config**: `connections`, `tenant_domains`.
- **Supporting**: `iam`, `crm`, `core`, `copilot`, `shared`.

### 1.3 Reglas arquitectónicas fijas (enforced por fitness tests)
- Prohibido cross-module import (excepto `copilot` como orquestador infra-like).
- Domain layer sin imports de frameworks (SQLAlchemy, FastAPI, httpx).
- Todo endpoint debe declarar `response_model=` (PII allowlist).
- `FastAPI(redirect_slashes=False)` obligatorio a nivel app.
- Soft deletes únicamente (`deleted_at`), nunca hard delete.
- Solo sintaxis SQLAlchemy 2.0 (`select(...).where(...)`).
- `DateTime(timezone=True)` en todas las columnas; nunca `datetime.utcnow()`.
- Currency nunca hardcodeado (excepto en `shared/domain/currency.py`).
- Tenant isolation: toda query filtra por `tenant_id`.

### 1.4 Shared infrastructure
- `shared/domain/base_entity.py` — entidad base.
- `shared/domain/currency.py`, `shared/domain/locale.py` — master data (TenantLocale VO).
- `shared/events/` — event bus interno.
- `shared/links/` — ports inter-módulo.
- `core/` — config, database, security, settings.

---

## 2. Diseño Técnico del Software

### 2.1 Backend — Stack Python
- **Python 3.11+** (target ruff: `py311`).
- **FastAPI 0.135.1** — API framework async.
- **Uvicorn 0.34.0** + **Gunicorn ≥23** — ASGI servers (dev / prod).
- **Pydantic v2** (≥2.10) + **pydantic-settings** — DTOs, validación, config.
- **SQLAlchemy 2.0.27** async (con `greenlet`) — ORM.
- **Alembic ≥1.13** — migraciones idempotentes (raw SQL + `IF NOT EXISTS`).
- **psycopg2-binary 2.9.9** — driver PostgreSQL.
- **structlog ≥24** — logging estructurado.
- **python-jose / PyJWT ≥2.12** + **cryptography ≥46** — JWT, firma y cifrado.
- **passlib[bcrypt]** — hashing de passwords.
- **httpx ≥0.26** + **requests ≥2.32** — HTTP clients.
- **Jinja2 ≥3.1.6** — templating para prompts y emails.
- **email-validator ≥2.1** — validación RFC.
- **python-multipart** — uploads.
- **BeautifulSoup4** + **python-docx** + **pypdf** — scraping/parsing docs.
- **Pillow ≥12** — procesamiento de imágenes.
- **Svix ≥1.1** — verificación de webhooks.
- **FastAPI Depends pattern** — DI en endpoints.

### 2.2 Backend — IA / Agentic
- **LangChain 1.2.12** (+ `langchain-core`, `langchain-community`, `langchain-experimental`, `langchain-text-splitters`) — framework de agentes.
- **LangGraph 1.1.2** — state machines para el sales_agent.
- **langchain-openai 1.1.11** — cliente OpenAI.
- **langchain-google-genai 4.2.1** — cliente Gemini.
- **Qdrant** + **qdrant-client ≥1.13** — vector DB para RAG.
- **FastEmbed** + **flashrank** — embeddings y re-ranking local.

### 2.3 Backend — Workers / ETL
- **arq 0.27.0** — task queue sobre Redis.
- `SchedulerSettings` + `WorkerSettings` — cron y workers separados.
- **ETL Extraction Contract** (`extraction_contract.py`) — contrato declarativo + doc auto-generado + test de drift.
- Providers: Meta (Facebook Business SDK ≥22 <26), Google (GA4, Ads, OAuth2), Shopify, MailerLite, ManyChat (pass-through), CRM interno.

### 2.4 Backend — Admin
- **Streamlit ≥1.31** — panel administrativo interno (`src/admin/`).

### 2.5 Backend — Integraciones externas
- **facebook-business ≥22 <26** — Meta Ads / IG.
- **google-auth-oauthlib**, **google-api-python-client**, **google-analytics-data** — Google suite.
- **boto3 ≥1.34** — AWS S3.
- **Clerk** (vía JWT validation) — auth.
- **Sentry SDK ≥1.40** — error tracking.

### 2.6 Frontend — Stack
- **Next.js 16.2.3** con App Router + Turbopack.
- **React 19.2.3** + **React DOM 19.2.3**.
- **TypeScript 5.9** — strict mode, 0 errors.
- **Tailwind CSS v4.1.18** + **@tailwindcss/postcss** + **autoprefixer**.
- **Clerk** (`@clerk/nextjs` 6.36) — auth + sesión + test tokens.
- **TanStack Query 5.90** + **devtools** + **react-virtual** — data fetching y listas virtualizadas.
- **React Hook Form 7.71** + **@hookform/resolvers** + **Zod 4.3** — formularios + validación.
- **Zustand 5.0** — estado global.
- **Server Components por defecto**; `"use client"` solo cuando necesario.

### 2.7 Frontend — UI kit y primitivos
- **Shadcn UI** (auto-generado en `components/ui/`, no editar).
- **Radix UI primitives**: accordion, alert-dialog, avatar, checkbox, collapsible, dialog, dropdown-menu, label, popover, radio-group, scroll-area, select, separator, slot, switch, tabs, tooltip.
- **lucide-react** + **react-icons** — iconografía.
- **class-variance-authority** + **clsx** + **tailwind-merge** — utilidad `cn()`.
- **cmdk** — command palette.
- **next-themes** — dark/light mode.
- **framer-motion 12** — animaciones.
- **sonner 2** — toasts.
- **tailwindcss-animate** — animaciones de utilidad.

### 2.8 Frontend — Visualización y tooling UI
- **Recharts 2.15** — charts básicos.
- **@visx/** (sankey, shape, group, gradient, responsive, tooltip) — charts custom.
- **react-day-picker 9** + **date-fns 4** + **date-fns-tz** — fechas.
- **react-textarea-autosize**, **nextjs-toploader**, **@dnd-kit/core** — UX helpers.
- **@puckeditor/core** — editor visual de páginas.
- **colorthief** — extracción de paleta.
- **uuid** — IDs.

### 2.9 Frontend — lib interno
- `lib/fetchClient` — auto-inyecta `X-Tenant-ID` desde sesión Clerk.
- `lib/format-money.ts`, `lib/format-date.ts` — respetan `TenantLocale`.
- `lib/design-system/` — registry de tokens.
- `lib/case-conversion.ts`, `lib/http-client.ts`, `lib/utils.ts`.

### 2.10 Contratos tipados cross-stack
- Pydantic v2 → JSON Schema → tipos TypeScript derivados manualmente, alineados por fitness tests.
- `response_model=` en FastAPI actúa como allowlist (PII sanitisation — regla Tessl).

---

## 3. Diseño UX / UI / System Design

### 3.1 Design system
- Tokens centralizados en `lib/design-system/` + `tailwind.config`.
- Dark/light mode vía `next-themes`.
- Shadcn UI como librería base de componentes atómicos.
- Composición via Radix primitives + variantes con `class-variance-authority`.

### 3.2 Metodologías UX
- **Design Thinking** (7-phase workflow) via skill `ux-disruptivo`.
- **Feature-Sliced Design Lite** como guía de estructura de componentes por dominio.
- **Server-First rendering** (Next.js RSC) para performance.
- **Journey mapping + flow audits** via skill `ux-flow-architect` (genera FLOW-SPEC.md, mockups HTML navegables).
- **Buyer personas + brand voice capture** (Brand Onboarding + Interview Engine).

### 3.3 Localización / Master Data
- **Spanish-first**: tildes y eñes obligatorios en texto user-facing (regla `spanish-text.md`).
- **TenantLocale**: currency (ISO 4217) y timezone (IANA) por tenant.
- **Currency display rules**: fuente + equivalente tenant + USD según contexto (`formatMoneyDual`, `formatAggregatedMoney`).
- **Timezones**: UTC en DB, conversión en frontend con `formatTenantDate/Time/DateTime`.

### 3.4 Accesibilidad
- **eslint-plugin-jsx-a11y** — reglas a11y en build.
- **@storybook/addon-a11y** — auditoría en Storybook.
- Radix UI aporta ARIA y keyboard nav por defecto.

### 3.5 Prototipado y documentación de UI
- **Storybook 10.3.4** (`@storybook/nextjs-vite`) con `addon-themes`, `addon-a11y`, `eslint-plugin-storybook`.
- Mockups HTML servidos en `localhost:8888` para validación de flujos.
- `docs/mockups/`, `docs/ui-specs/`, `docs/flow-specs/` — artefactos de diseño.

### 3.6 Patrones UI sistémicos
- Expandable sidebar (3 estados) + preview pane + focus tools (Unified Copilot).
- Progressive disclosure en wizards (Brand, Offer, Onboarding).
- Server-First layout con hidratación selectiva.
- Command palette (`cmdk`) para navegación power-user.

---

## 4. Desarrollo de Software

### 4.1 Metodologías y prácticas
- **TDD obligatorio** (regla `tdd-mandatory.md`): RED → GREEN → REFACTOR por capa DDD.
- **Anti-hallucination**: leer `docs/domains/INDEX.md` antes de codificar.
- **Conventional Commits** — `<type>(<scope>): <description>`.
- **Trunk-based single-branch**: todo el trabajo en `development`; `main` = producción.
- **Ratchet pattern** en fitness tests (allowlists solo decrecen).
- **Native-First Testing**: lint/tests/type-checks se ejecutan nativamente en WSL, nunca `docker exec`.
- **Fix quality mandate**: root cause, leave-it-better, no nuevos `// TODO` / `any` / disabled rules.
- **4-Layer Data Reliability**: ETL execution → source probe → pipeline integrity → UI fidelity.

### 4.2 Editor y control de versiones
- Editor primario: **Claude Code** (Anthropic CLI) + VS Code.
- **Git** + **GitHub** (`alpacapurpura/ap_sales_agent`).
- **Husky 9** + **lint-staged 16** — pre-commit hooks.
- **Prettier 3.8** + **@trivago/prettier-plugin-sort-imports** + **prettier-plugin-tailwindcss** — formato.

### 4.3 Backend — tooling
- **Ruff** con 70+ reglas (Waves 1–5): E/W/F, I, UP, B, S, C901, PERF, DTZ, SIM, PIE, RET, RSE, C4, FURB, FLY, N, A, ISC, T20, LOG, ERA, PGH, PT, TCH, PL, RUF, ARG, FBT, EM, INP, ANN, D, FAST, NPY, PYI, PTH, TD, FIX, G, TRY, BLE.
- **ruff format** — Black-compatible, line-length 120.
- **interrogate** — docstring coverage.
- **pip-audit** — vulnerabilidades de dependencias.
- **jscpd** — detección de duplicación cross-file.
- `pydocstyle` Google convention.
- Complejidad McCabe max 15.

### 4.4 Frontend — tooling
- **ESLint 9** flat config (`eslint.config.mjs`) con ~60+ reglas.
- Plugins: `@typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-boundaries`, `eslint-plugin-check-file`, `eslint-plugin-import`, `eslint-plugin-jsdoc`, `eslint-plugin-jsx-a11y`, `eslint-plugin-prettier`, `eslint-plugin-react-perf`, `eslint-plugin-sonarjs`, `eslint-plugin-storybook`, `eslint-config-next`, `eslint-config-prettier`.
- **TypeScript** strict, 0 errors.
- **knip 6.4** — dead code.
- **madge 8** — detección de ciclos de import.
- **jscpd 4** — duplicación (baseline 4.52%).
- **npm audit** `--audit-level=high`.
- Límites: max-lines 350, max-lines-per-function 100, cognitive-complexity 15, max-params 4.

### 4.5 Skills y agentes internos (automatización IDE)
- Skills custom en `.claude/skills/`: `backend-expert`, `frontend-expert`, `sales-agent-expert`, `metrics-expert`, `manychat-expert`, `data-storyteller`, `content-hunter`, `brand-offer-auditor`, `git-manager`, `ux-disruptivo`, `ux-flow-architect`, `pase-produccion`, `cierra-limpio`, `dev-up`, `estado`, `migrate`, `review-pr`, entre otros.
- Sub-agentes especializados: `nicolify-architect`, `nicolify-backend`, `nicolify-frontend`, `nicolify-agentic`, `nicolify-backend-auditor`, `nicolify-ux-designer`.

### 4.6 MCP servers disponibles
- GitHub MCP, Shopify Dev MCP, Clerk MCP, Google Drive MCP, Tessl MCP, Google Dev Knowledge MCP.

---

## 5. Testing

### 5.1 Backend — Python
- **pytest** con `asyncio_mode=auto`.
- **pytest-randomly** — detección de dependencias de orden ocultas (`--randomly-seed=last`).
- **pytest-timeout 30s** — protege contra tests async colgados.
- **pytest-cov** — coverage (fail_under 43%, source `src/modules` + `src/shared`).
- **factory-boy** + **faker** — fixtures.
- **Markers**: `integration` (APIs reales), `verify` (verificación de datos reales, excluido por default).
- **Arch fitness tests** (10 gates en `tests/architecture/`): DDD boundaries, API contracts, conventions, currency consistency, extraction contract, master data, meta provider invariants, folder naming, domain purity.

### 5.2 Frontend — Vitest
- **Vitest 4.1** + **@vitest/coverage-v8** — unit + integration.
- **happy-dom 20** / **jsdom 27** — DOM runtime.
- **@testing-library/react 16**, **@testing-library/dom**, **@testing-library/jest-dom** — assertions.
- **1063 tests**, threshold 20% (real: 25/21/22/25 stmts/branches/funcs/lines).
- **Arch fitness tests** (8 gates en `src/__tests__/architecture/`): component naming, file naming, folder naming, hook location, no default exports, no duplicate names, feature structure, api location.

### 5.3 End-to-End
- **Playwright 1.59** (`@playwright/test`).
- **@clerk/testing 2.0** (`clerkSetup()` + `setupClerkTestingToken`) para bypass de bot detection.
- **Proyectos**: `setup`, `smoke`, `regression`, `public`, `visual`, `perf`, `verify`.
- **Ejecución nativa en WSL** (`npx playwright test`). Prohibido correr Docker E2E localmente.
- **Preflight script** (`scripts/e2e-preflight.sh`): verifica containers, módulos, auth, env vars antes de cada run.
- POMs en `frontend/e2e/pages/`, fixtures en `frontend/e2e/fixtures/`.
- Locators: `getByRole`, `getByText`, `getByLabel` (nunca CSS selectors).

### 5.4 Verificación de datos (Data Reliability — 4 layers)
- **Layer 0 — ETL execution**: `make verify-etl provider={name}`.
- **Layer 1 — Source probe**: `make verify-probe-{provider}` (API externa vs DB).
- **Layer 2 — Pipeline integrity**: `pytest -m verify` (`tests/verification/`).
- **Layer 3 — UI fidelity**: Playwright `--project=verify` (`frontend/e2e/specs/verify/`).

### 5.5 Quality gates y comandos unificados
- `/test-backend`, `/test-frontend`, `/test-all`, `/estado`, `/cierra-limpio`, `/dev-up`, `/migrate`, `/review-pr`.
- `make arch-test`, `make extraction-contract`, `make audit`.

---

## 6. Deployment

### 6.1 Runtime y empaquetado
- **Docker** multi-stage Dockerfiles (stages: `dev`, `lint`, `test`, `e2e`, `final`, `runner`).
- **Docker Compose** — `docker-compose.yml` (dev) + `docker-compose.prod.yml` (prod).
- **BuildKit** + **docker buildx** con cache GitHub Actions (`type=gha`).
- Profiles: `core`, `extended`, `etl`, `tooling`, `e2e`, `admin`.
- **Cloudflare Tunnel** (`cloudflared`) para exponer `dev-app.nicolify.com` desde local.

### 6.2 Runtime services (containers)
- `visionarias_brain_dev` — FastAPI (uvicorn `--reload`).
- `visionarias_client_dev` — Next.js dev server.
- `visionarias_admin_dev` — Streamlit admin.
- `visionarias_postgres` — PostgreSQL 15-alpine.
- `visionarias_redis` — Redis 7-alpine (appendonly).
- `visionarias_qdrant` — Qdrant v1.7.3.
- `visionarias_scheduler` + `visionarias_worker` — arq workers.
- `cloudflare-tunnel` — Cloudflare tunnel.

### 6.3 Environments
- **Local** — `.env`, `docker compose up`, hostnames `salesagent.local` (Traefik local).
- **Dev tunnel** — `dev-app.nicolify.com` (Cloudflare tunnel a local).
- **Producción** — `app.nicolify.com` + `api.nicolify.com` (VPS Hetzner/similar).

### 6.4 CI/CD — GitHub Actions (`deploy-prod.yml`)
- Trigger: `push` a `main` (con `paths-ignore: .github/workflows/**`).
- **Jobs**:
  1. `quality-gates` — docker build targets `lint` y `test`, ejecuta ruff + pytest + vitest + tsc + eslint + pip-audit + npm audit.
  2. `security-scan` — **Trivy 0.35** (OS + library, HIGH+CRITICAL, `ignore-unfixed`).
  3. `build` — push a **GitHub Container Registry** (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest|{sha}`).
  4. `deploy` — `appleboy/scp-action` + `appleboy/ssh-action` al VPS, pull + `docker compose up -d` + `alembic upgrade head`.
  5. `healthcheck` — `curl` a `/health/ready` y `/sign-in` (12 retries, 15s interval).
  6. `deploy-worker` — `npx wrangler deploy` del Cloudflare Worker (`sentry-slack-alerts`).
  7. `notify-failure` — **Slack webhook** (`slackapi/slack-github-action@v2`).
- **Codecov** — subida de coverage (backend xml + frontend json).

### 6.5 E2E workflow separado
- `e2e-tests.yml` — corre Playwright E2E en GitHub Actions (no local, evita crash de laptop).

### 6.6 Cloudflare Workers
- `workers/sentry-slack-alerts/` — Worker que reenvía alerts de Sentry a Slack.
- **Wrangler CLI** para deploy.

### 6.7 Migrations
- **Alembic** aplicado post-deploy (`docker exec visionarias_brain alembic upgrade head`).
- Idempotentes: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS` (raw SQL).
- Test de migración contra DB clonada antes de prod.

### 6.8 Release notes
- Skill `git-manager` genera changelogs duales (técnico + de negocio) al hacer release.

---

## 7. Operations / DevOps

### 7.1 Orquestación local
- **Makefile** como interfaz unificada: `make dev-core`, `make prod`, `make stop`, `make logs`, `make tooling-up`, `make verify-meta`, `make arch-test`, `make extraction-contract`.
- **Traefik** como reverse proxy local (routers + labels en compose).
- Secure bindings: servicios internos expuestos solo en `127.0.0.1`.

### 7.2 Infraestructura de producción
- **VPS** (SSH via GitHub Actions, directorio `VPS_APP_PATH`).
- **Traefik** en prod como gateway + TLS (network externa `gateway`).
- **Cloudflare** — DNS + tunnel + Workers.
- **GitHub Container Registry (GHCR)** — imágenes Docker versionadas.
- **PostgreSQL 15** + **Redis 7** + **Qdrant v1.7.3** como datastores gestionados por Compose.

### 7.3 Observabilidad
- **Sentry** (`@sentry/nextjs 10.47` + `sentry-sdk` Python ≥1.40) — error tracking + releases atadas a `DEPLOY_SHA`.
- Org: `alpaca-purpura-to`, proyectos: `nicolify-frontend`, `nicolify-backend`.
- **structlog** — logging estructurado con contexto (tenant, provider, sub_extractor).
- **Slack webhook** — alertas de deploy failure + Sentry alerts via Worker.
- Healthchecks Docker (liveness) + endpoints `/health/ready` (readiness).
- **Codecov** — tendencias de cobertura.

### 7.4 Secrets management
- `.env` (local) + `.env.prod` (VPS, copiado vía SSH).
- GitHub Actions secrets: `VPS_HOST`, `VPS_SSH_KEY`, `VPS_PORT`, `VPS_APP_PATH`, `GHCR_TOKEN`, `CODECOV_TOKEN`, `CLOUDFLARE_API_TOKEN`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `SLACK_DEPLOY_WEBHOOK_URL`, `SENTRY_AUTH_TOKEN`, etc.
- Nunca commitear `.env*`, credentials, tokens.

### 7.5 Runbooks y documentación operacional
- `docs/runbooks/` — procedimientos de operación.
- `docs/guides/` — guías de dev/ops.
- `docs/etl/extraction-contract.md` — doc auto-generado del ETL.
- `docs/references/` — references técnicas (e2e fixes plan, channel dashboard playbook).
- `docs/mejoras-proceso/to-do.md` — mejoras continuas detectadas en runtime.

### 7.6 Seguridad
- **Clerk** — auth + session management + bot protection.
- **Trivy** — scan de vulnerabilidades en imágenes (HIGH + CRITICAL).
- **pip-audit** + **npm audit** — dependencias.
- **Bandit** via Ruff `S` rules (70+ checks).
- Tenant isolation estricta.
- PII sanitisation (regla Tessl `pii-sanitisation.md`) — allowlist vía `response_model=`.
- JWT signing + bcrypt hashing + cryptography suite.
- Svix para verificación de webhooks inbound.

### 7.7 Deploy pipeline — flujos
- **Dev pipeline**: push a `development` → nada automático (local dev only).
- **Prod pipeline**: merge a `main` → quality-gates → security-scan → build → deploy → healthcheck → slack-notify-on-failure.
- **Rollback**: re-push imagen anterior por SHA a `:latest` o `docker compose pull` explícito.

### 7.8 Reglas de proceso críticas
- Nunca force-push a `main`.
- Nunca `docker exec` para lint/tests/type-checks (volumes apuntan al clon principal, no a worktrees).
- Push a `origin main` = deploy a producción (requiere aprobación explícita).
- Stagear archivos por nombre (`git add path`), nunca `git add .`/`-A`/`-u` (sesiones paralelas).
- Al iniciar/cerrar conversación: chequeo de estado + garantía de working tree limpio.
- TDD obligatorio, regression test antes del fix.
- Después de cualquier cambio a ETL: `make extraction-contract && pytest tests/architecture/test_extraction_contract.py`.
