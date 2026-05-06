<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# T-4 Review — Multi-layer assertion library (sales-agent-eval-runner-foundation)

> Auditor: `auditor-agentic` (Opus 4.7) — invariants validated against
> canonical docs as of 2026-05-06.
> Iter: 1
> Verdict: **APPROVED** (with 1 documented WARN on architectural-spec drift)
> Generated: 2026-05-06T00:00:00Z

## Inputs

- `CONTEXT-BRIEF.md`: used (validator PASS, faithfulness=clean, 16/16 sections, 2 MEDIUM advisories non-blocking)
- `gate-output.json`: used (10 gates PASS, exit 0, 1200s native sweep)
- Skills invoked:
  - `copilot-expert` (auto-loaded — anti-duplication §0 reference + composition pattern reference)
  - `sales-agent-expert` (auto-loaded — §0 anti-duplication cardinal + §3 protected surfaces map + Spanish neutro exception scope)
  - `tessl__langgraph` (auto-loaded — N/A confirmed: T-4 does not modify graph code, reads spy outputs only)
  - `tessl__graceful-degradation` (auto-loaded — Rule 1 + Rule 6 evaluated for langdetect lazy import path)

R24 brief acceptance gate: PASS (`Validator pass: ...validation.md (PASS — 2 MEDIUM ...)` header line populated; faithfulness flag `clean` non-blocking).

## Gate status (from `gate-output.json`)

| Gate | Status | Errors |
|---|---|---|
| ruff_lint | PASS | 0 |
| ruff_format | PASS | 0 |
| pytest_architecture | PASS | 0 (823/823) |
| pytest_coverage (full BE suite) | PASS | 0 (9041 PASS / 34 SKIP / 16 deselected) |
| acceptance_a1_assertions_api_complete | PASS | 0 |
| acceptance_a2_assert_output_named_failure | PASS | 0 |
| acceptance_a3_assert_voice_fidelity_placeholder | PASS | 0 |
| acceptance_a4_detect_language_safe | PASS | 0 |
| anti_duplication_grep | PASS | 0 mirrors |
| langdetect_lazy_import (top-level grep + AST walk) | PASS | 0 offenders |

Independent verification by auditor (re-ran the 4 acceptance + arch AST tests natively): `5 passed, 38 deselected, 1 warning in 11.73s` — all PASS.

## Downstream regression scope (R3 + R21 mandatory step)

Diff inspected: `git diff --name-only 3ff20d6b 674967c4`:

| Path | In SSoT table `.claude/rules/auditor-downstream-regression.md`? | Downstream targets |
|---|---|---|
| `backend/tests/agentic_evals/sales_agent/runner/assertions.py` | NO (test-only path) | NA |
| `backend/tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` | NO (test-only path) | NA |
| `docs/projects/active/...T-4-impl-log.md` | NO (docs) | NA |

**Verdict:** ZERO `shared/` or `modules/X/` src/ paths touched → no downstream regression scope triggered. Builder's claim consistent. Full BE suite (`-m "not integration"` 9041 tests) already covers any indirect ripple.

