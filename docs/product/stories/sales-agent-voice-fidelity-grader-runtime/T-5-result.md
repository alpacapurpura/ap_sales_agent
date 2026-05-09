# T-5 Result — maj_eval.py MAJ-EVAL state machine

**Ticket**: T-5 (Opus 4.7 — ★ critical complexity)
**State**: pushed (build phase done, tests-passing)
**Owner**: builder-agentic
**Completed**: 2026-05-08T22:35Z

## Deliverables shipped

### NEW `backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` (768 lines)

State machine per 03-arch.md §4.3 verbatim pseudocode. Public API entry
`grade_transcript_maj_eval(request, *, session, obs_context) -> list[MajEvalScore]`.

Cement constants (Final):
- `VARIANCE_R1_THRESHOLD: Final[float] = 0.15` (D3)
- `VARIANCE_R2_TARGET: Final[float] = 0.10` (D4)
- `JUDGE_CONCURRENCY: Final[int] = 20` (D17)

Workflow per (turn, rubric):
1. PII sanitize defense-in-depth — `sanitize_payload({"content": turn.content})` per turn (D10)
2. Compute 5-field cache key (D8) — transcript_hash + tenant_voice_hash + judge_set_hash via T-6 helpers
3. Cache lookup — graceful degradation Rule 2 (DB unavailable → re-grade)
4. Round 1 — `asyncio.gather` 3 judges in parallel under `Semaphore(20)` (D17 DoS protection)
5. Variance check — `max - min` simple range (D3, NOT statistical)
6. Round 2 conditional — variance > 0.15 → debate trigger; peer-only reasoning (DQ3 anti-anchoring)
7. R2 partial fallback (DQ6) — judge fails R2 → use R1 score for that judge + flag `r2_partial=True`
8. Convergence — R2 variance < 0.10 → final = R2; ≥ 0.10 → unconverged + R1 fallback (D4)
9. Suspicious flag (DQ8) — all 3 judges score=1.0 + ANY injection_attempt → suspicious=True
10. <2 valid judges defense — log error + unconverged fallback
11. Persist + cache — best-effort try/except (Rule 2). NEVER raises out.

Auxiliary helpers (private):
- `_invoke_judge` — Semaphore-guarded dispatch via judge_registry.get_judge() + build_judge_prompt
- `_weighted_average` — Σ(score × weight) / Σ(weight), excludes None scores, renormalizes
- `_variance` — max-min over non-None scores, returns 0.0 for empty
- `_build_score` — composes MajEvalScore from R1 + optional R2 opinions
- `_persist_grade` — INSERT eval_simulator_grade ON CONFLICT DO NOTHING (idempotent)
- `_get_rubric_version` — lru_cached YAML frontmatter parser
- `_read_rubric_md` — lru_cached file reader for slot 2 rubric_md_verbatim

### NEW `backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_unit.py` (768 lines, 24 tests)

All marked `pytest.mark.no_eval` — pure unit tests, no real LLM/DB. Uses `AsyncMock` for judge
adapters + cache helpers + rubric MD reader, `MagicMock` for AsyncSession + observability context.

Tests landed:

