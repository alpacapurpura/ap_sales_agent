# Clerk + Playwright — Deep Dive

> **Read when:** auth fails, "Bot traffic detected", "Clerk Frontend API URL is required", "signIn timed out", session expired mid-test, or before changing anything in `clerk.setup.ts` / `auth.fixture.ts` / `frontend/src/middleware.ts`.

This document explains *exactly why* Clerk + Playwright is hard, and what the Nicolify-specific design decisions are. After reading this, the failure modes catalogued at the end should look obvious instead of cryptic.

---

## 1. The three independent problems Clerk testing solves

When you load a Clerk-protected page in a real browser, three protection layers fire:

1. **Cloudflare Turnstile** — runs JavaScript challenges to prove a human typed the URL. Default behavior in Playwright = challenge appears, test stalls.
2. **Clerk's bot heuristics** — IP reputation, request fingerprint, rate of sign-in attempts. Default behavior with automation = `429 too many requests` or `403 bot detected`.
3. **Session validation** — even with valid cookies, the FE SPA must hydrate `window.Clerk` before any UI is interactive.

The `@clerk/testing` package provides three primitives — one per problem.

| Primitive | Solves | Where it runs |
|---|---|---|
| `clerkSetup()` | (1) and (2) — fetches a server-side **testing token** from the Clerk API that bypasses Turnstile + bot heuristics for the duration of the test session | Once per Playwright invocation, in the `setup` project |
| `setupClerkTestingToken({ page })` | (1) and (2) — installs a route interceptor that injects the testing token into every request to `*.clerk.accounts.dev` originating from `page` | Once per test, in the `auth.fixture.ts` |
| `clerk.signIn({ page, signInParams })` | (3) — performs a programmatic, password-based sign-in via the Clerk JS SDK; far more reliable than UI clicks | Once per setup, in `clerk.setup.ts` |

**Crucially:** the testing token from `clerkSetup()` lives in `process.env.CLERK_TESTING_TOKEN`. It must be *re-injected per page* via `setupClerkTestingToken({ page })` — having it in env is necessary but NOT sufficient. The interceptor must be installed on every browser context.

This is why our `auth.fixture.ts` calls `setupClerkTestingToken({ page })` in every test, even though the setup project already called `clerkSetup()`. The two work together; neither is redundant.

---

## 2. Why a pre-saved `storageState` is fast but fragile

Playwright's `storageState` is a JSON snapshot of cookies + localStorage + sessionStorage. By saving it once in `setup` and reusing it across hundreds of tests, we save ~10s × N test invocations.

The trade-off: **session state is time-sensitive**. The cookies inside `user.json` represent a moment in time. Specifically:

| Cookie | Set by | TTL | What happens when expired |
|---|---|---|---|
| `__client` (or `__session_*`) | Clerk | ~7 days | Session ends; user is unauthenticated; redirects to `/sign-in` |
| `__client_uat` | Clerk | session | Synced with `__client`; soft-expires earlier |
| `__cf_bm` | Cloudflare | ~30 min | New requests trigger Turnstile challenge |
| `_cfuvid` | Cloudflare | session | Visitor identifier; usually fine for hours |
| `__refresh` | Clerk | session | Used to refresh JWT; if expired, hard re-auth needed |

**The 4-hour freshness window** in our setup picks the smallest cookie TTL that matters under stress (`__cf_bm` ≈ 30 min) and adds a safety multiplier. We pick 4h not 30min because the testing token *usually* bypasses Cloudflare even with stale `__cf_bm`, but ~5% of the time it does not (anti-replay heuristic). 4 hours is the empirical sweet spot between "fast" (skip re-auth) and "reliable" (re-auth before stress hits).

If you change this constant, you are trading flake rate for speed. Document the trade-off.

---

## 3. The full freshness-gate algorithm (line-by-line)

```typescript
function isAuthFileFresh(): boolean {
  if (!fs.existsSync(authFile)) return false;             // never auth'd yet
  try {
    const stat = fs.statSync(authFile);
    const ageMs = Date.now() - stat.mtimeMs;
    if (ageMs > FRESH_WINDOW_MS) return false;            // gate 1: 4h hard limit on file mtime

    const raw = JSON.parse(fs.readFileSync(authFile, 'utf-8')) as {
      cookies?: Array<{ name: string; expires?: number }>;
    };
    const cookies = raw.cookies ?? [];
    if (cookies.length === 0) return false;               // gate 2: empty file = corrupted

    const nowS = Math.floor(Date.now() / 1000);
    const cfBm = cookies.find((c) => c.name === '__cf_bm');
    if (cfBm?.expires && cfBm.expires - nowS < CF_BM_SAFETY_MARGIN_S) return false;
                                                          // gate 3: cf_bm < 5min from expiry
    const clerkSession = cookies.find((c) =>
      c.name.startsWith('__session') || c.name.startsWith('__client')
    );
    if (!clerkSession) return false;                      // gate 4: no Clerk session cookie at all

    return true;                                          // all gates pass → reuse
  } catch {
    return false;                                          // any parse error → re-auth
  }
}
```

