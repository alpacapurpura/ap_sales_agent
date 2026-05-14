# T-extensions-1 Result

**Ticket:** T-extensions-1 — extensions.py register_all EP-1..EP-18 entry point
**Story:** luana-vitalia-bootstrap (Story 11)
**Verdict:** tests-passing (awaiting auditor-agentic independent verdict per R30)
**Date:** 2026-05-14
**Iteration:** 1/3
**Builder:** Claude Opus 4.7 (R23 production AGENTIC code mandatory)

---

## Acceptance Criteria Evidence

### A1 — register_all succeeds without exception

```
$ cd /home/chris/luana-platform/vitalia/backend && \
  /home/chris/luana-platform/.venv/bin/python -m pytest \
  tests/unit/test_extensions_register_all.py -v --tb=short

collected 18 items

tests/unit/test_extensions_register_all.py::test_register_all_succeeds PASSED
tests/unit/test_extensions_register_all.py::test_register_all_populates_all_18_eps PASSED
tests/unit/test_extensions_register_all.py::test_register_all_idempotent_on_fresh_registry PASSED
tests/unit/test_extensions_register_all.py::test_all_registrations_use_vitalia_namespace PASSED
tests/unit/test_extensions_register_all.py::test_ep2_offer_preset_pack_count_one PASSED
tests/unit/test_extensions_register_all.py::test_ep3_sales_agent_tools_count_four PASSED
tests/unit/test_extensions_register_all.py::test_ep4_copilot_workflow_count_one PASSED
tests/unit/test_extensions_register_all.py::test_ep7_extractors_count_two PASSED
tests/unit/test_extensions_register_all.py::test_ep8_channel_adapters_count_three PASSED
tests/unit/test_extensions_register_all.py::test_ep13_guardrails_count_four PASSED
tests/unit/test_extensions_register_all.py::test_ep14_kb_packs_count_three PASSED
tests/unit/test_extensions_register_all.py::test_ep17_plan_tiers_count_three PASSED
tests/unit/test_extensions_register_all.py::test_ep3_tools_have_placeholder_handlers PASSED
tests/unit/test_extensions_register_all.py::test_ep14_kb_packs_tenant_scope_brand PASSED
tests/unit/test_extensions_register_all.py::test_ep17_plan_tiers_registered_with_override_mode PASSED
tests/unit/test_extensions_register_all.py::test_ep5_booking_policy_consent_required PASSED
tests/unit/test_extensions_register_all.py::test_ep1_field_override_dispatchable_returns_none_or_override PASSED
tests/unit/test_extensions_register_all.py::test_extensions_module_does_not_register_bare_names PASSED

============================== 18 passed in 0.12s ==============================
```

**A1 PASS** — 18/18 tests GREEN.

### A2 — Docs extension_points.md completeness arch fitness GREEN

```
$ cd /home/chris/luana-platform && \
  .venv/bin/pytest core/tests/architecture/test_docs_extension_points_completeness.py -v

collected 8 items

core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_file_exists PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_section_1_header PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_vitalia_examples PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_comunify_examples PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_lupulo_examples PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_no_ep19_literal PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_vertical_agent_recipe PASSED
core/tests/architecture/test_docs_extension_points_completeness.py::test_docs_has_cross_brand_learning_principle PASSED

============================== 8 passed in 0.10s ==============================
```

**A2 PASS** — V-NF-13 (per 04-validators.yaml) GREEN.

---

## Validators Run

- **V-NF-13** (Extension SDK docs completeness — vitalia register_all surface covered) → **PASS**

---

## Files Created (luana-platform side)

```
vitalia/backend/src/modules/vitalia/extensions.py                   (production: register_all EP-1..EP-18)
vitalia/backend/src/modules/vitalia/agentic/__init__.py             (skeleton package)
vitalia/backend/src/modules/vitalia/agentic/tools/__init__.py       (skeleton package)
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py  (skeleton package)
vitalia/backend/src/modules/vitalia/agentic/prompts/__init__.py     (skeleton package)
vitalia/backend/src/modules/vitalia/copilot/__init__.py             (skeleton package)
vitalia/backend/src/modules/vitalia/copilot/extractors/__init__.py  (skeleton package)
vitalia/backend/src/modules/vitalia/copilot/workflows/__init__.py   (skeleton package)
vitalia/backend/src/modules/vitalia/copilot/kb/__init__.py          (skeleton package)
vitalia/backend/tests/unit/test_extensions_register_all.py          (18 unit tests)
```

## Files Created (AISALESHT side — docs)

```
docs/product/stories/luana-vitalia-bootstrap/T-extensions-1-impl-log.md
docs/product/stories/luana-vitalia-bootstrap/T-extensions-1-result.md  (this file)
```

---

## Decisions Honored

- **D1** — Vitalia subdir at `luana-platform/vitalia/` (no separate repo) — extensions.py
  lives in `vitalia/backend/src/modules/vitalia/`.
- **D5** — Slot 4 MEDICAL_SAFETY_RAILS reserved at architecture phase. Real prompt MD
  ratified for T-prompts-1 (NOT registered via EP — slot is part of prompt layout SSoT
  in `02-design-agentic § 10`).
