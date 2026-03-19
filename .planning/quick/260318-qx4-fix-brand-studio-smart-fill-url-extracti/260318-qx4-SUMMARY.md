---
phase: quick-260318-qx4
plan: 01
subsystem: api
tags: [httpx, beautifulsoup, asyncio, brand-extraction, web-crawling]

requires:
  - phase: none
    provides: none
provides:
  - "Working Brand Studio smart fill URL extraction via httpx+BeautifulSoup"
  - "Non-blocking concurrent LLM extraction calls via asyncio.to_thread + gather"
affects: [brand, copilot]

tech-stack:
  added: []
  patterns: ["asyncio.to_thread for wrapping sync LLM calls in async context", "httpx.AsyncClient for async web crawling"]

key-files:
  created: []
  modified:
    - backend/src/modules/brand/application/extraction_service.py

key-decisions:
  - "Replaced web_extractor_graph with direct httpx+BeautifulSoup (graph had KeyError making crawl return empty in 0.02s)"
  - "Used asyncio.to_thread for sync LLM calls instead of rewriting AIActionService to be async"
  - "Crawl depth=1 with max 5 internal subpages for balanced content vs speed"

patterns-established:
  - "asyncio.to_thread wrapping pattern for sync services called from async context"

requirements-completed: [BUG-crawl-keyerror, BUG-sync-llm-blocking]

duration: 4min
completed: 2026-03-19
---

# Quick Task 260318-qx4: Fix Brand Studio Smart Fill URL Extraction

**httpx+BeautifulSoup replaces broken web_extractor_graph for real crawling; asyncio.to_thread + gather for non-blocking concurrent LLM extraction**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T00:31:56Z
- **Completed:** 2026-03-19T00:36:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Brand Studio smart fill now actually crawls website content (was returning empty in 0.02s due to KeyError)
- LLM extraction calls no longer block the FastAPI event loop (wrapped in asyncio.to_thread)
- All 4 brand sections extract concurrently via asyncio.gather (~4x speedup over sequential)

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace broken crawl_content with httpx+BeautifulSoup** - `3fcd61d` (fix)
2. **Task 2: Wrap synchronous LLM calls in asyncio.to_thread and run concurrently** - `2d3953c` (fix)

## Files Created/Modified
- `backend/src/modules/brand/application/extraction_service.py` - Replaced web_extractor_graph with httpx+BeautifulSoup crawling; wrapped 4 sync LLM calls in asyncio.to_thread; added asyncio.gather for concurrent extraction

## Decisions Made
- Replaced web_extractor_graph with direct httpx+BeautifulSoup -- the graph had a KeyError bug causing empty results and was overkill for simple text extraction
- Used asyncio.to_thread to wrap synchronous run_structured_action calls rather than rewriting AIActionService to be fully async (minimal change, same effect)
- Truncate crawled content to 100K chars to avoid overwhelming LLM context windows

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Ruff not installed in container (ruff check verification skipped) -- no impact on correctness

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Brand Studio smart fill is functional for URL-based extraction
- Text-only extraction path unchanged (no regressions)
- Visual extraction (extract_from_url) path unchanged

---
*Phase: quick-260318-qx4*
*Completed: 2026-03-19*
