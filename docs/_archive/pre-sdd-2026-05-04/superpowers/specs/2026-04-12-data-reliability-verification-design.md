# Data Reliability Verification System

**Date:** 2026-04-12
**Status:** Design
**Pilot:** Meta (ig-organic, fb-organic, meta-ads)
**Goal:** End-to-end confidence that values displayed in Growth Studio match the source API, with a repeatable protocol enforced on every modification.

---

## Problem

Growth Studio displays metrics extracted from external APIs (Meta, GA4, YouTube, etc.). Today we verify visually that "things render" but have no automated way to know if the **values are correct**. Data can diverge at 3 points:

1. **Extraction** -- the ETL provider parses the API response incorrectly
2. **Aggregation** -- the stage service sums, averages, or transforms incorrectly
3. **Presentation** -- the frontend formats, rounds, or displays incorrectly

We need a system that catches all 3 types of divergence.

---

## Architecture: 4-Layer Verification Protocol

```
Layer 0: ETL Execution
  Trigger extraction for a provider/tenant/date range
  Wait for completion
  Result: official_metrics populated with fresh data

Layer 1: Source Probe
  Call the real external API (Meta Graph API) with same params the ETL used
  Compare raw API values vs official_metrics rows
  Result: "the ETL extracted correctly" (or list of discrepancies)

Layer 2: Pipeline Integrity
  Read official_metrics for a known tenant/date
  Call our backend API endpoints
  Compare DTO field values vs raw DB values
  Result: "the stage service transforms correctly"

Layer 3: UI Fidelity
  Call our backend API to get expected values
  Navigate Growth Studio in Playwright
  Assert visible text/numbers match expected values
  Result: "the frontend displays what the backend returns"
```

Each layer is **independently runnable**. When you modify a provider, run Layers 0+1. When you modify a stage service, run Layer 2. When you modify a frontend component, run Layer 3. When you want full confidence, run all 4.

---

## Layer 0: ETL Execution

### Purpose

Trigger a fresh extraction so Layers 1-3 work with current data, not stale rows from weeks ago.

### Implementation

**File:** `backend/scripts/verify/run_etl.py`

```python
"""
Trigger ETL extraction for a provider and wait for completion.

Usage:
  # Local (default -- uses Docker container)
  python scripts/verify/run_etl.py --provider meta --days 7

  # Production (SSH to VPS)
  python scripts/verify/run_etl.py --provider meta --days 7 --env prod
"""
```

**Behavior:**
1. Resolve tenant_id from env (`VERIFY_TENANT_ID` or `E2E_TENANT_ID`)
2. Call `POST /api/v1/analytics/metrics/sync?days={days}` with `X-Tenant-ID` header
3. Poll until response shows provider completed (or timeout after 5 min)
4. Print summary: loaded/skipped/failed counts
5. Exit 0 if success, 1 if failed

**Env routing:**
- `--env local` (default): `http://localhost:8000`
- `--env prod`: SSH tunnel to `161.132.41.191` port 8000

### Makefile target

```makefile
verify-etl:
	cd backend && .venv/bin/python scripts/verify/run_etl.py \
		--provider $(provider) --days $(days) --env $(env)
```

Usage: `make verify-etl provider=meta days=7` or `make verify-etl provider=meta days=7 env=prod`

---

## Layer 1: Source Probe

### Purpose

Call the real external API directly (bypassing our ETL) and compare the raw response with what the ETL stored in `official_metrics`. This catches extraction bugs: wrong field mapping, missed metrics, type coercion errors.

### Implementation

**Directory:** `backend/scripts/verify/probes/`

Each provider gets one probe file following a base protocol.

**Base protocol:** `backend/scripts/verify/probes/base_probe.py`

```python
@dataclass
class ProbeResult:
    provider: str
    channel_slug: str
    metric_name: str
    date: date
    api_value: float          # raw value from external API
    db_value: float | None    # value in official_metrics (None = missing)
    match: bool               # abs(api - db) / max(api, 1) < threshold
    pct_diff: float           # percentage difference
    api_raw: dict             # raw API response fragment for debugging

@dataclass  
class ProbeReport:
    provider: str
    tenant_id: UUID
    probe_date: date
    date_range: tuple[date, date]
    env: str                  # "local" | "prod"
    results: list[ProbeResult]
    total_metrics: int
    matched: int
    mismatched: int
    missing_in_db: int
    missing_in_api: int
    threshold_pct: float      # default 1.0%

    def to_json(self) -> str: ...
    def to_table(self) -> str: ...  # human-readable table
    def passed(self) -> bool: ...   # all matched
```

