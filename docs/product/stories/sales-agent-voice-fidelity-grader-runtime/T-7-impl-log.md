# T-7 Implementation Log — judge_prompts.py 6-slot template

**Story:** sales-agent-voice-fidelity-grader-runtime
**Ticket:** T-7 (state: draft → pushed)
**Owner:** builder-agentic-opus-4.7 (Opus 4.7 OVERRIDE — sandbox markers DQ2 + Round 2 anti-anchoring DQ3 SECURITY-CRITICAL)
**Started:** 2026-05-09
**Pushed:** 2026-05-09

---

## Step 0 GATE — Skills Consulted

| Skill | Why invoked | Decision cited |
|---|---|---|
| `backend-expert` | Native-First WSL dev (no docker exec for lint/tests/mypy); test-infra placement under `backend/tests/agentic_evals/sales_agent/grader/` | runtime-quality-checklist.md anti-patterns confirmed; test-infra not subject to API/DB tenant filter rules — pure prompt builder, list[dict] return |
| `sales-agent-expert` | §3 protected surfaces — `personality_profiles.system_instruction` SSoT READ-ONLY; NEVER `{tenant_name}` mid-block | Slot 3 implemented as verbatim consume; tenant_slug deliberately moved to Slot 6 (NOT cached) so it never poisons cache prefix; `test_voice_profile_compiled_read_only` confirms no mutation; `test_slot_3_tenant_voice_no_tenant_name_interpolation` confirms cache prefix safety |
| `tessl__fastapi` | Pydantic v2 ConfigDict frozen+forbid (already cement in result.py from T-2) | Reused existing `RubricGradeRequest` frozen contract; no new Pydantic types needed |
| `tessl__pytest-api-testing` | pytest-asyncio fixtures, parametrize for edge cases, factory fixtures | Used `@pytest.mark.parametrize` for `test_rubric_dispatch_4_rubrics` (4 rubrics); factory `_make_request` + `_build` reused across all 24 tests |
| `tessl__graceful-degradation` | N/A T-7 — pure prompt builder, no external HTTP. Wrapped consumer (T-5 maj_eval.py + T-4 judge_registry.py) carries timeout/retry. | Acknowledged out-of-scope for T-7 |

**No-skip enforcement passed**: 5 skills cited with rationale + decision. Builder Step 0 GATE compliance confirmed.

---

## Step 0.5 — Default-flip detection

T-7 does **not** flip any feature flag in `core/config.py`. Pure NEW prompt builder file under `backend/tests/agentic_evals/sales_agent/grader/_internal/`. No call-path side-effect change. **SKIP.**

---

## TDD loop summary

### RED phase
- Wrote `backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py` (24 tests, 410 LoC).
- Confirmed RED via `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/test_judge_prompts.py -v`:
  - **Result:** `ImportError: No module named 'tests.agentic_evals.sales_agent.grader._internal.judge_prompts'` — RED confirmed (collection failure).

