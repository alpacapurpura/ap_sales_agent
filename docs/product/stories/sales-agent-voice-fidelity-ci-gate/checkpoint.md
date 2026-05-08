---
story_id: sales-agent-voice-fidelity-ci-gate
outcome: pi-12-sales-agent-eval-foundation
state: ready
phase: READY_PACKAGE_DELIVERED
last_artifact: 06-tickets.yaml  # ready package complete (03-arch + 04-validators + 05-guidelines + 06-tickets)
last_modified: 2026-05-08T13:00:00Z
next_action: "/dev-team build (BLOCKED on Stories B+C+D+E+F+H build done — hard blocker per spec § Build order ack: Story G es LAST en sub-épica eval-foundation). Critical path: T-1 → T-2 → (T-3 parallel-safe) → T-4 → T-5 → T-6. ~13h sequential, ~11h with concurrency. All 6 tickets owner_eligibility=builder-backend Sonnet OK per R23 + Chris autonomy mandate (service-story BE-only, deterministic CI orchestrator). Escalation paths declared on T-4 (subprocess error handling) + T-5 (required check semantics + PR comment idempotent edit) if iteration cap reached → Opus override puntual. Decoupled build option: T-1+T-2+T-3+T-6 can build with synthetic fixtures BEFORE Stories C/D/E/F/H land; T-4+T-5 require real upstream artifacts. PM/dev-team decides parallelization at build trigger."
ratified_by_chris: true
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: true
blocked_reason: null
artifacts:
  - 00-story.md
  - 01-spec.md  # po_version=2, ratified Chris 2026-05-08T12:00Z (Q1-Q7 todas opción A recomendada)
  - 03-arch.md  # /architect orchestrator delivered 2026-05-08T13:00Z (consolidated BE-only — SINGLE_SHOT_FULLSTACK mode)
  - 04-validators.yaml  # 32 validators across 3 categories (non_functional 13 + functional 16 + agentic_eval 11)
  - 05-guidelines.md  # patterns required + forbidden + files in/out scope + owner routing
  - 06-tickets.yaml  # 6 tickets atomic DAG dependencies, owner_eligibility=Sonnet OK all tickets
