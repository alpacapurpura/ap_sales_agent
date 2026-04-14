# E2E Testing Rules

## When to write E2E tests
- Feature nueva con UI (page, form, widget)
- Bug fix que afecta interacción de usuario
- Cambios en navegación o flujo de auth

## When NOT to write E2E tests
- Cambios solo backend (usar pytest)
- Solo styling (usar visual regression)
- Funciones utilitarias (usar Vitest)

## Preflight Check — OBLIGATORIO antes de CADA ejecución de Playwright

**SIEMPRE correr el preflight ANTES de cualquier `npx playwright test`:**

```bash
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
```

El preflight verifica (en 3 segundos):
1. Docker containers corriendo y frontend respondiendo 200
2. No hay "Module not found" en logs (causa #1 de 500 en frontend)
3. Clerk auth state existe y no está expirado
4. Variables de entorno E2E presentes en .env

**Si el preflight falla, NO correr Playwright.** Seguir las instrucciones de fix que muestra.

**Si frontend responde 500:**
```bash
# Ver qué módulo falta
docker logs visionarias_client_dev 2>&1 | grep "Module not found"
# Instalar DENTRO del container (no local — Docker tiene su propio node_modules)
docker exec visionarias_client_dev npm install <módulo-faltante>
docker compose restart client_dashboard_dev
# Esperar 20-30s y verificar
sleep 25 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

**SIEMPRE usar `E2E_BASE_URL` para evitar que Playwright intente arrancar su propio webServer:**
```bash
E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

## Execution — Native Playwright in WSL

**NUNCA usar Docker para E2E localmente** (`make e2e`, `make e2e-smoke` crashean la laptop).
**SIEMPRE ejecutar `npx playwright test` nativamente desde `frontend/`.**

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

**Requisitos para que funcione:**
- Dev containers corriendo: `docker compose up -d`
- `.env` en la raíz del repo con `E2E_CLERK_USER_EMAIL`, `E2E_CLERK_USER_PASSWORD`, `E2E_TENANT_ID`
- `playwright.config.ts` carga `.env` automáticamente via `dotenv` — no hace falta exportar variables manualmente
- Si `test-results/` tiene permisos root (de un Docker run viejo): `docker run --rm -v $PWD/frontend:/f alpine sh -c 'rm -rf /f/test-results/'`

## Clerk Auth Setup

- Usa `@clerk/testing/playwright` (paquete oficial)
- Setup: `clerkSetup()` + `setupClerkTestingToken({ page })` — **AMBOS son requeridos**
- `setupClerkTestingToken` bypasea bot detection de Cloudflare en Clerk FAPI
- Si sign-in falla con "Password is incorrect": sincronizar password en Clerk Dashboard con el valor de `E2E_CLERK_USER_PASSWORD` en `.env`
- Session persistida en `playwright/.clerk/user.json` — se regenera automáticamente al correr `--project=setup`

## Structure
- Tests: `frontend/e2e/specs/` (smoke/, regression/, public/, visual/, perf/)
- POMs: `frontend/e2e/pages/`
- Fixtures: `frontend/e2e/fixtures/`
- Auth: `frontend/e2e/fixtures/auth.fixture.ts`
- Clerk setup: `frontend/e2e/setup/clerk.setup.ts`
- Tag smoke: `test.describe('feature @smoke', ...)`

## Page Objects
- Un POM por página de usuario
- Locators: `getByRole`, `getByText`, `getByLabel` — NUNCA selectores CSS
- **Usar `.first()` en locators ambiguos** para evitar strict mode violations
- Acciones: `clickSave()`, `fillField()` | Assertions: `expectLoaded()`, `expectError()`

## Multi-tenant
- Siempre importar `test` desde `e2e/fixtures/auth.fixture.ts`
- Nunca hardcodear tenant IDs
- Verificar X-Tenant-ID en requests interceptados

## E2E en flujos de trabajo

| Flujo | E2E? | Cómo |
|---|---|---|
| Simulación de pase a producción | SÍ | `cd frontend && npx playwright test --project=smoke` (native) |
| Pase a producción real | NO | Solo quality-gates (lint+tests), NO E2E |
| Feature con UI nueva | SÍ | Smoke test antes de commitear |
| Pre-PR | SÍ | Smoke test local |

## Pre-PR checklist
Antes de crear un PR con UI changes:
1. Smoke tests deben pasar: `cd frontend && npx playwright test --project=smoke`
2. Si agregaste una página nueva, debe tener al menos un smoke test
3. Si modificaste un flujo crítico (auth, checkout, onboarding), agregar regression test

## Smoke vs Regression
- **Smoke (`@smoke`):** Verifica que las rutas críticas cargan y responden. ~2 min native. Corre en cada PR.
- **Regression:** Verifica flujos completos end-to-end (multi-step forms, CRUD cycles). Más lento. Corre antes de releases.
- Regla: cada página pública y cada flujo crítico debe tener al menos un smoke test

## Mocks para Growth Studio
- Base: `growth-studio.fixture.ts` — mockea summary, detail, overview (vacío), timeseries, catalog, connections (healthy)
- Canales: cada canal tiene su propio setup (ig-organic-setup.ts, etc.) que agrega overview con `channel_list` y dashboard
- **El overview endpoint (`/metrics/{stage}/overview`) es OBLIGATORIO** — sin él, los channel cards no renderizan

## PROHIBIDO
```
make e2e          # Docker, crashea la laptop
make e2e-smoke    # Docker, crashea la laptop
docker compose --profile e2e run ...  # Mismo problema
```
