# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Modular Monolith with Domain-Driven Design (DDD) + Feature-Sliced Design (FSD)

**Key Characteristics:**
- Single deployable unit (Docker Compose) containing a FastAPI backend and Next.js 14 frontend
- Backend is partitioned into 13 bounded contexts under `backend/src/modules/`, each enforcing strict layer separation
- Frontend is partitioned into feature slices under `frontend/src/features/`, each exposing a public API via `index.ts`
- Multitenancy is mandatory — every authenticated request carries an `X-Tenant-ID` header resolved to a UUID; a Python `ContextVar` propagates it across async boundaries
- AI agent workflows (LangGraph) are first-class citizens in the `application` layer of relevant modules

## Backend Layers

The prescribed layer order (outside-in for requests, inside-out for building) is:

```
api/ → application/ → domain/ → infrastructure/
```

**`api/` — Interface/Transport Layer:**
- Purpose: FastAPI routers, Pydantic DTO validation, dependency injection wiring
- Location: `backend/src/modules/{module}/api/`
- Contains: `router.py` (or resource-named files), `dto/` sub-folder for request/response schemas, `dependencies.py`
- Depends on: `application/` services and `domain/` types
- Used by: FastAPI app (`backend/src/main.py`)
- Rule: No business logic or DB queries here

**`application/` — Use Cases / Orchestration Layer:**
- Purpose: Business logic, AI agent graphs, orchestrators
- Location: `backend/src/modules/{module}/application/`
- Contains: `services/`, `agents/` (LangGraph), `orchestrators/`
- Depends on: `domain/` entities, `infrastructure/` repositories (injected)
- Used by: `api/` layer

**`domain/` — Pure Business Rules:**
- Purpose: Entities, enums, domain events, exceptions. Zero dependencies on infrastructure.
- Location: `backend/src/modules/{module}/domain/`
- Contains: Pydantic models (not ORM), enums, domain event dataclasses
- Depends on: Nothing (or `shared/domain/`)
- Used by: All other layers

**`infrastructure/` — Technical Implementations:**
- Purpose: SQLAlchemy ORM models, repositories, external API clients, prompt loaders
- Location: `backend/src/modules/{module}/infrastructure/`
- Contains: `models/`, `repositories/`, `external/`, `prompts/`
- Depends on: `domain/` (translates to/from ORM)
- Used by: `application/` layer

## Frontend Layers

**`app/` — Routing Only:**
- Purpose: Next.js App Router file-system routing. Layouts and page entry points only.
- Location: `frontend/src/app/`
- Contains: `page.tsx` (entry), `layout.tsx`, route group folders `(main)`, `(landing)`
- Rule: Minimal logic. Pages import from `features/`, pass data as props.

**`features/` — Feature Slices:**
- Purpose: Self-contained business domain implementations. Deleting a feature should not break the build.
- Location: `frontend/src/features/{domain}/`
- Contains: `components/`, `hooks/`, `types/`, `api/`, `utils/`
- Exports: Only via `index.ts` barrel file (public API contract)
- Rule: Cross-feature imports must go through the barrel `index.ts`, never direct deep imports

**`components/` — Shared UI:**
- Purpose: Global UI primitives and layout components
- Location: `frontend/src/components/`
- Contains: `ui/` (Shadcn primitives — do not modify), `shared/layout/` (Sidebar, navigation), `auth/`, `providers/`

**`lib/` — Infrastructure/Utilities:**
- Purpose: API clients, config, shared utilities
- Location: `frontend/src/lib/`
- Contains: `api/` (per-domain fetch wrappers), `http-client.ts` (fetch interceptor), `config.ts`, `utils/`, `constants/`

## Data Flow

**Authenticated API Request (Backend):**

