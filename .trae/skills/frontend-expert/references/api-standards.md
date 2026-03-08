# Frontend API & Authentication Standards

## 1. Authentication Pattern
We use **Clerk** for authentication, but we handle token injection **manually** to ensure full control over server-side and client-side requests.

### Key Rules
1.  **No Global Interceptors**: Do not rely on a global Axios interceptor for Auth.
2.  **Explicit Injection**: Pass the `token` as an argument to API functions.
3.  **Client-Side Fetching**: Use `useAuth().getToken()` in components/hooks and pass it down.

## 2. Multi-Tenancy: X-Tenant-ID Header

Every request to the backend **must** include the `X-Tenant-ID` header. The backend uses it to enforce strict data isolation between tenants. It accepts the tenant's **UUID or slug**.

### How it is injected (by context)

| Context | Mechanism | Action required |
|---|---|---|
| **Client Component / Hook** | `fetchClient` lo inyecta **automáticamente** leyendo el primer segmento de la URL (`/[tenantId]/...`) con fallback a `localStorage('x-tenant-id')`. | Ninguna. Solo usar `fetchClient`. |
| **Server Component** | `fetchClient` es browser-only y no aplica. Debes inyectar el header **manualmente**. | Leer `params.tenantId` de la ruta y pasarlo en headers. |

> **⚠️ NUNCA** pases `X-Tenant-ID` manualmente en Client Components que usan `fetchClient` — ya está inyectado. Hacerlo doble puede causar conflictos.

### Server Component — patrón correcto

```typescript
// src/app/(main)/[tenantId]/my-page/page.tsx
export default async function Page({ params }: { params: { tenantId: string } }) {
  const { getToken } = auth();
  const token = await getToken();

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/resource`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-ID': params.tenantId, // Inyección manual obligatoria
    },
    cache: 'no-store',
  });
  // ...
}
```

### Cache Partitioning (comportamiento interno de fetchClient)

`fetchClient` agrega automáticamente `?_t=<tenantId>` a todas las peticiones GET para forzar aislamiento de caché del navegador entre tenants. No interfieras con este parámetro.

## 3. HTTP Client
Always use `@/lib/http-client` (`fetchClient`) instead of raw `fetch`.
This wrapper handles:
- `X-Tenant-ID` injection (automatic, from URL or localStorage)
- Cache partitioning for GET requests (`?_t=<tenantId>`)
- 401 Unauthorized (Redirects to login)
- 403 Forbidden (Redirects to /forbidden)

## 4. Implementation Guide

### A. The API Definition (`src/lib/api/`)

```typescript
// src/lib/api/my-feature.ts
import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

const BASE_URL = config.api.baseUrl;

export const myFeatureApi = {
  /**
   * [AI Context] Fetches data for the dashboard.
   * [Constraints] Requires valid Bearer token.
   */
  getData: async (token: string): Promise<MyData> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/resource`, {
      headers: {
        Authorization: `Bearer ${token}`, // Explicit injection
      },
    });
    
    if (!res.ok) throw new Error("Failed to fetch data");
    return res.json();
  }
};
```

### B. The Hook (`src/features/my-feature/hooks/use-data.ts`)

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
    enabled: isLoaded && isSignedIn, // Prevent fetch if not auth
  });
}
```

### C. Server Components
For Server Components, use Clerk's `auth()` helper and inject `X-Tenant-ID` manually from route params.
See the full pattern in **Section 2 (Multi-Tenancy)** above — it covers both `Authorization` and `X-Tenant-ID` injection.
