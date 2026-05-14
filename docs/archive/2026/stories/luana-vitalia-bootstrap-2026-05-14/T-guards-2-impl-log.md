# T-guards-2 — Impl Log

**Ticket:** Guardrail `medical_safety_no_prescription` (forced disclaimer chunk retrieval — input + output layers)
**Surface:** AGENTIC · production_code:true · R23 Opus 4.7 EXCLUSIVE
**Estimate:** 3h · **Actual:** ~1h (single-iter GREEN)
**Validators:** V-AE-8 (49 new + 99 sibling tests = 148 total guardrail PASS) · V-AE-11 deferred to T-eval-1 W17

---

## Skills Consulted

- **copilot-expert** (loaded auto via skill-format prompt) — applied resilience invariants:
  best-effort observability via try/except + structlog warning + audit_log decision NEVER breaks
  guard verdict. Tenant isolation: every audit_log carries `tenant_id`. PII via
  `sanitize_payload` (no user_msg / llm_response verbatim in payload — lengths only).
- **sales-agent-expert** (loaded auto via skill-format prompt) — anti-duplication §0 invoked:
  guardrail surface is a NEW vertical-medical artifact (no shared base exists yet — sibling
  guards T-guards-1 + T-guards-3 also stand alone, lift-shared deferred until 2nd brand
  needs the same shape per design § 18.2 YAGNI). Spec § 17.2 cement strings preserved
  byte-equal at module level. Spanish neutro tuteo enforced for fallback string per spec
  § 17.4 chrome rule (refusal strings stay generic across tenants regardless of voseo
  dialect; voice slot 5 owns the voiced channel-side turn composition).
- **tessl__langgraph** (loaded auto) — N/A this ticket: guard is a plain async pipeline
  function (input + output entry points), not a LangGraph node. State machine wiring
  happens in T-eval-1 W17 via the orchestrator.
- **tessl__graceful-degradation** (loaded auto) — applied Rule 1 (timeout on every external
  call: classifier wrapped at 5s) + Rule 2 (every timeout has fallback: structlog warning
  + return None → guard degrades to pass-through on outage, justified by false-positive
  cost > false-negative cost for input + adversarial pass^5 ≥0.95 cement at V-AE-11
  catches paraphrased asks at end-to-end eval level).
- **tessl__pytest-api-testing** (loaded auto) — N/A direct (no FastAPI route here), but
  applied factory-fixture pattern + parametrize for edge cases (9 fire + 9 benign
  examples for input keyword scan; 5 fire + 5 benign examples for output regex).
- **tessl__fastapi** (loaded auto) — N/A this ticket: pure module, no route surface.

---

## Step 0 — Anti-duplication GATE (per `.claude/rules/anti-duplication.md`)

```bash
$ find /home/chris/AISALESHT/backend/src /home/chris/luana-platform/vitalia/backend/src \
       /home/chris/luana-platform/core -name "medical_safety_no_prescription*" 2>/dev/null
(empty)

$ grep -rn "medical_safety_no_prescription\|MedicalSafetyNoPrescription" \
       /home/chris/luana-platform/vitalia/backend/src/ \
       /home/chris/luana-platform/core/ \
       /home/chris/AISALESHT/backend/src/ 2>/dev/null
vitalia/backend/src/modules/vitalia/extensions.py:502  # placeholder registration tuple
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py:5  # skeleton entry
vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/manifest.yaml:38,51  # spec citations
vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/00_disclaimer.md:3  # spec citation
```

Verdict: ZERO file collisions. Only references = design docs + KB manifest + extension
placeholder + skeleton `__init__.py`. NEW vertical-medical artifact, no mirror risk.
Proceeded with NEW guard implementation per anti-duplication.md decision tree (NEW
last-resort branch — no existing 80% match in shared/luana-platform/AISALESHT trees).

Anti-dup also for medication keyword catalog: source-of-truth is
`medical_kb_psychiatry_v1/manifest.yaml::medication_keywords` (T-kb-3 cement, 300
entries). Loaded once at module init via `_load_medication_keywords()` — NEVER
duplicated to a Python literal. Single edit point keeps KB retrieval + safety guard
in lock-step.

---

## Step 0.5 — Default flip detection

N/A — this ticket adds a NEW module + extends `__init__.py` + adds tests. No
`core/config.py` defaults touched, no feature flag flipped.

---

