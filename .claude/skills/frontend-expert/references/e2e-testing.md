---
globs: "frontend/e2e/**/*.{ts,tsx}"
description: E2E Playwright testing protocol — preflight, execution, structure
---

# E2E Testing

## Cuándo escribir
- Nueva UI feature (page/form/widget)
- Bug fix user interaction
- Nav/auth flow changes

## Cuándo NO
- Backend-only (usar pytest)
- Styling-only (visual regression)
- Utils (Vitest)

## Preflight — OBLIGATORIO antes CADA ejecución

```bash
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
```

Checks (3s):
1. Docker containers up, frontend 200
2. No "Module not found" en logs (top cause FE 500s)
3. Clerk auth state exists, not expired
4. E2E env vars en .env

Fail → no correr Playwright. Seguir fix instructions.

**FE returns 500:**
```bash
docker logs visionarias_client_dev 2>&1 | grep "Module not found"
docker exec visionarias_client_dev npm install <módulo>
docker compose restart client_dashboard_dev
sleep 25 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

**Always `E2E_BASE_URL`** → Playwright no spawns own webServer:
```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

## Execution — Native WSL

**NEVER Docker E2E local** (`make e2e*` crashea laptop). Always native from `frontend/`.

```bash
# Smoke (~2min)
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke

# Regression
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=regression

# Specific
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke --grep "name"

# Setup only (verify Clerk)
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=setup
```

**Reqs:**
- Dev containers up: `docker compose up -d`
- `.env` root con `E2E_CLERK_USER_EMAIL`, `E2E_CLERK_USER_PASSWORD`, `E2E_TENANT_ID`
- `playwright.config.ts` loads `.env` via `dotenv`
- Si `test-results/` has root perms: `docker run --rm -v $PWD/frontend:/f alpine sh -c 'rm -rf /f/test-results/'`

## Clerk Auth Setup

- `@clerk/testing/playwright` (official)
- Setup: `clerkSetup()` + `setupClerkTestingToken({ page })` — **both required**
- `setupClerkTestingToken` bypasses CF bot detection en Clerk FAPI
- Sign-in "Password incorrect" → sync Clerk Dashboard con `E2E_CLERK_USER_PASSWORD`
- Session en `playwright/.clerk/user.json` — auto-regen en `--project=setup`

## Structure
- Tests: `frontend/e2e/specs/` (smoke/, regression/, public/, visual/, perf/)
- POMs: `frontend/e2e/pages/`
- Fixtures: `frontend/e2e/fixtures/`
- Auth: `frontend/e2e/fixtures/auth.fixture.ts`
- Clerk setup: `frontend/e2e/setup/clerk.setup.ts`
- Tag smoke: `test.describe('feature @smoke', ...)`

## POMs
- One per page
- Locators: `getByRole`, `getByText`, `getByLabel`. Never CSS.
- Use `.first()` en ambiguous locators
- Actions: `clickSave()`, `fillField()` | Assertions: `expectLoaded()`, `expectError()`

## Multi-tenant
- Import `test` from `e2e/fixtures/auth.fixture.ts`
- Never hardcode tenant IDs
- Verify X-Tenant-ID en requests

## E2E en workflows

| Flow | E2E? | Cómo |
|---|---|---|
| Simulación pase prod | SÍ | `npx playwright test --project=smoke` native |
| Pase prod real | NO | Solo quality-gates |
| Feature UI nueva | SÍ | Smoke antes commit |
| Pre-PR | SÍ | Smoke local |

## Pre-PR
1. Smoke pass: `cd frontend && npx playwright test --project=smoke`
2. Nueva page → al menos 1 smoke
3. Flow crítico modificado (auth/checkout/onboarding) → regression

## Smoke vs Regression
- **Smoke (`@smoke`):** Verifies critical routes load. ~2min. Every PR.
- **Regression:** Full e2e flows (multi-step forms, CRUD). Slower. Pre-release.
- Rule: every public page + critical flow → al menos 1 smoke

## Mocks Growth Studio
- Base: `growth-studio.fixture.ts` — summary, detail, overview (empty), timeseries, catalog, connections healthy
- Channels: cada uno own setup (ig-organic-setup.ts, etc.) adding overview con `channel_list` + dashboard
- **Overview endpoint (`/metrics/{stage}/overview`) REQUIRED** — sin él, channel cards no renderizan

## PROHIBIDO
```
make e2e          # Docker, crashea
make e2e-smoke    # Docker, crashea
docker compose --profile e2e run ...
```
