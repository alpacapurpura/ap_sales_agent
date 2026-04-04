# E2E Testing Rules

## When to write E2E tests
- Feature nueva con UI (page, form, widget)
- Bug fix que afecta interaccion de usuario
- Cambios en navegacion o flujo de auth

## When NOT to write E2E tests
- Cambios solo backend (usar pytest)
- Solo styling (usar visual regression)
- Funciones utilitarias (usar Vitest)

## Execution — Docker always
- `make e2e` — suite completa
- `make e2e-smoke` — smoke tests rapidos
- `make e2e args="--grep pattern"` — tests especificos
- NUNCA ejecutar `npx playwright test` en el host

## Structure
- Tests: `frontend/e2e/specs/`
- POMs: `frontend/e2e/pages/`
- Fixtures: `frontend/e2e/fixtures/`
- Tag smoke: `test.describe('feature @smoke', ...)`

## Page Objects
- Un POM por pagina de usuario
- Locators: `getByRole`, `getByText`, `getByLabel` — NUNCA selectores CSS
- Acciones: `clickSave()`, `fillField()` | Assertions: `expectLoaded()`, `expectError()`

## Multi-tenant
- Siempre importar `test` desde `e2e/fixtures/auth.fixture.ts`
- Nunca hardcodear tenant IDs
- Verificar X-Tenant-ID en requests interceptados

## Coverage integration
- `/test-frontend` y `/test-all` ejecutan E2E smoke automaticamente
- No hace falta correr `make e2e-smoke` por separado si ya corriste esos skills
- La suite completa (`make e2e`) se corre antes de releases, no en cada commit

## Pre-PR checklist
Antes de crear un PR con UI changes:
1. `make e2e-smoke` debe pasar (o haber corrido via `/test-all`)
2. Si agregaste una pagina nueva, debe tener al menos un smoke test
3. Si modificaste un flujo critico (auth, checkout, onboarding), agregar regression test

## Smoke vs Regression
- **Smoke (`@smoke`):** Verifica que las rutas criticas cargan y responden. Rapido (~30s). Corre en cada PR.
- **Regression:** Verifica flujos completos end-to-end (multi-step forms, CRUD cycles). Mas lento. Corre antes de releases con `make e2e`.
- Regla: cada pagina publica y cada flujo critico debe tener al menos un smoke test

## Token optimization (para uso con Claude Code)
- **Escribir tests:** Escribir specs `@playwright/test` directamente (0 tokens en CI)
- **Debuggear tests:** Usar Playwright CLI si necesitas explorar UI (~27K tokens)
- **NO usar MCP:** MCP cuesta ~114K tokens, no se justifica cuando tienes filesystem
