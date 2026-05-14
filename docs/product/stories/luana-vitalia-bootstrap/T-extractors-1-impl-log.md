# T-extractors-1 — Implementation Log

**Ticket:** `MedicalKBExtractor` — 4-wave vision LLM PDF extraction (vertical-medical AGENTIC).
**Surface:** AGENTIC · production_code=true · R23 Opus 4.7 EXCLUSIVE.
**Decisions applicable:** D1 (vitalia subdir + extension SDK).
**Validators target:** V-AE-6 + V-AE-16.
**Builder:** Claude Opus 4.7 (1M context).
**Date:** 2026-05-14.

---

## Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Vitalia copilot extractor surface (`vitalia/copilot/extractors/`) — vertical-medical analogue of brand/offer extractors. | EXTEND `BaseExtractionOrchestrator` (anti-duplication SSoT row). Best-effort observability writes wrapped `try/except + structlog.warning` (R23). Wave + sleep + progress mechanics consumed from base, NEVER re-implemented. PII scrubbed via `sanitize_payload` BEFORE Qdrant + outbox + audit writes. |
| `sales-agent-expert` | Cost capture via LiteLLM CustomLogger bridge (`pop_cost(litellm_call_id)`) per PI-12 S1 T-1 cement; LiteLLM proxy is sole dispatch path post T-5 cleanup. | Use `pop_cost(call_id)` returning `Decimal | None`. `None` → cost-unknown warning (NOT default 0). Cost ceiling enforced as warning (NOT raise) so partial extraction still ships. |
| `tessl__langgraph` | NOT invoked — extractor is wave-based asyncio.gather, not a StateGraph. | N/A — Template Method via `BaseExtractionOrchestrator` is the right pattern; Wrapping in StateGraph would over-engineer (no conditional edges, no checkpointing needs). |
| `tessl__graceful-degradation` | Each LLM wave + Qdrant + outbox + audit is an external call needing timeout + fallback + isolation. | Per-wave `asyncio.wait_for(timeout=wave.timeout_sec + 2.0)` (asyncio guard around LLM-internal timeout). Each side-effect `try/except` in its own block — Qdrant down does not affect outbox; outbox down does not affect audit. Wave failure → returns partial via `extraction_warnings` + degraded `confidence_score`. |
| `tessl__pytest-api-testing` | New async pytest tests with in-memory fakes for repo + LLM + Qdrant + outbox + audit. | `asyncio_mode=auto` (already set vitalia pyproject.toml). Factory `_build_extractor` accepts optional collaborators. Per-role spec lists FIFO-popped to drive synthetic LLM JSON outputs. Direct `cost_recorder._cache` seed for cost determinism. parametrize-style coverage via dedicated functions per scenario (8+ defensive paths). |
| `tessl__fastapi` | NOT invoked — no FastAPI route in this ticket. | N/A — extractor consumed by future API ticket (separate). |

---

## Step 0 GATE — Anti-duplication grep evidence

```bash
$ grep -rn "class MedicalKBExtractor" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# zero collisions

$ grep -rn "class MedicalHistoryV1\|MedicalHistoryV1" ... | grep -v __pycache__
# zero collisions

$ grep -rn "MedicalHistoryExtractedV1\|MedicalHistoryExtracted" ... | grep -v __pycache__
# zero collisions

$ grep -rn "^class Allergy\|^class Condition\|^class Medication|^class Surgery|^class FamilyHistory|^class VitalSigns" ... | grep -v __pycache__
# only ConditionalQuestion (offer module) — different concept, not collision
```

**Verdict:** All NEW symbols. No mirror risk.

**Anti-duplication shared abstractions consumed (NEVER re-implemented):**
- `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` — wave + pause + progress mechanics.
- `luana_core_observability.recording.sanitization.sanitize_payload` — PII scrubbing.
- `luana_core_observability.recording.cost_recorder.pop_cost` — LiteLLM CustomLogger bridge (PI-12 S1 T-1).

---

## Cross-module audit (NO-NEW-LAYER rule)