## 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | NA | T-4 does not touch state machine, graph code, or reducers |
| 2 | Tool registration & contracts | PASS | `assert_tool_calls` accepts `required` + `forbidden` lists from caller (B4 binding); zero inline tool-name hardcode in `assertions.py` |
| 3 | Prompt cache architecture | NA | T-4 makes zero LLM calls; cache prefix invariants enforced by upstream production code (slot 5 `BRAND_VOICE` per `sales-agent-expert` skill) |
| 4 | deepagents subagent isolation | NA | T-4 reads spy outputs only; no `task` tool / SubAgentMiddleware in scope |
| 5 | Observability (`copilot_trace_event` + cost recording) | PASS | `assert_cost_recorded` is read-only consumer of `sales_agent_llm_call`; `_build_cost_query` filters BOTH `tenant_id == tenant_id` AND `turn_id == run_id` (`assertions.py:420-423`); zero new LLM call wrappers |
| 6 | Eval goldens (sales_agent specifically) | PASS (foundation scope) | T-4 builds the assertion infrastructure consumed by future goldens (Story 7 voice grader explicit `NotImplementedError` placeholder per B7 binding); smoke goldens themselves are T-5 scope, NOT T-4 |
| 7 | RAG / Qdrant hygiene | NA | T-4 does not touch Qdrant or `KnowledgeService`; no vector search in scope |
| 8 | LLM provider routing | NA | T-4 makes zero LLM calls; provider routing handled upstream |
| 9 | Cost optimization | NA | T-4 is dev-internal eval harness; no per-turn cost target applies |
| 10 | Channel format & brand voice | PASS | Spanish neutro LATAM in user-facing error messages: "se esperó", "se observó", "no aparece", "Trayectoria incompleta", "Idioma del output no coincide", "Suma de costos excede presupuesto del smoke", "Latencia observada excede el límite del smoke" — zero voseo (`-ás`/`-és`/`-ís`) detected via regex sweep |
| 11 | DDD compliance (agentic) | WARN | T-4 file location correct (`tests/agentic_evals/sales_agent/runner/assertions.py`); zero src/ touch; **drift documented below**: 4 assertion signatures in builder code differ from `03-arch-be.md` § "Assertion library (T4 detail)" prescriptive signatures (lines 329-365) — see Findings WARN |
| 12 | Tests / TDD | PASS | RED→GREEN evidence in `T-4-impl-log.md` § "TDD evidence": 18 tests RED (ModuleNotFoundError) → 18 GREEN. AST-walk arch test `test_assertions_module_no_top_level_langdetect_import` provides ratchet enforcement of B5 lazy import. 14 edge case tests cover: includes/exact mode mismatch, forbidden tool present, language unknown skip, cost = 0 row, model mismatch, sum > max budget, latency aggregate / per-tool / no-signal pass-through |
| 13 | Mirror detection (cross-module duplication) | PASS | Step 0 GATE in impl-log shows: 0 mirrors of `detect_lang`/`sanitize_payload`/`BaseAgentCallbackHandler` in `tests/agentic_evals/sales_agent/runner/`. `TrajectorySpy` (T-3, audit-passed) is composition pattern (added to `RunnableConfig.callbacks` list), NOT subclass of `SalesAgentCallbackHandler`. No new shared abstraction candidate detected (eval harness intentionally isolated — anti-duplication.md inventory satisfied) |
| 14 | Default-flip side-effect coverage | NA | T-4 does not touch `core/config.py` defaults or any flag in inventory (`USE_OUTBOX_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`); confirmed via diff `--name-only` |
| 15 | Decisions honored cite (R6) | PASS | Commit body `674967c4` § "Decisions honored" cites B4, B5, B7 verbatim with concrete impl descriptions: B4 "registry-sourced lists; no inline hardcode" (caller supplies via `STAGE_TOOL_SCOPE` constant per arch-agentic § "Tool registry mapping"), B5 "lazy import + AST-walk arch test enforces" (`test_assertions_module_no_top_level_langdetect_import`), B7 "`assert_voice_fidelity` placeholder raising `NotImplementedError`" — all 3 binding decisions traceable to file:line. Note: ticket frontmatter does NOT have explicit `decisions_applicable` field, but the architect docs (03-arch-agentic.md + 03-arch-be.md) bind B4/B5/B7 to T-4 deliverables — the auditor accepts the cite as honored |

## Findings (file:line)

### FAIL

(none)

### WARN