## Cross-module systems audit (NO-NEW-LAYER per architect rule)

Cross-codebase grep verified:
- `shared/agent_observability/` (AISALESHT) — sanitization helper consumed
  (`luana_core_observability.recording.sanitization::sanitize_payload`), NEVER duplicated.
- `core/luana-core-extension-sdk/` (luana-platform) — guard NOT registered yet via
  ExtensionPointRegistry; placeholder tuple in `vitalia/extensions.py:502`. Wiring
  happens in T-eval-1 W17 (orchestrator integration).
- No shared `GuardrailBase` ABC exists yet (sibling T-guards-1 + T-guards-3 also
  stand alone). Per design § 18.2 YAGNI: lift-shared deferred until 2nd brand needs
  the same guard shape. Documented in module docstring.

---

## TDD RED → GREEN

1. **RED** — Wrote `tests/agentic_evals/guardrails/test_medical_safety_no_prescription.py`
   first (49 unit tests covering A1 + ratchet invariants + tenant isolation +
   graceful degradation + PII guard + frozen dataclass cement). Confirmed RED:
   `ModuleNotFoundError: No module named 'src.modules.vitalia.agentic.guardrails.medical_safety_no_prescription'`.

2. **GREEN** — Wrote
   `src/modules/vitalia/agentic/guardrails/medical_safety_no_prescription.py`
   (~620 lines including module docstring + cement constants + protocols + frozen
   result dataclasses + pure helpers + classifier consultation wrappers + side-effecting
   checks + best-effort audit emission). 49/49 PASS on first run.

3. **Lint+format** — Two long lines (verbs regex literal + test deferred-tag URL)
   wrapped + `ruff format` applied to both files. All checks passed post-fix.

4. **Cross-guard regression** — Ran full guardrails suite: 148/148 PASS
   (T-guards-1 + T-guards-2 + T-guards-3 mutually consistent — `__init__.py` edit
   preserved sibling exports, removed only colliding shared-name dataclass exports
   in favour of fully-qualified import path documented in `__init__.py` docstring).

---

## Files touched (this session, scope by name)

- **NEW** `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_prescription.py`
- **NEW** `vitalia/backend/tests/agentic_evals/guardrails/test_medical_safety_no_prescription.py`
- **EXTEND** `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py`
  (re-read before edit per M8; appended T-guards-2 imports + reserved exports;
  removed colliding shared-name dataclass exports `InputGuardrailResult` /
  `OutputGuardrailResult` / `FALLBACK_RESPONSE_TEMPLATE` / `render_fallback_response`
  in favour of fully-qualified module imports — documented in `__init__.py` docstring;
  no consumer in tree imports those from `__init__` yet, verified via grep).

Did NOT touch (parallel sessions WIP — left intact per parallel-safety.md):
- `core/DEFERRED-FILES.md`, `core/luana-core-platform/...`, `core/tests/architecture/...`
  (luana-core platform session)
- `nicolify/backend/uv.lock`, `vitalia/backend/uv.lock` (untracked WIP)
- `vitalia/backend/tests/integration/__init__.py` (untracked, T-be-7 PARALLEL session)

---

## Spec compliance — § 17.2 verbatim cement

