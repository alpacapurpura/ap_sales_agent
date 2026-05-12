---
story_id: luana-copilot-engine
ticket: T-8
owner: builder-agentic (claude-opus-4-7)
started_at: 2026-05-11
completed_at: 2026-05-11
status: GREEN
---

# T-8 — Lift copilot infrastructure {channels, voice, qdrant, cache, prompts, web, workers, in_memory_*_registry}

## Skills consulted
- `copilot-expert` — Qdrant marketing_kb_store (F10), Telegram bot adapter, in_memory registries
- `tessl__graceful-degradation` — confirmed `tavily_search.py`, `trafilatura_client.py`, `whisper_transcriber.py` already wrap external calls per F0-F11 baseline (timeouts + try/except). No new external calls introduced in lift.
- `tessl__pytest-api-testing` — applied patch string-literal sed for unittest.mock patches

## Scope
Lift 7 subfolders + 3 in_memory registries verbatim per 05-guidelines.md §1.3.

### Source (AISALESHT — READ-ONLY)
- `backend/src/modules/copilot/infrastructure/{channels,voice,qdrant,cache,prompts,web,workers}/`
- `backend/src/modules/copilot/infrastructure/in_memory_{hook,rule,skill}_registry.py`
- `backend/tests/modules/copilot/test_{marketing_kb_store,whisper_transcriber,data_query_cache,trafilatura_client,tavily_search}.py` (5 baseline) + `test_marketing_kb_layout_in_system_prompt.py` (1 opportunistic, blocked on T-9 orchestrator)

### Target (luana-platform — CREATED)
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/{channels,voice,qdrant,cache,prompts,web,workers}/`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/in_memory_{hook,rule,skill}_registry.py`
- `core/luana-core-copilot/tests/test_*.py` (6 files)

### Files lifted
- 21 source files in subfolders (channels: 3, voice: 2, qdrant: 2, cache: 2, prompts: 4 + 28 Jinja templates + brand_extraction subdir, web: 3, workers: 2)
- 3 in_memory_*_registry.py at infra/ root
- 28 Jinja `.j2` template files (no sed — Jinja, not Python)
- 6 test files

## Execution

### Step 1 — cp -r lift
```bash
for sub in channels voice qdrant cache prompts web workers; do
  cp -r /home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/$sub \
        core/luana-core-copilot/src/luana_core_copilot/infrastructure/
done
cp /home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/in_memory_*_registry.py \
   core/luana-core-copilot/src/luana_core_copilot/infrastructure/
```
Pycache stripped.

### Step 2 — sed substitutions
Applied per 05-guidelines.md §1.3 (full 23 substitutions × 7 subdirs + 3 root files).

**T-7 process drift carried forward:** also applied patch string-literal sed:
```bash
sed -i 's|"src\.modules\.copilot\.|"luana_core_copilot.|g' tests/...
sed -i "s|'src\\.modules\\.copilot\\.|'luana_core_copilot.|g" tests/...
sed -i 's|"src\.shared\.|"luana_core_platform.|g' tests/...
```
to catch `unittest.mock.patch("dotted.path")` references.

### Step 3 — Verification
- ✅ Zero `from src.*` leaks in src/ + tests/
- ✅ Zero `"src.*"` / `'src.*'` string-literal leaks in tests/
- ✅ Templates `.j2` files clean (Jinja templates do not import Python)
- ✅ Class declarations preserved (verbatim cp)
- ✅ Ruff check: 5 I001 (import order) auto-fixed (sed reorder broke alphabetical)
- ✅ Ruff format check: 49 files already formatted

### Step 4 — Dependency resolution
```bash
uv run python -c "import qdrant_client, arq, jinja2, trafilatura, tiktoken; print('all OK')"
```
**Result: qdrant-client + arq + jinja2 + trafilatura + tiktoken all resolve** (per pyproject T-2 deps).

### Step 5 — Isolated test run
```bash
POSTGRES_USER=... (full env) uv run pytest \
  core/luana-core-copilot/tests/test_marketing_kb_store.py \
  core/luana-core-copilot/tests/test_data_query_cache.py \
  core/luana-core-copilot/tests/test_whisper_transcriber.py \
  core/luana-core-copilot/tests/test_trafilatura_client.py \
  core/luana-core-copilot/tests/test_tavily_search.py -x -q
```
**Result: 59 passed in 1.89s GREEN**

### V-F-marketing-kb smoke (validator addressed)
```bash
uv run pytest core/luana-core-copilot/tests/test_marketing_kb_store.py -x -q
```
**Result: 17 passed in 0.73s GREEN**

### Test blocked by T-9 (orchestrator lift)
- `test_marketing_kb_layout_in_system_prompt.py` requires `luana_core_copilot.application.orchestrator.system_prompt_layout` — that module lifts in T-9. Test was opportunistically copied (consistent with §3.4 "lift ALL tests") but cannot run until T-9 GREEN. Will activate in T-15 aggregate GREEN.

## Anti-duplication
- `marketing_kb_store.py` consumes Qdrant client directly — no observability mirror created. F10 pattern preserved (tenant-agnostic `nicolify_marketing_kb` collection, dim 3072).
- `telegram_bot.py`, `whisper_transcriber.py`, `trafilatura_client.py`, `tavily_search.py` — all wrap external HTTP/SDK calls per pre-existing graceful-degradation pattern. No new external calls introduced; lift preserves existing timeouts + try/except.
- 3 `in_memory_*_registry.py` files: hook/rule/skill stub registries (boot-time substitutes pending Redis/DB persistence). No anti-duplication concerns — these are internal copilot infrastructure.

## D-T6 observability subclass invariant
Not applicable to T-8 (observability subfolder = T-13). Verified no `class FXResolver|CostCalculator|PricingResolver|BaseObservabilityContext|BaseAgentCallbackHandler` declarations introduced.

## [COPILOT-*] anchors
Anchors live in `application/orchestrator/` (T-9) + `domain/` (already lifted T-3). Final count check runs T-15+T-20.

## Files touched
### Created (luana-platform main branch)
Source (21 Python files + 28 templates):
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/channels/{__init__,in_memory_channel,telegram_bot}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/voice/{__init__,whisper_transcriber}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/qdrant/{__init__,marketing_kb_store}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/cache/{__init__,data_query_cache}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/prompts/{__init__,base,sanitizer}.py + brand_extraction/__init__.py + templates/*.j2 (28 files)`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/web/{__init__,tavily_search,trafilatura_client}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/workers/{__init__,telegram_worker}.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/in_memory_{hook,rule,skill}_registry.py`

Tests:
- `core/luana-core-copilot/tests/test_marketing_kb_store.py`
- `core/luana-core-copilot/tests/test_data_query_cache.py`
- `core/luana-core-copilot/tests/test_whisper_transcriber.py`
- `core/luana-core-copilot/tests/test_trafilatura_client.py`
- `core/luana-core-copilot/tests/test_tavily_search.py`
- `core/luana-core-copilot/tests/test_marketing_kb_layout_in_system_prompt.py` (activated post-T-9)

### Modified
None.

## Validators addressed
- V-NF-2 (pyproject 0.0.6-alpha preserved)
- V-F-marketing-kb (Qdrant marketing_kb_store 17/17 PASS GREEN — F10 invariant)

## Verdict
done — T-8 infrastructure subfolders lifted GREEN. 59 tests PASS isolated. V-F-marketing-kb GREEN. 28 Jinja templates copied verbatim. All deps resolve.
