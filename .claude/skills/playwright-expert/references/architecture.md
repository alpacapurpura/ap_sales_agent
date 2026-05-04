# Playwright E2E Architecture (Nicolify)

> **Read order:** if this is your first contact with the suite, read top to bottom once. Otherwise jump to the section that matches your concern.

## 1. Why Playwright at all

E2E tests answer one question that unit tests cannot: **"Does the user actually get the experience we promised?"** They run the real browser, the real Clerk session, the real Next.js render pipeline, against the real (or carefully mocked) backend.

In Nicolify the value is concentrated in three places:
1. **Auth flows** — Clerk + multi-tenant routing must not regress. A broken sign-in is a P0.
2. **Critical UI primitives** — sidebar, navigation, copilot drawer, brand/offer studios. These are the spines of every other screen.
3. **Data-driven dashboards** — Growth Studio renders depend on overview/summary endpoints. A missing channel card means a customer thinks their integration is broken.

Everything else (per-component logic, hooks, utilities) is better tested with Vitest — faster, isolated, deterministic.

## 2. The five projects

Defined in `frontend/playwright.config.ts`. Each project = a distinct slice of the suite with its own contract, its own timing budget, its own dependencies.

```
                 ┌────────────────────────────────────────┐
                 │  setup    (clerk.setup.ts, serial)     │
                 └────────────────────────────────────────┘
                 ▲ dependencies: ['setup']      ▲
                 │                              │
   ┌─────────────┼─────────┬──────────────┬─────┴─────┐
   │             │         │              │           │
┌──┴──┐    ┌────┴───┐  ┌──┴──┐      ┌────┴────┐  ┌───┴───┐
│smoke│    │regress.│  │public│      │ visual  │  │verify │
└─────┘    └────────┘  └──────┘      └─────────┘  └───────┘
```

| Project | Match | Auth? | Parallel? | Timeout | Purpose |
|---|---|---|---|---|---|
| `setup` | `*.setup.ts` | runs auth | serial (forced) | 60s | Run `clerkSetup()` once + create/refresh `playwright/.clerk/user.json` |
| `smoke` | `*.smoke.spec.ts` | uses storageState | parallel | 60s | Critical-route render + first-action checks; runs every PR |
| `regression` | other `*.spec.ts` in `regression/` | uses storageState | parallel | 60s | Multi-step user flows; runs pre-release |
| `public` | `*.public.spec.ts` | NO auth | parallel | 60s | Unauthenticated landing/booking pages |
| `visual` | `*.visual.spec.ts` | uses storageState | parallel | 60s | Pixel-diff against baseline |
| `verify` | `*.verify.spec.ts` | uses storageState | parallel | 600s | Real LLM end-to-end (no mocks) |

The `dependencies: ['setup']` clause means: **before any test in the dependent project runs, the entire `setup` project must succeed**. If setup fails, Playwright skips the dependents and reports cleanly.

## 3. The setup project — what it actually does

File: `frontend/e2e/setup/clerk.setup.ts`

Two sequential setup tests (`mode: 'serial'` enforced):

### Test 1: `clerk setup`
Invokes `clerkSetup()` from `@clerk/testing/playwright`. Side effects:
- Reads `CLERK_SECRET_KEY` from env
- Calls `POST https://api.clerk.com/v1/testing_tokens` to fetch a session-scoped testing token
- Sets `process.env.CLERK_TESTING_TOKEN = <token>` for the current Node process
- Returns; nothing persisted to disk

Why this matters: the testing token is what bypasses Clerk's bot protection (Cloudflare Turnstile + heuristics). Without it, `clerk.signIn()` will be blocked or rate-limited within minutes.

### Test 2: `authenticate`
Three-stage logic with a freshness gate, retry, and sanity check.

```
                    ┌────────────────────────┐
                    │ user.json exists AND   │
                    │ < 4h old AND           │
                    │ cf_bm cookie still     │ ── YES ──> SKIP (return early)
                    │ valid for >5min AND    │
                    │ has __session/__client │
                    │ cookie?                │
                    └────────────────────────┘
                              │ NO
                              ▼
                    ┌────────────────────────┐
                    │ wipe stale user.json   │
                    │ mkdir -p target dir    │
                    │ setupClerkTestingToken │
                    │   ({ page })           │
                    └────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────────┐
            │ for attempt in 1..3:                │
            │   page.goto('/sign-in')             │
            │   clerk.signIn({ password creds })  │
            │   page.goto('/')                    │
            │   assert window.Clerk.session       │
            │   storageState({ path: authFile })  │
            │   on success: return                │
            │   on error: wipe + backoff 3*N s    │
            └─────────────────────────────────────┘
```

The freshness gate is the most important architectural decision in the suite — it solves the historical "siempre falla cuando más lo necesito" by making auth state self-healing without paying the 15s sign-in cost on every run.