audit_iterations: 0
legacy_exempt: true
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/*/stories/sales-agent-voice-fidelity-ci-gate/
build_blockers:
  - "Story B (DONE 2026-05-08) — provides run_simulation API + eval_simulator_trace_event table + cost-bucket invariants + H1 SCHEMA_MIGRATIONS"
  - "Story C (REFINED) — provides _TRIAL_POLICY_BY_PERSONA_KIND + 15 archetype-aware personas"
  - "Story D (REFINED) — provides 20-30 goldens YAML + 5 smoke goldens curated for PR cadence"
  - "Story E (REFINED) — provides eval_simulator_grade table + MajEvalScore rows + judge_registry config"
  - "Story F (REFINED) — provides eval_pass_k_summary table + pass_k_report.json + compute_pass_k_report.py --validate-strict"
  - "Story H (REFINED) — provides BudgetState schema + budget_summary.json + exit code 2 cascade + budget caps per cadence"
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending. Última story del Sprint 3 — cierra el loop del Objetivo 2 del PI-12.
- 2026-05-06 — Migrado a paradigma v4: state=refining (legacy_exempt). Pendiente /po para spec ratification.
- 2026-05-06 17:11Z — Reframe synthetic-first (outcome `pi-12-sales-agent-eval-foundation.md`). Rol en sub-épica eval-foundation-* = **G — CI gate dynamic threshold (daily→weekly→monthly)**. Spec ratification awaits A (tenant-seed) + B (simulator-homologation) refined.
- 2026-05-08 11:30Z — `/po` redactó `01-spec.md` v1 reframe dynamic threshold per cadence (outcome v2 mandate). 3 cadences: PR (5 smoke goldens × K=1 × 0.65 × $30/$80 × block × <5min) / nightly (full × heterogeneous K × 0.70 × $150/$500 × block × <30min) / monthly (full + adversarial Story I × 0.75 × $200/$700 × warning + Chris semestral × <60min). Consume Story F `pass_k_report.json` + Story H `budget_summary.json` cascade. GitHub Actions workflow `voice-fidelity-gate.yml` + path filters + cron + required check branch protection. PR comment rich attribution con root cause Bloom stage + reproduce cmd + calibration ref. 5-layer bypass defense (skip ci → required check + workflow file changes review + goldens hash + threshold defaults arch fitness + audit trail). Schema `GateVerdict` v1 SCHEMA_MIGRATIONS forward-compat. DDL idempotent `eval_gate_verdict` table NEW. 4 scenarios obligatorios. 15 decisiones D1-D15. 7 open questions Q1-Q7.
- 2026-05-08 12:00Z — Chris ratificó Q1-Q7 (todas opción A recomendada). `/po` bump v2 inline. `ratified_by_chris: true`. Service-story → **transition `state: refining → refined`**. Phase=SPEC_RATIFIED. `next_action: /architect`.
- 2026-05-08 13:00Z — `/architect` orchestrator delivered ready package (SINGLE_SHOT_FULLSTACK mode — BE-only since AGENTIC N/A + FE N/A). 5 deliverables produced:
  - **`03-arch.md`** (~1650 lines) — 11 sections — §0 resumen + §1 surfaces (BE-only — AGENTIC/FE N/A) + §2 existing systems audit (NO NEW LAYER cross-module greps verbatim — feature genuinely NEW; consume Stories B/C/D/E/F/H artifacts read-only via subprocess + JSON read + DB select; pattern reuse Story F inputs_hasher justified; orthogonal `llm-eval-gate.yml` paradigm preserved) + §3 BE arch (DDL migration 129 idempotent + SQLA 2.0 model R5 schema-mirror + Pydantic v2 types `GateVerdict`/`FailingGoldenDetail`/`CadenceConfig`/`GateValidationError` + `cadence_config.py` declarative 3 cadences cement + `inputs_hasher.py` sha256 deterministic composite cache key + `orchestrator.py` 13-step pipeline subprocess Stories B+E+F+H + cache lookup + UPSERT + `comment_generator.py` 4 verdict templates Spanish neutro + `scripts/run_eval_gate.py` CLI argparse + exit codes 0/1/2 + `.github/workflows/voice-fidelity-gate.yml` GitHub Actions workflow + path filters + cron schedule + required check + secrets + idempotent PR comment via actions/github-script@v7 + 1 NEW arch fitness gate test_gate_threshold_defaults_protected.py + extend Story F gate test_aggregator_no_llm_calls.py to scan ci_gate/ paths) + §4 AGENTIC N/A (read-only orchestrator) + §5 cross-cutting consolidadas (tenant isolation + PII consume only via Story F passthrough + voice + currency Decimal + schema versioning forward-compat + observability writes + determinism + Spanish neutro + native-first + anti-duplication §0 + parallel safety) + §6 D-BE-1..D-BE-12 (12 decisiones arch + reference 15 spec decisions D1-D15 = 27 total) + §7 output contract para Story I (extends `monthly` cadence row additively) + §8 8 architecture risks R1-R8 with mitigations + §9 out of scope anti-creep (15 items) + §10 research notes (GitHub Actions required check + skip-ci semantics WebSearch 2026-05-08; cron schedule production patterns 2026; sha256 + Pydantic v2 reuse Story F precedent; knowledge cutoff disclosure post-Jan 2026) + §11 capability YAML + module narrative branch protection setup checklist + auditor-downstream-regression rule updates required (post-merge by /pm)
  - **`04-validators.yaml`** (~530 lines) — schema v4 con 32 validators across 3 categories (non_functional 13: lint+format+mypy+arch_fitness+coverage+jscpd+migration_idempotency+legacy_invariants+gate_no_llm_imports+gate_threshold_defaults+workflow_yaml_lint+workflow_paths_canonical+workflow_cron_canonical+read_only_db_invariant) + functional 16 (4 scenarios × happy 4 + edge 7 + adversarial 6) + agentic_eval 11 (cost_bucket_invariant + inputs_hash_deterministic + cache_short_circuit + cache_invalidation + idempotency + 3_cadences_no_drift + verdict_json_schema_valid + pii_sanitization_consume_only + spanish_neutro_pr_comment + subprocess_invocation_stories_consume_only). Scenario coverage 4/4 (happy/edge×2/adversarial). Hardening coverage matrix H1+H6+H7+H9+H10 + D9_TAMPER_DETECTION 5-layer + D6_CACHE_PRECISION + D8_EXIT_CODE_SEMANTICS. Iteration policy max 3.
  - **`05-guidelines.md`** (~390 lines) — patterns required (Pydantic v2 ConfigDict frozen, structlog, utc_now, Decimal monetary, async SQLA 2.0 + UPSERT pg_insert.on_conflict_do_update, raw SQL IF NOT EXISTS, sha256 deterministic, subprocess timeout-bounded list-args, actions/github-script@v7 idempotent edit, read-only orchestrator invariant cement, cadence config declarative 3 cadences cement, inputs_hash composition order frozen, cache key composite invalidation precision, GitHub Actions workflow contract D11+D14, PR comment 4 templates Spanish neutro, PII consume only Story F passthrough, schema versioning Literal forward-compat, TDD orden 6 layers) + patterns forbidden (cero LLM imports, no mirror grading/runner/persona-loader/pass^K/budget-guard/inputs_hasher composition Story F, no Story §3 protected surfaces, no datetime.utcnow, no yaml.load sin Loader, no subprocess shell=True, no statistical tests, no FE/Streamlit/Slack/email, no LLM-summarized comment, no auto-retry, no per-PR custom thresholds) + files in/out scope (12 NEW + 5 EDIT) + reference docs Stories B/C/D/E/F/H + native-first + TDD obligatorio order 6 layers + decisiones owner routing 6-row matrix (Sonnet OK all tickets, escalation paths declared on T-4 + T-5).
  - **`06-tickets.yaml`** (~590 lines) — 6 tickets atomic (T-1 DDL+SQLA, T-2 Pydantic+cadence config+SCHEMA_MIGRATIONS anchor, T-3 inputs_hasher, T-4 orchestrator+comment_generator+integration, T-5 CLI+GitHub Actions workflow+bypass defense tests, T-6 arch fitness gate+Story F gate extend+capability YAML+module narrative+downstream regression rule). DAG dependencies declared. owner_eligibility builder-backend Sonnet (R23 + Chris autonomy mandate). Escalation paths declared on T-4 (subprocess error handling) + T-5 (required check semantics + PR comment idempotent edit) if iteration cap reached → Opus override puntual. Critical path: T-1 → T-2 → (T-3 parallel-safe) → T-4 → T-5 → T-6. Estimated 13h total sequential, 11h with concurrency. Decoupled build option: T-1+T-2+T-3+T-6 can build with synthetic fixtures BEFORE Stories C/D/E/F/H land; T-4+T-5 require real upstream artifacts.
  - **`checkpoint.md`** updated — state `refined → ready` + phase `READY_PACKAGE_DELIVERED` + `next_action: /dev-team build (BLOCKED on Stories B+C+D+E+F+H build done — hard blocker)`.

  Research notes cited (per §10 03-arch.md, accessed 2026-05-08):
  - GitHub Actions required check + skip-ci semantics — `https://github.com/orgs/community/discussions/13836` + `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule` + `https://blog.pantsbuild.org/skipping-github-actions-jobs-without-breaking-branch-protection/` (D11 cement validated — `[skip ci]` does NOT bypass required checks per GitHub Actions semantics)
  - GitHub Actions workflow path filters + cron schedule production patterns 2026 — `https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions` + `https://tech-insider.org/github-actions-tutorial-cicd-12-steps-2026/` (D14 cement validated — POSIX cron syntax + IANA timezone optional + 5min minimum interval; combining paths + branches narrows scope)
  - sha256 + json.dumps deterministic — Python 3.12 stdlib (Story F precedent reused as pattern reference; collision probability ~10^-77 negligible)
  - Pydantic v2 ConfigDict frozen + Literal forward-compat — `docs.pydantic.dev/latest` (Story F precedent)
  - Knowledge cutoff disclosure: Topic researched live on 2026-05-08 via WebSearch — Opus 4.7 cutoff is Jan 2026 (5 months prior). GitHub Actions v7 syntax + branch protection semantics stable since 2024; no breaking changes Jan-May 2026 per searches.

  Build order ack (per spec § Build order):
  - **HARD BLOCKER**: Story G build BLOCKED on Stories B+C+D+E+F+H build done. Story G es **LAST** en sub-épica eval-foundation (cierra Objetivo 2 del PI-12).
  - **DECOUPLED OPTION**: T-1+T-2+T-3+T-6 can build BEFORE Stories C/D/E/F/H if synthetic test fixtures used. T-4+T-5 require real artifacts → blocked on upstream builds.
  - **PARALLEL-SAFETY**: Story G is parallel-safe with Story I (Story I extends Story G `monthly` cadence row additively post-merge). Build serialization: B(done) → C → D → E → (F+H parallel) → G → I.

## Próximo paso

**`state=ready` → /dev-team build trigger** (espera Stories B+C+D+E+F+H build done — bloqueador hard per spec). PM/dev-team decides parallelization at build trigger. All 6 tickets ready autonomous build per 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml.

## Anti-telephone-game return contract

`/architect` orchestrator (this run) returns:

```
done -> docs/product/stories/sales-agent-voice-fidelity-ci-gate/06-tickets.yaml
```