| Test | Coverage target |
|---|---|
| `test_variance_max_minus_min_pure` | D3 — simple range NOT statistical |
| `test_variance_excludes_none_scores` | None judges excluded from variance |
| `test_variance_empty_returns_zero` | Defense — empty input |
| `test_weighted_average_excludes_none_scores` | Renormalize on judge fail |
| `test_aggregation_weights_sonnet_04_gpt4o_04_kimi_02` | D2 weights cement |
| `test_weighted_average_zero_weight_returns_zero` | Defense — all judges fail |
| `test_round_1_parallel_3_judges_returns_3_opinions` | Round 1 happy path |
| `test_variance_below_15_triggers_no_round_2` | Convergence at R1 |
| `test_variance_above_15_triggers_round_2` | D3 trigger |
| `test_round_2_uses_peer_only_prompts` | DQ3 anti-anchoring (verify call args) |
| `test_round_2_convergence_below_10_returns_r2_avg` | D4 — converged R2 |
| `test_round_2_unconverged_above_10_marks_unconverged_true` | D4 — unconverged fallback to R1 |
| `test_r2_partial_one_judge_timeout_marks_partial` | DQ6 — R2 partial fallback |
| `test_suspicious_flag_when_score_1_with_injection_attempt` | DQ8 — adversarial trap |
| `test_cache_hit_short_circuits_judge_calls` | Cache HIT skips judges + persist |
| `test_cache_miss_computes_then_persists` | Cache MISS triggers all writes |
| `test_cache_bypass_policy_skips_lookup` | cache_policy="bypass" |
| `test_cost_aggregation_sums_per_judge` | cost_usd_total = Σ judges |
| `test_judge_concurrency_constant_is_20` | D17 cement |
| `test_variance_r1_threshold_is_0_15` | D3 cement |
| `test_variance_r2_target_is_0_10` | D4 cement |
| `test_orchestration_per_rubric_per_turn` | 4 turns × 3 rubrics = 12 rows |
| `test_lt_2_valid_judges_unconverged_score_null` | <2 valid judges defense |
| `test_pii_sanitize_called_pre_judge` | D10 — sanitize before judge call |

## Validators GREEN

| Validator | Result |
|---|---|
| `be_lint` (ruff check) | PASS — All checks passed |
| `be_format` (ruff format --check) | PASS — 2 files already formatted |
| `be_mypy_strict` (mypy) | PASS — Success: no issues found |
| `test_maj_eval_unit.py` | PASS — 24/24 tests |
| Full grader suite | PASS — 101/101 tests |
| `test_grader_pii_sanitize_pre_judge.py` (arch) | PASS — both static AST checks GREEN (PII import + invocation) |
| `test_grader_round_2_no_self_reasoning.py` (arch) | PASS — DQ3 cement preserved |
| `test_grader_sandbox_markers_enforced.py` (arch) | PASS — DQ2 layer 2 preserved |
| `test_grader_no_mirrors_shared.py` (arch) | PASS — anti-duplication clean |
| Story B legacy arch fitness (5 gates) | PASS — H7/H9/H10 cement intact |
| Story C personas arch fitness | PASS — untouched |
| **Full arch suite** (`tests/architecture/`) | **PASS — 1044/1045 (1 env-gated skip)** |

## Acceptance criteria mapping

| Acceptance | Status |
|---|---|
| **A1** Variance + weighted aggregate logic correct (be_lint/be_format/be_mypy_strict) | ✅ PASS — 6 unit tests cover variance + weighted avg edge cases |
| **A2** PII sanitize pre-judge call (defense-in-depth even synthetic) | ✅ PASS — both arch test_grader_pii_sanitize_pre_judge.py probes (import + invocation) |
| **A3** Round 2 peer-only — DQ3 (static AST) | ✅ PASS — test_round_2_uses_peer_only_prompts verifies via call_args; arch gate test_grader_round_2_no_self_reasoning.py PASS (already passing pre T-5; preserved) |
| **A4** Unconverged fallback semantics (R2 variance ≥ 0.10 → R1 fallback + flag) | ✅ PASS — test_round_2_unconverged_above_10_marks_unconverged_true verifies final_score = R1_weighted_avg, unconverged=True |
| **A5** R2 partial fallback semantics (judge fail R2 → R1 score for that judge) | ✅ PASS — test_r2_partial_one_judge_timeout_marks_partial verifies r2_partial=True flag |

## Cement decisions enforced

