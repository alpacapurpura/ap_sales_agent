---
name: playwright-expert
description: "Use this skill ANY time you write, debug, run, audit, extend, or even *think about* Playwright E2E tests in Nicolify. Activate when the user mentions: 'smoke test', 'e2e', 'playwright', 'tests E2E', 'agreguemos un smoke', 'el smoke falla', 'auth de Clerk en tests', 'test:e2e', 'spec.ts', 'storageState', 'auth.fixture', 'POM', 'page object', 'browser test', 'test integral', 'preflight', 'test que abra el navegador', 'verificar el flujo X end-to-end', 'CI de Playwright', 'fixtures de Playwright', '/test-all flake', 'playwright report', 'trace viewer', 'visual regression Playwright', 'verify project', 'Clerk testing token', 'CLERK_TESTING_TOKEN', 'playwright/.clerk/user.json', 'Bot traffic detected', 'Clerk Frontend API URL is required', 'session expired Playwright'. ALSO trigger proactively before any commit/PR that touches `frontend/e2e/**` or any UI flow that could affect smoke tests, and before any GH Actions change to `e2e-tests.yml`. Covers: Clerk auth lifecycle (testing token + storageState + freshness gate + retry + sanity check), Page Object Models, network mocking with `page.route`, multi-tenant fixture, sharding, flaky-test debugging via trace viewer, and Nicolify-specific anti-patterns (NEVER `make e2e*` Docker — crashes the laptop). When in doubt, USE this skill — under-triggering Playwright knowledge is the #1 cause of broken E2E suites in this codebase."
---

# Playwright Expert (Nicolify)

Single source of truth for E2E testing in Nicolify. Anchors on Playwright 1.59+, `@clerk/testing` 2.x, `@clerk/nextjs` 6.36+, native WSL execution, and the multi-tenant + Clerk + Cloudflare Turnstile reality of this codebase.

> **Mantra:** *"E2E tests are not flaky. Auth is flaky. Networks are flaky. Mocks are flaky. The test runner is deterministic — fix the substrate, not the test."*

---

## Stop. Read first, do not assume.

Before changing anything in `frontend/e2e/**`, the architect-level mental model lives in:

| Concern | SSoT | Read when |
|---|---|---|
| **End-to-end pipeline architecture** (projects, deps, fixtures, env flow) | `references/architecture.md` | First time touching this skill or after a Playwright major bump |
| **Clerk auth — full lifecycle** (testing token, cf_bm cookie, freshness gate, retry, sanity check, multi-worker) | `references/clerk-auth-deep-dive.md` | Auth fails, "Bot traffic detected", "Clerk Frontend API URL is required", session expired, signIn flake, storageState corruption |
| **Recipe: add a new smoke test** (the most common future task) | `references/adding-smoke-test.md` | User asks "agreguemos un smoke para X", "necesito test de Y", "smoke de la nueva ruta", or any new UI page lands |
| **Page Object Models — patterns + locator priority** | `references/pom-patterns.md` | Writing/refactoring a POM, choosing a locator, debugging "element not found" |
| **Fixtures + network mocks** | `references/fixtures-and-mocks.md` | `auth.fixture.ts`, growth-studio mocks, Copilot SSE mocks, mocking external APIs (Meta/IG/YT/Email) |
| **CI + flaky test debugging** | `references/ci-and-flaky-tests.md` | Test passes locally fails CI, trace viewer, sharding, retry tuning, GH Actions changes |
| **Anti-patterns — what NEVER to do** | `references/anti-patterns.md` | Reviewing a PR that touches e2e, before merging, when about to write something that "feels off" |
| **Project-specific Spanish neutro** | `.claude/rules/spanish-text.md` | Any user-visible string asserted in tests (`getByText('Configura...')`) |

**Rule of thumb:** if the question is "how do I make Playwright/Clerk/auth work?" → `clerk-auth-deep-dive.md`. If "how do I write a test?" → `adding-smoke-test.md`. If "why is it flaky?" → `ci-and-flaky-tests.md`.

---

## The 3-second mental model

