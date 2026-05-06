---
id: pi-4-brand-evolutive-maintenance
state: done
title: Mantenimiento evolutivo Brand Studio (rolling)
why_now: |
  Track rolling para responder feedback usuario sobre schema/UX Brand Studio
  sin pelear cap Now con feature PIs. Permite eliminar/fusionar/renombrar
  fields existentes en days, no weeks.
target_end: 2026-04-29
closed_at: 2026-05-06
priority: 3
created: 2026-04-29
last_modified: 2026-05-06
migrated_from: docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/
story_ids: []
success_metrics:
  - "Completion rate buyer persona post-cleanup"
  - "Cualitativo: 'los formularios no me piden cosas que no necesito'"
  - "Tiempo desde feedback → ship < 5 días"
tags:
  - module:brand
  - type:rolling-maintenance
---

# Mantenimiento evolutivo Brand Studio

Track rolling de modificaciones de campos/secciones Brand Studio basado en
feedback usuarios. Sprint = batch de items micro shipeados juntos cuando son
cohesivos. NO compite cap Now con feature PIs — corre paralelo.

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-4-brand-evolutive-maintenance/`.

Estado en migración: rolling — S1 PR-1 (drop-buyer-persona-fields) tiene
RESULT.md (shipped). Track sigue activo hasta que Chris declare cierre.

## Original content summary

Modelo de operación rolling maintenance:
- Sprint cierra cuando batch deployado y `current-state/brand.md` actualizado
- Nuevo sprint se abre cuando Chris trae nuevo feedback usuario
- Upgrade a feature PI si scope crece a refactor cross-secciones o ≥3 fields
  cohesivos con UX nueva

Scope in: eliminación/fusión/rename/reorder de fields existentes en cualquier
sección Brand Studio (identity, visuals, story, positioning, narrative,
personality, communication, buyer_personas, team, testimonials, authority).
Tweaks copy UI por feedback claridad. Ajustes form-runtime (renderAs, defaults).
Coordinación cross-impacto con copilot (extraction prompts, persisters,
field paths) cuando se toca schema brand.

Scope out: capacidades nuevas grandes (upgrade a feature PI), cambios voice
sales_agent (PI-3), wire copilot multi-canal (PI-5), refactor cross-módulo
brand→offer→landing.

Restricciones cardinales: brand→copilot impact (cleanup copilot dentro del
mismo PR, no splitear); migration safety (DROP COLUMN sin data migration
plan = riesgo); form-runtime arch tests respetados (ratchet shrink-only).

## Closure note (2026-05-06)

Rolling track cerrado por decisión Chris. Estado real al cierre:

- **Legacy PR-1 `drop-buyer-persona-fields` retro-filled** — RESULT.md + REVIEW.md
  completados retroactivamente en `docs/archive/2026/legacy-pis/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/`.
  Originalmente shipped 2026-04-29 / 2026-05-01 en 4 commits (`80551ec5`, `00fa55b0`,
  `d047c10b`, `e4df74b8`) con 24 regression tests (21 BE + 3 FE), pero los templates
  jamás fueron llenados antes de la migración Wave 2 al paradigma nuevo.
- **5 brand capabilities live** en `docs/product/capabilities/brand/`:
  brand-buyer-personas, brand-credentials, brand-extraction, brand-identity-visuals,
  brand-personality-voice. INDEX.md flagged for regen via R32 `scripts/reconcile_capabilities.py`.
- **Module narrative live** en `docs/product/modules/brand.md` (paradigma nuevo SSoT
  funcional reemplazó `current-state/brand.md` legacy).

### Future scope

Si en el futuro Chris trae nuevos batches de feedback sobre schema/UX Brand Studio →
`/pm` crea outcome **nuevo** bajo paradigma actual (`docs/product/outcomes/{slug}.md`)
con stories en `docs/product/stories/{story-id}/`. **NO reabrir PI-4** — ese PI cierra
paradigma legacy y queda como audit trail inmutable en `docs/archive/2026/legacy-pis/`.

### Lessons learned

- **Rolling-track paradigm vs finite-outcome.** El rolling track sirvió bajo legacy para
  no pelear cap Now con feature PIs, pero degradó closure discipline: PR-1 shipped pero
  RESULT/REVIEW jamás llenados. El paradigma nuevo prefiere outcomes **finitos** event-
  driven (cada batch de feedback = un outcome nuevo con scope definido y closure
  explícita) — no rolling indefinido.
- **Migration windows requieren retro-fill obligatorio.** Cuando se migra paradigma con
  loops abiertos, la transición debe forzar cierre formal (RESULT/REVIEW retroactivos)
  ANTES de reasignar state, no DESPUÉS — para evitar audit gaps que se descubren días
  después al cerrar el track.
