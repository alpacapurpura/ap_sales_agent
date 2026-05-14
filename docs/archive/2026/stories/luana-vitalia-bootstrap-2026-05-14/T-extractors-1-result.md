# T-extractors-1 — Result

**Ticket:** `MedicalKBExtractor` — 4-wave vision LLM PDF extraction (vertical-medical AGENTIC).
**State:** `tests-passing` (developing → developed, awaiting auditor verdict per R30).
**R23:** production_code=true → Opus 4.7 EXCLUSIVE.
**Date:** 2026-05-14.
**Builder:** Claude Opus 4.7 (1M context).

---

## TL;DR

25/25 tests GREEN (24 unit + 1 arch fitness). `MedicalKBExtractor(BaseExtractionOrchestrator)` extends shared base per anti-duplication SSoT. 4-wave pipeline (Sonnet vision + Sonnet vision + Haiku + Sonnet text validator) returns `MedicalHistoryV1` with confidence_score + warnings. Cost ceiling ≤$0.15 USD per PDF enforced as warning (not raise). Best-effort persistence + Qdrant + outbox + audit_log isolated per side-effect. PII non-leak + tenant isolation invariants verified. No mirror — luana-core-extraction is canonical home, luana-core-observability supplies sanitization + cost bridge.

---

## Deliverables

### Production code (luana-platform main)

