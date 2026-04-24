# Fase 04 — Drop `OFFER_FIELDS_BY_FE_SECTION`

## Objetivo

Eliminar el dict legacy. Reemplazar por util `fields_by_section(contract, section_key)` derivado puro de `FieldContract`.

## Scope

**Dentro**:
- Util `backend/src/modules/offer/domain/field_contract.py::fields_by_section(section)` → tuple[str, ...]
- Consumers migrados:
  - `backend/src/modules/offer/workers/tasks.py` (on_progress) — usa la util
  - `backend/src/modules/offer/domain/extraction_section_map.py::fields_to_fe_sections` — refactor a usar util
- Tests de extraction worker updated con nueva util
- Dict `OFFER_FIELDS_BY_FE_SECTION` eliminado
- Arch test: el dict no puede re-aparecer

**Fuera**:
- Downstream sales-agent/landing consume contract directamente (Fase 05)

## Análisis requerido al abrir fase

- Verificar que `FieldContract` tiene TODOS los fields que `OFFER_FIELDS_BY_FE_SECTION` lista hoy (checks paridad)
- Si falta alguno → Fase 02 no cerró completo. Volver a Fase 02.
- Tests extraction section grouping (post-diff, wave grouping) no regressan

## Duración estimada

0.5 sprint.

## Riesgo

Bajo. Paridad testeable.

## DoD

Al abrir fase, escribir ACCEPTANCE.md.
