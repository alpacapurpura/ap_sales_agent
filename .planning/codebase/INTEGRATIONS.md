# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

### AI / LLM Providers

**OpenAI (Primary):**
- Used for: Chat completions, structured output, embeddings
- SDK: `langchain-openai` + direct `openai` client
- Auth: `OPENAI_API_KEY` (env)
- Models: `OPENAI_MODEL` (default: `gpt-4o-mini`), `OPENAI_FAST_MODEL` (default: `gpt-4o-mini`), `OPENAI_EMBEDDING_MODEL` (default: `text-embedding-3-large`)
- Tenant override: Tenants can supply their own key via `tenant.openai_api_key`
- Factory: `backend/src/shared/infrastructure/llm/factory.py`

**Google Gemini (Secondary):**
- Used for: Alternative LLM provider (switchable via `AI_PROVIDER=gemini`)
- SDK: `langchain-google-genai`
- Auth: `GEMINI_API_KEY` (env)
- Model: `GEMINI_MODEL` (default: `gemini-pro`)
- Provider: `backend/src/shared/infrastructure/llm/providers/gemini.py`

### Messaging Channels

**WhatsApp — Evolution API (Self-Hosted QR):**
- Used for: Sales agent conversations via QR-based WhatsApp (non-Cloud)
- Protocol: REST API to self-hosted Evolution API instance
- Auth: `EVOLUTION_API_KEY` (env), per-tenant credentials in `ChannelConnection.credentials`
- Config: `EVOLUTION_API_URL` (env), `EVOLUTION_API_VERSION` (`v1` or `v2`)
- Abstraction: Strategy pattern — `WhatsAppProvider` interface at `backend/src/modules/connections/infrastructure/channels/whatsapp/interface.py`
- Implementations: `backend/src/modules/connections/infrastructure/channels/whatsapp/v1.py`, `v2.py`
- Factory: `backend/src/modules/connections/infrastructure/channels/whatsapp/factory.py`
- Note: Evolution API container is commented out in `docker-compose.yml` (external deployment)

**WhatsApp Cloud API (Meta):**
- Used for: Official Meta Cloud API WhatsApp messaging
- Auth: `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` (env)
- Webhook: `GET /api/v1/connections/whatsapp` (verify) + `POST` (events)
- Implementation: `backend/src/modules/connections/infrastructure/channels/whatsapp/base.py`

**Telegram:**
- Used for: Telegram bot integration for AI agent conversations
- SDK: HTTP calls to Telegram Bot API
- Auth: `TELEGRAM_BOT_TOKEN` (env)
- Router: `backend/src/modules/connections/api/telegram.py`
- Service: `backend/src/modules/connections/infrastructure/channels/telegram_service.py`

### Meta (Facebook / Instagram)

**Meta Business Platform:**
- Used for: Ads management, Instagram integration, Facebook page connections, Pixel tracking, WABA
- SDK: `facebook-business >=22.0,<26.0`
- Auth: `META_APP_ID`, `META_APP_SECRET`, `META_VERIFY_TOKEN`, `META_REDIRECT_URI`, `META_CONFIG_ID` (env)
- OAuth: Facebook Login for Business flow (system user or user-level token)
- Adapter: `backend/src/modules/connections/infrastructure/channels/meta.py`
- Analytics provider: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`
- Channel types: `META`, `FACEBOOK_PAGE`, `INSTAGRAM_ACCOUNT`, `META_ADS_ACCOUNT`, `META_PIXEL`, `WHATSAPP_BUSINESS_ACCOUNT`

### Google Workspace

**Google Calendar:**
- Used for: Scheduling integration, availability sync, calendar event creation
- SDK: `google-api-python-client`, `google-auth-oauthlib`
- Auth: OAuth2 via `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` (env)
- Scopes: `https://www.googleapis.com/auth/calendar`, `calendar.events`
- Adapter: `backend/src/modules/connections/infrastructure/channels/google_calendar.py`

**Gmail:**
- Used for: Email integration for sales agent inbox
- SDK: `google-api-python-client`
- Auth: OAuth2 (shared Google credentials)
- Router: `backend/src/modules/connections/api/gmail.py`
- Implementation: `backend/src/modules/connections/infrastructure/channels/gmail.py`

**Google Analytics (GA4):**
- Used for: Website traffic analytics for Growth Studio
- SDK: `google-analytics-data >=0.20.0`
- Auth: OAuth2 (shared Google credentials)
- Implementation: `backend/src/modules/connections/infrastructure/channels/google_analytics.py`

