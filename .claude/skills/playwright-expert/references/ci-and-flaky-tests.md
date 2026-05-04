# CI + Flaky Test Debugging

> **Read when:** test passes locally but fails in CI, you need to shard the suite, you are debugging a `retries: 2` exhaustion, or you are about to change `.github/workflows/e2e-tests.yml`.

CI and flakes share an underlying skill: reading traces, isolating non-determinism, and choosing the right escalation (fix substrate vs fix test vs fix product). This document teaches both.

---

## 1. The CI workflow at a glance

File: `.github/workflows/e2e-tests.yml`

```
push to development (paths: frontend/**) ─────┐
PR to development|main (paths: frontend/**) ──┤
workflow_dispatch (manual w/ suite selector) ─┘
                                              ▼
                              ┌─────────────────────────┐
                              │   e2e job (ubuntu)      │
                              │   timeout: 20 min       │
                              └─────────────────────────┘
                                              │
                  ┌───────────────────────────┼───────────────────────────┐
                  │                           │                           │
                  ▼                           ▼                           ▼
         Free disk + setup        Materialize .env from         docker compose up
         buildx (~25 GB)          GH Secrets + curl            postgres/redis/qdrant
                                  CLERK_TESTING_TOKEN          /api_dev/client_dashboard_dev
                                              │
                                              ▼
                                  alembic upgrade head
                                              │
                                              ▼
                                  seed E2E tenant (psql)
                                              │
                                              ▼
                                  npx playwright test --project=<smoke|regression|""> 
                                              │
                                              ▼
                                  upload playwright-report + test-results (7d)
```

Default suite for auto-runs: `smoke`. Manual dispatch lets you pick `smoke | regression | full`.

### What CI does that local doesn't
- **Generates a fresh `CLERK_TESTING_TOKEN`** by curling Clerk's API. Local relies on `clerkSetup()` which reads the token from env if pre-set, OR fetches one if missing. Both paths converge on a valid token.
- **Builds the FE container** from scratch every run. Local uses the long-running dev container.
- **Disk-cleans first** — runner has ~14 GB free initially; we add 25 GB by removing Android SDK / dotnet / Docker images.
- **No interactive `--headed` or `--debug`** — always headless, always isolated.

