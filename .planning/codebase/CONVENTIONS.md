# Coding Conventions

**Analysis Date:** 2026-03-20

> This document cross-references actual codebase patterns with the desired standards
> defined in `.trae/skills/backend-expert/references/standards.md` and
> `.trae/skills/frontend-expert/references/component-rules.md`.
> Deviations are marked with ⚠️.

---

## Backend (Python / FastAPI)

### Language & Runtime

- Python 3.11+, enforced via `pyproject.toml` `target-version = "py311"`.
- All I/O-bound operations use `async def` (FastAPI endpoints, DB access, external HTTP calls).
  - Most API layer functions are `async def`. Some service/repo layer functions remain sync
    (`Session` not `AsyncSession`) — this is an architectural inconsistency (see CONCERNS.md).

### Linting & Formatting

- **Tool:** `ruff`
- **Config:** `backend/pyproject.toml` — line length 88, Black-style quotes (double), spaces.
- **Enabled rules:** `E4`, `E7`, `E9`, `F` (Pyflakes + pycodestyle errors).
- **Run command (in Docker):** `docker exec -it visionarias_brain_dev ruff check src --fix`
- Stricter rules (isort, type annotation checks) are NOT enabled in ruff yet.

### Naming Patterns

**Files:**
- `snake_case.py` throughout.
- Router files: `{noun}.py` (e.g., `leads.py`, `products.py`, `calendar.py`).
- Service files: `{noun}_service.py`.
- Repository files: `{noun}_repository.py` or `{noun}_metrics_repository.py`.
- DTO files live in `api/dto/` subdirectory.

**Functions & Methods:**
- `snake_case` always.
- Repository methods: `get_by_*`, `list_*`, `save`, `update`, `delete`.
- Service methods: verb-first, e.g., `get_sales_metrics`, `create_offer`, `patch_offer`.

**Classes:**
- `PascalCase` always.
- Domain models: plain name (e.g., `Lead`, `Offer`, `User`).
- SQLAlchemy ORM models: `{Name}Model` suffix (e.g., `LeadModel`, `ProductModel`).
- Pydantic DTOs: descriptive suffix (e.g., `ProductCreate`, `ProductUpdate`, `SalesHeaderKpisDTO`).

**Variables & Constants:**
- `snake_case` for variables.
- `UPPER_SNAKE_CASE` for module-level constants (e.g., `EVENT_SCORES`, `LOW_CONVERSION_THRESHOLDS`, `PROFILE_SAFE`).

### Type Hints

- **Desired:** All functions must have return type annotations.
- **Actual:** Return type annotations are present on most public methods but coverage is incomplete in infrastructure layer.
  - Correct pattern: `def calculate_score(self, profile_id: UUID) -> int:`
  - Use native generics (`list[str]`, `dict[str, Any]`) or `Optional`, `List` from `typing` — both styles coexist.
- ⚠️ **Deviation:** Some infrastructure functions lack return annotations.

### Pydantic V2

- `BaseModel` from Pydantic V2 is used throughout.
- **Correct pattern:** `model_config = ConfigDict(...)` — used in `brand`, `offer`, and `iam` domain models.
- ⚠️ **Deviation:** A few legacy files still use `class Config:` inner class:
  - `backend/src/modules/offer/api/dto/offer_gallery.py`
  - `backend/src/modules/sales_agent/domain/events.py`
  - `backend/src/modules/crm/api/dto/cdp.py`
- `model_dump(exclude_unset=True)` is correctly used for PATCH operations.
- `model_validate` is used over `from_orm` (no `from_orm` calls found).

### Error Handling

- **API layer:** `HTTPException` from FastAPI is the standard for controlled errors.
- **Domain exceptions:** Custom exceptions should live in `src/shared/domain/exceptions.py` per the standard — partially implemented.
- **Pattern for resource not found:**
  ```python
  if not product or str(product.tenant_id) != str(user.tenant_id):
      raise HTTPException(status_code=404, detail="Product not found")
  ```
