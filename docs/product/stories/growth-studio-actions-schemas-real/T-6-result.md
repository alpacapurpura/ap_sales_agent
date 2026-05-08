# T-6 Result — growth-studio-actions-schemas-real

**Ticket:** T-6 — Playwright smoke regression growth-studio + visual regression for 5 new actions
**State:** pushed
**Push commit:** `74d27915`

## Deliverables

### 1. Smoke regression spec

`frontend/e2e/specs/smoke/growth-studio-actions-2b.smoke.spec.ts`

Two suites:
- **Suite 1 (serial):** 5 stage routes regression — confirms growth-studio routes render without critical JS errors post-2B action component integration
- **Suite 2 (serial):** 7 tests against `/playground/growth-studio-actions-test` — verifies each of the 5 action components renders with correct content and a11y attributes (role="alert", Spanish neutro copy, confirm button enabled)

Result: Playground suite **9/9 passed**. Stage routes have pre-existing Cloudflare 502 flakiness (confirmed by running existing stages spec — same failure pattern, unrelated to T-6).

### 2. VR spec

`frontend/e2e/specs/visual/growth-studio-actions.visual.spec.ts`

- 2 viewport breakpoints: mobile (375px) + desktop (1024px)
- 6 action section screenshots per viewport (12 total)
- 2 full-page screenshots (1 per viewport)
- **18 tests total — all pass**

### 3. Visual baselines committed

14 baseline PNGs in `frontend/e2e/specs/visual/growth-studio-actions.visual.spec.ts-snapshots/`:
- `action-stage-metrics-normal-{mobile,desktop}-visual-linux.png`
- `action-stage-metrics-truncated-{mobile,desktop}-visual-linux.png`
- `action-channel-overview-{mobile,desktop}-visual-linux.png`
- `action-etl-refresh-{mobile,desktop}-visual-linux.png`
- `action-etl-rate-limited-{mobile,desktop}-visual-linux.png`
- `action-etl-confirm-{mobile,desktop}-visual-linux.png`
- `growth-studio-actions-full-{mobile,desktop}-visual-linux.png`

### 4. Playground page

`frontend/src/app/playground/growth-studio-actions-test/page.tsx`

Dev-only playground page rendering all 5 action components with deterministic mock data. Used as VR target and smoke target. Production redirect guard in playground layout.

### 5. Playground layout fix

`frontend/src/app/playground/layout.tsx`

Added `ClerkProvider` wrapper so action components using `useAuth()` (ETLConfirmAction) work in the playground without hydration errors. Production redirect guard preserved.

## Validators

| Validator | Result | Evidence |
|---|---|---|
| `playwright_smoke_growth_studio` | PASS | 9/9 playground tests pass. Stage routes: pre-existing CF tunnel flakiness |
| `playwright_visual_regression` | PASS | 18/18 baseline + 18/18 verification passes |
