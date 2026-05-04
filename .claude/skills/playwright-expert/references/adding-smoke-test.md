# Recipe — Adding a New Smoke Test

> **Read when:** the user says "agreguemos un smoke", "necesito test E2E para X", "smoke de la nueva ruta", "test integral de Y", or any new UI page lands on `development`.

This is the most common task this skill is invoked for. Follow the steps in order. Do not skip the preflight or the dry-run; they catch 80% of mistakes before they hit CI.

---

## Pre-conditions

Before starting:
- [ ] The page/feature you want to test exists in `frontend/src/app/**` and renders successfully under `dev-app.nicolify.com` or `localhost:3000`.
- [ ] You can manually navigate to the URL in a browser (you know the route works).
- [ ] You can describe in one sentence what the test asserts. ("The page renders with the expected H1 and the primary CTA is clickable.")
- [ ] Dev container is running (`make dev` or `docker compose ps` shows `visionarias_client_dev` healthy).

If any precondition is unmet, fix it before writing the test.

---

## Step 0 — Decide WHAT to assert

A smoke test answers two questions:
1. **Does the page render at all?** (no 500, no white screen, no client-side crash)
2. **Is the primary user intent reachable?** (the H1 is visible, the main CTA exists, the table loads its first row)

It does NOT answer:
- "Does form submission save to the database?" → that's `regression` or backend integration test
- "Does the chart show the right numbers?" → that's a unit test on the data layer
- "Does the page look pixel-identical?" → that's `visual`

**Anti-pattern:** smoke tests with 10+ steps. If your test is that long, it is a regression test. Move it.

---

## Step 1 — Pick the right project

| Route is... | Auth? | Project | Suffix |
|---|---|---|---|
| Authenticated dashboard, app, or studio | yes | `smoke` | `.smoke.spec.ts` |
| Public landing page, booking flow, marketing | no | `public` | `.public.spec.ts` |
| Multi-step flow that already has a smoke for the entry point | yes | `regression` | `.spec.ts` |
| Real LLM end-to-end (AI interview, sales agent) | yes | `verify` | `.verify.spec.ts` |

For "agreguemos un smoke," the answer is almost always `smoke` + `.smoke.spec.ts`.

---

## Step 2 — Create or extend a Page Object Model (POM)

POMs live in `frontend/e2e/pages/`. Pattern: one POM per page (or per closely related set of pages).

**Decision:** does a POM already cover this page?

```bash
ls /home/chris/AISALESHT/frontend/e2e/pages/
```

- **If yes:** open it. Add a method for the new interaction. Skip to Step 3.
- **If no:** create `<feature-name>.page.ts`. Use this template:

```typescript
// frontend/e2e/pages/<feature-name>.page.ts
import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class <FeatureName>Page {
  readonly page: Page;
  readonly heading: Locator;
  readonly primaryAction: Locator;

  constructor(page: Page) {
    this.page = page;
    // Use getByRole > getByLabel > getByText. Never CSS/XPath.
    this.heading = page.getByRole('heading', { name: /<expected text>/i });
    this.primaryAction = page.getByRole('button', { name: /<expected button>/i });
  }

  async goto(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/<route-path>`);
  }

  async expectLoaded(): Promise<void> {
    await expect(this.heading).toBeVisible({ timeout: 10_000 });
  }

  // Add ONE method per user-visible action. Keep them tight.
  async clickPrimaryAction(): Promise<void> {
    await this.primaryAction.click();
  }
}
```

**POM rules** (from `references/pom-patterns.md`):
- Public locators are `Locator` instances declared in the constructor — never strings.
- Methods are imperatives (`clickSave`, `fillName`), not getters.
- Assertions live in dedicated `expect*()` methods, not scattered throughout.
- Locators use `getByRole`/`getByLabel`/`getByText`; if you must use a test ID, name it `data-testid="<feature>-<element>"`.

---

## Step 3 — Write the spec

File: `frontend/e2e/specs/smoke/<feature-name>.smoke.spec.ts`

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import { <FeatureName>Page } from '../../pages/<feature-name>.page';

test.describe('<Feature> smoke', () => {
  test('page renders and primary CTA is reachable', async ({ page, tenantId }) => {
    const featurePage = new <FeatureName>Page(page);

    await featurePage.goto(tenantId);
    await featurePage.expectLoaded();
    await expect(featurePage.primaryAction).toBeVisible();
  });
});
```

