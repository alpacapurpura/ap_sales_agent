# Coding Conventions

**Analysis Date:** 2026-03-15

## Naming Patterns

**Backend (Python):**
- Files: `snake_case` (e.g., `offer_service.py`, `brand_repository.py`, `lead_model.py`)
- Classes: `PascalCase` (e.g., `OfferService`, `BrandRepository`, `LeadModel`)
- Functions/Methods: `snake_case` (e.g., `get_settings`, `save_settings`, `patch_offer`)
- Variables: `snake_case` (e.g., `tenant_id`, `offer_type`, `guarantee_type`)
- Constants/Module-level maps: `UPPER_SNAKE_CASE` (e.g., `OFFER_TYPE_TO_DETAILS_MAPPING`, `OFFER_METADATA`)
- Private helpers: prefix with `_` (e.g., `_to_domain`, `_apply_tenant_filter`, `_CHANNEL_CONNECTION_MAP`)

**Frontend (TypeScript):**
- Files: `kebab-case` (e.g., `brand-validation.ts`, `http-client.ts`, `offer-card.tsx`)
- React components: `PascalCase` in both file export and file name (e.g., `OfferCard`, `StrategyCanvas`)
- Hooks: `camelCase` with `use` prefix (e.g., `useBrandSettings`, `useRouter`)
- Utility functions: `camelCase` (e.g., `validateIdentity`, `backendToFrontend`, `getBrandHealth`)
- API objects: `camelCase` with `Api` suffix (e.g., `brandApi`, `offerApi`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MOCK_BACKEND_RESPONSE`, `ENABLE_MOCKS`, `API_URL`)
- Types/Interfaces: `PascalCase` (e.g., `BrandSettings`, `OfferFormValues`, `Offer`)

## Code Style

**Backend Formatting:**
- Tool: Ruff (configured in `backend/pyproject.toml`)
- Line length: 88 characters (Black-compatible)
- Indent: 4 spaces
- Quotes: double quotes for strings
- Target: Python 3.11+
- Lint rules: E4, E7, E9, F (Pyflakes + pycodestyle errors)
- Run: `ruff check src --fix` inside `visionarias_brain_dev` container

**Frontend Formatting:**
- Linting: ESLint with `next/core-web-vitals` ruleset (`frontend/.eslintrc.json`)
- TypeScript: strict mode enabled (`tsconfig.json`)
- No separate Prettier config detected — formatting deferred to ESLint/Next.js defaults

## Import Organization

**Backend (Python):**
1. Standard library imports (`from typing import`, `from uuid import`, `from datetime import`)
2. Third-party imports (`from fastapi import`, `from sqlalchemy import`, `from pydantic import`)
3. Internal imports (`from src.shared.domain import`, `from src.core import`, `from src.modules.X import`)
4. Relative imports within the same module (rare, prefer absolute)

**Frontend (TypeScript):**
1. React/Next.js (`import { useAuth } from "@clerk/nextjs"`)
2. Third-party libs (`import { useQuery } from "@tanstack/react-query"`)
3. Internal aliased imports via `@/` (`import { brandApi } from "@/features/brand/api"`)
4. Relative imports within feature (`import { backendToFrontend } from "./adapter"`)

**Path Aliases:**
- Frontend: `@/` maps to `frontend/src/` (configured in `tsconfig.json`)
- Do NOT use deep relative imports across FSD layers (e.g., `../../features/X` from a page)

## Backend Architecture Patterns

**Domain Layer (`domain/`):**
- Pydantic v2 models extending `BaseEntity` (`from src.shared.domain.base_entity import BaseEntity`)
- `BaseEntity` has `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- Domain models are pure data containers with optional `@model_validator` for business rules
- Optional fields use `Optional[T] = None` or `Optional[T] = Field(None, description="...")`
- Lists default to `Field(default_factory=list)` not `= []`

```python
class BrandSettings(BaseEntity):
    model_config = ConfigDict(extra='ignore')
    identity: Optional[BrandIdentity] = Field(None, description="Visual identity")
    team: Optional[List[KeyFigure]] = Field(default_factory=list, description="Team structure")
```

**Infrastructure Layer (`infrastructure/`):**
- SQLAlchemy models extend `Base` from `src.shared.domain.base_entity`
- Model class names: `XModel` suffix (e.g., `LeadModel`, `TenantModel`, `ProductModel`)
- Table names: `snake_case` plural (e.g., `__tablename__ = "leads"`)
- UUID primary keys: `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- Timestamps: `created_at = Column(DateTime(timezone=True), server_default=func.now())`
- Soft delete: use `deleted_at` / `is_active` pattern (never hard delete)
- JSONB columns for semi-structured data (e.g., `profile_data = Column(JSONB, default={})`)

**Repository Pattern:**
- Constructor injects `db: Session`
- Method `_to_domain(model: XModel) -> DomainEntity` converts ORM to Pydantic
- Tenant isolation enforced in every query: `filter(Model.tenant_id == tenant_id)`
- `BaseRepository` at `src/core/base_repository.py` provides `_apply_tenant_filter` and `_set_tenant`
- SQLAlchemy 2.0 syntax: use `select(Model)` style (legacy `db.query()` still present in older repos)

**Application Layer (`application/`):**
- Service classes with `__init__(self, db: Session)` that instantiate repositories
- Services named `XService` (e.g., `OfferService`, `MetricsService`, `BrandExtractionService`)
- Business logic lives here, not in API or domain

**API Layer (`api/`):**
- FastAPI routers using `APIRouter()`
- Route handlers are `async def`
- Dependencies injected via `Depends()`: `db: Session = Depends(get_db)`, `user: User = Depends(get_current_user)`
- DTOs live in `api/dto/` subdirectory
- Tenant access check: compare `str(resource.tenant_id) != str(user.tenant_id)` before operating

## Frontend Architecture Patterns

**Feature-Sliced Design (FSD):**
- Layer order (low to high): `shared` → `entities` → `features` → `widgets` → `pages`
- No upward imports: a `feature` must not import from `widgets` or `pages`
- Each feature has structure: `components/`, `hooks/`, `api/`, `types/`, `utils/`
- Barrel exports via `index.ts` at feature root (e.g., `src/features/offer-studio/index.ts`)

**Hooks:**
- Data fetching hooks use `@tanstack/react-query` (`useQuery`, `useMutation`)
- Hook returns `{ data, isLoading, error, mutate }` shaped objects
- Cache keys are string arrays: `queryKey: ['brand-settings']`
- `staleTime` set to 5 minutes for settings data

**API Client Pattern:**
- All fetch calls go through `fetchClient` at `src/lib/http-client.ts`
- `fetchClient` auto-injects `X-Tenant-ID` header from URL path segment
- `fetchClient` handles 401 (redirect to `/sign-in`) and 403 (redirect to `/forbidden`)
- Feature-specific API modules export an object (e.g., `brandApi`, `offerApi`) with typed methods
- Adapter pattern: `backendToFrontend()` and `frontendToBackend()` in `api/adapter.ts` per feature

**Mock Data:**
- Mock flag: `ENABLE_MOCKS` imported from `src/lib/mock-config.ts`
- Mock data files: `api/mock-data.ts` within each feature
- Feature APIs check `USE_MOCK_DATA` before making real requests

## Error Handling

**Backend:**
- API errors: `raise HTTPException(status_code=X, detail="message")` directly in route handlers
- 404: resource not found or tenant mismatch (security-conscious — don't reveal existence)
- 401: invalid auth token or webhook secret
- 403: tenant inactive or forbidden
- 500: repository failures (e.g., `"Failed to delete avatar"`)
- Domain/application errors: `raise ValueError("message")` — caught and converted at API boundary
- Structlog used for structured logging: `logger = structlog.get_logger()`
- Context binding: `structlog.contextvars.bind_contextvars(tenant_id=str(tenant.id))`

**Frontend:**
- API errors caught with `try/catch` in hooks and API modules
- User-facing errors via `toast.error("message")` from `sonner`
- Silent catch `try { ... } catch {}` used in mutation callbacks (not recommended but present)
- `fetchClient` silently handles 401/403 via redirects — no thrown errors

## Logging

**Backend Framework:** `structlog` (configured at `src/core/logger.py`)

**Usage:**
```python
import structlog
logger = structlog.get_logger()

# Bind context vars (per-request)
structlog.contextvars.bind_contextvars(tenant_id=str(tenant.id))

# Log events
logger.info("event_name", key="value")
```

**Frontend:** `console.log` / `console.error` for debug — no structured logging library.

## Comments

**Backend:**
- Docstrings on class definitions explaining purpose and storage (e.g., `"""Configuration for the Brand Identity..."""`)
- Inline comments explain non-obvious logic (e.g., `# Fix known legacy types`, `# Scope filtering moved to Repo`)
- Spanish comments acceptable in domain code (codebase uses both EN/ES)

**Frontend:**
- JSDoc not consistently used; inline `//` comments for intent
- Mock flags and debug logs often include emoji (e.g., `"🔸 Using Mock Data"`) — avoid in new code

## Module Design

**Backend:**
- Each bounded context is a self-contained module under `backend/src/modules/X/`
- Standard layout: `domain/`, `infrastructure/`, `application/`, `api/`
- Cross-module imports allowed but should go domain → domain only; never infrastructure → infrastructure across modules
- `__init__.py` used to re-export key domain entities

**Frontend:**
- Feature barrels (`index.ts`) export only public API of the feature
- Internal components not exported from barrel (they are `feature/components/X`)
- Types exported via `types/index.ts` within each feature

## Tenant Isolation (Critical)

- Every backend query MUST filter by `tenant_id`
- Every API route that accesses tenant data MUST use `user: User = Depends(get_current_user)` and check `user.tenant_id`
- Frontend MUST include `X-Tenant-ID` header (handled automatically by `fetchClient`)
- Context variable `_tenant_id_ctx` at `src/core/context.py` propagates tenant ID across async context

---

*Convention analysis: 2026-03-15*
