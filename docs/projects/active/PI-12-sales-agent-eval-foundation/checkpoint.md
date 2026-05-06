---
level: PI
id: PI-12
phase: EXECUTING                                 # PLANNING | EXECUTING | WRAP_UP | ARCHIVED
status: in-progress                              # pending | in-progress | done | blocked
last_artifact: sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/07-merge.md
last_modified: 2026-05-06T03:55Z
next_action: "S1 wrap-up: Story A + Story B audit-passed (REVIEW-final.md + 07-merge.md per story written). Story C + D deferred to S2 planning. /pase-produccion deploys A + B together. Post-deploy: /pm closes deferred A1/A3/A4/A5 verifiers + auto-promotes T-6b → verified per Streamlit query. Then S2 planning kicks off (pass-k-tracking + budget-cap)."
spawned_at: 2026-05-04T19:00:00Z
spawned_by: /pm
parallel_safe: false                             # PI-12 toca sales_agent — single session only durante este PI
blocked_reason: null
audit_iterations: 13
---

## Phases (PI-level)

| Phase | Owner | Output |
|---|---|---|
| `PLANNING` | /pm | PI.md + N `00-story.md` |
| `EXECUTING` | (mix) | sprints + stories en estados varios |
| `WRAP_UP` | /pm | retrospective en PI.md + decisions.md |
| `ARCHIVED` | (closed) | mover a `projects/archive/PI-12/` |

## Bitácora

> Append-only.

- 2026-05-04 19:00 — `/pm` creó folder + PI.md desde template `PI-template.md`. Status=PLANNING. Esperando ratificación Chris para decomposition.
- 2026-05-04 20:00 — Chris ratificó: 3 objetivos OK, decomposition OK, agregar Story 3 budget-cap, mover Story 4 cost-fix de S4 a S1, goldens curation híbrido (b), path `backend/tests/agentic_evals/sales_agent/` confirmado. /pm actualizó PI.md con 9 stories finales + creó 4 sprints + 9 `00-story.md`. Status → EXECUTING.

## Decisiones ratificadas (2026-05-04)

1. ✅ 3 objetivos del PI aprobados (eval suite + voice gate + cost accuracy)
2. ✅ Decomposition 9 stories / 4 sprints / ~23d
3. ✅ Story `sales-agent-eval-cost-budget-cap` agregada como Story 3 en S1 (defensa preventiva runaway costo)
4. ✅ Story `sales-agent-cost-tracking-deepseek-fix` movida de S4 a S1 (quick win + reporting confiable día 1)
5. ✅ Goldens curation híbrido (b): agent-helper extrae candidatos de `sales_agent_session` real + `sanitize_payload`, Chris ratifica los 12 finales
6. ✅ Path `backend/tests/agentic_evals/sales_agent/` confirmado

## Sprints creados

- `sprints/S1-eval-runner/` — 4 stories (runner, pass^k, budget-cap, deepseek-fix). Status=PLANNING.
- `sprints/S2-goldens-personas/` — 2 stories (goldens-dataset, personas-runtime). Status=PLANNING.
- `sprints/S3-voice-fidelity-gate/` — 2 stories (grader-runtime, ci-gate). Status=PLANNING.
- `sprints/S4-adversarial/` — 1 story (jailbreak-suite). Status=PLANNING.

## Next session resume protocol

1. `cat docs/projects/active/PI-12-sales-agent-eval-foundation/checkpoint.md`
2. `cat docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/checkpoint.md`
3. Identificar primera story con phase `PM_DRAFT` y status `pending` → invocar `/po` ahí
4. Phase orden ejecución S1: `eval-runner-foundation` → `eval-pass-k-tracking` (depends 1) → `eval-cost-budget-cap` (depends 1) → `cost-tracking-deepseek-fix` (independiente, paralelizable con qwen-opencode)

- 2026-05-06 03:55 — **S1 Wave 8 closure** — `/pm` writes REVIEW-final.md + 07-merge.md per story:
  - Story A `sales-agent-litellm-canonicalization`: 11/11 tickets resolved (10 audit-APPROVED + T-6b PM-ratified per R7). REVIEW-final.md verdict APPROVED. 07-merge.md ready for /pase-produccion deploy.
  - Story B `sales-agent-eval-runner-foundation`: 6/6 tickets audit-passed. REVIEW-final.md verdict APPROVED. 07-merge.md ready for /pase-produccion smoke verify.
  - Story C `sales-agent-eval-pass-k-tracking`: DEFERRED to S2 planning (not started this sprint).
  - Story D `sales-agent-eval-cost-budget-cap`: DEFERRED to S2 planning (not started this sprint).
  - sprint.md status `wrap-up` (not done since 2 stories deferred). Retrospective brief documented (wins + process improvements + risks + S2 recommendations).
  - PI-12 status remains in-progress (more sprints/stories pending: S2 + S3 + S4).
