# External Integrations

**Analysis Date:** 2026-03-15

## Authentication & Identity

**Clerk:**
- Purpose: Primary auth provider — user sign-in, sign-up, JWT session management, organization/tenant metadata
- Frontend SDK: `@clerk/nextjs ^6.36.8`
- Frontend middleware: `frontend/src/middleware.ts` — all non-public routes protected via `clerkMiddleware`
- Frontend provider: `ClerkProvider` in `frontend/src/app/(main)/layout.tsx`
- Tenant ID stored in `user.publicMetadata.tenant_id`, synced to localStorage on login (`frontend/src/app/providers.tsx`)
- Backend SDK: `svix >=1.1.1` for webhook signature verification
- Backend REST client: `backend/src/shared/infrastructure/external/clerk.py` — calls `https://api.clerk.com/v1/users`
- Webhook listener: `backend/src/modules/iam/api/webhooks.py` at `/api/v1/iam/webhooks` — handles `user.created`, `user.updated`, `user.deleted` events to sync Clerk users to local DB
- Required env vars: `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (frontend build-time)
- Custom auth domain: `CLERK_DOMAIN` env var (used in `frontend/next.config.js` CORS origins)

## AI / LLM Providers

**OpenAI (Primary):**
- Purpose: Chat completions, embeddings for RAG, offer/brand AI generation
- SDK: `langchain-openai >=0.0.8` (wraps official openai SDK)
- Default models: `gpt-4-turbo-preview` (reasoning), `gpt-3.5-turbo` (fast/cheap), `text-embedding-3-large` (3072-dim embeddings)
- Tenant-level key override: tenants can supply their own `openai_api_key`; falls back to platform key if `can_use_platform_keys` is true
- Factory: `backend/src/shared/infrastructure/llm/factory.py` (`LLMFactory`)
- Required env vars: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_FAST_MODEL`, `OPENAI_EMBEDDING_MODEL`

**Google Gemini (Secondary/Optional):**
- Purpose: Alternative LLM provider (same `LLMFactory` interface)
- SDK: `langchain-google-genai 0.0.9`
- Default model: `gemini-pro`
- Required env vars: `GEMINI_API_KEY`, `GEMINI_MODEL`
- Provider selection: `AI_PROVIDER` env var (`openai` or `gemini`), default: `openai`

**Provider selection:**
- `backend/src/core/config.py`: `AI_PROVIDER: AIProvider = AIProvider.OPENAI`
- Prompt source: `PROMPT_SOURCE` env var (`hybrid`, `file`, or `db`)

## Data Storage

**PostgreSQL 15:**
- Purpose: Primary relational database — all domain models (tenants, users, brands, offers, CRM, scheduling, connections, assets, analytics)
- Image: `postgres:15-alpine`
- Connection: Sync SQLAlchemy engine in `backend/src/core/database.py`
- URL built from: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`
- Migrations: Alembic (`backend/alembic/`)
- Dev port binding: `127.0.0.1:5432:5432` (secure)
- Prod: internal network only (no host port)

**Redis 7:**
- Purpose: Session caching, conversation history buffers, Evolution API cache
- Image: `redis:7-alpine`
- Persistence: AOF (`appendonly yes`)
- Client: `redis 5.0.1` (sync), initialized in `backend/src/core/database.py`
- Required env var: `REDIS_URL` (e.g. `redis://redis:6379/0`)
- Evolution API uses Redis DB `1` with prefix `evolution:`
- Dev port binding: `127.0.0.1:6379:6379` (secure)

**Qdrant v1.7.3:**
- Purpose: Vector database for semantic memory and RAG (Sales Agent knowledge base)
- Image: `qdrant/qdrant:v1.7.3`
- Client: `qdrant-client 1.7.3`
- Collections: `visionarias_knowledge` (dense), `visionarias_hybrid` (hybrid BM25 + dense)
- Vector size: 3072 (text-embedding-3-large)
- Sparse model: `Qdrant/bm25` (via fastembed)
- Reranker: `ms-marco-MiniLM-L-12-v2` (local, cached at `/app/model_cache`)
- Implementation: `backend/src/modules/sales_agent/infrastructure/memory/vector_store.py`
- Required env vars: `QDRANT_URL`, `QDRANT_API_KEY` (optional locally, required in prod)
- Dev ports: `127.0.0.1:6333:6333`, `127.0.0.1:6334:6334`

## File Storage

**Local Filesystem (Default):**
- Upload directory: `static/uploads` (configured via `UPLOAD_DIR` env var)
- Static files served via FastAPI `StaticFiles` at `/static`
- Volume mounted in prod: `./data/static:/app/static`