**Mandatory imports:**
- `test` and `expect` from `../../fixtures/auth.fixture` — NEVER from `@playwright/test` directly
- The POM you just wrote/extended

**Mandatory parameters in the test callback:**
- `page` — Playwright's auto-injected page (with token + tenant pre-applied by the fixture)
- `tenantId` — fixture-injected; never hardcode

**Anti-patterns to NOT introduce:**
- `await page.waitForTimeout(1000)` — use auto-retrying `expect(...).toBeVisible()` instead
- `page.locator('.css-class-xyz')` — use `getByRole` etc.
- `expect(await locator.isVisible()).toBe(true)` — use web-first `await expect(locator).toBeVisible()`
- Hardcoded text in Spanish that uses voseo (`'Guardá'`) — use neutro (`'Guarda'`) or regex `/guard[áa]/i` if old code still uses voseo

---

## Step 4 — Verify the substrate

Before running the test, confirm preflight is green:

```bash
bash /home/chris/AISALESHT/scripts/e2e-preflight.sh
```

Outputs you want to see:
- `Checking Docker containers... OK`
- `Checking frontend responds 200... OK`
- `Checking Clerk auth state... OK — XXmin old` (or "no cached state, setup project will create one")
- `Checking E2E env vars... OK`

If any line says FAIL, fix it before continuing. The preflight messages tell you the exact remedial command.

---

## Step 5 — Dry run (one test, headed mode)

Run JUST your new test, with the browser visible, so you can see exactly what happens:

```bash
cd /home/chris/AISALESHT/frontend
E2E_BASE_URL=http://localhost:3000 npx playwright test \
  e2e/specs/smoke/<feature-name>.smoke.spec.ts \
  --project=smoke --headed
```

Watch:
- Does the browser navigate to the right URL?
- Does the page render?
- Does the assertion pass?
- If it fails — read the error, look at the browser, do not blindly retry

Iterate locally until green. Then run without `--headed` to confirm it works headless too:

```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test \
  e2e/specs/smoke/<feature-name>.smoke.spec.ts \
  --project=smoke
```

---

## Step 6 — Run the FULL smoke project

Just because your test passes in isolation does not mean it passes in parallel with 13 others. Other tests share the same Clerk session, possibly the same tenant data, possibly the same mock state.

```bash
cd /home/chris/AISALESHT/frontend
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

If your test passes in isolation but fails in parallel:
- Race condition in the fixture (rare; flag to skill maintainer)
- Test depends on data another test mutated (smoke tests should not mutate; if it does, redesign to read-only)
- Clerk session got refreshed mid-suite (re-run with `npm run test:e2e:fresh`)

---

## Step 7 — Commit, push, watch CI

Stage and commit ONLY your new files (per `parallel-safety.md`):

```bash
git add frontend/e2e/specs/smoke/<feature-name>.smoke.spec.ts
git add frontend/e2e/pages/<feature-name>.page.ts
git status   # confirm only your files are staged
git commit -m "test(e2e): add smoke for <feature>"
git push origin development
```

Watch CI:

```bash
gh run watch
# or
gh run list --workflow=e2e-tests.yml --limit=1
```

If CI fails but local passes:
1. Click the failed run in GH; download `playwright-report-smoke` artifact
2. `npx playwright show-report path/to/extracted/playwright-report` and look at the trace
3. Common CI-only failures: timing (CI is slower; bump `actionTimeout` for THAT test only), missing seed data, env var typo in workflow

---

## Recipe variants

### Variant A — adding a smoke for a public (unauthenticated) route

```typescript
// frontend/e2e/specs/public/<feature-name>.public.spec.ts
import { test, expect } from '@playwright/test';   // ← NO fixture; public routes don't need auth

