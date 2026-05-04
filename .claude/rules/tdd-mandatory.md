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

## Default flag flips (origen PI-11 2026-05-04)

Cuando flipeás default de feature flag side-effect (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, etc.) → TDD NO basta. **OBLIGATORIO** workflow extra:

1. Tests pre-flip: grep tests mockean path viejo, listar
2. Tests RED migración: adaptar tests AL PATH NUEVO antes flip
3. Run suite con AMBOS valores flag (RED en path viejo confirma migración necesaria; GREEN en path nuevo confirma migración correcta)
4. Tests GREEN flip: mergeable cuando ambos paths verde
5. Documentar en commit body: "Flag X flipped Y→Z. Tests audited: N migrated, M bypass."

Sin estos pasos: tests siguen probando path muerto. Producción rompe silenciosa (path nuevo nunca probado real).

Caso origen: commit `64738354` flipeó `USE_OUTBOX_PATTERN_*=False→True` sin audit → 25 BE failures + polluter snapshot test no identificable + 80min hunt agente.

Ver `.claude/rules/anti-default-flip-audit.md` (rule cardinal + 6 flags inventario + 7 enforcement layers).
