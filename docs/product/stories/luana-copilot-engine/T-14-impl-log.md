---
story_id: luana-copilot-engine
ticket: T-14
phase: completed
last_modified: 2026-05-11
---

# T-14 impl-log — Lift copilot api/ (21 files: 10 routers + 10 DTOs + _dependencies.py)

## Surface

- **Source AISALESHT:** `backend/src/modules/copilot/api/` (21 files)
- **Target luana-platform:** `core/luana-core-copilot/src/luana_core_copilot/api/`

## Steps executed

1. `cp -r` full api/ subfolder (21 files)
2. Cleared `__pycache__`
3. Applied §1.3 sed mapping (extended with string-literal `patch()` + `from src.workers` rules from Batch 3 process drift)
4. Verified zero `from src.*` leaks
5. Copied 14 missing API tests from AISALESHT (test_actions_router + test_chat_routing_integration already existed from prior batches)
6. Applied sed on tests
7. Ran subset of T-14 unit tests (40 PASS in voice + plan + media_max_bytes + knowledge_search + conversational_channel_port suite). DB-fixture-dependent tests deferred to T-15.

## Files lifted (21 src + 14 tests)

src/luana_core_copilot/api/:
- __init__.py
- _dependencies.py
- 10 routers: chat, conversations, voice, telegram, plan, suggestions, actions, events, media, knowledge, nudge
- 10 DTOs: conversation_dto, document_dto, media_dto, suggestions_dto, tenant_limits_dto, voice_dto, telegram_dto, dto

Tests added:
- test_conversation_security.py
- test_conversational_e2e.py
- test_conversational_channel_port.py
- test_voice_api.py + test_voice_combined.py + test_voice_domain.py + test_voice_rate_limit.py + test_voice_rate_limit_per_tenant_override.py
- test_plan_card_emission.py
- test_media_upload.py + test_media_db_roundtrip.py + test_media_max_bytes_env.py
- test_knowledge_search_tool.py
- test_conversation_repository_count_window.py

## Results

40 unit tests PASS isolated across T-14 surfaces.

## Notes

- `FastAPI(redirect_slashes=False)` invariant preserved per CLAUDE.md backend-ddd.md
- Per arch test gate: app-level only (no APIRouter individual override) — preserved verbatim
- Remaining DB-fixture-dependent tests deferred to T-15

## Next

T-15 — evals + utils + finalize copilot package GREEN aggregate.
