---
globs: "frontend/e2e/**/*.{ts,tsx}"
description: E2E Playwright testing protocol — preflight, execution, structure
---

# E2E Testing Rules

## When to write E2E tests
- New UI feature (page, form, widget)
- Bug fix affecting user interaction
- Nav or auth flow changes

## When NOT to write E2E tests
- Backend-only changes (use pytest)
- Styling-only (use visual regression)
- Utility functions (use Vitest)

## Preflight Check — OBLIGATORIO antes de CADA ejecución de Playwright

**Run preflight BEFORE any `npx playwright test`:**

```bash
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
```

Preflight checks (3 seconds):
1. Docker containers running, frontend returns 200
2. No "Module not found" in logs (top cause of frontend 500s)
3. Clerk auth state exists and not expired
4. E2E env vars present in .env

**Preflight fails → don't run Playwright.** Follow fix instructions shown.

**Frontend returns 500:**
```bash
# Ver qué módulo falta
docker logs visionarias_client_dev 2>&1 | grep "Module not found"
# Instalar DENTRO del container (no local — Docker tiene su propio node_modules)
docker exec visionarias_client_dev npm install <módulo-faltante>
docker compose restart client_dashboard_dev
# Esperar 20-30s y verificar
sleep 25 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

**Always use `E2E_BASE_URL` so Playwright doesn't try to spin own webServer:**
```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

## Execution — Native Playwright in WSL

**NEVER use Docker for E2E locally** (`make e2e`, `make e2e-smoke` crash the laptop).
**Always run `npx playwright test` natively from `frontend/`.**

```bash
# Smoke tests (rápido, ~2 min)
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke

# Regression suite (más lento)
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=regression

# Test específico
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke --grep "test-name"

# Solo setup (verificar que Clerk autentica)
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=setup
```

**Requirements:**
- Dev containers running: `docker compose up -d`
- `.env` at repo root with `E2E_CLERK_USER_EMAIL`, `E2E_CLERK_USER_PASSWORD`, `E2E_TENANT_ID`
- `playwright.config.ts` loads `.env` via `dotenv` — no manual export needed
- If `test-results/` has root permissions (old Docker run): `docker run --rm -v $PWD/frontend:/f alpine sh -c 'rm -rf /f/test-results/'`

## Clerk Auth Setup

- Uses `@clerk/testing/playwright` (official package)
- Setup: `clerkSetup()` + `setupClerkTestingToken({ page })` — **both required**
- `setupClerkTestingToken` bypasses Cloudflare bot detection on Clerk FAPI
- Sign-in fails "Password is incorrect": sync password in Clerk Dashboard with `E2E_CLERK_USER_PASSWORD` in `.env`
- Session persisted in `playwright/.clerk/user.json` — auto-regenerates on `--project=setup`

## Structure
- Tests: `frontend/e2e/specs/` (smoke/, regression/, public/, visual/, perf/)
- POMs: `frontend/e2e/pages/`
- Fixtures: `frontend/e2e/fixtures/`
- Auth: `frontend/e2e/fixtures/auth.fixture.ts`
- Clerk setup: `frontend/e2e/setup/clerk.setup.ts`
- Tag smoke: `test.describe('feature @smoke', ...)`

## Page Objects
- One POM per user page
- Locators: `getByRole`, `getByText`, `getByLabel` — never CSS selectors
- **Use `.first()` on ambiguous locators** to avoid strict mode violations
- Actions: `clickSave()`, `fillField()` | Assertions: `expectLoaded()`, `expectError()`

## Multi-tenant
- Always import `test` from `e2e/fixtures/auth.fixture.ts`
- Never hardcode tenant IDs
- Verify X-Tenant-ID in intercepted requests

## E2E en flujos de trabajo

| Flujo | E2E? | Cómo |
|---|---|---|
| Simulación de pase a producción | SÍ | `cd frontend && npx playwright test --project=smoke` (native) |
| Pase a producción real | NO | Solo quality-gates (lint+tests), NO E2E |
| Feature con UI nueva | SÍ | Smoke test antes de commitear |
| Pre-PR | SÍ | Smoke test local |

## Pre-PR checklist
Before creating PR with UI changes:
1. Smoke tests must pass: `cd frontend && npx playwright test --project=smoke`
2. New page → must have at least one smoke test
3. Modified critical flow (auth, checkout, onboarding) → add regression test

## Smoke vs Regression
- **Smoke (`@smoke`):** Verifies critical routes load and respond. ~2 min native. Runs each PR.
- **Regression:** Verifies full end-to-end flows (multi-step forms, CRUD cycles). Slower. Runs before releases.
- Rule: every public page and critical flow needs at least one smoke test

## Mocks para Growth Studio
- Base: `growth-studio.fixture.ts` — mocks summary, detail, overview (empty), timeseries, catalog, connections (healthy)
- Channels: each channel has own setup (ig-organic-setup.ts, etc.) adding overview with `channel_list` and dashboard
- **Overview endpoint (`/metrics/{stage}/overview`) is REQUIRED** — without it, channel cards don't render

## PROHIBIDO
```
make e2e          # Docker, crashea la laptop
make e2e-smoke    # Docker, crashea la laptop
docker compose --profile e2e run ...  # Mismo problema
```