- `vitalia/backend/src/modules/vitalia/copilot/extractors/medical_kb_extractor.py` — `MedicalKBExtractor` class extending `BaseExtractionOrchestrator`. Methods: `_define_waves`, `run`, `_run_one_wave`, `_run_validate_wave`, `_resolve_wave_cost`, `_parse_wave_json`, `_merge_outputs`, `_parse_list`, `_parse_optional`, `_merge_and_save`, `_persist_history`. Constants: `DEFAULT_COST_BUDGET_USD=Decimal('0.15')`, `MIN_ACCEPTABLE_CONFIDENCE=0.7`, `EXTRACTOR_VERSION='medical_kb_v1'`. Protocols: `_LiteLLMServiceLike`, `_PatientMedicalHistoryRepoLike`, `_QdrantIndexerLike`, `_OutboxLike`, `_AuditLogLike`. ~700 lines including verbose docstrings + spec citations.
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_schemas.py` — Pydantic schemas (`Allergy`, `Condition`, `Medication`, `Surgery`, `FamilyHistorySummary`, `VitalSigns`, `MedicalHistoryV1` with `schema_version: Literal[1]` cement) + `ExtractionWave` dataclass. Sibling T-extractors-2 also appended dental primitives (M8 coexistence, sibling owns).
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/__init__.py` — package marker + cache prefix invariant doc.
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_allergies_meds.j2` — W1 prompt template (Sonnet vision). Cache-friendly: invariant prefix BEFORE `<<CACHE_BOUNDARY>>` marker, variable PDF text AFTER.
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_conditions_surgeries.j2` — W2 prompt template (Sonnet vision).
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_family_vitals.j2` — W3 prompt template (Haiku).
- `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_validate_merge.j2` — W4 prompt template (Sonnet text validator).

### Tests (luana-platform main)

- `vitalia/backend/tests/agentic_evals/extractors/test_medical_kb_extractor.py` — 24 unit tests covering A1, A2, A3 + 8 defensive paths (wave failure, malformed entity, invalid JSON, cost-unknown, persistence/Qdrant/outbox/audit failure isolation) + tenant isolation + PII non-leak + wave declaration sanity. ~600 lines.
- `vitalia/backend/tests/architecture/test_extraction_orchestrator_inheritance.py` — A1 verifier; vitalia-scoped twin of AISALESHT arch fitness gate. AST scan of `vitalia/copilot/extractors/*.py`. Ratchet allowlist `KNOWN_EXTRACTORS_WITHOUT_BASE = set()` (shrink-only).

### Conftest extension (M8)

- `vitalia/backend/conftest.py` — appended `luana_core_extraction/src` to `_WORKSPACE_SRC_PATHS` tuple (1 line).

### Docs (AISALESHT development)

- `docs/product/stories/luana-vitalia-bootstrap/T-extractors-1-impl-log.md` — Skills Consulted, Step 0 GATE evidence, iteration log, acceptance coverage matrix, architectural decisions, cost ceiling design, tenant isolation invariant, PII handling, validator results.
- `docs/product/stories/luana-vitalia-bootstrap/T-extractors-1-result.md` — this file.

---

## Acceptance criteria coverage

| AC | Test | Result |
|---|---|---|
| A1 — Subclass of BaseExtractionOrchestrator (arch fitness) | `tests/architecture/test_extraction_orchestrator_inheritance.py::test_every_vitalia_extractor_inherits_base` | **PASS** |
| A2 — 4 waves complete + merge produces MedicalHistoryV1 with confidence_score | `tests/agentic_evals/extractors/test_medical_kb_extractor.py::test_4_wave_pipeline` | **PASS** |
| A3 — Cost per PDF ≤$0.15 USD | `tests/agentic_evals/extractors/test_medical_kb_extractor.py::test_cost_budget` | **PASS** |

Plus 22 additional unit tests covering defensive paths, persistence semantics, side-effect isolation, tenant isolation invariant, PII non-leak, wave declaration sanity. **24/24 unit + 1/1 arch = 25/25 GREEN.**

---

## Validators

| ID | Test path | Status |
|---|---|---|
| V-AE-6 (medical scope) | `tests/agentic_evals/extractors/test_medical_kb_extractor.py` | **GREEN 24/24** |
| V-AE-16 (cost budget) | `test_cost_budget` + `test_cost_budget_exceeded_recorded_as_warning_not_raised` | **GREEN** |
| Arch fitness (A1) | `tests/architecture/test_extraction_orchestrator_inheritance.py` | **GREEN 1/1** |

V-AE-6 also runs sibling `test_dental_history_extractor.py` (T-extractors-2 — parallel session). Sibling has 1 unrelated test failure NOT in my scope per M8.

---

## Lint + format

```
ruff check src/modules/vitalia/copilot/extractors/ tests/agentic_evals/extractors/test_medical_kb_extractor.py tests/architecture/test_extraction_orchestrator_inheritance.py
→ All checks passed!

ruff format --check src/modules/vitalia/copilot/extractors/ tests/agentic_evals/extractors/test_medical_kb_extractor.py tests/architecture/test_extraction_orchestrator_inheritance.py
→ 7 files already formatted
```

---

## Out-of-scope (not implemented in this ticket — documented for follow-up)

- **`extensions.py` `ExtractorDef.prompt_template_ref` update** — current placeholder cites `vitalia/medical_kb_extractor.j2` (single file), but the actual extractor uses 4 separate templates. Updating extensions.py is in T-extensions-1 / future wiring scope.
- **Real LiteLLM service injection** — production wiring (`LiteLLMService` instance + cost_recorder ARQ bootstrap registration) lands in the agentic-runtime mounting ticket. Tests use in-memory `FakeLiteLLMService` — production behavior is contract-equivalent (Protocol surface).
- **Real Qdrant per-tenant collection bootstrap** — collection-create logic lands in the Qdrant bootstrap ticket; extractor consumes via injected `QdrantIndexer` instance.
- **Real outbox publisher injection** — outbox ARQ table publish wiring lands in the events runtime ticket.
- **Real audit_log repo injection** — `MedicalAuditLogRepository` (T-be-3) is available; constructor injection happens at the agentic-runtime mounting ticket.

---

## Skills Consulted (per Step 0 GATE)

| Skill | Decision |
|---|---|
| `copilot-expert` | EXTEND `BaseExtractionOrchestrator`. Best-effort observability `try/except + structlog.warning` (R23). |
| `sales-agent-expert` | Cost via `pop_cost(litellm_call_id)` per PI-12 S1 T-1 cement. None → cost-unknown warning. |
| `tessl__langgraph` | N/A — Template Method via base, not StateGraph (no conditional edges). |
| `tessl__graceful-degradation` | Per-wave `asyncio.wait_for(timeout)`. Each side-effect isolated try/except. Wave failure → partial result + warning. |
| `tessl__pytest-api-testing` | `asyncio_mode=auto`. Factory fixture pattern. Per-role spec lists FIFO. Direct `cost_recorder._cache` seed for cost determinism. |
| `tessl__fastapi` | N/A — no FastAPI route. |

---

## State transition

- Pre-build: `state=draft`.
- Build complete: `state=tests-passing` (developing → developed, awaiting auditor).
- Awaiting: `/auditor` Conv 3 spawn for independent verdict per R30.

---

**Last line:** `done -> docs/product/stories/luana-vitalia-bootstrap/T-extractors-1-result.md`
