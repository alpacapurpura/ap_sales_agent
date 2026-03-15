# Phase 1: Critical Bug Fixes - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix three critical issues blocking real data flow: update deprecated Meta API version (v19.0 → latest stable), verify Meta SDK multi-tenant isolation (fix if leaking), and implement missing GA4 Data API client. Also fix sync-in-async issues and pin dependency versions discovered during codebase scout.

</domain>

<decisions>
## Implementation Decisions

### Meta API Version (BUGFIX-01)
- Use the latest stable Meta Graph API version at implementation time (likely v22.0+), not a hardcoded pin
- Pin `facebook-business` package to a compatible version range in requirements.txt (e.g., `>=20.0,<22.0`)
- Update all references in `meta.py` (line 23 constant + URL constructions)

### Meta SDK Multi-Tenant Safety (BUGFIX-02)
- Verification approach: both sequential AND concurrent multi-tenant tests
- Sequential test: two requests with different tenant tokens return correct data
- Concurrent test: two async requests running simultaneously never cross-contaminate
- If tests reveal `FacebookAdsApi.init()` leaks global state: fix in this phase, don't ship a known vulnerability
- Audit Meta adapter for sync-in-async patterns (same audit as GA4)

### GA4 Data API Client (BUGFIX-03)
- Build a flexible `runReport()` wrapper that accepts arbitrary dimensions/metrics as parameters — one client serves all future stages (4-10)
- Add `analytics.readonly` scope to existing Google Analytics OAuth flow (users who already connected will need to re-authorize once)
- Add `google-analytics-data` package dependency to requirements.txt
- Testing: both unit tests (mocked responses for logic) AND integration test hitting real GA4 property for Visionarias tenant

### Sync-in-Async Fixes (Bonus)
- Fix sync-in-async issue in `google_analytics.py:111` — wrap `exchange_code()` in `asyncio.to_thread()`
- Audit Meta adapter for the same pattern and fix if found
- Keep fixes scoped to connections module adapters touched in this phase

### Claude's Discretion
- Where GA4 Data API client lives (connections vs analytics module) — decide based on DDD module boundaries
- Exact facebook-business version range to pin
- Test implementation details (pytest fixtures, mock strategy)
- Whether to convert sync methods to fully async or use `asyncio.to_thread()` wrapper

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MetaAdapter` in `connections/infrastructure/channels/meta.py`: Per-request instantiation pattern already correct, API_VERSION constant at line 23
- `GoogleAnalyticsAdapter` in `connections/infrastructure/channels/google_analytics.py`: Admin API only, uses `googleapiclient.discovery.build()`
- `EncryptedJSON` column type on `ChannelConnectionModel`: Transparent credential encryption/decryption
- `ChannelConnectionRepository.get_active(tenant_id, channel_type)`: Tenant-isolated credential retrieval

### Established Patterns
- Per-request adapter instantiation (Meta): Each endpoint creates a new adapter instance — safe pattern
- OAuth flow: `exchange_code()` → store encrypted credentials → `get_active()` for retrieval
- Tenant isolation: All queries filter by `tenant_id` via `X-Tenant-ID` header → `get_current_user` dependency
- Requirements file: `backend/requirements.txt` — some packages pinned, some not

### Integration Points
- `meta.py:23` — `API_VERSION = "v19.0"` → change to latest stable
- `meta.py:48` — `FacebookAdsApi.init(api_version=self.API_VERSION)`
- `meta.py:83,98,112,158` — API version in Graph API URLs
- `google_analytics.py:84` — `build('analyticsadmin', 'v1beta', ...)` Admin API only
- `google_analytics.py:111` — sync `exchange_code()` called in async context
- `requirements.txt:41` — `facebook-business` unpinned
- `requirements.txt:33-34` — `google-auth-oauthlib>=1.2.0`, `google-api-python-client>=2.118.0`

</code_context>

<specifics>
## Specific Ideas

- GA4 client should be a reusable wrapper — Phase 4 (organic search), Phase 6 (Mailerlite engagement via GA4 events), and future stages will all call it with different dimensions/metrics
- Meta SDK test should simulate real production conditions: two different tenant tokens making concurrent requests to the same process
- The "proof of life" for GA4 should demonstrate a real `runReport()` call returning session data from Visionarias' connected GA4 property

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-critical-bug-fixes*
*Context gathered: 2026-03-15*
