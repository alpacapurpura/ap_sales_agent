# Architecture

**Analysis Date:** 2026-03-15

## Pattern Overview

**Overall:** Modular Monolith with Domain-Driven Design (DDD)

**Key Characteristics:**
- Single deployable backend unit (`visionarias_brain_dev`) composed of ~13 bounded-context modules
- Each module owns its domain layer, application layer, infrastructure layer, and API layer independently
- Frontend is a Next.js 14 App Router SPA following Feature-Sliced Design (FSD)
- All API calls are multitenant: every request carries `X-Tenant-ID` header; tenant context propagated via Python `ContextVar`
- Separate admin Streamlit dashboard (`visionarias_admin_dev`) shares the backend Docker image

## Backend Layers (per module)

**Domain Layer:**
- Purpose: Pure business logic — entities, aggregates, value objects, enums. No I/O.
- Location: `backend/src/modules/{module}/domain/`
- Contains: Pydantic `BaseEntity` subclasses, domain aggregates, enums, identity types
- Depends on: `src/shared/domain/base_entity.py` (provides `BaseEntity` and SQLAlchemy `Base`)
- Used by: Application layer, Infrastructure repositories

**Infrastructure Layer:**
- Purpose: Persistence adapters — SQLAlchemy ORM models, repositories, external integrations, prompts
- Location: `backend/src/modules/{module}/infrastructure/`
- Contains: ORM models (`infrastructure/models/`), repository classes (`infrastructure/repositories/`), external connectors, prompt files
- Depends on: Domain layer, `src/core/database.py`, `src/shared/infrastructure/`
- Used by: Application layer

**Application Layer:**
- Purpose: Use cases, services, AI orchestration. Coordinates domain + infrastructure.
- Location: `backend/src/modules/{module}/application/`
- Contains: Service classes, DTOs (`application/dto/`), LangGraph agent graphs (`application/agents/`, `application/orchestrator/`)
- Depends on: Domain layer, Infrastructure layer
- Used by: API layer

**API Layer:**
- Purpose: FastAPI routers — request/response handling, dependency injection, DTO validation
- Location: `backend/src/modules/{module}/api/`
- Contains: FastAPI `APIRouter` instances, Pydantic request/response DTOs (`api/dto/`), route handlers
- Depends on: Application layer, `src/modules/iam/api/dependencies.py` for auth/tenant
- Used by: `src/main.py` (router registration)

## Frontend Layers (Feature-Sliced Design)

