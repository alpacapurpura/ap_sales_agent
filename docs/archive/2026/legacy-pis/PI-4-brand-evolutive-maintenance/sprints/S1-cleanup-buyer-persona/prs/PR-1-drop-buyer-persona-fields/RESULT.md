# RESULT — PR-1-drop-buyer-persona-fields

> **Retro-fill 2026-05-06 — original closure loop never executed under legacy paradigm.**
> Code shipped 2026-04-29 / 2026-05-01 across 4 commits. RESULT/REVIEW templates were
> never populated because PI-4 was migrated to the new paradigm (`docs/product/outcomes/`)
> on 2026-05-05 (Wave 2) before the legacy PM closure prompt ran. This file is being
> filled retroactively to make the audit trail complete prior to closing the rolling
> outcome `pi-4-brand-evolutive-maintenance` as `done`.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped (retro-confirmed 2026-05-06) |
| Fecha cierre | 2026-04-29 (BE+copilot+migration) / 2026-05-01 (FE) |
| Commits | `80551ec5`, `00fa55b0`, `d047c10b` (2026-04-29) + `e4df74b8` (2026-05-01) |
| Branch merged a | development |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Drop `buyer_persona.objections` cross-stack | BE entity + model + DTO + route + copilot + migration + FE schema + FE types | Done en 4 commits | ✅ cumplido |
| Drop `buyer_persona.preferred_channels` cross-stack | idem | Done en mismos 4 commits | ✅ cumplido |
| Preservar surfaces distintas con mismo nombre | `offer.objections` (módulo distinto) y `sales_agent.objection_history` (session-state) intactos | Verificado por test `test_offer_list_paths_objections_still_present` | ✅ cumplido |
| Migration idempotente | Raw SQL `DROP COLUMN IF EXISTS` testeado clone DB cycle | Done — `acdcfa45d526` verificado stamp 082 → upgrade head → downgrade -1 → upgrade head → upgrade head no-op | ✅ cumplido |
| Regression tests | Suite que blinde reintroducción | 21 cases BE + 3 cases FE = 24 regression tests | ✅ cumplido (overshoot positivo) |
| Anthropic prompt cache safety | Slot order del template preservado | Líneas rule-4 (objections/preferred_channels) caen sin alterar pre/post | ✅ cumplido |

Veredicto: ✅ cumplido

## Surface entregada (concreta)

### Backend (commit `80551ec5` — 2026-04-29)
| Tipo | Path | Notas |
|---|---|---|
| Domain entity | `backend/src/modules/brand/domain/buyer_persona.py` | objections + preferred_channels removed |
| Field contract | `backend/src/modules/brand/domain/buyer_persona_field_contract.py` | section_map + overrides cleaned |
| SQLA model | `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py` | columns dropped |
| Repository | `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py` | update methods cleaned |
| DTO | `backend/src/modules/brand/api/dto/buyer_personas.py` | request + response sans fields |
| Route | `backend/src/modules/brand/api/buyer_personas.py` | `_PROFILE_FIELDS` denominator 9→7 |
| Tests (regression) | `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` | 21 cases (new) |
| Tests (updated) | `tests/modules/brand/test_buyer_persona_entity.py`, `_model.py`, `_repository.py` | fixtures cleaned |

Diff size BE: 10 files changed, 239 insertions(+), 33 deletions(-).

### Copilot (commit `00fa55b0` — 2026-04-29)
| Tipo | Path | Notas |
|---|---|---|
| Persister | `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py` | `_LIST_FIELDS` cleaned |
| Field paths hint | `backend/src/modules/copilot/domain/field_paths_hint.py` | `_LIST_PATHS["buyer_persona"]` cleaned (offer.objections preserved) |
| Prompt template | `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2` | rule-4 cues stripped, slot order safe |
| Registry comment | `backend/src/modules/copilot/domain/extraction_domain_registry.py` | comment updated |
| Tests (updated) | `tests/modules/copilot/test_buyer_persona_extraction_template.py`, `test_editable_fields_integration.py`, `test_extract_validation.py` | fixtures cleaned |

Diff size copilot: 7 files changed, 20 insertions(+), 32 deletions(-).

### Migration (commit `d047c10b` — 2026-04-29)
| Tipo | Path | Notas |
|---|---|---|
| Alembic | `backend/alembic/versions/acdcfa45d526_drop_buyer_persona_fields.py` | raw SQL `ALTER TABLE ... DROP COLUMN IF EXISTS`, idempotente per `backend-migrations.md` |

Diff size migration: 1 file changed, 38 insertions(+).

