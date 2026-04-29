# TDD Obligatorio

Tests PRIMERO, implementación DESPUÉS. Sin excepciones.

## Aplica
Feature nuevo / modificación existente / bug fix (test regresión ANTES fix) / refactor (tests pasan antes+después).
**No aplica:** config pura (Docker/CI/env), docs, styling sin lógica.

## RED → GREEN → REFACTOR
- BE (pytest, DDD): domain → infrastructure → application → API arch+E2E. RED por capa antes implementar.
- FE (Vitest): hook → component → store. RED antes.
- E2E (Playwright): ruta nueva → smoke en `e2e/specs/smoke/` ANTES página. Flow crítico modificado → regression.
- Feature existente sin tests: baseline (comportamiento actual) → RED cambio → GREEN.

## Prohibido
Código sin test. Commit con tests rotos. `skip`/`xfail` para pasar CI. Reducir coverage con código nuevo sin tests.
