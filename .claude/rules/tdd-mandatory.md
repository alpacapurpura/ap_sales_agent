# TDD Obligatorio

**Regla no negociable:** Tests PRIMERO, implementación DESPUÉS. Sin excepciones.

## Cuándo aplica

- Feature nuevo → tests por capa antes de implementar
- Modificación de feature existente → actualizar/crear tests antes de modificar
- Bug fix → test de regresión que reproduce el bug ANTES del fix
- Refactor → tests pasan antes y después

## Cuándo NO aplica

- Configuración pura (Docker, CI, env vars)
- Documentación
- Styling sin lógica

## Flujo RED → GREEN → REFACTOR

### Backend (pytest, por capa DDD)

1. `test_domain_models.py` → Escribir test (RED) → implementar domain/
2. `test_{name}_repository.py` → Escribir test (RED) → implementar infrastructure/
3. `test_{name}_service.py` → Escribir test (RED) → implementar application/
4. API: cubierta por arch fitness + E2E

### Frontend (Vitest)

1. `hook-name.test.ts` → Escribir test (RED) → implementar hook
2. `component-name.test.tsx` → Escribir test (RED) → implementar componente
3. Stores: `store-name.test.ts` si aplica

### E2E (Playwright)

- Ruta nueva → smoke test en `e2e/specs/smoke/` ANTES de implementar la página
- Flujo crítico modificado → regression test en `e2e/specs/regression/`

## Feature existente sin tests

1. Escribir tests del comportamiento ACTUAL (baseline)
2. Escribir test del cambio esperado (RED)
3. Implementar el cambio (GREEN)

## Prohibido

- Implementar código sin test correspondiente
- Commitear sin que los tests pasen
- `skip`/`xfail` para "pasar" CI
- Reducir coverage con código nuevo sin tests
