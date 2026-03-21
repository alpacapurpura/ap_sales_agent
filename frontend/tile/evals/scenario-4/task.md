# Multi-Tenant HTTP Fetch Client

A fetch wrapper function for a multi-tenant SaaS application. It automatically injects the tenant identifier header into every outgoing request and handles authentication errors by redirecting the browser to appropriate error pages.

The tenant ID is read from a cookie named `tenant-id`. The function must:
1. Read the `tenant-id` cookie value from `document.cookie`
2. Inject it as an `X-Tenant-ID` header on every request
3. On a `401 Unauthorized` response, redirect to `/sign-in`
4. On a `403 Forbidden` response, redirect to `/forbidden`
5. Otherwise, return the response normally

## Capabilities

### Tenant header injection

Adds the X-Tenant-ID header to all outgoing fetch requests.

- A request to `/api/data` includes the `X-Tenant-ID` header set to the value of the `tenant-id` cookie [@test](./tests/fetch-tenant-header.test.ts)
- Existing headers in the request options are preserved alongside the injected header [@test](./tests/fetch-preserves-headers.test.ts)

### Authentication error interception

- A `401` response triggers `window.location.href` redirect to `/sign-in` [@test](./tests/fetch-401-redirect.test.ts)
- A `403` response triggers `window.location.href` redirect to `/forbidden` [@test](./tests/fetch-403-redirect.test.ts)
- A `200` response is returned directly without any redirect [@test](./tests/fetch-200-passthrough.test.ts)

## Implementation

[@generates](./src/http-client.ts)

## API

```typescript { #api }
export function fetchClient(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the multi-tenant fetch client with automatic tenant header injection and auth error interception.

[@satisfied-by](visionarias-client)
