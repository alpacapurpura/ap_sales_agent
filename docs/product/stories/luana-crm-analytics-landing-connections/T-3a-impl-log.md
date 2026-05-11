---
ticket_id: T-3a
story_id: luana-crm-analytics-landing-connections
state: pushed
phase: BUILD
last_modified: 2026-05-11
owner: builder-backend (Opus 4.7 rescue, after 3 Sonnet stalls)
artifact_kind: impl-log
spec_ref: 06-tickets.yaml § T-3a
---

# T-3a — Implementation log

## Rescue context

Spawned by /pm after 3 Sonnet builder attempts cap_reached on test-isolation issue per outcome §7.2 autonomous batch policy. Opus rescue scope: complete T-3a per spec (framework + domain), commit, push.

## Diagnostic findings

Sonnet over-lifted: included `infrastructure/` and `workers/` directories in the analytics-engine package. Per 06-tickets.yaml § T-3a lines 124-134 + 144, T-3a scope is `api + application + domain + __init__.py` ONLY. Lines 144 explicitly forbids `cp -r analytics/{infrastructure,workers,copilot_provider}` for this ticket — those belong to T-3b and T-3c respectively.

Sonnet's "test isolation" rabbit hole was a symptom of the over-lift: tests calling `from luana_core_analytics_engine.infrastructure.X import ...` will obviously fail when infrastructure doesn't exist yet. Per spec line 159: "Tests may NOT all be GREEN yet (infrastructure missing). DOCUMENT count + which tests fail (likely most due to missing repositories/providers). Defer GREEN check to T-3c."

## Actions taken

### Step 1 — Scope correction

Removed over-lifted directories that belong to later sub-tickets:

```bash
rm -rf core/luana-core-analytics-engine/src/luana_core_analytics_engine/infrastructure/
rm -rf core/luana-core-analytics-engine/src/luana_core_analytics_engine/workers/
```

`infrastructure/` will return in T-3b. `workers/` will return in T-3c.

Final T-3a `src/luana_core_analytics_engine/` layout:

```
__init__.py
api/        (5 modules: campaigns, email_metrics, etl_admin, metrics + __init__)
application/
  __init__.py
  config.py
  cost_type_mapping.py
  dto/         (15 DTO modules)
  services/    (28 service modules + stage_services/)
domain/     (13 modules: campaign_entities, enums, event, exceptions,
             extraction_contract, extraction_result, industry_benchmarks,
             metric_catalog, metric_resolver, models, period_config, ports)
```

### Step 2 — Verify pyproject.toml + workspace registration

`core/luana-core-analytics-engine/pyproject.toml` is well-formed:
- `name = "luana-core-analytics-engine"` ✓
- `version = "0.0.1-alpha"` ✓ (matches §1.1 lift mode rule)
- `requires-python = ">=3.12"` ✓
- Dependencies: pydantic, sqlalchemy, fastapi, structlog, httpx, arq, redis, luana-core-platform, luana-core-iam, plus provider SDKs (google-auth-oauthlib, google-api-python-client, google-analytics-data, facebook-business).

Workspace root `~/luana-platform/pyproject.toml` already includes `core/luana-core-analytics-engine` in `[tool.uv.workspace] members` (committed in `2cac18d`).

### Step 3 — sed import rewrites verification

`grep -rn "from src\.\|import src\." src/` → **0 hits**. All AISALESHT-style imports already converted to `luana_core_analytics_engine.*` / `luana_core_platform.*` / `luana_core_iam.*`.

`grep -rn "src\.modules\.copilot\|src\.modules\.sales_agent\|copilot_provider" src/ tests/` → **0 hits**. Per 05-guidelines.md §3.3 deferred list.

### Step 4 — Cross-scope leak audit

`luana-core-platform/pyproject.toml` shows `M` in git status. Diff:

```
+    "passlib>=1.7.4",
```

Verified legitimate: `luana-core-platform/src/luana_core_platform/core/security.py:7` uses `from passlib.context import CryptContext`. This was a Story 2/3 transitive that needs declaration; keeping the change.

`uv.lock` rebuilt from `uv sync` to reflect passlib resolution. Kept.

### Step 5 — Brand-agnostic engine verification (per 05-guidelines.md §1.7)

```bash
cd ~/luana-platform/core/luana-core-analytics-engine/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_analytics_engine/
# → 0 hits (OK)
grep -rEn '(API_KEY|SECRET|TOKEN)\s*=\s*"...{8,}"' luana_core_analytics_engine/
# → 0 hits (OK)
```

### Step 6 — Tests baseline (per spec line 159 — defer GREEN to T-3c)

```bash
cd ~/luana-platform && uv run pytest core/luana-core-analytics-engine/tests/ --collect-only -q
# → 920 tests collected, 39 errors during collection (18 distinct test files)
```

Tests that COLLECT FAIL: 18 files. All fail because they reference `luana_core_analytics_engine.infrastructure.*` which doesn't exist until T-3b lands. Affected files (T-3b will resolve):

