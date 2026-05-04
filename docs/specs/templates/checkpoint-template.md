# Checkpoint Template — Resume Protocol

> Cada nivel (PI / sprint / story) tiene SU checkpoint.md.
> Cualquier sesión nueva lee este archivo PRIMERO para saber dónde retomar.
> Hooks `.claude/hooks/post-edit-checkpoint.sh` actualizan `last_artifact` + `last_modified` automáticamente.

---
level: story                                     # PI | sprint | story
id: STORY_ID                                     # match folder name
phase: PO_SPEC                                   # ver tabla abajo
status: in-progress                              # pending | in-progress | done | blocked
last_artifact: 01-spec.md                        # último archivo escrito en este nivel
last_modified: 2026-05-04T15:23:00Z
next_action: "Chris ratifica spec → invocar /ux-agentico"
spawned_at: 2026-05-04T14:00:00Z
spawned_by: /pm
parallel_safe: true                              # ¿otra sesión puede tocar artefactos de esta story sin conflict?
blocked_reason: null
audit_iterations: 0                               # cuenta intentos auditor (cap 2 → escala)
---

## Phases (story-level)

| Phase | Owner | Inputs | Output | Next |
|---|---|---|---|---|
| `PM_DRAFT` | /pm | opportunity / idea | `00-story.md` | `PO_SPEC` |
| `PO_SPEC` | /po | `00-story.md` + spec template | `01-spec.md` + story YAML | `UX_UI` o `UX_AGENTIC` o `ARCHITECT` (según type) |
| `UX_UI` | /ux-ui | `01-spec.md` (ui-story) | `02-design-ui.md` (+ optional spec delta) | `ARCHITECT` |
| `UX_AGENTIC` | /ux-agentico | `01-spec.md` (agentic-story) | `02-design-agentic.md` (+ optional spec delta) | `ARCHITECT` |
| `ARCHITECT` | /architect | `01` + `02` | spawns architect-{be,fe,agentic} paralelo → `03-arch-*.md` + `04-tickets.yaml` | `DEV_T1` |
| `DEV_T{n}` | /dev-team | `T-{n}-handoff.md` | `T-{n}-impl-log.md` + `T-{n}-result.md` + push commit | `AUDIT_T{n}` |
| `AUDIT_T{n}` | /auditor | `T-{n}-result.md` + tests | `T-{n}-review.md` (APPROVED \| CHANGES_REQUESTED) | next ticket O `MERGE` |
| `MERGE` | /pm | all tickets audit-passed + `REVIEW-final.md` | `07-merge.md` + apply diff to `product/` | `DONE` |
| `DONE` | (closed) | — | — | — |
| `BLOCKED` | any | — | escala Chris | resolver bloqueo |

## Phases (sprint-level)

| Phase | Owner | Output |
|---|---|---|
| `PLANNING` | /pm | `sprint.md` + N `00-story.md` |
| `EXECUTING` | (mix) | stories en estados varios |
| `WRAP_UP` | /pm | sprint retrospective en `sprint.md` |
| `DONE` | (closed) | sprint movido a archive cuando PI cierra |

## Phases (PI-level)

| Phase | Owner | Output |
|---|---|---|
| `DISCOVERY` | /pm + Chris | `PI.md` + opportunities validadas |
| `EXECUTING` | (mix) | sprints + stories |
| `WRAP_UP` | /pm | PI retrospective |
| `ARCHIVED` | (closed) | mover a `projects/archive/PI-N/` |

## Bitácora

> Append-only. Cada agent que toca un artefacto logea aquí.

- 2026-05-04 14:00 — /pm creó folder y `00-story.md`
- 2026-05-04 14:30 — /po redactó `01-spec.md`. Chris ratificó.
- 2026-05-04 15:23 — En espera de /ux-agentico

## Notas

- Si `parallel_safe=false`, otra sesión NO debe tocar artefactos hasta `next_action` complete.
- Si `blocked_reason != null`, ningún agent procede hasta Chris/PM resuelva.
- `audit_iterations >= 2` → escala automática a Chris (no más self-fix loops).