**Meta probe:** `backend/scripts/verify/probes/meta_probe.py`

The Meta probe replicates the exact API calls from `meta_provider.py` but independently:

```python
class MetaProbe:
    """
    Calls Meta Graph API directly and compares with official_metrics.
    
    Channels probed:
    - ig-organic: IG Insights API (reach, views, likes, comments, etc.)
    - fb-organic: FB Page Insights (page_reach, page_engagement)
    - meta-ads: Ads Insights API (spend, impressions, clicks, conversions, etc.)
    """
    
    async def probe(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        env: str = "local",
    ) -> ProbeReport:
        # 1. Get credentials (from DB or prod)
        # 2. Call Meta APIs directly (same endpoints as meta_provider.py)
        # 3. Parse raw responses into {channel_slug, metric_name, date} -> value
        # 4. Query official_metrics for same tenant/provider/date_range
        # 5. Compare and produce ProbeReport
```

**Key design decisions:**

1. **Independent API calls** -- the probe does NOT import from `meta_provider.py`. It makes its own HTTP calls using the same endpoints and field lists. This ensures we're verifying the provider, not just re-running it. **Why independent?** If the provider has a bug (e.g., parses `reach` from the wrong JSON path), importing the provider would replicate the bug. The probe's EXPECTED_MAPPINGS serve as a second opinion. **Maintenance cost:** When Meta changes their API or we add a new metric, both the provider and the probe need updating. The probe's mapping dict is deliberately small and flat (no nested logic) to make this cheap.

2. **Field mapping defined in probe** -- each probe has its own `EXPECTED_MAPPINGS` dict that documents what API field should map to what `metric_name`. If the provider changes a mapping, the probe catches the drift.

