# Pitfalls Research

**Domain:** Multi-provider marketing analytics integration (Meta, Google, TikTok, Shopify, Mailerlite) — unified funnel dashboard, multi-tenant SaaS
**Researched:** 2026-03-15
**Confidence:** HIGH (critical pitfalls verified against official docs and existing codebase inspection)

---

## Critical Pitfalls

### Pitfall 1: Meta API Version Hardcoded at v19.0 — Already Deprecated

**What goes wrong:**
The existing `MetaAdapter` has `API_VERSION = "v19.0"` hardcoded. As of September 9, 2025, Meta no longer accepts requests to Graph API versions older than v22.0. Any insights, ad account, or page call using v19.0 will return an error. The current codebase is already broken for production Meta API calls.

**Why it happens:**
Meta releases a new major version every ~6 months. Teams pin a version at integration time and forget it. The facebook_business SDK version and the API_VERSION constant drift independently — upgrading the SDK doesn't update the URL version string.

**How to avoid:**
- Immediately update `MetaAdapter.API_VERSION` to `"v22.0"` (minimum) or `"v23.0"` (current as of Q1 2026).
- Do not hardcode the version in the class constant. Read it from `settings.META_API_VERSION` so it can be updated without code changes.
- Add a version-expiry check on application startup: if `API_VERSION` is more than 2 major versions behind the latest known version, log a CRITICAL warning.
- Subscribe to Meta's developer changelog at `developers.facebook.com/docs/graph-api/changelog`.

**Warning signs:**
- HTTP 400 responses with `{"error": {"code": 2635, "message": "You must upgrade your API"}}`.
- Meta dashboard shows deprecation warnings on the app's API version.
- The `/v19.0/` prefix appearing in any HTTP request logs.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — before any real API calls are made. This is a pre-condition for all subsequent phases.

---

### Pitfall 2: Meta Long-Lived Token Expiry Not Handled — Silent Data Gaps

**What goes wrong:**
The `MetaAdapter.exchange_code()` correctly exchanges short-lived tokens for long-lived tokens (~60 days). However, there is no token refresh job anywhere in the codebase. After 60 days, every tenant's Meta connection silently returns 401 errors. The metrics dashboard shows zeros or stale data with no user-facing explanation of why.

**Why it happens:**
Unlike Google OAuth (which issues refresh tokens), Meta's long-lived user tokens simply expire. There is no standard `refresh_token` grant. The only mitigation is a System User token (never expires, for business-owned accounts) or re-prompting the user for consent before expiry. This is non-obvious and easy to miss in initial implementation.

**How to avoid:**
- Store `expires_in` and the token creation timestamp in `credentials` JSONB for every Meta connection.
- Create a background job (Celery beat or FastAPI lifespan task) that runs daily, checks all Meta connections approaching expiry (< 7 days remaining), and either: (a) automatically refreshes if the `fb_exchange_token` endpoint still works, or (b) marks the connection as `requires_reauth` and surfaces a warning banner in the frontend.
- For the Growth Studio dashboard: when fetching metrics, detect 401/expired-token errors from Meta per-tenant and return a `connection_status: "reauth_required"` flag in the DTO instead of crashing or returning zeros.
- Prefer System User tokens for agency/platform use cases — they never expire.

**Warning signs:**
- Meta returns `{"error": {"code": 190, "error_subcode": 463, "message": "Error validating access token: Session has expired"}}`.
- Metrics for a tenant suddenly drop to zero for Meta channels while other channels still show data.
- `updated_at` on a `ChannelConnectionModel` row hasn't changed in > 50 days for Meta connections.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — token lifecycle management must be established before Phase 2 (Stage-by-stage API integration).

---

### Pitfall 3: Attribution Double-Counting — Inflated Conversion Totals

