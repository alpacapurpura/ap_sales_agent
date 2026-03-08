---
name: front-back-integrator
description: Expert in validating and testing frontend-backend integrations in a multi-tenant environment (Next.js + FastAPI). Use when implementing new features, refactoring APIs, or troubleshooting data flow issues to ensure correct tenant context propagation, data type consistency, and error handling.
---

# Front-Back Integrator Skill

This skill specializes in auditing and verifying the integration between the Frontend (Next.js) and Backend (FastAPI) in the Visionarias Brain architecture. It ensures that the multi-tenant context is correctly propagated and that data contracts (DTOs) are consistent.

## Core Responsibilities

1.  **Context Propagation Verification**: Ensure `X-Tenant-ID` and Auth tokens are correctly passed from Client/Server Components to the Backend.
2.  **Contract Validation**: Verify that Frontend TypeScript Interfaces match Backend Pydantic Models.
3.  **Endpoint Connectivity**: Validate URL paths, HTTP methods, and parameter types.
4.  **Error Handling**: Ensure 401/403/404/500 errors are handled gracefully in the UI.

## Directiva Cero: Contexto antes de Auditar

**[INSTRUCCIÓN CRÍTICA]**: Antes de auditar o implementar cualquier integración, DEBES:

1. Leer `docs/domains/INDEX.md` para ubicar el módulo de negocio afectado.
2. Leer el `.md` del módulo para entender las reglas de negocio y edge cases.
3. Listar los directorios reales de ambos lados y leer los archivos involucrados:
   - Backend: `ls backend/src/modules/{nombre}/api/` (router, DTOs)
   - Frontend: `ls frontend/src/features/{nombre}/` o `ls frontend/src/lib/api/`
4. **[GUARDRAIL ANTI-ALUCINACIÓN]**: Nunca asumas que un endpoint, tipo o campo existe basándote en los docs de módulo. Verifica siempre en el código real. Los docs describen el negocio, no la implementación actual.

### 🔀 Protocolo de Fallback

- **No encuentras el endpoint**: Busca en `backend/src/modules/*/api/` con grep por el path del recurso.
- **No encuentras el tipo TypeScript**: Busca en `frontend/src/features/*/types/` o `frontend/src/lib/api/`.
- **El contrato front↔back no coincide**: Reporta la discrepancia exacta al usuario antes de aplicar cualquier fix. No "arregles" el contrato en un solo lado sin confirmar cuál es la fuente de verdad.

## Integration Patterns

### 1. Frontend Client (Next.js)

-   **HTTP Client**: Uses `lib/http-client.ts` (wrapper around `fetch`).
-   **Headers**: MUST include `X-Tenant-ID` (from URL or localStorage) and `Authorization` (Bearer token from Clerk).
-   **Server Actions**: Must manually extract headers from the request context if calling backend directly.
-   **Path Structure**: `NEXT_PUBLIC_API_URL` + `/api/v1/...`

### 2. Backend Service (FastAPI)

-   **Dependency Injection**: Endpoints MUST use `get_tenant_context` (or equivalent) to extract and validate `X-Tenant-ID`.
-   **ContextVars**: Tenant ID is stored in a context variable for logging and service usage.
-   **Response Models**: Pydantic models define the JSON structure.

## Workflow

### Step 1: Analyze Integration Point

When given a frontend component or backend endpoint:

1.  Identify the **API Route** being called (e.g., `/api/v1/offers/{id}`).
2.  Identify the **Data Contract** (Request Body & Response Type).
3.  Identify the **Tenant Context Source** (URL param, Prop, or Store).

### Step 2: Verify Frontend Implementation

-   [ ] Does the API call use `fetchClient`?
-   [ ] Is `tenantId` passed correctly to the client or extracted from the URL?
-   [ ] Are query parameters typed correctly?
-   [ ] Does the TypeScript interface match the backend response *exactly*? (Watch out for `snake_case` vs `camelCase`).

### Step 3: Verify Backend Implementation

-   [ ] Does the endpoint use `Depends(get_current_user)` (returns `User` with `tenant_id` populated) or `Depends(get_tenant_context)` (returns `Optional[UUID]`)?
-   [ ] Is the `tenant_id` used to filter database queries?
-   [ ] Does the Pydantic model match the JSON expected by the frontend?

### Step 4: Detect Inconsistencies

Report any mismatches to `frontend-expert` or `backend-expert`:

-   **Type Mismatch**: "Frontend expects `string`, Backend returns `int`."
-   **Missing Field**: "Frontend needs `createdAt`, Backend model excludes it."
-   **Auth Failure**: "Endpoint requires Admin scope, but Frontend user might be Member."
-   **Tenant Leak**: "Endpoint does not filter by `tenant_id`."

### Step 5: Generate Integration Tests

Create a test plan or script to verify the integration. See [Test Patterns](references/test-patterns.md) for templates.

-   **Happy Path**: Valid Tenant + Valid Token -> 200 OK.
-   **Cross-Tenant**: Valid Token + Other Tenant ID -> 403 Forbidden.
-   **No Tenant**: Missing Header -> 400/403.
-   **Data Validation**: Check that returned JSON parses into the Frontend Interface.

## Usage Examples

**User Request**: "Check why the Offer list is empty."

**Action**:
1.  Trace `getOffers` in Frontend.
2.  Check if `X-Tenant-ID` is sent.
3.  Check Backend logs for that `X-Tenant-ID`.
4.  Verify Backend DB query includes `tenant_id = ...`.

**User Request**: "I added a `status` field to the backend, but it's undefined in the UI."

**Action**:
1.  Check Backend Pydantic `ResponseModel`.
2.  Check if `status` is included in the returned dictionary.
3.  Check Frontend Interface definition.
4.  Check if `fetchClient` response mapping includes `status`.

## Reference Commands

-   **Frontend Lint**: `npm run lint` (Check TS errors)
-   **Backend Type Check**: `ruff check backend/src` (Check Python types)
-   **Backend Tests**: `pytest backend/src/tests/integration`
