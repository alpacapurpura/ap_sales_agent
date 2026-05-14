# T-extractors-2 — DentalHistoryExtractor (R23 Opus 4.7) — impl log

Date: 2026-05-14
Owner: Claude Opus 4.7 (1M context)
Story: luana-vitalia-bootstrap (Story 11) Sesion 4 W4
Surface: AGENTIC `production_code: true` — Opus EXCLUSIVE per R23
Decisions: D1 (vertical-medical DDD)
Validators: V-AE-6 (extractor wave + merge tests) + V-AE-16 (cost ≤$0.18/PDF)
Sibling parallel: T-extractors-1 (MedicalKBExtractor, written concurrently in W4)

## Skills consulted

| Skill | Section invoked | Decision |
|---|---|---|
| `copilot-expert` | "Anti-duplication cardinal" + "Cuándo extender (no parchear)" + "Cost guards" | EXTEND `BaseExtractionOrchestrator` (anti-duplication SSoT row); 4 waves + per-wave timeout + degraded-confidence error mode (graceful degradation pattern); cost ceiling cement at $0.18 |
| `sales-agent-expert` | "Anti-duplication cardinal" inventory | Confirmed `sanitize_payload` lives in `luana_core_observability.recording.sanitization` — consumed not re-implemented (PII regex SSoT) |
| `tessl__langgraph` | "Conditional Branching" + "Anti-Patterns: Infinite Loop Without Exit" | Wave count is class-scope frozen (4) — no cycles, no infinite loop possible. State machine fundamentals not applicable here (extractor is sequential pipeline, not StateGraph; LangGraph applies to T-workflow-1 TreatmentFollowupWorkflow downstream) |
| `tessl__graceful-degradation` | "Rule 1: every external call needs a timeout" + "Rule 2: every timeout needs a fallback" + "Rule 5: per-dependency error isolation" | Per-wave `asyncio.wait_for` with `timeout_sec` from `ExtractionWave` config; on timeout → log warning + decrement confidence + continue (NOT crash); Qdrant indexing best-effort (failure → log + continue); persistence is the only critical dependency (failure → bubble up, no event published) |
| `tessl__pytest-api-testing` | "Factory Fixtures" + "Mocks vs monkeypatch" + "parametrize for Edge Cases" | `_build_extractor_with_fakes()` builder pattern (DI); `AsyncMock` for collaborators; FDI validation parameterized via Pydantic field_validator |
| `tessl__fastapi` | n/a | No FastAPI route surface — extractor invoked from upload pipeline (T-be-7 wires the route) |

## Step 0 anti-dup grep (per `.claude/rules/anti-duplication.md` + sales-agent-expert + copilot-expert §0)

```bash
grep -rn "DentalHistoryExtractor\b\|DentalHistoryV1\b\|class FDI\|FDIPosition\|ToothPosition\b" \
  /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# → Only design doc references + medical_history_model.py columns. Zero class collisions.

grep -rn "BaseExtractionOrchestrator\b" /home/chris/luana-platform/vitalia/backend/src/
# → Empty. We are the first vitalia subclass (sibling MedicalKBExtractor lands T-extractors-1).
```

PASS — `DentalHistoryExtractor` + `DentalHistoryV1` + `ToothPosition` are NEW symbols. No mirror risk.

## Cross-module systems audit (NO-NEW-LAYER per architect rule)

- `BaseExtractionOrchestrator` lives in `core/luana-core-extraction/src/luana_core_extraction/base_orchestrator.py` (shared SSoT row in anti-duplication.md). EXTENDED by subclassing — no new orchestrator base.
- `ExtractionWave` dataclass already defined in sibling `_schemas.py` by T-extractors-1 (parallel W4). REUSED — appended `DentalHistoryV1` + dental primitives to same file (M8 extend pattern).
- `sanitize_payload` consumed from `luana_core_observability.recording.sanitization` — NEVER re-implemented. Extractor adds a structural-key pre-strip layer (`_strip_pii_keys`) for vertical-medical PII surface (DNI / address / DOB) that bare regex misses without keyword anchor — this is defense in depth complementing (not replacing) the shared regex.
- `VitaliaPatientDentalHistoryModel` ORM model already exists in `infrastructure/models/medical_history_model.py` from T-be-2. Repository protocol consumed (no new model created).

## Files written / modified

