---
story_id: luana-copilot-engine
ticket: T-7
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-7 result — Lift copilot infrastructure persisters

## Status: GREEN

## Commit
luana-platform main: `a60fa7b` (feat(luana-core-copilot): lift copilot infrastructure persisters)

## Validators satisfied
- V-NF-2 (pyproject 0.0.6-alpha preserved)

## Tests run
- `test_brand_persister.py` + `test_buyer_persona_persister.py` + `test_offer_persister.py` — 34/34 PASS (with env vars supplied — conftest lifts T-15)

## Files lifted
- 5 source files (persisters dir)
- 3 test files

## Process drift noted
05-guidelines.md §1.3 sed mapping does NOT cover `unittest.mock.patch("dotted.path")` string literals. 2 manual fixes in test_brand_persister.py. Recommend §1.3 extension for T-8 onward to include string-literal variants.

## Next
T-8 — channels/voice/qdrant/cache/prompts/web/workers/in_memory_*_registry