| Spec aspect (§ 17.2) | Implementation verification |
|---|---|
| Runtime layer: BOTH input + output | `medical_safety_no_prescription_input_check` + `medical_safety_no_prescription_output_check` (two entry points, single module) |
| INPUT trigger: keyword scan medication names (200+) + verbs `(tomar\|aumentar\|disminuir\|cambiar\|reemplazar)` | `_INPUT_PRESCRIPTION_RE` couples 300 medication keywords (loaded from `manifest.yaml::medication_keywords`, T-kb-3 cement) with verb pattern within 80-char window. Two orderings (verb→med + med→verb). Plus Haiku classifier fallback. |
| OUTPUT trigger: regex `(te recomiendo tomar\|aumenta la dosis\|cambia tu medicación\|deja de tomar\|reemplaza)` | `_OUTPUT_PRESCRIPTION_RE` cement spec verbatim + Haiku classifier fallback ("Does response recommend medication? bool only."). |
| Action INPUT: forced top-1 retrieval `disclaimer_psychiatric_prescription_only` chunk + Slot 4 reminder + sales_agent inserts disclaimer verbatim + derives to psychiatrist | `InputGuardrailResult.action='force_disclaimer_chunk_retrieval'` + `forced_chunk_id='disclaimer_psychiatric_prescription_only'` + `augment_slot_4_safety_reminder=True` + `derive_to_specialty='psychiatry'` (4-tuple directive payload). Orchestrator W17 consumes via `appointment_reschedule_with_doctor` tool. |
| Action OUTPUT: BLOCK + regenerate + retry 1x + fallback "Solo un psiquiatra puede recetar..." | `OutputGuardrailResult.action='regenerate_with_no_prescription_instruction'` on retry_attempted=False; `action='use_fallback_response'` + `fallback_response=render_fallback_response(...)` on retry_attempted=True. Cement template: `"Solo un psiquiatra puede recetar o ajustar medicación. Te agendo con el {dr_name} de {clinic_name}."` |
| Audit log `medical_safety_no_prescription_fired` (severity HIGH — production-critical psychiatry) | `_AUDIT_EVENT_TYPE = "medical_safety_no_prescription_fired"` + `_AUDIT_SEVERITY = "high"`, written best-effort via `_emit_audit_log` per `.claude/rules/copilot-observability.md`. |
| Tenant isolation cement | `tenant_id: uuid.UUID` required param on both entry points + tested in `test_audit_log_records_tenant_id_input` + `test_audit_log_records_tenant_id_output`. |
| PII cement | Audit payload contains lengths + flags + detection_source ONLY — never user_msg / llm_response verbatim. `sanitize_payload` applied per `.tessl/RULES.md pii-sanitisation`. Tested in `test_audit_payload_does_not_leak_*_verbatim`. |
| Best-effort observability | audit_log failure swallowed + structlog warning, decision NEVER breaks. Tested in `test_*_check_*_even_if_audit_log_raises` + `test_*_check_works_without_audit_log`. |
| Graceful degradation (classifier outage) | classifier raise → structlog warning + return None → pass-through (false-positive cost > false-negative cost; V-AE-11 adversarial cement catches). Tested in `test_*_check_degrades_when_classifier_fails`. |
| Cost guard (regex/keyword fast-path skip classifier) | Verified `classifier.calls == []` after regex/keyword hit in `test_input_check_fires_on_keyword_match_without_calling_classifier` + `test_output_check_blocks_on_regex_match_emits_regenerate_hint`. |

---

## Acceptance criteria — verification

| AC | Test | Status |
|---|---|---|
| A1 — Medication keyword + verb triggers forced disclaimer chunk retrieval | `test_input_check_fires_on_keyword_match_without_calling_classifier` (regex path) + `test_input_check_fires_on_classifier_when_keywords_miss` (classifier path) + `test_forced_disclaimer_chunk_id_matches_kb_manifest` + `test_medication_keywords_loaded_from_manifest` | **PASS** |
| A2 — Adversarial medication persona pass^5 ≥0.95 | `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py::test_prescription_safety` (FILE NOT YET CREATED) | **DEFERRED** to T-eval-1 W17 — explicit per ticket spec ("DEFER (grader scenario file is T-eval-1 W17)"). Documented gap in T-guards-2-result.md. |

---

## Validators run

- **V-AE-8** — 49 new tests (this ticket) + 99 sibling tests (T-guards-1 + T-guards-3) =
  148/148 guardrail tests PASS in 0.16s.
- **V-AE-11** — DEFERRED to T-eval-1 W17 (file `test_vertical_medical_fidelity_adversarial.py`
  not yet created — that ticket wires the synthetic-tenant adversarial grader).
- **lint+format** — `ruff check` + `ruff format --check` on all 3 modified files: clean.

---

## Push race protocol — observed

T-be-7 PARALLEL session also touches `vitalia/backend/`. Pre-commit `git status` shows
`vitalia/backend/tests/integration/__init__.py` untracked (T-be-7 WIP). Will NOT stage
that file. If push fails non-fast-forward → STOP, report `blocked` with reason
"parallel push race vs T-be-7", NO `git pull` / `git reset` per parallel-safety.md M5.

---

## Cost — actuals

Single iter, no Opus retries needed. Tests passed first run after impl + format fix
(2 long-line tweaks). Estimate 3h vs actual ~1h: spec § 17.2 is well-cemented, T-guards-1
gave a clean shape blueprint, and 354-entry medication catalog was already curated by
T-kb-3 — most work was protocol-shaped TDD with high test coverage upfront.
