# Phase 1: Critical Bug Fixes - Research

**Researched:** 2026-03-15
**Domain:** Meta Graph API, facebook-business SDK multi-tenancy, Google Analytics Data API
**Confidence:** HIGH

## Summary

Phase 1 addresses three critical bugs blocking real data flow: (1) Meta Graph API uses deprecated v19.0 which has been returning HTTP 400 since September 2025, (2) the `FacebookAdsApi.init()` singleton pattern sets global state that can leak between tenants in a multi-tenant async environment, and (3) the Google Analytics adapter only has Admin API for property discovery but lacks the Data API client needed for `runReport()` metric retrieval.

The codebase already has correct per-request adapter instantiation in the API routes (each endpoint creates a new `MetaAdapter` instance with the tenant's token). However, `MetaAdapter._init_api()` calls `FacebookAdsApi.init()` which sets a class-level `_default_api` -- this is the singleton leak vector. The fix is to create per-instance `FacebookAdsApi` objects and pass them explicitly to SDK objects via the `api` parameter, avoiding the global default entirely.

**Primary recommendation:** Update API version constant to v22.0+ (v24.0 recommended for stability), replace `FacebookAdsApi.init()` with per-instance API creation, add `google-analytics-data` package and build a reusable `runReport()` wrapper in the connections module, and wrap sync calls in `asyncio.to_thread()`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Meta API: Use latest stable Meta Graph API version at implementation time (likely v22.0+), not a hardcoded pin
- Meta API: Pin `facebook-business` package to a compatible version range in requirements.txt
- Meta API: Update all references in `meta.py` (line 23 constant + URL constructions)
- Meta SDK: Verification with both sequential AND concurrent multi-tenant tests
- Meta SDK: If tests reveal `FacebookAdsApi.init()` leaks global state, fix in this phase
- Meta SDK: Audit Meta adapter for sync-in-async patterns
- GA4: Build a flexible `runReport()` wrapper that accepts arbitrary dimensions/metrics as parameters
- GA4: Add `analytics.readonly` scope to existing Google Analytics OAuth flow
- GA4: Add `google-analytics-data` package dependency to requirements.txt
- GA4: Both unit tests (mocked) AND integration test hitting real GA4 property
- Sync-in-async: Fix sync-in-async issue in `google_analytics.py:111` via `asyncio.to_thread()`
- Sync-in-async: Audit Meta adapter for same pattern and fix if found
- Sync-in-async: Keep fixes scoped to connections module adapters touched in this phase

### Claude's Discretion
- Where GA4 Data API client lives (connections vs analytics module) -- decide based on DDD module boundaries
- Exact facebook-business version range to pin
- Test implementation details (pytest fixtures, mock strategy)
- Whether to convert sync methods to fully async or use `asyncio.to_thread()` wrapper

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUGFIX-01 | Update Meta API version from deprecated v19.0 to v22.0+ | Graph API v24.0 is latest stable (Oct 2025); v22.0 minimum since Sept 2025. Update constant + all URL references. |
| BUGFIX-02 | Fix Meta SDK singleton pattern -- must be per-request/per-tenant | `FacebookAdsApi.init()` sets class-level `_default_api`. Fix: create per-instance API objects, avoid global state. |
| BUGFIX-03 | Implement GA4 Data API client (`BetaAnalyticsDataClient.runReport()`) | `google-analytics-data>=0.20.0` package. Client accepts `credentials` param for OAuth. Scope already configured. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| facebook-business | >=22.0,<26.0 | Meta Graph API / Marketing API SDK | Official Meta SDK; version 25.0.0 is latest (Mar 2026), aligns with Graph API v25.0 |
| google-analytics-data | >=0.20.0 | GA4 Data API (BetaAnalyticsDataClient) | Official Google Cloud client for GA4 reporting; v0.20.0 latest (Jan 2026) |
| google-auth-oauthlib | >=1.2.0 | OAuth2 credential management (already installed) | Required for user-credential OAuth flows |
| google-api-python-client | >=2.118.0 | Google Admin API (already installed) | Used for property discovery, remains unchanged |
| httpx | ==0.26.0 | Async HTTP client (already installed) | Used for direct Graph API calls in MetaAdapter |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0.0 | Test framework (already installed) | All unit and integration tests |
| pytest-asyncio | >=0.23.5 | Async test support (already installed) | Testing async adapter methods |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| facebook-business SDK | Direct httpx to Graph API | Already using httpx for most calls; SDK only used for `User.api_get()` in `get_user_profile()`. Could eliminate SDK dependency entirely but adds maintenance burden for future Marketing API needs (Phase 4+). Keep SDK. |

**Installation:**
```bash
# Add to backend/requirements.txt
facebook-business>=22.0,<26.0
google-analytics-data>=0.20.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/src/modules/connections/
  infrastructure/
    channels/
      meta.py              # MetaAdapter (update API version, fix singleton)
      google_analytics.py  # GoogleAnalyticsAdapter (add runReport wrapper, fix sync)
```

The GA4 Data API client should live in `connections/infrastructure/channels/google_analytics.py` alongside the existing Admin API adapter. Rationale: the connections module owns all external API integrations and credential management. The analytics module will consume this through a service interface in Phase 2 (INFRA-02).

### Pattern 1: Per-Instance FacebookAdsApi (replacing singleton)
**What:** Create `FacebookAdsApi` instances per-request instead of calling `FacebookAdsApi.init()` which sets global state.
**When to use:** Every time the MetaAdapter needs SDK functionality.
**Example:**
```python
# Source: facebook-business SDK documentation + DeepWiki analysis
from facebook_business.api import FacebookAdsApi
from facebook_business.session import FacebookSession

class MetaAdapter:
    API_VERSION = "v24.0"  # Updated from v19.0

    def __init__(self, app_id=None, app_secret=None, access_token=None):
        self.app_id = app_id or settings.META_APP_ID
        self.app_secret = app_secret or settings.META_APP_SECRET
        self.access_token = access_token
        self._api_instance = None

        if self.access_token:
            self._init_api()

    def _init_api(self):
        """Create a per-instance API object. Never call FacebookAdsApi.init()."""
        session = FacebookSession(
            app_id=self.app_id,
            app_secret=self.app_secret,
            access_token=self.access_token,
        )
        self._api_instance = FacebookAdsApi(session, api_version=self.API_VERSION)
        # Do NOT set as default: FacebookAdsApi.set_default_api(self._api_instance)

    async def get_user_profile(self):
        if not self._api_instance:
            raise ValueError("Access token not initialized")

        api = self._api_instance  # Capture for closure
        def _get_profile():
            me = User(fbid="me", api=api)  # Pass explicit api instance
            return me.api_get(fields=["id", "name", "email"])

        profile = await asyncio.to_thread(_get_profile)
        return profile.export_all_data()
```

### Pattern 2: GA4 runReport Wrapper with OAuth Credentials
**What:** Generic `runReport()` method that accepts dimensions, metrics, date ranges.
**When to use:** Any GA4 metric retrieval (Phases 1, 4, 6, future stages).
**Example:**
```python
# Source: Google Analytics Data API quickstart + googleapis.dev docs
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
)
from google.oauth2.credentials import Credentials

class GoogleAnalyticsAdapter:
    # ... existing __init__ with client_config and credentials_data ...

    def _get_data_client(self) -> BetaAnalyticsDataClient:
        """Create GA4 Data API client using OAuth credentials."""
        if not self.creds:
            raise ValueError("Credentials not initialized")
        return BetaAnalyticsDataClient(credentials=self.creds)

    async def run_report(
        self,
        property_id: str,
        dimensions: list[str],
        metrics: list[str],
        start_date: str = "30daysAgo",
        end_date: str = "today",
    ) -> dict:
        """Execute a GA4 runReport call. Returns normalized dict."""
        client = self._get_data_client()
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )

        # BetaAnalyticsDataClient.run_report() is synchronous
        response = await asyncio.to_thread(client.run_report, request)

        return self._normalize_report_response(response)

    def _normalize_report_response(self, response) -> dict:
        """Convert GA4 response to a plain dict structure."""
        rows = []
        for row in response.rows:
            rows.append({
                "dimensions": [dv.value for dv in row.dimension_values],
                "metrics": [mv.value for mv in row.metric_values],
            })
        return {
            "row_count": response.row_count,
            "rows": rows,
            "metadata": {
                "dimensions": [h.name for h in response.dimension_headers],
                "metrics": [h.name for h in response.metric_headers],
            },
        }
```

### Pattern 3: Sync-in-Async Fix
**What:** Wrap synchronous library calls in `asyncio.to_thread()`.
**When to use:** Any blocking I/O call inside an async function.
**Example:**
```python
# Fix for google_analytics.py:111 — exchange_code() is sync but called in async context
# In the API router (google_analytics.py api):
token_data = await asyncio.to_thread(adapter.exchange_code, code, redirect_uri)

# Also: get_account_summaries() is sync
summaries = await asyncio.to_thread(adapter.get_account_summaries)
```

### Anti-Patterns to Avoid
- **Calling `FacebookAdsApi.init()` anywhere:** Sets global `_default_api` class variable. In async/multi-tenant, two concurrent requests will overwrite each other's tokens. Always use per-instance API objects.
- **Hardcoding API version in URLs:** Use `self.API_VERSION` constant consistently. Never have `f"https://graph.facebook.com/v19.0/..."` -- always `f"{self.BASE_URL}/{self.API_VERSION}/..."`.
- **Calling sync SDK methods without `asyncio.to_thread()`:** `BetaAnalyticsDataClient.run_report()`, `flow.fetch_token()`, and `User.api_get()` all perform blocking I/O. In FastAPI async endpoints, these block the event loop.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GA4 report queries | Custom HTTP calls to GA4 REST API | `google-analytics-data` SDK (`BetaAnalyticsDataClient`) | Handles pagination, retries, auth refresh, protobuf parsing |
| Meta Graph API auth | Custom OAuth implementation | `facebook-business` SDK + `httpx` for direct Graph calls | Already established pattern in codebase |
| OAuth credential refresh | Manual token refresh logic | `google.oauth2.credentials.Credentials` auto-refresh | Google auth library handles refresh_token exchange automatically |
| Async wrapping | Custom thread pool executors | `asyncio.to_thread()` | Python 3.11+ built-in, cleaner than `loop.run_in_executor()` |

**Key insight:** The codebase already has a mixed pattern -- SDK for some operations, direct httpx for others. Don't try to unify; just fix the bugs in each path.

## Common Pitfalls

### Pitfall 1: FacebookAdsApi Global State Race Condition
**What goes wrong:** Two async requests call `FacebookAdsApi.init()` with different tenant tokens. Request A sets token_A, Request B sets token_B, then Request A reads data using token_B.
**Why it happens:** `FacebookAdsApi.init()` stores the API instance as a class-level variable `_default_api`. In async/concurrent execution, this is shared across all requests.
**How to avoid:** Never call `FacebookAdsApi.init()`. Create `FacebookAdsApi(session)` instances directly and pass `api=instance` to all SDK objects.
**Warning signs:** Intermittent wrong data in responses, data from tenant A appearing in tenant B's responses, test passes individually but fails under concurrency.

### Pitfall 2: Google OAuth Scope Mismatch
**What goes wrong:** Existing connected tenants have tokens with only `analyticsadmin` scope. Adding `analytics.readonly` to the SCOPES list doesn't retroactively grant it.
**Why it happens:** OAuth tokens are scoped at authorization time. Adding a scope to the code requires re-authorization.
**How to avoid:** The existing code already has `analytics.readonly` in the SCOPES list (line 16-18 of google_analytics.py). Users who authorized before this scope was added will need to disconnect and reconnect. Document this in release notes.
**Warning signs:** `run_report()` returns 403 "insufficient permissions" for some tenants but works for new connections.

### Pitfall 3: BetaAnalyticsDataClient Is Synchronous
**What goes wrong:** Calling `client.run_report()` directly in an async FastAPI handler blocks the event loop, causing timeouts for other concurrent requests.
**Why it happens:** The `google-analytics-data` Python client uses gRPC under the hood but exposes a synchronous API. There is an async client (`BetaAnalyticsDataAsyncClient`) but it uses gRPC async which may conflict with the existing httpx-based async patterns.
**How to avoid:** Use `asyncio.to_thread(client.run_report, request)` to run the sync client in a thread pool. This is the simplest and safest approach.
**Warning signs:** Endpoint hangs for 2-3 seconds, other endpoints become unresponsive during GA4 calls.

### Pitfall 4: Meta API Version Mismatch Between SDK and Direct Calls
**What goes wrong:** Updating `API_VERSION` constant but the `facebook-business` SDK internally uses a different version for its own API calls.
**Why it happens:** The SDK has its own version default. When creating `FacebookAdsApi(session, api_version=...)`, the version must be passed explicitly.
**How to avoid:** Always pass `api_version=self.API_VERSION` when constructing `FacebookAdsApi`. Verify both SDK calls and direct httpx calls use the same version.
**Warning signs:** Some API calls succeed (direct httpx) while SDK calls fail (wrong version).

### Pitfall 5: facebook-business Package Version vs API Version
**What goes wrong:** Installing `facebook-business==22.0.0` doesn't mean it supports Graph API v24.0.
**Why it happens:** The package version roughly tracks the Marketing API version, but they're not 1:1. Newer SDK versions add support for newer API features.
**How to avoid:** Pin to `>=22.0,<26.0`. The SDK version 25.0.0 (latest) supports Graph API v22.0 through v25.0. Use >=22.0 as floor since that's when v22.0 API support was solidified.
**Warning signs:** `ValueError` or unsupported version errors from the SDK.

## Code Examples

### Existing Code That Must Change

#### 1. meta.py Line 23 -- API Version Constant
```python
# BEFORE (broken since Sept 2025)
API_VERSION = "v19.0"

# AFTER
API_VERSION = "v24.0"  # Stable, expires TBD. v22.0 minimum enforced by Meta.
```

#### 2. meta.py Lines 42-52 -- _init_api() Singleton
```python
# BEFORE (global state leak)
def _init_api(self):
    FacebookAdsApi.init(
        app_id=self.app_id,
        app_secret=self.app_secret,
        access_token=self.access_token,
        api_version=self.API_VERSION,
    )

# AFTER (per-instance, thread-safe)
def _init_api(self):
    from facebook_business.session import FacebookSession
    session = FacebookSession(
        app_id=self.app_id,
        app_secret=self.app_secret,
        access_token=self.access_token,
    )
    self._api_instance = FacebookAdsApi(session, api_version=self.API_VERSION)
```

#### 3. google_analytics.py API router Line 111 -- Sync in Async
```python
# BEFORE (blocks event loop)
token_data = adapter.exchange_code(code, redirect_uri)

# AFTER
token_data = await asyncio.to_thread(adapter.exchange_code, code, redirect_uri)
```

#### 4. google_analytics.py API router -- get_account_summaries sync calls
```python
# BEFORE (blocks event loop in callback, test, properties endpoints)
summaries = adapter.get_account_summaries()

# AFTER
summaries = await asyncio.to_thread(adapter.get_account_summaries)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Meta Graph API v19.0 | v22.0+ minimum, v24.0 recommended | Sept 2025 (Meta enforcement) | v19.0 returns HTTP 400 errors |
| `FacebookAdsApi.init()` singleton | Per-instance `FacebookAdsApi(session)` | Always available, just not used | Prevents multi-tenant data leaks |
| GA4 Admin API only | Admin API + Data API (`runReport()`) | GA4 Data API stable since 2023 | Enables actual metric retrieval |
| Sync SDK calls in async handlers | `asyncio.to_thread()` wrapping | Python 3.9+ (3.11 recommended) | Prevents event loop blocking |

**Deprecated/outdated:**
- Meta Graph API v19.0: Expired, returns 400. Minimum is v22.0 since Sept 9, 2025.
- Meta Graph API v20.0: Expires Sept 24, 2026. Don't target this version.
- `FacebookAdsApi.init()`: Not deprecated per se, but architecturally wrong for multi-tenant. The per-instance pattern has always been available.

## Open Questions

1. **GA4 Property ID Storage**
   - What we know: OAuth flow stores `account_count` in config. Property discovery uses Admin API.
   - What's unclear: Where is the selected GA4 property ID stored? The user must select a property after connecting for `runReport()` to work.
   - Recommendation: Check if `ChannelConnectionModel.config` stores a `property_id` field. If not, the integration test should use a known Visionarias property ID. Property selection UX is out of scope for Phase 1 -- the `runReport()` wrapper just needs to accept `property_id` as a parameter.

2. **facebook-business SDK Thread Safety Beyond init()**
   - What we know: `FacebookAdsApi.init()` sets global state. Per-instance API objects are safe.
   - What's unclear: Whether `User(fbid="me", api=instance)` with an explicit API instance is fully thread-safe internally.
   - Recommendation: The existing code already wraps SDK calls in `asyncio.to_thread()` (line 142 of meta.py), which runs them in separate threads. Combined with per-instance API objects, this should be safe. The concurrent test will verify.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0.0 + pytest-asyncio >=0.23.5 |
| Config file | `backend/pyproject.toml` (no pytest section yet -- uses defaults) |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUGFIX-01 | Meta API calls use v22.0+ and return valid responses | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_api_version.py -x` | No -- Wave 0 |
| BUGFIX-02a | Sequential multi-tenant Meta requests return correct data | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_tenant_isolation.py::test_sequential -x` | No -- Wave 0 |
| BUGFIX-02b | Concurrent multi-tenant Meta requests never cross-contaminate | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_tenant_isolation.py::test_concurrent -x` | No -- Wave 0 |
| BUGFIX-03a | GA4 runReport wrapper returns normalized data (mocked) | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_ga4_data_client.py -x` | No -- Wave 0 |
| BUGFIX-03b | GA4 runReport returns real session data from Visionarias property | integration | `docker exec -t visionarias_brain_dev pytest tests/integration/test_ga4_live.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/connections/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/connections/test_meta_api_version.py` -- covers BUGFIX-01: verify API_VERSION constant, verify all URL constructions use correct version
- [ ] `tests/modules/connections/test_meta_tenant_isolation.py` -- covers BUGFIX-02: sequential + concurrent tenant isolation tests with mocked SDK
- [ ] `tests/modules/connections/test_ga4_data_client.py` -- covers BUGFIX-03: unit tests for runReport wrapper with mocked BetaAnalyticsDataClient
- [ ] `tests/integration/test_ga4_live.py` -- covers BUGFIX-03: integration test hitting real GA4 API (requires credentials, may be skipped in CI)

## Sources

### Primary (HIGH confidence)
- [Meta Graph API Versions](https://developers.facebook.com/docs/graph-api/changelog/versions/) -- v25.0 latest (Feb 2026), v22.0 minimum since Sept 2025, v19.0 expired
- [facebook-business PyPI](https://pypi.org/project/facebook-business/) -- v25.0.0 latest (Mar 10, 2026)
- [google-analytics-data PyPI](https://pypi.org/project/google-analytics-data/) -- v0.20.0 latest (Jan 9, 2026)
- [GA4 Data API Quickstart](https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart-client-libraries) -- Official Python example with BetaAnalyticsDataClient
- [BetaAnalyticsData docs](https://googleapis.dev/python/analyticsdata/latest/data_v1beta/beta_analytics_data.html) -- API reference for run_report

### Secondary (MEDIUM confidence)
- [DeepWiki - Python SDK analysis](https://deepwiki.com/facebook/facebook-business-sdk-codegen/2.2-python-sdk) -- Confirmed singleton pattern in FacebookAdsApi.init(), per-instance API creation via FacebookSession
- [facebook-python-business-sdk GitHub](https://github.com/facebook/facebook-python-business-sdk) -- Source code confirming _default_api class variable pattern

### Tertiary (LOW confidence)
- None -- all findings verified with primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Verified package versions against PyPI, API versions against official Meta changelog
- Architecture: HIGH -- Patterns derived from reading actual codebase + official SDK documentation
- Pitfalls: HIGH -- Singleton issue confirmed by reading SDK source structure; sync-in-async confirmed by reading actual code

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable domain; Meta API versions change quarterly)
