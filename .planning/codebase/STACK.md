# Technology Stack

**Analysis Date:** 2026-03-15

## Languages

**Primary:**
- Python 3.11 - Backend API, domain logic, AI orchestration (`backend/src/`)
- TypeScript 5.9 - Frontend application (`frontend/src/`)

**Secondary:**
- Python 3.11 - Admin dashboard (Streamlit) (`backend/src/admin/`)

## Runtime

**Backend Environment:**
- Python 3.11-slim (Docker)
- WSGI/ASGI: Uvicorn (dev), Gunicorn + UvicornWorker (prod, 4 workers)

**Frontend Environment:**
- Node.js (Docker, version not pinned — derived from Next.js image)
- Next.js standalone output mode (`output: 'standalone'` in `frontend/next.config.js`)

**Package Manager:**
- Backend: pip with `requirements.txt` (no lockfile)
- Frontend: npm with `package-lock.json` (lockfile present)

## Frameworks

**Core Backend:**
- FastAPI 0.109.2 - REST API framework (`backend/src/main.py`)
- Pydantic v2 (>=2.10.0) - Data validation and settings management
- pydantic-settings 2.1.0 - Environment-based configuration (`backend/src/core/config.py`)
- SQLAlchemy 2.0.27 - ORM (sync engine, `backend/src/core/database.py`)
- Alembic >=1.13.1 - Database migrations (`backend/alembic/`)

**AI / LLM:**
- LangChain >=0.1.9 + langchain-openai >=0.0.8 + langchain-core >=0.1.26 - LLM orchestration
- LangGraph 0.0.24 - Stateful agent graph execution (`backend/src/modules/sales_agent/application/`)
- langchain-google-genai 0.0.9 - Gemini provider support
- fastembed >=0.2.0 - Local sparse embedding model (BM25/SPLADE)
- flashrank >=0.2.0 - Local cross-encoder reranker (ms-marco-MiniLM-L-12-v2)

**Core Frontend:**
- Next.js ^14.2.35 - App Router, server actions, standalone output (`frontend/`)
- React ^19.2.3 - UI rendering
- Tailwind CSS ^4.1.18 - Utility-first CSS
- Shadcn UI - Component system built on Radix UI primitives

**UI Components:**
- Radix UI - Headless component primitives (accordion, dialog, dropdown, etc.)
- Framer Motion ^12.35.0 - Animations
- Lucide React ^0.562.0 - Icon library
- Sonner ^2.0.7 - Toast notifications
- cmdk ^1.1.1 - Command palette
- @puckeditor/core ^0.21.1 - Rich text / page editor

**Data Fetching:**
- @tanstack/react-query ^5.90.19 - Server state management (`frontend/src/app/providers.tsx`)
- Native `fetch` with custom wrapper `fetchClient` (`frontend/src/lib/http-client.ts`) — injects `X-Tenant-ID` header automatically

**Form Handling:**
- react-hook-form ^7.71.1 + @hookform/resolvers ^5.2.2 + zod ^4.3.6 - Forms with schema validation

**Data Visualization:**
- @visx/sankey, @visx/shape, @visx/group, @visx/tooltip, @visx/gradient, @visx/responsive ^3.12.0 - Funnel / Sankey diagrams (Growth Studio)

**Admin Dashboard:**
- Streamlit >=1.31.0 - Internal admin UI (`backend/src/admin/app.py`)

**Testing:**
- Frontend: Vitest ^4.0.17 + @testing-library/react ^16.3.1 + happy-dom
- Backend: pytest >=8.0.0 + pytest-asyncio >=0.23.5

**Build/Dev:**
- ESLint 8 + eslint-config-next - Frontend linting
- Husky ^9.1.7 + lint-staged ^16.2.7 - Pre-commit hooks
- Ruff >=0.3.0 - Python linting + formatting (`backend/pyproject.toml`, line-length 88, py311 target)
- Docker + Docker Compose - All dev and prod environments

## Key Dependencies

