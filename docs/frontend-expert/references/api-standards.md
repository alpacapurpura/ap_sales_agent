# Frontend API & Authentication Standards

## 1. Authentication Pattern
We use **Clerk** for authentication, but we handle token injection **manually** to ensure full control over server-side and client-side requests.

### Key Rules
1.  **No Global Interceptors**: Do not rely on a global Axios interceptor for Auth.
2.  **Explicit Injection**: Pass the `token` as an argument to API functions.
3.  **Client-Side Fetching**: Use `useAuth().getToken()` in components/hooks and pass it down.

## 2. HTTP Client
Always use `@/lib/http-client` (`fetchClient`) instead of raw `fetch`.
This wrapper handles:
- 401 Unauthorized (Redirects to login)
- 403 Forbidden (Redirects to /forbidden)
- Base URL configuration

## 3. Implementation Guide

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
For Server Components, use Clerk's `auth()` helper.

```typescript
// src/app/dashboard/page.tsx
import { auth } from "@clerk/nextjs/server";

export default async function Page() {
  const { getToken } = auth();
  const token = await getToken();
  // ... call API
}
```