| Decision | Mechanism in T-5 |
|---|---|
| D2 — weights 0.4/0.4/0.2 | Imported from `JUDGE_WEIGHTS`; test_aggregation_weights_sonnet_04_gpt4o_04_kimi_02 |
| D3 — variance threshold 0.15 max-min | `VARIANCE_R1_THRESHOLD: Final[float] = 0.15`; `_variance()` returns max-min |
| D4 — unconverged fallback to R1 | `_build_score()` final_score logic when unconverged → r1_weighted |
| D10 — PII sanitize defense-in-depth | sanitize_payload({"content": turn.content}) per turn pre-judge |
| D17/D-AG-9 — Semaphore(20) | `JUDGE_CONCURRENCY: Final[int] = 20`; asyncio.Semaphore(JUDGE_CONCURRENCY) |
| D-AG-3 — asyncio.gather Round 1 | 3 judges via asyncio.gather with weight from JUDGE_WEIGHTS.items() |
| D-AG-4 — Round 2 conditional | `if r1_variance <= VARIANCE_R1_THRESHOLD: return early` |
| D-AG-5 — Peer-only DQ3 | `[(op.judge_id, op.score, op.reasoning) for op in r1_opinions if op.judge_id != jid]` |
| D-AG-6 — Judge timeout fallback DQ6 | r2_partial fallback uses R1 op when r2_op.score is None |
| D-AG-10 — DB write best-effort Rule 2 | try/except wrap on _persist_grade + cache_persist; structlog warn fallback |
| D-AG-12 — State machine cement | _grade_one_turn_rubric() implements 8-step workflow per 03-arch §4.3 |

## Out of scope (per ticket; preserved)

- ❌ Cache impl (T-6 — already done)
- ❌ Judge prompts builder (T-7 — already done)
- ❌ Integration scenarios (T-9)
- ❌ judge_registry (T-4 — already done)
- ❌ H9 expand simulator/__init__.py (T-8)
- ❌ Docs reconciliation (T-10)

## Cross-cutting invariants preserved

- ✅ Cost-bucket H7: `_persist_grade` writes ONLY to `eval_simulator_grade` (NOT copilot_*/sales_agent_*)
- ✅ Voice cement (sales-agent-expert §3): `personality_profile.system_instruction` consumed READ-ONLY via `compute_tenant_voice_hash` (T-6) and Slot 3 (T-7)
- ✅ Anti-duplication §0: REUSE shared `sanitize_payload` + LiteLLM Proxy via judge_registry (T-4) + cost_recorder via Story B `EvalSimulatorCallbackHandler`
- ✅ R5 schema-mirror exception: NO module/{copilot,sales_agent}/{domain,application,api}/ touched
- ✅ Spanish neutro: code + structlog English (judge prompts English per DQ4); voseo magic comment used in docstring citing rubric IDs

## Decisions for downstream tickets (T-9 integration)

The grader public API contract is locked:
```python
async def grade_transcript_maj_eval(
    request: RubricGradeRequest,
    *,
    session: AsyncSession,
    obs_context: EvalSimulatorObservabilityContext,
) -> list[MajEvalScore]
```

T-9 callback wiring:
- `request.simulation_id` MUST be `str(simulation_id)` (Story B simulation UUID)
- `obs_context.eval_metadata` carries Story B+C base metadata; T-4 adapter extends with Story E 5 NEW keys (grader/rubric_id/rubric_version/judge_id/round_n/cache_hit)
- Each judge's `cost_usd` populates via `cost_recorder.pop_cost(litellm_call_id)` Story B canonical bridge (already wired by `EvalSimulatorCallbackHandler`)

T-8 H9 expand:
- Public name to add: `grade_transcript_maj_eval` (alphabetic insertion at index 5 between SimulationState and run_simulation)

## Files changed

```
backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py     (NEW, 768 lines)
backend/tests/agentic_evals/sales_agent/grader/test_maj_eval_unit.py     (NEW, 768 lines)
docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-5-impl-log.md (NEW)
docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-5-result.md   (NEW)
docs/product/stories/sales-agent-voice-fidelity-grader-runtime/06-tickets.yaml (state→pushed)
```

Net diff: +1536 lines, -2 lines (06-tickets.yaml state transition entry append).

## Verdict

`tests-passing` — orchestrator → gate-runner → auditor-{backend,agentic} pipeline next.