**YouTube / YouTube Analytics:**
- Used for: YouTube channel metrics and analytics data
- SDK: `google-api-python-client`
- Auth: OAuth2 (shared Google credentials)
- Implementations: `backend/src/modules/connections/infrastructure/channels/youtube.py`, `youtube_analytics.py`

**Google Workspace (general):**
- Used for: Google Workspace account connections
- Router: `backend/src/modules/connections/api/google_workspace.py`

### E-Commerce

**Shopify:**
- Used for: E-commerce store integration — customer/order sync, analytics
- Auth: OAuth2 (`SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_APP_URL`)
- API version: `2026-01`
- Scopes: Read/write customers, orders, analytics, products, and 40+ additional scopes
- Connector: `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py`
- HMAC webhook verification
- Compliance endpoints: `backend/src/modules/connections/api/shopify_compliance.py` (GDPR data erasure)

### Marketing Automation

**MailerLite:**
- Used for: Email marketing campaign data sync and subscriber management
- SDK: Direct HTTP via `httpx` to `https://connect.mailerlite.com/api`
- Auth: Per-tenant API key (stored in `ChannelConnection.credentials`)
- ETL: Cron sync every 6 hours via ARQ worker (`run_mailerlite_etl_sync`)
- Connector: `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py`

**ManyChat:**
- Used for: ManyChat subscriber data ingestion and webhook events
- SDK: HTTP connector
- Router: `backend/src/modules/connections/api/manychat.py`
- Connector: `backend/src/modules/connections/infrastructure/marketing_connectors/manychat.py`

## Data Storage

### Databases

**PostgreSQL 15 (Primary):**
- Role: Main relational database (all domain data)
- Image: `postgres:15-alpine` (container: `visionarias_postgres`)
- Connection: `postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}`
- Env vars: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`
- ORM: SQLAlchemy 2.0.27 (sync sessions — `SessionLocal` at `backend/src/core/database.py`)
- Migrations: Alembic at `backend/alembic/versions/`
- Note: Sessions are **synchronous** (`create_engine`, not `create_async_engine`) — deviation from async standard

**Qdrant v1.7.3 (Vector Store):**
- Role: RAG knowledge base, semantic search for sales agent, semantic routing
- Image: `qdrant/qdrant:v1.7.3` (container: `visionarias_qdrant`)
- Connection: `QDRANT_URL` (default: `http://qdrant:6333`), `QDRANT_API_KEY`
- Collections: `visionarias_knowledge` (dense), `visionarias_hybrid` (sparse+dense)
- Embedding model: `text-embedding-3-large` (3072 dimensions)
- Sparse model: `Qdrant/bm25` (via fastembed)
- Client: `qdrant-client >=1.13.3`
- Usage files: `backend/src/modules/sales_agent/infrastructure/memory/vector_store.py`

**Redis 7 (Cache + Job Queue):**
- Role: Session cache, ARQ job queue, ephemeral state
- Image: `redis:7-alpine` (container: `visionarias_redis`)
- Connection: `REDIS_URL` (default: `redis://redis:6379/0`)
- Persistence: AOF enabled (`appendonly yes`)
- Client: `redis 5.0.1` + `arq` for job queue
- Usage: `backend/src/core/database.py` (redis_client), ARQ workers

### File Storage

**Local Filesystem (default):**
- Path: `backend/static/` (mounted volume)
- Config: `STORAGE_PROVIDER=LOCAL`, `UPLOAD_DIR=static/uploads`
- Served: FastAPI `StaticFiles` at `/static`

