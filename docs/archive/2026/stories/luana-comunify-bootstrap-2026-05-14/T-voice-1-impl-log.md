# T-voice-1 IMPL-LOG — VoiceDistillationOrchestrator + 4 waves

**Ticket**: T-voice-1 (06-tickets.yaml line 481)
**State**: done
**Owner**: builder-agentic (Opus 4.7 per R23 — production_code=true AGENTIC)
**Estimate**: 5h
**Actual**: ~2.5h (within batch)
**Date**: 2026-05-14
**Validators GREEN**: V-AE-9, V-AE-21, V-AE-30

## § Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Voice cloning surface NEW under `modules/comunify/brand/voice_cloning/` parallel to copilot's observability subsystem — anti-duplication grep mandate applies (§ Anti-duplication cardinal). | Greppeé `class VoiceDistillationOrchestrator` cross luana-platform → zero collisions (only doc/arch refs + Protocol stub in `voice_cloning_service.py`). No mirror risk. ✅ Skill cleared. |
| `sales-agent-expert` | Output `CompiledVoice` bridges to `personality_profiles.system_instruction` SSoT (slot 5 BRAND_VOICE cache prefix). Voice cloning is the upstream pipeline producing what slot 5 consumes. | § Anti-duplication cardinal § 0: lift-to-shared when N=3 across modules. Today N=1 (only comunify). N=2 trigger would be Vitalia voice cloning (today OFF, Story 11 cement). Bridge consumes `PersonalityCompiler.compile()` SSoT in T-voice-3, NEVER reimplements. ✅ Skill cleared. |
| `tessl__langgraph` | NOT needed — VoiceDistillationOrchestrator extends `BaseExtractionOrchestrator` (sequential wave runner), NOT a LangGraph StateGraph. Spec § 5.3 explicitly says "wave-based" not "graph-based". | Skipped explicitly. ✅ Documented. |
| `tessl__graceful-degradation` | Every LLM call wrapped in `asyncio.wait_for(timeout_sec + 2.0)` + try/except → degraded warning + Decimal('0') cost on exception. Cost recorder bridge fallback (no-op) when observability package unavailable. | Pattern from offer_ladder_advisor.py replicated verbatim. ✅ Skill applied. |
| `tessl__pytest-api-testing` | 23 in-module smoke tests + 5 arch fitness tests use factory fixtures + parametrize + in-memory fakes. | Pattern from `test_offer_ladder_advisor.py` (T-extractors-1) replicated. ✅ Skill applied. |
| `tessl__fastapi` | NOT applicable — T-voice-1 produces no FastAPI routes (orchestrator is application-layer worker). | N/A documented. |

## § Cross-module audit (NO-NEW-LAYER) — Step 1

Per `.claude/rules/anti-duplication.md` SSoT inventory:

| Pattern | Canonical shared | Decision |
|---|---|---|
| Wave-based extraction orchestrator | `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` | **EXTEND**. `VoiceDistillationOrchestrator(BaseExtractionOrchestrator)` — direct inheritance per anti-duplication.md row "Extraction orchestrator". |
| LLM transport primitive (`_LLMResponse`, `_LiteLLMServiceLike`) | Sibling in `comunify/copilot/extractors/offer_ladder_advisor.py` | **CONSUME EXISTING**. N=2 within comunify; lift to shared when N=3 (next vertical with voice cloning surfaces). |
| `sanitize_payload` | `luana_core_observability.recording.sanitization` | **CONSUME**. Lazy import + truncate-only fallback. |
| `pop_cost` (LiteLLM CustomLogger bridge) | `luana_core_observability.recording.cost_recorder` | **CONSUME**. Lazy import + None fallback. |
| `CompiledVoice` schema | NEW vertical-creator-economy primitive | **CREATE** in `_schemas.py`. Schema-cemented v1 per Story D playbook. |

No new layers introduced. No mirror risk.

## § Files created