**What goes wrong:**
When a user sees a TikTok ad, then searches on Google, then clicks a Meta retargeting ad before purchasing, all three platforms independently count that conversion. Summing reported conversions across Meta + Google + TikTok yields 150-200% of actual sales. The funnel dashboard Stage 4 (Ventas) will show inflated numbers that destroy trust with the business owner.

**Why it happens:**
Each platform applies its own default attribution window and methodology:
- Meta: 7-day click, 1-day view (default)
- Google Ads: last-click, 30-day conversion window (default)
- TikTok: 7-day click, 1-day view — but multi-session tracking (TikTok Pixel is multi-session, UTMs are single-session) means TikTok often counts conversions that GA4 attributes elsewhere

**How to avoid:**
- The Nicolify funnel's authoritative conversion source must be the internal CRM (`lifecycle_stage = CUSTOMER` transitions), NOT the sum of ad platform reported conversions.
- Use ad platform data for reach/impression/click metrics only (top-funnel). Use the internal CRM + Shopify as the source of truth for actual conversions.
- Display a "Platform Reported" vs "Verified (CRM)" distinction in Stage 4.
- Document attribution windows per channel in code comments so future developers don't accidentally sum cross-platform conversions.
- When displaying cost-per-acquisition: use `ad_spend / crm_new_customers`, not `ad_spend / platform_reported_conversions`.

**Warning signs:**
- Stage 4 (Ventas) shows more sales than the payment processor recorded.
- Sum of Meta + Google + TikTok "conversions" exceeds Shopify orders by > 30%.
- A single Shopify order ID appears in multiple platform conversion reports.

**Phase to address:**
Phase 2 (Stage implementations) — specifically when building Stage 4 (Ventas) and Stage 0 (Atracción) metrics. The CRM-as-truth pattern must be established before any conversion metrics are rendered.

---

### Pitfall 4: GA4 Data API Not Implemented — Only Admin API Exists

**What goes wrong:**
The current `GoogleAnalyticsAdapter` builds an `analyticsadmin` service (`v1beta`), which only covers property management (listing properties, accounts). It has zero ability to call `runReport()` for actual sessions, events, or traffic data. All organic search metrics in Stage 0 (Atracción) — including `google-organic`, `direct`, `ai-search` — have no data source and will fall through to mocks indefinitely.

**Why it happens:**
GA4 has two separate API surfaces with separate service names: `analyticsadmin` for account management and `analyticsdata` (the Data API) for reporting. They have different SDK modules (`google-analytics-admin` vs `google-analytics-data`), different auth scopes, and different base URLs. Initial integration touched only the Admin API for property discovery.

**How to avoid:**
- Add `google-analytics-data` to backend dependencies (`pip install google-analytics-data`).
- Create a separate `GA4DataAdapter` class (or extend `GoogleAnalyticsAdapter`) that builds from `BetaAnalyticsDataClient` and exposes a `run_report(property_id, metrics, dimensions, date_range)` method.
- The same OAuth credentials and `analytics.readonly` scope work for both APIs — no new OAuth flow needed.
- Know the GA4 data freshness constraint: data can lag 24-48 hours. Never show "today" data as final; mark it as "preliminary" in the UI.
- For high-traffic properties (>10M sessions/month), GA4 sampling applies. Use the `keepEmptyRows` and `samplingLevel` parameters in `runReport` and detect `samplingMetadata` in responses to flag sampled results.

**Warning signs:**
- `google-analytics-data` not found in `requirements.txt` or `pyproject.toml`.
- `get_service()` returns an `analyticsadmin` resource — any attempt to call `.runReport()` will fail with `AttributeError`.
- Stage 0 organic metrics always show zero or mock values even when Google is connected.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — GA4 Data API client must exist before any organic traffic metrics can be implemented.

---

### Pitfall 5: Google OAuth Refresh Token Silent Invalidation

