# Growth Studio Sync & Instagram Data Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 bugs that prevent Growth Studio sync from completing and Instagram organic metrics from appearing.

**Architecture:** All bugs are in the analytics module's ETL pipeline. Three are data-layer issues (credential key mismatch, API parameter missing, staging table cleanup), one is an API-layer crash (Redis string handling). All fixes are minimal, targeted, and independent.

**Tech Stack:** FastAPI, Redis (decode_responses=True), Meta Graph API v24.0, SQLAlchemy 2.0

---

## Bug Summary

| # | Bug | Impact | Root Cause |
|---|-----|--------|------------|
| 1 | `metrics.py:323` — `.decode()` on Redis string | **500 on every sync** (blocker) | Redis client configured with `decode_responses=True` returns `str`, not `bytes` |
| 2 | IG account ID not resolved | IG organic returns `[]` silently | Credentials store ID under `tracked_ig_id`, code looks for `instagram_account_id` |
| 3 | IG Insights API 400 error | IG organic extraction fails | Graph API v24.0 requires `metric_type=total_value` for day-period IG metrics |
| 4 | UniqueViolation on staging_metrics | Sync fails on re-run | Stale staging rows from prior failed runs conflict with new inserts |

## Files Overview

| File | Change | Bug |
|------|--------|-----|
| `backend/src/modules/analytics/api/metrics.py:323` | Remove `.decode()` | #1 |
| `backend/src/modules/analytics/infrastructure/providers/meta_provider.py` | IG ID fallback + `metric_type` param | #2, #3 |
| `backend/src/modules/analytics/infrastructure/repositories/staging_repository.py` | Add `delete_by_tenant_provider()` | #4 |
| `backend/src/modules/analytics/infrastructure/etl/pipeline.py:151` | Call staging cleanup before insert | #4 |
| `backend/src/modules/analytics/application/services/etl_service.py:491` | Call staging cleanup before insert in `run_initial_load` | #4 |

## Audit Checklist (Changes Already Applied)

Before executing, the implementer MUST audit the current state of each file against this plan. Some changes were partially applied in a prior attempt. This plan documents the **correct final state** for each file.

---

### Task 1: Fix Redis `.decode()` crash (Bug #1 — BLOCKER)

**Files:**
- Modify: `backend/src/modules/analytics/api/metrics.py:323`

This is the reason the user sees "Failed to fetch". The sync endpoint crashes with 500 before any extraction begins.

**Root cause:** `redis_client` is created with `decode_responses=True` (see `backend/src/core/database.py:22`), so `.get()` returns `str`, not `bytes`. Calling `.decode()` on a `str` raises `AttributeError`.

- [ ] **Step 1: Fix the `.decode()` call**

In `metrics.py:323`, change:
```python
# Before (crashes):
elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last_sync.decode())

# After (correct):
elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last_sync)
```

- [ ] **Step 2: Run lint**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src/modules/analytics/api/metrics.py --no-cache"
```
Expected: `All checks passed!`

- [ ] **Step 3: Verify via logs**

Trigger a sync from Growth Studio or via curl, then check:
```bash
docker logs visionarias_brain_dev --tail 20 2>&1 | grep -E 'sync.*500|decode|AttributeError'
```
Expected: No errors. The POST /sync should return 200.

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/api/metrics.py
git commit -m "fix(analytics): remove .decode() on Redis string in sync cooldown

Redis client uses decode_responses=True, so .get() returns str not bytes.
Calling .decode() crashed the sync endpoint with 500."
```

---

### Task 2: Audit IG account ID resolution (Bug #2 — already applied)

**Files:**
- Verify: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`

The Meta connection stores the IG account ID under the key `tracked_ig_id`. The provider code looked for `instagram_account_id` (non-existent key) → returned `[]` silently → zero ig-organic metrics.

**Correct state** — these 3 locations must use the fallback pattern:

1. `extract_period_metrics` (~L108):
```python
ig_user_id = (
    credentials.get("instagram_business_account_id")
    or credentials.get("tracked_ig_id")
    or credentials.get("instagram_account_id")
)
```

2. `_extract_instagram_organic` (~L339):
```python
ig_account_id = (
    credentials.get("instagram_account_id")
    or credentials.get("tracked_ig_id")
    or credentials.get("instagram_business_account_id")
)
```

3. `_extract_instagram_organic_daily` (~L874):
```python
ig_account_id = (
    credentials.get("instagram_account_id")
    or credentials.get("tracked_ig_id")
    or credentials.get("instagram_business_account_id")
)
```

- [ ] **Step 1: Verify all 3 locations have the fallback pattern**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && grep -n 'tracked_ig_id' src/modules/analytics/infrastructure/providers/meta_provider.py"
```
Expected: 3 occurrences (lines ~110, ~341, ~876).

- [ ] **Step 2: Verify NO other places lookup IG ID without fallback**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && grep -n 'instagram_account_id\|instagram_business_account_id' src/modules/analytics/infrastructure/providers/meta_provider.py"
```
Expected: Each occurrence is part of a multi-line `or` chain that includes `tracked_ig_id`.

---

### Task 3: Audit `metric_type=total_value` on IG Insights (Bug #3 — already applied)

**Files:**
- Verify: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`

