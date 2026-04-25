---
status: done
opened_at: 2026-04-24
closed_at: 2026-04-24
baseline_green_commit: 1f210a5d
last_green_commit: e1f44284
sub_step: F/F
baseline_arch_tests: 490
final_arch_tests: 507
baseline_copilot_acceptance: 52
final_copilot_acceptance: 52
---

# Fase 08 — Copilot unification · Status

**Done**. 5 commits atómicos (0d9ccc40 → e1f44284). Copilot ahora
consume `FieldContract` cross-module sin SSoT paralelos. Reduce 5
fuentes (port + 3 catalog files + schema_introspection) a 1 (registry).

## Resultados

| Métrica | Pre-Fase 08 | Post-Fase 08 |
|---|---|---|
| Catalog projection files (offer/brand/buyer_persona) | 3 boilerplate idéntico | 0 (deriva en port) |
| `_DOMAIN_BUILDERS` source | mixto (Pydantic walk + import + hand-authored) | 1 (FieldContract registry) |
| `_DOMAIN_DICT_PARENTS` | hand-authored hardcoded | derivado de `BUYER_PERSONA_DICT_SUBKEYS.keys()` |
| Tests arch | 490 | 507 (+25 derivation/anti-regression -8 dropped projection) |
| Tests copilot acceptance | 52 | 52 (byte-identical) |

## Sub-steps

| # | Commit | Descripción |
|---|---|---|
| 08.A | `0d9ccc40` | docs PRE_INVESTIGATION + SPEC + ACCEPTANCE |
| 08.B | `b4e7a43d` | port deriva + drop 3 catalog projection files |
| 08.C | `074977b6` | schema_introspection._build_*_paths derivan |
| 08.D | `e1f44284` | 3 arch tests anti-regression (derivation + no catalog files + no hand-authored paths) |
| 08.F | (this commit) | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 09 |

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