1. HTTP request arrives at FastAPI with `Authorization: Bearer <token>` and `X-Tenant-ID: <uuid>` headers
2. `get_tenant_context` dependency in `backend/src/modules/iam/api/dependencies.py` verifies the Clerk JWT, resolves the user from the DB, validates user membership in the target tenant, and sets `tenant_id` on the `User` object and in the Python `ContextVar` (`backend/src/core/context.py`)
3. Router function calls an application service or AI orchestrator, passing `user.tenant_id`
4. Service applies business rules, calls repositories with `tenant_id` filter
5. Repository executes SQLAlchemy 2.0 `select(Model)` queries filtered by `tenant_id`
6. Results travel back as domain entities or Pydantic DTOs; never raw ORM objects past the repository boundary

**Frontend Client Request:**

1. User navigates to a tenant-scoped URL `/{tenantId}/...`
2. `frontend/src/middleware.ts` runs `clerkMiddleware`, protects non-public routes, injects `x-current-path` header
3. `frontend/src/app/providers.tsx` reads the Clerk user's `tenant_id` from `publicMetadata` and stores it in `localStorage`
4. Page component (Server Component or Client Component) uses a feature hook (e.g., `useBrandSettings`)
5. Feature hook calls a `brandApi.*` function from `frontend/src/features/brand/api/index.ts`
6. API function calls `fetchClient` (`frontend/src/lib/http-client.ts`), which automatically injects `X-Tenant-ID` from the URL path and `Authorization: Bearer <token>` from Clerk
7. Response is managed via TanStack Query cache; UI updates optimistically or on `onSuccess`

**AI Agent Conversation Flow (Sales Agent):**

1. Incoming webhook (Telegram/WhatsApp/etc.) hits a `connections` router
2. Router dispatches to `ChatOrchestrator` (`backend/src/modules/sales_agent/application/orchestrator/chat.py`)
3. Orchestrator resolves the tenant connection, sets tenant context, identifies/creates the lead via CRM `IdentityService`
4. `LangGraph` compiled graph (`agent_app`) is invoked with `AgentState` (message history, lead profile, tenant knowledge)
5. Graph nodes execute: supervisor → sales agent subgraph → response nodes
6. Output is routed back to the correct channel via `OutputManager`
7. `LeadCapturedEvent` or other domain events are published to `EventBus` (`backend/src/shared/domain/events.py`), which dispatches handlers after DB commit

**Cross-Module Communication (EventBus):**

- Modules do NOT import from each other directly
- Cross-module side effects use `EventBus.publish(event, session=db)` from `backend/src/shared/domain/events.py`
- Handlers register at startup in `backend/src/main.py` via `register_event_handlers()`
- Example: `sales_agent` publishes `LeadCapturedEvent`; `analytics` or `crm` module handles it

## Key Abstractions

**Tenant Context (Backend):**
- `ContextVar[Optional[UUID]]` in `backend/src/core/context.py`
- Set by `get_tenant_context` FastAPI dependency before any business logic runs
- All services receive `tenant_id` as an explicit parameter; never read globally

**`X-Tenant-ID` Header (Frontend):**
- Injected by `fetchClient` in `frontend/src/lib/http-client.ts` by parsing the first path segment of the URL
- Falls back to `localStorage` if URL parsing yields a global route name

**LLMFactory (Shared AI):**
- `backend/src/shared/infrastructure/llm/factory.py`
- Singleton for platform key; creates per-tenant instances when tenants supply their own OpenAI/Gemini keys
- All AI-consuming modules call `LLMFactory.get_service_for_tenant(tenant)` — never instantiate providers directly

**EventBus (Cross-Module):**
- `backend/src/shared/domain/events.py`
- In-process, class-level handler registry
- Deferred dispatch after SQLAlchemy session commit (prevents partial-write inconsistencies)

**TanStack Query Cache (Frontend):**
- Feature hooks use `useQuery` / `useMutation` from `@tanstack/react-query`
- `QueryClient` is provided globally in `frontend/src/app/providers.tsx`
- Cache keys are per-feature (e.g., `['brand-settings']`, `['offers']`)

**PromptLoader:**
- `backend/src/modules/copilot/infrastructure/prompts/base.py`
- Loads Jinja2 prompt templates from `templates/` subdirectories
- Intended to be the standard mechanism; some modules still have hardcoded prompts (see CONCERNS.md)

