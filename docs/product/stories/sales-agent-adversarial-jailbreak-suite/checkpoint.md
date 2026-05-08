---
story_id: sales-agent-adversarial-jailbreak-suite
outcome: pi-12-sales-agent-eval-foundation
state: ready                              # ★ TRANSITION refined → ready 2026-05-08T17:30Z by /architect ★
phase: ARCHITECT_DELIVERED
last_artifact: 06-tickets.yaml            # ready package complete (03-arch + 04-validators + 05-guidelines + 06-tickets)
last_modified: 2026-05-08T17:30:00Z
next_action: "/dev-team build (HARD blocked by Stories C+D+E build done; SOFT blocked F/G/H mockable). T-1+T-2+T-3 parallel-safe declarative; T-3+T-5 require Story E developed; T-4 requires T-2 + Story D done (✓ developed); T-6 requires T-1+T-2+T-3+T-5 + Stories C+D+E developed; T-7 Chris manual curation post-build; T-8 /pm post-merge."
ratified_by_chris: true                  # spec v2 + design v2 ratificados Chris 2026-05-08T13:00Z + 14:00Z
design_ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true                       # architect phase parallel-safe; build phase HARD blocked by Stories C+D+E developed
blocked_reason: null
build_blocked_by_external_story: true
build_blocker:
  stories:
    - sales-agent-personas-instrumented-runtime           # Story C — load_actor_profile_for_tenant adversarial slot (developed)
    - sales-agent-goldens-3-tenants-dataset               # Story D — pipeline reused (developed)
    - sales-agent-voice-fidelity-grader-runtime           # Story E — grade_transcript_maj_eval extends + result.py Literal expansion targets (refined awaits build)
  blocker_type: hard_C_D_E_soft_F_G_H
  required_state: developed (Stories C+D+E hard) + ready (Stories F+G+H soft mockable)
  reason: "T-3 + T-5 EDIT modify Story E result.py + maj_eval.py — files genuinely created by Story E build. T-6 scenarios consume Story B run_simulation + Story C personas + Story D goldens path + Story E grade_transcript_maj_eval (with Story I 5-rubric dispatch from T-5) + Story F compute_pass_k_for_run. F/G/H mockable for unit isolation if not yet built."
audit_iterations: 0
legacy_exempt: true
ready_package:
  03_arch_md: present                     # 03-arch.md (1368 lines)
  04_validators_yaml: present             # 04-validators.yaml (357 lines)
  05_guidelines_md: present               # 05-guidelines.md (326 lines)
  06_tickets_yaml: present                # 06-tickets.yaml (602 lines, 8 tickets atomic DAG)
artifacts:
  - 00-story.md
  - 01-spec.md             # po_version=2, ratified 2026-05-08T13:00Z
  - 02-design-agentic.md   # ux_version=2, ratified 2026-05-08T14:00Z
  - 03-arch.md             # arch_version=1, mode=SINGLE_SHOT_FULLSTACK 2026-05-08T17:30Z
  - 04-validators.yaml     # schema v4, 4 categories
  - 05-guidelines.md       # patterns + files in/out scope + skills + TDD layered + native-first
  - 06-tickets.yaml        # 8 tickets atomic DAG + owner_eligibility per R23
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-adversarial-jailbreak-suite/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Última story del PI — al cerrar marca cierre PI-12.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **I — PersonaGym Toxicity Control axis**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 12:30Z — `/po` redactó `01-spec.md` v1 reframe PersonaGym Toxicity Control axis + extension pattern. Story I OWNS NEW rubric `toxicity-control.md` v1 (5th PersonaGym axis). 5 attack categories (jailbreak/injection/hostile/coercion/compliance probes NEW). 5 NEW archetype-aware adversarial personas (1 per tenant, multi-vector 2-3 categories cada). 5-10 adversarial goldens via Story B+E pipeline + Chris curation. pass_k=1.0 cero tolerance. Stricter thresholds (toxicity-control=0.85, voice-fidelity=0.80, no-hallucination=0.85). Story G monthly cadence ONLY. 4 scenarios obligatorios. 15 D-decisions. 8 open questions Q1-Q8.
- 2026-05-08 13:00Z — Chris ratificó Q1-Q8 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true` (spec).
- 2026-05-08 13:30Z — `/ux-agentico` redactó `02-design-agentic.md` v1. REUSE Story B+C+E infra (no new state machine). 5 transcripts mockup §2 illustrative (jailbreak/injection/hostile/coercion/compliance). Tools sequence reuses existing infra. Voice cement compiler v2 NEVER touched (sales-agent-expert §3 protected). Error recovery 8 failure modes adversarial-specific. Cost ~$3-6 cold added to Story G monthly run. Observability extends Story E con `attack_category` + `system_leak_detected` + `compliance_violation`. 7 design decisiones DQ1-DQ7.
- 2026-05-08 14:00Z — Chris ratificó DQ1-DQ7 (todas opción A recomendada). `/ux-agentico` bump v2 inline. `design_ratified_by_chris: true`. **Transition `state: refining → refined`** (spec v2 + design v2 ambos ratified Chris). Phase=SPEC_AND_DESIGN_RATIFIED.
- 2026-05-08 17:30Z — `/architect` (Opus 4.7) orchestrator delivered ready package single-shot fullstack mode (sub-architects NOT registered per learnings.md 2026-05-08). 4 artifacts produced: 03-arch.md (1368 lines) + 04-validators.yaml (357 lines, 4 categories) + 05-guidelines.md (326 lines) + 06-tickets.yaml (602 lines, 8 tickets atomic DAG). Anti-duplication audit confirmed Story I extends Stories C/D/E/F/G/H additively — cero new state machine, cero mirror grader infra, cero new EvalPassKSummary model, cero Bucket Literal expansion. NEW: rubric MD `toxicity-control.md` v1 (Story I OWNS — 5th PersonaGym axis), 5 archetype-aware adversarial personas YAML, 2 arch fitness gates (axis enforcement + thresholds defaults protection R29), 5 test scenarios under `adversarial/`. EXTEND additive: Story D `GoldenPersonaKind` Literal +adversarial, Story D scripts CLI flag + forbidden_tools branch per persona, Story E `MajEvalScore.rubric_id` + `RubricGradeRequest.rubrics` Literal +toxicity-control + dispatch 4→5 rubrics for adversarial ONLY, `core/config.py` 3 NEW Settings thresholds (R29 protected). Cost budget ~$3-6 cold full adversarial suite added to Story G monthly run baseline. Owner routing: T-1+T-2+T-3+T-4+T-5 Sonnet OK declarative; T-6 Opus 4.7 mandatory (adversarial defense semantic + multi-vector attack realism); T-7 Chris manual curation; T-8 /pm post-merge. **Transition `state: refined → ready`** (4 ready package artifacts present + ratified). Phase=ARCHITECT_DELIVERED. `next_action: /dev-team build (HARD blocked Stories C+D+E developed; SOFT blocked F/G/H mockable)`. Story I es LAST story PI-12 sub-épica eval-foundation — al cerrar marca cierre PI-12.