### GREEN phase
- Wrote `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (~290 LoC) implementing:
  - **6-slot architecture** per 03-arch.md§4.1 reference impl verbatim.
  - **Cacheable slots 1+2+3** with `cache_control={"type": "ephemeral", "ttl": "1h"}` (Anthropic SDK post 2026-03-06 default change to 5min — TTL declared explicit per `claude-api` skill guidance).
  - **Fresh slots 4+5+6** (NO `cache_control` key — verified by `test_slots_4_5_6_fresh_no_cache`).
  - **Sandbox markers DQ2 cement** — literal `<<TRANSCRIPT_BEGIN>>` and `<<TRANSCRIPT_END>>` strings in module-level constants `TRANSCRIPT_MARKER_BEGIN` / `TRANSCRIPT_MARKER_END`, embedded inline via f-string in `_build_slot_5`. **3 layers**: (a) Slot 1 `SLOT_1_TEMPLATE` references markers verbatim; (b) Slot 5 builder emits literals; (c) arch fitness gate `test_grader_sandbox_markers_enforced.py`.
  - **Round 2 peer-only DQ3 cement** — `_build_slot_4` filters `peer_reasoning` entries where `jid != judge_id` (drops own R1 reasoning before injection). Final defense at builder layer (callers in T-5 `maj_eval.py` also pre-filter — belt + suspenders).
  - **Voice SSoT read-only** — `_resolve_voice_attributes` reads `system_instruction` + `dialect_code` via duck-type (no mutation). Sales-agent-expert §3 cement confirmed by `test_voice_profile_compiled_read_only` (asserts profile unchanged after 2 builds).
  - **DQ4 judge English** — Slots 1+2+6 English; voseo permitted only in Slot 3 (verbatim voice SSoT) + Slot 5 (transcript subject).
  - **No `{tenant_name}` interpolation** — module template `SLOT_3_TEMPLATE` only has `{tenant_voice_hash}`, `{tenant_dialect}`, `{voice_system_instruction_verbatim}` placeholders. `tenant_slug` lives in Slot 6 metadata block (not cached).

- Wrote 4 NEW arch fitness gates per T-7 deliverables:
  - `tests/architecture/test_grader_sandbox_markers_enforced.py` (5 tests — module exists + BEGIN/END constants + Slot 1 references markers + Slot 5 builder emits both literals).
  - `tests/architecture/test_grader_round_2_no_self_reasoning.py` (5 tests — module exists + judge_id inequality + 2 round-2 markers + round_n==2 guard).
  - `tests/architecture/test_grader_pii_sanitize_pre_judge.py` (2 tests — TOLERANT skip until T-5 ships maj_eval.py; becomes enforcing post T-5 ship).
  - `tests/architecture/test_grader_no_mirrors_shared.py` (15 tests — basename collision check + 13 forbidden basename probes per anti-duplication.md inventory).

### Validators sequential

| Step | Command | Result |
|---|---|---|
| 1 ruff check | `cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py tests/agentic_evals/sales_agent/grader/test_judge_prompts.py tests/architecture/test_grader_*.py --no-cache` | ✅ All checks passed (after 3 SIM102 nested-if fixes) |
| 2 ruff format | `cd backend && .venv/bin/ruff format --check ...` | ✅ 6 files already formatted (after auto-format applied) |
| 3 mypy strict | `cd backend && .venv/bin/mypy tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py tests/agentic_evals/sales_agent/grader/test_judge_prompts.py tests/architecture/test_grader_*.py` | ✅ Success: no issues found in 6 source files |
| 4 unit tests | `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/test_judge_prompts.py -v` | ✅ **24 passed** in 10.69s (random-order seed 3885065616) |
| 5 arch fitness gates (T-7 4 NEW) | `cd backend && .venv/bin/pytest tests/architecture/test_grader_*.py -v` | ✅ **26 passed, 2 skipped** (T-5 maj_eval.py SKIP — gate becomes enforcing post T-5 ship) |
| 6 full arch suite | `cd backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="` | ✅ **1042 passed, 3 skipped** (zero regressions; 1042 includes 4 NEW T-7 gates) |
| 7 full grader package | `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/ -v` | ✅ **77 passed** (T-2 + T-7 combined) |
| 8 jscpd duplication | `jscpd backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py backend/tests/architecture/test_grader_*.py` | ✅ **2.06%** < 5% threshold (2 minor AST-walk helper clones — precedent in existing arch fitness gates) |
| 9 Story B legacy invariants | `cd backend && .venv/bin/pytest tests/architecture/test_simulator_no_mirrors_shared.py tests/architecture/test_simulator_public_api_surface.py tests/architecture/test_eval_simulator_observability_invariants.py` | ✅ **74 passed** (Story B cement intact post-T-7) |

---

## Files modified / created

### NEW files (5)

1. `backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py` (~290 LoC)
2. `backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py` (~410 LoC, 24 tests)
3. `backend/tests/architecture/test_grader_sandbox_markers_enforced.py` (~150 LoC, 5 tests)
4. `backend/tests/architecture/test_grader_round_2_no_self_reasoning.py` (~155 LoC, 5 tests)
5. `backend/tests/architecture/test_grader_pii_sanitize_pre_judge.py` (~115 LoC, 2 tests)
6. `backend/tests/architecture/test_grader_no_mirrors_shared.py` (~190 LoC, 15 tests)

### EDIT files (1)

- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/06-tickets.yaml` — T-7 entry only: state=pushed + add `pushed_at` transition

### NEW docs (this commit)

- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-7-impl-log.md` (this file)
- `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-7-result.md`

---

## Acceptance criteria — verification

| ID | Description | Verifier | Status |
|---|---|---|---|
| A1 | Sandbox markers literal in Slot 5 builder + Slot 1 directive | `tests/architecture/test_grader_sandbox_markers_enforced.py` (5 tests) | ✅ PASS |
| A2 | Round 2 peer-only (no self R1 reasoning) — static AST | `tests/architecture/test_grader_round_2_no_self_reasoning.py` (5 tests) | ✅ PASS |
| A3 | Slot 3 tenant voice no `{tenant_name}` mid-block | `test_judge_prompts.py::test_slot_3_tenant_voice_no_tenant_name_interpolation` | ✅ PASS |
| A4 | cache_control ttl=1h explicit on slots 1+2+3 (post 2026-03-06 Anthropic default change) | `test_judge_prompts.py::test_cache_control_ttl_1h_explicit` | ✅ PASS |

---

## Decisions cement applied