**What goes wrong:**
Google OAuth refresh tokens issued by a GCP project in "Testing" status expire after 7 days. When the project is promoted to "Production" (published), user-granted tokens become permanent. However, if any user revokes access, or if more than 50 users connect and the 51st token is issued, older tokens begin failing silently. In a multi-tenant system, this means specific tenants lose Google data without any explicit error surfacing to the dashboard.

There is also a 100-token-per-client limit across all users — once exceeded, the oldest tokens are invalidated.

**Why it happens:**
Google's refresh token lifecycle is complex and poorly documented in one place. Development happens with Testing-mode apps (7-day tokens), and the shift to Production is sometimes done late in the project, causing all existing tenant tokens to become permanent while making developers believe the refresh mechanism is robust.

**How to avoid:**
- Ensure the GCP OAuth consent screen is published (Production status) before any real tenant connects.
- Store token creation timestamps and track `invalid_grant` errors per tenant. On `invalid_grant`, immediately set `is_active = False` on the `ChannelConnectionModel` and enqueue a `reauth_required` notification.
- Do not exceed 50 tokens per account during testing — rotate test credentials frequently.
- Use the `google-auth` library's built-in automatic refresh (pass `credentials` object, not raw token string, to all API calls) so expiry of the 1-hour access token is handled transparently.

**Warning signs:**
- `invalid_grant: Token has been expired or revoked` errors in logs for Google connections.
- Google-sourced metrics (GA4, YouTube Analytics, Google Ads) silently return zero for specific tenants.
- GCP Console shows OAuth consent screen in "Testing" status while real users are connected.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — token health monitoring infrastructure needed before any Google API calls are made in production.

---

### Pitfall 6: Multi-Tenant Token Cross-Contamination via Shared SDK Singleton

**What goes wrong:**
The `MetaAdapter._init_api()` calls `FacebookAdsApi.init(...)` which sets a **global process-level singleton** in the facebook_business SDK. In a multi-tenant async FastAPI application, when Tenant A's request initializes the Facebook SDK with their token, a concurrent Tenant B request that assumes the singleton is already initialized will execute API calls using Tenant A's token. This is a data leak and a security violation.

**Why it happens:**
Many advertising SDKs (facebook_business, some Google client libs) were designed for single-account CLI tools, not multi-tenant servers. They use module-level or class-level global state. This is not obvious from the API surface and is not documented in the integration guides.

**How to avoid:**
- Never use `FacebookAdsApi.init()` at the class level. Instead, create a fresh `FacebookAdsApi` instance per request using the constructor overload: `api = FacebookAdsApi(FacebookSession(app_id, app_secret, access_token))`.
- Pass the `api` instance explicitly to every object that needs it instead of relying on `FacebookAdsApi.get_default_api()`.
- Add a linting rule / code review checklist: "No SDK init calls in request handlers or shared services."
- For Google APIs: use `Credentials` objects per request rather than a module-level service client.
- Write an integration test that fires two concurrent requests with different tenant tokens and asserts each response contains only that tenant's data.

**Warning signs:**
- `FacebookAdsApi.init()` called inside any path reachable from an HTTP request handler.
- Ad account data from one tenant appearing in another tenant's metrics response.
- Race condition flakiness in analytics tests when run in parallel.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — the SDK instantiation pattern must be correct before any multi-tenant API calls are made.

---

### Pitfall 7: Timezone Mismatch Causing Day-Boundary Metric Discrepancies

**What goes wrong:**
Meta, Google Ads, GA4, TikTok, and Shopify each have their own timezone setting configured at the account level. When Nicolify fetches "yesterday's" data using a UTC date range, a Meta account configured to America/New_York will return data that is 5 hours offset from what GA4 (configured to Europe/Madrid) returns. The unified dashboard shows different totals for the "same" day that can never be reconciled. Business owners lose trust in the data.

Concretely: a sale at 11pm NY time is attributed to "today" in Meta but to "tomorrow" in a UTC-normalized system.

**Why it happens:**
APIs accept date strings (e.g., `"2026-03-14"`) and interpret them in the account's configured timezone, not UTC. When multiple providers each interpret the same date string differently, cross-provider comparisons on the same date range are not apple-to-apple.

