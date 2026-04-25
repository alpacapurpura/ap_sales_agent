---
status: in_progress
opened_at: 2026-04-24
closed_at: null
baseline_green_commit: 1f210a5d
sub_step: A/F
baseline_arch_tests: 490
baseline_copilot_acceptance: 52
---

# Fase 08 — Copilot unification · Status

**In progress** (sub-step 08.A). Fase 07 cerrada. 3 módulos migrados al
FieldContract platform: offer + brand + buyer_persona.
490 arch tests + 52 copilot acceptance tests verde como baseline.

## Scope (per PLAN.md §Fase 08)

Eliminar duplicación interna del copilot. `editable_fields` port +
`schema_introspection` consumen `FieldContract` cross-module en lugar
de su set/dict paralelo. Reduce 2 SSoT a 1.

## Deliverables esperados

- `shared/links/ports/editable_fields.py` rewriteado: `get_catalog(domain)`
  proyecta de `get_module_contracts(domain)` con filtro `can_propose=True`
  + `status=ACTIVE`.
- `copilot/domain/schema_introspection.py`:
  - `_build_offer_paths` / `_build_brand_paths` / `_build_buyer_persona_paths`
    consumen `get_module_contracts(domain)` directo.
  - `_DOMAIN_DICT_PARENTS["buyer_persona"]` deriva de
    `BUYER_PERSONA_DICT_SUBKEYS.keys()` o se elimina si validator pasa
    a strict.
  - `validate_field_path`: strict mode opcional.
- `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS`: evaluar drop
  del archivo o promoción a `get_module_contracts("offer")` directo.
- Tests acceptance copilot existentes pasan idéntico.

## Pre-investigación obligatoria

- Mapeo TODOS los call sites de `get_catalog`, `validate_field_path`,
  `is_editable_path`, `get_model_sections`, `format_editable_field_catalog_markdown`.
- Identificar dónde `propose_field_updates` valida paths — flujo crítico.
- Confirmar que ningún consumer downstream consume el shape interno
  de `_DOMAIN_FIELD_CACHE` directo.
- Acceptance copilot tests: chat tests + propose_field_updates tests
  + interview persister tests.

## Riesgo

Medio-alto. Copilot está en producción. Tests acceptance exhaustivos
requeridos.
