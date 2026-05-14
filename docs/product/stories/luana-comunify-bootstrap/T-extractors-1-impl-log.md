# T-extractors-1 — impl-log

> Story: luana-comunify-bootstrap · Ticket: T-extractors-1 · Surface: AGENTIC ·
> R23 Opus 4.7 production code · Date: 2026-05-14

## Phase 0 — Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Extractor lives in `modules/comunify/copilot/extractors/` — verified anti-duplication cardinal rule (no mirror of vitalia primitives without N=2+ shared lift), best-effort observability writes with `try/except + structlog.warning`, PII via `sanitize_payload` (lazy import fallback mirror of `qualify_for_cohort.py`). | EXTEND from `BaseExtractionOrchestrator` (canonical shared abstraction in `luana_core_extraction`), keep `_LLMResponse` + `LLMClientProtocol` inline (N=2 today — flagged for future lift after T-extractors-2). |
| `sales-agent-expert` | Not directly applicable (extractor is offline batch analysis, not a sales conversation turn). § 0 anti-duplication cardinal still consulted. | Confirm: no shared abstraction collision; extractor outputs structured data, not voice — no Slot 5 BRAND_VOICE concern. |
| `tessl__langgraph` | Not applicable — this is a wave-based extractor inheriting `BaseExtractionOrchestrator`, NOT a LangGraph `StateGraph`. T-workflows-1/2 land LangGraph state machines later. | N/A — confirmed wave-based pattern is the spec (03-arch-agentic § 5.1). |
| `tessl__graceful-degradation` | Every LLM call wraps `asyncio.wait_for` with `wave.timeout_sec + 2.0s` guard around the LiteLLM-internal timeout. Per-wave exception isolation: each wave is caught individually, returning empty payload + warning. Cost-recorder + sanitize_payload have ImportError fallbacks. Side-effect collaborators (advice_repo, qdrant, outbox, audit_log) each in their own try/except — failure of one MUST NOT block others. | Implemented with isolated per-wave + per-side-effect try/except — see `_run_one_wave` + `_merge_and_save`. Cost-unknown path documented (`None` not 0 — avoids masking drift). |
| `tessl__pytest-api-testing` | Async fakes via `@dataclass` factory pattern. asyncio_mode=auto inherited from comunify `pyproject.toml`. Spec-driven `FakeLLMResponseSpec` for per-wave behavior (cost, latency, exceptions). | Tests are 100% in-memory (no DB, no network). Cost cache seeded via direct `cost_recorder._cache` access (mirror vitalia test pattern). |
| `tessl__fastapi` | N/A — no FastAPI route in this ticket. Future ticket may expose `POST /api/v1/comunify/copilot/offer-ladder/advise` as the entry point. | N/A. |

## Phase 0.5 — Default-flip detection

Not applicable — this ticket does NOT touch `core/config.py` defaults nor any
feature flag. Pure NEW code in `modules/comunify/copilot/extractors/`.

## Phase 1 — Cross-module systems audit (NO-NEW-LAYER + anti-duplication)

### Grep audit (Step 0 GATE)

```bash
grep -rn "class OfferLadderAdvisor\|class OfferLadderAdviceV1\|class LadderGap\|class SuggestedOffer\|class TierOptimization" /home/chris/luana-platform/ /home/chris/AISALESHT/
# → only docs/product/stories/.../02-design-agentic.md + 03-arch-agentic.md (spec)
# Zero code collisions. All NEW symbols.

find /home/chris/luana-platform -name "base_orchestrator.py"
# → /home/chris/luana-platform/core/luana-core-extraction/src/luana_core_extraction/base_orchestrator.py
# → /home/chris/luana-platform/nicolify/backend/src/shared/application/extraction/base_orchestrator.py
# Canonical: luana_core_extraction (workspace package).
```

### Inventory lookup (`.claude/rules/anti-duplication.md`)