- **Pattern for invalid input:**
  ```python
  try:
      lead = service.get_lead(UUID(lead_id))
  except ValueError:
      raise HTTPException(status_code=400, detail="Invalid UUID format")
  ```

### Logging

- **Desired:** `structlog` exclusively. No `print()`, no `logging.getLogger`.
- **Actual pattern (correct):**
  ```python
  import structlog
  logger = structlog.get_logger()
  logger.warning("unknown_extraction_profile", requested=name, fallback="safe")
  ```
- ⚠️ **Deviation:** Multiple infrastructure files still use standard `logging` module:
  - `backend/src/modules/connections/infrastructure/channels/gmail.py`
  - `backend/src/modules/connections/infrastructure/channels/telegram.py`
  - `backend/src/modules/connections/infrastructure/channels/youtube.py`
  - `backend/src/modules/iam/application/auth.py` — uses `logging.getLogger(__name__)`
  - `backend/src/shared/domain/events.py`
- ⚠️ **Deviation:** One `print()` call in `backend/src/shared/infrastructure/llm/providers/openai.py:157`.
- Scripts in `backend/scripts/` use `print()` intentionally (acceptable for CLI scripts).

### Environment & Config

- Centralized in `src/core/config.py` using `pydantic-settings`.
- Accessed as `from src.core.config import settings`.
- ⚠️ **Deviation:** `backend/src/modules/iam/application/auth.py` reads `os.getenv()` directly instead of using `settings`.

### Async/Sync Consistency

- **Desired:** All DB access should be async.
- ⚠️ **Deviation:** Most service and repository layers use synchronous `Session` from `sqlalchemy.orm`,
  not `AsyncSession`. API endpoints are `async def` but call sync services.
  This is widespread — see `backend/src/modules/offer/application/offer_service.py`,
  `backend/src/modules/crm/application/services/lead_service.py`, etc.

---

## Frontend (TypeScript / Next.js)

### Language & Runtime

- TypeScript with strict mode (`frontend/tsconfig.json`).
- Next.js 14+ App Router.
- React 18+.

### Linting & Formatting

- **ESLint:** `next/core-web-vitals` (`frontend/.eslintrc.json`).
- **Pre-commit hook:** `husky` → `lint-staged` runs ESLint fix + `tsc --noEmit` on all `.ts`/`.tsx` files.
- No Prettier config found — formatting is handled by ESLint rules only.
- **Lint commands:** `npm run lint` / `npm run lint:fix` (inside container).

### Naming Patterns

**Files:**
- React components: `kebab-case.tsx` (e.g., `sales-dashboard.tsx`, `brand-nav-rail.tsx`).
- Hooks: `use-kebab-case.ts` (e.g., `use-offer.ts`, `use-debounce.ts`).
- Types/utilities: `kebab-case.ts` (e.g., `brand-validation.ts`, `section-helpers.ts`).
- API modules: `kebab-case.ts` in `src/lib/api/` (e.g., `leads.ts`, `connections.ts`).

**Components & Types:**
- Component functions: `PascalCase` (e.g., `SalesDashboard`, `BrandNavRail`).
- Props interfaces: `{ComponentName}Props` convention.
- Hooks: `use{PascalCase}` (e.g., `useBrandSettings`, `useOfferMetadata`).
- API objects: `{noun}Api` (e.g., `brandApi`, `offerApi`, `myFeatureApi`).

### Component Structure

- **Preferred export:** Named function exports (e.g., `export function SalesDashboard()`).
- **`"use client"` directive:** Present on all interactive components — 124 instances in features.
- ⚠️ **Deviation:** The component template in `.trae/skills/frontend-expert/assets/templates/component.tsx`
  prescribes `forwardRef` for all feature components. In practice, `forwardRef` is used only in `src/components/ui/`
  (Shadcn, 81 instances) and NOT in `src/features/` (0 instances). Feature components use simple arrow functions.
- Props are typed with `interface` or `type` — consistently applied.
- Desestructuring of props in function signature — generally followed.

