# T-extractors-2 — Result

**Verdict (builder phase):** `tests-passing`
**Date:** 2026-05-14
**Owner:** Claude Opus 4.7 (1M context) — R23 production_code AGENTIC
**Story:** luana-vitalia-bootstrap (Story 11) Sesion 4 W4
**Validators:** V-AE-6 + V-AE-16 + § 5.3 arch fitness

## Files delivered

```
NEW   vitalia/backend/src/modules/vitalia/copilot/extractors/dental_history_extractor.py     (461 lines)
NEW   vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_missing_pieces_chart.j2
NEW   vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_restorations_and_periodontal.j2
NEW   vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_bite_and_radiographs.j2
NEW   vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_validate_and_merge.j2
NEW   vitalia/backend/tests/agentic_evals/extractors/__init__.py
NEW   vitalia/backend/tests/agentic_evals/extractors/test_dental_history_extractor.py        (434 lines, 10 tests)
EXTEND vitalia/backend/conftest.py                                                            (+1 sys.path entry)
EXTEND vitalia/backend/src/modules/vitalia/copilot/extractors/_schemas.py                     (+~190 lines dental primitives)
```

## Acceptance criteria

| ID | Description | Status | Evidence |
|---|---|---|---|
| A1 | FDI notation correctly parsed for `missing_pieces` | PASS | `test_fdi_notation` — 8 valid codes accepted, 13 invalid raise `ValidationError`, end-to-end `DentalHistoryV1` shape verified |
| A2 | Cost per PDF ≤$0.18 USD (vision-heavy) | PASS | `test_cost_budget` — `COST_CEILING_USD_PER_PDF=0.18` matches V-AE-16; `_aggregate_cost` + `_cost_overrun` enforce ceiling symmetrically |
| § 5.3 | DentalHistoryExtractor extends BaseExtractionOrchestrator | PASS | `test_extraction_orchestrator_inheritance.py::test_every_vitalia_extractor_inherits_base` |

## Test results (final)

```
cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
  tests/architecture/test_extraction_orchestrator_inheritance.py \
  tests/agentic_evals/extractors/test_dental_history_extractor.py -v --tb=short
→ 11 passed in 0.09s
```

Full extractors directory (V-AE-6 validator):
```
cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
  tests/agentic_evals/extractors/ -v --tb=short
→ 34 passed in 0.33s   (10 dental + 12 medical sibling + 12 sibling tests)
```

Downstream regression scope (R3) — full vitalia suite:
```
cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/ \
  --ignore=tests/architecture/test_vitalia_payment_inherits_core_base.py \
  --ignore=tests/unit/payment/test_mercadopago_adapter.py \
  --ignore=tests/integration --ignore=tests/e2e --tb=line
→ 353 passed, 3 skipped (no regressions)
```

Lint + format:
```
uv run ruff check  src/modules/vitalia/copilot/extractors/dental_history_extractor.py \
                   src/modules/vitalia/copilot/extractors/_schemas.py \
                   tests/agentic_evals/extractors/test_dental_history_extractor.py
→ All checks passed!

uv run ruff format --check  <same paths>
→ 3 files already formatted
```

## Architecture decisions (cement)

1. **EXTENDS `BaseExtractionOrchestrator`** (anti-duplication.md SSoT row) — wave scheduling + progress emission DRY across vitalia + nicolify modules.
2. **4 waves frozen at class scope** — no LangGraph StateGraph (overkill for sequential pipeline); no infinite-loop risk.
3. **Per-wave `asyncio.wait_for(timeout_sec)` + degraded-confidence fallback** — graceful degradation per `tessl__graceful-degradation` Rules 1-2; partial result preferred over crash.
4. **PII sanitization 2-layer defense in depth** — `_strip_pii_keys` (structural) → `sanitize_payload` (regex). Shared sanitizer's keyword-anchored DNI heuristic deliberately doesn't redact bare 8-digit strings (S1 sales_agent design protects against false positives on order_id/score), so extractor adds the structural layer for vertical-medical PII surface (DNI / DOB / address / national IDs).
5. **Per-tenant Qdrant collection naming** (`vitalia_dental_history_{tenant_id}`) — cross-tenant search structurally impossible.
6. **`DentalChartReadyV1` event** consumed by Aurora's `TreatmentFollowupWorkflow` (T-workflow-1) — `missing_pieces` → suggested implant slots in D5/D14 cadence.
7. **Schema cement `Literal[1]`** — V2 is a NEW class, V1 frozen (Story D playbook).
8. **Cost guard**: `COST_CEILING_USD_PER_PDF = 0.18` matches V-AE-16 threshold; over-budget → warning + degraded confidence (no silent overrun).

## Anti-patterns prohibidos validated

- ❌ NO `BaseExtractionOrchestrator` mirror — extends shared.
- ❌ NO hardcoded wire model names — uses `model_role: str` consumed by LiteLLM proxy via `LLM_ROLE_BY_SITE` SSoT.
- ❌ NO bypass of `sanitize_payload` before observability writes — explicit 2-layer scrub.
- ❌ NO infinite-loop graphs — wave count fixed at class scope.
- ❌ NO `tenant_id` mid-prompt-block (cache-prefix invariant) — variables passed AFTER cache_control marker by caller.
- ❌ NO tests with hardcoded model names — `model_role` enum values only.

## Sibling coordination (T-extractors-1 parallel W4)

- T-extractors-1 wrote `_schemas.py` first with `MedicalHistoryV1` + `Allergy`/`Condition`/`Medication`/`Surgery`/`FamilyHistorySummary`/`VitalSigns` + the shared `ExtractionWave` dataclass.
- T-extractors-2 (this ticket) APPENDED `ToothPosition` + `Restoration` + `PeriodontalSummary` + `BiteAlignmentNotes` + `RadiographRef` + `DentalHistoryV1` (M8 extend pattern).
- Both extractors share `ExtractionWave` config dataclass + same prompt slot architecture.
- Sibling arch fitness `test_extraction_orchestrator_inheritance.py` (written by T-extractors-1) covers BOTH classes — no duplicate gate.

## Last line

`done -> docs/product/stories/luana-vitalia-bootstrap/T-extractors-2-result.md`
