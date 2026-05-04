# PR-2 — Coverage Lift P0 Modules

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-coverage-p0-modules |
| Sprint padre | S1-test-integrity-and-coverage |
| PI padre | PI-11-backend-quality-guardrails |
| Estado | ready |
| Tipo | refactor |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — |

## Problema

`crm` (59.3%) y `scheduling` (59.9%) tienen la cobertura más baja del backend. Servicios críticos como `lead_query_service`, `nps_service`, `referral_service`, `availability_service` y `public_links` carecen casi por completo de tests. Un bug en cualquiera de estos rompe el funnel de ventas o la experiencia de agendamiento.

## Outcome esperado

- `crm` ≥75% cobertura.
- `scheduling` ≥75% cobertura.
- Tests unitarios para servicios de aplicación y repositorios sin cobertura.

## Walking skeleton

Tests unitarios + de integración liviana (mocks) para capas `application` e `infrastructure` de `crm` y `scheduling`. No toca API ni dominio (que ya tienen cobertura razonable).

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Cobertura P0 en un solo PR (crm + scheduling) | Cohesivo; mismo patrón de test (repo mock + service unit) | Scope L pero manejable para Opus/Sonnet 1M | **ELEGIDA** |
| B — Split crm y scheduling en 2 PRs | Menor blast radius | Overhead PM; patrón idéntico de tests | descartada |

## Validación técnica preliminar

- Modules afectados: `crm`, `scheduling`.
- Blockers: ninguno (PR-1 debe mergear primero para CI verde base).
- Tiempo estimado: 1 iter backend builder + audit.

## Existing systems audit

Skip. No crea nuevos subsistemas.

## Decisiones diferidas

- Si `crm` requiere tests de integración con Postgres (lead repo), usar fixtures existentes en `conftest.py`.

## Out of scope

- Cobertura `shared` (va en S2).
- Cobertura `sales_agent`/`copilot` (va en S2).
- Cambio de lógica de negocio.

## Copilot-first checklist

- [x] No aplica — infraestructura de calidad.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Implementation | `nicolify-backend` (Sonnet) | `prompts/02-builder-start.md` | code + tests + IMPL-LOG |
| Audit | `nicolify-backend-auditor` (Opus) | `prompts/03-auditor-start.md` | REVIEW.md |
| Cierre | `/pm` | `prompts/04-pm-close.md` | RESULT.md |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Tests nuevo | `tests/modules/crm/unit/test_*.py` | servicios sin cobertura |
| Tests nuevo | `tests/modules/crm/integration/test_*.py` | repos con DB mock |
| Tests nuevo | `tests/modules/scheduling/unit/test_*.py` | servicios sin cobertura |
| Tests nuevo | `tests/modules/scheduling/integration/test_*.py` | repos con DB mock |

## Aceptación

- [ ] `crm` coverage ≥75% (`pytest --cov=src/modules/crm`).
- [ ] `scheduling` coverage ≥75%.
- [ ] `IMPL-LOG.md` completo.
- [ ] `REVIEW.md` sin FAIL.
- [ ] `RESULT.md` escrito por PM.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Tests de repo requieren schema SQLite que no existe | Usar fixtures existentes de `conftest.py` (transactional DB). |
| Subir cobertura expone tests rotos latentes (dependen de estado global) | Aislar tests con fixtures factory + cleanup. |