### Styling (Tailwind CSS)

- **Tailwind CSS** is the sole styling approach.
- `cn()` utility (clsx + twMerge) from `@/lib/utils` is used for conditional/dynamic classes — 140+ usages in features.
- ⚠️ **Deviation:** `style={{...}}` inline styles are used in 84 places, primarily in:
  - `frontend/src/features/brand/sections/visuals/visuals-preview.tsx` — uses dynamic colors/fonts
    that cannot be expressed as static Tailwind classes (e.g., `fontFamily`, `backgroundColor` from user data).
  - This is a legitimate exception for dynamic design tokens, but should be documented.
- Shadcn UI components from `src/components/ui/` are reused before creating primitives from scratch.

### State & Effects

- `useState` and `useEffect` are used extensively (367 and 108 instances in features, respectively).
- React Query (`@tanstack/react-query`) is the standard for server state — hooks follow the
  `useQuery` + `useMutation` pattern with `queryKey`, `queryFn`, `staleTime`.
- Forms: `react-hook-form` + `zod` schemas (`frontend/src/features/offer-studio/types/schema.ts`).
- ⚠️ **Deviation vs desired:** Many hooks still sync derived state with `useEffect` in some places.
  The desired pattern is inline derivation (compute at render time without useEffect).

### Data Fetching & API Layer

- **HTTP client:** `fetchClient` from `@/lib/http-client` — wraps native `fetch` with:
  - `X-Tenant-ID` auto-injection from URL first segment, localStorage fallback.
  - 401 → redirect to `/sign-in`.
  - 403 → redirect to `/forbidden`.
- ⚠️ **Deviation:** `fetchClient` does NOT inject cache partitioning (`?_t=<tenantId>`) as documented
  in `api-standards.md`. The actual implementation only injects `X-Tenant-ID` header.
- **API definition pattern:** `src/lib/api/{feature}.ts` exports a plain object `{noun}Api` with async methods.
  Each method receives `token: string` as explicit argument and calls `fetchClient`.
- **Auth pattern:** `useAuth().getToken()` in hooks, token passed explicitly to API functions.
- **Mock data:** Both `brandApi` and `offerApi` support a `USE_MOCK_API` flag from `@/lib/mock-config` —
  controlled by `ENABLE_MOCKS` constant. Enables offline UI development.

### Logging (Frontend)

- ⚠️ **Deviation:** 165 `console.log/error/warn` calls exist in `src/features/` (no structured logging).
  Heavy use of `[BrandAPI]`, `[useBrandSettings]` prefixed console logs for debugging — not removed after development.
  Should be replaced with a structured logger or removed before production.

### Navigation & Images

- ⚠️ **Partial deviation:** 16 raw `<a>` tags and 13 raw `<img>` tags found in features (should use
  `next/link` and `next/image`). Only 6 `next/link` imports and 9 `next/image` imports used.

### Import Organization

**Typical order observed:**
1. React / Next.js core (`react`, `next/link`, `next/image`)
2. Third-party libraries (`@clerk/nextjs`, `@tanstack/react-query`, `sonner`)
3. Internal `@/components/ui/` (Shadcn)
4. Internal `@/features/` or `@/lib/`
5. Local relative imports

**Path Aliases:**
- `@/` → `./src/` (configured in `tsconfig.json` and `vitest.config.mts`).

### Module Design

- **Barrel files (`index.ts`):** Present in most features for re-exporting types:
  - `src/features/offer-studio/index.ts` — re-exports `./types`.
  - `src/features/brand/types/index.ts` — all brand type exports.
- Feature API files (`src/features/{feature}/api/index.ts`) export the API object and types.
- `src/lib/api/` holds cross-feature API modules used by multiple features.

### Comments

- JSDoc comments are used sparingly — mostly on API method objects in `src/lib/api/`.
- Backend uses inline comments heavily in Spanish for logic explanations.
- Frontend uses English for JSDoc but Spanish for UI-facing text/labels.

---

*Convention analysis: 2026-03-20*
