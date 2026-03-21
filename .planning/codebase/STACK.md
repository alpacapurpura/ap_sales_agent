# Technology Stack

**Analysis Date:** 2026-03-20

## Languages

**Primary:**
- Python 3.11+ — Backend API, AI agents, ETL workers, admin dashboard
- TypeScript 5.9+ — Frontend application (strict mode enabled)

**Secondary:**
- SQL (raw) — Alembic migrations (idempotent pattern with `IF NOT EXISTS`)
- Jinja2 — LLM prompt templates (`backend/src/modules/sales_agent/infrastructure/prompts/templates/`)

## Runtime

**Backend:**
- Python 3.11-slim (Docker image `python:3.11-slim`)
- Container: `visionarias_brain_dev`

**Frontend:**
- Node.js 22-alpine (Docker image `node:22-alpine`)
- Container: `visionarias_client_dev`

**Package Managers:**
- Backend: `pip` with `requirements-runtime.txt` + `requirements-dev.txt`
- Frontend: `npm` — lockfile `frontend/package-lock.json` present

## Frameworks

**Backend Core:**
- FastAPI `0.135.1` — Async HTTP API (ASGI via Uvicorn)
- Uvicorn `0.34.0` — ASGI server (dev: `--reload`; prod: Gunicorn workers)
- Pydantic v2 `>=2.10.0` — Schema validation and settings
- pydantic-settings `>=2.10.1` — Environment config via `BaseSettings` at `backend/src/core/config.py`

**AI / Agent Orchestration:**
- LangChain `1.2.12` — LLM abstraction layer
- LangGraph `1.1.2` — Stateful agent graph execution (sales agent, copilot agents)
- langchain-openai `1.1.11` — OpenAI provider
- langchain-google-genai `4.2.1` — Gemini provider
- langchain-community `0.4.1` — Community integrations
- langchain-text-splitters `1.1.1` — Document chunking for RAG

**Frontend Core:**
- Next.js `15.5.13` — App Router, React Server Components, standalone output
- React `19.2.3` — UI runtime
- Tailwind CSS `4.1.18` — Utility-first styling
- Shadcn UI (Radix Primitives) — Component system via `frontend/components.json`

**Admin Dashboard:**
- Streamlit `>=1.31.0` — Internal admin UI at port 8501/8502 (`backend/src/admin/app.py`)

**Testing:**
- Backend: `pytest >=8.0.0` + `pytest-asyncio >=0.23.5`
- Frontend: Vitest `4.0.17` + `@testing-library/react 16.3.1`, environment: `happy-dom`
- Frontend E2E: Not configured

**Build/Dev:**
- Backend linting: `ruff >=0.3.0` (Black-compatible, line-length 88, target `py311`)
- Frontend linting: ESLint `8.57.1` + `eslint-config-next 15.5.13`
- Frontend pre-commit: Husky `9.1.7` + lint-staged (ESLint fix + `tsc --noEmit`)
- Frontend component explorer: Storybook `10.2.19` (port 6006)
- Container orchestration: Docker Compose (dev/prod profiles)
- Reverse proxy: Traefik (external network `gateway`)
- Tunnel: Cloudflare Tunnel for external webhook access

## Key Dependencies

**State & Data:**
- SQLAlchemy `2.0.27` — ORM (sync sessions via `SessionLocal`)
- Alembic `>=1.13.1` — DB migrations
- psycopg2-binary `2.9.9` — PostgreSQL driver
- Redis `5.0.1` — Cache + ARQ job queue
- Qdrant client `>=1.13.3` — Vector store client
- fastembed `>=0.2.0` — Local sparse embeddings (BM25)
- flashrank `>=0.2.0` — Local reranker for RAG pipeline

**Background Jobs:**
- arq `0.27.0` — Async job queue over Redis. Worker: `WorkerSettings`, Scheduler: `SchedulerSettings` at `backend/src/modules/analytics/workers/settings.py`

**HTTP:**
- httpx `>=0.26.0` — Async HTTP client (external API calls)
- requests `>=2.32.5` — Sync HTTP (legacy/scripts)

**File Processing:**
- pypdf `>=4.0.0` — PDF text extraction
- python-docx `>=0.8.11` — DOCX parsing
- beautifulsoup4 `>=4.12.3` — HTML scraping (brand extraction)
- Pillow `>=12.1.1` — Image processing
- python-multipart `>=0.0.9` — File upload handling

**Auth & Security:**
- PyJWT `>=2.12.0` — Clerk JWKS JWT verification at `backend/src/modules/iam/application/auth.py`
- cryptography `>=46.0.5` — Crypto primitives
- passlib[bcrypt] `>=1.7.4` — Password hashing (legacy)
- svix `>=1.1.1` — Clerk webhook signature verification at `backend/src/modules/iam/api/webhooks.py`

**Observability:**
- structlog `>=24.1.0` — Structured logging (all backend modules use `structlog.get_logger()`)
- sentry-sdk `>=1.40.0` — Error tracking (ARQ workers + app)