**How to avoid:**
- Store each connected account's timezone in `config` JSONB of `ChannelConnectionModel` at connection time (retrieve from the API's account metadata).
- When building multi-provider reports, normalize all date ranges to the account's own timezone before sending API requests, then convert returned data to a single canonical timezone (UTC) for storage.
- Display the "as of" timezone to the business owner in the UI: "Data synced to UTC. Your Meta account reports in America/New_York."
- For day-level granularity, accept 1-day boundary ambiguity as normal and document it in the UI with a tooltip.

**Warning signs:**
- Stage 0 totals for "Meta reach" and "GA4 sessions" for the same day don't match when both are connected to the same campaign.
- Metrics jump or drop sharply at midnight UTC even when underlying business activity is continuous.
- Different row counts when using `date_preset=yesterday` vs explicit date strings.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — timezone normalization layer must be part of the base provider adapter interface, not added per-provider later.

---

### Pitfall 8: Meta Insights API Rate Limiting Without Per-Tenant Throttling

**What goes wrong:**
Meta's rate limiting is per-app-token, not per-user-token (for certain limit types). In a multi-tenant system, if 5 tenants all trigger a dashboard refresh simultaneously, they collectively exhaust the app-level rate budget. Meta throttles based on both call count and query complexity — large date ranges and many breakdowns are treated as heavier calls. After exhausting the budget, all tenants see errors for 1-2 hours.

**Why it happens:**
Teams test with one tenant and never hit rate limits. The first time multiple tenants use the dashboard simultaneously, the rate limit is hit. Meta's `X-Ad-Account-Usage` and `X-Business-Use-Case` response headers carry current usage, but most implementations ignore them.

**How to avoid:**
- Implement a per-tenant request queue with configurable concurrency limits (max 2 concurrent Meta API calls per tenant).
- Read and log `X-Business-Use-Case-Usage` and `X-Ad-Account-Usage` headers on every Meta response. Alert when any bucket exceeds 70% usage.
- For large date ranges (> 7 days), use Meta's async insights jobs: POST to `/insights?async=true`, poll `async_status` until `Job Completed`. Do not use synchronous calls for anything beyond a 7-day window.
- Cache insights responses in Redis with a TTL matching the refresh cadence (e.g., 5 minutes for live view, 1 hour for historical). The React Query `staleTime` on the frontend is already set to 5 minutes — the backend cache should match.

**Warning signs:**
- HTTP 400 with `{"error": {"code": 17, "message": "User request limit reached"}}` or code 32.
- Metrics load successfully for some tenants but not others during peak hours.
- No rate-limit header logging in the Meta adapter's response handling.

**Phase to address:**
Phase 2 (Stage-by-stage API integration) — implement caching layer before connecting multiple tenant accounts.

---

### Pitfall 9: Shopify Webhook Missed Events Without Reconciliation Jobs

**What goes wrong:**
Shopify webhooks have a 5-second response timeout and retry up to 8 times over 4 hours. If the endpoint is unavailable for the entire retry window (e.g., during a deployment), the webhook subscription is automatically deleted after 19 consecutive failures. Stage 3 (Oportunidad) abandoned-cart data and Stage 6 (Expansión) subscription renewal events will have permanent gaps with no indication of missing data.

**Why it happens:**
Webhook-only architectures assume delivery guarantees that don't exist. One deployment, one infrastructure hiccup, or one slow database write causes missed events that are never retried again once the subscription is deleted.

**How to avoid:**
- Treat webhooks as a speed optimization, not as the source of truth. Implement nightly reconciliation jobs that poll Shopify REST API for orders, checkouts, and subscription events from the last 48 hours and upsert into the CRM.
- Implement idempotency keys for every webhook handler: store processed `webhook_id` in Redis with 72-hour TTL, skip if already seen.
- Webhook endpoint must respond HTTP 200 within 500ms and process asynchronously (enqueue to Redis/Celery, return immediately).
- Verify `X-Shopify-Hmac-Sha256` signature on every incoming webhook before processing.
- Monitor webhook subscription health: periodically call Shopify API to verify subscriptions still exist.