### Frontend (commit `e4df74b8` — 2026-05-01)
| Tipo | Path | Notas |
|---|---|---|
| Schema | `frontend/src/features/brand-studio/schemas/buyer-persona.schema.ts` | 68 líneas removidas (bloques array fields) |
| API types | `frontend/src/lib/api/buyer-persona.ts` | `BuyerPersona` interface + `BuyerPersonaSectionUpdateDTO` union cleaned |
| Page | `frontend/src/features/brand-studio/pages/PersonaDetailPage.tsx` | EDITABLE_FIELDS cleaned |
| Tests (regression) | `frontend/src/features/brand-studio/schemas/__tests__/buyer-persona-schema-cleanup.test.ts` | 3 regression cases (new) |
| Tests (updated) | `frontend/src/features/brand-studio/pages/__tests__/PersonaDetailPage.test.tsx`, `components/dashboard/__tests__/BuyerPersonasDashboard.test.tsx` | mocks cleaned |

Diff size FE: 6 files changed, 27 insertions(+), 79 deletions(-).

### Total surface

- 24 archivos productivos modificados (BE+copilot+migration+FE)
- 24 regression tests nuevos (21 BE + 3 FE)
- 4 commits sobre `development`, todos pushed

## Capacidades agregadas (lineage para current-state)

No nuevas capabilities. Mantenimiento evolutivo: depreca 2 sub-fields del schema buyer_persona
sin alterar la capability `brand-buyer-personas` (que sigue live cubriendo demographics +
psychographics + pain_points/desires + buying_behavior). Ver
`docs/product/capabilities/brand/brand-buyer-personas.yaml` para estado live.

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D-1 | Distinct `objections` preserved cross-module (`offer.objections` + `sales_agent.objection_history`) | Surfaces distintas con mismo nombre — drop quirúrgico solo `buyer_persona.objections`. Test `test_offer_list_paths_objections_still_present` blinda. | IMPL-LOG (BE) |
| D-2 | Migration `DROP COLUMN IF EXISTS` raw SQL, downgrade re-crea columnas vacías sin recovery de data | `can_propose=False` + zero downstream consumers + Chris explicitly accepted data loss. | CONTRACT + IMPL-LOG |
| D-3 | Slot order template `interview/buyer_persona_doc_extraction.j2` preservado (caen líneas rule-4 sin reordenar pre/post) | Anthropic prompt cache prefix safety. | IMPL-LOG (copilot) |
| D-4 | Backup script opt-in del CONTRACT omitido | `can_propose=False` + zero consumers + Chris approved data loss = backup innecesario. | IMPL-LOG (BE) |
| D-5 | Completeness denominator `_PROFILE_FIELDS` 9→7 actualizado en route | Alineación con drop. Test `test_completeness_denominator_is_seven` blinda. | IMPL-LOG (BE) |

## Métricas medidas

No se midieron baseline pre-PR ni cierre PR (rolling track sin instrumentación métrica
formal). Outcome `pi-4-brand-evolutive-maintenance.md` lista métricas de éxito cualitativas
para el track entero, no por PR individual.

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| Ninguna | Drop quirúrgico self-contained sin TODO/HACK/disabled lint introducido | n/a |

Pre-existing nota: arch test `test_module_folders_have_ddd_layers` falla por leftover dir
`backend/src/modules/campaigns/observability/` (vacía, untracked) de sesión paralela PI-1.
NO atribuible a PR-1. Reportado intacto en su momento.

## Update obligatorios hechos

- [x] Code shipped a `development` (4 commits, todos pushed)
- [x] Migration aplicada (verificada idempotente clone DB cycle)
- [x] Tests regresión 24 cases — 21 BE + 3 FE
- [x] Quality gates verdes — Ruff + pytest 1997 brand+copilot + arch 644 + TSC + ESLint + vitest 89/89 + arch FE 51/51
- [N/A] `current-state/{módulo}.md` — paradigma legacy reemplazado por `docs/product/modules/brand.md` + `docs/product/capabilities/brand/`
- [N/A] `decisions.md` PI append — paradigma legacy, decisiones D-1..D-5 quedan en este RESULT.md
- [N/A] Sprint `learnings.md` append — ver `docs/process/learnings.md` (PM aggregate cross-paradigm)
- [N/A] Capability deprecada — n/a, sub-fields del schema, no capability completa
- [N/A] handoff.md — n/a, sprint cierra con outcome rolling, no hay handoff a sprint siguiente bajo legacy

## Próximo paso PM

- Outcome `pi-4-brand-evolutive-maintenance` rolling track cierra como `done` en paradigma nuevo (2026-05-06).
- Future scope: si Chris trae nuevos batches de feedback brand schema → /pm crea outcome nuevo bajo paradigma actual (`docs/product/outcomes/{slug}.md`). NO reabrir PI-4.

---

PR-1 **shipped** (retro-confirmed 2026-05-06). Loop completo cerrado retroactivamente.