| Subsystem | Canonical path | Decision |
|---|---|---|
| Wave-based LLM extraction | `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` | EXTEND (consume `_run_wave`/`_pause_between_waves`/`_announce_sections`). |
| PII sanitization | `luana_core_observability.recording.sanitization.sanitize_payload` | EXTEND via lazy import + truncate fallback (mirror `qualify_for_cohort.py`). |
| Cost recovery | `luana_core_observability.recording.cost_recorder.pop_cost` | EXTEND via lazy import (same fallback pattern). |
| `_LLMResponse` dataclass | vitalia precedent (sibling extractor module) | KEEP INLINE (N=2: comunify + vitalia). Lift to `luana_core_extraction.types` when 3rd vertical surfaces. |
| `LLMClientProtocol` (`_LiteLLMServiceLike`) | `modules/comunify/agentic/tools/qualify_for_cohort.py` (sibling consumer in this same repo) | KEEP INLINE for now (N=2 within comunify). FLAG: anti-duplication threshold reached — escalate `/pm` to lift into shared comunify module-level protocol in next ticket. |

### Files in scope (ticket spec verbatim)

- `comunify/backend/src/modules/comunify/copilot/extractors/offer_ladder_advisor.py` — NEW
- `comunify/backend/tests/agentic_evals/extractors/test_offer_ladder_advisor.py` — NEW

### Additional files touched (extension of scope, justified)

- `comunify/backend/src/modules/comunify/copilot/extractors/_schemas.py` — NEW. Pydantic
  primitives (`OfferLadderAdviceV1`, `LadderGap`, `SuggestedOffer`, `TierOptimization`,
  `ExtractionWave`). Mirrors vitalia `_schemas.py` pattern. Required by the
  extractor's `output_schema` declaration + tests assertions.
- `comunify/backend/tests/agentic_evals/extractors/__init__.py` — NEW package marker.

The `_schemas.py` addition is a structural prerequisite — the alternative
(inlining 5 Pydantic models in the extractor module) violates anti-pollution.
Vitalia precedent: `vitalia/.../extractors/_schemas.py` holds MedicalHistoryV1 +
DentalHistoryV1 primitives.

## Phase 2 — Implementation (Inside-Out)

### Domain primitives (`_schemas.py`)

| Symbol | Role |
|---|---|
| `ExtractionWave` (dataclass frozen) | Per-wave config (name + model_role + timeout_sec). Mirror vitalia. |
| `LadderGap` (Pydantic frozen + Literal level enum) | Detected missing ladder level + reasoning + priority. |
| `SuggestedOffer` (Pydantic frozen + Literal target_level enum + fit_score 0..1) | Candidate offer per gap. |
| `TierOptimization` (Pydantic frozen + Literal progression_quality enum) | Pricing + positioning analysis. |
| `OfferLadderAdviceV1` (Pydantic non-frozen + `schema_version: Literal[1]`) | Top-level extractor output. Schema cement per Story D playbook. |

All Pydantic models use `model_config = ConfigDict(frozen=True, extra="forbid")`
except `OfferLadderAdviceV1` which is non-frozen so caller can populate after
`__init__` if needed (matches vitalia `MedicalHistoryV1`). Schema migrations
must go to a NEW `V2` class — NEVER mutate `V1`.

### Infrastructure (none — extractor is application-layer)

No SQL models, no migrations, no repos. The `comunify_offer_ladder_advice`
persistence table is documented in 02-design § 7.1 as a side-effect target but
NOT yet materialized in alembic (no `T-be-N` ticket created it). The extractor
accepts an optional `advice_repo` protocol so a future migration can wire it
up without re-touching the extractor (D1 DI).

### Application (extractor)

`OfferLadderAdvisor(BaseExtractionOrchestrator)`:

- `_define_waves()` returns 4 `ExtractionWave` configs matching § 5.1:
  - W1 `analyze_current_offers` — `reasoning` (Sonnet 4.6), ≤30 s
  - W2 `detect_ladder_gaps` — `reasoning` (Sonnet 4.6), ≤30 s
  - W3 `generate_suggestions` — `nano` (Haiku 4.5), ≤30 s
  - W4 `validate_and_merge` — `reasoning` (Sonnet 4.6), ≤25 s
- `run(*, tenant_id, current_offers, creator_niche, country)` — entry point.
  Returns `OfferLadderAdviceV1` (never None, never raises).
- `_run_one_wave(wave, *, prompt_inputs, on_exception)` — executes 1 wave with
  `asyncio.wait_for(..., wave.timeout_sec + 2.0)` guard. Catches all exceptions,
  returns dict with `parsed` (empty if failed), `cost_usd` (Decimal('0') if
  unknown), `error` (None or summary). Logs warnings on every degraded path.