**Warning signs:**
- Shopify admin shows webhooks in "Failed" or "Inactive" state.
- Stage 3 and Stage 6 metrics have clean round numbers (a sign of mock data) while other stages show varied real values.
- Webhook processor takes > 1 second per event (sign of synchronous processing).

**Phase to address:**
Phase 2 (Stage 3 and Stage 6 implementations) — reconciliation jobs must be designed alongside webhook handlers, never as an afterthought.

---

### Pitfall 10: Mailerlite Webhook Processing Blocking the Request Thread

**What goes wrong:**
Mailerlite webhooks (subscriber_opened, subscriber_clicked, etc.) batch multiple events in a single request. If the handler performs database writes synchronously within the 3-second response window and a batch contains 100+ events, the handler times out. Mailerlite treats timeouts as failures and retries — triggering duplicate processing. Stage 2 (Nutrición) email engagement metrics become double-counted.

**Why it happens:**
Webhook handlers are written as standard synchronous FastAPI route handlers without offloading. A single-subscriber campaign fires one event; a broadcast email fires thousands simultaneously. The load difference between dev testing and production is 100-1000x.

**How to avoid:**
- Webhook handler must: (1) verify `X-MailerLite-Signature`, (2) enqueue event payload to Redis queue, (3) return HTTP 200 within 500ms.
- Celery worker processes the queue asynchronously with idempotency checks (store event ID in Redis, TTL 48h).
- Never return 4xx or 5xx from business logic errors — Mailerlite will retry indefinitely. Return 200 and log the error internally.

**Warning signs:**
- Mailerlite dashboard shows webhook delivery failures or retries.
- Email open-rate metrics for Stage 2 are exactly 2x or 3x the expected value.
- FastAPI logs show webhook handlers taking > 2 seconds.

**Phase to address:**
Phase 2 (Stage 2 Nutrición implementation).

---

### Pitfall 11: Google Ads API Requires Per-Account Queries — No MCC Aggregation

**What goes wrong:**
Developers assume a single Google Ads API call against the Manager Account (MCC) can return aggregated metrics for all sub-accounts. This is false. The Google Ads API does not support cross-account metric aggregation — every metric request must be issued against a specific customer (client account) ID. For a tenant with 3 Google Ads accounts, this means 3 separate API calls per metric set, and the aggregation must happen in Nicolify's backend.

**Why it happens:**
The Google Ads UI shows MCC-level rolled-up metrics, creating the impression the API works the same way. It doesn't.

**How to avoid:**
- When a tenant connects Google Ads, store all linked customer IDs (not just the MCC ID) in `ChannelConnectionModel.config`.
- The analytics service must iterate over all stored customer IDs and issue parallel requests.
- Implement a fallback: if a tenant has only one customer ID, skip the iteration overhead.
- Use `asyncio.gather` with concurrency limits when issuing parallel per-account requests.

**Warning signs:**
- Google Ads metrics always show zero or only one account's data even when multiple accounts are linked.
- A single `customer_id` stored per Google tenant in `ChannelConnectionModel`.
- Errors like `CUSTOMER_NOT_FOUND` when querying an MCC ID directly for metrics.

