# Codebase Structure

**Analysis Date:** 2026-03-15

## Directory Layout

```
AISALESHT/                          # Project root
├── backend/                        # FastAPI backend (Python)
│   ├── src/
│   │   ├── main.py                 # App entry point, router registration
│   │   ├── core/                   # Shared infrastructure (config, db, context, logging)
│   │   ├── shared/                 # Cross-module domain + infra primitives
│   │   ├── modules/                # DDD bounded contexts (13 modules)
│   │   └── admin/                  # Streamlit admin dashboard
│   ├── alembic/                    # DB migrations
│   │   └── versions/               # Migration files
│   ├── tests/                      # Backend test suite
│   ├── scripts/                    # Dev/test utility scripts
│   ├── static/                     # Static file serving
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                       # Next.js 14 frontend (TypeScript)
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages
│   │   ├── features/               # FSD feature slices
│   │   ├── components/             # Shared/global UI components
│   │   ├── hooks/                  # Shared React hooks
│   │   ├── lib/                    # Shared utilities (http-client, config, etc.)
│   │   └── middleware.ts           # Clerk auth middleware
│   └── Dockerfile
├── docs/                           # Product & domain documentation
│   ├── domains/INDEX.md            # Business domain index (CRITICAL reference)
│   └── vision/product-vision.md   # Product vision
├── docker-compose.yml              # Dev Docker Compose
├── docker-compose.prod.yml         # Prod Docker Compose
├── CLAUDE.md                       # Project conventions for AI agents
└── Makefile                        # Dev shortcuts
```

## Backend Module Structure

Every module in `backend/src/modules/{module}/` follows this layout:

```
{module}/
├── domain/                         # Pure business logic — no I/O
│   ├── aggregates.py               # Root aggregates (Pydantic BaseEntity)
│   ├── entities.py                 # Sub-entities
│   ├── enums.py                    # Domain enums
│   └── value_objects.py            # Value objects
├── infrastructure/
│   ├── models/                     # SQLAlchemy ORM models
│   │   └── {entity}_model.py
│   └── repositories/               # Data access objects
│       └── {entity}_repository.py
├── application/
│   ├── services/                   # Use case services
│   │   └── {name}_service.py
│   ├── dto/                        # Internal DTOs (application-level)
│   │   └── {name}_dto.py
│   └── agents/                     # LangGraph agent graphs (AI modules only)
│       └── {name}/
│           ├── graph.py
│           └── state.py
└── api/
    ├── router.py (or named routes)  # FastAPI APIRouter instances
    └── dto/                         # Request/response Pydantic models
        └── {name}_dto.py
```

**Active modules:**
- `backend/src/modules/iam/` — Tenants, Users, Clerk webhooks, auth dependencies
- `backend/src/modules/brand/` — Brand identity, strategy, story, avatars
- `backend/src/modules/offer/` — Offer Ladder (products, offer types, definitions)
- `backend/src/modules/landing/` — Landing page generation and configuration
- `backend/src/modules/assets/` — Asset gallery (images, generated files)
- `backend/src/modules/crm/` — Leads, customers (CDP), sales, pipeline
- `backend/src/modules/sales_agent/` — AI SDR orchestration (LangGraph), audit
- `backend/src/modules/scheduling/` — Event types, booking, agenda
- `backend/src/modules/analytics/` — Funnel/Bowtie metrics, Sankey data
- `backend/src/modules/advertising/` — Ad campaign data (API not yet exposed)
- `backend/src/modules/social_media/` — Social media data (API not yet exposed)
- `backend/src/modules/connections/` — External integrations (Meta, WhatsApp, Telegram, Shopify, Gmail, YouTube, MailerLite, ManyChat, Google Analytics, Google Calendar, Google Workspace)
- `backend/src/modules/copilot/` — AI copilot: web extractor, style analyzer, brand extraction agents

## Backend Core & Shared

**`backend/src/core/`** — Infrastructure primitives:
- `config.py` — Pydantic `Settings` (env-driven config)
- `database.py` — SQLAlchemy engine, `SessionLocal`, `get_db`, `init_db()`
- `context.py` — `ContextVar` tenant ID store (`get_tenant_id`, `set_tenant_id`)
- `base_repository.py` — `BaseRepository` with tenant filter helpers
- `logger.py` — Structlog setup
- `security.py` — Auth utilities
- `exceptions.py` — Custom exceptions
- `enums.py` — Shared enums