3. **Threshold-based matching** -- floating point and rounding differences are expected. Default threshold: 1.0%. Configurable per metric (e.g., `reach` is NON_AGGREGABLE so period sums won't match -- probe handles this).

4. **Output as JSON** -- `ProbeReport.to_json()` produces a snapshot that Layer 3 can consume.

### Makefile targets

```makefile
verify-probe-meta:
	cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py \
		--days $(days) --env $(env) --output scripts/verify/snapshots/meta-latest.json

verify-probe: verify-probe-meta  # Add more providers as implemented
```

Usage: `make verify-probe-meta days=7` or `make verify-probe-meta days=7 env=prod`

### Snapshot files

Probe output saved to `backend/scripts/verify/snapshots/{provider}-latest.json`. These are:
- Gitignored (contain real metric values)
- Used by Layer 3 Playwright tests as expected values
- Regenerated on each probe run

---

## Layer 2: Pipeline Integrity

### Purpose

Verify that `official_metrics` rows are correctly transformed by stage services into DTOs. This catches aggregation bugs: wrong SUM/AVG, missing channels, incorrect grouping.

### Implementation

**File:** `backend/tests/verification/test_pipeline_integrity_meta.py`

This is a **pytest test file** with marker `@pytest.mark.verify` that:

1. Reads `official_metrics` directly from DB for a known tenant/date range
2. Calls the backend API endpoint (e.g., `GET /metrics/attraction`)
3. Compares specific DTO fields against expected values computed from raw DB rows

```python
@pytest.mark.verify
class TestMetaPipelineIntegrity:
    """
    Verifies stage services correctly transform official_metrics into DTOs.
    Requires: real data in DB (run Layer 0 first).
    """

    async def test_attraction_ig_organic_metrics_match_db(
        self, async_client, tenant_id, db
    ):
        """
        For ig-organic channel in attraction stage:
        - Read official_metrics WHERE channel_slug='ig-organic' AND provider='meta'
        - Call GET /metrics/attraction
        - Assert DTO.groups['organic_social'].channels['ig-organic'].metrics
          matches the DB rows (sum of daily values for count metrics,
          last value for snapshot metrics)
        """

    async def test_attraction_meta_ads_spend_matches_db(
        self, async_client, tenant_id, db
    ):
        """
        Meta Ads spend in DTO must equal SUM(value) from official_metrics
        WHERE channel_slug='meta-ads' AND metric_name='spend'
        """

    async def test_attraction_meta_ads_derived_metrics(
        self, async_client, tenant_id, db
    ):
        """
        Derived metrics (CPC, CTR, ROAS) in DTO must match
        the formulas applied to raw DB values.
        e.g., CPC = spend / clicks, CTR = clicks / impressions * 100
        """
```

**Test discovery convention:**
- Files: `backend/tests/verification/test_pipeline_integrity_{provider}.py`
- Marker: `@pytest.mark.verify` (excluded from normal `pytest` runs)
- Run explicitly: `cd backend && .venv/bin/pytest -m verify -x -q`
- **Database:** These tests require PostgreSQL (Docker), NOT SQLite in-memory. They read real `official_metrics` rows. The `conftest.py` uses `POSTGRES_DSN` from env to connect to `visionarias_postgres` container.

### What to verify per channel

For each channel, the test checks:

| Check | What | How |
|-------|------|-----|
| **Completeness** | All metrics in DB appear in DTO | Compare metric_name sets |
| **Values** | DTO values match DB aggregation | SUM for additive, LAST for snapshot, AVG for weighted |
| **Currency** | DTO currency matches DB currency | Direct comparison |
| **Grouping** | Channel appears in correct group | Check DTO group key matches channel_registry |
| **Period** | Date range in DTO matches request | Compare DTO.period vs query params |

### Makefile target

```makefile
verify-pipeline:
	cd backend && .venv/bin/pytest tests/verification/ -m verify -x -q --tb=short
```

---

## Layer 3: UI Fidelity

### Purpose

Verify that the frontend displays exactly what the backend API returns. This catches presentation bugs: wrong number formatting, misplaced decimal, incorrect currency symbol, values in wrong cards.

### Implementation

**Directory:** `frontend/e2e/specs/verify/`

These are **Playwright tests** that:
1. Intercept the backend API response (or call it directly)
2. Navigate to the Growth Studio page
3. Assert that specific visible values match the API response

**Key file:** `frontend/e2e/specs/verify/meta-data-fidelity.verify.spec.ts`

```typescript
/**
 * Layer 3: UI Fidelity for Meta channels.
 *
 * Strategy: intercept real backend responses (not mocked),
 * capture the DTO values, then assert the UI shows them correctly.
 *
 * Requires: dev containers running with real data (post Layer 0+1).
 * Run: npx playwright test --project=verify
 */

test.describe('Meta Ads - Data Fidelity @verify', () => {
  let capturedDto: AttractionDetailDTO;

  test.beforeAll(async ({ request }) => {
    // Call backend API directly to capture expected values
    const response = await request.get(
      `${BASE_URL}/api/v1/analytics/metrics/attraction`,
      { headers: { 'X-Tenant-ID': TENANT_ID } }
    );
    capturedDto = await response.json();
  });

  test('meta-ads spend matches API value', async ({ page }) => {
    await page.goto(growthStudioUrl('atraccion-captura'));
    // Find the Meta Ads channel, open sidebar
    // Locate the "Inversión" KPI card
    // Assert displayed value matches formatMoney(capturedDto.spend, capturedDto.currency)
  });

  test('ig-organic reach matches API value', async ({ page }) => {
    // Similar: navigate, find IG Organic, assert reach value
  });

  test('meta-ads ROAS matches API value', async ({ page }) => {
    // Assert ROAS displayed with correct decimal places
  });
});
```

**Snapshot mode (optional, for CI without live APIs):**

When a probe snapshot exists (`backend/scripts/verify/snapshots/meta-latest.json`), the verify tests can read it and use it as expected values instead of calling the live backend. This allows running Layer 3 in CI even when the backend isn't connected to real APIs.

```typescript
// If snapshot exists, use it; otherwise call live backend
const snapshot = loadSnapshot('meta-latest.json');
const expected = snapshot ?? await fetchFromBackend();
```

### Playwright project

Add a `verify` project to `playwright.config.ts`:

```typescript
{
  name: 'verify',
  testMatch: '**/*.verify.spec.ts',
  dependencies: ['setup'],
  use: {
    ...devices['Desktop Chrome'],
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
  },
}
```

### What to verify per dashboard

For each channel dashboard, the test checks:

| Check | What | How |
|-------|------|-----|
| **Hero KPIs** | Each KPI card shows correct value | Match against DTO field |
| **Currency** | Monetary values show correct symbol | Match against DTO.currency |
| **Percentages** | CTR, ROAS, conversion rates display correctly | Match against DTO with formatting rules |
| **Charts** | Chart data points present (not empty) | Assert chart container has data |
| **Tabs** | Each tab loads without error | Navigate all tabs |
| **Period selector** | Changing period updates values | Compare before/after |

### Makefile target

```makefile
verify-ui:
	cd frontend && npx playwright test --project=verify
```

---

## Full Verification Commands

### Complete chain (all 4 layers)

```bash
# Full verification for Meta, local environment
make verify-meta

# Full verification for Meta, production
make verify-meta env=prod
```

Where `verify-meta` is a composite target:

```makefile
verify-meta: verify-etl-meta verify-probe-meta verify-pipeline verify-ui
	@echo "=== Meta verification complete ==="

verify-etl-meta:
	cd backend && .venv/bin/python scripts/verify/run_etl.py --provider meta --days 7 --env $(env)

verify-all: verify-meta  # Add more providers as implemented
```

### Per-layer (for targeted verification after changes)

```bash
# Only re-run ETL
make verify-etl-meta

# Only probe API vs DB
make verify-probe-meta days=7

# Only check pipeline integrity (stage services)
make verify-pipeline

# Only check UI fidelity
make verify-ui
```

---

## Extending to New Providers

When adding a new provider (e.g., GA4), follow this checklist:

### 1. Create the probe

Copy `meta_probe.py` as template. Implement:

```
backend/scripts/verify/probes/{provider}_probe.py
```

Define `EXPECTED_MAPPINGS` for all API fields the provider extracts. The probe must make its own HTTP calls to the provider's API -- never import from the ETL provider class.

### 2. Create pipeline integrity tests

```
backend/tests/verification/test_pipeline_integrity_{provider}.py
```

One test class per stage the provider feeds. Each test reads `official_metrics` and compares with the stage DTO.

### 3. Create UI fidelity tests

```
frontend/e2e/specs/verify/{provider}-data-fidelity.verify.spec.ts
```

One test per dashboard/sidebar that displays the provider's data.

### 4. Add Makefile targets

```makefile
verify-{provider}: verify-etl-{provider} verify-probe-{provider} verify-pipeline verify-ui
verify-etl-{provider}:
	cd backend && .venv/bin/python scripts/verify/run_etl.py --provider {provider} --days 7 --env $(env)
verify-probe-{provider}:
	cd backend && .venv/bin/python scripts/verify/probes/{provider}_probe.py --days $(days) --env $(env)
```

### 5. Update the verify-all target

```makefile
verify-all: verify-meta verify-{provider}
```

---

## Enforcement: Claude Rule

**File:** `.claude/rules/data-reliability.md`

This rule is the primary enforcement mechanism. It triggers whenever any file in the Growth Studio pipeline is modified. See "Enforcement Rule" section below for full content.

### When the rule triggers

Any modification to:

| Layer | Files | Verification required |
|-------|-------|-----------------------|
| **ETL Provider** | `backend/src/modules/analytics/infrastructure/providers/*.py` | Layer 0 + Layer 1 |
| **ETL Pipeline** | `backend/src/modules/analytics/infrastructure/etl/*.py` | Layer 0 + Layer 1 |
| **Stage Service** | `backend/src/modules/analytics/application/services/stage_services/*.py` | Layer 2 |
| **DTO** | `backend/src/modules/analytics/application/dto/*.py` | Layer 2 |
| **Metrics API** | `backend/src/modules/analytics/api/metrics.py` | Layer 2 |
| **Channel Registry** | `backend/src/modules/analytics/application/services/channel_registry.py` | Layer 2 |
| **Frontend Dashboard** | `frontend/src/features/growth-studio/components/sidebar/**` | Layer 3 |
| **Frontend API hooks** | `frontend/src/features/growth-studio/api/*.ts` | Layer 3 |
| **Frontend display** | `frontend/src/features/growth-studio/components/**` | Layer 3 |
| **Format utilities** | `frontend/src/lib/format-money.ts`, `format-date.ts` | Layer 3 |

### What the rule mandates

1. **Before modifying:** Run the relevant layer to capture baseline
2. **After modifying:** Run the same layer to verify no regression
3. **Commit:** Include verification results in commit message or PR description

---

## Enforcement Rule Content

**`.claude/rules/data-reliability.md`**

```markdown
# Data Reliability Verification -- Always Verify, Never Guess

Non-negotiable workflow rule for any task that touches the Growth Studio data pipeline.
The 4-Layer Verification Protocol is the only way to confirm that displayed values are correct.

## The 4 Layers

| Layer | What it verifies | Command | When to run |
|-------|-----------------|---------|-------------|
| 0: ETL Execution | Fresh data in DB | `make verify-etl-{provider}` | Before Layers 1-3 |
| 1: Source Probe | API raw values == official_metrics | `make verify-probe-{provider}` | After touching providers/ETL |
| 2: Pipeline Integrity | official_metrics == stage service DTOs | `make verify-pipeline` | After touching services/DTOs |
| 3: UI Fidelity | Backend API response == UI display | `make verify-ui` | After touching frontend |

## Trigger Matrix

| You modified... | Run these layers |
|----------------|-----------------|
| `providers/*.py` | 0 + 1 + 2 |
| `etl/pipeline.py` or `etl/aggregations.py` | 0 + 1 + 2 |
| `stage_services/*.py` | 2 |
| `dto/*.py` | 2 + 3 |
| `api/metrics.py` or `api/campaigns.py` | 2 + 3 |
| `features/growth-studio/components/**` | 3 |
| `features/growth-studio/api/*.ts` | 3 |
| `lib/format-money.ts` or `lib/format-date.ts` | 3 |

## The 5-step verification workflow

1. Run the baseline (relevant layers) BEFORE making changes
2. Make the change
3. Run the same layers AFTER the change
4. If any layer fails: investigate and fix, do not skip
5. Include in commit message: which layers ran, pass/fail

## Quick commands

make verify-meta              # Full chain (all 4 layers), local
make verify-meta env=prod     # Full chain, production
make verify-pipeline          # Layer 2 only (pytest)
make verify-ui                # Layer 3 only (Playwright)
make verify-probe-meta days=7 # Layer 1 only

## Anti-patterns to refuse

- Modifying a provider without running Layer 1
- Modifying a stage service without running Layer 2
- Modifying a dashboard component without running Layer 3
- Skipping verification because "it's just a small change"
- Using mocked data in verify tests (they exist specifically for real data)
- Committing without noting which verification layers passed
```

---

## Playwright E2E Coverage Expansion

Separate from (but complementary to) the verification system, the existing E2E smoke/regression coverage has gaps. The verify tests (Layer 3) cover data correctness; smoke/regression tests cover UI behavior (navigation, interactions, error states).

### Current coverage

| Area | Smoke | Regression | Verify (new) |
|------|-------|------------|--------------|
| Meta Ads | 3 tests | 11 tests | TBD |
| IG Organic | 6 tests | -- | TBD |
| YouTube | 6 tests | -- | TBD |
| Email/Mail | 7 tests | -- | TBD |
| Attraction/Capture | -- | 2 tests | TBD |
| Nurture/Opportunity | -- | -- | -- |
| Adoption | -- | -- | -- |
| Sales | -- | -- | -- |
| Expansion/Evangelization | -- | -- | -- |
| Campaigns | -- | -- | -- |
| Website/GA4 | -- | -- | -- |

### Coverage expansion plan (post-verification system)

After the verification system is implemented, expand E2E coverage for the remaining stages. Each stage needs:

1. **Smoke test** (renders, navigation works)
2. **Regression test** (interactions, period switching, error states)
3. **Verify test** (data fidelity -- Layer 3)

Priority order:
1. **Meta verify tests** (pilot -- proves the pattern)
2. **Remaining stage smoke tests** (Nurture, Adoption, Sales, Expansion)
3. **Campaigns page** (entirely untested)
4. **Website/GA4 verify tests** (second provider)
5. **Remaining channel verify tests** (YouTube, MailerLite, Shopify)

---

## File Structure Summary

```
backend/
  scripts/
    verify/
      run_etl.py                          # Layer 0: ETL trigger
      probes/
        base_probe.py                     # Base protocol (ProbeResult, ProbeReport)
        meta_probe.py                     # Layer 1: Meta source probe
      snapshots/                          # Gitignored probe output
        meta-latest.json
  tests/
    verification/
      conftest.py                         # Shared fixtures (tenant_id, db, async_client)
      test_pipeline_integrity_meta.py     # Layer 2: Meta pipeline tests

frontend/
  e2e/
    specs/
      verify/
        meta-data-fidelity.verify.spec.ts # Layer 3: Meta UI fidelity

.claude/
  rules/
    data-reliability.md                   # Enforcement rule for Claude

Makefile                                  # verify-* targets
```

---

## Dependencies and Prerequisites

1. **Meta token must be active** -- Layer 0+1 require valid credentials
2. **Dev containers must be running** -- Layer 0 calls the backend API
3. **Real data in DB** -- Layers 2+3 need official_metrics rows
4. **Frontend dev server running** -- Layer 3 needs the Next.js app

---

## Success Criteria

- [ ] `make verify-meta` runs all 4 layers end-to-end and reports pass/fail
- [ ] `make verify-meta env=prod` works against production
- [ ] Meta probe detects intentional data corruption (sanity test)
- [ ] Pipeline integrity test catches a wrong SUM (sanity test)
- [ ] UI fidelity test catches a wrong format (sanity test)
- [ ] `.claude/rules/data-reliability.md` triggers on any Growth Studio file change
- [ ] Adding a second provider (GA4) takes <2 hours following the pattern
- [ ] All 4 layers run independently without dependencies on each other (except Layer 0 populates data for 1-3)
