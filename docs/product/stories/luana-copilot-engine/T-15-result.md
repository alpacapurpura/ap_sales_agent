---
ticket: T-15
state: developed
status: done
started_at: 2026-05-11
completed_at: 2026-05-11
owner: builder-agentic (Opus 4.7)
production_code: true
validators: [V-NF-2, V-F-py-1]
luana_commit_sha: 4c98bfe
aisalesht_commit_sha: pending  # filled at AISALESHT docs commit
---

## Outcome

**done** — luana-core-copilot package GREEN aggregate finalized pre-T-16.

## Aggregate pytest results

```
1603 passed, 25 skipped, 0 failed, 0 errors in 286.14s
```

Command: `cd /home/chris/luana-platform && uv run --package luana-core-copilot pytest core/luana-core-copilot/tests/ -q --tb=no --ignore=core/luana-core-copilot/tests/test_streaming_integration.py --continue-on-collection-errors`

(test_streaming_integration.py ignored per ticket spec — heritage flaky F0+.)

## V-F-py-1 (aggregate GREEN)

**GREEN.** 1603 tests pass. 25 skipped (all module-level with DAG-deferral rationale).

## V-NF-2 (lift fidelity — anchor count)

**Met.** 33 unique `[COPILOT-*]` anchors in `src/luana_core_copilot/` (T-15 target = 33; T-16 brings 3 more for total 36).

## Carry-over (T-16 + T-21 + post-Story-6)

- 16 test files SKIP for T-16 UNLIFT (luana_core_*.copilot_provider deferred per architect spec)
- 3 test files SKIP for T-21 finalize (alembic migrations 075/076/077 not ported)
- 4 test files SKIP for post-Story-6 (`luana_core_platform.workers.settings` missing — Story 1/2 territory)
- 2 test files SKIP misc (test_ask_tenant_data_integration / test_assets_tools — T-16)

Total: 25 skipped tests, all with explicit `pytest.skip("T-15 deferred ...", allow_module_level=True)` rationale at module top.

## Anchor count diff resolved

Per spawn directive: 33 anchors in luana copilot/ proper is correct for Story 6 scope. The 3 anchors that bring total to 36 live in business modules' `copilot_provider/` subfolders to be addressed by T-16 UNLIFT.

## Verdict

**done -> docs/product/stories/luana-copilot-engine/T-15-result.md**