Each gate covers a real failure we have hit in production:
- **Gate 1**: simple time bomb. Ages out before any pathological cookie does.
- **Gate 2**: covers the "setup crashed mid-`storageState({ path })`" case where the file ends up `{}` or partial.
- **Gate 3**: the most subtle one. If you skip this, your tests start failing intermittently at 30+ minutes uptime with Turnstile challenges.
- **Gate 4**: paranoid — if Clerk renames cookies in a future major, or our regex is wrong, fail safe and re-auth.

---

## 4. The retry + sanity check loop

```typescript
let lastErr: unknown;
for (let attempt = 1; attempt <= SIGNIN_RETRIES + 1; attempt++) {
  try {
    await page.goto('/sign-in', { waitUntil: 'networkidle', timeout: 60_000 });
    await clerk.signIn({ /* password creds */ });

    await page.goto('/', { waitUntil: 'domcontentloaded', timeout: 30_000 });
    const isAuthed = await page.evaluate(() => {
      const w = window as unknown as { Clerk?: { session?: unknown } };
      return Boolean(w.Clerk?.session);
    });
    expect(isAuthed, 'Clerk session not active after signIn').toBe(true);

    await page.context().storageState({ path: authFile });
    return;
  } catch (err) {
    lastErr = err;
    wipeAuthFile();
    if (attempt <= SIGNIN_RETRIES) {
      await new Promise((r) => setTimeout(r, SIGNIN_BACKOFF_MS * attempt));
    }
  }
}
throw new Error(`Clerk auth failed after ${SIGNIN_RETRIES + 1} attempts: ${String(lastErr)}`);
```

Three engineering decisions encoded here:

### A. Wipe-on-failure
Why: a partial `storageState` from a failed sign-in is poison. The file may have cookies but no session. Reusing it on the next attempt corrupts the next test run. Always start fresh.

### B. Linear backoff (3s, 6s, 9s)
Why: Clerk's testing token endpoint and FAPI are usually back within seconds of a transient 5xx. Exponential backoff would slow us down for no reason. Linear is enough.

### C. The sanity check
Why: `clerk.signIn()` resolves successfully even when the SPA hasn't hydrated `window.Clerk`. We have observed this in CI under load — auth "succeeds" but the saved storageState is incomplete. Forcing one `page.goto('/')` and reading `window.Clerk.session` proves the SPA is interactive before we save.

If `isAuthed` is false:
- The error message is descriptive ("Clerk session not active after signIn")
- The current attempt is wiped and retried
- After 3 failures, the whole setup fails with the last error attached — Chris sees a real diagnostic, not "test timed out"

---

## 5. The per-worker propagation problem

Playwright spawns N worker processes for parallelism. Each worker gets a **fresh Node process** with a fresh `process.env`. The `CLERK_TESTING_TOKEN` set by `clerkSetup()` in the setup project's worker does NOT propagate to the smoke-project workers.

How this still works:
- Workers that need `setupClerkTestingToken({ page })` will, if `process.env.CLERK_TESTING_TOKEN` is undefined, **fetch a fresh token from the Clerk API on first use** (using `CLERK_SECRET_KEY` which IS in env).
- This adds ~200ms to the first test in each worker but is acceptable.

Alternative we considered and rejected: globalSetup function. Quoting Clerk's docs verbatim:

> "With a function-based `globalSetup`, the setup runs in a separate process and the environment variables set by `clerkSetup()` don't propagate to your test workers."

Project-based setup with `dependencies: ['setup']` is the canonical pattern and is what we use. Do not migrate away from it.

---

## 6. Why we re-inject the token in `auth.fixture.ts` and not just rely on storageState

Even with a valid storageState (cookies present), individual test pages need the testing token interceptor installed. Cookies alone do NOT bypass Cloudflare bot protection — they only authenticate the user once they have passed Cloudflare. The `setupClerkTestingToken({ page })` call adds a header that proves "this is a Playwright test, let me through."

If you remove the call from `auth.fixture.ts`:
- Setup will continue passing (the setup page got the token at signIn time)
- Tests will start failing intermittently when Cloudflare's `__cf_bm` cookie expires
- Failures look like "Bot traffic detected" or random 429s
- You will spend a day re-debugging this exact scenario