- **[Cat 11 — DDD compliance / architectural-spec drift]** `backend/tests/agentic_evals/sales_agent/runner/assertions.py:77` (LayerAssertionError base class) — Builder implements `class LayerAssertionError(Exception)`. `03-arch-be.md:329` prescribes `class LayerAssertionError(AssertionError)`. Functional difference is subtle (pytest treats both equivalently in `pytest.raises`), BUT `AssertionError` is the conventional base for assertion-style failures and aligns with spec line 91: "El error NO es un genérico `AssertionError` sin contexto" — the spec phrasing suggests the layered errors SHOULD subclass `AssertionError` (ergonomics around pytest-assert auto-introspection). → Recommend follow-up: switch base to `AssertionError` in a future cleanup commit if T-5 smoke encounters introspection drift. NOT blocking — A1 acceptance verifier asserts only `issubclass(LayerAssertionError, Exception)` which passes both ways.
- **[Cat 11 — DDD compliance / architectural-spec drift]** `backend/tests/agentic_evals/sales_agent/runner/assertions.py:221, 279, 338, 426, 595` (4 assertion signatures) — Builder's signatures functionally diverge from `03-arch-be.md` § "Assertion library (T4 detail)":
  - `assert_trajectory(spy, expected_specialists, *, mode="includes"|"exact")` vs arch-be `assert_trajectory(spy, *, first_specialist, forbidden_specialists)` — T-5 smoke needs to compose 2 calls (or inline assertion) to express "qualifier first AND closer not present" (spec scenario 1 line 39). Builder's API is more general but does NOT express the negative condition without composition.
  - `assert_output(text, *, language, must_mention)` vs arch-be `assert_output(text, *, min_length, spanish_marker_min_count, must_mention_one_of)` — Builder drops `min_length` precondition AND drops `spanish_marker_min_count >= 3` regex word-boundary check (arch-be line 322 documented this as "defense-in-depth: langdetect catches genuine regression to English, marker count catches edge-case English with code-switching"). Builder also changes `must_mention_one_of` (logical OR) → `must_mention` (logical AND). Ticket spec line 272 explicitly mandates "Spanish marker count" as part of `assert_output`.
  - `assert_cost_recorded(run_id, *, db_session, tenant_id, model_pattern, max_cost_usd)` vs arch-be `assert_cost_recorded(db, *, tenant_id, turn_id, min_cost_usd, model_pattern)` — Builder uses `max_cost_usd` (upper bound) where arch-be specifies `min_cost_usd` (lower bound). Builder's actual logic does check `cost > 0` (line 506) AND total ≤ max (line 534) — functionally captures both regression-up and regression-to-zero, which is stricter than arch-be. Naming drift only.
  - `assert_latency(spy, *, max_ms)` vs arch-be `assert_latency(start_ts, end_ts, *, max_ms)` — Builder reads spy `duration_ms` (3 fallbacks); arch-be expected `time.perf_counter()` start/end pair. Builder's choice avoids modifying T-3 spy (audit-passed) and accepts pass-through when no signal exists. Functionally equivalent for the smoke when T-3 spy is augmented later (arch-agentic § "Riesgos" line 374 documents that current spy may not capture timing).

  → Recommend: T-5 smoke builder MUST compose `assert_trajectory(spy, ["qualifier"])` + inline `assert "closer" not in spy.specialist_history` to cover the spec scenario 1 negative trajectory. T-5 smoke MUST decide whether to add Spanish marker count as a separate inline check (per spec line 42, ticket line 272) or accept that builder's `assert_output` substitutes langdetect detection + must_mention as sufficient defense (since must_mention can be passed as `["que", "de", "la"]` to approximate marker count via substring presence — though that does not match the ≥3 frequency contract). The CONTEXT-BRIEF `must_mention` description was authoritative for the builder; downstream T-5 may add a thin wrapper `assert_spanish_marker_count(text, min_count=3)` if the smoke gold reveals false-negative drift.

  This drift was NOT documented in `T-4-impl-log.md` § "Decisions honored" — the impl-log mentions the builder's signatures as if they match the arch, when in fact they intentionally diverge. Future implementations should add an explicit "Architectural drift acknowledged" section when builder's signatures functionally diverge from prescriptive arch-be code blocks.

### info

- **[Cat 5 — Observability]** `assertions.py:421-422` — `_build_cost_query` filters both `tenant_id` AND `turn_id` → tenant isolation rule honored verbatim. Cross-tenant leakage is impossible by construction.
- **[Cat 6 — Eval goldens placeholder]** `assertions.py:630-668` — `assert_voice_fidelity` placeholder explicitly raises `NotImplementedError` with message naming "Story 7" and "future" → accionable failure if a future smoke accidentally invokes it. B7 binding satisfied verbatim.
- **[Cat 12 — Tests]** `test_eval_runner_fixtures.py:1242-1275` — AST walk arch test enforces B5 binding with structural ratchet: walks top-level `ast.Import` and `ast.ImportFrom` nodes, fails accionable if any future commit introduces top-level `import langdetect` / `from langdetect import …`. This is a ratchet-grade enforcement layer — much stronger than a one-time grep.
- **[Cat 13 — Anti-duplication]** Step 0 GATE in `T-4-impl-log.md:38-58` documents the cross-codebase greps performed: 0 matches for any candidate mirror. Inventory in `.claude/rules/anti-duplication.md` § "Inventario shared abstractions" cross-checked — eval harness has no candidate for shared lift (intentional test-only isolation).

## Cross-scope flags

(none — all paths within `backend/tests/agentic_evals/sales_agent/` and `docs/projects/`)

## Research notes (date-aware — 2026-05-06)

