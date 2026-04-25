---
last_updated: 2026-04-24 (Fase 09 sub-paso A done)
last_green_commit: a61aea16
active_phase: 09-multi-channel-projection
sub_step: A/G done (docs)
status: in-progress
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
- **Fase activa**: 09-multi-channel-projection (ready-to-start)
- **Última fase cerrada**: 08-copilot-unification (5 commits, 0d9ccc40 → e1f44284)
- **Rama**: `development`
- **Working tree**: limpio

## Próxima acción

Arrancar Fase 09. Seguir:

1. Lee [protocol/RESUME.md](protocol/RESUME.md).
2. Lee [phases/09-multi-channel-projection/STATUS.md](phases/09-multi-channel-projection/STATUS.md).
3. Crear `phases/09-multi-channel-projection/PRE_INVESTIGATION.md` con
   inventario del estado del copilot conversacional cross-channel
   (whatsapp/telegram channel adapters, bound tools, current question
   flow), trade-offs LLM vs algoritmo determinístico, compat web↔chat.
4. Crear `phases/09-multi-channel-projection/SPEC.md` con plan algoritmo
   `next_question(module, state)` data-driven + integración channel
   adapters + tests E2E channel-agnostic.
5. Capturar baseline acceptance tests (copilot + sales-agent + cualquier
   E2E chat existente).
6. Escribir ACCEPTANCE.md.
7. Ejecutar PRE_FLIGHT.md.

Prompt completo en [HANDOFF.md](HANDOFF.md).

## Contexto mínimo

- Fase 08 cerró: copilot consume `FieldContract` cross-module unificado.
  3 catalog projection files dropeados (boilerplate idéntico). Port +
  schema_introspection derivan del registry. 25 arch tests anti-regression.
  507 arch tests (+17 net), 695 copilot tests pass, 52 acceptance verde
  byte-identical.
- 3 módulos migrados al FieldContract platform: offer (Fase 04), brand
  (Fase 06), buyer_persona (Fase 07). Copilot (Fase 08) ya consume
  unificado.
- Diferidos en LEARNINGS Fase 05 (siguen pendientes — posible sub-fase
  de Fase 09): full data-driven loop en `agent_identity.j2`, alineación
  completion ↔ contract semantics, migración landing builders al Offer
  aggregate.
- Diferidos en LEARNINGS Fase 08 (tangenciales):
  - `offer_fields.py` alias mantenido (4 consumers críticos).
  - `get_model_sections` consumers (admin + 6 copilot) sin migrar al
    FieldContract — out of scope Fase 08, futuro phase si necesario.
  - Walker extension list[dict] item sub-keys (LEARNINGS Fase 07).

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
| 07.G | `1f210a5d` | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 08 |

## Historial Fase 08

| Sub-step | Commit | Descripción |
|---|---|---|
| 08.A | `0d9ccc40` | docs PRE_INVESTIGATION + SPEC + ACCEPTANCE Fase 08 |
| 08.B | `b4e7a43d` | editable_fields port deriva + drop 3 catalog projection files |
| 08.C | `074977b6` | schema_introspection._build_*_paths derivan del FieldContract registry |
| 08.D | `e1f44284` | 3 arch tests anti-regression (derivation + no catalog files + no hand-authored paths) |
| 08.F | (this commit) | close phase + LEARNINGS + STATE/STATUS bump + HANDOFF Fase 09 |

## Convención de actualización

Cada commit material:
1. Update `last_updated` + `last_green_commit`.
2. Update `sub_step` y/o `active_phase`.
3. Update `status` si transición.
4. Si hay blocker → listarlo explícito.

Nunca dejes STATE.md desactualizado después de commit material.