Don't.

---

## 7. Catalog of failure modes

When something goes wrong, match the symptom to a row, then jump to the fix.

| Symptom | Root cause | Fix |
|---|---|---|
| `Error: [playwright.config] Missing required env vars: ...` | env var literally missing from `.env` | Add to `.env`. Compare with `frontend/.env.e2e.example` |
| `Clerk Frontend API URL is required` | `clerkSetup()` did not run (you removed setup project? called helper outside fixtures?) | Confirm `dependencies: ['setup']` on the project. Re-run with `--project=setup` first |
| `Bot traffic detected` mid-test | `setupClerkTestingToken({ page })` not in fixture, OR `page` was created via `browser.newContext()` outside fixture | Ensure all tests `import { test } from '../../fixtures/auth.fixture'`. If you must `newContext()`, manually call `setupClerkTestingToken({ page: newPage })` |
| `signIn() timed out after 30000ms` | Clerk dev instance throttled OR password mismatch OR Clerk API outage | (1) Check Clerk dashboard for the test user; sync password. (2) Check Clerk status page. (3) `npm run test:e2e:auth` to retry with backoff |
| `Cookies invalid` / first navigation redirects to `/sign-in` | `storageState` stale (cookies expired) or corrupted | `npm run test:e2e:fresh` |
| Setup passes, smoke tests redirect to /sign-in | sanity check missed a partial sign-in (rare); OR storageState was saved from wrong base URL | (1) Re-run `npm run test:e2e:auth`. (2) Check `E2E_BASE_URL` matches the URL Clerk dev instance is configured for |
| `expect(isAuthed).toBe(true)` failed in setup | SPA didn't hydrate Clerk in 30s after sign-in | Check FE container logs for hydration errors. Possibly the dev server is OOM. `docker logs visionarias_client_dev --tail 100` |
| Setup runs but fails with `mtimeMs` error | Race: another concurrent setup writing the file | Don't run two `--project=setup` invocations in parallel. There's no lock. |
| Test fails locally fine, fails CI | CI uses Docker + a CI-generated `CLERK_TESTING_TOKEN`; check the GH Actions log step "Generate Clerk testing token" — if curl returned `null`, the secret is wrong | Verify GH Secret `CLERK_SECRET_KEY` matches Clerk dashboard |
| `__cf_bm` keeps expiring during long runs | Test suite > 30 min total; cookies aged out mid-run | Shard the suite (`--shard=1/3` etc.) so each shard is < 30 min |
| Setup passes 6 hours apart but smoke fails after | Freshness gate accepted the file but `__cf_bm` actually expired | Check `CF_BM_SAFETY_MARGIN_S`; we use 5min. Increase if Cloudflare changes its TTL |

---

## 8. What to do if Clerk is fundamentally down

You will know because:
- `clerkSetup()` fails with a 5xx from `api.clerk.com`
- All retries fail with the same error

Options:
1. **Wait.** Clerk has a status page; outages are usually brief.
2. **Skip E2E for the urgent merge.** Add `[skip-e2e]` to the commit message (CI workflow does not actually parse this; it's a signaling convention).
3. **Run only `public` project locally.** It does not require auth: `npx playwright test --project=public`.

Do NOT mock Clerk. The whole point of these tests is the real auth path. A mocked Clerk passes false-positively.

---

## 9. When to update Clerk packages

Bumping `@clerk/testing` major or `@clerk/nextjs` major may change:
- The shape of the `signInParams` accepted by `clerk.signIn()`
- The location of cookies (rename of `__session_*` → `__clerk_*` happened in 2025)
- The Turnstile bypass mechanism

Protocol:
1. Read the Clerk migration guide for the major bump.
2. Run `npm run test:e2e:auth` with the new version. If it fails, debug `clerk.setup.ts` first.
3. Run `npm run test:e2e:smoke`. If it fails for cookie reasons, update gate 4 of `isAuthFileFresh()` to match the new cookie names.
4. Run on CI. CI is the canary for Cloudflare interaction differences.

Never bump Clerk in the same PR as new feature code. Auth is its own blast radius.

---

## 10. The single thing to remember

If you forget everything else: **the freshness gate + retry + sanity check + per-fixture token injection all exist to make Clerk auth feel reliable on top of an inherently flaky substrate.** Each line of `clerk.setup.ts` and `auth.fixture.ts` is paying for a real failure mode we have hit. Removing any of them re-introduces the failure within a week.

When in doubt, do not "simplify" the setup file. Add more guards, never fewer.