- Source: `.claude/rules/anti-duplication.md` § "Inventario shared abstractions" (read 2026-05-06) — the inventory lists `BaseAgentCallbackHandler`, `sanitize_payload`, `FXResolver.default()`, `PricingResolver`, etc.; T-4 does NOT introduce new candidates.
- Source: `.claude/rules/auditor-downstream-regression.md` SSoT table (read 2026-05-06) — confirmed test-only path changes do not trigger downstream regression scope.
- Knowledge cutoff disclosure: Opus 4.7 cutoff January 2026; `tessl__langgraph` skill anchors verified live against canonical docs not required for T-4 (no new graph topology, no new state schema, no LLM call). Skill anchors held.
- WebSearch / WebFetch: NOT performed for T-4. No novel agentic pattern introduced (lazy import + try/except is standard Python; AST walk is standard `ast` module). Brief § 13 documented the same: zero WebFetch executed by context-builder for T-4 scope.

## Recommendations for builder fix-loop

T-4 is APPROVED. No mandatory fixes blocking merge.

Optional follow-up (NOT blocking T-4 close, can be deferred):

1. (Cat 11 WARN — base class) Future commit may switch `class LayerAssertionError(Exception)` → `class LayerAssertionError(AssertionError)` for ergonomic alignment with pytest convention + spec line 91 phrasing. Single-line change. No test rewrite needed (existing `issubclass(LayerAssertionError, Exception)` continues to pass).
2. (Cat 11 WARN — signature drift) When T-5 builder writes the smoke goldens, document the wrapping pattern explicitly: how T-5 composes builder's API to express the negative trajectory + Spanish marker count contracts from spec scenario 1. If gaps surface, add a thin wrapper (e.g., `assert_spanish_marker_count(text, min_count=3)`) in `runner/assertions.py` rather than renaming existing API (back-compat preserves the 18 T-4 tests without rewrites).

## Drift detection (CONTRACT vs code)

**YES (WARN level — non-blocking).**

CONTRACT documents drift:

| Spec/Arch line | Builder code | Drift type |
|---|---|---|
| `03-arch-be.md:329` `LayerAssertionError(AssertionError)` | `assertions.py:77` `LayerAssertionError(Exception)` | base class (functionally equivalent for `pytest.raises`; spec line 91 phrasing favors AssertionError) |
| `03-arch-be.md:349` `assert_trajectory(spy, *, first_specialist, forbidden_specialists)` | `assertions.py:221` `assert_trajectory(spy, expected_specialists, *, mode)` | API shape (more general; T-5 must compose for negative trajectory) |
| `03-arch-be.md:353` `assert_output(text, *, min_length, spanish_marker_min_count, must_mention_one_of)` | `assertions.py:338` `assert_output(text, *, language, must_mention)` | DROPS `min_length` precondition; DROPS `spanish_marker_min_count`; OR→AND on mention list; ADDS `language` param. Ticket line 272 mandates Spanish marker count. |
| `03-arch-be.md:355` `assert_cost_recorded(db, *, tenant_id, turn_id, min_cost_usd, model_pattern)` | `assertions.py:426` `assert_cost_recorded(run_id, *, db_session, tenant_id, model_pattern, max_cost_usd)` | naming (`min_cost_usd` → `max_cost_usd`); positional vs keyword on identifier; functionally stricter |
| `03-arch-be.md:357` `assert_latency(start_ts, end_ts, *, max_ms)` | `assertions.py:595` `assert_latency(spy, *, max_ms)` | input source (perf_counter pair → spy duration_ms duck-typed); avoids T-3 spy modification |

The CONTEXT-BRIEF (validator-approved) summarized T-4 in line with the builder's actual signatures — i.e., the brief was already the authoritative source for the builder, and faithfulness flag was `clean`. The architect docs prescriptive code blocks were illustrative scaffolding that the architect approved without re-binding when the brief simplified the signatures. This is a **brief-vs-arch consistency gap** — not a builder error.

Drift IS in scope for `<!-- @pm: DRIFT detected -->` flag. The drift is documented for `/pm` awareness so a future cleanup or T-5 wrapper can close the gap. **NOT blocking T-4 merge** because:

1. All ticket-level acceptance verifiers (A1-A4) PASS
2. CONTEXT-BRIEF was authoritative + validator-approved
3. Builder's choices are functionally equivalent or stricter than arch-be prescriptions
4. Drift is forward-compatible — T-5 can compose / wrap without back-incompatible changes

`<!-- @pm: DRIFT detected (Cat 11 WARN — non-blocking, documented for T-5 awareness). T-4 verdict APPROVED. Builder & arch-be code-block prescriptions diverge in 5 places; CONTEXT-BRIEF aligned with builder. Recommend `/pm` confirm whether T-5 should add thin wrappers for `assert_spanish_marker_count` + negative-trajectory helper, OR accept composition pattern. No code change required for T-4 close. -->
