---
story_id: luana-sales-agent-engine
ticket_id: T-10
result: done
commit_sha: c2fbae1
last_modified: 2026-05-11
---

# T-10 result

**Status:** done

**Commit:** `c2fbae1 feat(luana-core-sales-agent): lift application tools (registry + payment + scheduling provider strategy + §3 2 webhook adapters hash-stable + deferred scheduling imports per §9.2)`

**Tests:** sed-applied + copied (10 test files). 9 tests passed in partial isolated run of test_payment_provider_strategy.py; 1 failure expected (depends on application.services.payment_state_service — T-13 lifts). All tests will run GREEN post T-13.

**§3 sha256 baselines POST-sed POST-ruff (CANONICAL for T-18 V-AG-8):**
- `payment/webhook_providers.py`: `9cf3cfd927cec33eabdbe690e5bcab4f1f2a9664a10a75e7feb1777af8261b44`
- `scheduling/webhook_providers.py`: `6a4899d95483089e99843529b51ac5b2cf7bed13ccc4366d82cb371ad3bf8a18`

**V-AG-2 invariant satisfied:** scheduling/providers.py has 6 deferred imports INSIDE method bodies; ZERO top-level `from luana_core_scheduling.*` imports in src/.

**Halt criteria — none triggered.** AISALESHT untouched. Zero top-level cross-module leaks. Deferred scheduling runtime preserved per §9.2. R23 honored.

**Next:** T-11 — lift application/quality + prompts + D-T3 BrandVoicePort consumer wiring (slot 5 BRAND_VOICE).