**App Layer (Pages/Routing):**
- Purpose: Next.js App Router pages — thin wrappers that import from features
- Location: `frontend/src/app/`
- Pattern: Route groups `(main)`, `(landing)` with `[tenantId]` path params. Pages are 10–15 lines; they simply render a feature component.
- Example: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-settings/page.tsx` renders `<BrandSettingsPage />` from features

**Features Layer:**
- Purpose: Self-contained vertical slices — each feature owns API client, hooks, components, types
- Location: `frontend/src/features/{feature}/`
- Subdirectories per feature: `api/`, `hooks/`, `components/`, `types/`, optional `utils/`, `config/`, `sections/`
- Rule: Features do NOT import from other features (no horizontal coupling)

**Shared/Components Layer:**
- Purpose: Cross-cutting UI primitives and layout
- Location: `frontend/src/components/` — `ui/` (Shadcn), `shared/layout/` (sidebar, app chrome), `providers/`, `auth/`
- Location: `frontend/src/lib/` — `http-client.ts`, `config.ts`, `mock-config.ts`, `utils/`

## Core Shared Backend Infrastructure

**`src/core/`:**
- `config.py` — Settings (Pydantic BaseSettings, env-driven)
- `database.py` — SQLAlchemy session factory, `get_db` dependency, `init_db()`
- `context.py` — `ContextVar[UUID]` for tenant ID propagation (`get_tenant_id`, `set_tenant_id`)
- `logger.py` — Structlog configuration
- `base_repository.py` — `BaseRepository` with `_apply_tenant_filter()` and `_set_tenant()` helpers
- `exceptions.py` — Shared exception types
- `security.py` — Auth utilities

**`src/shared/`:**
- `domain/base_entity.py` — `BaseEntity` (Pydantic), SQLAlchemy `Base` (declarative)
- `infrastructure/llm/` — LLM factory and providers
- `infrastructure/database/` — DB types
- `infrastructure/channels/` — Shared channel abstractions
- `infrastructure/external/` — Shared external service clients
- `infrastructure/files/` — File handling utilities

## Data Flow

**Standard API Request (Authenticated):**

1. Clerk JWT arrives in `Authorization: Bearer` header; `X-Tenant-ID` in separate header
2. FastAPI middleware logs request; `get_tenant_context` dependency runs
3. `get_user_from_token` in `src/modules/iam/api/dependencies.py` verifies JWT with Clerk, resolves `User` from DB
4. `get_current_user` resolves and validates tenant membership, sets `user.tenant_id`
5. `get_tenant_context` calls `set_tenant_id(tenant_id)` to store in `ContextVar`
6. Router handler instantiates Application Service, passes `db` and `user.tenant_id`
7. Service calls Infrastructure Repository; repository applies tenant filter via `_apply_tenant_filter()`
8. Domain entities returned to API layer, serialized to Pydantic response DTO
9. JSON response sent to frontend

**Frontend API Call Flow:**

1. React component calls hook (e.g., `useBrandSettings`)
2. Hook uses TanStack Query (`useQuery`/`useMutation`) with Clerk token via `getToken()`
3. Feature API module calls `fetchClient()` from `src/lib/http-client.ts`
4. `fetchClient` auto-injects `X-Tenant-ID` (extracted from URL pathname segment 0) and `Authorization` header
5. Response mapped from snake_case (backend) to camelCase (frontend) in API module
6. `fetchClient` intercepts 401 (redirect to `/sign-in`) and 403 (redirect to `/forbidden`)

**AI Agent Flow (Sales Agent):**

1. Incoming message arrives via Connections webhook (WhatsApp/Telegram/ManyChat)
2. `src/modules/connections/` routes to `src/modules/sales_agent/application/orchestrator/graph.py`
3. LangGraph `StateGraph` supervisor routes to `sales_agent` subgraph
4. Sales subgraph runs agent nodes, reads memory from Qdrant (RAG), writes to PostgreSQL
5. Response sent back through originating channel

**State Management (Frontend):**
- Server state: TanStack Query (React Query) — all API calls use `useQuery`/`useMutation` with query keys
- Local UI state: React `useState` within components
- No global state stores (no Redux, no Zustand detected)

## Key Abstractions

**Module (Backend):**
- Purpose: Bounded context owning all four layers independently
- Examples: `backend/src/modules/brand/`, `backend/src/modules/analytics/`, `backend/src/modules/sales_agent/`
- Pattern: Every module has `domain/` → `infrastructure/` → `application/` → `api/`; registered in `src/main.py`

**BaseRepository:**
- Purpose: Tenant-aware persistence base class
- Location: `backend/src/core/base_repository.py`
- Pattern: `_apply_tenant_filter(query, model)` reads from `ContextVar`; all concrete repos extend this

**BaseEntity:**
- Purpose: Pydantic model base for all domain objects
- Location: `backend/src/shared/domain/base_entity.py`
- Pattern: `ConfigDict(from_attributes=True)` enables ORM → Pydantic conversion

**Feature Slice (Frontend):**
- Purpose: Vertical self-contained unit of UI functionality
- Examples: `frontend/src/features/brand/`, `frontend/src/features/marketing-studio/`, `frontend/src/features/offer-studio/`
- Pattern: Each slice exports `api/index.ts`, `hooks/`, `components/`, `types/index.ts`; page just renders the top-level feature component

**fetchClient:**
- Purpose: Tenant-aware HTTP client wrapper
- Location: `frontend/src/lib/http-client.ts`
- Pattern: Wraps native `fetch`; reads tenant from URL path[0]; injects `X-Tenant-ID` and handles 401/403 globally

**LangGraph Agent:**
- Purpose: AI workflow execution for Sales Agent and Copilot
- Examples: `backend/src/modules/sales_agent/application/orchestrator/graph.py`, `backend/src/modules/copilot/application/agents/`
- Pattern: `StateGraph` with typed state, supervisor node routes to sub-agent subgraphs

## Entry Points

**Backend:**
- Location: `backend/src/main.py`
- Triggers: `uvicorn src.main:app --host 0.0.0.0 --port 8000` (Docker CMD)
- Responsibilities: Creates FastAPI app, configures CORS/middleware/logging, registers all module routers under `/api/v1/{domain}/`

**Admin Dashboard:**
- Location: `backend/src/admin/app.py`
- Triggers: Streamlit run command (separate Docker service `visionarias_admin_dev`)
- Responsibilities: Internal tenant/user management UI

**Frontend:**
- Location: `frontend/src/app/layout.tsx` (root), `frontend/src/middleware.ts` (auth gate)
- Triggers: Next.js server; middleware runs on every non-static request
- Responsibilities: `middleware.ts` protects routes via Clerk; root layout wraps app in providers

## Error Handling

**Strategy:** HTTP status codes + structured logging (structlog)

**Patterns:**
- 401: Clerk token invalid/expired → `get_user_from_token` raises `HTTPException(401)`; frontend `fetchClient` redirects to `/sign-in`
- 403: Tenant access denied → `get_current_user` raises `HTTPException(403)`; frontend `fetchClient` redirects to `/forbidden`
- 404: Resource not found → domain services return `None`; API layer raises `HTTPException(404)`
- Unhandled exceptions caught by HTTP middleware in `main.py` → structlog `error` with full traceback

## Cross-Cutting Concerns

**Logging:** Structlog with contextvars. `request_id` and `tenant_id` bound per request via HTTP middleware in `src/main.py`. All service classes use `structlog.get_logger()`.

**Validation:** Pydantic v2 at API boundaries (request DTOs, response models). Domain entities are Pydantic `BaseEntity` subclasses.

**Authentication:** Clerk JWTs. Backend verifies via `src/modules/iam/application/auth.py`. Frontend uses `@clerk/nextjs` middleware and `useAuth()` hook.

**Tenant Isolation:** `ContextVar` in `src/core/context.py`. Set by `get_tenant_context` dependency on every protected router. All queries must call `_apply_tenant_filter()` from `BaseRepository`.

**Mocking:** Frontend has a `ENABLE_MOCKS` flag in `src/lib/mock-config.ts`. Feature API modules check this flag and return local mock data (in `*-mock-data.ts` files). Allows UI development without backend.

---

*Architecture analysis: 2026-03-15*