1. `comunify/backend/src/modules/comunify/brand/__init__.py` — subpackage anchor
2. `comunify/backend/src/modules/comunify/brand/voice_cloning/__init__.py` — public surface
3. `comunify/backend/src/modules/comunify/brand/voice_cloning/_schemas.py` — `CompiledVoice` + `VoiceExtractionWave`
4. `comunify/backend/src/modules/comunify/brand/voice_cloning/voice_distillation_orchestrator.py` — main orchestrator + 4 inline prompts
5. `comunify/backend/tests/agentic_evals/voice_cloning/__init__.py`
6. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_orchestrator_smoke.py` — 23 smoke tests
7. `comunify/backend/tests/architecture/test_comunify_voice_distillation_inherits_base_orchestrator.py` — 5 arch fitness tests

## § Design decisions

- **No separate `waves/*.py` modules.** The spec mentioned `waves/` dir but the existing sibling pattern (`offer_ladder_advisor.py`) keeps wave logic inline + prompts inline for cache prefix invariance + locality. Decision: inline pattern is the in-repo SSoT. Spec's `waves/` directive treated as illustrative.
- **No separate `prompts/*.j2` Jinja templates.** Same reasoning — inline string templates with `<<MARKER>>_VALUE` substitution sites preserve cache prefix invariance better than Jinja (which would interpolate per call). Per offer_ladder_advisor cement.
- **`VoiceExtractionWave` vs `ExtractionWave`.** Voice cloning needs `prompt_key` + `confidence_weight` fields the generic `ExtractionWave` doesn't have. Created vertical-specific frozen dataclass in `_schemas.py` (not lifted — N=1).
- **D15 raw-samples deletion.** Wired as `RawSamplesRemoverProtocol` DI port. Orchestrator only calls it on `final_status ∈ {completed, completed_low_confidence}` — NEVER on `failed`. Insufficient-samples short-circuit returns `failed` → no deletion → creator can retry with more uploads.
- **3-tier final_status classification**: `completed` (confidence ≥ 0.65) / `completed_low_confidence` (< 0.65 but ≥ 4 bloques present) / `failed` (≥4 bloques missing OR insufficient samples).

## § Tests audited

- 23 smoke tests in `test_voice_distillation_orchestrator_smoke.py`:
  - A1 subclass invariant (3 tests)
  - A2 4-wave pipeline + merge (6 tests including malformed JSON, partial failure, all-wave failure)
  - A3 cost budget (2 tests — happy + exceeded; skip when observability unavailable)
  - A4 insufficient samples graceful path (1 test)
  - A5 tenant isolation (1 test)
  - A6 D15 raw-samples remover invariants (3 tests — success / failure / all-wave-failure)
  - Best-effort side-effects don't raise (3 tests)
  - Outbox event shape (2 tests — success / failure marker)
  - Constructor validates wave weights sum (1 test)
  - Wave routes by model_role (1 test)

- 5 arch fitness tests in `test_comunify_voice_distillation_inherits_base_orchestrator.py`:
  - subclass invariant
  - inherits shared wave helpers
  - log_prefix comunify-specific
  - 4 waves match spec
  - confidence weights sum to 1.0

**Run result**: `28 passed in 1.2s` (arch fitness gates + smoke suite combined).

## § Default-flip detection (Step 0.5)

NOT triggered — no `core/config.py` defaults modified.

## § Pre-flight verification

- `git status --short` on both repos before write — verified no other-session WIP touched in our scope.
- `find /home/chris/luana-platform -name "base_orchestrator.py"` confirms `BaseExtractionOrchestrator` source present.
- `grep -rn "class VoiceDistillationOrchestrator"` confirms zero collision (only Protocol stub in service file).

## § R23 enforcement

Production code (orchestrator + schemas) authored by Opus 4.7 per R23. Tests authored by Opus 4.7 as part of same batch (tests-over-agentic, marked `production_code: false` in spec — Sonnet eligible too, but kept consistent for batch).

## § Out-of-scope (deferred)

- ARQ scheduler wiring (orchestrator can be invoked by any async caller — T-voice-2 worker bridges samples ingest → kickoff). Production wiring of LiteLLM service + outbox + audit log + raw remover lives in `extensions.py` (T-extensions-1) module factory pattern; this ticket scoped to the orchestrator class itself.
- Per-wave separate `.j2` files (decision documented above — inline kept).
- `waves/` subdirectory module structure (decision documented above — single-file kept).