**Cloudflare R2 (Production Option):**
- Purpose: Object storage for uploads (images, assets) — switchable via `STORAGE_PROVIDER=R2`
- SDK: `boto3 >=1.34.0` (S3-compatible API)
- Required env vars: `CLOUDFLARE_ACCOUNT_ID`, `R2_BUCKET_NAME`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL`

## Messaging / Communication Channels

**WhatsApp Business API (Meta Cloud):**
- Purpose: Inbound/outbound WhatsApp messages for Sales Agent
- SDK: Meta's HTTP API directly
- Webhook: `POST /api/v1/connections/whatsapp/webhooks/whatsapp` (handled by `backend/src/modules/connections/api/whatsapp.py`)
- Webhook verification: `GET` with hub token challenge
- Required env vars: `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`

**Evolution API (Self-Hosted WhatsApp Engine):**
- Purpose: Alternative multi-instance WhatsApp bridge (self-hosted)
- Image: `atendai/evolution-api:v1.8.2`
- Versions supported: v1 (default), v2 — configurable via `EVOLUTION_API_VERSION`
- Implementation: `backend/src/modules/connections/infrastructure/channels/whatsapp/` (factory, v1.py, v2.py)
- Required env vars: `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`
- Dev port: `127.0.0.1:8080:8080` (internal use)

**Telegram:**
- Purpose: Telegram bot integration for Sales Agent
- SDK: Bot API (direct HTTP, no SDK)
- Webhook: `POST /api/v1/connections/telegram/webhooks/telegram` (global) and `/webhooks/telegram/{tenant_id}` (per-tenant)
- Implementation: `backend/src/modules/connections/infrastructure/channels/telegram_service.py`
- Required env var: `TELEGRAM_BOT_TOKEN`

## Social & Ad Platforms

**Meta (Facebook/Instagram):**
- Purpose: Facebook Pages, Instagram DMs, Meta Ads accounts management
- SDK: `facebook-business` pip package
- Backend: `backend/src/modules/connections/infrastructure/channels/meta.py`, `instagram.py`
- API: `backend/src/modules/connections/api/meta.py`
- Webhook: `POST /api/v1/connections/meta/webhook` (signature verified via `verify_meta_signature` dependency)
- OAuth flow: Standard Meta OAuth with `META_CONFIG_ID` (Facebook Login for Business)
- Required env vars: `META_APP_ID`, `META_APP_SECRET`, `META_VERIFY_TOKEN`, `META_REDIRECT_URI`, `META_CONFIG_ID`

**YouTube / YouTube Analytics:**
- Purpose: YouTube channel data and analytics
- SDK: `google-api-python-client`
- Implementation: `backend/src/modules/connections/infrastructure/channels/youtube.py`, `youtube_analytics.py`
- API: `backend/src/modules/connections/api/youtube.py`, `youtube_analytics.py`

**ManyChat:**
- Purpose: ManyChat integration for marketing automation flows
- SDK: Direct HTTP API
- Implementation: `backend/src/modules/connections/infrastructure/marketing_connectors/manychat.py`
- API: `backend/src/modules/connections/api/manychat.py`

## Google Services

**Google Calendar:**
- Purpose: Scheduling integration — event creation, availability check
- SDK: `google-api-python-client`, `google-auth-oauthlib`
- Implementation: `backend/src/modules/connections/infrastructure/channels/google_calendar.py`
- API: `backend/src/modules/connections/api/calendar.py` at `/api/v1/connections/calendar`
- OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

**Gmail:**
- Purpose: Email sending and reading via Gmail OAuth
- SDK: `google-api-python-client`
- Implementation: `backend/src/modules/connections/infrastructure/channels/gmail.py`
- API: `backend/src/modules/connections/api/gmail.py` at `/api/v1/connections/gmail`

**Google Analytics:**
- Purpose: Website analytics data ingestion
- SDK: `google-api-python-client`
- Implementation: `backend/src/modules/connections/infrastructure/channels/google_analytics.py`
- API: `backend/src/modules/connections/api/google_analytics.py`
- Per-tenant OAuth credentials (client_id/client_secret stored in `ChannelConnectionModel`)

**Google Workspace:**
- Purpose: Workspace integration (Drive, Docs, etc.)
- SDK: `google-api-python-client`
- API: `backend/src/modules/connections/api/google_workspace.py`

## E-commerce

**Shopify:**
- Purpose: E-commerce store connection — product sync, order webhooks
- SDK: Direct Shopify Admin API (OAuth flow)
- Implementation: `backend/src/modules/connections/infrastructure/marketing_connectors/shopify.py`
- API: `backend/src/modules/connections/api/shopify.py` at `/api/v1/connections/shopify`
- Compliance router: `backend/src/modules/connections/api/shopify_compliance.py` (GDPR compliance webhooks)
- OAuth: Authorization URL generation → callback exchange
- Required env vars: `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_APP_URL`
- Frontend: `SHOPIFY_API_KEY` also injected into Next.js container

## Email Marketing

**MailerLite:**
- Purpose: Email list management and campaign triggers
- SDK: Direct HTTP API (no official SDK)
- Implementation: `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py`
- API: `backend/src/modules/connections/api/mailerlite.py` at `/api/v1/connections/mailerlite`
- Auth: API key stored encrypted in `ChannelConnectionModel.credentials`

## Infrastructure & Networking

**Traefik (Reverse Proxy):**
- Purpose: HTTP routing, TLS termination, service discovery
- Configuration: Docker labels in `docker-compose.yml` and `docker-compose.prod.yml`
- TLS: Let's Encrypt via `certresolver=letsencrypt` in prod
- Required env var: `TRAEFIK_NETWORK` (external Docker network name)

**Cloudflare Tunnel:**
- Purpose: Secure public ingress without exposing server ports
- Image: `cloudflare/cloudflared:latest`
- Required env var: `CLOUDFLARE_TUNNEL_TOKEN`
- Used in dev compose only (prod uses Traefik directly)

## Webhooks

**Incoming Webhooks (Backend receives):**
- `POST /api/v1/iam/webhooks` — Clerk user lifecycle events (user.created, user.updated, user.deleted)
- `POST /api/v1/connections/whatsapp/webhooks/whatsapp` — WhatsApp Business API messages
- `POST /api/v1/connections/telegram/webhooks/telegram` — Telegram bot messages (global + per-tenant)
- `POST /api/v1/connections/meta/webhook` — Meta (Facebook/Instagram) events
- `POST /api/v1/connections/marketing-webhooks` — Generic marketing platform webhooks
- `POST /api/v1/connections/shopify/compliance` — Shopify GDPR compliance webhooks
- `/api/v1/connections/webhook` — Generic inbound webhook handler
- Frontend proxies all `/api/webhooks/*` → backend via Next.js rewrites (public route, bypasses Clerk auth)

**Outgoing:**
- Sales Agent sends messages via WhatsApp API, Telegram Bot API
- MailerLite API for subscriber management
- ManyChat API for flow triggers
- Shopify Admin API for store operations
- Google APIs (Calendar event creation, Gmail send, Analytics read)
- Meta Graph API for ad account operations
- Clerk Backend API (`https://api.clerk.com/v1`) for user management

## Monitoring & Observability

**Logging:**
- Backend: `structlog >=24.1.0` — structured JSON logging with request_id context binding
- Configured in `backend/src/core/logger.py`
- HTTP middleware logs every request with method, path, status, process time
- Level controlled via `LOG_LEVEL` env var

**Error Tracking:**
- No external error tracking service detected (no Sentry, Datadog, etc.)

**Health Check:**
- Backend: `GET /health` returns `{"status": "ok", "version": "1.0.0"}`
- Docker healthcheck hits `http://localhost:8000/health` every 30s

## Environment Configuration Summary

**Required for all environments:**
```
OPENAI_API_KEY
POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB / POSTGRES_HOST / POSTGRES_PORT
REDIS_URL
QDRANT_URL
API_SECRET_KEY
CLERK_SECRET_KEY
CLERK_WEBHOOK_SECRET
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
WHATSAPP_API_TOKEN / WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_VERIFY_TOKEN
TRAEFIK_NETWORK
CORS_ORIGINS
API_URL
NEXT_PUBLIC_API_URL / NEXT_PUBLIC_APP_URL / INTERNAL_API_URL
```

**Feature-gated (empty defaults):**
```
GEMINI_API_KEY                    # Gemini LLM provider
EVOLUTION_API_URL / EVOLUTION_API_KEY  # Self-hosted WhatsApp
TELEGRAM_BOT_TOKEN                # Telegram integration
GOOGLE_CLIENT_ID / SECRET / REDIRECT_URI  # Google OAuth
META_APP_ID / SECRET / VERIFY_TOKEN / REDIRECT_URI / CONFIG_ID
SHOPIFY_API_KEY / SECRET / APP_URL
CLOUDFLARE_ACCOUNT_ID + R2_* vars  # R2 object storage
QDRANT_API_KEY                    # Qdrant auth (prod)
CLOUDFLARE_TUNNEL_TOKEN           # Cloudflare Tunnel
```

---

*Integration audit: 2026-03-15*