**Storage:**
- boto3 `>=1.34.0` — Cloudflare R2 via S3-compatible API at `backend/src/modules/assets/infrastructure/storage/r2.py`

**Frontend State & Forms:**
- TanStack Query `5.90.19` — Server state, caching, and async data fetching
- React Hook Form `7.71.1` — Form management
- Zod `4.3.6` — Schema validation (client-side)
- framer-motion `12.35.0` — Animations

**Frontend Visualization:**
- visx (gradient, group, responsive, sankey, shape, tooltip) `3.12.0` — Data visualization (funnel/Sankey diagrams for Growth Studio)

**Frontend UI Tools:**
- @puckeditor/core `0.21.1` — Drag-and-drop landing page editor
- date-fns `4.1.0` + date-fns-tz `3.2.0` — Date utilities
- sonner `2.0.7` — Toast notifications
- lucide-react `0.562.0` — Icon library
- colorthief `2.6.0` — Brand color extraction from images
- cmdk `1.1.1` — Command palette (cmdk)
- next-themes `0.4.6` — Dark/light theme support

## Configuration

**Backend Environment:**
- Loaded via `pydantic-settings` from `.env` file at `backend/src/core/config.py`
- Required vars: `OPENAI_API_KEY`, `REDIS_URL`, `QDRANT_URL`, `POSTGRES_*`, `WHATSAPP_*`, `API_SECRET_KEY`
- Optional vars: `GEMINI_API_KEY`, `SENTRY_DSN`, `SHOPIFY_*`, `META_*`, `TELEGRAM_BOT_TOKEN`, `GOOGLE_*`, `CLERK_*`, `CLOUDFLARE_*`
- AI provider switchable: `AI_PROVIDER=openai|gemini` (default: `openai`)
- Storage provider switchable: `STORAGE_PROVIDER=LOCAL|R2` (default: `LOCAL`)

**Frontend Environment:**
- `NEXT_PUBLIC_API_URL` — Public API base URL
- `NEXT_PUBLIC_APP_URL` — Public app base URL
- `INTERNAL_API_URL` — Docker-internal API URL for server-side fetching
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk auth (build-time arg)
- `SHOPIFY_API_KEY` — Shopify OAuth

**Build:**
- Backend: Multi-stage Dockerfile (`builder` → `dev` → `test` → `final`) at `backend/Dockerfile`
- Frontend: Multi-stage Dockerfile (`deps` → `dev` → `test` → `build` → `runner`) at `frontend/Dockerfile`
- Frontend output: `standalone` mode for minimal production image

## Platform Requirements

**Development:**
- Docker Compose (mandatory — Docker-first philosophy)
- `.env` file from `.env.example`
- WSL2 compatible (polling enabled: `CHOKIDAR_USEPOLLING=true`, `WATCHPACK_POLLING=true`)

**Production:**
- `docker-compose.prod.yml` with `--env-file .env.prod`
- Traefik external network (`TRAEFIK_NETWORK`)
- Optional profiles: `extended` (admin, scheduler, worker, tunnel), `tooling`

## Deviations from Reference Standards

**Backend (vs `.trae/skills/backend-expert/references/standards.md`):**
- **DEVIATION**: Database uses **synchronous** SQLAlchemy sessions (`SessionLocal`, `create_engine`) instead of the prescribed async SQLAlchemy (`AsyncSession`, `create_async_engine`). The standard requires all I/O to be `async`. This is pervasive across all modules.
- **DEVIATION**: Some modules still use `logging` instead of `structlog` (e.g., `backend/src/modules/connections/infrastructure/channels/google_calendar.py`, IAM auth).
- **CONFORMANT**: `ruff` for linting, `pydantic-settings` for config, `structlog` in most modules, `HTTPException` for API errors.

**Database (vs `.trae/skills/backend-expert/references/database.md`):**
- **DEVIATION**: Standard prescribes async repositories with `AsyncSession`. Actual implementation uses sync `Session` from `SessionLocal` dependency injection.
- **CONFORMANT**: Module-prefixed table naming (e.g., `iam_users`), repository pattern, cross-module FK isolation (IDs only), Alembic migrations.
- **ENHANCEMENT**: CLAUDE.md overrides Alembic standard — requires raw SQL with `IF NOT EXISTS` for idempotency (not covered in `.trae` reference).

**Frontend (vs `.trae/skills/frontend-expert/references/tech-stack.md`):**
- **DEVIATION**: Actual stack uses Next.js **15**, React **19**, Tailwind CSS **v4** — reference specifies Next.js 14+, React 18+, Tailwind CSS v3.4+. The codebase is ahead of the documented standard.
- **DEVIATION**: Reference lists "Axios" as HTTP option. Actual codebase uses native `fetch` wrapped in `fetchClient` at `frontend/src/lib/http-client.ts` (no Axios).
- **CONFORMANT**: TanStack Query for server state, Zod for validation, Clerk for auth, ESLint.
- **ADDITION**: Vitest (not in reference), Storybook (not in reference), Husky/lint-staged, framer-motion, visx for charts.

---

*Stack analysis: 2026-03-20*
