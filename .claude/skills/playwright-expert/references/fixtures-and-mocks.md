# Fixtures and Network Mocks

> **Read when:** writing or extending `auth.fixture.ts`, mocking a backend endpoint, integrating Growth Studio / Copilot SSE / Meta Ads / IG / YT / Email mocks, working with seeded test data.

Fixtures are Playwright's dependency-injection mechanism. Mocks are how we keep tests fast, deterministic, and independent of external services. Together they form the substrate every spec relies on.

---

## 1. The two kinds of fixtures

| Kind | Scope | Use for |
|---|---|---|
| **Test fixture** | Per test | Things every test in this scope needs: auth, tenant, mocked APIs, seeded data |
| **Worker fixture** | Per worker process | Expensive, reusable resources: a custom database connection, a per-worker user session |

Nicolify exclusively uses test-scope fixtures (no worker fixtures). The Clerk session is reused via `storageState` — not a worker fixture, but conceptually similar.

---

## 2. The canonical auth fixture

File: `frontend/e2e/fixtures/auth.fixture.ts`

```typescript
import { test as base, expect } from '@playwright/test';
import { setupClerkTestingToken } from '@clerk/testing/playwright';

type TenantFixtures = { tenantId: string };

export const test = base.extend<TenantFixtures>({
  tenantId: [process.env.E2E_TENANT_ID!, { option: true }],
  page: async ({ page, tenantId }, use) => {
    await setupClerkTestingToken({ page });
    await page.addInitScript((tid) => {
      localStorage.setItem('x-tenant-id', tid);
    }, tenantId);
    await use(page);
  },
});

export { expect };
```

What this gives every test that imports from this file:

| Resource | Where it comes from | Why |
|---|---|---|
| `page` | Playwright base | Standard browser page |
| `tenantId` | `process.env.E2E_TENANT_ID` (overridable per project) | Tests stay tenant-agnostic |
| Clerk testing token | `setupClerkTestingToken({ page })` | Bypass Cloudflare Turnstile per page |
| `X-Tenant-ID` header | `localStorage.x-tenant-id` → `fetchClient` middleware | Backend filters by tenant |

### Why `addInitScript` and not `evaluateOnNewDocument`

`addInitScript` runs the snippet BEFORE any page script executes, including in iframes. `localStorage` is set before the FE bootstraps. If we used `evaluate()` after navigation, the FE's first React render would see no tenant and fire a useless API request.

---

## 3. Composing fixtures — when to add a new one

If multiple tests need the same setup that goes beyond auth/tenant, create a domain fixture:

```typescript
// frontend/e2e/fixtures/copilot-chat.fixture.ts
import { test as authTest, expect } from './auth.fixture';

type CopilotFixtures = {
  copilotConversationId: string;
};

export const test = authTest.extend<CopilotFixtures>({
  copilotConversationId: async ({ page }, use) => {
    // 1. Mock the conversation creation endpoint
    await page.route('**/api/v1/copilot/conversations', (route) =>
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'mock-conv-id', messages: [] }),
      }),
    );
    // 2. Navigate to a Copilot-enabled route
    await page.goto('/');
    // 3. Hand the conversation ID to the test
    await use('mock-conv-id');
  },
});

export { expect };
```

Tests that need a conversation just import from this file — they get auth + tenant + conversation, all set up.

```typescript
import { test, expect } from '../../fixtures/copilot-chat.fixture';

test('user can send a message', async ({ page, copilotConversationId }) => {
  // ...
});
```

**Rule:** never extend `@playwright/test` directly when an `auth.fixture` extension is what you need. Always chain from `auth.fixture` → domain fixture → spec.

---

## 4. Network mocking with `page.route`

The most common pattern. Intercept a request, fulfill it with canned data.

```typescript
await page.route('**/api/v1/brand', (route) =>
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      id: 'brand-id',
      name: 'Test Brand',
      slug: 'test-brand',
    }),
  }),
);

await page.goto(`/${tenantId}/brand-studio`);
await expect(page.getByText('Test Brand')).toBeVisible();
```

