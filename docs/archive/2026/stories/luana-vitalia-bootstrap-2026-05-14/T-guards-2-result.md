# T-guards-2 — Result

**Status:** tests-passing (awaiting orchestrator → gate-runner → auditor-agentic per R30).

## Summary

Vitalia AGENTIC guardrail `medical_safety_no_prescription` (input + output layers,
severity HIGH, production-critical for psychiatry tenants) implemented per
02-design § 17.2 + 03-arch § 10.2. Ships:

- **Input layer:** medication-keyword + verb scan (300-name catalog loaded from
  `medical_kb_psychiatry_v1/manifest.yaml::medication_keywords` T-kb-3 cement) +
  Haiku classifier fallback. On fire → directive payload `(force_disclaimer_chunk_retrieval,
  forced_chunk_id='disclaimer_psychiatric_prescription_only',
  augment_slot_4_safety_reminder=True, derive_to_specialty='psychiatry')` for orchestrator
  consumption. Cost guard: regex hit short-circuits classifier.
- **Output layer:** spec § 17.2 verbatim regex (te recomiendo tomar | aumenta la dosis |
  cambia tu medicación | deja de tomar | reemplaza) + Haiku classifier fallback. On fire +
  retry_attempted=False → BLOCK + `regenerate_with_no_prescription_instruction`. On fire +
  retry_attempted=True → BLOCK + cement fallback `"Solo un psiquiatra puede recetar o
  ajustar medicación. Te agendo con el {dr_name} de {clinic_name}."`
- **Audit log:** `medical_safety_no_prescription_fired` (severity HIGH) on fire/block
  only, best-effort write via `sanitize_payload` (lengths + flags + detection_source —
  NEVER user_msg / llm_response verbatim).
- **Graceful degradation:** classifier outage → structlog warning + pass-through (false-
  positive cost > false-negative; V-AE-11 adversarial cement catches paraphrased asks).
- **Tenant isolation:** `tenant_id: uuid.UUID` required on both entry points + propagated
  through every audit_log write.
- **Frozen result dataclasses:** `InputGuardrailResult` + `OutputGuardrailResult` (slots,
  kw_only, frozen) — caller cannot mutate verdict after dispatch.

## Files delivered

| File | Status | Lines |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_prescription.py` | NEW | ~620 |
| `vitalia/backend/tests/agentic_evals/guardrails/test_medical_safety_no_prescription.py` | NEW | ~620 |
| `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py` | EXTEND (preserve T-guards-1 + T-guards-3 entries; add T-guards-2 exports; remove colliding shared-name dataclass exports in favour of fully-qualified import path documented in `__init__.py` docstring) | +28 / −7 |

## Validators

- **V-AE-8** (guardrails) — `cd vitalia/backend && uv run pytest tests/agentic_evals/guardrails/ -v`
  → **148/148 PASS** in 0.16s (49 new + 99 sibling guard tests).
- **lint+format** — `ruff check` + `ruff format --check` on all 3 modified files: clean.
- **V-AE-11** (adversarial pass^5 ≥0.95) — DEFERRED to T-eval-1 W17 (the grader scenario
  file `test_vertical_medical_fidelity_adversarial.py::test_prescription_safety` is
  produced there). Explicit per ticket spec.

## Acceptance criteria

| AC | Status | Evidence |
|---|---|---|
| A1 — Medication keyword + verb triggers forced disclaimer chunk retrieval | **PASS** | `test_input_check_fires_on_keyword_match_without_calling_classifier` (regex path, cost-guard verifies classifier not called) + `test_input_check_fires_on_classifier_when_keywords_miss` (classifier path) + `test_forced_disclaimer_chunk_id_matches_kb_manifest` (chunk_id cement matches T-kb-3 manifest) + `test_medication_keywords_loaded_from_manifest` (300+ entries + canonical INN + brand sample present) |
| A2 — Adversarial medication persona pass^5 ≥0.95 | **DEFERRED** | T-eval-1 W17 owns `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py::test_prescription_safety`. T-guards-2 spec ticket explicitly defers this AC ("DEFER (grader scenario file is T-eval-1 W17)"). |

## Skills consulted

- **copilot-expert** — best-effort observability + tenant isolation + PII via sanitize_payload.
- **sales-agent-expert** — anti-duplication §0 (NEW vertical-medical surface, ZERO mirror) +
  Spanish neutro tuteo for fallback string per spec § 17.4 chrome rule.
- **tessl__graceful-degradation** — Rule 1 (5s classifier timeout) + Rule 2 (structlog
  warning + return None on outage → pass-through, justified rationale documented).
- **tessl__pytest-api-testing** — factory fixtures + parametrize for edge cases (49
  granular tests covering happy paths + 6 graceful-degradation paths + 4 PII guards).
- **tessl__langgraph** + **tessl__fastapi** — N/A this ticket (pure async pipeline functions,
  no LangGraph node, no FastAPI route).

## Anti-duplication audit (per `.claude/rules/anti-duplication.md`)

```bash
$ find /home/chris/AISALESHT/backend/src /home/chris/luana-platform/vitalia/backend/src \
       /home/chris/luana-platform/core -name "medical_safety_no_prescription*" 2>/dev/null
(empty)

$ grep -rn "class MedicalSafetyNoPrescription" /home/chris/AISALESHT/backend/src/ \
       /home/chris/luana-platform/ 2>/dev/null
(empty)
```

Verdict: ZERO file/class collisions. NEW vertical-medical artifact. Sibling guards
T-guards-1 + T-guards-3 also stand alone (no shared `GuardrailBase` ABC exists yet —
lift-shared deferred until 2nd brand needs the same guard shape per design § 18.2 YAGNI).

Medication keyword catalog → SSoT in `medical_kb_psychiatry_v1/manifest.yaml::medication_keywords`
(T-kb-3 cement, 300 entries) loaded once at module init via `_load_medication_keywords()`.
NEVER duplicated to a Python literal. Single edit point keeps KB retrieval + safety guard
in lock-step.

## Cost-bucket impact

N/A — guard is pure regex/keyword path on hot path ($0). Classifier fallback consumed via
LiteLLM Proxy CustomLogger bridge (PI-12 S1 T-1 cement) → cost recorded via existing
`copilot_llm_call` / `cost_recorder` infrastructure on caller side. No new cost bucket
introduced.

## Footer

<!-- @pm: build phase done (state: tests-passing). Commit: pending push. Files: 3 (1 NEW prod + 1 NEW test + 1 EXTEND init). Native ticket tests: 49/49 PASS · sibling-suite regression 148/148 PASS · ruff check + format clean. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict per R30). -->