### Why the sanity check matters
`clerk.signIn()` returns successfully even when the SPA hasn't finished hydrating Clerk's client. We have observed cases where the call resolves but `window.Clerk.session` is still `undefined` 200ms later — the resulting `storageState` then has cookies but no live session, and every dependent test fails with redirects to `/sign-in`. Forcing `page.goto('/')` + `await page.evaluate(...)` reads the live session and turns this silent corruption into a loud retry.

## 4. The auth fixture — what it does per test

File: `frontend/e2e/fixtures/auth.fixture.ts`

```typescript
export const test = base.extend<TenantFixtures>({
  tenantId: [process.env.E2E_TENANT_ID!, { option: true }],
  page: async ({ page, tenantId }, use) => {
    await setupClerkTestingToken({ page });           // (a)
    await page.addInitScript((tid) => {
      localStorage.setItem('x-tenant-id', tid);       // (b)
    }, tenantId);
    await use(page);                                  // (c)
  },
});
```

Three things every test gets, automatically, with zero ceremony:

| Step | What | Why |
|---|---|---|
| (a) | Inject `CLERK_TESTING_TOKEN` into all Clerk FAPI requests for this page | Bypass Cloudflare bot protection for the LIFETIME of this test, not just the setup |
| (b) | Seed `localStorage.x-tenant-id` BEFORE first script runs | `fetchClient` reads this to inject `X-Tenant-ID` header into every backend call; without it, every API request 403s |
| (c) | Hand the augmented `page` to the test | Tests just write `test('x', async ({ page, tenantId }) => ...)` and get auth + tenant for free |

Tests **must** import `test` from this fixture, not from `@playwright/test` directly. Otherwise (a) and (b) don't run and the test fails in confusing ways.

```typescript
// ✅ correct
import { test, expect } from '../../fixtures/auth.fixture';

// ❌ broken — missing token + tenant
import { test, expect } from '@playwright/test';
```

## 5. Environment variable flow

The Node process running Playwright is **separate** from the Next.js process running the dev server. Each has its own env. Cross-pollination requires explicit wiring.

```
                          ┌──────────────────────────┐
                          │   /home/chris/AISALESHT  │
                          │   /.env  (single source) │
                          └────────────┬─────────────┘
                                       │
                                       ▼
                       ┌───────────────┴───────────────┐
                       │                               │
                       ▼                               ▼
           ┌─────────────────────┐         ┌─────────────────────┐
           │  Next.js dev server │         │  Playwright runner  │
           │  reads .env via     │         │  reads .env via     │
           │  built-in dotenv    │         │  playwright.config  │
           │                     │         │  dotenv.config(...) │
           └─────────────────────┘         └─────────────────────┘
                                                       │
                                                       │ override (optional)
                                                       ▼
                                           ┌─────────────────────┐
                                           │  frontend/.env.e2e  │
                                           │  (gitignored)       │
                                           └─────────────────────┘
```

Required vars (`playwright.config.ts` fails fast if missing):
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk dev instance public key
- `CLERK_SECRET_KEY` — needed by `clerkSetup()` to mint testing tokens
- `E2E_CLERK_USER_EMAIL` — test user's identifier
- `E2E_CLERK_USER_PASSWORD` — test user's password (configured in Clerk dashboard)
- `E2E_TENANT_ID` — UUID of the seeded test tenant

Optional:
- `CLERK_TESTING_TOKEN` — if pre-set, `clerkSetup()` reuses it instead of fetching; CI does this
- `E2E_BASE_URL` — if set, Playwright skips `webServer` and points at this URL

Misconfigured? `playwright.config.ts` throws BEFORE the first test runs:

```
Error: [playwright.config] Missing required env vars for Clerk E2E setup:
  E2E_CLERK_USER_EMAIL, E2E_TENANT_ID. Check /home/chris/AISALESHT/.env.
```

This is intentional and expensive to remove — it has saved hours of "why doesn't auth work" debugging.

## 6. Test isolation guarantees

Playwright spawns a fresh browser context per test (cookies, localStorage, sessionStorage all isolated). The `storageState` is *imported* into each context; modifications during a test do not leak back to disk.

What is shared:
- `playwright/.clerk/user.json` — read-only at test start, written ONLY by setup project
- `process.env.CLERK_TESTING_TOKEN` — set by setup, read by per-test `setupClerkTestingToken()` (per worker; if undefined, the helper fetches a fresh token from Clerk API)
- `playwright-report/` — HTML report aggregating all workers
- `test-results/` — per-test traces, screenshots, videos

What is NOT shared:
- Database state — tests must not mutate; if they must, restrict to known tenant + clean up
- Cookies between tests in same project — each test gets its own browser context
- LocalStorage between tests — same as cookies

## 7. Run modes — local vs CI

| Mode | Workers | Retries | Trace | Video | webServer |
|---|---|---|---|---|---|
| Local, dev container running, `E2E_BASE_URL=http://localhost:3000` | 4 | 1 | on-first-retry | on-first-retry | skipped (uses dev server) |
| Local, no env override | 4 | 0 | on-first-retry | on-first-retry | spawns `npm run dev` (slow, avoid) |
| CI (`process.env.CI`) | 2 | 2 | on-first-retry | on-first-retry | uses Docker compose service |