```
                                ┌────────────────────────────────────────┐
                                │  setup project (clerk.setup.ts)        │
                                │  ─ clerkSetup() once                   │
                                │  ─ if user.json fresh & valid → SKIP   │
                                │  ─ else: signIn 3x retry → sanity →    │
                                │            save storageState           │
                                └────────────────────────────────────────┘
                                                  │ dependencies: ['setup']
                                                  ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │  smoke   │    │regression│    │  public  │    │  verify  │
   │ ~14 tests│    │ ~10 tests│    │ ~2 tests │    │ ~1 test  │
   └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │                │                │
       ▼ each test:    ▼                ▼                ▼
   auth.fixture inject CLERK_TESTING_TOKEN per page → load storageState →
   addInitScript(localStorage.x-tenant-id) → run test → trace on retry
```

Three actors, three failure modes:

| Actor | Failure mode | Fix in |
|---|---|---|
| `clerk.setup.ts` | stale storageState, signIn rejected, Cloudflare challenge | `references/clerk-auth-deep-dive.md` |
| `auth.fixture.ts` | testing token not injected → "Bot traffic detected" mid-test, tenant header missing | `references/fixtures-and-mocks.md` |
| Test body | flaky locator, race condition, missing mock | `references/pom-patterns.md` + `references/ci-and-flaky-tests.md` |

---

## Diagnostic flow — when something breaks

Run **in this exact order**. Skip steps and you waste 20 minutes.

```
1. Identify the symptom precisely:
   ├─ "Bot traffic detected" / Cloudflare challenge      → CLERK token missing
   ├─ "Clerk Frontend API URL is required"               → clerkSetup() didn't run
   ├─ "signIn() timed out"                               → password/email mismatch OR Clerk API outage
   ├─ "Cookies invalid"/redirected to /sign-in mid-test  → storageState stale
   ├─ "Element not found" / locator timeout              → POM drift OR mock missing
   ├─ "page.goto: net::ERR_CONNECTION_REFUSED"           → FE container down
   └─ "Browser closed / Target closed"                   → Crash OOM (E2E inside Docker — FORBIDDEN)

2. Run preflight (3s, catches 80%):
   bash /home/chris/AISALESHT/scripts/e2e-preflight.sh

3. Tail the failing trace:
   cd frontend && npx playwright show-report --host 0.0.0.0
   # Click failing test → "Trace" tab → step through actions, screenshots, network

4. Force fresh auth + rerun ONE failing test:
   npm run test:e2e:auth   # wipes user.json + reauthenticates
   cd frontend && npx playwright test path/to/the-spec.ts --project=smoke --headed

5. If still failing — load reference matching the actor (clerk-auth | pom | mocks).
```

Never debug "in general." Pick the failing actor, load that reference.

---

## Daily commands (memorize these)

All commands run NATIVE in WSL from `frontend/`. **NEVER** `make e2e*` (Docker, crashes the laptop).

```bash
# ─── happy path (cached auth ≤ 4h) ────────────────────────────────
npm run test:e2e:smoke               # smoke project, parallel workers

# ─── auth feels stale / "siempre falla" ───────────────────────────
npm run test:e2e:fresh               # wipe user.json + run smoke
npm run test:e2e:auth                # wipe + run setup project ONLY (regenerate storageState)

# ─── debugging ────────────────────────────────────────────────────
cd frontend && npx playwright test --project=smoke --headed                # see browser
cd frontend && npx playwright test --project=smoke --debug                 # step-by-step
cd frontend && npx playwright test path/to/x.smoke.spec.ts --project=smoke # one file
cd frontend && npx playwright show-report --host 0.0.0.0                   # HTML report + traces
cd frontend && npx playwright test --ui --ui-host 0.0.0.0                  # watch mode

# ─── full suites ──────────────────────────────────────────────────
cd frontend && npx playwright test --project=regression
cd frontend && npx playwright test --project=verify   # AI-driven, 10min/test

# ─── preflight (run before every Playwright invocation) ───────────
bash /home/chris/AISALESHT/scripts/e2e-preflight.sh
```

**Always set `E2E_BASE_URL`** if you don't want Playwright to spawn its own `next dev`:

