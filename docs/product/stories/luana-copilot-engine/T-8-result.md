---
story_id: luana-copilot-engine
ticket: T-8
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-8 result — Lift copilot infrastructure {channels, voice, qdrant, cache, prompts, web, workers, in_memory_*_registry}

## Status: GREEN

## Commit
luana-platform main: `e1e446f` (feat(luana-core-copilot): lift copilot infrastructure channels + voice + qdrant + cache + prompts + web + workers)

## Validators satisfied
- V-NF-2 (pyproject 0.0.6-alpha preserved)
- V-F-marketing-kb (Qdrant marketing_kb_store smoke 17/17 PASS — F10 tenant-agnostic invariant)

## Tests run
- 59/59 PASS across test_marketing_kb_store + test_data_query_cache + test_whisper_transcriber + test_trafilatura_client + test_tavily_search (env vars supplied — conftest lifts T-15)
- `test_marketing_kb_layout_in_system_prompt.py` deferred to T-15 (requires application.orchestrator lifted T-9)

## Files lifted
- 21 Python source files in 7 subfolders + 3 in_memory_*_registry.py at infra root
- 28 Jinja template files (`.j2`) under prompts/templates/
- 6 test files
- Total: 24 source .py + 28 templates + 6 tests = 58 files

## Dependencies verified
qdrant-client, arq, jinja2, trafilatura, tiktoken — all resolve via uv

## Batch 2 (T-6 + T-7 + T-8) summary
- T-6: 23 source + 8 tests, 18/18 message_codec PASS, others defer to T-15
- T-7: 5 source + 3 tests, 34/34 PASS
- T-8: 24 source + 28 templates + 6 tests, 59/59 PASS, V-F-marketing-kb GREEN

Total Batch 2: 52 source .py + 28 templates + 17 tests, 111 cumulative test PASS

## Process drifts documented for /pm + auditor
1. **T-6 step 7 spec drift** — `message_model.py` does NOT exist in copilot; lives in sales_agent (Story 7). T-17 spec also needs correction.
2. **05-guidelines.md §1.3 sed gap** — does not cover `unittest.mock.patch("dotted.path")` string literals. Manual fixes applied in T-7 + T-8.
3. **T-6 step 5 spec drift** — `test_conversation_repository.py` GREEN expected but requires `db` fixture from conftest.py (lifts T-15). Documented as DAG order natural consequence.

## Next
T-9 — application/orchestrator/ (LangGraph + deepagents harness) — 16 files
