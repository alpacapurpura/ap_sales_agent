# Checkpoint Template — Resume Protocol (v4 — Punto 4 2026-05-06)

> Cada story tiene SU `checkpoint.md`. Cualquier sesión nueva lee este archivo PRIMERO para saber dónde retomar.
> El skill que cierra cada handoff (`/pm`, `/po`, `/po-ux`, `/architect`, `/dev-team`, `/auditor`) actualiza `last_artifact` + `last_modified` manualmente al escribir el frontmatter. NO existe hook automático (el viejo `post-edit-checkpoint.sh` fue removido 2026-05-06 — lógica rota).

---
story_id: STORY_ID                                # match folder name
outcome: OUTCOME_SLUG                             # docs/product/outcomes/{slug}.md
state: refining                                   # 10 estados v4 — ver tabla abajo
phase: PO_SPEC                                    # ver tabla phase abajo (informational)
last_artifact: 01-spec.md                         # último archivo escrito
last_modified: 2026-05-06T15:23:00Z
next_action: "Chris ratifica spec → invocar /architect"
ratified_by_chris: false                          # true cuando spec + diseño ratificados
spawned_at: 2026-05-06T14:00:00Z
spawned_by: /pm
parallel_safe: true                               # ¿otra sesión puede tocar artefactos de esta story sin conflict?
blocked_reason: null
audit_iterations: 0                               # cap 2 → escala automática
hotfix_metadata:                                  # opcional, solo hot-fix tickets (R26)
  repro_verified: false
  repro_command: null
  diagnosis_validates_handoff: null
---

## Estados v4 (10 macro)

| # | Estado | Significado | Owner | WIP cap |
|---|---|---|---|---|
| 1 | `idea` | Spark + research opcional. Puede nunca implementarse | Chris + `/pm` | ∞ |
| 2 | `refining` | Decompose stories + drafts spec/UX/agentic. Loop iterativo | `/pm` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | Spec + UX/diseño ratificados Chris. Listo para architects | `/pm` cierra | ≤ 5 |
| 4 | `ready` | Paquete autocontenido completo (4 archivos canónicos) | `/architect` | ≤ 5 |
| 5 | `developing` | Autonomous build activo iterando vs validators | opencode/Sonnet/Opus (R23) | ≤ 3 |
| 6 | `developed` | Validators GREEN. Build cerrado, awaiting QA | `/dev-team` | ≤ 2 |
| 7 | `reviewing` | Auditor QA en curso (Opus C1-C3 + Sonnet tests) | `/auditor` | ≤ 2 |
| 8 | `done` | Auditor APPROVED + merge + capability promovida + docs | `/pm` | rolling 90d |
| 9 | `parked` | De-prioritized, NO abandonado | Chris | ∞ |
| 10 | `dropped` | Won't do (terminal) | Chris | ∞ |

## Phases (story-level — informational, no enforcement)

| Phase | Owner | Inputs | Output | Next |
|---|---|---|---|---|
| `PM_DRAFT` | /pm | opportunity / idea | `00-story.md` (opcional) | `PO_SPEC` |
| `PO_SPEC` | /po o /po-ux | `00-story.md` + spec template | `01-spec.md` + story YAML | `UX_UI` o `UX_AGENTIC` o `ARCHITECT` (según type) |
| `UX_UI` | /po-ux fusión | `01-spec.md` (ui-story) | wireframes inline en spec.md | `ARCHITECT` |
| `UX_AGENTIC` | /ux-agentico | `01-spec.md` (agentic-story) | `02-design-agentic.md` | `ARCHITECT` |
| `SPEC_RATIFIED` | Chris ratifica | spec + diseño | transition state=refining→refined | `ARCH` |
| `ARCH_DONE` | /architect | `01` + `02` | spawns architect-{be,fe,agentic} → `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` | state=refined→ready |
| `BUILD_T{n}` | /dev-team | `06-tickets.yaml` | `T-{n}-impl-log.md` + `T-{n}-result.md` + push commit | next ticket O `BUILD_DONE` |
| `BUILD_DONE` | /dev-team | all validators GREEN | state=developing→developed | (Chris triggers /auditor) |
| `AUDIT_T{n}` | /auditor | `T-{n}-result.md` + tests | `T-{n}-review.md` (APPROVED \| CHANGES_REQUESTED) | next ticket O `MERGE` |
| `MERGE` | /pm | all tickets audit-passed + `CHECKPOINTS.md` | `07-merge.md` + apply diff to `product/` | `DONE` (state=reviewing→done) |
| `DONE` | (closed) | — | — | — |
| `BLOCKED` | any | — | escala Chris | resolver bloqueo |

## Bitácora

> Append-only. Cada agent que toca un artefacto logea aquí con timestamp.

- 2026-05-06 14:00 — /pm creó folder y checkpoint.md (state=refining)
- 2026-05-06 14:30 — /po redactó `01-spec.md`. Chris ratificó.
- 2026-05-06 15:23 — Spec ratificada → state=refined. En espera de /architect.

## Notas

- Si `parallel_safe=false`, otra sesión NO debe tocar artefactos hasta `next_action` complete.
- Si `blocked_reason != null`, ningún agent procede hasta Chris/PM resuelva.
- `audit_iterations >= 2` → escala automática a Chris (no más self-fix loops).
- Para hot-fix tickets (R26): `hotfix_metadata.repro_verified` MUST ser `true` antes spawn builder.
