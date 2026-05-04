# Anti-Patterns — Things That Will Hurt You

> **Read when:** about to write something that "feels off," reviewing a PR that touches `frontend/e2e/**`, designing a new test, choosing a tool that "would make this easier."

This is the catalog of every mistake we have made or seen made. Each entry has the WHAT, the WHY (the failure mode it produces), and the FIX. If you find yourself doing one of these, stop and apply the fix — do not "do it just this once."

---

## A. Auth & Setup

### A1. Importing `test` from `@playwright/test` in an authenticated spec

```typescript
// ❌ wrong
import { test, expect } from '@playwright/test';

test('dashboard loads', async ({ page }) => {
  await page.goto('/some-tenant-id/dashboard');
});
```

**Why bad:** the Clerk testing token is not injected, the tenant header is not set. Cloudflare blocks the request OR the backend returns 403. Symptom: random "Bot traffic detected" or "Tenant not found" failures.

**Fix:**

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
test('dashboard loads', async ({ page, tenantId }) => {
  await page.goto(`/${tenantId}/dashboard`);
});
```

### A2. Manually calling `clerkSetup()` in a per-test fixture

**Why bad:** `clerkSetup()` is a session-scoped operation. Calling it per test wastes ~200ms each, hits Clerk rate limits, and provides no benefit (the testing token is already in env after the setup project ran).

**Fix:** never call `clerkSetup()` outside `clerk.setup.ts`. Use `setupClerkTestingToken({ page })` per test instead.

### A3. Reusing a stale `playwright/.clerk/user.json`

**Why bad:** cookies expire. cf_bm cookie expires in ~30 min. After 4-7 days, even the Clerk session JWT expires. Tests redirect to /sign-in and fail with confusing "redirect loop" errors.

**Fix:** the freshness gate in `clerk.setup.ts` handles this automatically. Never edit `user.json` by hand. If suspect, `npm run test:e2e:fresh`.

### A4. Committing `playwright/.clerk/user.json`

**Why bad:** (1) it leaks a real Clerk session token to git history, (2) every contributor pulling will reuse YOUR stale cookies, (3) eventually it will be ancient and break setup for everyone.

**Fix:** the file IS in `.gitignore` (root). If you ever see it in `git status`, do not `git add` it.

### A5. Hardcoding `E2E_TENANT_ID` in tests

```typescript
// ❌
await page.goto('/123e4567-e89b-12d3-a456-426614174000/dashboard');
```

**Why bad:** breaks in any environment with a different test tenant. Locks tests to one Clerk dev instance.

**Fix:** use `tenantId` from the fixture: `await page.goto(\`/${tenantId}/dashboard\`)`.

### A6. Function-based `globalSetup`

**Why bad:** Clerk's docs explicitly warn that env vars set in a function-based globalSetup don't propagate to worker processes. `clerkSetup()` writes `CLERK_TESTING_TOKEN` to env — workers won't see it.

**Fix:** use the project-based pattern (we do). `setup` project is a normal test that has `mode: 'serial'`.

### A7. Bypassing `auth.fixture.ts` to "test the auth flow itself"

If you want to test the sign-in page UI, do it in a `public` test (no auth state):

```typescript
import { test, expect } from '@playwright/test';
test('sign-in page renders', async ({ page }) => {
  await page.goto('/sign-in');
  await expect(page.getByRole('heading', { name: /iniciar sesión/i })).toBeVisible();
});
```

Don't try to "manually log in" inside an authenticated test — you'll fight the existing storageState.

---

## B. Locators

### B1. CSS class selectors

```typescript
// ❌
await page.locator('.btn-primary.bg-blue-500').click();
```

**Why bad:** Tailwind generates hashed class names; Shadcn version bumps shuffle them. Test breaks on every UI tweak.

**Fix:** `page.getByRole('button', { name: /save/i })`.

### B2. XPath selectors

```typescript
// ❌
await page.locator('//div[contains(@class, "card")]//button[1]').click();
```

**Why bad:** XPath is even more brittle than CSS — depends on full DOM structure. Reads like assembly.

**Fix:** restructure as `page.getByRole('article').first().getByRole('button')` or similar role-based query.

### B3. `nth(N)` without explanation

```typescript
// ❌
await page.locator('button').nth(3).click();
```

**Why bad:** silently breaks when button order changes (DOM reshuffle, A/B test, conditional render).

**Fix:** `.filter({ hasText: 'Save' })` or `.filter({ has: page.getByRole('img', { name: /icon-save/ }) })`.

### B4. `page.waitForSelector(...)` followed by `.click()`

```typescript
// ❌
await page.waitForSelector('.btn');
await page.locator('.btn').click();
```

**Why bad:** double resolution (search twice). Auto-retry assertions cover both wait + assert in one call.

**Fix:** `await expect(page.getByRole('button')).toBeVisible(); await page.getByRole('button').click();` — or just `await page.getByRole('button').click()`, which waits internally.

### B5. `page.evaluate(() => document.querySelector(...))`

**Why bad:** runs in browser context, no auto-retry, no Playwright assertions. Reinvents `getByX` poorly.

**Fix:** use a Playwright locator. Reserve `evaluate` for things genuinely impossible otherwise (reading window state).

---

## C. Assertions

### C1. `expect(await x.isVisible()).toBe(true)`

```typescript
// ❌ snapshots once, no retry
expect(await page.getByText('OK').isVisible()).toBe(true);
```

**Why bad:** evaluated once. If the page is mid-render when `isVisible()` runs, you get false. No auto-retry.

**Fix:**

```typescript
await expect(page.getByText('OK')).toBeVisible();
```

### C2. `await page.waitForTimeout(N)`

```typescript
// ❌
await page.waitForTimeout(2000);
await expect(page.getByText('OK')).toBeVisible();
```

**Why bad:** when fast, slows you down. When slow, still flakes.

**Fix:** the assertion ITSELF retries until timeout. `await expect(page.getByText('OK')).toBeVisible({ timeout: 10_000 });`

### C3. Loose text assertions

```typescript
// ❌
await expect(page.locator('body')).toContainText('Hola');
```

**Why bad:** `body` is the whole page. Match could come from anywhere — header, footer, breadcrumb. Hides regressions.

**Fix:** assert on the SPECIFIC element: `await expect(page.getByRole('heading', { name: /hola/i })).toBeVisible()`.

### C4. Asserting on hardcoded copy that may change

```typescript
// ❌
await expect(page.getByText('Configurá tu marca')).toBeVisible();
```

**Why bad:** uses voseo (`Configurá`); rule says neutro. When the FE fixes the copy to `Configura`, test breaks.

**Fix:** `await expect(page.getByText(/configur[áa] tu marca/i)).toBeVisible();` (regex tolerates both forms during migration).

### C5. Asserting on internal state

```typescript
// ❌
const html = await page.content();
expect(html).toContain('class="loaded"');
```

**Why bad:** asserts implementation detail. Changes when the FE changes how it signals load state.

**Fix:** assert on user-visible behavior: `await expect(page.getByText(/cargado/i)).toBeVisible()`.

---

## D. Fixtures & Mocks

### D1. `page.route('**', ...)` (no scoping)

**Why bad:** intercepts EVERYTHING — fonts, CSS, the Next.js HMR socket. Page won't render. Hangs forever.

**Fix:** scope to `**/api/v1/**` or specific endpoints.

### D2. Mocking the wrong layer (third-party API directly)

```typescript
// ❌
await page.route('https://graph.facebook.com/...', ...);
```

**Why bad:** Nicolify's FE doesn't call Facebook directly. It calls our backend, which calls Facebook. Mocking at FB level changes nothing.

**Fix:** mock the Nicolify endpoint that wraps it (`**/api/v1/integrations/meta/...`).

### D3. Mocking with fake-shaped data

```typescript
// ❌
await page.route('**/api/v1/offers', (route) =>
  route.fulfill({ body: JSON.stringify([1,2,3]) }),  // backend returns objects, not numbers
);
```

**Why bad:** the test passes only because the FE crashes silently and the assertion happens to also fail in the right spot. False green.

**Fix:** copy a real backend response shape and use it. Even better, generate from the OpenAPI schema.

### D4. Stateful mocks across tests

```typescript
// ❌
let counter = 0;
test.beforeEach(async ({ page }) => {
  await page.route(..., () => counter++);  // shared across tests in this file
});
```

**Why bad:** test order affects counter. Tests are no longer independent.

**Fix:** reset state in beforeEach OR move mock setup inside the test body.

### D5. Using `browser.newContext()` instead of the fixture's `page`

```typescript
// ❌
test('x', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  // no auth, no tenant, no testing token
});
```

**Why bad:** bypasses every guarantee the fixture provides.

**Fix:** use `({ page, tenantId })` from the fixture. Only create new contexts when genuinely testing multi-tab/multi-user flows.

---

## E. Test Structure

### E1. Long smoke tests (10+ steps)

**Why bad:** a smoke is a sanity check. Long flows are regressions. Mixing them up means smoke takes longer and regressions don't get the right project budget.

**Fix:** split. Smoke = "does the page render and is the primary CTA reachable?" Anything more goes in `regression/`.

### E2. Tests that depend on data created by other tests

```typescript
// test1.spec.ts: creates an offer
// test2.spec.ts: assumes the offer exists
```

**Why bad:** order-dependent. Parallel-hostile. Run test2 alone and it fails.

**Fix:** each test creates its own data (or mocks it).

### E3. `test.skip` permanente

**Why bad:** dead code. False sense of coverage. Bit-rots.

**Fix:** delete the test (recoverable from git history) or fix it. We removed 3 perma-skips on 2026-05-04; do not reintroduce.

### E4. Tests that mutate the test tenant's database state without cleanup

**Why bad:** next test inherits the mess. Eventually the test tenant is unusable.

**Fix:** tests should be read-only OR clean up in `afterEach`/`afterAll`.

### E5. Conditional tests (`if (env.X) test(...)`)

**Why bad:** different runs execute different test sets. Coverage report lies.

**Fix:** if a test only makes sense in certain envs, use `test.skip(condition, reason)` — but better, organize by project.

### E6. `test.only` left in committed code

**Why bad:** suite is silently 1 test. Pre-commit catches it usually but not always.

**Fix:** `forbidOnly: !!process.env.CI` is set in our config — CI fails if `.only` is present. Verify your local CI dry-run.

### E7. Custom assert utilities

```typescript
// ❌
function assertVisible(locator: Locator) { /* custom logic */ }
```

**Why bad:** you reinvent web-first matchers, badly. Loses Playwright trace info.

**Fix:** use `await expect(locator).toBeVisible()` directly.

---

## F. Execution & Environment

### F1. `make e2e` / `make e2e-smoke` locally

**Why bad:** runs Playwright inside Docker on WSL2. Empirically crashes within 5 min (OOM).

**Fix:** native WSL: `npm run test:e2e:smoke`. CI uses Docker — that's fine because Linux runners.

### F2. Playwright spawning its own `next dev`

**Why bad:** when `E2E_BASE_URL` is unset, Playwright spawns `npm run dev` from the config's `webServer` block. This is slow, fights with your existing dev container, and pollutes your terminal.

**Fix:** always export `E2E_BASE_URL=http://localhost:3000` when the dev container is up. The config skips `webServer` when this is set.

### F3. Running E2E without preflight

**Why bad:** wastes 5+ min on a problem that preflight would surface in 3 sec.

**Fix:** `bash scripts/e2e-preflight.sh` first, every time. If you're impatient, alias it.

### F4. Forcing more workers than the runner can handle

**Why bad:** 8 workers with 7 GB RAM = swapping = 30s test takes 5 min and times out.

**Fix:** stay at 4 local / 2 CI. Bump only after measuring.

### F5. Running multiple Playwright invocations in parallel (different terminals)

**Why bad:** they share `playwright/.clerk/user.json` write access. Race condition corrupts auth state for both.

**Fix:** sequential. Or accept one will fail with "auth state not ready" and re-run.

---

## G. Migration & Maintenance

### G1. Bumping `@clerk/testing` major in the same PR as feature work

**Why bad:** if Clerk introduces a breaking change to cookie names or signIn shape, you'll be debugging both auth AND your feature. Hours wasted.

**Fix:** Clerk bumps are their own PR. Run `npm run test:e2e:auth` first; verify; then merge.

### G2. Adding a `make e2e-*` target

**Why bad:** undocumented, runs Docker, eventually crashes someone's laptop.

**Fix:** add to `frontend/package.json` scripts as `npm run test:e2e:*`. Document in `SKILL.md`.

### G3. Removing the freshness gate to "simplify" setup

**Why bad:** every line of the gate covers a real bug. Removing them reintroduces the bugs within a week.

**Fix:** if you must change the gate, keep all four checks; only adjust the constants.

### G4. "Improving" `auth.fixture.ts` to "share state across tests"

**Why bad:** breaks isolation. One test's mutation leaks into another. Hours of debugging.

**Fix:** test isolation is non-negotiable. Each test gets its own context. Period.

### G5. Adding a new project without updating `playwright.config.ts` `dependencies`

**Why bad:** new project doesn't trigger setup. Gets undefined storageState. All tests fail.

**Fix:** `dependencies: ['setup']` on every project that needs auth.

---

## H. CI

### H1. "Just rerun" until green

**Why bad:** hides real flakes. They will eventually fire in production-blocking moments.

**Fix:** investigate every failure. If 3 reruns are needed to pass, the test is not green.

### H2. Bumping `retries: 5` to mask flakes

**Why bad:** masks instead of fixes. Flakes compound.

**Fix:** keep `retries: 2` on CI. If a test consistently uses retries, mark + investigate.

### H3. Adding `if: failure()` to skip cleanup

**Why bad:** leaves Docker volumes, eats disk, eventually fills the runner.

**Fix:** `cleanup: if: always()` (we do). Always.

### H4. Skipping the disk-cleanup step

**Why bad:** runner has 14 GB free; build needs ~25 GB. Run fails with "no space left on device" mid-build.

**Fix:** keep `Free disk space (~25 GB)` step.

### H5. Trying to set GH Secret values in workflow YAML

**Why bad:** secrets in committed code. `git log` reveals them forever.

**Fix:** secrets via `secrets.X` reference; values via GH Settings → Secrets.

---

## I. The "feels like a good idea but isn't" list

### I1. "Let me add a global beforeAll that pre-creates test data"

Tempting, but:
- Slows EVERY test, including those that don't need the data
- Hides what each test actually depends on
- Hard to mock per-test once you have it global

Use per-test fixtures instead. They're cheap.

### I2. "Let me write a custom Page Manager that orchestrates all POMs"

You're reinventing `test.use({})` and fixtures. Stop. Each test composes the POMs it needs.

### I3. "Let me convert all `getByText` to `getByTestId` for stability"

You're making tests opaque. Roles and labels test ACCESSIBILITY too. testids are an escape hatch, not a default.

### I4. "Let me add visual regression snapshots to every test"

Visual snapshots are EXPENSIVE (storage + diff time). Reserve for components that genuinely cannot be tested another way (charts, gradients, brand surfaces).

### I5. "Let me run E2E in parallel across 8 browsers"

We don't support 8 browsers. We support Chromium. Adding browsers without a customer demand is cargo cult.

### I6. "Let me cache `playwright/.clerk/user.json` in CI between runs"

Sounds smart, defeats the freshness gate, leaks state across runs, breaks the moment Clerk rotates a key. Don't.

### I7. "Let me catch the error and assert on the message"

```typescript
// ❌
try {
  await action();
} catch (e) {
  expect(e.message).toContain('blah');
}
```

You're testing the implementation of the error path AND silencing real test failures. Use `expect(action()).rejects.toThrow(/blah/)` if you genuinely test error paths — or just don't catch.

### I8. "Let me put my tests in a test/ folder under src/"

We standardize on `frontend/e2e/specs/`. Mixing E2E with unit tests confuses tooling (Vitest will try to pick them up).

---

## J. The two-question check before merging

For any PR that touches `frontend/e2e/**`:

1. **"Does this make the E2E suite faster, more reliable, or better-organized?"** If no, why are we adding it?
2. **"If I leave for 6 months, will this still make sense to the next person?"** If no, document or restructure.

If both answers are yes, ship it.