### What CI does NOT do
- Persist `playwright/.clerk/user.json` between runs (each run regenerates)
- Run a parallel session of dev container (the runner's container IS the test target)
- Allow secret rotation without a redeploy of GH Secrets

---

## 2. The CI failure decision tree

```
test fails in CI
  │
  ├─ does it pass locally?
  │   ├─ YES → environment differential. See "CI-only failures" below
  │   └─ NO  → reproduce locally, fix locally, re-push
  │
  └─ does it fail consistently in CI (3 reruns)?
      ├─ YES → real bug or substrate issue
      └─ NO  → flake. See "Flaky test debugging" below
```

**Never** "rerun until green." That hides real flakes that will bite production.

---

## 3. CI-only failures (passes local, fails CI)

| Symptom | Likely cause | Fix |
|---|---|---|
| `Module not found` in CI logs | Runner missed an `npm install` step OR `node_modules` was cached stale | Clear cache + push; check `Dockerfile.client` |
| Test timeout > 60s in CI but <5s local | CI runner is slower (1 vCPU shared) | Bump THIS test's timeout: `test('x', async ({page}) => { test.setTimeout(120_000); ... })`. Don't change global timeout |
| `Bot traffic detected` in CI only | `CLERK_TESTING_TOKEN` step failed silently — curl returned `null` | Check workflow logs step "Generate Clerk testing token". If TOKEN is empty, GH Secret `CLERK_SECRET_KEY` is wrong |
| `Tenant not found` 404 | Seed step failed | Check workflow log "Seed E2E tenant"; psql command must succeed |
| "Cookies are missing for `*.clerk.accounts.dev`" | Setup project failed silently | Check setup project log; likely `clerk.signIn()` timed out due to Clerk dev throttle |
| Different element exists locally vs CI | FE built differently — stale Docker layer cache | `docker compose build --no-cache client_dashboard_dev` (in workflow); rerun |
| Test passes 9/10 in CI but always fails the 10th | Genuine flake — see next section |

---

## 4. Flaky test debugging — the methodology

A flake is a test that does not produce the same result on the same code 100% of the time. Causes:

| Cause | How to detect | How to fix |
|---|---|---|
| Race condition | Same test fails when run with other tests but passes alone | Mock the dependency that's racing; or use `await expect(...)` for the post-condition |
| Clock-dependent | Fails when crossing a date boundary or timezone | Mock `Date.now()` via `page.addInitScript`; or use `await page.clock.install()` (Playwright 1.45+) |
| Auth state expires mid-run | Fails after 30+ minutes of running suite | Shard so each shard is < 30min; or refresh storageState mid-suite |
| Network jitter to backend/Clerk | Sporadic timeouts unrelated to logic | `retries: 2` (already config); bump per-test timeout; check substrate |
| Element appears + disappears (toast) | Assert before toast vanishes vs after | Use `await expect(toast).toBeVisible()` THEN `await expect(toast).toBeHidden()` |
| Order-dependent | Test A passes alone, fails after test B | Tests share state — find the leak (cookies, localStorage, mock state) |

### Step-by-step: debug a flake

```
1. Identify the flaky test from CI run (it has "retried" markers in HTML report)
2. Reproduce locally with --repeat-each:
   cd frontend && npx playwright test path/to/test.spec.ts --project=smoke --repeat-each=10
3. If 10/10 pass → environment-specific; check CI logs more carefully (rate limit?)
4. If 1-9/10 pass → real flake, hunt the cause:
   a. Run with --headed --slow-mo=500: watch the browser
   b. Run with --trace=on then open trace viewer: see network + DOM at every step
5. Apply fix. Re-run --repeat-each=10. Must pass 10/10 before merging.
```

### Anti-patterns (do not do these to "fix" a flake)

- ❌ `await page.waitForTimeout(2000)` — moves the symptom, not the cause
- ❌ `test.setTimeout(300_000)` — gives the flake more rope
- ❌ `retries: 5` (per project) — masks instead of fixing
- ❌ `test.fixme(...)` permanently — that's just `test.skip` with a different name
- ❌ Adding `try/catch` around the failing assertion — silences the signal

### Acceptable mitigations (when you genuinely cannot fix the substrate)
- Per-test `test.setTimeout(N)` documented with a comment explaining WHY
- Per-test retry: `test('x', { retries: 3 }, async ...)` — only with comment
- Tag flaky tests with `test.fail()` when investigating — temporary, with TODO and date

---

## 5. Trace viewer — the only debug tool you need

After any failure, the trace contains: every action, every network request, before/after DOM screenshots, console logs, and source mapping. Open it:

```bash
# After a local failure
cd frontend && npx playwright show-report --host 0.0.0.0
# Click failing test → "Trace" tab

# After a CI failure
gh run download <run-id> --name playwright-report-smoke
cd /tmp && npx playwright show-report ./playwright-report
```

What to look at, in order:
1. **Action list (left panel)** — last action before failure is usually the smoking gun
2. **Snapshot (top-right)** — DOM at action time; compare "before" vs "after" of the failing step
3. **Source (bottom)** — your test code with the failing line highlighted
4. **Network tab** — did the API request you expected fire? Did it return what you expected?
5. **Console tab** — JS errors? React warnings? Hydration mismatches?

90% of debugs end at step 1 or 2. The action list shows you the locator that timed out, and the snapshot shows you the actual DOM at that moment — usually you can see immediately why the locator didn't match.

---

## 6. Sharding — when the suite gets too big

When the smoke suite exceeds ~10 minutes total CI time, shard:

```yaml
# .github/workflows/e2e-tests.yml (when needed; not currently configured)
strategy:
  matrix:
    shard: [1/3, 2/3, 3/3]
steps:
  # ...
  - name: Run Playwright tests
    run: npx playwright test --project=smoke --shard=${{ matrix.shard }}
```

Each shard runs a deterministic subset; merge HTML reports with `npx playwright merge-reports`.

**When to shard:**
- Smoke > 10 min total
- Regression > 30 min total
- You want different OS/browser combos in parallel

**When NOT to shard:**
- Suite is fast (< 5 min) — sharding overhead exceeds savings
- Tests have inter-suite dependencies — sharding will fail unpredictably (we have none, but watch for this)

---

## 7. CI cost vs reliability trade-offs

| Setting | Local | CI |
|---|---|---|
| `workers` | 4 | 2 (less RAM available) |
| `retries` | 0 (or 1 with E2E_BASE_URL) | 2 |
| `trace` | on-first-retry | on-first-retry |
| `video` | on-first-retry | on-first-retry |
| `screenshot` | only-on-failure | only-on-failure |
| `timeout` per test | 60s (600s for verify) | same |

**Why CI gets 2 retries and local gets 0-1:**
- Local: failures are usually real; retries hide your own bugs
- CI: occasional infrastructure jitter (Clerk throttle, runner slowness) deserves a free pass before paging humans

If a test ever uses 2 retries in CI, the failing trace IS NOT discarded — `retain-on-failure` keeps the first failed run's trace too.

---

## 8. Disk and memory budgets

Runner has 14 GB initial free; we boost to ~40 GB via cleanup step.

| Consumer | Approx | Notes |
|---|---|---|
| Docker images (postgres, qdrant, redis, api_dev, client_dashboard_dev) | 8 GB | builds from scratch each run |
| `node_modules` (frontend) | 1.5 GB | |
| Playwright browsers | 1 GB | only Chromium; `--with-deps` adds OS libs |
| FE build output (`.next/standalone`) | 500 MB | |
| `playwright-report/` + `test-results/` | 100-500 MB | varies with trace size |
| Free margin | ~25 GB | safety |

If we add Firefox/WebKit, add 2 GB each.

Memory: runner has 7 GB. Chromium uses ~500 MB per worker. With 2 workers + Next.js + Postgres + Qdrant + Redis, total is ~5.5 GB. Tight but works. Pay attention if adding more workers in CI.

---

## 9. When CI fails for "infra" reasons

Symptoms: workflow runs but tests don't even start, or the runner crashes mid-run.

| Symptom | Cause | Resolution |
|---|---|---|
| "No space left on device" | Build cache + node_modules > free margin | Add to free-disk-space step; or delete artifacts more aggressively |
| Clerk API 5xx in CI logs | Clerk dev instance outage | Wait, retry. If persistent, switch to `disable-bot-protection` flag (last resort) |
| Postgres "could not connect" | Migration step ran before postgres was healthy | Check container health-check window; ensure `depends_on: postgres condition: healthy` |
| Cleanup step times out | Stuck `docker compose down` | Add `|| true` (we do); investigate next time it happens |

If CI is broken at the workflow level (not test level), do not push fixes blind — open a PR specifically for the workflow file, run via `workflow_dispatch` first.

---

## 10. Runbook — "smoke is failing on development"

```
1. gh run list --workflow=e2e-tests.yml --branch=development --limit=5
2. gh run view <run-id> --log-failed | head -200
3. gh run download <run-id> --name playwright-report-smoke
4. cd /tmp && npx playwright show-report ./playwright-report
5. Open failing test → trace → identify root cause
6. Reproduce locally:
   bash scripts/e2e-preflight.sh
   npm run test:e2e:fresh   # if auth was the failure
   cd frontend && npx playwright test path/to/file.spec.ts --project=smoke
7. Fix; commit; push; watch
8. If still flaky → see Section 4 above
```

For the on-call rotation: when smoke fails on development, it blocks deploys. Treat it as P1.

---

## 11. The "freezer" pattern for genuinely undebuggable tests

If a test is failing in production-blocking ways and you cannot fix it in time:

1. Move the spec to `frontend/e2e/specs/_freezer/<name>.frozen.spec.ts` (project filter ignores `_freezer/`).
2. Open an issue tagged `e2e-frozen` with the failing trace, hypotheses, and a deadline (max 2 weeks).
3. After 2 weeks: either fix or delete. No permanently frozen tests.

This is `test.skip` with extra friction. Use only when truly stuck.

---

## 12. Hardening over time — the maturity model

| Maturity | What you have | Next investment |
|---|---|---|
| **Level 1** | Smoke runs every PR, mostly green | Eliminate any flakes (10/10 pass on `--repeat-each=10`) |
| **Level 2** (we are here) | Smoke green > 95%, regression nightly | Add `verify` project with real LLMs, run weekly |
| **Level 3** | All projects green > 98%, sharded for speed | Visual diffs with baselines, perf budgets enforced |
| **Level 4** | Coverage instrumentation across E2E | Use E2E coverage to find untested user journeys |
| **Level 5** | Tests written FROM customer journey logs | Production-mirror test flows from real session replays |

Don't chase the next level until the current one is solid. Skipping ahead means stacking flakes on top of an unstable foundation.