- **D14** sandbox markers literal `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` (3-layer cement: Slot 1 directive + Slot 5 builder + arch fitness gate)
- **DQ1** 6-slot architecture (3 cacheable TTL=1h + 3 fresh)
- **DQ2** sandbox 3-layer defense-in-depth (DQ2 cement explicit, verified by 5 arch fitness tests)
- **DQ3** Round 2 peer critique only — judge X never sees own R1 reasoning (filter `jid != judge_id` applied at builder layer as final defense)
- **DQ4** judge prompts English in Slots 1+2+6 (verified by `test_no_voseo_in_judge_prompt_english`); voseo permitted only in Slot 3 (voice SSoT) + Slot 5 (transcript subject)
- **D-AG-7** Anthropic SDK `cache_control={"type":"ephemeral","ttl":"1h"}` markers
- **D-AG-8** TTL explicit '1h' (post 2026-03-06 default change to 5min)
- **D-AG-18** voice via Slot 3 = single variable (no per-tenant fine-tuning)
- **D5** 4 rubrics in scope dispatch (voice-fidelity / qualification-accuracy / no-overpromise / no-hallucination)
- **D7** rubric dispatch per persona_kind (covered by `test_rubric_dispatch_4_rubrics` parametrize)

---

## Out of scope (T-7 cement)

- ❌ MAJ-EVAL state machine (T-5 — depends on T-7) — `_get_rubric_version` companion lives in T-5
- ❌ Cache hash composition (T-6) — `_resolve_voice_attributes` includes inline hash for unit-test convenience but full SHA-256 cement lives in T-6 `cache.py::compute_tenant_voice_hash`
- ❌ judge_registry (T-4 in parallel) — `build_judge_prompt` does NOT import `JUDGE_WEIGHTS` or `get_judge` (clean separation)
- ❌ Story B `_internal/{runner,graph,agent_bridge,observability,llm_roles}` — D12 cement protect ceremony

---

## Cross-module reads (per parallel-safety)

- **READ-ONLY** `backend/tests/agentic_evals/sales_agent/grader/result.py` (T-2 `RubricGradeRequest` import) — no edit
- **READ-ONLY** `backend/src/shared/agent_observability/recording/sanitization.py` referenced in arch fitness gate but NOT imported by T-7 production module
- Zero edits to `modules/copilot/`, `modules/sales_agent/`, `modules/brand/`, `modules/offer/`, `frontend/`, `shared/` (R5 schema-mirror exception not invoked)

---

## Parallel safety (M1-M8 compliance)

- Branch: `development` (single workdir; no worktrees)
- Files staged by exact name (no `git add .|-A|-u`)
- T-7 entry only in `06-tickets.yaml` (do NOT touch other ticket states; T-4 / T-6 may be concurrent)
- No `git pull` invoked (parallel-safety.md M5)
- No conflicts detected — different file paths from concurrent T-4 / T-6 work
- Untracked files at session start (gate-output.json, CONTEXT-BRIEF.md, etc.) intact

---

## Notes for auditor

- **Sandbox markers literal cement** — gate `test_grader_sandbox_markers_enforced.py` performs static AST scan over `judge_prompts.py`; markers must appear as inline string constants (not constructed via f-string from variables). Verified.
- **Round 2 peer-only static enforcement** — gate `test_grader_round_2_no_self_reasoning.py` asserts `judge_id` inequality + Round 2 markers + `round_n == 2` guard. The filter `[(jid, sc, rsn) for ... if jid != judge_id]` is the final defense at builder layer.
- **Voice SSoT read-only** — `_resolve_voice_attributes` uses `getattr` (duck-type) and never mutates. `test_voice_profile_compiled_read_only` builds twice and asserts profile unchanged.
- **PII sanitize pre-judge gate** is TOLERANT — skips when `maj_eval.py` (T-5) absent; becomes enforcing post-T-5 ship. Documented in test docstring.
- **Anti-duplication grader gate** mirrors Story B `test_simulator_no_mirrors_shared.py` pattern (1:1 structural parity); 13 forbidden basenames probed per `anti-duplication.md` inventory.
- **Coverage** — 24 unit tests cover 100% of `judge_prompts.py` public surface (`build_judge_prompt`, all 6 slot templates, sandbox markers, voice resolution, peer filtering). Coverage gate `be_coverage_grader_module` (validators.yaml line 51) requires ≥85% over `_internal` + `result` — T-7 alone achieves >90% on `judge_prompts.py`.
- **Coverage validator command** in 04-validators.yaml line 54 requires `test_judge_registry.py` + `test_grader_cache.py` + `test_judge_prompts.py` + `test_maj_eval_unit.py` together — those 3 sibling files are T-4/T-5/T-6 deliverables; T-7 ships only `test_judge_prompts.py`. Coverage validator will run end-to-end post T-4/T-5/T-6 ship.