**Cloudflare R2 (production option):**
- Config: `STORAGE_PROVIDER=R2`
- Env vars: `CLOUDFLARE_ACCOUNT_ID`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL`
- SDK: `boto3` via S3-compatible API
- Implementation: `backend/src/modules/assets/infrastructure/storage/r2.py`
- Strategy pattern: `StorageStrategy` base class with `LocalStorageStrategy` and `R2StorageStrategy`

### Caching

**Redis** (see Data Storage above)

## Authentication & Identity

**Clerk (Primary Auth Provider):**
- Role: User authentication, session management, organization/tenant metadata
- Frontend: `@clerk/nextjs ^6.36.8` — Middleware at `frontend/src/middleware.ts`
- Frontend protection: `clerkMiddleware` + `createRouteMatcher` for public routes
- Backend JWT verification: JWKS-based at `backend/src/modules/iam/application/auth.py`
  - Fetches signing keys from `{CLERK_ISSUER}/.well-known/jwks.json`
  - Algorithm: RS256, leeway: 60s
- Backend webhook sync: Svix signature verification at `backend/src/modules/iam/api/webhooks.py`
  - Events: `user.created`, `user.updated` → sync to local `iam_users` table
- Env vars: `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`, `CLERK_ISSUER`
- Tenant ID flow: Stored in Clerk `publicMetadata.tenant_id` → localStorage (`x-tenant-id`) → `X-Tenant-ID` header
- Multitenant enforcement: `backend/src/modules/iam/api/dependencies.py` `get_tenant_context`

## Monitoring & Observability

**Sentry:**
- Role: Error tracking and performance monitoring
- SDK: `sentry-sdk >=1.40.0`
- Configured in: ARQ `WorkerSettings.on_startup()` and `SchedulerSettings.on_startup()` at `backend/src/modules/analytics/workers/settings.py`
- Config: `SENTRY_DSN` (env), `ENVIRONMENT` (env)
- Sample rate: `traces_sample_rate=0.1`
- Note: FastAPI app itself does not explicitly call `sentry_sdk.init()` (only ARQ workers do)

**Structlog (Logging):**
- Role: Structured JSON logging
- Config: `backend/src/core/logger.py`
- Pattern: `logger = structlog.get_logger()` in all backend modules
- Request tracing: Request ID bound per request via `structlog.contextvars`
- Audit tracing: LangGraph node execution traced at `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py`

## CI/CD & Deployment

**Hosting:**
- Docker Compose on self-managed VPS/server
- Dev: `docker compose up -d` (`.env` + `docker-compose.yml`)
- Prod: `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d`

**Reverse Proxy:**
- Traefik (external, shared network `TRAEFIK_NETWORK`)
- Routing rules via Docker labels (HTTP routers per service)

**Cloudflare Tunnel:**
- Used for: Exposing local/dev services for webhook testing
- Image: `cloudflare/cloudflared:latest` (container: `cloudflare-tunnel`)
- Config: `CLOUDFLARE_TUNNEL_TOKEN` (env)
- Profile: `extended` (not started by default)

**CI Pipeline:**
- Not detected — no GitHub Actions or similar CI config found

## Webhooks & Callbacks

**Incoming Webhooks (backend receives):**
- `/api/v1/iam/webhooks` — Clerk user lifecycle events (verified via Svix)
- `/api/v1/connections/whatsapp` — WhatsApp Cloud API events (verified via `WHATSAPP_VERIFY_TOKEN`)
- `/api/v1/connections/telegram` — Telegram bot updates
- `/api/v1/connections/marketing-webhooks` — Generic marketing events (MailerLite, ManyChat, Shopify)
- `/api/v1/connections/shopify` — Shopify order/customer events (HMAC verified)
- `/api/v1/connections/shopify/compliance` — GDPR data erasure requests
- `/api/v1/connections/meta` — Meta/Facebook events (verify token + signature)
- `/api/webhooks/:path*` — Next.js rewrites to backend (from `frontend/next.config.js`)

**Outgoing Webhooks (backend sends):**
- WhatsApp: Messages via Evolution API REST endpoints
- Telegram: Messages via Telegram Bot API
- MailerLite: Subscriber/campaign management via `https://connect.mailerlite.com/api`
- Shopify: Store management via Shopify Admin API
- Meta Ads: Via `facebook-business` SDK

## Environment Configuration

**Required Backend Environment Variables:**
- `OPENAI_API_KEY` — OpenAI API access
- `REDIS_URL` — Redis connection string
- `QDRANT_URL` — Qdrant connection string
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT` — DB connection
- `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN` — WhatsApp Cloud API
- `API_SECRET_KEY` — Internal API security
- `CLERK_ISSUER` — JWT verification base URL
- `LOG_LEVEL`, `DOMAIN_NAME`, `TRAEFIK_NETWORK` — Infrastructure
- `API_URL` — Internal URL used for self-referencing webhooks

**Required Frontend Environment Variables:**
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk (build-time, required)
- `NEXT_PUBLIC_API_URL` — Public API URL
- `NEXT_PUBLIC_APP_URL` — Public app URL
- `INTERNAL_API_URL` — Docker-internal API URL for server-side requests

**Secrets Location:**
- `.env` file (local dev, gitignored)
- `.env.prod` file (production, gitignored)
- Template: `.env.example` (committed, no secrets)

---

*Integration audit: 2026-03-20*
