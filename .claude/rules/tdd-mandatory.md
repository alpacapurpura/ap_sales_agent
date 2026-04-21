# TDD Obligatorio

Tests PRIMERO, implementación DESPUÉS. Sin excepciones.

## Aplica
- Feature nuevo → tests por capa antes
- Modificación feature existente → actualizar/crear tests antes
- Bug fix → test regresión reproduciendo bug ANTES fix
- Refactor → tests pasan antes y después

## NO aplica
- Config pura (Docker, CI, env)
- Docs
- Styling sin lógica

## RED → GREEN → REFACTOR

### Backend (pytest, DDD)
1. `test_domain_models.py` → RED → implement domain/
2. `test_{name}_repository.py` → RED → implement infrastructure/
3. `test_{name}_service.py` → RED → implement application/
4. API: arch fitness + E2E

### Frontend (Vitest)
1. `hook-name.test.ts` → RED → implement hook
2. `component-name.test.tsx` → RED → implement component
3. Stores: `store-name.test.ts` si aplica

### E2E (Playwright)
- Ruta nueva → smoke en `e2e/specs/smoke/` ANTES página
- Flow crítico modificado → regression en `e2e/specs/regression/`

## Feature existente sin tests
1. Escribir tests comportamiento ACTUAL (baseline)
2. Escribir test cambio esperado (RED)
3. Implement cambio (GREEN)

## Prohibido
- Código sin test correspondiente
- Commit sin tests passing
- `skip`/`xfail` para "pasar" CI
- Reducir coverage con código nuevo sin tests
