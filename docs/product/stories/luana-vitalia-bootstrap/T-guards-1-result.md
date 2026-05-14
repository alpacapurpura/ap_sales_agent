# T-guards-1 — Result

**Ticket:** Guardrail medical_safety_no_diagnosis (input + output layers)
**State:** tests-passing (developing → developed, awaiting auditor verdict per R30)
**R23:** production_code=true → Opus 4.7 EXCLUSIVE
**Date:** 2026-05-14
**Builder:** Claude Opus 4.7 (1M context)

---

## TL;DR

47/47 new tests + 99/99 wider guardrails suite GREEN on iter 1. NEW vertical-medical safety guard `medical_safety_no_diagnosis` lands in `vitalia/backend/src/modules/vitalia/agentic/guardrails/` covering BOTH input (pre-LLM call, pipeline step 3) and output (post-LLM call, pipeline step 6) layers per spec § 17.1 + § 17.5. Single module exposes two entry points (`medical_safety_no_diagnosis_input_check` + `medical_safety_no_diagnosis_output_check`) sharing audit-log emission infrastructure.

Algorithm: cheap regex first (cost guard — skip Haiku call when regex already fires), Haiku classifier fallback on regex miss. Best-effort observability invariant respected — `audit_log` failures never break safety verdict. Graceful degradation policy on classifier outage = pass-through (false-positive cost > false-negative cost; downstream output guard + adversarial pass^5 ≥0.95 cement at V-AE-11 catches paraphrased claims at end-to-end eval level).

Anti-duplication audit Step 0 GATE returned NEW. Cross-codebase grep evidence cited verbatim in impl-log. Slot 4 sandbox markers + reminder text REFERENCED via spec citation only — T-prompts-1 j2 file NOT modified by this ticket. ZERO regression introduced (downstream extensions test 18/18 PASS).

## Deliverables

### Production code (luana-platform main)

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py` (~430 lines including verbose docstrings + spec citations + anti-duplication audit notes):
  - `FALLBACK_RESPONSE_TEMPLATE` cement (Spanish neutro tuteo, spec § 17.1 verbatim).
  - `_INPUT_DIAGNOSIS_RE` + `_OUTPUT_DIAGNOSIS_RE` cement regex catalog (append-only safety ratchet). OUTPUT subject list extended (`diabetes`, `cuadro`) beyond cement strict per § 17.1 — append-only, true-positives rise — with rationale comment in-line.
  - `_LLMClassifierLike` Protocol (NARROWER than sibling extractor `_LiteLLMServiceLike` — single-method `aclassify_bool` for bool classification only).
  - `_AuditLogLike` Protocol (structural typing, mirrors sibling guardrails + extractors surface).
  - `InputGuardrailResult` + `OutputGuardrailResult` (frozen kw-only dataclasses).
  - `fires_input_regex()` + `fires_output_regex()` + `render_fallback_response()` (pure helpers — unit testable, no I/O).
  - `_consult_classifier_input()` + `_consult_classifier_output()` (timeout + try/except wrappers per `tessl__graceful-degradation` rule 2).
  - `medical_safety_no_diagnosis_input_check()` + `medical_safety_no_diagnosis_output_check()` (side-effecting entry points composing regex → classifier → audit_log → result).
  - `_build_output_block_result()` (centralised result composition — regex hit and classifier hit produce structurally identical results).
  - `_emit_audit_log()` (best-effort try/except + `sanitize_payload` per anti-duplication.md SSoT row).

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py` — extended to re-export 8 NEW T-guards-1 symbols alongside existing T-guards-3 surface (20 symbols total).

### Tests (luana-platform main)