```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

The `playwright.config.ts` will SKIP its `webServer` block when `E2E_BASE_URL` is set — this is what you want when the dev container is already running.

---

## What a healthy run looks like

```
[clerk.setup] auth file fresh — skipping re-auth     ← OR ← [clerk.setup] auth state saved (attempt 1)
Running 14 tests using 4 workers
  ✓  smoke/navigation.smoke.spec.ts (3.2s)
  ✓  smoke/copilot-sidebar.smoke.spec.ts (4.1s)
  ✓  smoke/brand-crud.smoke.spec.ts (5.7s)
  ...
  14 passed (35s)
```

**Red flags even when "passing":**
- `attempt 2` or `attempt 3` in the setup log → Clerk is degraded; investigate via Clerk dashboard
- Setup taking >25s → cf_bm cookie misconfig, or Clerk dev instance throttling
- More than 1 test retried → flaky locator or missing mock — fix it, do not normalize retries
- Trace size >10 MB per test → too many network logs; consider scoping `trace: 'retain-on-failure'`

---

## When to write a smoke vs regression vs verify vs visual

| Type | Suffix | Trigger | Mocked? | Time | Owner of golden path |
|---|---|---|---|---|---|
| `smoke` | `.smoke.spec.ts` | Every PR. New route, critical UI primitive (sidebar, nav, auth gate), public page | Mostly mocked (auth real, data mocked) | <8s/test | Page renders 200, h1 visible, no console error |
| `regression` | `.spec.ts` (no other suffix in `regression/`) | Multi-step flow that has broken before. Pre-release | Selectively mocked | 15-60s/test | Full happy path of one user story |
| `public` | `.public.spec.ts` | Landing pages, booking — anything UNAUTHENTICATED | Real backend | <10s/test | SEO meta + initial render |
| `visual` | `.visual.spec.ts` | UI library / design tokens / brand surface that must not pixel-shift | Mocked | <5s/test | Screenshot diff vs baseline |
| `verify` | `.verify.spec.ts` | Real LLM run end-to-end (AI interview, sales agent close). Run nightly or on-demand | NOT mocked | 5-12min/test | Real Claude/DeepSeek call returns expected shape |

**Rule:** if you are about to write a new test and unsure → `smoke`. If a smoke turns out to need 20 steps and 4 mocks → split it: smoke covers "renders + first action," regression covers the long flow.

---

## When you MUST extend the suite (recipes)

User says... | Skill action
---|---
"Agreguemos smoke para la nueva pantalla de X" | Open `references/adding-smoke-test.md`. Walk steps 1-7 with Chris. Output: 1 spec + 1 POM (or extend) + green CI run.
"El smoke de Y se cuelga" | Step 1-5 of diagnostic flow above. Then `references/ci-and-flaky-tests.md` if it persists.
"Reescribamos los POMs" | `references/pom-patterns.md`. Audit locators; convert any CSS/XPath to `getByRole`.
"Tenemos un endpoint nuevo del backend, hay que mockearlo" | `references/fixtures-and-mocks.md` § "Network mocking with `page.route`".
"Configuremos el CI para correr regression nightly" | `references/ci-and-flaky-tests.md` § "GH Actions wiring".
"Estamos cambiando la lógica de Clerk en el FE" | Re-read **all** of `references/clerk-auth-deep-dive.md` BEFORE touching `clerkMiddleware`. Then run `npm run test:e2e:auth` to confirm setup still passes.
"Voy a borrar `playwright/.clerk/`" | Sí. Es `.gitignore`d. Setup project lo regenera. Sin riesgo.
"Quiero mockear OpenAI/Anthropic en un verify test" | Don't. `verify` exists precisely to call real LLMs. Use `regression` if you need mocks.

---

## Hard invariants (the "do not negotiate" list)

These are enforced by skill, code review, and the auditor. Violations get reverted.

1. **NATIVE WSL only.** `make e2e`, `make e2e-smoke`, `docker compose --profile e2e` are forbidden locally — they crash WSL2. CI uses Docker, that is fine.
2. **`setupClerkTestingToken({ page })` is called in every per-test fixture (`auth.fixture.ts`).** Without it, Cloudflare Turnstile blocks the request mid-test even if storageState is valid.
3. **`storageState` lives in `playwright/.clerk/user.json`, gitignored, regenerated by `setup` project.** Never commit, never edit by hand.
4. **`fullyParallel: true`** at the config root, with `setup` describe pinned to `mode: 'serial'`. Workers default 4 local / 2 CI.
5. **Locator priority:** `getByRole` > `getByLabel` > `getByText` > `getByTestId` >>> NEVER CSS/XPath.
6. **Web-first assertions only.** `await expect(locator).toBeVisible()` — never `expect(await locator.isVisible()).toBe(true)`.
7. **All assertions on user-visible Spanish neutro text.** `getByRole('button', { name: /configura/i })` not `/configurá/`. See `.claude/rules/spanish-text.md`.
8. **Multi-tenant header** is auto-injected by `auth.fixture.ts` via `addInitScript` → `localStorage.x-tenant-id`. Never hardcode tenant IDs in tests.
9. **`E2E_BASE_URL` is the canonical entry point.** If unset, Playwright spawns `next dev` — slow and flaky in WSL2. Always export it locally.
10. **No `test.skip` permanente.** If a test is skipped > 1 sprint, delete it (recoverable from git history) or fix it. We removed 3 perma-skips on 2026-05-04 — do not reintroduce.
11. **Preflight before every CI-grade run.** `scripts/e2e-preflight.sh` is the gate. Auto-wipes stale `user.json` (>4h).
12. **No new `make e2e*` targets.** If you find yourself wanting one, you are about to crash someone's laptop. Use `npm run test:e2e:*` instead.

---

## Files this skill owns (modify these freely; flag PR for review)

```
frontend/playwright.config.ts
frontend/e2e/setup/clerk.setup.ts
frontend/e2e/fixtures/*.ts
frontend/e2e/pages/*.ts
frontend/e2e/specs/{smoke,regression,public,visual,verify,perf}/**/*.spec.ts
frontend/package.json (only the test:e2e:* scripts block)
scripts/e2e-preflight.sh
.github/workflows/e2e-tests.yml
.claude/rules/e2e-testing.md (it points HERE; keep the pointer)
```

Files this skill **must not** modify:
- `frontend/src/**` to "fix" a flaky test → fix the test, not the production code
- `clerkMiddleware` config in `frontend/src/middleware.ts` without explicit Chris approval (auth blast radius is huge)
- `.env` / `.env.e2e` → use `.env.e2e.example` as template for documentation; the real `.env` is hand-managed by Chris

---

## Bootstrap checklist for a new contributor / a new agent / a new model

If you are seeing this skill for the first time:

1. Skim `references/architecture.md` (~10 min). Internalize: setup → smoke → regression → verify dependency graph.
2. Run `bash scripts/e2e-preflight.sh && npm run test:e2e:smoke`. If green, the substrate is healthy.
3. Read `references/clerk-auth-deep-dive.md` end-to-end. 90% of failures live there.
4. Open `frontend/e2e/specs/smoke/navigation.smoke.spec.ts` and `frontend/e2e/pages/navigation.page.ts` side by side — they are the gold-standard pair.
5. The next time you write a test, follow `references/adding-smoke-test.md` literally for the first 5 tests.
6. Subscribe to `.github/workflows/e2e-tests.yml` notifications — when smoke fails on `development`, page yourself.

---

## Versions pinned (last verified 2026-05-04)

| Package | Version | Notes |
|---|---|---|
| `@playwright/test` | `^1.59.1` | Web-first assertions, `getByRole` API |
| `@clerk/testing` | `^2.0.8` | `clerkSetup()` + `setupClerkTestingToken()` |
| `@clerk/nextjs` | `^6.36.8` | Powers FE; testing must match major |
| Node | 20.x (FE container) | Matches Vercel target |

When bumping `@playwright/test` major or `@clerk/testing` major: re-run the FULL bootstrap checklist above; do not rely on backward compat assumptions in `clerk-auth-deep-dive.md`.

---

## Pre-PR checklist (paste into PR description)

```
- [ ] `bash scripts/e2e-preflight.sh` passed
- [ ] `npm run test:e2e:smoke` green locally
- [ ] If new route: at least one `*.smoke.spec.ts` covers it
- [ ] If new auth-touching code: `npm run test:e2e:auth` regenerates storageState successfully
- [ ] No `test.skip(` introduced
- [ ] No CSS/XPath locators introduced (`getByRole` etc.)
- [ ] All asserted text is Spanish neutro (no voseo)
- [ ] No `make e2e*` invocation in any script or doc
```