- `_resolve_wave_cost(response, *, wave_name)` — bridges LiteLLM CustomLogger
  via `pop_cost(call_id)`. Returns `None` when call_id missing (avoids masking
  cost-tracking drift — never default to 0).
- `_parse_wave_json(content, *, wave_name)` — tolerant JSON parser; strips
  markdown code fences defensively.
- `_merge_outputs(...)` — composes `OfferLadderAdviceV1` from the 4 wave
  payloads. Per-entity defensive construction (`_parse_list` + `_parse_optional`)
  drops malformed items + records warnings.
- `_merge_and_save(...)` — 4 isolated best-effort side-effects:
  1. `advice_repo.save_advice(row)` — persists advice payload (when supplied).
  2. `qdrant_indexer.index_offer_ladder_advice(...)` — RAG index (when supplied).
  3. `outbox.publish(event_type="OfferLadderAdviceGeneratedV1", ...)`.
  4. `audit_log.log(event_type="offer_ladder_advice_generated", ...)`.
  Each in its own try/except — failure of one does NOT block others.

### Prompt cache architecture (cache-prefix friendly)

Inline prompt templates (`_WAVE_PROMPTS` dict at module scope) use `<<MARKER>>`
substitution boundaries — caller swaps via `str.replace`. This keeps the cache
prefix byte-identical across calls until the marker boundary (Anthropic prompt
caching invariant). Variable inputs (offers JSON, creator_niche, country, wave
outputs) sit AFTER the markers.

NB: prompts are intentionally INLINE in this ticket (not externalised to a
`_prompts/` Jinja dir like vitalia) to respect `files_in_scope: 2`. A future
ticket can lift them when T-extractors-2 (AuthorityVaultExtractor) lands and
both extractors gain by sharing the prompt-load infrastructure.

### Confidence aggregation