**`backend/src/shared/`** — Cross-module domain/infra:
- `domain/base_entity.py` — `BaseEntity` (Pydantic) and SQLAlchemy `Base`
- `domain/messages.py` — Shared message value objects
- `domain/value_objects.py` — Shared value objects
- `infrastructure/llm/` — LLM factory (`base.py`, `factory.py`, `providers/`)
- `infrastructure/channels/` — Channel abstractions
- `infrastructure/external/` — External service clients
- `infrastructure/files/` — File utilities
- `infrastructure/database/types.py` — Custom DB column types

**`backend/src/admin/`** — Streamlit admin dashboard:
- `app.py` — Streamlit entry point
- `modules/` — Admin UI module pages
- `tenants.py`, `users.py` — Admin logic files

## Frontend App Router Structure

```
frontend/src/app/
├── (main)/                         # Main route group (auth-gated via middleware)
│   ├── [tenantId]/                 # Tenant-scoped routes
│   │   ├── (dashboard)/            # Dashboard route group (shared layout)
│   │   │   ├── layout.tsx          # Sidebar layout wrapper
│   │   │   ├── page.tsx            # Dashboard home
│   │   │   ├── brand-settings/     # Brand Studio page
│   │   │   ├── marketing-studio/   # Growth Studio (Funnel + Metrics)
│   │   │   ├── offer-studio/       # Offer Ladder + Landing Editor
│   │   │   ├── sales/              # Sales Operations Hub
│   │   │   ├── settings/           # Tenant settings
│   │   │   ├── onboarding/         # Onboarding wizard
│   │   │   ├── avatars/            # Buyer persona management
│   │   │   ├── authority/          # Authority vault
│   │   │   └── admin/              # Super-admin panel
│   │   └── preview/[offerId]/      # Landing page preview
│   ├── (public)/p/[slug]/          # Public landing pages
│   ├── book/[tenant_slug]/         # Public booking pages
│   ├── onboarding/                 # First-time onboarding flow
│   ├── sign-in/[[...sign-in]]/     # Clerk sign-in
│   ├── sign-up/[[...sign-up]]/     # Clerk sign-up
│   ├── visit/[token]/              # Token-based visit tracking
│   └── forbidden/                  # 403 error page
├── (landing)/[tenantId]/editor/    # Landing page editor (separate route group)
│   └── [offerId]/
├── api/auth/shopify/               # Next.js API route for Shopify OAuth
└── connections/                    # OAuth callback pages (Meta, brand-settings)
```

## Frontend Feature Slice Structure

```
frontend/src/features/
├── brand/                          # Brand Studio
│   ├── api/index.ts                # brandApi client
│   ├── api/mock-data.ts
│   ├── hooks/useBrandSettings.ts   # TanStack Query hook
│   ├── types/index.ts              # TypeScript types
│   ├── components/                 # UI components
│   │   ├── container/              # Layout containers
│   │   ├── forms/                  # Form components
│   │   ├── navigation/             # Nav rail
│   │   └── smart-fill/             # AI auto-fill components
│   └── sections/                   # Content sections (identity, story, etc.)
├── marketing-studio/               # Growth Studio (Metrics Dashboard)
│   ├── api/metrics-api.ts
│   ├── api/metrics-mock-data.ts
│   ├── hooks/useMarketingData.ts
│   ├── hooks/useAttractionDetail.ts
│   ├── types/                      # Metrics TypeScript types
│   └── components/
│       ├── metrics-dashboard/      # Main dashboard components
│       │   ├── channel-widgets/
│       │   └── detail-panels/
│       └── strategy-canvas/        # LangGraph-style canvas UI
├── offer-studio/                   # Offer Ladder + Landing Pages
│   ├── api/
│   ├── hooks/
│   ├── types/
│   ├── config/
│   └── components/
│       ├── editor/                 # Offer editor (sections, cards, widgets)
│       ├── landing/                # Landing page builder/preview
│       └── navigation/
├── sales/                          # Sales Operations Hub
│   ├── components/
│   │   ├── atoms/
│   │   ├── molecules/
│   │   ├── organisms/
│   │   └── dashboard/lanes/        # Kanban pipeline lanes
│   ├── hooks/
│   ├── services/
│   └── types/
├── connections/                    # Integration connections UI
├── audit/                          # Sales audit log
├── settings/                       # Tenant settings
└── admin/                          # Super-admin components
```

## Frontend Shared Structure

**`frontend/src/components/`:**
- `ui/` — Shadcn UI primitives (Button, Card, Dialog, etc.) — never modified directly
- `shared/layout/app-sidebar.tsx` — Main application sidebar
- `shared/layout/sidebar-context.tsx` — Sidebar state context
- `shared/layout/tenant-switcher.tsx` — Tenant selector component
- `providers/theme-provider.tsx` — Theme provider
- `auth/` — Auth-related UI components