```
test_mailerlite_provider_enhanced.py
test_meta_campaign_provider.py
test_meta_demographics_extraction.py
test_meta_provider.py
test_meta_provider_ad_level.py
test_meta_provider_extractors_use_daily.py
test_meta_provider_invariants.py
test_metric_aggregation_upsert.py
test_opportunity_repository.py
test_overview_stage.py
test_performance_benchmarks.py
test_period_metrics_integration.py
test_scheduler_tick.py
test_shopify_provider.py
test_stage_overview_endpoint.py
test_stage_overview_service.py
test_tiktok_provider.py
test_youtube_provider.py
```

Tests that pass (domain-only smoke):

```bash
cd ~/luana-platform && uv run pytest \
  core/luana-core-analytics-engine/tests/test_metric_resolver_supplemental.py \
  core/luana-core-analytics-engine/tests/test_metric_catalog.py -x -q
# → 31 passed
```

Mixed-scope smoke (some pass, some fail per infra missing):
```bash
cd ~/luana-platform && uv run pytest \
  core/luana-core-analytics-engine/tests/test_metric_catalog.py \
  core/luana-core-analytics-engine/tests/test_metric_resolver_supplemental.py \
  core/luana-core-analytics-engine/tests/test_journey_event.py \
  core/luana-core-analytics-engine/tests/test_subscription_split.py \
  core/luana-core-analytics-engine/tests/test_period_pipeline.py
# → 43 passed, 18 failed (test_period_pipeline.py needs infrastructure)
```

### Step 7 — Aggregate test isolation deferred to T-3c

Per spec line 159, aggregate `core/luana-core-analytics-engine/tests/` GREEN status is **NOT a T-3a acceptance criterion**. T-3c explicitly owns aggregate GREEN.

Cross-package aggregate test isolation (running `pytest core/` and seeing analytics tests interact with crm tests) was the Sonnet rabbit hole. We defer this verification to T-3c, when:
- infrastructure exists → model registration completes
- workers exist → scheduler tests don't ERROR on collection
- The full test runner strategy (per-package Makefile-driven runs) lands

The conftest.py JSONB/UUID patch at module-load time (lines 14-81) is structurally correct. It mirrors `AISALESHT/backend/tests/conftest.py`. We do NOT touch it in T-3a; T-3c gets the final aggregate runner adjustments.

## Validators addressed

- **V-NF-2 (lift fidelity)**: scope = api + application + domain. Verbatim, names preserved, no logic refactors. ✓
- **V-F-py-2 (analytics tests GREEN)**: DEFERRED to T-3c per spec. ✓

## Files changed

```
A  core/luana-core-analytics-engine/README.md                              (1 KB)
A  core/luana-core-analytics-engine/pyproject.toml                         (~700 B)
A  core/luana-core-analytics-engine/src/luana_core_analytics_engine/__init__.py
A  core/luana-core-analytics-engine/src/luana_core_analytics_engine/api/*.py             (5 files)
A  core/luana-core-analytics-engine/src/luana_core_analytics_engine/application/**/*.py  (~50 files)
A  core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/*.py          (13 files)
A  core/luana-core-analytics-engine/tests/conftest.py
A  core/luana-core-analytics-engine/tests/test_*.py                        (~75 files, 920 tests, 18 file-level errors documented)
A  core/luana-core-analytics-engine/docs/                                  (lifted docs)
A  core/luana-core-analytics-engine/scripts/                               (lifted scripts; ETL contract regen lands T-3b/T-3c)
M  core/luana-core-platform/pyproject.toml                                 (+1 line: passlib>=1.7.4)
M  uv.lock                                                                 (regen for passlib resolution)
```

## Deferred to T-3b

- `infrastructure/` (cache, etl, models, providers, repositories, sync) — ~70 files
- 18 test files that reference `luana_core_analytics_engine.infrastructure.*` start collecting cleanly

## Deferred to T-3c

- `workers/` (manychat_sync, scheduler, settings, tasks) — 4 files
- Aggregate GREEN: full `pytest core/luana-core-analytics-engine/tests/` passes
- Aggregate cross-package isolation: full `pytest core/` passes (Makefile-driven per-package strategy)
- ETL extraction-contract Makefile + idempotency smoke (per 05-guidelines.md §1.6)

## AISALESHT untouched verification

```bash
cd /home/chris/AISALESHT && git diff ca1ab02f HEAD --name-only
# → empty
cd /home/chris/AISALESHT && git status --short
# → only docs/product/stories/luana-crm-analytics-landing-connections/* (story tracking files,
#   not production code; pre-existing pending updates from /architect ratification)
```

AISALESHT production code is untouched. Story tracking docs (checkpoint.md + 5 architect artifacts) are the only outstanding changes — those are out-of-scope for T-3a and will be staged with subsequent /pm bookkeeping commits.
