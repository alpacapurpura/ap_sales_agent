---
level: PI
id: PI-12
phase: PLANNING                                  # PLANNING | EXECUTING | WRAP_UP | ARCHIVED
status: in-progress                              # pending | in-progress | done | blocked
last_artifact: PI.md
last_modified: 2026-05-04T19:00:00Z
next_action: "Chris ratifica scope (3 objetivos + decomposition 8 stories) → /pm crea stories/{id}/00-story.md por cada uno → hand off /po"
spawned_at: 2026-05-04T19:00:00Z
spawned_by: /pm
parallel_safe: false                             # PI-12 toca sales_agent — single session only durante este PI
blocked_reason: null
audit_iterations: 0
---

## Phases (PI-level)

| Phase | Owner | Output |
|---|---|---|
| `PLANNING` | /pm | PI.md + 8 `00-story.md` |
| `EXECUTING` | (mix) | sprints + stories en estados varios |
| `WRAP_UP` | /pm | retrospective en PI.md + decisions.md |
| `ARCHIVED` | (closed) | mover a `projects/archive/PI-12/` |

## Bitácora

> Append-only.

- 2026-05-04 19:00 — `/pm` creó folder + PI.md desde template `PI-template.md`. Status=PLANNING. Esperando ratificación Chris para decomposition.

## Decisiones pendientes (ratificación Chris)

1. ¿Aprobás los 3 objetivos del PI?
2. ¿Aprobás decomposition en 8 stories / 4 sprints?
3. ¿Algún story que querés cambiar/agregar/quitar?
4. ¿Cambiar orden sprints? (ej. cost-fix S4 → S1 si preferís quick win primero)
5. ¿Quién cura goldens dataset (S2 story 3) — vos solo o spawn agent helper?

## Next session resume protocol

1. `cat docs/projects/active/PI-12-sales-agent-eval-foundation/checkpoint.md`
2. Si `phase: PLANNING` + `next_action: Chris ratifica` → preguntar Chris ratificación antes proceder
3. Si ratificado → crear `sprints/S1-eval-runner/sprint.md` + checkpoint.md + 2 `stories/{id}/00-story.md` + handoff /po
4. Si NO ratificado → preguntar Chris decisión