**Critical Backend:**
- `langchain` / `langchain-openai` / `langgraph` - Powers the Sales Agent AI orchestrator
- `qdrant-client 1.7.3` - Vector DB client for RAG/semantic memory
- `redis 5.0.1` - Session cache, rate limiting, event buffers
- `sqlalchemy 2.0.27` + `psycopg2-binary 2.9.9` - PostgreSQL ORM
- `svix >=1.1.1` - Clerk webhook signature verification (`backend/src/modules/iam/api/webhooks.py`)
- `pyjwt 2.8.0` + `cryptography 42.0.5` - JWT verification and Fernet symmetric encryption
- `passlib[bcrypt] >=1.7.4` - Password hashing
- `facebook-business` - Meta/Facebook Ads SDK
- `boto3 >=1.34.0` - AWS S3 / Cloudflare R2 compatible storage
- `google-api-python-client >=2.118.0` + `google-auth-oauthlib >=1.2.0` - Google APIs (Calendar, Analytics, Gmail, YouTube)
- `beautifulsoup4 >=4.12.3` - Web scraping for Brand extraction
- `structlog >=24.1.0` - Structured logging throughout backend

**Critical Frontend:**
- `@clerk/nextjs ^6.36.8` - Auth provider (middleware, hooks, components)
- `@tanstack/react-query ^5.90.19` - All API data fetching
- `zod ^4.3.6` - Schema validation for forms and API contracts
- `@visx/sankey` - Bowtie funnel visualization (Growth Studio)

**Infrastructure:**
- `gunicorn 21.2.0` - Production WSGI server (wraps uvicorn workers)
- `python-multipart >=0.0.9` - File upload support in FastAPI

## Configuration

**Backend Environment:**
- Single `.env` file for dev, `.env.prod` for prod
- Loaded via `pydantic-settings` in `backend/src/core/config.py`
- Key required vars: `OPENAI_API_KEY`, `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `REDIS_URL`, `QDRANT_URL`, `API_SECRET_KEY`, `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`, `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- Optional/feature-gated: `GEMINI_API_KEY`, `SHOPIFY_*`, `META_*`, `TELEGRAM_BOT_TOKEN`, `GOOGLE_*`, `CLOUDFLARE_*` (R2 storage), `EVOLUTION_API_*`

**Frontend Environment:**
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` - Required at build time (baked into Docker image)
- `NEXT_PUBLIC_API_URL` - Public API URL for client-side requests
- `NEXT_PUBLIC_APP_URL` - Application URL
- `INTERNAL_API_URL` - Docker-internal API URL for SSR (avoids external hop)
- `SHOPIFY_API_KEY` - Public Shopify key (exposed to client)

**API Routing:**
- Frontend proxies all `/api/v1/*` and `/api/webhooks/*` to backend via Next.js rewrites (`frontend/next.config.js`)
- Server-side requests use `INTERNAL_API_URL` (Docker internal), client-side use `NEXT_PUBLIC_API_URL`

**Build:**
- Backend: Multi-stage Docker build (builder → runtime), non-root user, BuildKit cache mounts (`backend/Dockerfile`)
- Frontend: Multi-stage Docker build with `dev` and standalone prod targets (`frontend/Dockerfile`)
- CI/CD images: Published to `ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`

**TypeScript Paths:**
- `@/*` → `./src/*` (configured in `frontend/tsconfig.json` and `frontend/vitest.config.mts`)

## Platform Requirements

**Development:**
- Docker + Docker Compose
- `.env` file with all required variables
- Run via `make dev` or `docker compose up -d`
- Hot reload enabled: `CHOKIDAR_USEPOLLING=true`, `WATCHPACK_POLLING=true` (WSL2 compatibility)

**Production:**
- Docker Compose with `docker-compose.prod.yml` + `.env.prod`
- Traefik reverse proxy (external network required: `${TRAEFIK_NETWORK}`)
- Let's Encrypt TLS via Traefik cert resolver
- Cloudflare Tunnel for secure ingress (`cloudflare/cloudflared:latest`)
- Gunicorn with 4 UvicornWorker processes for backend
- Evolution API (WhatsApp engine): `atendai/evolution-api:v1.8.2`

---

*Stack analysis: 2026-03-15*