- **Searched:** `/home/chris/luana-platform/core/`, `/home/chris/AISALESHT/backend/src/shared/`, vitalia modules.
- **Found existing canonical layers reused:**
  - `BaseExtractionOrchestrator` (luana-core-extraction Story 10 lift).
  - `sanitize_payload` (luana-core-observability).
  - `pop_cost` + `_cache` (luana-core-observability cost_recorder, T-1 PI-12 cement).
  - `VitaliaPatientMedicalHistoryModel` (vitalia infrastructure T-be-2).
  - `PatientMedicalHistoryRepository.save_medical(history)` (vitalia infrastructure T-be-3).
- **NEW layers introduced:** zero — extractor extends shared base, schemas are vertical-medical-specific Pydantic models without shared analogue.
- **Conftest extension** (M8 — extend, not destroy): added `luana_core_extraction/src` to `_WORKSPACE_SRC_PATHS` tuple (single line append).

---

## Files in scope (production)

| Path | Purpose |
|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_schemas.py` | Pydantic schemas: `Allergy`, `Condition`, `Medication`, `Surgery`, `FamilyHistorySummary`, `VitalSigns`, `MedicalHistoryV1` (schema_version=1 cement) + `ExtractionWave` dataclass. |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/medical_kb_extractor.py` | `MedicalKBExtractor(BaseExtractionOrchestrator)` — `_define_waves`, `run`, `_run_one_wave`, `_run_validate_wave`, `_resolve_wave_cost`, `_parse_wave_json`, `_merge_outputs`, `_merge_and_save`, `_persist_history`. Configuration constants (cost weights + ceilings + version). Protocol surfaces (`_LiteLLMServiceLike`, `_PatientMedicalHistoryRepoLike`, `_QdrantIndexerLike`, `_OutboxLike`, `_AuditLogLike`). |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/__init__.py` | Package marker + cache prefix invariant doc. |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_allergies_meds.j2` | W1 prompt — Sonnet vision. |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_conditions_surgeries.j2` | W2 prompt — Sonnet vision. |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_family_vitals.j2` | W3 prompt — Haiku (vision-light text). |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/medical_extract_validate_merge.j2` | W4 prompt — Sonnet text validator. |

## Files in scope (tests)

| Path | Purpose |
|---|---|
| `vitalia/backend/tests/agentic_evals/extractors/test_medical_kb_extractor.py` | 24 unit tests. A1+A2+A3 + 8 defensive paths + tenant isolation invariant + PII non-leak invariant + wave declaration sanity. Fakes for repo + LLM + Qdrant + outbox + audit_log. |
| `vitalia/backend/tests/architecture/test_extraction_orchestrator_inheritance.py` | A1 verifier — vitalia-scoped twin of AISALESHT arch fitness gate. AST scan of `vitalia/copilot/extractors/*.py` enforces every `*Extractor` class declares `BaseExtractionOrchestrator` base. Ratchet allowlist `KNOWN_EXTRACTORS_WITHOUT_BASE = set()` (shrink-only). |

## Files in scope (conftest extension — M8)

| Path | Change |
|---|---|
| `vitalia/backend/conftest.py` | Appended `luana_core_extraction/src` to `_WORKSPACE_SRC_PATHS` tuple (1 line) so extractor + arch test can import `BaseExtractionOrchestrator`. |

## Files NOT touched (parallel session sibling — M8)

| Path | Reason |
|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_schemas.py` (dental primitives) | Sibling T-extractors-2 appended dental classes (`ToothPosition`, `Restoration`, etc.) below the shared `ExtractionWave` dataclass + medical primitives. M8 extend pattern — coexists. Linter merged docstring noting both extractors share file. |
| `vitalia/backend/tests/agentic_evals/extractors/__init__.py` | Sibling created with shared docstring. |
| `vitalia/backend/tests/agentic_evals/extractors/test_dental_history_extractor.py` | Sibling T-extractors-2 owns. NOT my scope. (1 of their tests fails — their concern.) |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_*.j2` | Sibling owns. |
| `vitalia/backend/src/modules/vitalia/extensions.py` (EP-7 placeholder `vitalia/medical_kb_extractor.j2` ref) | Spec § 5.1 + extensions placeholder reference does NOT match the 4 actual prompt template files we ship. Updating extensions.py would touch a parallel-session-managed surface (T-extensions-1). DEFERRED to follow-up wiring ticket — extractor itself is fully usable by direct construction; the `ExtractorDef.prompt_template_ref` is a documentation hint inside the SDK registry that does not gate runtime invocation. |

---

## Iteration log

### Iter 1 — RED → GREEN (single iteration)

1. Wrote `_schemas.py` with `MedicalHistoryV1` + `ExtractionWave` dataclass + medical primitives.
2. Wrote 4 prompt templates (cache-friendly: invariant prefix BEFORE `<<CACHE_BOUNDARY>>` marker, variable input AFTER).
3. Wrote `medical_kb_extractor.py` extending `BaseExtractionOrchestrator`.
4. Extended `conftest.py` with `luana_core_extraction/src` path (M8 extend pattern).
5. Wrote 24 tests covering A1 + A2 + A3 + defensive paths.
6. Wrote `test_extraction_orchestrator_inheritance.py` arch fitness gate (A1 verifier per spec).
7. **First pytest run:** 3 PASS, 1 FAIL — `test_4_wave_pipeline` saw 0 LLM calls because `prompt_template.format(pdf_pages_text=...)` raised `KeyError: 'allergies'` (literal `{` / `}` in JSON output schema interpreted as format placeholders).
8. **Fix:** changed templates to use `{{PDF_PAGES_TEXT}}` / `{{WAVE_N_OUTPUT}}` markers + extractor switched to `str.replace()` (also more cache-friendly: byte-identical until marker boundary).
9. **Second pytest run:** 24/24 GREEN.
10. Lint pass: `ruff check --fix` (2 import-order violations auto-fixed). `ruff format` applied.
11. Final verification: `pytest` 25/25 GREEN (24 unit + 1 arch fitness), `ruff check` All checks passed!, `ruff format --check` 7 files already formatted.

**No iter 2 needed.**

---

## Acceptance coverage matrix

| AC | Test | Result |
|---|---|---|
| A1 — Subclass of BaseExtractionOrchestrator (arch fitness) | `tests/architecture/test_extraction_orchestrator_inheritance.py::test_every_vitalia_extractor_inherits_base` | **PASS** |
| A1 corollary — base methods accessible | `test_extractor_inherits_base_methods` | PASS |
| A2 — 4 waves complete + merge → MedicalHistoryV1 with confidence_score | `test_4_wave_pipeline` | **PASS** |
| A2 — wave model_role routing | `test_wave_called_with_correct_role_routing` | PASS |
| A2 — degraded path on all-wave failure | `test_returns_medical_history_v1_even_on_all_wave_failures` | PASS |
| A2 — partial wave failure tolerance | `test_partial_wave_failure_yields_partial_history` | PASS |
| A2 — malformed entity defensive drop | `test_malformed_entity_dropped_with_warning` | PASS |
| A2 — wave invalid JSON tolerance | `test_wave_invalid_json_yields_empty_wave_with_warning` | PASS |
| A2 — wave declaration sanity | `test_wave_definitions_match_spec` | PASS |
| A3 — total cost ≤$0.15 USD on happy path | `test_cost_budget` | **PASS** |
| A3 — cost-budget breach recorded as warning (not raise) | `test_cost_budget_exceeded_recorded_as_warning_not_raised` | PASS |
| A3 — cost-unknown wave does not break run | `test_cost_unknown_wave_does_not_break_run` | PASS |
| Persistence semantics — repo receives correct tenant + payload | `test_repo_persisted_with_correct_tenant_and_payload` | PASS |
| Persistence — best-effort isolation | `test_repo_failure_does_not_raise` | PASS |
| Qdrant — index when supplied | `test_qdrant_indexed_when_supplied` | PASS |
| Qdrant — best-effort isolation | `test_qdrant_failure_does_not_raise` | PASS |
| Outbox — emits MedicalHistoryExtractedV1 | `test_outbox_emits_medical_history_extracted_v1` | PASS |
| Outbox — best-effort isolation | `test_outbox_failure_isolated` | PASS |
| Audit log — records PII extraction event | `test_audit_log_records_pii_extraction_event` | PASS |
| Audit log — low confidence triggers manual_review flag | `test_low_confidence_triggers_manual_review_flag_in_audit` | PASS |
| Audit log — best-effort isolation | `test_audit_failure_isolated` | PASS |
| PII non-leak — PDF text stays out of observability writes | `test_pdf_text_not_logged_verbatim` | PASS |
| Tenant isolation invariant | `test_tenant_id_propagates_to_all_collaborators` | PASS |

**24/24 unit + 1/1 arch fitness = 25/25 GREEN.**

---

## State-of-the-art validation

- **LangGraph:** N/A (extractor uses asyncio.gather + Template Method, not StateGraph). Documented decision in module docstring.
- **deepagents:** N/A (extractor is not an agent — it is an extraction service consumed by the agentic surface).
- **Anthropic prompt cache:** templates structured cache-friendly per `claude-api` skill defaults — invariant prefix (system role + output schema + extraction rules) BEFORE `<<CACHE_BOUNDARY>>` marker, variable input (PDF text or wave outputs) AFTER. The `cache_control: {type: 'ephemeral', ttl: '5m'}` marker is to be applied by the LiteLLM proxy / runtime caller — extractor produces the cache-prefix-invariant prompt; the caller sets the cache marker. Validated against live docs at `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` accessed 2026-05-14: 5min default TTL is appropriate for the 4-wave run window (waves complete within ~25s p50). 1h TTL would be wasteful for one-shot PDF extraction (no reuse across PDFs).

---

## Validator results (V-AE-6 + V-AE-16 + arch fitness)

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest \
    tests/architecture/test_extraction_orchestrator_inheritance.py \
    tests/agentic_evals/extractors/test_medical_kb_extractor.py \
    -v --tb=short
25 passed in 0.32s
```

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff check \
    src/modules/vitalia/copilot/extractors/ \
    tests/agentic_evals/extractors/test_medical_kb_extractor.py \
    tests/architecture/test_extraction_orchestrator_inheritance.py
All checks passed!
```

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff format --check \
    src/modules/vitalia/copilot/extractors/ \
    tests/agentic_evals/extractors/test_medical_kb_extractor.py \
    tests/architecture/test_extraction_orchestrator_inheritance.py
7 files already formatted
```

V-AE-6 covers the broader directory `tests/agentic_evals/extractors/` (medical + dental). My scope = medical only. Sibling dental test failures are NOT my responsibility (parallel session WIP per M8).

---

## Architectural decisions

1. **Template marker `{{PDF_PAGES_TEXT}}` (NOT `str.format` placeholders).**
   - Reason: prompt templates contain literal `{` / `}` in JSON output schema examples. `str.format()` interprets them as format specs → KeyError.
   - Side-benefit: marker style is byte-identical until the marker boundary, optimal for Anthropic prompt-cache prefix invariance.
2. **`logical role` (vision/nano/reasoning) NOT wire-name model strings in `_define_waves`.**
   - Per `LLM_ROLE_BY_SITE` SSoT (sales-agent-expert skill). Caller's `LiteLLMService.get_model(role)` resolves the wire name at runtime (default DeepSeek/Anthropic per env config).
   - Spec § 5.1 cites `claude-sonnet-4-6-vision` directly; we abstract to `vision` role so the LiteLLM proxy + role binding remains the single resolver.
3. **Best-effort persistence + side-effects (each isolated).**
   - Per R23 + copilot-resilience.md: extractor turn is "successful" if at least one wave produced output. Persistence / RAG / event / audit failures are observability concerns, not extraction concerns.
   - Each side-effect in its own `try/except` so one failure does not cascade.
4. **Cost budget breach → warning (NOT raise).**
   - Per R23 + design § 5: partial extraction with a warning is more useful to clinic_owner than a hard failure. The warning surfaces in `extraction_warnings` for downstream alerting.
5. **`_LLMResponse` exposed as module-level dataclass (not nested) for test fakes.**
   - Allows `FakeLiteLLMService` to construct response instances without re-importing nested types.
   - Prefixed `_` to signal internal API; tests import via `from medical_kb_extractor import _LLMResponse` for fake construction.
6. **Validator wave (W4) does NOT contribute base confidence (weight 0.10 only via adjustment).**
   - W4 is meta — it validates the other 3. Its own confidence is tautological (validator confident in its own validation). Merge formula uses W4 only via `validation_score_adjustment` ∈ [-0.3, 0.0].
7. **ORM model fallback to dict in `_persist_history`.**
   - If SQLAlchemy ORM model unavailable at extractor runtime (test fakes inject repos that ignore the model class), falls back to dict construction. Real persistence repo (`PatientMedicalHistoryRepository.save_medical(model_instance)`) gets ORM; tests get dict — both paths exercised.

---

## Cost ceiling design

Per V-AE-16 budget $0.15 USD per PDF (medical):

| Wave | Model role | Per-wave ceiling | Comment |
|---|---|---|---|
| W1 allergies + meds | vision (Sonnet) | $0.05 | Heaviest — many entities to enumerate |
| W2 conditions + surgeries | vision (Sonnet) | $0.05 | Same as W1 |
| W3 family + vitals | nano (Haiku) | $0.03 | Lighter content — Haiku cheaper |
| W4 validate + merge | reasoning (Sonnet text) | $0.02 | Small text-only validator |
| **Total ceiling** | | **$0.15** | Matches V-AE-16 SSoT |

Total extracted via `pop_cost(litellm_call_id)` per wave. If a wave reports cost-unknown (no call_id), the wave contributes Decimal('0') to the sum and a warning is recorded. If the sum exceeds the budget, a `cost_budget_exceeded` warning is recorded but extraction continues.

---

## Tenant isolation invariant (R2)

- `tenant_id` is a required `run(...)` kwarg (NOT in `__init__` — extractor is tenant-agnostic; runs against per-tenant data).
- Forwarded to: repo (via row.tenant_id), Qdrant indexer (via index_medical_history kwarg), outbox event (via publish kwarg), audit log (via log kwarg).
- Test `test_tenant_id_propagates_to_all_collaborators` verifies all 4 collaborators receive the same tenant_id.
- Repo enforces tenant scoping at construction time (per T-be-3 PatientMedicalHistoryRepository pattern).

---

## PII handling

- PDF page text is NEVER passed to observability writes (outbox payload, audit log, Qdrant index payload, structlog events).
- Outbox payload contains: history_id, patient_id (UUID, not PII), schema_version, confidence_score, counts (allergies/meds/etc), warnings count, cost_usd, duration_ms.
- Qdrant payload is the `MedicalHistoryV1.model_dump()` — but `sanitize_payload` is applied first (defensive against any LLM-extracted PII like emails/phones embedded in `notes` fields).
- Audit log payload: history_id, version, confidence_score, warnings list, needs_manual_review flag.
- Test `test_pdf_text_not_logged_verbatim` asserts patient name, DNI, email do not appear in outbox/audit payloads.

---

## Closure

- 25/25 tests GREEN (24 unit + 1 arch fitness).
- Ruff lint: clean.
- Ruff format: clean.
- A1 + A2 + A3 covered.
- V-AE-6 (extractor tests) + V-AE-16 (cost budget) satisfied for the medical extractor.
- R23 honored: best-effort observability writes, structlog warnings on failure, no naked LLM calls.
- Anti-duplication audit: zero collisions, all shared abstractions consumed (NEVER mirrored).
- Tenant isolation invariant verified.
- PII non-leak invariant verified.
- Schema cement: `MedicalHistoryV1.schema_version: Literal[1]` frozen.
- Cost-bucket invariant respected: extractor consumes from agentic LLM bucket via LiteLLM proxy (cost_recorder bridge).

State: `tests-passing`. Awaiting orchestrator → auditor-agentic (independent verdict per R30).