## Entry Points

**Backend:**
- `backend/src/main.py` — FastAPI application factory; mounts all routers under `/api/v1/`; registers startup handlers; configures CORS and structlog middleware

**Frontend:**
- `frontend/src/app/(main)/layout.tsx` — Root shell for authenticated app
- `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` — Dashboard shell: `AppSidebar` + responsive main area
- `frontend/src/middleware.ts` — Edge middleware: Clerk auth enforcement + header injection

**AI Agents:**
- `backend/src/modules/sales_agent/application/orchestrator/graph.py` — Compiled LangGraph `agent_app` (supervisor → sales subgraph)
- `backend/src/modules/copilot/application/agents/web_extractor/graph.py` — Web extraction pipeline for brand auto-fill

## Error Handling

**Backend Strategy:** HTTP exceptions propagated from service or dependency layers; structlog logs every request/response with `request_id` and `tenant_id` context variables.

**Frontend Strategy:**
- `fetchClient` intercepts 403 (redirects to `/forbidden`) and 401 (redirects to `/sign-in`)
- Feature hooks surface errors through TanStack Query `error` state; pages render inline error UI with retry

## Cross-Cutting Concerns

**Logging:** `structlog` with context variables (`request_id`, `tenant_id`); configured globally in `backend/src/core/logger.py`

**Validation:** Pydantic v2 on backend (DTOs + domain entities); TypeScript interfaces + occasional Zod on frontend

**Authentication:** Clerk JWT on both sides. Backend verifies via `verify_clerk_token` in `backend/src/modules/iam/application/auth.py`. Frontend uses `@clerk/nextjs` SDK.

**Multitenancy Enforcement:** Every protected router includes `Depends(get_tenant_context)` in `backend/src/main.py`. Repositories must filter by `tenant_id` on all queries.

**Soft Deletes:** All persistent models use `deleted_at` or `is_active` — hard deletes are forbidden.

---

## Architecture Deviations vs. Reference Standards

The following gaps exist between actual code and the north-star architecture documented in `.trae/skills/`:

1. **Hardcoded prompts in `sales_agent`:** The `infrastructure/prompts/templates/legacy/` directory contains hardcoded `.j2` templates not loaded through the `PromptLoader` system. The reference standard requires all prompts to go through `PromptLoader`. (See `backend/src/modules/sales_agent/infrastructure/prompts/templates/legacy/`)

2. **No barrel files on many features:** `frontend/src/features/offer-studio/index.ts` only exports `./types`, not components or hooks. `frontend/src/features/brand/` has no `index.ts` at all. The FSD standard requires every feature to export only through `index.ts`. Deep imports from pages currently bypass this contract.

3. **Pages use `'use client'` wholesale:** `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-settings/page.tsx` is a full Client Component. The reference standard requires pages to be Server Components by default, pushing `'use client'` down to the smallest interactive boundary.

4. **Legacy SQLAlchemy 1.x queries in dependencies:** `backend/src/modules/iam/api/dependencies.py` uses `db.query(UserModel).filter(...)` — the legacy Session.query() syntax. The standard mandates SQLAlchemy 2.0 syntax (`select(Model)`).

5. **`sales_agent/infrastructure/` has non-standard sub-directories:** Contains `db/models/`, `db/repositories/` alongside `infrastructure/models/` and `infrastructure/repositories/`. The reference standard calls for a flat `models/` and `repositories/` directly under `infrastructure/`.

6. **`analytics` module DTOs live in `application/dto/`:** The reference architecture places DTOs in `api/dto/`. In `analytics`, they are in `application/dto/` which creates an inconsistency with all other modules.

7. **`sales` feature uses Atomic Design internally:** `frontend/src/features/sales/components/atoms/`, `molecules/`, `organisms/`. The FSD cheatsheet explicitly does not enforce these sub-layers, preferring a flat `components/` directory. This is an internally-consistent deviation but non-standard.

---

*Architecture analysis: 2026-03-20*
