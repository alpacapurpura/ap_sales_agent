---
last_updated: 2026-04-24 (Fase 06 done)
last_green_commit: ed8a3a4f
active_phase: 07-buyer-migration
sub_step: 0/? (ready-to-start)
status: ready-to-start
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
- **Fase activa**: 07-buyer-migration (ready-to-start)
- **Última fase cerrada**: 06-brand-migration (6 commits, 61606fcf → ed8a3a4f)
- **Rama**: `development`
- **Working tree**: limpio

## Próxima acción

Arrancar Fase 07. Seguir:

1. Lee [protocol/RESUME.md](protocol/RESUME.md).
2. Lee [phases/07-buyer-migration/PRE_INVESTIGATION.md](phases/07-buyer-migration/PRE_INVESTIGATION.md).
3. Lee [phases/07-buyer-migration/SPEC.md](phases/07-buyer-migration/SPEC.md).
4. Knowledge load: inventario `BUYER_PERSONA_EDITABLE_FIELDS` (independent
   catalog) + `BuyerPersona` Pydantic (dict-typed JSONB columns) + drift
   audit + decisión walker vs hand-authored para JSONB sub-keys.
5. Capturar baseline golden buyer-persona.
6. Escribir ACCEPTANCE.md.
7. Ejecutar PRE_FLIGHT.md.

Prompt completo en [HANDOFF.md](HANDOFF.md).

## Contexto mínimo

- Fase 06 cerró: brand FieldContract registry derivado (113 contracts,
  86 proposable, 38/38 WORKING preserved, 0 BROKEN resurfaced, +48 nuevas
  capabilities via Drift C closure). 471 arch tests, 4261+ backend tests.
- Drift cerrado:
  - A: 17 shorthand 2-level paths broken (`positioning.insight_tension`,
    `narrative.problem_villain` etc) — el walker emite los sub-objects
    como OBJECT can_propose=False.
  - B: 23 paths bajo wrong section (`contact.legal_*` → `identity.legal_*`)
    corregidos preservando labels.
  - C: 48 Pydantic fields sin entry catalog ahora cubiertos por derivación.
- Buyer-persona standalone (no es sub-model de BrandSettings) — registrado
  como dominio separado `"buyer_persona"`. Fase 07 lo migra como módulo
  virtual con su propio FieldContract.
- Diferidos en LEARNINGS Fase 05: full data-driven loop en
  `agent_identity.j2`, alineación completion ↔ contract semantics,
  migración landing builders al Offer aggregate.

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
| 06.G | (this commit) | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 07 |

## Convención de actualización

Cada commit material:
1. Update `last_updated` + `last_green_commit`.
2. Update `sub_step` y/o `active_phase`.
3. Update `status` si transición.
4. Si hay blocker → listarlo explícito.

Nunca dejes STATE.md desactualizado después de commit material.