- `vitalia/backend/tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py` — 47 tests. Coverage:
  - `FALLBACK_RESPONSE_TEMPLATE` spec phrase verbatim + `render_fallback_response` substitution invariant (no unresolved placeholders).
  - INPUT regex parametrize: 9 diagnosis claims (covers 6 verbs × 7 conditions sample) + 7 benign clinical queries.
  - INPUT end-to-end:
    - Regex match → fire WITHOUT classifier call (cost guard invariant).
    - Regex miss → classifier consulted; `True` → fires.
    - Both clear → no fire, no audit entry.
  - OUTPUT regex parametrize: 6 diagnosis phrases + 5 benign responses.
  - OUTPUT end-to-end:
    - Regex match + `retry_attempted=False` → block + `regenerate_with_no_diagnosis_instruction` action (no fallback string yet).
    - Regex match + `retry_attempted=True` → block + `use_fallback_response` action with cement string composed via `render_fallback_response`.
    - Classifier fallback fires when regex misses paraphrased phrasing.
    - Benign response → no block, no audit.
  - Best-effort observability:
    - INPUT + OUTPUT decisions hold even when `audit_log` raises (R23 production-critical invariant).
    - `audit_log=None` works (graceful when not provisioned).
    - Classifier failure on regex MISS → graceful pass-through (no fire, no false-positive blocking on outage).
  - Tenant isolation invariant (cardinal):
    - INPUT + OUTPUT audit_log entries carry the supplied `tenant_id` (separate tests).
  - PII non-leakage:
    - Audit payload contains lengths + flags + classifier confidence ONLY — NEVER `user_msg` / `llm_response` verbatim text (separate tests for INPUT + OUTPUT).
  - Frozen dataclass cement:
    - Mutating either result type raises (caller cannot tamper with verdict).

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py` updated re-exports list.

### Docs (AISALESHT)

- `docs/product/stories/luana-vitalia-bootstrap/T-guards-1-impl-log.md` — Skills consulted (5 — `copilot-expert` + `sales-agent-expert` + `tessl__langgraph` + `tessl__graceful-degradation` + `tessl__pytest-api-testing`); Step 0 GATE grep evidence verbatim; cross-module audit; inside-out implementation order; observability writes plan.
- `docs/product/stories/luana-vitalia-bootstrap/T-guards-1-result.md` (this file).
- `docs/product/stories/luana-vitalia-bootstrap/checkpoint.md` — append T-guards-1 closure entry.

## Validators GREEN

- **V-AE-8** (`tests/agentic_evals/guardrails/`) — 99/99 PASS in 0.12s. Includes 47 new T-guards-1 + 25 T-guards-3 disclaimer + 27 T-guards-3 prompt injection.
- **Lint** — `ruff check` 0 errors on the 2 new files + 1 modified `__init__.py`.
- **Format** — `ruff format --check` clean (post-format adjustment for `FALLBACK_RESPONSE_TEMPLATE` collapsed to single line + line-length cleanup in test fixture).
- **Downstream regression (R3)** — `tests/unit/test_extensions_register_all.py` 18/18 PASS (guardrail folder is referenced by extensions registry per EP-13 placeholder; package import unchanged at runtime since `__init__.py` only added re-exports, no signature changes).

## Acceptance criteria

- **A1 (test_input_fires)** — GREEN. `tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py::test_input_check_fires_on_regex_match_without_calling_classifier` + `test_input_check_fires_on_classifier_when_regex_misses` cover regex + classifier fallback paths exhaustively. Plus 9 parametrized regex direct-fire cases + 7 benign passes.
- **A2 (test_output_blocks)** — GREEN. `test_output_check_blocks_on_regex_match_emits_regenerate_hint` + `test_output_check_returns_fallback_after_retry_exhausted` + `test_output_check_classifier_fallback_when_regex_misses` cover regex hit + retry semantics + classifier fallback. Plus 6 parametrized regex direct-fire cases + 5 benign passes.
- **A3 (Adversarial diagnosis persona pass^5 ≥0.95)** — DEFERRED to T-eval-1 W17 cross-ticket. Per ticket spec verbatim "DEFER (grader scenario file is T-eval-1 W17 cross-ticket, document gap in result.md)". Documented gap below in § Cross-ticket gap.

### Cross-ticket gap (A3 deferred to T-eval-1 W17)

The adversarial pass^5 ≥0.95 production-critical safety bar (V-AE-11) is exercised at end-to-end eval level by `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py` per ticket spec. That test does NOT exist yet — it is created in T-eval-1 (W17). When T-eval-1 lands, the adversarial diagnosis personas (`patient-adversarial-diagnosis-mx.yaml`) will exercise this guard end-to-end and the pass^5 cement will validate the input + output layers in concert under simulator pressure.

This unit test suite (T-guards-1 in scope) cements:
- Decision invariants (regex + classifier paths).
- Cost invariants (regex hit short-circuits classifier).
- Best-effort observability invariants (audit_log failures NEVER break decision).
- Graceful degradation invariants (classifier outage NEVER breaks decision).
- Tenant isolation invariants (every audit_log carries tenant_id).
- PII non-leakage invariants (payload contains lengths only, NEVER text verbatim).
- Frozen result type invariants (caller cannot mutate verdict).

This is the right scope split per `.claude/rules/tdd-mandatory.md` + ticket boundary discipline — adversarial cement is end-to-end concern owned by T-eval-1, not unit-level concern owned by T-guards-1.

## Skills consulted (R30 evidence)

- `copilot-expert` — best-effort observability (try/except + structlog warning), tenant_id propagation invariant, no-skip rule trazas first. Decision: audit_log emission via `try/except` swallowing exception with structlog warning, NEVER breaks turn. Sanitize_payload from shared before persist.
- `sales-agent-expert` — anti-duplication §0 cardinal: input/output guardrails are vertical-medical surface (NEW, no shared base in luana-core). Slot 4 BRAND_VOICE separation respected: regex + classifier ops are deterministic + cheap, no LLM voice impact. Tenant isolation on every audit_log write.
- `tessl__langgraph` — N/A (guardrail is NOT a LangGraph node — it's middleware in input/output pipeline order 3+6 per § 17.5). Pure async functions composable in pre/post LLM call hooks. No state graph involved.
- `tessl__graceful-degradation` — Rules 1+2: Haiku classifier LLM call wrapped in `asyncio.wait_for`-equivalent timeout (delegated to LiteLLM service `timeout_sec` arg per existing extractor pattern) + try/except. On timeout/error: graceful degradation — pass-through on regex miss (false-positive cost > false-negative cost for INPUT layer when adversarial cement V-AE-11 is end-to-end backstop).
- `tessl__pytest-api-testing` — function-scoped fixtures default; in-memory `_FakeAuditLog` + `_FakeLLMClassifier` per test. parametrize for input/output regex coverage. Async tests via `pytest.mark.asyncio` (existing T-guards-3 fixture pattern).

## Step 0 anti-duplication GATE evidence

```bash
$ grep -rln "medical_safety_no_diagnosis\|MedicalSafetyNoDiagnosis" /home/chris/luana-platform/ 2>/dev/null
/home/chris/luana-platform/vitalia/config/brand.yaml                                       # BrandConfig declarative ref
/home/chris/luana-platform/vitalia/backend/tests/unit/test_extensions_register_all.py      # EP-13 registry test
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py               # EP-13 registry placeholder
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py  # adversarial grader cross-ref comment only
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py  # T-guards-1 placeholder