**Phase to address:**
Phase 1 (Data Infrastructure Foundation) — the multi-account query pattern must be in the Google Ads adapter design before Stage 0 implementation.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode `API_VERSION` constant | Simple, readable | Breaks silently when Meta deprecates version | Never — always read from settings |
| Use mock data flag (`ENABLE_MOCKS`) for Shopify | Unblocks development | Masks broken integration; technical debt accumulates | MVP only, must be removed by launch |
| Synchronous Meta SDK calls (`asyncio.to_thread`) | Works, familiar | Blocks thread pool under load; no backpressure | Only until async SDK alternative is available |
| Skip token expiry tracking for Meta | Saves schema design time | 60-day silent data gaps for all tenants | Never |
| Sum ad-platform conversions for Stage 4 | Quick implementation | Inflated 150-200% conversion numbers | Never — always use CRM as source of truth |
| One `MetricsService` that calls all APIs inline | Simple code structure | Unresponsive dashboard when one provider is slow | Acceptable in Phase 1, must use adapter + circuit-breaker by Phase 2 |
| Single `google-analytics` connection for both Admin and Data APIs | Fewer connections | Admin API and Data API are separate clients — will fail | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Meta Marketing API | Use `FacebookAdsApi.init()` global singleton in async routes | Instantiate `FacebookAdsApi` with `FacebookSession` per request; never use global init |
| Meta Insights | Synchronous call for > 7-day date range | POST with `async=true`, poll `async_status` until `Job Completed` |
| Meta Insights | Request all available fields to "be thorough" | Request only the exact fields needed; extra fields increase rate limit cost |
| GA4 Data API | Use `analyticsadmin` service for reports | Use `analyticsdata` (`BetaAnalyticsDataClient`) for `runReport()` |
| GA4 | Show "today" data as final | Mark data < 48h old as "preliminary" — GA4 processes with up to 48h delay |
| Google Ads | Query at MCC level for aggregated metrics | Query each customer ID separately, aggregate in backend |
| Google OAuth | Assume refresh tokens last forever | Detect `invalid_grant`, mark connection as `reauth_required` |
| TikTok Ads | Use Sandbox URL (`sandbox-ads.tiktok.com`) in production | Switch to `business-api.tiktok.com` for live accounts |
| TikTok Ads | Include TikTok's reported conversions in total conversion count | Use TikTok data only for reach, clicks, CPM — CRM handles conversions |
| Shopify Webhooks | Process webhook synchronously within HTTP handler | Enqueue to Redis/Celery, return HTTP 200 within 500ms |
| Shopify Webhooks | Rely solely on webhooks for event data | Implement nightly reconciliation job via REST API |
| Mailerlite Webhooks | Return 4xx for duplicate/unknown events | Always return 200 to stop retries; handle errors internally |
| Mailerlite | Parse each webhook event with full DB round-trip | Batch-process from queue; use Redis for dedup |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Dashboard waits for all API providers before rendering | 10-15s load time; one slow provider blocks all stages | Fetch providers in parallel; render stages independently as each resolves | Single tenant with all 6 providers connected |
| No backend cache for API responses | Every page visit triggers live API calls; rate limits hit immediately | Redis cache per provider per tenant (5min TTL for live, 1h for historical) | 2+ tenants using dashboard simultaneously |
| Meta async job polling in request thread | Request hangs for 30-60s; load balancer timeout | Return job ID immediately, poll via background task, push result to frontend via polling or WebSocket | Any Meta insights query > 7 days |
| Timezone conversion per-row in Python | Slow aggregation for large datasets | Normalize to UTC on storage; apply timezone display offset only at DTO layer | Tenant with > 100k CRM events |
| Shopify reconciliation job re-fetches all history | Job takes hours; overlaps with itself | Watermark-based incremental fetch using `updated_at` cursor | Any Shopify store with > 1k orders |
| Sequential per-tenant background sync | Sync job takes N*minutes for N tenants | Use Celery group/chord pattern for parallel tenant sync | 5+ active tenants |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Store OAuth tokens in plaintext `config` JSONB column | Full account access exposed if DB is compromised | Use `EncryptedJSON` column type (already in `credentials` column — do not use `config` for tokens) |
| Log full access tokens in debug output | Token appears in log aggregators (Datadog, Sentry) | Mask tokens in logs: log only first 8 chars + `...` |
| Return another tenant's connection tokens in API response | Cross-tenant token leak | All connection queries must filter by `tenant_id`; add test asserting no cross-tenant leakage |
| Store Meta page_access_token in frontend state | Token accessible via browser JS, can be exfiltrated | page_access_tokens must stay server-side only; never include in API responses to frontend |
| Single encryption key for all tenant credentials | One key compromise exposes all tenants | Per-tenant encryption keys (or KMS-backed rotation) — current Fernet key is app-global, flag for future rotation |
| Webhook endpoints without signature verification | Fake webhook injection to manipulate metrics | Verify `X-Shopify-Hmac-Sha256` (Shopify), `X-MailerLite-Signature` (Mailerlite), Meta's `X-Hub-Signature-256` on every request |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Show zero when provider API is down or token expired | Owner thinks their business has no activity; panic | Show last-known value with staleness indicator: "Meta data from 3h ago — reconnect required" |
| Show "platform-reported" conversions without disclaimer | Owner double-counts revenue; makes bad budget decisions | Add "Source: CRM (verified)" vs "Source: Meta (self-reported)" labels per metric |
| Same metric name across providers means the same thing | Incorrect business decisions (Meta "reach" vs Google "impressions" are different) | Use Nicolify-normalized metric names with tooltip explaining source formula |
| No loading state per stage card | Dashboard appears broken while APIs load | Skeleton loaders per stage card; stages render independently as data arrives |
| GA4 "preliminary" data looks the same as finalized data | Owner makes decisions on incomplete data | Visual indicator on metrics < 48h old: "Datos preliminares — se actualizan en 24-48h" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Meta Integration:** Shows data in dev — verify with a real token that `API_VERSION` is v22.0+, not v19.0; check that async jobs are used for > 7-day ranges.
- [ ] **Google Analytics:** Property list populates — verify `analyticsdata` (Data API) is separate from `analyticsadmin`; check `runReport()` actually returns session data, not just property metadata.
- [ ] **Token Expiry:** Connections show "Conectado" status — verify that the `expires_in` field is stored and a background check job exists; connection status should degrade to "Reauth needed" after 53 days.
- [ ] **Conversion Metrics:** Stage 4 shows a number — verify the source is `lifecycle_stage = CUSTOMER` transitions in CRM, not a sum of ad-platform reported conversions.
- [ ] **Shopify Events:** Stage 3 shows abandoned cart data — verify there is a nightly reconciliation job, not only a webhook handler; confirm webhook subscription still exists in Shopify admin.
- [ ] **Multi-Tenant Isolation:** Works for tenant A — verify that tenant B's dashboard does not show tenant A's data by running both in parallel and checking API response content.
- [ ] **Timezone Normalization:** Metrics look correct in UTC+0 — verify the same metrics look correct for a tenant whose Meta account is in UTC-5 and GA4 is in UTC+1.
- [ ] **Rate Limits:** Works in dev — verify Redis cache and per-tenant throttling are in place before enabling concurrent multi-tenant access.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Meta API version broken (v19.0) | LOW | Update `API_VERSION` constant, update facebook_business SDK, redeploy |
| Meta tokens expired for all tenants | HIGH | Add reauth UI banner, contact affected tenants to reconnect, implement proactive refresh job |
| Attribution inflation discovered post-launch | MEDIUM | Audit Stage 4 query, switch to CRM-sourced conversions, re-backfill historical display data |
| Cross-tenant token contamination incident | CRITICAL | Rotate all OAuth tokens for all tenants, audit API call logs for cross-tenant calls, notify affected users, patch SDK instantiation pattern |
| Shopify webhook subscription deleted | MEDIUM | Re-register webhook subscription, run full historical backfill reconciliation job for last 30 days |
| Google OAuth tokens expired en masse | HIGH | Surface reauth prompts for all affected tenants, add token health monitoring to prevent recurrence |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Meta API v19.0 hardcoded | Phase 1 — Infrastructure | CI test that asserts `API_VERSION >= v22.0`; integration test against live Meta sandbox |
| Meta token expiry unhandled | Phase 1 — Infrastructure | Unit test for token expiry detection; integration test asserting `reauth_required` flag on 401 |
| Attribution double-counting | Phase 1 + Phase 2 (Stage 4) | Audit query: Stage 4 conversion count source must be CRM, not ad platform sum |
| GA4 Data API not implemented | Phase 1 — Infrastructure | `google-analytics-data` in requirements; `runReport()` integration test |
| Google OAuth silent invalidation | Phase 1 — Infrastructure | Token health monitor job exists; `invalid_grant` handling tested |
| Meta SDK global singleton leak | Phase 1 — Infrastructure | Concurrency test: two parallel requests with different tenant tokens must return distinct data |
| Timezone mismatch | Phase 1 — Infrastructure | Adapter interface requires `account_timezone` parameter; UTC normalization unit tested |
| Meta rate limiting without caching | Phase 2 — API Integration | Redis cache exists; rate-limit header logging present; load test with 3+ concurrent tenants |
| Shopify webhook missed events | Phase 2 (Stage 3, Stage 6) | Reconciliation job exists; idempotency test simulating duplicate webhook delivery |
| Mailerlite webhook blocking | Phase 2 (Stage 2) | Webhook handler response time < 500ms; duplicate event idempotency test |
| Google Ads no MCC aggregation | Phase 1 — Infrastructure | Multi-account connection stored; parallel per-account query test |