### Patterns by use case

#### Match-all GET, return canned JSON

```typescript
await page.route('**/api/v1/offers', (route) => {
  if (route.request().method() === 'GET') {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    });
  }
  return route.continue();   // let other methods through
});
```

#### Mock POST and capture the request body

```typescript
let capturedBody: unknown = null;
await page.route('**/api/v1/offers', async (route) => {
  if (route.request().method() === 'POST') {
    capturedBody = await route.request().postDataJSON();
    return route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'new-offer-id', ...capturedBody as object }),
    });
  }
  return route.continue();
});

// ... user creates offer ...

expect(capturedBody).toMatchObject({ name: 'Test Offer' });
```

#### Simulate failure

```typescript
await page.route('**/api/v1/offers', (route) =>
  route.fulfill({ status: 500, body: 'Internal Server Error' }),
);
// Now test the error UI
```

#### Conditional response (different responses on subsequent calls)

```typescript
let callCount = 0;
await page.route('**/api/v1/jobs/*/status', (route) => {
  callCount++;
  const status = callCount < 3 ? 'pending' : 'completed';
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status }),
  });
});
```

### Order matters
`page.route` registrations are LIFO — last registered, first matched. If you register a generic catch-all and then a specific override, the specific one wins.

### Cleanup
Routes registered on a `page` are automatically cleared when the test ends. No manual cleanup needed.

---

## 5. Server-Sent Events (SSE) mocking — Copilot pattern

Copilot streams responses via SSE. Mocking SSE in `page.route` requires manually building the response body:

```typescript
const sseBody = [
  'event: message',
  'data: {"type":"start"}',
  '',
  'event: message',
  'data: {"type":"delta","content":"Hola"}',
  '',
  'event: message',
  'data: {"type":"end"}',
  '',
].join('\n');

await page.route('**/api/v1/copilot/stream', (route) =>
  route.fulfill({
    status: 200,
    contentType: 'text/event-stream',
    body: sseBody,
  }),
);
```

For multi-event streams with delays, use `page.route` with a stream from `route.fulfill({ body: stream })`. See `frontend/e2e/fixtures/copilot-chat.fixture.ts` for the full pattern.

---

## 6. Mock data lives next to the fixture

Convention:
- `frontend/e2e/fixtures/<feature>-mock-data.ts` — pure data, no logic
- `frontend/e2e/fixtures/<feature>-setup.ts` — registers routes; consumes the data
- `frontend/e2e/fixtures/<feature>.fixture.ts` — exposes a Playwright fixture that calls the setup

Example: `meta-ads-mock-data.ts` + `meta-ads-setup.ts` are paired files. To use:

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import { setupMetaAdsMocks } from '../../fixtures/meta-ads-setup';

test('meta ads dashboard renders', async ({ page, tenantId }) => {
  await setupMetaAdsMocks(page);
  await page.goto(`/${tenantId}/growth/meta-ads`);
  // assertions
});
```

This split keeps `auth.fixture` lean and lets each feature opt in.

---

## 7. The Growth Studio mock contract (critical)

Growth Studio uses progressive loading: summary → overview → group-detail → stage-detail. The FE will NOT render channel cards unless the **overview endpoint** returns a `channel_list`. This catches everyone the first time.

`frontend/e2e/fixtures/growth-studio.fixture.ts` provides:
- `/metrics/summary` → minimal stage counts
- `/metrics/{stage}/overview` → MUST include `channel_list`; if you add a new channel, ADD IT HERE
- `/metrics/{stage}/groups/{group}` → cached group detail
- `/metrics/{stage}/channels/{channel}` → DB-loaded stage detail
- `/metrics/timeseries` → trend data
- `/api/v1/connections` → all healthy
- `/api/v1/catalog/...` → catalog metadata

Per-channel fixtures (`ig-organic-setup.ts`, `meta-ads-setup.ts`, etc.) ADD their channel to the overview's `channel_list`. If you forget this step, the channel card silently doesn't render and your test fails with "element not found."

---

## 8. Don't mock what you can avoid mocking

Order of preference for backend interactions:

1. **Real backend, real test tenant** — best for `verify` and some `regression`. You assert the real contract.
2. **Mocked endpoint, real-shaped data** — default for `smoke`. Fast, deterministic, but you can drift from the real backend.
3. **Mocked endpoint, fake-shaped data** — bad. Catches nothing real. Avoid.

If you mock a response, copy the shape from a real backend response (run the dev backend, hit the endpoint, paste the JSON). Then trim to what your test needs. This is the difference between a useful smoke and a fake green.

---

## 9. Mock guards — fail loudly when the real backend changes

Add a regression check that the mocked shape is plausible:

```typescript
const MOCK_OFFER = {
  id: 'mock-id',
  name: 'Test',
  variant_structure: 'STANDARD',   // backend enum; if backend renames, smoke catches it via:
};