$ grep -rln "medical_safety_no_diagnosis\|MedicalSafetyNoDiagnosis" /home/chris/AISALESHT/backend/src/ 2>/dev/null
(empty)
```

**Verdict:** zero collisions. NEW vertical-medical surface. NO mirror risk per anti-duplication.md.

## Decisions honored

- **D5** (Slot 4 `MEDICAL_SAFETY_RAILS` NEW prompt slot) — guardrail returns `action='augment_slot_4_safety_reminder'` directive to caller without composing the augmented prompt itself (orchestrator owns prompt assembly). Slot 4 j2 cement file NOT modified.
- **D6** (pass^k adversarial bar ≥0.95) — A3 deferred to T-eval-1 W17 per ticket spec verbatim. Unit-level invariants cement what the adversarial cement at V-AE-11 will validate end-to-end.

## Files committed (luana-platform main)

```
vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py
vitalia/backend/tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py
```

**Commit attribution caveat (parallel-session collision):** during commit phase, a concurrent agent (T-tools-4) was running. My 3 T-guards-1 files landed in commit `7dc63a3` whose message reads `feat(story-11/T-tools-4): vitalia treatment_followup_check workflow tool 7 actions (R23 Opus)`. The commit ALSO contains the other agent's T-tools-4 + T-tools-3 files (5 files total spanning 3 tickets). All T-guards-1 work IS preserved at HEAD (verified via `git show HEAD --stat | grep medical_safety_no_diagnosis` + 47/47 GREEN). Push DEFERRED per `.claude/rules/parallel-safety.md` M5 (do NOT push when collision unresolved). See impl-log.md § Parallel-session commit collision for orchestrator action options (a/b/c).

## Notes for orchestrator → auditor-agentic

- This is the first AGENTIC R23 Opus 4.7 ticket in Sesion 4 W9. Auditor should verify per `.claude/rules/auditor-downstream-regression.md` SSoT row that `vitalia/backend/src/modules/vitalia/agentic/guardrails/*` consumers + `tests/architecture/*` arch-fitness gates remain GREEN.
- Anti-duplication §0 GATE evidence cited verbatim in impl-log + this result. Auditor C1 should confirm no mirror introduced.
- A3 deferred is INTENTIONAL per ticket spec — auditor should NOT flag as missing acceptance; T-eval-1 owns end-to-end adversarial cement.
- Best-effort observability + graceful-degradation invariants verified by 6 dedicated test cases covering audit_log raising AND classifier raising paths (4+2 split for INPUT + OUTPUT layers).
- Tenant isolation cardinal verified per `.claude/rules/tenant-isolation.md` § Repos: `tenant_id` is a required `kw_only` parameter on both entry points; audit_log writes propagate it verbatim. Two dedicated tests assert this invariant.
- PII non-leakage cardinal verified per `.tessl/RULES.md pii-sanitisation`: payload sanitization via `sanitize_payload` from shared (NEVER re-implemented). Two dedicated tests assert no verbatim text leaks (INPUT + OUTPUT).
- Append-only regex ratchet documented in-line with rationale for OUTPUT subject extension (`diabetes` + `cuadro`). True-positives rise; false-positives bounded by 80-char non-greedy gap.
