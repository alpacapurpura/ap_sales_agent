# T-7 Result — judge_prompts.py 6-slot template (DELIVERED)

**Story:** sales-agent-voice-fidelity-grader-runtime
**Ticket:** T-7
**State transition:** draft → pushed (2026-05-09)
**Owner:** builder-agentic-opus-4.7

---

## Verdict

**state: tests-passing** — all T-7 acceptance criteria GREEN (24 unit + 27 arch fitness, 2 SKIP for T-5 gate, 1042 full arch suite GREEN). Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict).

---

## Deliverables

| Path | Status | Notes |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` | **NEW** | 6-slot prompt builder per 03-arch.md§4.1 verbatim |
| `backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py` | **NEW** | 24 unit tests (mark.no_eval — pure unit) |
| `backend/tests/architecture/test_grader_sandbox_markers_enforced.py` | **NEW** | 5 static AST tests (DQ2 layer 3) |
| `backend/tests/architecture/test_grader_round_2_no_self_reasoning.py` | **NEW** | 5 static AST tests (DQ3 anti-anchoring) |
| `backend/tests/architecture/test_grader_pii_sanitize_pre_judge.py` | **NEW** | 2 tests (TOLERANT skip until T-5 ships maj_eval.py) |
| `backend/tests/architecture/test_grader_no_mirrors_shared.py` | **NEW** | 15 tests (basename collision + 13 forbidden basename probes) |

---

## Acceptance criteria — verifier results

| ID | Description | Verifier | Status |
|---|---|---|---|
| A1 | Sandbox markers literal in Slot 5 builder + Slot 1 directive | `tests/architecture/test_grader_sandbox_markers_enforced.py` (5 tests) | ✅ PASS |
| A2 | Round 2 peer-only (no self R1 reasoning) — static AST | `tests/architecture/test_grader_round_2_no_self_reasoning.py` (5 tests) | ✅ PASS |
| A3 | Slot 3 tenant voice no `{tenant_name}` mid-block | `test_judge_prompts.py::test_slot_3_tenant_voice_no_tenant_name_interpolation` | ✅ PASS |
| A4 | cache_control ttl=1h explicit on slots 1+2+3 | `test_judge_prompts.py::test_cache_control_ttl_1h_explicit` | ✅ PASS |

---

## Validators (T-7 quality_gates)

| Validator ID | Status |
|---|---|
| `be_lint` | ✅ PASS — ruff check 0 errors |
| `be_format` | ✅ PASS — ruff format 6 files already formatted |
| `be_mypy_strict` | ✅ PASS — Success: no issues found in 6 source files |
| `sandbox_markers_static_enforced` | ✅ PASS — 5/5 arch fitness tests |
| `round_2_no_self_reasoning` | ✅ PASS — 5/5 arch fitness tests |
| `jscpd_no_duplication` | ✅ PASS — 2.06% < 5% threshold |
| `be_coverage_grader_module` | ⏸ DEFERRED — requires T-4 + T-5 + T-6 sibling files (validators.yaml line 54). T-7 alone achieves >90% on `judge_prompts.py`. Validator runs end-to-end post-T-4/T-5/T-6. |

---

## Summary metrics

- **24 unit tests passing** (T-7 GREEN)
- **27 arch fitness tests passing** (4 NEW gates: 5+5+2+15 — 2 skip for T-5 deliverable)
- **1042 architecture tests passing** in full suite (zero regressions; includes 4 NEW T-7 gates)
- **77 grader package tests** (T-2 + T-7 combined)
- **74 Story B legacy invariants intact** post-T-7
- **2.06% jscpd duplication** vs 5% threshold

---

## Decisions cement applied

D14, DQ1, DQ2, DQ3, DQ4, D-AG-7, D-AG-8, D-AG-18, D5, D7

---

## Out of scope (handed to T-4 / T-5 / T-6 / T-8)

- judge_registry (T-4) — `JUDGE_WEIGHTS` + `get_judge` not imported by T-7
- maj_eval state machine (T-5) — `grade_transcript_maj_eval` orchestration is T-5's responsibility; PII sanitize gate skips until T-5 ships
- cache (T-6) — full SHA-256 hash composition (`compute_tenant_voice_hash`, `compute_cache_key`) lives in T-6 `cache.py`
- public API surface H9 expand (T-8) — `simulator/__init__.py` re-export of `grade_transcript_maj_eval` is T-8's responsibility

---

## Last line for orchestrator

done -> docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-7-result.md