// In a setup test, optionally:
test.beforeAll(async ({ request }) => {
  const real = await request.get(`${process.env.E2E_BASE_URL}/api/v1/_schema/offer`);
  const schema = await real.json();
  expect(Object.keys(MOCK_OFFER)).toEqual(expect.arrayContaining(schema.required));
});
```

This is opt-in and only worth doing for high-traffic shapes. Most mocks don't need it.

---

## 10. External service mocking (Meta, IG, YT, Email)

These are mocked at the BACKEND boundary, not in Playwright. The test backend is configured to return canned responses for `/integrations/meta/...` etc. Playwright mocks Nicolify endpoints — never the third-party API directly.

If you find a test that does:

```typescript
await page.route('https://graph.facebook.com/...', ...)   // ❌ wrong layer
```

That's a mistake — fix it to mock the Nicolify endpoint that wraps it instead.

---

## 11. Test data factory — `test-data.ts`

Canonical fixtures for tenants, users, sessions live in `frontend/e2e/fixtures/test-data.ts`. Use these instead of hardcoding IDs:

```typescript
import { TEST_TENANTS, TEST_USERS } from '../../fixtures/test-data';

await page.goto(`/${TEST_TENANTS.primary.id}/...`);
```

When a test needs a NEW tenant, do not invent UUIDs — extend `test-data.ts` with the seed data and reference the symbol.

---

## 12. Storage manipulation — when fixtures don't fit

For tests that need a non-default localStorage/sessionStorage state (feature flags, onboarding state), use `addInitScript`:

```typescript
test('shows onboarding on first visit', async ({ page, tenantId }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('onboarding-completed');
  });
  await page.goto(`/${tenantId}/`);
  await expect(page.getByText(/bienvenido/i)).toBeVisible();
});
```

Use this sparingly. If the manipulation is used in > 2 tests, lift it into a fixture.

---

## 13. Hard rules

- **Always import `test` from a fixture file**, never directly from `@playwright/test` (in authenticated specs).
- **Never `page.route('**', ...)`** — too greedy; will block CSS, fonts, the Next.js HMR socket. Always scope to `**/api/...` or similar.
- **Never seed data via the FE UI in a fixture** (e.g., "log in, click create offer"). Use direct API calls (`page.request.post(...)`) — faster and more reliable.
- **Mock JSON responses, not HTML** — never intercept the page navigation itself; let Next.js render.
- **Routes are scoped to the page**, not the context. If you create a new `BrowserContext` you have to re-register routes. Avoid creating new contexts in tests; use the auto-injected `page`.

---

## 14. Debugging mocks

When a mock isn't firing:

1. Add a `console.log` in the route handler:
   ```typescript
   await page.route('**/api/v1/offers', (route) => {
     console.log('[mock] caught', route.request().url());
     return route.fulfill(...);
   });
   ```
2. Run with `--headed` and open DevTools → Network. See if the request URL matches your pattern.
3. Check route ORDER — a more general route registered after may shadow a specific one.
4. Confirm the test isn't bypassing `page.route` by using `page.request.get()` (those are NOT intercepted by `page.route`; they go through Playwright's `APIRequestContext` and have separate mocking via `request.fixtures` if needed).
