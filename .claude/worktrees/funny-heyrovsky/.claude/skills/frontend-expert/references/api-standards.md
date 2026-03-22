# Frontend API & Authentication Standards

## 1. Authentication Pattern
Se usa **Clerk** para autenticacion, pero la inyeccion del token se maneja **manualmente** para control total sobre requests server-side y client-side.

### Reglas Clave
1. **No Global Interceptors**: No depender de un interceptor global de Axios para Auth.
2. **Explicit Injection**: Pasar el `token` como argumento a funciones de API.
3. **Client-Side Fetching**: Usar `useAuth().getToken()` en componentes/hooks y pasarlo.

## 2. Multi-Tenancy: X-Tenant-ID Header

Cada request al backend **debe** incluir el header `X-Tenant-ID`. El backend lo usa para enforcar aislamiento estricto de datos entre tenants. Acepta el **UUID o slug** del tenant.

### Inyeccion por contexto

| Contexto | Mecanismo | Accion requerida |
|----------|-----------|------------------|
| **Client Component / Hook** | `fetchClient` lo inyecta **automaticamente** leyendo el primer segmento del URL (`/[tenantId]/...`) con fallback a `localStorage('x-tenant-id')`. | Ninguna. Solo usar `fetchClient`. |
| **Server Component** | `fetchClient` es browser-only y no aplica. Inyectar header **manualmente**. | Leer `params.tenantId` de la ruta y pasarlo en headers. |

> **NUNCA** pasar `X-Tenant-ID` manualmente en Client Components que usan `fetchClient` — ya esta inyectado. Hacerlo doble puede causar conflictos.

### Server Component — patron correcto

```typescript
// src/app/(main)/[tenantId]/my-page/page.tsx
export default async function Page({ params }: { params: { tenantId: string } }) {
  const { getToken } = auth();
  const token = await getToken();

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/resource`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-ID': params.tenantId, // Inyeccion manual obligatoria
    },
    cache: 'no-store',
  });
  // ...
}
```

### Cache Partitioning (comportamiento interno de fetchClient)

`fetchClient` agrega automaticamente `?_t=<tenantId>` a todas las peticiones GET para forzar aislamiento de cache del navegador entre tenants. No interferir con este parametro.

## 3. HTTP Client
Siempre usar `@/lib/http-client` (`fetchClient`) en lugar de `fetch` directo.
Este wrapper maneja:
- Inyeccion de `X-Tenant-ID` (automatica, desde URL o localStorage)
- Cache partitioning para GET requests (`?_t=<tenantId>`)
- 401 Unauthorized (Redirect a login)
- 403 Forbidden (Redirect a /forbidden)

## 4. Guia de Implementacion

### A. Definicion de API (`src/lib/api/`)

```typescript
// src/lib/api/my-feature.ts
import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

const BASE_URL = config.api.baseUrl;

export const myFeatureApi = {
  getData: async (token: string): Promise<MyData> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/resource`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to fetch data");
    return res.json();
  }
};
```

### B. Hook (`src/features/my-feature/hooks/use-data.ts`)

```typescript
// src/features/my-feature/hooks/use-data.ts
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { myFeatureApi } from "@/lib/api/my-feature";

export function useMyData() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery({
    queryKey: ["my-data"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No token");
      return myFeatureApi.getData(token);
    },
    enabled: isLoaded && isSignedIn,
  });
}
```

### C. Server Components
Para Server Components, usar el helper `auth()` de Clerk e inyectar `X-Tenant-ID` manualmente desde route params.
Ver el patron completo en la seccion 2 (Multi-Tenancy) arriba.
