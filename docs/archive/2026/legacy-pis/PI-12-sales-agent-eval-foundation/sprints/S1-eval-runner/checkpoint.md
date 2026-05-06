---
level: sprint
id: S1-eval-runner
phase: PLANNING                                  # PLANNING | EXECUTING | WRAP_UP | DONE
status: in-progress                              # pending | in-progress | done | blocked
last_artifact: sprint.md
last_modified: 2026-05-04T20:00:00Z
next_action: "Chris invoca /po dentro de stories/sales-agent-eval-runner-foundation/ → expandir 00-story.md a 01-spec.md (orden sugerido en sprint.md)"
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false                             # PI-12 entero parallel_safe=false (sales_agent single session)
blocked_reason: null
audit_iterations: 0
---

## Phases (sprint-level)

| Phase | Owner | Output |
|---|---|---|
| `PLANNING` | /pm | `sprint.md` + N `00-story.md` |
| `EXECUTING` | (mix) | stories en estados varios |
| `WRAP_UP` | /pm | sprint retrospective en `sprint.md` |
| `DONE` | (closed) | sprint movido a archive cuando PI cierra |

## Stories status

| Story | Phase | Status |
|---|---|---|
| `sales-agent-eval-runner-foundation` | PM_DRAFT | pending |
| `sales-agent-eval-pass-k-tracking` | PM_DRAFT | pending |
| `sales-agent-eval-cost-budget-cap` | PM_DRAFT | pending |
| `sales-agent-cost-tracking-deepseek-fix` | PM_DRAFT | pending |

## Bitácora

- 2026-05-04 20:00 — `/pm` creó sprint folder + 4 `00-story.md`. Status=PLANNING.

## Notas

- Chris arranca con `/po` en `sales-agent-cost-tracking-deepseek-fix` (independiente, paralelizable) o `sales-agent-eval-runner-foundation` (bloquea 2 y 3) — cualquiera de los dos primero.
- Recordá: `parallel_safe=false` a nivel PI. Otra sesión NO debe tocar `modules/sales_agent/` ni `shared/agent_observability/cost/` durante este sprint.