| Path | Action | Notes |
|---|---|---|
| `vitalia/backend/conftest.py` | EXTEND | Appended `luana-core-extraction/src` to `_WORKSPACE_SRC_PATHS` (M8 extend, parallel-safe with T-extractors-1) |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_schemas.py` | EXTEND | Appended `ToothPosition` + `Restoration` + `PeriodontalSummary` + `BiteAlignmentNotes` + `RadiographRef` + `DentalHistoryV1` (T-extractors-1 owns medical primitives above; both share `ExtractionWave`) |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/dental_history_extractor.py` | NEW (461 lines) | `DentalHistoryExtractor` extends `BaseExtractionOrchestrator`; 4 waves; cost guard; per-tenant Qdrant collection; `DentalChartReadyV1` event; PII sanitization defense in depth |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_missing_pieces_chart.j2` | NEW | Wave 1 vision prompt — FDI 11-48 quadrant rules; cache-prefix invariant (no PII in prompt body) |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_restorations_and_periodontal.j2` | NEW | Wave 2 vision prompt — restoration types + periodontal summary |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_bite_and_radiographs.j2` | NEW | Wave 3 Haiku-vision prompt (cheaper) — bite alignment + radiograph types |
| `vitalia/backend/src/modules/vitalia/copilot/extractors/_prompts/dental_extract_validate_and_merge.j2` | NEW | Wave 4 reasoning prompt — confidence calc + cross-wave consistency check |
| `vitalia/backend/tests/agentic_evals/extractors/__init__.py` | NEW | Package marker |
| `vitalia/backend/tests/agentic_evals/extractors/test_dental_history_extractor.py` | NEW (~430 lines) | 10 tests: T1-T10 covering A1 (FDI), A2 (cost), wave def, schema shape, side-effects (event + persist), PII, tenant isolation, timeout degradation |

## Implementation chronology (TDD)

1. RED — wrote `test_dental_history_extractor.py` with 10 tests (T1-T10). All fail at collection (`ModuleNotFoundError: luana_core_extraction`).
2. EXTEND `vitalia/backend/conftest.py` adding `luana-core-extraction/src` to `_WORKSPACE_SRC_PATHS` (parallel-safe with T-extractors-1).
3. EXTEND `_schemas.py` with `_validate_fdi_code()` helper + `ToothPosition` + `Restoration` + `PeriodontalSummary` + `BiteAlignmentNotes` + `RadiographRef` + `DentalHistoryV1`. T2/T3/T5 GREEN.
4. WRITE `dental_history_extractor.py` with `DentalHistoryExtractor(BaseExtractionOrchestrator)`, 4 wave configs, `DentalChartReadyV1` dataclass, collaborator protocols (DI), cost helpers (`_aggregate_cost` / `_cost_overrun`), wave runner with `asyncio.wait_for` + degraded-confidence on timeout, merge-and-persist + Qdrant indexing + event emission, observability with sanitization. T1, T2, T4, T5, T6, T7, T9, T10 GREEN. T8 (PII) RED.
5. WRITE 4 j2 prompt templates (cache-prefix invariant — no `{tenant_name}`, no timestamps, no `{patient_id}` interpolation mid-block).
6. EXTEND `_sanitize_for_trace`: shared `sanitize_payload` is keyword-anchored for bare DNI digits (per S1 sales_agent design — protects against false positives on order_id/score). Added a structural-key pre-strip (`_strip_pii_keys`) covering medical-PII surface (DNI / email / address / DOB / national IDs) BEFORE delegating to shared regex. Defense in depth, NOT a replacement. T8 GREEN.
7. ruff `--fix` removed unused imports (smoke import duplicates) + `ruff format` re-formatted test file. All clean.

## Validators run

```bash
# Per ticket spec validator block (lines 933, V-AE-6 + V-AE-16):
cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
  tests/architecture/test_extraction_orchestrator_inheritance.py \
  tests/agentic_evals/extractors/test_dental_history_extractor.py \
  -v --tb=short
# → 11 passed (1 arch fitness + 10 dental tests)

cd /home/chris/luana-platform/vitalia/backend && uv run ruff check \
  src/modules/vitalia/copilot/extractors/dental_history_extractor.py \
  src/modules/vitalia/copilot/extractors/_schemas.py \
  tests/agentic_evals/extractors/test_dental_history_extractor.py
# → All checks passed!

cd /home/chris/luana-platform/vitalia/backend && uv run ruff format --check \
  src/modules/vitalia/copilot/extractors/dental_history_extractor.py \
  src/modules/vitalia/copilot/extractors/_schemas.py \
  tests/agentic_evals/extractors/test_dental_history_extractor.py
# → 3 files already formatted

# V-AE-6 full extractors directory (includes sibling T-extractors-1):
cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
  tests/agentic_evals/extractors/ -v --tb=short
# → 34 passed (10 dental + 12 medical + others — sibling T-extractors-1 wrote first)
```

## Downstream regression scope (R3 / `.claude/rules/auditor-downstream-regression.md`)

Surfaces touched + downstream test paths verified:

- `vitalia/backend/conftest.py` extended → all 287+ vitalia tests still collect cleanly (sys.path layering didn't shadow anything).
- `_schemas.py` extended → T-extractors-1 medical tests still GREEN (12/12) — primitives are namespaced, no collision.
- `dental_history_extractor.py` NEW → arch fitness `test_extraction_orchestrator_inheritance.py` passes for both medical + dental subclasses.

Full vitalia regression scan:
```
cd /home/chris/luana-platform/vitalia/backend && uv run pytest tests/ \
  --ignore=tests/architecture/test_vitalia_payment_inherits_core_base.py \
  --ignore=tests/unit/payment/test_mercadopago_adapter.py \
  --ignore=tests/integration --ignore=tests/e2e --tb=line
