# T-voice-2 IMPL-LOG — Voice samples ingestion (WhatsApp ZIP + Whisper + PII sanitize)

**Ticket**: T-voice-2 (06-tickets.yaml line 511)
**State**: done
**Owner**: builder-agentic (Opus 4.7 per R23 — production_code=true AGENTIC)
**Estimate**: 4h
**Actual**: ~1.5h (within batch)
**Date**: 2026-05-14
**Validators GREEN**: V-F-17, V-AE-28

## § Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Worker writes to `comunify_voice_cloning_samples` (T-be-2 schema). Anti-duplication grep mandate for any new file. | grep `voice_samples_ingest` cross codebase → zero collisions. ✅ |
| `sales-agent-expert` | Output feeds into voice cloning pipeline (T-voice-1) → eventually `personality_profiles.system_instruction`. § Anti-duplication cardinal: PII sanitization is shared abstraction; comunify uses inline minimal patterns as fallback (FYI for future shared lift). | Inline regex `_PII_PATTERNS` documented as candidate for lift-to-shared when N=2 (vitalia + comunify). ✅ |
| `tessl__graceful-degradation` | Whisper transcribe MUST timeout + fallback to empty string. ZIP fetch + parse + delete also have isolated try/except. | `asyncio.wait_for(timeout_sec + 2.0)` wrapper + try/except returning empty string + structlog warning. Worker NEVER raises. ✅ |
| `tessl__pytest-api-testing` | 22 PII/parser/worker tests use synthetic ZIP fixtures + factory fakes (Whisper transcriber, samples repo, upload store, distillation kickoff). | Pattern applied. ✅ |
| `tessl__langgraph` | NOT needed — worker is plain async function, not a LangGraph node. | Skipped. ✅ |
| `tessl__fastapi` | NOT applicable — worker has no FastAPI routes. | N/A. |

## § Cross-module audit (NO-NEW-LAYER)

| Pattern | Canonical | Decision |
|---|---|---|
| PII regex patterns | None canonical yet — vitalia uses ad-hoc; comunify Story D `scripts/_pii_patterns.py` is AISALESHT-side | **INLINE FALLBACK** in `samples_parser._PII_PATTERNS`. 9 categories (email + phone + DNI_AR/PE + CUIT_AR + RFC_MX + RUT_CL + CURP_MX). Document as N=1 lift-to-shared candidate. |
| Whisper transcription | None canonical | **PROTOCOL** in `samples_parser.WhisperTranscriberProtocol`. Stub-friendly; production wires LiteLLM proxy Whisper-1. |
| WhatsApp ZIP parsing | None canonical | **NEW** in `samples_parser.parse_whatsapp_zip`. Vertical-creator-economy specific (WhatsApp export). |
| `voice_samples_ingest` worker | None canonical | **NEW** in `application/tasks/voice_samples_ingest_worker.py`. |
| `ZipUploadStoreProtocol` / `VoiceCloningSamplesRepoProtocol` / `VoiceDistillationKickoffProtocol` | None canonical | **NEW** Protocols local to worker. |

## § Files created

Source:
1. `comunify/backend/src/modules/comunify/brand/voice_cloning/samples_parser.py` — ZIP parser + PII strip + Whisper wrapper
2. `comunify/backend/src/modules/comunify/application/tasks/__init__.py`
3. `comunify/backend/src/modules/comunify/application/tasks/voice_samples_ingest_worker.py` — async worker entry point

Tests:
4. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_samples_pii_sanitized.py` — 22 tests
5. `comunify/backend/tests/architecture/test_comunify_no_pii_in_voice_samples_persistence.py` — 3 arch fitness tests

## § Design decisions

- **Inline PII patterns vs shared.** Comunify lives in luana-platform; AISALESHT-side `scripts/_pii_patterns.py` is not reachable. Local 9-pattern fallback chosen. When luana-platform grows N=2 consumers (vitalia voice cloning surfaces), lift to `luana_core_observability.pii_patterns`.
- **PII strip BEFORE returning from parser.** Parser strips PII at the boundary between raw ZIP bytes and parsed `ChatLine` objects. Caller (worker) never sees the original.
- **D15 strict invariant**: worker persists ONLY `chats_count` + `voice_notes_count` + filename + country in `upload_history_entry`. Raw chat lines + transcriptions are passed in-memory to the distillation kickoff and dropped when the function returns. Original blob deleted after persist via `zip_store.delete_upload()`.
- **Best-effort everywhere**: every sub-step (fetch / parse / transcribe / persist / delete / kickoff) is in its own try/except. Failure of one does NOT block the others; surfaces as warning in `IngestResult.warnings`.
- **Whisper graceful degradation**: timeout via `asyncio.wait_for(timeout_sec + 2.0)`. Per-file exception returns empty string + structlog warning. Empty transcriptions filtered when building distillation lines (won't pollute the orchestrator).
- **Auto-kickoff threshold**: 50 (matches `VoiceDistillationOrchestrator._MIN_SAMPLES_THRESHOLD`). Kickoff only fires when combined chat + transcribed voice count ≥ threshold.

## § Tests audited

22 in-module tests + 3 arch fitness tests:

- Parser tests (8): PII strip per category (email, phone, DNI, RFC), voseo not clobbered, voice note hint lines excluded, voice note files collected, corrupt ZIP handled, missing _chat.txt handled.
- Whisper tests (4): timeout → empty + warning; exception → empty + warning; PII strip from transcription; empty list short-circuit.
- Worker tests (7): persists counts only (D15), deletes upload after persist, handles corrupt ZIP, fetch failure, persist failure, auto-kicks above threshold, doesn't kick below, threads tenant_id.
- Arch fitness (3): `upload_history_entry` dict keys allowlist, no `chat_lines`/`transcriptions` kwargs to repo calls, ORM model has no raw-content fields.

**Run result**: `25 passed in 0.6s`.

## § Default-flip detection (Step 0.5)

NOT triggered.

## § R23 enforcement

Production worker authored by Opus 4.7. Tests Opus 4.7 (consistent within batch).

## § Out-of-scope (deferred)

- Production Whisper wiring (LiteLLM proxy Whisper-1). Today: Protocol + stub. Production lives in extension factory (T-extensions-1).
- Shared lift of PII regex (waiting for N=2 trigger).