- **D7** — compliance_level=hipaa_lite encoded in `KbPackDef.metadata.compliance_level`
  for all 3 EP-14 KB packs.
- **D8** — voice_cloning_enabled=false reflected in brand.yaml (already populated by T-config-1).
  No SDK surface for voice cloning (sales-agent voice = personality_profiles SSoT, not per-brand).

---

## Quality Gates

| Gate | Status | Evidence |
|---|---|---|
| Anti-duplication Step 0 GATE | PASS | impl-log §Phase 0 grep evidence |
| Step 0 skills invocation | PASS | impl-log §Skills Consulted (7 skills cited) |
| Default-flip detection | N/A | No `core/config.py` defaults touched |
| Cross-module audit (NO-NEW-LAYER) | PASS | impl-log §Cross-module Audit |
| TDD cycle (RED → GREEN → REFACTOR) | PASS | impl-log §TDD Cycle |
| Ruff lint (line-length 120) | PASS | `ruff check` 0 errors on new files |
| Ruff format | PASS | `ruff format --check` 0 reformats needed (post-fix) |
| Test suite scope (vitalia unit + arch) | PASS | 82/82 PASS (18 new + 64 pre-existing) |
| V-NF-13 arch fitness | PASS | 8/8 PASS on `test_docs_extension_points_completeness.py` |
| Parallel-safety M8 (other-session files intact) | PASS | git status verified post-implementation |
| Spanish neutro / no voseo | PASS | Labels: "Pendiente consentimiento", "Datos de la clínica", "Seguimientos" — tuteo |
| Tenant isolation invariant | N/A | No DB queries here; BrandContext arrives at request time |
| Best-effort observability | N/A | Pure declarative registration; no LLM/external calls |

---

## Downstream Regression Scope (R3)

Surface added: `vitalia/backend/src/modules/vitalia/extensions.py` (brand-side SDK
consumer — NOT a shared/ abstraction). No cross-module consumers. SDK code at
`core/luana-core-extension-sdk/` UNTOUCHED. No downstream regression mandatory.

Pre-commit freshness gate: new files do NOT live under `backend/src/shared/`. Gate
does not apply.

---

## Tickets Unblocked

Per ticket `blocks` field in 06-tickets.yaml:
- T-tools-1 (prepaid_payment_check) — handler placeholder in place; real impl can land
- T-tools-2 (medical_consent_request) — handler placeholder in place
- T-tools-3 (appointment_reschedule_with_doctor) — handler placeholder in place
- T-tools-4 (treatment_followup_check) — handler placeholder in place (also blocked by T-workflow-1)
- T-extractors-1 (MedicalKBExtractor) — ExtractorDef registered; real class lands in extractor module
- T-extractors-2 (DentalHistoryExtractor) — ExtractorDef registered; real class lands in extractor module
- T-kb-1..3 (medical_kb_dental_v1, medical_kb_psychology_v1, medical_kb_psychiatry_v1) — KbPackDef registered with documents_path + Qdrant collection_name
- T-prompts-1 (Slot 4 MEDICAL_SAFETY_RAILS prompt) — NOT via EP, but acknowledged in extensions.py docstring

---

## Notable Implementation Decisions

(Brief — full detail in `T-extensions-1-impl-log.md`)

1. **Pattern Option C (skeleton modules)** selected for `agentic/{tools,guardrails,prompts}/` +
   `copilot/{extractors,workflows,kb}/` empty packages. Later tickets drop files in.
2. **Design vs SDK reconciliation** — pseudo-code `register_all(brand_slug=, config=)` shown
   in design docs translated to test-brand pattern `def register_all(registry)`. CC-5
   inmutable SDK cannot grow classmethod. Same intent, same single-call interface.
3. **EP-13 guardrails mode='append'** despite future replacement — CC-2 forbids override
   on EP-13, so T-guards-* will replace by direct file edit (not re-register).
4. **EP-17 + EP-18 mode='override'** intentionally used — CC-2 explicit allowance for
   tier + wizard step replacement per brand vertical.
5. **EP-14 tenant_scope='brand'** for all 3 medical KB packs — cross-tenant share OK
   under D7 hipaa_lite (medical reference content, no PHI).

---

## Iteration Outcome

Iteration 1/3 completed in single pass. No re-iterations needed:
- Anti-duplication GATE green first try (test-brand pattern reference matched)
- TDD RED → GREEN single pass (18/18 tests)
- Ruff auto-fix sorted imports + reformatted line breaks (no manual intervention)
- A1 + A2 acceptance criteria both PASS

Cost estimate (per impl-log): ~50k tokens.

---

## Awaiting

Per R30 (2026-05-05 builder NEVER claims audit verdict), this ticket is in state
`tests-passing`. Orchestrator (`/dev-team` skill) spawns:
1. `gate-runner` Haiku for full `/test-backend` 13 gates (downstream regression if applicable).
2. `auditor-agentic` Opus for independent verdict (C1-C3 Code/Spec/Architecture audit).

Builder phase output: `tests-passing` ONLY. Final verdict (APPROVED / CHANGES_REQUESTED /
ESCALATED) decided by auditor-agentic per `/auditor` skill.