# → 353 passed, 3 skipped (no regressions; 2 ignored files have pre-existing
#    collection errors due to missing httpx + langchain_core — unrelated to T-extractors-2)
```

## Acceptance evidence

| ID | Description | Verifier | Evidence |
|---|---|---|---|
| A1 | FDI notation correctly parsed for `missing_pieces` | `test_dental_history_extractor.py::test_fdi_notation` | PASS — 8 valid codes accepted (11-18, 21-28, 31-38, 41-48), 13 invalid codes raise `ValidationError` (10/19/20/29/30/39/40/49/50/99/0/-1/100); end-to-end `DentalHistoryV1` shape verified. |
| A2 | Cost per PDF ≤$0.18 USD (vision-heavy bar) | `test_dental_history_extractor.py::test_cost_budget` | PASS — `COST_CEILING_USD_PER_PDF = 0.18` matches V-AE-16 threshold; `_aggregate_cost` sums correctly; `_cost_overrun` enforces ceiling symmetrically (sub-budget = False, hostile-PDF synthetic over = True). |
| § 5.3 inheritance gate | `DentalHistoryExtractor` subclass of `BaseExtractionOrchestrator` | `test_extraction_orchestrator_inheritance.py::test_every_vitalia_extractor_inherits_base` | PASS — sibling T-extractors-1 wrote the gate; my class declares `BaseExtractionOrchestrator` in `_ALLOWED_BASES`. |

## State-of-the-art validation (live docs check)

- LangGraph: extractor is sequential pipeline (not StateGraph) — LangGraph 2.0 patterns N/A here. State machine surface is `T-workflow-1 TreatmentFollowupWorkflow`. The `BaseExtractionOrchestrator` shared base predates LangGraph adoption; design uses `asyncio.gather` for intra-wave concurrency + sequential wave dispatch.
- Anthropic prompt caching: prompts are cache-prefix invariant (no `{tenant_name}`, no `{patient_id}`, no timestamps inside the prompt body — variable inputs are passed in the user message AFTER the cache_control marker by the LiteLLM proxy caller). Per `sales-agent-expert` slot 5 cache prefix discipline.
- deepagents: not used — extractor is a domain pipeline, no subagent isolation needed. Wave isolation is achieved by Pydantic validation + per-wave timeout + per-wave warning collection.

## Known gaps / future work

- **Cost recording integration**: extractor returns `wave_cost_usd` from the LLM service (the LiteLLM proxy CustomLogger already records this). Direct `copilot_llm_call` row writes are NOT in this ticket's scope — those land via the LiteLLM bridge in T-be-7 (route wiring) + future observability ticket.
- **Real LLM smoke run**: tests use `FakeLLM` returning canned wave outputs. End-to-end against a real Sonnet vision call is deferred to T-eval-1 (agentic eval suite).
- **Chart auto-rotation**: spec § 7.2 mentions "chart image rotation detection → auto-rotate retry". This is implemented as a wave-level warning ("rotated chart detected") — the actual auto-rotate retry would happen at the LiteLLM proxy / image preprocessing layer (out of extractor scope; documented as future work).
- **Pediatric dentition (FDI 51-85)**: explicitly out of scope per `_validate_fdi_code` docstring — Story 11.bis if needed.

## Self-audit checklist

- [x] Step 0 GATE — domain skills + cross-cutting skills invoked + decisions captured
- [x] Step 0 anti-dup grep — no class collision, no mirror risk
- [x] Cross-module audit done (NO-NEW-LAYER) — `BaseExtractionOrchestrator` extended via subclass
- [x] Inside-Out layers respected (domain `_schemas.py` → app `dental_history_extractor.py`)
- [x] Tenant isolation: `tenant_id` required in `run()`; embedded in Qdrant collection name; passed to repos
- [x] Conditional edges total — no infinite loops (4 waves frozen at class scope)
- [x] External calls wrapped: timeout (`asyncio.wait_for`) + fallback (degraded confidence + warning) + per-dependency isolation (Qdrant best-effort, persist critical)
- [x] LLM calls support `wave_cost_usd` accounting (LiteLLM CustomLogger bridge)
- [x] Trace events emitted (best-effort try/except + structlog warning) — PII sanitized via 2-layer scrub
- [x] Cache prefix slot architecture respected — no `{tenant_id}` / `{patient_id}` / timestamps in prompts (variables go AFTER cache_control marker via the caller)
- [x] Cache TTL choice deferred to T-be-7 (route wiring)
- [x] DentalHistoryV1 schema-cement (Story D playbook)
- [x] AsyncPostgresSaver checkpointer NOT applicable (not a LangGraph workflow — pipeline only)
- [x] Conventional Commits scoped (this commit will only touch the 8 files I created/extended)