**`frontend/src/lib/`:**
- `http-client.ts` — `fetchClient` wrapper (auto-injects `X-Tenant-ID`, handles 401/403)
- `config.ts` — `config.api.baseUrl` (server: `INTERNAL_API_URL`, client: `NEXT_PUBLIC_API_URL`)
- `mock-config.ts` — `ENABLE_MOCKS` boolean flag
- `utils.ts` — `cn()` class name utility (clsx + tailwind-merge)
- `utils/` — Additional utility modules
- `constants/` — App-wide constants

**`frontend/src/hooks/`** — Shared hooks:
- `use-debounce.ts`, `use-intersection-observer.ts`, `use-local-storage.ts`

## Naming Conventions

**Backend Files:**
- Module names: `snake_case` (`sales_agent`, `social_media`)
- Service files: `{name}_service.py` (e.g., `metrics_service.py`, `extraction_service.py`)
- Model files: `{entity}_model.py` (e.g., `avatar_model.py`, `tenant_model.py`)
- Repository files: `{entity}_repository.py`
- Router files: descriptive noun (`metrics.py`, `products.py`, `leads.py`)

**Frontend Files:**
- Feature directories: `kebab-case` (`marketing-studio`, `offer-studio`)
- Component files: `PascalCase.tsx` (e.g., `MetricsDashboard.tsx`)
- Hook files: `use{Name}.ts` (e.g., `useBrandSettings.ts`, `useMarketingData.ts`)
- API modules: `{name}-api.ts` (e.g., `metrics-api.ts`)
- Type files: `index.ts` inside `types/` directory, or `{name}.ts`

**API Routes (Backend):**
- Pattern: `/api/v1/{domain}/{resource}` (e.g., `/api/v1/analytics/metrics/sankey`)
- All tenant-protected routes registered with `dependencies=[Depends(get_tenant_context)]`

## Where to Add New Code

**New Backend Module:**
1. Create `backend/src/modules/{new_module}/` with the four-layer structure
2. Add domain entities extending `src/shared/domain/base_entity.BaseEntity`
3. Add SQLAlchemy model extending `Base` from `src/shared/domain/base_entity`
4. Add repository extending `src/core/base_repository.BaseRepository`
5. Register router in `backend/src/main.py` with `dependencies=[Depends(get_tenant_context)]`
6. Create Alembic migration: `alembic revision --autogenerate -m "description"`

**New Backend Endpoint in Existing Module:**
1. Add route handler to `backend/src/modules/{module}/api/{router_file}.py`
2. Add application service method to `backend/src/modules/{module}/application/services/`
3. Add DTOs to `backend/src/modules/{module}/api/dto/`
4. No registration needed if using existing router file

**New Frontend Feature:**
1. Create `frontend/src/features/{feature}/` with: `api/`, `hooks/`, `components/`, `types/`
2. Add API client in `api/index.ts` using `fetchClient` from `@/lib/http-client`
3. Add TanStack Query hook in `hooks/use{Feature}.ts`
4. Create page in `frontend/src/app/(main)/[tenantId]/(dashboard)/{feature}/page.tsx`
5. Page should be minimal — render the feature's top-level component

**New Frontend Component:**
- Feature-specific: `frontend/src/features/{feature}/components/{ComponentName}.tsx`
- Cross-feature shared UI: `frontend/src/components/shared/{ComponentName}.tsx`
- Primitive/base UI: `frontend/src/components/ui/` (Shadcn only)

**New API Mock:**
- Add mock data to `frontend/src/features/{feature}/api/{feature}-mock-data.ts`
- Guard API calls with `if (ENABLE_MOCKS) return MOCK_DATA` at top of function

**New DB Migration:**
- Run inside backend container: `alembic revision --autogenerate -m "describe_change"`
- Apply: `alembic upgrade head`
- Files land in: `backend/alembic/versions/`

## Special Directories

**`backend/model_cache/`:**
- Purpose: Cached Qdrant embedding model (multilingual MiniLM)
- Generated: Yes (downloaded at runtime)
- Committed: No (excluded from git, mounted via Docker volume)

**`backend/alembic/versions/`:**
- Purpose: Database schema migration files
- Generated: Yes (via `alembic revision`)
- Committed: Yes

**`frontend/.next/`:**
- Purpose: Next.js build output
- Generated: Yes
- Committed: No

**`docs/domains/`:**
- Purpose: Business domain documentation — ANTI-HALLUCINATION reference
- Key file: `docs/domains/INDEX.md` — must be read before coding any domain logic
- Committed: Yes

**`.planning/codebase/`:**
- Purpose: AI agent analysis documents for GSD workflow
- Generated: Yes (by map-codebase command)
- Committed: Yes

---

*Structure analysis: 2026-03-15*
