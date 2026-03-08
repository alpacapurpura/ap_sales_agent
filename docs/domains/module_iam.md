# Módulo de IAM (Identity & Access Management) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la FUENTE DE VERDAD para entender la autenticación, autorización y aislamiento multi-tenant. Úsalo para razonar sobre problemas de "acceso denegado", "usuarios no encontrados" o "datos cruzados entre organizaciones".

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/iam/`
  - Entidades de dominio (`User`, `Tenant`): `domain/`
  - Modelos SQL (tabla pivote `user_tenants`): `infrastructure/models/`
  - **Dependencias críticas de auth** (`get_current_user`, `get_tenant_context`): `api/dependencies.py`
  - Webhooks de sincronización con Clerk: `api/webhooks.py`
- **Frontend**:
  - HTTP client con inyección de `X-Tenant-ID`: `frontend/src/lib/http-client.ts`
  - Hooks de gestión de tenants: `frontend/src/features/settings/hooks/`
  - Guards de protección de rutas: `frontend/src/components/auth/`

## 2. Lógica de Negocio (The "Why" & "How")

### Arquitectura de "Auth Sandwich" (Híbrida)
1.  **Capa 1 (Identidad - Clerk)**: Clerk maneja el Login/Sign-up y emite el JWT. Es la fuente de verdad de la *identidad* (quién eres).
2.  **Capa 2 (Sincronización - Webhooks)**: Al crearse un usuario en Clerk, un webhook asíncrono lo crea en la tabla `public.users` local.
    - *Regla Crítica*: El `clerk_id` es el vínculo inmutable. Si el webhook falla, el usuario existe en Clerk pero no en DB -> **Error 403** al intentar usar la API.
3.  **Capa 3 (Autorización - Backend)**:
    - Cada request debe tener un token válido (validado con JWKS de Clerk).
    - El backend busca al usuario en DB local por `email` (o `clerk_id` como fallback).
    - **Aislamiento**: Si el request trae header `X-Tenant-ID`, se verifica estrictamente que exista la relación en `user_tenants`.

### Estrategia Multi-Tenant (Isolation)
- **Identificación**: El Tenant activo se determina por, en orden de prioridad:
  1.  Header `X-Tenant-ID` (Inyectado por frontend basado en URL/Storage).
  2.  **Fallback**: El primer tenant asociado al usuario en DB (Default).
- **Protección de Datos**: Todas las consultas a DB (Repositorios) deben filtrar por `tenant_id`.
- **ContextVars**: El `tenant_id` se almacena en una variable de contexto global (`src.core.context`) para ser accesible en logs y auditoría sin pasar argumentos explícitos.

## 3. Casos Borde y Gotchas (Edge Cases)

- **Desincronización de Metadata (Clerk vs DB)**:
  - *Problema*: `TenantGuard` (Frontend) a veces verifica `user.publicMetadata.tenant_id` (en Clerk), mientras que el Backend verifica la tabla `user_tenants`.
  - *Consecuencia*: Si el webhook de actualización de metadata falla, el usuario podría ver "Acceso Denegado" en frontend aunque el backend permita acceso, o viceversa.
- **Cache Pollution en Frontend**:
  - *Problema*: Usuario cambia de Tenant A a Tenant B. React Query/SWR devuelve datos cacheados de A porque la URL es la misma (`/api/v1/leads`).
  - *Solución*: `http-client.ts` agrega `?_t={tenant_id}` a las URLs GET. Esto fuerza a que la key de caché sea única por tenant.
- **Usuarios "Huérfanos"**:
  - Usuarios que se registran pero no son invitados a ningún tenant ni crean uno.
  - El sistema los redirige al flujo de **Onboarding** (`/onboarding`) para crear su primera organización.
- **Navegación Cross-Tenant**:
  - Si un usuario intenta acceder manualmente a una URL de un tenant al que no pertenece (ej. cambiando el ID en la barra de direcciones), el backend devuelve `403 Forbidden` y el frontend lo redirige a `/forbidden`.

## 4. Snippets para Agentes (Common Tasks)

### Backend: Obtener Usuario y Tenant Actual
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# En un router o servicio
from src.modules.iam.domain.user import User
from fastapi import Depends
from src.modules.iam.api.dependencies import get_current_user

@router.get("/my-data")
async def get_my_data(user: User = Depends(get_current_user)):
    # user.tenant_id ya está poblado y validado en el objeto user
    # También está disponible en el contexto global para logs
    print(f"User {user.email} accessing Tenant {user.tenant_id}")
    return {"data": "secure", "tenant": str(user.tenant_id)}
```

### Frontend: Llamada Segura a API
```typescript
// ⚠️ Verificar nombres exactos de componentes/hooks en el código real antes de usar
import { fetchClient } from "@/lib/http-client";

// El token se inyecta automáticamente si usas fetchClient + useAuth (en componentes)
// O manualmente si es una función utilitaria:
export async function getData(token: string) {
  // fetchClient inyectará X-Tenant-ID automáticamente del contexto/localStorage
  // También agregará ?_t=... para cache busting
  return fetchClient("/api/v1/data", {
    headers: { Authorization: `Bearer ${token}` }
  });
}
```

### Backend: Sincronización Manual (Fallback)
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
# Si el webhook falla, se puede forzar sync en el login (dependencies.py)
# Esto ya está implementado en get_user_from_token:
# 1. Verifica token.
# 2. Si datos en token (nombre, email) difieren de DB -> Actualiza DB.
```