Meta Graph API v24.0 requires `metric_type=total_value` for IG Insights metrics like views, likes, shares, etc. Without it, the API returns 400: `"The following metrics (...) should be specified with parameter metric_type=total_value"`.

**Correct state** — these 3 IG Insights calls must include `"metric_type": "total_value"`:

1. `_extract_instagram_organic` (~L354) — params for `period=day`
2. `_extract_instagram_organic_daily` (~L889) — params for `period=day`
3. `_extract_ig_organic_period` (~L162) — params for `period=week/days_28`

The demographics calls at ~L430 and ~L963 already have `metric_type=total_value` (pre-existing).

- [ ] **Step 1: Verify all 3 day/period calls have metric_type**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && grep -c 'metric_type.*total_value' src/modules/analytics/infrastructure/providers/meta_provider.py"
```
Expected: 5 (3 new + 2 pre-existing demographics).

---

### Task 4: Audit staging cleanup (Bug #4 — already applied)

**Files:**
- Verify: `backend/src/modules/analytics/infrastructure/repositories/staging_repository.py`
- Verify: `backend/src/modules/analytics/infrastructure/etl/pipeline.py:151`
- Verify: `backend/src/modules/analytics/application/services/etl_service.py:491`

When a previous ETL run inserts into `staging_metrics` and then fails before commit, stale rows remain. On retry, the same metrics are re-extracted and conflict with the unique constraint `uq_staging_metrics_natural_key`.

The fix: delete stale staging rows for the tenant+provider before inserting fresh data. This is idempotent, runs within the transaction, and aligns with staging table semantics (temporary landing zone).

- [ ] **Step 1: Verify `delete_by_tenant_provider` exists in staging_repository.py**

The method should:
- Accept `tenant_id: UUID` and `provider: str`
- Use `delete(StagingMetricModel).where(...)` with both filters
- Call `self.db.flush()` (not commit — stays in transaction)
- Return `result.rowcount`

- [ ] **Step 2: Verify pipeline.py calls it before bulk_insert**

At ~L151:
```python
self.staging_repo.delete_by_tenant_provider(tenant_id, provider_name)
rows_staged = self.staging_repo.bulk_insert(staging_models)
```

- [ ] **Step 3: Verify etl_service.py calls it before bulk_insert in run_initial_load**

At ~L491:
```python
staging_repo.delete_by_tenant_provider(tenant_id, provider_name)
staging_repo.bulk_insert(staging_models)
```

---

### Task 5: Clean stale DB data and verify end-to-end

**Prerequisite:** Tasks 1-4 complete.

- [ ] **Step 1: Clear stale data to force re-extraction**

```sql
-- Run in postgres container:
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c "
  DELETE FROM staging_metrics
  WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f' AND provider = 'meta';

  DELETE FROM official_metrics
  WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f' AND provider = 'meta';

  DELETE FROM metric_aggregations
  WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f'
  AND channel_slug IN ('fb-organic', 'meta-ads', 'ig-organic');
"
```

- [ ] **Step 2: Wait for server hot-reload**

```bash
docker logs visionarias_brain_dev --tail 5 2>&1 | grep 'Started server'
```
Expected: Recent "Started server process" line.

- [ ] **Step 3: Trigger sync**

From Growth Studio UI or:
```bash
# Clear Redis cooldown first
docker exec -t visionarias_redis redis-cli DEL "sync_all:d68f4af3-3871-4f09-9cbd-a9856235025f"
```

Then trigger sync from the UI.

- [ ] **Step 4: Verify no errors in logs**

```bash
docker logs visionarias_brain_dev --tail 100 2>&1 | grep -iE '500|error|traceback|decode|UniqueViolation|400 Bad' | grep -v 'shopify\|mailerlite'
```
Expected: No meta-related errors.

- [ ] **Step 5: Verify ig-organic data exists**

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c "
  SELECT channel_slug, COUNT(*), MAX(metric_date) as latest
  FROM official_metrics
  WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f'
  GROUP BY channel_slug ORDER BY channel_slug;
"
```
Expected: `ig-organic` row with count > 0.

- [ ] **Step 6: Trigger sync a second time (idempotency test)**

Wait 2 minutes (global cooldown), then sync again. Should NOT fail with UniqueViolation.

- [ ] **Step 7: Run full CI**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```
Expected: All checks passed, all tests pass.

- [ ] **Step 8: Final commit**

```bash
git add backend/src/modules/analytics/infrastructure/providers/meta_provider.py \
        backend/src/modules/analytics/infrastructure/repositories/staging_repository.py \
        backend/src/modules/analytics/infrastructure/etl/pipeline.py \
        backend/src/modules/analytics/application/services/etl_service.py
git commit -m "fix(analytics): resolve IG data missing + staging UniqueViolation

- Resolve IG account ID from tracked_ig_id credential key (3 methods)
- Add metric_type=total_value for IG Insights API v24.0 (3 calls)
- Clear stale staging rows before insert to prevent UniqueViolation"
```
