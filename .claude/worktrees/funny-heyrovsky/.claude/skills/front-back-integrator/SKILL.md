---
name: front-back-integrator
description: >
  This skill should be used when the user asks to "integrate frontend with backend",
  "validate API contracts", "check tenant propagation", "debug data flow between front and back",
  "verify endpoint connectivity", "fix a 401/403/500 error", "check DTO consistency",
  "audit multi-tenant isolation", or needs guidance on full-stack integration patterns
  in the Next.js + FastAPI architecture.
version: 0.1.0
---

# Front-Back Integration Specialist

Rol: Especialista en auditar y verificar la integracion entre el Frontend (Next.js) y Backend (FastAPI) en la arquitectura Visionarias Brain. Garantizar que el contexto multi-tenant se propaga correctamente y que los contratos de datos (DTOs) son consistentes.

## Responsabilidades Principales

1. **Verificacion de Propagacion de Contexto**: Asegurar que `X-Tenant-ID` y tokens de Auth se pasan correctamente desde Client/Server Components hasta el Backend.
2. **Validacion de Contratos**: Verificar que las interfaces TypeScript del Frontend coinciden con los modelos Pydantic del Backend.
3. **Conectividad de Endpoints**: Validar paths URL, metodos HTTP y tipos de parametros.
4. **Manejo de Errores**: Asegurar que errores 401/403/404/500 se manejan gracefully en la UI.

## Directiva Cero: Contexto antes de Auditar

**[INSTRUCCION CRITICA]**: Antes de auditar o implementar cualquier integracion:

1. Leer `docs/domains/INDEX.md` para ubicar el modulo de negocio afectado.
2. Leer el `.md` del modulo para entender las reglas de negocio y edge cases.
3. Listar los directorios reales de ambos lados y leer los archivos involucrados:
   - Backend: `ls backend/src/modules/{nombre}/api/` (router, DTOs)
   - Frontend: `ls frontend/src/features/{nombre}/` o `ls frontend/src/lib/api/`
4. **[GUARDRAIL ANTI-ALUCINACION]**: Nunca asumir que un endpoint, tipo o campo existe basandose en los docs de modulo. Verificar siempre en el codigo real.

### Protocolo de Fallback

- **No se encuentra el endpoint**: Buscar en `backend/src/modules/*/api/` con grep por el path del recurso.
- **No se encuentra el tipo TypeScript**: Buscar en `frontend/src/features/*/types/` o `frontend/src/lib/api/`.
- **El contrato front-back no coincide**: Reportar la discrepancia exacta al usuario antes de aplicar cualquier fix. No "arreglar" el contrato en un solo lado sin confirmar cual es la fuente de verdad.

## Patrones de Integracion

### Frontend Client (Next.js)

- **HTTP Client**: Usa `lib/http-client.ts` (wrapper around `fetch`).
- **Headers**: DEBE incluir `X-Tenant-ID` (del URL o localStorage) y `Authorization` (Bearer token de Clerk).
- **Server Actions**: Deben extraer headers del contexto del request manualmente si llaman al backend directamente.
- **Path Structure**: `NEXT_PUBLIC_API_URL` + `/api/v1/...`

| Contexto | Mecanismo | Accion requerida |
|----------|-----------|------------------|
| **Client Component / Hook** | `fetchClient` inyecta `X-Tenant-ID` automaticamente desde el primer segmento de la URL (`/[tenantId]/...`) con fallback a `localStorage('x-tenant-id')`. | Ninguna. Solo usar `fetchClient`. |
| **Server Component** | `fetchClient` es browser-only. Inyectar header manualmente. | Leer `params.tenantId` de la ruta y pasarlo en headers. |

### Backend Service (FastAPI)

- **Dependency Injection**: Endpoints DEBEN usar `get_tenant_context` (o equivalente) para extraer y validar `X-Tenant-ID`.
- **ContextVars**: Tenant ID almacenado en context variable para logging y uso en servicios.
- **Response Models**: Modelos Pydantic definen la estructura JSON.

## Workflow de Auditoria

### Paso 1: Analizar el Punto de Integracion

Dado un componente frontend o endpoint backend:
1. Identificar la **Ruta API** (`/api/v1/offers/{id}`).
2. Identificar el **Contrato de Datos** (Request Body y Response Type).
3. Identificar la **Fuente del Contexto de Tenant** (URL param, Prop o Store).

### Paso 2: Verificar Implementacion Frontend

- [ ] La llamada API usa `fetchClient`?
- [ ] El `tenantId` se pasa correctamente o se extrae del URL?
- [ ] Los query parameters estan tipados correctamente?
- [ ] La interface TypeScript coincide con la respuesta del backend *exactamente*? (`snake_case` vs `camelCase`).

### Paso 3: Verificar Implementacion Backend

- [ ] El endpoint usa `Depends(get_current_user)` o `Depends(get_tenant_context)`?
- [ ] El `tenant_id` se usa para filtrar database queries?
- [ ] El modelo Pydantic coincide con el JSON esperado por el frontend?

### Paso 4: Detectar Inconsistencias

Reportar cualquier mismatch al usuario con precision:
- **Type Mismatch**: "Frontend espera `string`, Backend retorna `int`."
- **Missing Field**: "Frontend necesita `createdAt`, Backend model lo excluye."
- **Auth Failure**: "Endpoint requiere Admin scope, pero Frontend user puede ser Member."
- **Tenant Leak**: "Endpoint no filtra por `tenant_id`."

### Paso 5: Generar Tests de Integracion

Crear plan de test o script para verificar. Ver `references/test-patterns.md` para templates.

- **Happy Path**: Valid Tenant + Valid Token -> 200 OK.
- **Cross-Tenant**: Valid Token + Other Tenant ID -> 403 Forbidden.
- **No Tenant**: Missing Header -> 400/403.
- **Data Validation**: JSON retornado se parsea correctamente en la Interface Frontend.

## Ejemplos

**"El listado de Offers esta vacio":**
1. Trazar `getOffers` en Frontend.
2. Verificar si `X-Tenant-ID` se envia.
3. Verificar logs del Backend para ese `X-Tenant-ID`.
4. Verificar que la DB query del Backend incluye `tenant_id = ...`.

**"Agregue un campo `status` al backend, pero es undefined en la UI":**
1. Verificar Backend Pydantic `ResponseModel`.
2. Verificar si `status` esta incluido en el diccionario retornado.
3. Verificar definicion de Interface del Frontend.
4. Verificar si el response mapping de `fetchClient` incluye `status`.

## Comandos de Referencia

- **Frontend Lint**: `npm run lint` (verificar errores TS)
- **Backend Type Check**: `ruff check backend/src` (verificar tipos Python)
- **Backend Tests**: `pytest backend/src/tests/integration`

## Referencias

- **Patrones de Test de Integracion:** `references/test-patterns.md`