Both modes share: `actionTimeout: 15s`, `navigationTimeout: 45s`, `timeout: 60s` per test (600s for `verify`).

## 8. Where new tests go (taxonomy)

```
frontend/e2e/
├── setup/
│   └── clerk.setup.ts                                     ← auth bootstrap; do not duplicate
├── fixtures/
│   ├── auth.fixture.ts                                    ← THE entry point for any authenticated test
│   ├── api-mock.fixture.ts                                ← generic page.route helpers
│   ├── copilot-chat.fixture.ts                            ← Copilot SSE mocks
│   ├── growth-studio.fixture.ts                           ← Growth dashboard summary/overview mocks
│   ├── meta-ads-{setup,mock-data}.ts                      ← Meta Ads provider mocks
│   ├── ig-organic-{setup,mock-data}.ts                    ← Instagram organic mocks
│   ├── yt-organic-{setup,mock-data}.ts                    ← YouTube organic mocks
│   ├── mail-dashboard-{setup,mock-data}.ts                ← Email dashboard mocks
│   ├── offer-studio.fixture.ts                            ← Offer Studio data
│   └── test-data.ts                                       ← canonical fixtures (tenants, users, tokens)
├── pages/
│   └── *.page.ts                                          ← One POM per visited page
└── specs/
    ├── smoke/*.smoke.spec.ts                              ← every PR
    ├── regression/{domain}/*.spec.ts                      ← pre-release
    ├── public/*.public.spec.ts                            ← unauthenticated routes
    ├── visual/*.visual.spec.ts                            ← pixel diffs
    ├── verify/*.verify.spec.ts                            ← real LLM, nightly
    └── perf/*.spec.ts                                     ← performance budgets (LCP, bundle)
```

Adding a test in the wrong directory is a common mistake. A test in `regression/` named `*.smoke.spec.ts` will be picked up by BOTH projects and run twice. Match suffix to directory.

## 9. The CI pipeline

File: `.github/workflows/e2e-tests.yml`

Triggers:
- `push` to `development` (paths-filtered to `frontend/**` + workflow file)
- `pull_request` to `development` or `main` (same path filter)
- `workflow_dispatch` (manual, with suite selector)

Steps (per run):
1. Checkout
2. Free disk space (~25 GB) — Docker images + Android SDK + dotnet eat the runner
3. Materialize `.env` from GH Secrets (Clerk keys, test user, test tenant ID)
4. **Generate `CLERK_TESTING_TOKEN`** via `curl POST https://api.clerk.com/v1/testing_tokens` and append to `.env`. This is what enables CI to bypass `clerkSetup()`'s API call.
5. `docker compose up -d --build` — bring up postgres, redis, qdrant, api_dev, client_dashboard_dev
6. Wait for Next.js to be healthy (poll `wget` 30 × 10s)
7. Run Alembic migrations
8. Seed E2E tenant via `docker exec ... psql`
9. Run Playwright via `docker compose --profile e2e run --rm e2e_runner`
10. Cleanup
11. Upload `playwright-report/` + `test-results/` artifacts (7-day retention)

Locally, you do NOT need any of this — your dev container is already up. `npm run test:e2e:smoke` against `E2E_BASE_URL=http://localhost:3000` is the equivalent of CI's step 9.

## 10. Why we do not run E2E inside Docker locally

Empirically: WSL2 + Docker + Chromium = OOM crash within 5 minutes. Chris has reproduced this multiple times across two laptops. The `make e2e*` targets exist for legacy reasons — they are scheduled for removal but until then **do not invoke them**. Use `npm run test:e2e:*` from the host.

CI is fine because (a) the runner has 16 GB and (b) Docker on Linux is not WSL2.

## 11. The 4-hour freshness window — why this number

A Clerk session JWT lives for 60 seconds and refreshes via the `__client` cookie, which lives 7 days. So the session itself is fine for days.

The constraint comes from `__cf_bm` — Cloudflare's bot management cookie. It expires in ~30 minutes. When it expires, the next request to `*.clerk.accounts.dev` triggers a Turnstile challenge, which Playwright cannot solve.

`setupClerkTestingToken({ page })` injects a header that bypasses this — but only if the cookie is also still considered "fresh" by Cloudflare's anti-replay. We picked 4 hours empirically: any longer and we see ~5% of runs hit a Turnstile challenge mid-test even with the testing token.

If you increase this window, you trade test speed for flake rate. We tried 24h. It was bad.

## 12. Ratchet rules (shrink-only invariants)

- **`workers`** can only go UP, never down. Currently 4 local / 2 CI.
- **Number of `test.skip` calls** can only decrease. Currently 0 in primary suites.
- **Test count per project** can only grow. Deletions require PR-level justification.
- **`actionTimeout` / `navigationTimeout`** can only go DOWN. If you need more time, your test is fighting the substrate — fix the substrate.
- **Locator quality**: replacements MUST move toward `getByRole`, never away.

When a future agent (including future you) is tempted to "just bump the timeout to make it green" — re-read this section.