Weighted sum across waves (`_WAVE_CONFIDENCE_WEIGHTS`: 0.30/0.30/0.30/0.10) +
validator adjustment (bounded `[-0.3, 0.0]`). Wave 4 only contributes via the
adjustment (it's a meta-validator), NOT via base weight on its own confidence.

### Cost budget enforcement

Total cost summed across waves; if `> _cost_budget_usd` (default `0.10 USD`),
records `cost_budget_exceeded` warning but DOES NOT raise. Caller can lower
budget via `cost_budget_usd=Decimal("0.05")` constructor kwarg.

### Empty ladder graceful path

`current_offers == []` → flag `empty_ladder=true` in wave 1 prompt; appends
advisory warning `no_offers_yet:suggest_level_1_first` to output. All 4 waves
still run (creator_niche + country still inform bootstrap suggestions).

## Phase 3 — Tests (30 cases, all GREEN)

| Group | Cases | Coverage |
|---|---|---|
| Acceptance A1 — subclass invariant | 4 | `issubclass(OfferLadderAdvisor, BaseExtractionOrchestrator)`, base methods inherited, log_prefix specific, wave definitions match § 5.1 spec |
| Acceptance A2 — 4 waves + merge | 5 | Happy path 4 LLM calls + 6 suggestions + 2 gaps + confidence ≥0.85; role routing (3 reasoning + 1 nano); all-wave-fail returns degraded V1; partial-wave-fail yields partial V1; malformed entity dropped + warning |
| A2 corollary — JSON robustness | 1 | Wave returns non-JSON → empty wave + warning, other waves intact |
| Acceptance A3 — cost ≤$0.10 | 3 | Happy path under budget; exceeded → warning not raised; cost-unknown wave doesn't break run |
| Acceptance A4 — empty ladder | 1 | 4 gaps + bootstrap suggestion + `no_offers_yet` warning |
| Acceptance A5 — tenant isolation | 2 | tenant_id propagates to repo + qdrant + outbox + audit; two consecutive runs don't leak across tenants |
| Persistence + side-effects | 8 | repo persisted with correct payload; repo failure isolated; qdrant indexed when supplied; qdrant failure isolated; outbox `OfferLadderAdviceGeneratedV1` event; outbox failure isolated; audit records event; low-confidence flags needs_manual_review; audit failure isolated |
| Schema cement | 3 | `schema_version == Literal[1]` frozen; `LadderGap` enum cement (invalid level rejected); `SuggestedOffer` enum cement; `TierOptimization` defaults |
| DI sanity | 1 | `offer_ladder_repo` handle accepted but not mutated by extractor |
| Total | 30 | |

```bash
cd /home/chris/luana-platform/comunify/backend && \
  .venv/bin/pytest tests/agentic_evals/extractors/test_offer_ladder_advisor.py -v --tb=short
# → 30 passed in 0.13s
```

## Phase 4 — Downstream regression

Per `.claude/rules/auditor-downstream-regression.md` SSoT table, this ticket
touches `modules/comunify/copilot/extractors/` (NEW path — not listed yet in
table). Downstream consumers today:

- `tests/agentic_evals/kb_pack/test_seed_idempotent.py` (15 tests)
- `tests/agentic_evals/kb_pack/test_tenant_filter_at_query.py` (7 tests)
- `tests/agentic_evals/kb_pack/test_vulnerable_disclosure_forced.py` (7 tests)
- `tests/agentic_evals/tools/test_*.py` (4 tool test files)

```bash
cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/ --tb=short
# → 166 passed in 0.44s   (was 136 pre-ticket — +30 new, 0 regression)
```

## Phase 5 — Quality gates

| Gate | Command | Result |
|---|---|---|
| Ruff lint | `cd backend && .venv/bin/ruff check src/.../extractors/ tests/.../extractors/ --no-cache` | All checks passed |
| Ruff format | `cd backend && .venv/bin/ruff format --check src/.../extractors/ tests/.../extractors/` | 6 files already formatted |
| Pytest extractors | `pytest tests/agentic_evals/extractors/test_offer_ladder_advisor.py -v` | 30/30 PASS |
| Pytest agentic_evals suite | `pytest tests/agentic_evals/` | 166/166 PASS |

Tests run in 0.13 s (in-memory fakes, no DB / no network / no live LLM).

## Skills validation summary

R23 owner_eligibility = `[opus]` — production AGENTIC code. Opus 4.7 used.

All applicable skill decisions captured above. No skill skipped — `tessl__langgraph`
+ `tessl__fastapi` explicitly N/A and documented.

## Anti-duplication audit (Phase 2 audit verbatim, repeated for auditor)

| File | Cross-codebase grep | Verdict |
|---|---|---|
| `offer_ladder_advisor.py` | `grep -rn "class OfferLadderAdvisor"` → only spec MDs | NEW symbol |
| `_schemas.py` | `grep -rn "class OfferLadderAdviceV1\|class LadderGap\|class SuggestedOffer\|class TierOptimization"` → only spec MDs | NEW symbols |
| `ExtractionWave` (in `_schemas.py`) | Mirror of vitalia primitive — sibling extractor module, brand-isolated | DOCUMENTED per anti-duplication.md row ("vertical primitives stay local; mechanics consumed from BaseExtractionOrchestrator") |
| `_LLMResponse` dataclass | Mirror of vitalia primitive | DOCUMENTED — lift candidate at N=3 |
| `_LiteLLMServiceLike` Protocol | Mirror of `qualify_for_cohort.py::_LLMClientLike` (same comunify module, N=2 within comunify) | DOCUMENTED — lift candidate FLAGGED (escalate /pm next ticket) |
| `_sanitize_payload` lazy import + fallback | Mirror of `qualify_for_cohort.py::_sanitize_payload` | DOCUMENTED — same N=2 lift flag |

Lift candidates DO NOT block this ticket. They are flagged in inline docstrings
+ here for the auditor + next ticket (`/pm` decides scope).

## Closure

T-extractors-1 ships:

- `OfferLadderAdvisor` extends `BaseExtractionOrchestrator` (R10 anti-dup
  cardinal honored).
- 4-wave pipeline (Sonnet/Sonnet/Haiku/Sonnet) per § 5.1.
- `OfferLadderAdviceV1` Pydantic frozen `schema_version: Literal[1]`.
- Cost budget ≤$0.10 USD enforced as warning (V-AE-8 SSoT).
- Cross-tenant isolation: tenant_id forwarded to every collaborator.
- Empty-ladder graceful path: 4-gap bootstrap.
- Schema cement: V1 Literal frozen, V2 reserved for future schema migration.
- 30 tests GREEN.
- 0 lint / format / regression issues.

Blocks resolved: T-eval-1 (next ticket) can now reference `OfferLadderAdvisor`
in agentic eval suite + cost_budget tests.
