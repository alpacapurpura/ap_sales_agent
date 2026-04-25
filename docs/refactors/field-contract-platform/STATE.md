---
last_updated: 2026-04-24 (Fase 08 in progress · sub-step D done)
last_green_commit: 074977b6
active_phase: 08-copilot-unification
sub_step: D/F
status: in_progress
blockers: none
branch: development
working_tree_clean: true
parallel_session_files_ignored:
  - buyer-persona-ai-flow-verified.png
  - qa-extract-clean.png
  - docs/refactors/copilot-architecture/
---

# Estado actual

## Dónde estamos

- **Refactor**: field-contract-platform
- **Fase activa**: 08-copilot-unification (ready-to-start)
- **Última fase cerrada**: 07-buyer-migration (6 commits, 8394ecee → e4714606)
- **Rama**: `development`
- **Working tree**: limpio

## Próxima acción

Arrancar Fase 08. Seguir:

1. Lee [protocol/RESUME.md](protocol/RESUME.md).
2. Lee [phases/08-copilot-unification/STATUS.md](phases/08-copilot-unification/STATUS.md).
3. Crear `phases/08-copilot-unification/PRE_INVESTIGATION.md` (no existe
   aún) inventariando call sites de `get_catalog`, `validate_field_path`,
   `is_editable_path`, `get_model_sections`, `format_editable_field_catalog_markdown`.
4. Crear `phases/08-copilot-unification/SPEC.md` con plan migración
   editable_fields port + schema_introspection a derivación de
   `get_module_contracts(domain)`.
5. Capturar baseline acceptance copilot tests.
6. Escribir ACCEPTANCE.md.
7. Ejecutar PRE_FLIGHT.md.

Prompt completo en [HANDOFF.md](HANDOFF.md).

## Contexto mínimo

- Fase 07 cerró: buyer-persona FieldContract registry derivado (18 contracts,
  12 proposable byte-identical al catalog legacy). Walker shared
  extendido con `dict_subkeys` arg (Patrón B) — habilita cualquier
  módulo futuro con JSONB sub-keys. 491 arch tests (+20), 4286+ BE tests.
- 3 módulos migrados al FieldContract platform: offer (Fase 04), brand
  (Fase 06), buyer_persona (Fase 07). Generic fitness gates parametrizadas
  cubren los 3 sin cambios — pattern Fase 04.I confirmado por tercera vez.
- Diferidos en LEARNINGS Fase 05: full data-driven loop en
  `agent_identity.j2`, alineación completion ↔ contract semantics,
  migración landing builders al Offer aggregate.
- Diferidos en LEARNINGS Fase 07 (scope Fase 08): convertir
  `_build_*_paths` en `schema_introspection.py` a `get_module_contracts(domain)`
  directo. Drop o simplificar `_DOMAIN_DICT_PARENTS` derivándolo de
  `BUYER_PERSONA_DICT_SUBKEYS.keys()`. Evaluar drop de
  `copilot/domain/offer_fields.py`.

## Workspaces

- **Activo**: `docs/refactors/field-contract-platform/` (este).
- **Histórico**: `docs/refactors/field-contract-ssot/` (Fases 00-03
  cerradas allá).

## Historial Fase 04

| Sub-step | Commit | Descripción |
|---|---|---|
| 04.A | `5ba48682` | docs workspace + ADRs 011-017 + plan 04-09 |
| 04.B | `5178cd68` | shared FieldContract platform core + 16 unit tests |
| 04.C | `9b9fb427` | offer migra a shared (153 contracts derivados) |
| 04.D | `5c810c5c` | fields_to_fe_sections deriva del registry |
| 04.E | `e23f14ec` | OFFER_EDITABLE_FIELDS proyecta del registry |
| 04.F | `f91792c6` | PERSISTABLE_FIELDS deriva |
| 04.G | `4bda9821` | drop OFFER_FIELDS_BY_FE_SECTION + anti-regression |
| 04.H | `6c643378` | cross-cutting arch tests (Pydantic ⊆ contract) |
| 04.I | `fc22f528` | generic future-module guards |
| 04.J | `c8ddd79e` | close phase + LEARNINGS + handoff |

## Historial Fase 05

| Sub-step | Commit | Descripción |
|---|---|---|
| 05.A | `94036809` | golden snapshots: agent_identity + landing + completion |
| 05.B | `7d0157a4` | sales_agent lifecycle gate via FieldContract |
| 05.C | `37154119` | arch test: agent_identity.j2 paths ⊆ contract |
| 05.D | `0aa7e550` | arch test: completion validators ⊆ contract |
| 05.E | `d0d121f1` | arch test: landing builders ⊆ contract |
| 05.G | `fcef64a4` | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 06 |

## Historial Fase 06

| Sub-step | Commit | Descripción |
|---|---|---|
| 06.A | `61606fcf` | brand catalog baseline + ACCEPTANCE + PRE_INVESTIGATION |
| 06.B | (folded) | platform tests pre-brand — fold-into-06.C |
| 06.C | `8d3dd998` | brand FieldContract registry derivado de BrandSettings |
| 06.D | `3539e85f` | BRAND_EDITABLE_FIELDS proyectado del registry |
| 06.E | `9c1ec582` | MIGRATED_MODULES bump brand + brand pydantic coverage |
| 06.F | `ed8a3a4f` | brand catalog anti-regression (projection mandatoria) |
| 06.G | `bd7bfd31` | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 07 |

## Historial Fase 07

| Sub-step | Commit | Descripción |
|---|---|---|
| 07.A | `8394ecee` | buyer-persona catalog baseline + ACCEPTANCE + PRE_INVESTIGATION |
| 07.B | `16648588` | walker dict_subkeys arg (Patrón B) + 6 unit tests |
| 07.C | `468569c4` | buyer-persona FieldContract registry derivado de BuyerPersona |
| 07.D | `61fae65b` | BUYER_PERSONA_EDITABLE_FIELDS proyectado del registry |
| 07.E | `4ff56c23` | MIGRATED_MODULES bump buyer + pydantic coverage |
| 07.F | `e4714606` | buyer-persona catalog anti-regression (projection mandatoria) |
| 07.G | (this commit) | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 08 |

## Convención de actualización

Cada commit material:
1. Update `last_updated` + `last_green_commit`.
2. Update `sub_step` y/o `active_phase`.
3. Update `status` si transición.
4. Si hay blocker → listarlo explícito.

Nunca dejes STATE.md desactualizado después de commit material.