---

## Sources

- [Meta Marketing API Rate Limiting](https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/) — official, HIGH confidence
- [Meta Marketing API Insights Best Practices](https://developers.facebook.com/docs/marketing-api/insights/best-practices/) — official, HIGH confidence
- [Meta Graph API Changelog 2025](https://developers.facebook.com/docs/marketing-api/out-of-cycle-changes/occ-2025/) — official, HIGH confidence
- [Google Ads API Credential Management](https://developers.google.com/google-ads/api/docs/oauth/credential-management) — official, HIGH confidence
- [Google Ads API Common Errors](https://developers.google.com/google-ads/api/docs/get-started/common-errors) — official, HIGH confidence
- [GA4 Data Freshness](https://support.google.com/analytics/answer/11198161) — official, HIGH confidence
- [GA4 APIs Limitations 2025](https://www.owox.com/blog/articles/google-analytics-api-comparison) — MEDIUM confidence
- [TikTok Attribution Overview](https://ads.tiktok.com/help/article/attribution-overview) — official, HIGH confidence
- [TikTok Conversion Discrepancies](https://ads.tiktok.com/help/article/conversion-discrepancies) — official, HIGH confidence
- [TikTok API Rate Limits](https://developers.tiktok.com/doc/tiktok-api-v2-rate-limit) — official, HIGH confidence
- [Shopify Webhook Best Practices](https://shopify.dev/docs/apps/build/webhooks/best-practices) — official, HIGH confidence
- [Mailerlite API Rate Limits](https://developers.mailerlite.com/docs/) — official, HIGH confidence
- [OWASP Multi-Tenant Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html) — official, HIGH confidence
- [Attribution Window Best Practices 2026](https://www.cometly.com/post/attribution-window-best-practices) — MEDIUM confidence
- [How to Actually Calculate CAC (andrewchen)](https://andrewchen.com/how-to-actually-calculate-cac/) — MEDIUM confidence
- Codebase inspection: `MetaAdapter` (`API_VERSION = "v19.0"`), `GoogleAnalyticsAdapter` (`analyticsadmin` only), `ChannelConnectionModel` (`EncryptedJSON` for credentials), `metrics_service.py` (hardcoded 40% retention heuristic) — HIGH confidence

---
*Pitfalls research for: Nicolify Growth Studio — multi-provider marketing metrics integration*
*Researched: 2026-03-15*
