# T-voice-3 IMPL-LOG — Compiler integration bridge (CompiledVoice → PersonalityCompiler v2 → Slot 5 cache invalidate)

**Ticket**: T-voice-3 (06-tickets.yaml line 538)
**State**: done
**Owner**: builder-agentic (Opus 4.7 per R23 — production_code=true AGENTIC)
**Estimate**: 4h
**Actual**: ~1.5h (within batch)
**Date**: 2026-05-14
**Validators GREEN**: V-AE-29

## § Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Bridge feeds slot 5 BRAND_VOICE cache prefix (10-slot architecture T-prompts-1). Anti-duplication grep mandate. | grep `compiler_integration` + `class.*VoiceCompiler` cross codebase → zero collisions. ✅ |
| `sales-agent-expert` | **§3 NO se toca** lists `PersonalityCompiler` SSoT — bridge MUST consume, NEVER reimplement (R10 anti-duplication.md cardinal). Slot 5 cache prefix invariance is the critical invariant. | Bridge directly imports `PersonalityCompiler.compile()` from `luana_core_brand_studio.domain.personality`. The arch test `test_sales_agent_uses_voice_port_no_direct_compiler_import.py` restricts ONLY `luana-core-sales-agent` from direct import — comunify (brand consumer same tier as brand-studio) is allowed. Documented in bridge module docstring. ✅ |
| `tessl__graceful-degradation` | Event bus emission MUST be best-effort (failure ≠ blocking the compile). Cache invalidator failure → handler returns False, no raise. | Both emission + invalidation wrapped try/except + structlog warning + audit-records failure flag. ✅ |
| `tessl__pytest-api-testing` | 26 bridge tests use in-memory fakes for profile writer + event bus + cache invalidator + audit log. | Pattern applied. ✅ |
| `tessl__langgraph` | NOT applicable — bridge is pure function (no graph). | Skipped. ✅ |
| `tessl__fastapi` | NOT applicable. | N/A. |

## § Cross-module audit (NO-NEW-LAYER)

| Pattern | Canonical shared | Decision |
|---|---|---|
| Voice → personality compilation | `luana_core_brand_studio.domain.personality::PersonalityCompiler.compile()` (Story 5 SSoT) | **CONSUME DIRECTLY**. Bridge produces (PersonalityDimensions, LinguisticPatterns, [SampleExchange]) and calls `compile()`. NEVER reimplements. |
| Bridge mapping heuristics | NEW vertical-creator-economy | **CREATE LOCAL** `_REGISTRO_KEYWORD_DELTAS` + `_DIALECT_GREETINGS` maps. Transparent + small (~25 keywords). |
| `PersonalityProfileWriterProtocol` | None canonical | **NEW** Protocol port for tenant-scoped UPDATE. Production wires `PersonalityProfileRepository` (already exists in brand-studio core). |
| `VoiceRatifiedEventBusProtocol` | `shared/agent_observability/persistence/outbox` (per anti-duplication.md row) | **PROTOCOL only here**; production wires the outbox adapter. Stub-friendly. |
| `voice_ratified_handler` cache invalidator | None canonical | **NEW** Protocol port. Production wires LiteLLM proxy cache key invalidation. |

## § Files created

Source (3 files):
1. `comunify/backend/src/modules/comunify/brand/voice_cloning/compiler_integration.py` — bridge entry points
2. `comunify/backend/src/modules/comunify/application/event_handlers/__init__.py`
3. `comunify/backend/src/modules/comunify/application/event_handlers/voice_ratified_handler.py` — Slot 5 cache invalidator

Tests (1 file, 26 tests):
4. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_compiler_integration.py`

Conftest extension:
5. `comunify/backend/conftest.py` — added `luana_core_brand_studio` to workspace src paths

## § Design decisions

- **Bridge MAPS 6 bloques → 5-block compiler inputs**, NEVER reimplements compilation:
  - Bloque 1 identidad → ANCHOR via `SampleExchange[0].context="identity_anchor"`
  - Bloque 2 dialecto → `LinguisticPatterns.greeting/farewell` via `_DIALECT_GREETINGS` map
  - Bloque 3 vocabulario → `LinguisticPatterns.unique_vocabulary + filler_phrases`
  - Bloque 4 registro → `PersonalityDimensions` via keyword-driven heuristic deltas
  - Bloque 5 asi_no → drives further dim shifts (e.g. "NUNCA chistes" → humor ↓)
  - Bloque 6 anclajes → `SampleExchange` follow-ups
- **VoiceRatifiedV1 payload carries METADATA ONLY** (R2 + D15): tenant_id, source_job_id, personality_profile_version, confidence_score, dialecto, samples_used. NO raw vocabulario / asi_no / anclajes lists. Arch-asserted via `forbidden_keys` set in `test_bridge_emits_voice_ratified_v1_event_with_metadata_only`.
- **Heuristic deltas are TRANSPARENT + EDITABLE**: creator can adjust `PersonalityProfile` directly in Brand Studio after bridge fires; bridge is the seed, not the immovable.
- **Handler classify-loud parsing**: `parse_voice_ratified_payload` returns None on malformed input. Handler returns False on parse failure or invalidation failure — caller (outbox processor) treats False as "retry later" or "alert"; doesn't crash.
- **Cache invalidation BEST-EFFORT**: handler logs + returns False on invalidator exception. Next live turn rebuilds cache via the version-keyed key naturally (worst case: one turn served from stale cache before version bump propagates).

## § Tests audited

26 tests in `test_voice_compiler_integration.py`:

- Mapping function (9 tests): returns 3 artefacts, dims clamped [0,1], warmth ↑ for cercano, humor ↓ for serio, warmth ↓ for formal+serio, es-AR yields voseo greeting, es-MX yields Mexican greeting, vocab carried through, anclajes become sample exchanges.
- `compile_voice_to_system_instruction` (3 tests): non-empty string, minimal voice still compiles, voseo voice produces 5 blocks.
- `bridge_compiled_voice_to_personality_profile` (6 tests): persists + bumps version, emits VoiceRatifiedV1 with METADATA ONLY (R2/D15), doesn't raise on event bus failure, works without event bus, threads tenant_id, metadata carries confidence + samples + dialecto + schema_version.
- `parse_voice_ratified_payload` (3 tests): valid, malformed → None, bad UUID → None.
- `handle_voice_ratified` (5 tests): invalidates, returns False on malformed, doesn't raise on invalidator failure, writes audit log, audit records failure flag when invalidator fails.

**Run result**: `26 passed in 0.5s`.

## § Default-flip detection (Step 0.5)

NOT triggered.

## § Conftest extension

Added `/home/chris/luana-platform/core/luana-core-brand-studio/src` to `_WORKSPACE_SRC_PATHS` in `conftest.py`. Required for `from luana_core_brand_studio.domain.personality import PersonalityCompiler` to resolve in test runtime.

## § R23 enforcement

Production code (compiler_integration + voice_ratified_handler) Opus 4.7. Tests Opus 4.7 (consistent within batch).

## § Out-of-scope (deferred)

- Production `PersonalityProfileWriter` adapter (concrete tenant-scoped UPDATE row + version bump). Today: Protocol + fake. Production wiring via T-extensions-1 module factory.
- Production cache invalidator concrete adapter (LiteLLM proxy cache key API). Today: Protocol + fake.
- LiteLLM proxy cache key key derivation `(tenant_id, personality_profile_version)`. Per 03-arch-agentic § 8.3 — keyed automatically via `prompt_cache_key=str(tenant_id)` + version in the slot 5 content block.
