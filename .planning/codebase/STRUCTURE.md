# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```
AISALESHT/                         # Monorepo root
├── backend/                       # FastAPI backend (Python)
│   ├── src/
│   │   ├── main.py                # FastAPI app factory + all router mounts
│   │   ├── core/                  # Global config, DB session, logging, enums
│   │   ├── modules/               # DDD bounded contexts (one per business domain)
│   │   │   ├── iam/               # Identity & Access Management
│   │   │   ├── brand/             # Brand DNA capture
│   │   │   ├── offer/             # Offer Ladder builder
│   │   │   ├── landing/           # Landing page AI generation
│   │   │   ├── sales_agent/       # AI SDR (LangGraph agents)
│   │   │   ├── copilot/           # In-app AI assistant
│   │   │   ├── crm/               # Leads, CDP, pipeline
│   │   │   ├── scheduling/        # Event types, availability
│   │   │   ├── analytics/         # Bowtie funnel metrics + ETL
│   │   │   ├── connections/       # External integrations (Meta, WA, TG, etc.)
│   │   │   ├── assets/            # Image gallery and offer assets
│   │   │   ├── advertising/       # (Stub — no router mounted yet)
│   │   │   └── social_media/      # (Stub — no router mounted yet)
│   │   └── shared/                # Cross-module reusable code
│   │       ├── domain/            # Base entities, EventBus, shared value objects
│   │       ├── infrastructure/    # DB session, LLM factory, channels, file parsing
│   │       ├── application/       # AIActionService and shared app utilities
│   │       └── links/             # Shared link generation utilities
│   ├── alembic/                   # Database migrations
│   │   └── versions/              # Migration scripts (idempotent raw SQL)
│   ├── scripts/                   # One-off admin/seed scripts
│   ├── tests/                     # Integration tests
│   ├── pyproject.toml             # Python project config (ruff, pytest)
│   └── requirements.txt           # Python dependencies
│
├── frontend/                      # Next.js 14 frontend (TypeScript)
│   ├── src/
│   │   ├── app/                   # Next.js App Router (routing only)
│   │   │   ├── (main)/            # Authenticated shell
│   │   │   │   ├── [tenantId]/    # Tenant-scoped routes
│   │   │   │   │   └── (dashboard)/ # Dashboard layout group
│   │   │   │   ├── sign-in/       # Clerk auth pages
│   │   │   │   └── sign-up/
│   │   │   ├── (landing)/         # Landing page editor shell
│   │   │   ├── connections/       # OAuth callback pages
│   │   │   ├── api/               # Next.js API routes (Shopify auth)
│   │   │   └── playground/        # Dev playground (non-production)
│   │   ├── features/              # FSD feature slices
│   │   │   ├── brand/             # Brand Studio
│   │   │   ├── offer-studio/      # Offer Ladder editor
│   │   │   ├── marketing-studio/  # Growth Studio (Bowtie metrics dashboard)
│   │   │   ├── sales/             # Sales Studio (inbox, pipeline)
│   │   │   ├── settings/          # Tenant/user settings
│   │   │   ├── connections/       # Integration config UI
│   │   │   ├── audit/             # AI conversation audit log
│   │   │   └── admin/             # Super-admin tenant list
│   │   ├── components/            # Shared UI components
│   │   │   ├── ui/                # Shadcn/Radix primitives (do not modify)
│   │   │   ├── shared/layout/     # AppSidebar, SidebarContext, TenantSwitcher
│   │   │   ├── auth/              # TenantGuard
│   │   │   └── providers/         # ThemeProvider
│   │   ├── lib/                   # Client-side infrastructure
│   │   │   ├── api/               # Per-domain fetch wrapper modules
│   │   │   ├── http-client.ts     # Fetch interceptor (X-Tenant-ID injection)
│   │   │   ├── config.ts          # Environment-driven config (API URL)
│   │   │   ├── utils.ts           # cn() and general utilities
│   │   │   ├── constants/         # Shared constants (currencies, etc.)
│   │   │   └── design-system/     # Design tokens
│   │   ├── hooks/                 # Global shared hooks (useDebounce, etc.)
│   │   ├── stories/               # Storybook stories (atoms/molecules/organisms)
│   │   └── test/                  # Test setup files
│   ├── public/                    # Static assets
│   ├── next.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── docker-compose.yml             # Dev environment (all services)
├── docker-compose.prod.yml        # Production deployment
├── .env.example                   # Required environment variable template
└── shopify_app/                   # Shopify app config generation
```

## Directory Purposes

**`backend/src/modules/{module}/`:**
Each module is a self-contained bounded context with four mandatory sub-layers:
- `api/` — FastAPI routers + Pydantic DTOs
- `application/` — Services, AI agents, orchestrators
- `domain/` — Pure Python/Pydantic entities and enums
- `infrastructure/` — ORM models, repositories, external clients

Key files per module:
- `api/router.py` or `api/{resource}.py` — primary router file
- `api/dto/` — Pydantic request/response schemas
- `infrastructure/models/{name}_model.py` — SQLAlchemy ORM model
- `infrastructure/repositories/{name}_repository.py` — DB access layer

**`backend/src/shared/`:**
- `domain/base_entity.py` — SQLAlchemy `Base` declarative base (all models import from here)
- `domain/events.py` — `EventBus` and `DomainEvent` base class
- `domain/messages.py` — `IncomingMessage` / `OutgoingMessage` types for agent channels
- `infrastructure/llm/factory.py` — `LLMFactory` (OpenAI/Gemini abstraction)
- `infrastructure/database/` — AsyncSession + sync `SessionLocal`, `get_db`, `redis_client`

**`backend/src/core/`:**
- `main.py` equivalent config/bootstrap: `config.py`, `database.py`, `logger.py`, `context.py`, `enums.py`
- `context.py` — `ContextVar` for async-safe tenant ID propagation

**`backend/alembic/versions/`:**
All migrations must be written as idempotent raw SQL:
- `CREATE TABLE IF NOT EXISTS` (not `op.create_table`)
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (not `op.add_column`)
- Enum types referenced by name, never re-created

**`frontend/src/app/(main)/[tenantId]/(dashboard)/`:**
All dashboard routes live here. The `[tenantId]` segment is the tenant UUID extracted by `fetchClient` for API calls. Each sub-route maps to a feature:
- `brand-settings/` → `features/brand`
- `offer-studio/` → `features/offer-studio`
- `marketing-studio/` → `features/marketing-studio`
- `sales/` → `features/sales`
- `settings/` → `features/settings`
- `audit/` → `features/audit`

**`frontend/src/features/{domain}/`:**
- `components/` — All UI components for this feature
- `hooks/` — Data-fetching and state hooks (TanStack Query wrappers)
- `api/` — Fetch functions wrapping `fetchClient`; may include `mock-data.ts`
- `types/` — TypeScript interfaces and Zod schemas
- `utils/` — Pure helper functions
- `index.ts` — Public API barrel file (required)

**`frontend/src/components/ui/`:**
Shadcn/Radix primitives. Do not modify logic. Add new components via `npx shadcn@latest add <component>`.

**`frontend/src/lib/api/`:**
Per-domain API modules (not feature-specific). These are thin wrappers:
`leads.ts`, `availability.ts`, `avatar.ts`, `booking-links.ts`, `connections.ts`, `event-types.ts`, `offer-gallery.ts`, `public.ts`, `settings.ts`, `whatsapp.ts`, `admin.ts`

## Key File Locations

**Entry Points:**
- `backend/src/main.py` — FastAPI app + all router registrations
- `frontend/src/app/(main)/layout.tsx` — Root authenticated layout (ClerkProvider wraps here)
- `frontend/src/app/providers.tsx` — QueryClient + ThemeProvider + tenant ID bootstrap
- `frontend/src/middleware.ts` — Clerk auth middleware (protects all non-public routes)

**Configuration:**
- `frontend/src/lib/config.ts` — `API_URL` and feature flags
- `backend/src/core/config.py` — Settings (Pydantic BaseSettings, reads from env)
- `docker-compose.yml` — Service definitions for dev
- `.env.example` — All required environment variables

**Authentication/Tenancy:**
- `backend/src/modules/iam/api/dependencies.py` — `get_current_user`, `get_tenant_context`
- `backend/src/core/context.py` — `ContextVar` for tenant ID
- `frontend/src/lib/http-client.ts` — `fetchClient` (injects `X-Tenant-ID` + Bearer token)

**AI Agents:**
- `backend/src/modules/sales_agent/application/orchestrator/graph.py` — Main agent LangGraph
- `backend/src/modules/sales_agent/application/agents/sales/graph.py` — Sales subgraph
- `backend/src/modules/copilot/application/agents/web_extractor/graph.py` — Web scraping agent
- `backend/src/modules/sales_agent/infrastructure/prompts/` — Prompt loader + Jinja2 templates

**Database:**
- `backend/src/shared/infrastructure/database/` — `session.py` (AsyncSession + sync fallback)
- `backend/alembic/` — Migration config and versions

**Shared Utilities:**
- `backend/src/shared/domain/events.py` — `EventBus` (cross-module events)
- `backend/src/shared/infrastructure/llm/factory.py` — `LLMFactory`
- `frontend/src/lib/utils.ts` — `cn()` (clsx + twMerge)

## Naming Conventions

**Backend Files:**
- Modules: `snake_case` directory names (`sales_agent`, `offer`, `iam`)
- Models: `{Name}Model` class, file `{name}_model.py` (e.g., `LeadModel` in `lead_model.py`)
- Repositories: `{Name}Repository` class, file `{name}_repository.py`
- Services: `{Name}Service` class, file `{name}_service.py`
- Routers: `router.py` (single) or `{resource}.py` (multiple per module)
- DTOs: Pydantic classes in `api/dto/` or `application/dto/`

**Frontend Files:**
- Components: `PascalCase.tsx` for class-style names, `kebab-case.tsx` for most feature components
- Hooks: `use-{name}.ts` or `use{Name}.ts` (both patterns exist; prefer `use-{name}.ts`)
- Types: `index.ts` inside `types/` directory, or named `{name}.ts`
- API modules: `{resource}.ts` in `lib/api/` or `api/index.ts` in features

**Backend Directories:**
- `snake_case` for all directories
- Exception: `infrastructure/db/` in `sales_agent` (non-standard — see ARCHITECTURE.md deviations)

**Frontend Directories:**
- `kebab-case` for all directories
- Exception: `features/sales/components/atoms|molecules|organisms` (Atomic Design variant)

## Where to Add New Code

**New Backend Module (Bounded Context):**
1. Create `backend/src/modules/{name}/` with four sub-directories: `api/`, `application/`, `domain/`, `infrastructure/`
2. Add `api/dto/` and `infrastructure/models/`, `infrastructure/repositories/`
3. Write domain entities in `domain/` (pure Pydantic, no SQLAlchemy)
4. Write ORM model in `infrastructure/models/{name}_model.py` inheriting from `Base` (`backend/src/shared/domain/base_entity.py`)
5. Create Alembic migration in `backend/alembic/versions/` using raw SQL with `IF NOT EXISTS`
6. Create service in `application/services/{name}_service.py`
7. Create router in `api/{resource}.py`, mount in `backend/src/main.py`
8. Add module docs to `docs/domains/INDEX.md`

**New Backend Endpoint (Existing Module):**
1. Add DTO in `backend/src/modules/{module}/api/dto/`
2. Add service method in `application/services/{name}_service.py`
3. Add route function in `api/{resource}.py`
4. If new DB columns needed, create Alembic migration

**New Frontend Feature:**
1. Create `frontend/src/features/{name}/` with: `components/`, `hooks/`, `types/`, `api/`
2. Create `frontend/src/features/{name}/index.ts` (barrel file — export only public interface)
3. Add API functions using `fetchClient` in `frontend/src/features/{name}/api/index.ts`
4. Create hooks in `hooks/` using TanStack Query (`useQuery`, `useMutation`)
5. Create page at `frontend/src/app/(main)/[tenantId]/(dashboard)/{name}/page.tsx`
6. Page should import from feature barrel only: `import { MyComponent } from '@/features/{name}'`

**New Frontend Component (Within Existing Feature):**
- Place in `frontend/src/features/{feature}/components/{component-name}.tsx`
- Export via feature's `index.ts` if needed by other features
- If shared across multiple features, promote to `frontend/src/components/shared/`

**New UI Primitive:**
- Run `npx shadcn@latest add <component>` inside the frontend container
- File lands in `frontend/src/components/ui/` — do not manually edit

**New Shared Hook:**
- Place in `frontend/src/hooks/{use-name}.ts`
- Export from `frontend/src/hooks/index.ts`

**New API Thin Wrapper (lib-level):**
- Add to `frontend/src/lib/api/{resource}.ts` for cross-feature or page-level use
- For feature-specific API calls, keep inside `frontend/src/features/{name}/api/`

## Special Directories

**`backend/static/`:**
- Purpose: Uploaded files (brand gallery images, etc.) served by FastAPI `StaticFiles`
- Generated: Yes (by upload operations)
- Committed: No (contains user content)

**`backend/alembic/versions/`:**
- Purpose: Database migration history
- Generated: Via `alembic revision` command inside backend container
- Committed: Yes (required for reproducible deployments)

**`backend/scripts/`:**
- Purpose: One-off admin scripts (seeding, data migration, DB sync)
- Not part of app runtime; run manually inside the container

**`frontend/.next/`:**
- Purpose: Next.js build output
- Generated: Yes
- Committed: No

**`frontend/src/stories/`:**
- Purpose: Storybook stories organized by Atomic Design level (atoms/molecules/organisms/tokens)
- Generated: No
- Committed: Yes (design system documentation)

**`frontend/src/pages/`:**
- Purpose: Legacy Next.js Pages Router directory (present but appears unused — App Router is primary)
- Generated: No
- Committed: Yes (but empty or minimal)

**`.planning/`:**
- Purpose: GSD planning documents (codebase maps, phase plans, roadmaps)
- Generated: By GSD tooling
- Committed: Yes

---

*Structure analysis: 2026-03-20*