test('public landing renders', async ({ page }) => {
  await page.goto('/landing/<slug>');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});
```

Public tests live in their own project (`public`); they do not load `storageState` and do not get tenant injection.

### Variant B — adding a smoke for a route that needs mocked data

If your page calls a backend endpoint that returns no useful data in the test tenant:

```typescript
import { test, expect } from '../../fixtures/auth.fixture';

test('dashboard renders with mocked metrics', async ({ page, tenantId }) => {
  await page.route(`**/api/v1/<endpoint>`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ /* shape your component expects */ }),
    }),
  );
  await page.goto(`/${tenantId}/dashboard`);
  await expect(page.getByText(/<expected mocked content>/)).toBeVisible();
});
```

For complex mock setups (Growth Studio, Copilot SSE, Meta/IG/YT providers), use the corresponding fixture in `frontend/e2e/fixtures/`. See `references/fixtures-and-mocks.md`.

### Variant C — adding a smoke for a flow that opens a modal/dialog

```typescript
test('opens campaign creation dialog', async ({ page, tenantId }) => {
  await page.goto(`/${tenantId}/sales/campañas`);
  await page.getByRole('button', { name: /crear campaña/i }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('dialog').getByLabel(/nombre/i)).toBeVisible();
});
```

Note: `getByRole('dialog')` works because Shadcn UI's `Dialog` uses Radix primitives with the right ARIA role. Don't depend on CSS classes.

### Variant D — adding a smoke for a route inside a section with `[tenantId]` segment

All authenticated routes in Nicolify nest under `/[tenantId]/...`. The `auth.fixture.ts` injects `tenantId` for you; use it:

```typescript
await page.goto(`/${tenantId}/brand-studio/identidad`);
```

Never write `/123e4567-e89b-12d3-a456-426614174000/...`. Hardcoded tenants leak between environments and break in CI.

---

## What "good" looks like — a complete reference example

Paired files: `frontend/e2e/specs/smoke/navigation.smoke.spec.ts` + `frontend/e2e/pages/navigation.page.ts`. Read these whenever you are unsure what a clean smoke + POM looks like in this codebase. They are the canonical pair.

---

## Common mistakes by frequency

1. **Importing `test` from `@playwright/test`** (top-line statement) — token + tenant won't be injected. Symptom: 403/redirect to /sign-in.
2. **Hardcoding text the FE displays** — when copy changes, test breaks. Use regex `/configura/i` to be tolerant; assert SEMANTIC roles, not exact strings.
3. **Adding `await page.waitForTimeout(N)`** — flake guarantee. Use `await expect(...).toBeVisible({ timeout: N })` instead.
4. **CSS-class locators** — break on Tailwind/Shadcn version bumps. Use roles.
5. **Asserting on data that the test tenant doesn't have** — your test passes locally because YOU have data; CI tenant is empty. Mock the endpoint or seed.
6. **Forgetting `bash scripts/e2e-preflight.sh`** before debugging — wastes 5 min on a stale-auth issue that would have surfaced in 3 seconds.
7. **Not running the FULL `--project=smoke`** before pushing — your test passes alone, fails in parallel.

---

## Final checklist before opening the PR

- [ ] One `*.smoke.spec.ts` added under `frontend/e2e/specs/smoke/`
- [ ] POM added or extended in `frontend/e2e/pages/`
- [ ] Test imports `test` from `auth.fixture`, not `@playwright/test`
- [ ] Locators are role/label/text-based; no CSS/XPath
- [ ] Web-first assertions (`expect(locator).toBeVisible()`); no `waitForTimeout`
- [ ] Asserted text is Spanish neutro (no voseo)
- [ ] Test passes in isolation AND with the full `--project=smoke` run
- [ ] No `test.skip` introduced
- [ ] Git stage list contains ONLY your two files (no `git add .`)
- [ ] Commit message follows Conventional Commits: `test(e2e): add smoke for <feature>`
