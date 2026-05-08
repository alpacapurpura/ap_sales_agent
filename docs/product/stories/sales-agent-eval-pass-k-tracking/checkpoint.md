---
story_id: sales-agent-eval-pass-k-tracking
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: READY_PACKAGE_DELIVERED
last_artifact: 06-tickets.yaml
last_modified: 2026-05-08T11:00:00Z
next_action: "/dev-team build (BLOCKED on Stories C+D+E build done — hard blocker per spec § Build order ack). T-1 through T-4 + T-7 + T-8 can build BEFORE Stories C+D+E if synthetic test fixtures used (decouple data dependency); T-5 (aggregator integration) + T-6 (CLI) require Stories E+B real data → BLOCKED on Stories C+D+E build done. PM/dev-team decides parallelization at build trigger. All 8 tickets owner_eligibility=builder-backend Sonnet OK per R23 + Chris autonomy mandate (service-story BE-only, deterministic read-only aggregator). Escalation paths declared on T-4 bloom_scorer + T-7 pre-commit hook if iteration cap reached → Opus override puntual."
ratified_by_chris: true                  # spec v2 ratified Chris 2026-05-08T10:00Z (Q1-Q7 todas opción A recomendada)
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md                            # po_version=2, ratified Chris 2026-05-08T10:00Z
  - 03-arch.md                            # /architect orchestrator delivered 2026-05-08T11:00Z (SINGLE_SHOT_FULLSTACK BE-only)
  - 04-validators.yaml                    # schema v4, 25 validators across 3 categories
  - 05-guidelines.md                      # patterns required + forbidden + files in/out scope
  - 06-tickets.yaml                       # 8 tickets atomic, DAG dependencies, owner_eligibility Sonnet
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-eval-pass-k-tracking/
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Bloqueado hasta Story 1.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **F — Bloom-style pass^k**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 09:30Z — `/po` redactó `01-spec.md` v1 reframe Bloom 4-stage strict all-of-K (Anthropic Bloom paper mayo 2026). Stages: Understanding/Ideation/Rollout/Judgment per trial. Heterogeneous K per persona_kind (Story C cement: happy=3, nurture=1, unqualified=3, adversarial=3). Aggregator read-only consume Story B (sim trace events) + Story C (trial policy) + Story D (goldens YAML ground truth) + Story E (MajEvalScore.final_score). Schema `EvalPassKSummary` v1 con `inputs_hash` tamper detection + `golden_yaml_hash` mutation snapshot. Per-stage threshold env vars (4 × `SALES_AGENT_BLOOM_<stage>_THRESHOLD=0.7`). DDL idempotent migration `eval_pass_k_summary` table NEW. JSON report `_artifacts/eval_runs/{run_id}/pass_k_report.json` versioned. 4 scenarios obligatorios (happy/edge stage attribution/edge heterogeneous K/adversarial tamper detection). 16 decisiones cardinales D1-D16. 7 open questions Q1-Q7.
- 2026-05-08 10:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true`. Service-story → **transition `state: refining → refined`**. Phase=SPEC_RATIFIED. `next_action: /architect`.
- 2026-05-08 11:00Z — `/architect` orchestrator delivered ready package (SINGLE_SHOT_FULLSTACK mode — BE-only since AGENTIC N/A + FE N/A). 5 deliverables produced:
  - `03-arch.md` (1232 LOC) — consolidated BE-only arch with §0-§11 sections (resumen, surfaces, existing systems audit, BE arch DDL+SQLA+Pydantic+aggregator+script+hook, AGENTIC N/A, cross-cutting, decisions D-BE-1..D-BE-18, output contract Stories G/H/I, 8 architecture risks R1-R8 with mitigations, out of scope, research notes Bloom paper + AWS Strands canonical citation 2026-05-08, capability YAML + module narrative + downstream regression rule updates required)
  - `04-validators.yaml` (410 LOC) — schema v4 con 25 validators across 3 categories (non_functional 11 + functional 9 + agentic_eval 5). 4 spec scenarios fully covered (happy/edge×2/adversarial). Hardening coverage matrix H1-H10 preserved + Story F additions. Iteration policy max 3.
  - `05-guidelines.md` (345 LOC) — patterns required (Pydantic v2 ConfigDict frozen, structlog, utc_now, raw SQL IF NOT EXISTS, sha256 deterministic, async SQLA 2.0, read-only aggregator invariant, Bloom 4-stage thresholds cement, heterogeneous K Story C cement, inputs_hash composition order frozen, goldens YAML immutability defense-in-depth 3 layers, schema versioning Literal[1]=1) + patterns forbidden (cero LLM imports, no mirror grading/runner/persona loader, no Story §3 protected surfaces, no datetime.utcnow, no yaml.load sin Loader, no statistical tests, no probabilistic pass^k, no FE/Streamlit) + files in/out scope (8 NEW + 6 EDIT) + reference docs + native-first + TDD obligatorio + owner routing decisions per ticket.
  - `06-tickets.yaml` (766 LOC) — 8 tickets atomic (T-1 DDL+SQLA, T-2 Pydantic+SCHEMA_MIGRATIONS, T-3 inputs_hasher, T-4 bloom_scorer, T-5 aggregator+integration+arch fitness no-LLM-imports, T-6 CLI script+--validate-strict, T-7 pre-commit hook Section 9, T-8 arch fitness gates 3 NEW + capability YAML + module narrative + downstream regression rule). DAG dependencies declared. owner_eligibility builder-backend Sonnet (R23 + Chris autonomy mandate). Escalation paths declared on T-4 + T-7. Critical path: T-1 → T-2 → (T-3+T-4 parallel) → T-5 → T-6 → T-8; T-7 parallel-independent. Estimated 16h total.
  - `checkpoint.md` updated — state `refined → ready` + phase `READY_PACKAGE_DELIVERED` + `next_action: /dev-team build (BLOCKED on Stories C+D+E build done)`.

  Research notes cited (per §10 03-arch.md):
  - Anthropic Bloom 4-stage framework — https://www.anthropic.com/research/bloom + https://alignment.anthropic.com/2025/bloom-auto-evals/ (released 2025-12, Claude Opus 4.1 Spearman 0.86 vs human; 4 stages canonical Understanding/Ideation/Rollout/Judgment)
  - AWS Strands Evals reliability framework — https://aws.amazon.com/blogs/machine-learning/evaluating-ai-agents-for-production-a-practical-guide-to-strands-evals/ (≥10 trials + variance analysis recommended; Story F adopts strict all-of-K binary as more conservative variant)
  - sha256 + json.dumps deterministic — Python 3.12 stdlib (collision probability ~10^-77 negligible)
  - Pydantic v2 ConfigDict frozen + Literal forward-compat — docs.pydantic.dev/latest
  - SQLAlchemy 2.0 async + JSONB + composite PK — docs.sqlalchemy.org/en/20

  Build order ack (per spec § Build order):
  - **HARD BLOCKER**: Story F build BLOCKED on Stories C+D+E build done (consume Story E `MajEvalScore` rows + Story C `trial_policy_by_persona_kind` + Story D goldens YAML + Story B trace events).
  - **DECOUPLED OPTION**: T-1 through T-4 + T-7 + T-8 can build BEFORE Stories C+D+E if synthetic test fixtures used. T-5 + T-6 require real data flow → blocked on upstream builds.
  - **PARALLEL-SAFETY**: Story F is parallel-safe with Story H (per spec consumer table). Build serialization: C → D → E → (F+H parallel) → G → I.

## Próximo paso

**`state=ready` → /dev-team build trigger** (espera Stories C+D+E build done — bloqueador hard per spec). PM/dev-team decides parallelization at build trigger. All 8 tickets ready autonomous build per 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml.

## Anti-telephone-game return contract

`/architect` orchestrator (this run) returns:

```
done -> docs/product/stories/sales-agent-eval-pass-k-tracking/03-arch.md
```
