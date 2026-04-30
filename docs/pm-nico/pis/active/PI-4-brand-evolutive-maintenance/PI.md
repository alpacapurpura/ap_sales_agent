# PI-4-brand-evolutive-maintenance — Mantenimiento Evolutivo Brand Studio

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-4-brand-evolutive-maintenance |
| Tipo | **maintenance** (rolling, no compite cap Now con feature PIs) |
| Estado | active |
| Tema | Mantenimiento evolutivo Brand Studio — modificaciones de campos/secciones desde feedback usuarios |
| Owner PM | /pm |
| Inicio | 2026-04-29 |
| Cierre estimado | rolling (cierra cuando Chris declara fin del track) |
| Cierre real | — |

## Modelo de operación (rolling maintenance)

- Sprint = batch de items micro shipeados juntos cuando son cohesivos.
- Sprint cierra cuando batch deployado y `current-state/brand.md` actualizado.
- Nuevo sprint se abre cuando Chris trae nuevo feedback usuario.
- NO compite cap Now con feature PIs (PI-1/2/3) — corre paralelo.
- **Upgrade a feature PI** si scope crece a refactor cross-secciones o ≥3 fields cohesivos con UX nueva.

## Outcome esperado

Brand Studio refleja schema/UX que **users reales necesitan**, sin campos huérfanos ni fricción innecesaria. Cada item shipeado responde a feedback validado.

- Cuantitativo: completion rate buyer persona (medible post-cleanup)
- Cualitativo: "los formularios no me piden cosas que no necesito"

## Scope (rolling)

### In

- Eliminación / fusión / rename / reorder de fields existentes en cualquier sección Brand Studio (identity, visuals, story, positioning, narrative, personality, communication, buyer_personas, team, testimonials, authority).
- Tweaks copy UI (labels, hints, placeholders) por feedback claridad.
- Ajustes form-runtime (renderAs, defaults) si feedback indica fricción.
- Coordinación cross-impacto con copilot (extraction prompts, persisters, field paths) cuando tocás schema brand.

### Out

- Capacidades nuevas grandes (upgrade a feature PI dedicado).
- Cambios que afecten contratos sales_agent voice (eso vive en PI-3 / sales-agent-expert).
- Wire copilot multi-canal (telegram/whatsapp) → vive en PI-2-copilot-improvement.
- Refactor cross-módulo brand→offer→landing.

## PRs (rolling, append-only)

| PR | Sprint | Slug | Estado | Folder |
|---|---|---|---|---|
| PR-1 | S1 | drop-buyer-persona-fields | ready | `sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/` |

## Sprints

| Sprint | Estado | Folder |
|---|---|---|
| S1 cleanup-buyer-persona | in-progress | `sprints/S1-cleanup-buyer-persona/` |

## Restricciones / Riesgos

- **R1 — Brand→copilot impact**: cualquier eliminación de field brand toca copilot extraction (templates j2, persisters, field_paths_hint, field-contract overrides). PR debe incluir cleanup copilot dentro del mismo PR. NO mover a PI-2.
- **R2 — Brand→sales_agent**: voz sales_agent NO usa estos fields hoy (verified Explore). Si futuro PR toca communication style → flag con `sales-agent-expert`.
- **R3 — Migration safety**: DROP COLUMN sin data migration plan = riesgo. Cada PR con DROP confirma "data útil = 0" o backup script antes.
- **R4 — Form-runtime arch tests**: schema editado debe respetar tests `frontend/src/__tests__/architecture/` (ratchet allowlists shrink-only).

## Decisiones clave (append-only)

| Fecha | Decisión | Razón |
|---|---|---|
| 2026-04-29 | Track rolling, no PI feature normal | Permite responder feedback usuario en días sin pelear cap Now ni encolar en PIs feature |
| 2026-04-29 | Cleanup copilot por dependencia brand vive DENTRO del PR brand | Cohesión + evita refactor splitado entre PIs |

## Métricas seguimiento

- # items shipeados / sprint
- # PRs con upgrade a feature PI (señal de scope mismatch)
- Tiempo desde feedback → ship (target < 5 días)

## Cierre / Retro

Track sigue activo hasta que Chris declare cierre. Cuando cierre:
1. `retro.md` consolida learnings cross-sprint
2. PI completo a `pis/archive/PI-4-brand-evolutive-maintenance/`
3. Roadmap "Done" linkea archive
