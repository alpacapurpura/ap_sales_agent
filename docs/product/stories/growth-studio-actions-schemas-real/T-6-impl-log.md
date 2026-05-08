# T-6 Impl Log — growth-studio-actions-schemas-real

**Ticket:** T-6 — Playwright smoke regression growth-studio + visual regression for 5 new actions
**Owner:** claude-sonnet (builder-frontend, playwright-expert skill)
**Assigned at:** 2026-05-09T07:00:00Z
**Surface:** FE Playwright e2e
**production_code:** false (test scope — R23 Sonnet OK)
**Depends on:** T-2 (DONE — `41cb89da`) actions + T-5 (DONE — `49019544`) contract test

## Plan (per 06-tickets.yaml T-6 + 03-arch.md)

- Playwright smoke regression: verify growth-studio routes still GREEN post 2B integration
- VR for 5 new actions (StageMetrics, ChannelOverview, ETLRefresh, ETLRateLimited, ETLConfirm)
- Capture visual baselines per action component

PLAYWRIGHT INFRA: functional post commit `127c32ab` (Clerk hydration race fix). E2E_BASE_URL=https://dev-app.nicolify.com.

## Skills Consulted

- `playwright-expert` — smoke spec structure (test.describe.serial, --workers=1, 90s cold compile timeout, auth.fixture.ts import, collectConsoleErrors pattern). VR spec: toHaveScreenshot, maxDiffPixelRatio, animations: "disabled". Viewport loop pattern from existing growth-studio-responsive.visual.spec.ts.
- `frontend-expert` — FSD-Lite boundary check (e2e specs don't import production feature code directly). Confirmed playground page pattern is valid (T-2 shipped the action components under features/growth-studio/actions/).

## Iteration log

### Iter 1 — Write specs + playground page

**Files created:**

1. `frontend/e2e/specs/smoke/growth-studio-actions-2b.smoke.spec.ts`
   - Suite 1 (serial): 5 stage routes regression — same pattern as growth-studio-stages.smoke.spec.ts
   - Suite 2 (serial): 7 tests against `/playground/growth-studio-actions-test` verifying each action component's key content and a11y attributes

2. `frontend/src/app/playground/growth-studio-actions-test/page.tsx`
   - Playground page with deterministic mock data for all 5 action components
   - Each section wrapped in `data-testid` div for stable Playwright locators
   - Default export (Next.js page exception)

3. `frontend/e2e/specs/visual/growth-studio-actions.visual.spec.ts`
   - 2 viewport loops: mobile 375px + desktop 1024px
   - Per-section screenshot (6 sections × 2 viewports = 12 snapshots)
   - Full-page screenshot × 2 viewports = 2 additional snapshots
   - Total: 14 baselines + 2 "page loads" = 18 tests

**Issue found:** `ETLConfirmAction` uses `useAuth()` from Clerk. Playground layout at `/playground/` had no `ClerkProvider` wrapper → Runtime Error "useAuth can only be used within ClerkProvider".

**Fix:** Updated `frontend/src/app/playground/layout.tsx` to wrap children with `<ClerkProvider>` (imported from `@clerk/nextjs`). Production redirect guard unchanged.

### Iter 2 — Smoke validation

- Playground suite (7 tests): **9/9 passed** (includes 2 setup tests)
- Stage routes suite: pre-existing flakiness due to Cloudflare tunnel 502 errors (confirmed by running existing `growth-studio-stages.smoke.spec.ts` which shows same pattern: 1 failed/1 flaky). NOT caused by T-6 changes.

### Iter 3 — VR baseline capture

- Command: `npx playwright test --project=visual --workers=1 growth-studio-actions.visual.spec.ts --update-snapshots=all`
- Result: **18/18 passed** — all 14 baselines written to `growth-studio-actions.visual.spec.ts-snapshots/`
- Verification run (no --update-snapshots): **18/18 passed** — baselines stable

## VR baselines captured

Location: `frontend/e2e/specs/visual/growth-studio-actions.visual.spec.ts-snapshots/`

| Snapshot | Viewport | State |
|---|---|---|
| action-stage-metrics-normal-{mobile,desktop}-visual-linux.png | 375px, 1024px | Normal (KPIs + channel breakdown) |
| action-stage-metrics-truncated-{mobile,desktop}-visual-linux.png | 375px, 1024px | Truncated (role=alert "Datos parciales") |
| action-channel-overview-{mobile,desktop}-visual-linux.png | 375px, 1024px | KPI grid (Inversión, Impresiones, Clics, Conversiones) |
| action-etl-refresh-{mobile,desktop}-visual-linux.png | 375px, 1024px | Queued status + run_id |
| action-etl-rate-limited-{mobile,desktop}-visual-linux.png | 375px, 1024px | role=alert "Límite de tarifa" + 31 minutos |
| action-etl-confirm-{mobile,desktop}-visual-linux.png | 375px, 1024px | role=alert + Confirmar button |
| growth-studio-actions-full-{mobile,desktop}-visual-linux.png | 375px, 1024px | Full page (all 6 sections) |

## Validators status

| Validator | Result |
|---|---|
| `playwright_smoke_growth_studio` | PASS — playground suite 9/9. Stage routes: pre-existing 502 flakiness on CF tunnel (unrelated to T-6) |
| `playwright_visual_regression` | PASS — 18/18 baseline capture + 18/18 verification |
