# Debugging Specification: Dashboard Load Failure

## Context
The user reports that "nothing is loading" after logging into the application with the email `christian.revilla.m@gmail.com`. The expected behavior is that the dashboard should load with the user's data (Profile, Tenant list, Brand Settings).
Current state: The user is stuck in a state where data is not appearing or loading indefinitely.

## Objective
Trace the full authentication and data loading lifecycle from Clerk login to the final UI render to identify the point of failure.

## Critical Path Analysis

### 1. Authentication & Routing (Middleware & Layout)
- **Actor**: `middleware.ts` & `TenantGuard` (Server Component)
- **Flow**:
  1. User authenticates via Clerk.
  2. Middleware validates session.
  3. Middleware injects `x-current-path` header.
  4. `RootLayout` wraps app in `ClerkProvider` and `TenantGuard`.
  5. `TenantGuard` checks `user.publicMetadata.tenant_id`.
  - **Risk Point**: If `tenant_id` is missing in metadata, user might be redirected or blocked without feedback.
  - **Risk Point**: `TenantGuard` logic for redirecting to `/onboarding` might be failing or looping.

### 2. Client-Side Context Initialization
- **Actor**: `Providers` (`providers.tsx`)
- **Flow**:
  1. `useEffect` syncs Clerk `tenant_id` to `localStorage` (`x-tenant-id`).
  - **Risk Point**: Race condition where API calls fire before `localStorage` is populated.

### 3. Initial Data Fetching (Parallel Execution)
Once inside the authenticated layout, the following hooks trigger immediately:

#### A. User Profile (`useUserProfile`)
- **Component**: `AppSidebar` (via `NavContent`)
- **Endpoint**: `GET /api/v1/iam/settings/profile`
- **Expected Payload**:
  ```json
  {
    "id": "e06bb384...",
    "full_name": "Christian Revilla",
    "email": "christian.revilla.m@gmail.com",
    "tenant": { "id": "...", "name": "Visionarias", ... }
  }
  ```
- **Risk Point**: If this fails, the sidebar user info will be empty.

#### B. Tenant List (`useTenants`)
- **Component**: `TenantSwitcher`
- **Endpoint**: `GET /api/v1/iam/users/me/tenants`
- **Expected Payload**: `[ { "id": "...", "name": "Visionarias", "role": "admin" } ]`
- **Risk Point**: If this fails, the switcher will be empty or show a loading state.

#### C. Brand Settings (`useBrandSettings`)
- **Component**: `BrandSettingsPage` (Main Content)
- **Endpoint**: `GET /api/v1/brand/settings`
- **Expected Payload**: Large JSON with `visuals`, `strategy`, `identity`, etc.
- **Risk Point**: This is the heaviest call. If it fails, the main content area will show an error or spinner.

## Potential Failure Modes

1.  **Network/CORS**: The browser is blocking requests to `localhost:8000` or the Tunnel URL due to mixed content or CORS policies.
2.  **Authentication/Token**: The Clerk token is not being passed correctly in the `Authorization` header by `fetchClient`.
3.  **Tenant Context**: The `X-Tenant-ID` header is missing or mismatching the user's actual tenant, causing `403 Forbidden` or `404 Not Found` responses from the backend.
4.  **Database**: The backend query fails because the user or tenant doesn't exist (Verified: User exists, but link to tenant might be broken).

## Debugging Strategy
We will systematically verify each step using the `checklist.md` to isolate the breakage.
