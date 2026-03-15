# Project Research Summary

**Project:** Nicolify Growth Studio — 8-Stage Funnel Metrics Dashboard
**Domain:** Multi-provider marketing analytics aggregation (Meta, Google Ads, GA4, TikTok, YouTube, Mailerlite, Shopify + internal CRM)
**Researched:** 2026-03-15
**Confidence:** HIGH

## Executive Summary

The Growth Studio metrics dashboard is a multi-provider analytics aggregation product built on top of an existing FastAPI + Next.js platform. The project's core challenge is not building a dashboard — the frontend shell, Stage 0 endpoint, and the ChannelGroup/ChannelRow component pattern already exist — it is wiring real data from 7 external APIs into a normalized pipeline that feeds 7 currently placeholder panels. Research confirms this is solvable with a provider adapter pattern backed by Redis TTL caching, but the order of operations matters: three infrastructure pieces (Meta API version fix, GA4 Data API client, CRM `move_stage()` automation) are hard blockers that will silently poison all downstream work if not addressed first.

The recommended approach is a two-phase execution: Phase 1 establishes data infrastructure (fixing broken Meta API version, adding GA4 Data client, building the provider adapter base, implementing CRM lifecycle transitions, and setting up Redis caching with per-tenant rate-limit shielding). Phase 2 implements each funnel stage sequentially, starting from Stage 1 (Captura) through Stage 7 (Evangelización), with the CRM as the authoritative source for conversion counts and ad platforms used only for top-funnel impression/click metrics. The Bowtie model covering post-sale stages (5-7) is the product's primary competitive differentiator and should not be deferred.

The dominant risks are operational rather than architectural. The existing `MetaAdapter` uses a deprecated API version (v19.0), has a global SDK singleton vulnerable to cross-tenant token contamination, and has no token-expiry handling — any of these will cause either silent data gaps or security incidents. Attribution double-counting across platforms is a near-certainty if ad-platform-reported conversions are summed for Stage 4; the fix is treating the internal CRM as the sole source of truth for conversion counts. Security and correctness must be established in Phase 1 before any provider data flows.

---

## Key Findings

### Recommended Stack

The project reuses almost all existing infrastructure. The new additions are minimal: `google-analytics-data==0.20.0` (GA4 Data API — a separate package from the Admin API already in use), `google-ads==29.2.0` (Google Ads GAQL client), `APScheduler==3.11.2` (recurring background polling — APScheduler v4 is alpha and must not be used), and the official `mailerlite` SDK (replaces current direct HTTP). TikTok has no reliable Python SDK; use `httpx.AsyncClient` with direct REST calls to `business-api.tiktok.com`. Shopify uses test data via feature flag until the connection is repaired.

On the frontend, Recharts is optional: use it only if stage panels require sparkline trend charts. For simple number + percentage change displays, a Tailwind `<div>` is faster. The project already has `@visx` for the Sankey diagram; do not use `@visx` for column panel charts — the D3 wiring overhead is ~3x that of Recharts for the same output.

**Core new technologies:**
- `google-analytics-data==0.20.0`: GA4 `runReport()` for organic session/traffic data — the only client that accesses the Data API (not Admin API)
- `google-ads==29.2.0`: Google Ads GAQL queries for campaign spend/clicks — requires per-customer-ID queries, no MCC aggregation
- `APScheduler==3.11.2` with `AsyncIOScheduler`: recurring metrics refresh inside FastAPI's event loop — no separate Celery infrastructure needed at current scale
- `mailerlite` official SDK: typed responses + rate-limit handling for email engagement metrics
- `httpx.AsyncClient` (already installed): TikTok Ads API and Shopify REST (async, avoids blocking the event loop)
- `recharts@^2.15.0` (conditional): React-idiomatic bar charts/sparklines if trend lines are needed in panels

**Critical version notes:**
- Meta API must be `v22.0` minimum (v19.0 is deprecated and will return HTTP 400)
- APScheduler must be `3.x`, not `4.x` alpha
- `recharts` requires `"use client"` directive — not SSR-safe by default

### Expected Features

Research against HubSpot, Triple Whale, Northbeam, and Databox confirms the competitive positioning. Nicolify's 8-stage Bowtie model (including post-sale Adopción, Expansión, Evangelización) is the strongest differentiator — no competitor tool shows both acquisition and retention in a single unified dashboard for the SMB creator segment.

**Must have (table stakes):**
- All 8 stage panels with real data replacing PlaceholderDetail components — 7 of 8 currently show placeholders
- Per-stage absolute count + conversion rate to next stage — minimum viable metric per card
- Channel-level breakdown within each stage (ChannelGroup + ChannelRow pattern, already built for Stage 0)
- Connection status badge in every panel — users must know if data is live or missing
- Cost tracking per stage/channel (NEUTRAL / EXPENSE / REVENUE type system)
- Stage 4 (Ventas) revenue with new vs. recurring split (CONVERSION vs. EXPANSION events)
- Mock/fallback for all Shopify-dependent metrics (connection known broken)
- CRM `move_stage()` implemented with automated rules — without this, stages 1-7 return zero counts

**Should have (competitive differentiators):**
- Stage 5 Adopción: active vs. inactive customer cohort (retention signal)
- Stage 6 Expansión: MRR retained vs. lost (churn visibility critical for creator businesses)
- Stage 7 Evangelización: referral count + K-Factor estimate (rare in SMB analytics tools)
- Offer Ladder breakdown in Stage 4 (unique — ties sales metrics to internal offer taxonomy)
- AI SDR contribution visibility in Stage 1 (unique to AaaS platforms)
- Attribution source labeling: "Source: CRM (verified)" vs "Source: Meta (self-reported)"

**Defer to v1.x (post-validation):**
- GA4 real organic session data for Stage 0 (mock works; real data is an improvement)
- LTV write-back to `customer_profiles` on EXPANSION events
- Date range selector (add after all 8 stages return validated data)

**Defer to v2+:**
- Action Triggers (automation launch from funnel node) — separate system, not this milestone
- Custom KPI goal setting, cross-tenant benchmarking, multi-attribution model selection
- Export/download (data schemas not yet stable)

### Architecture Approach

The architecture is a layered provider adapter system within the existing DDD `analytics` module. A `ProviderAdapterBase` ABC defines a uniform `fetch_metrics(tenant_id, credentials, config, date_from, date_to) -> RawMetrics` interface. Each external provider and the internal CRM implement this interface. `MetricsService` orchestrates all adapters for a given stage using `asyncio.gather`, merges partial results gracefully (a disconnected provider returns `None`, not an error), caches the merged result in Redis per tenant/stage/date-range, and maps to the stage-specific response DTO. One FastAPI endpoint per stage — never a single `/metrics/all` endpoint. The frontend loads each panel independently via TanStack Query, isolating slow providers from fast ones.

Cross-module reads follow a port pattern: `ConnectionPort` in `analytics/infrastructure/ports/` wraps `ChannelConnectionRepository` read-only — analytics never imports application services from `connections`. `CrmInternalAdapter` reads CRM repositories directly (no HTTP boundary in the monolith) and is the authoritative source for lifecycle stage counts and conversion metrics.

**Major components:**
1. `ProviderAdapterBase` ABC + `RawMetrics` dataclass — uniform interface; new providers plug in without touching service or API layers
2. `ConnectionPort` — read-only cross-module boundary; decrypts and returns credentials from `connections` module
3. `MetricsCacheRepository` — Redis TTL cache keyed `{tenant_id}:{stage}:{date_range}`; shields provider rate limits
4. `CrmLifecycleService` (`move_stage()`) — automated lifecycle transitions; must be implemented before any stage counts are meaningful
5. Per-provider adapters (`MetaAdsAdapter`, `GA4DataAdapter`, `GoogleAdsAdapter`, `TikTokAdsAdapter`, `YouTubeAnalyticsAdapter`, `MailerliteAdapter`, `ShopifyAdapter`, `CrmInternalAdapter`)
6. `MetricsService` — orchestrates adapters per stage, merges results, returns stage DTOs
7. 7 new frontend detail panel components following the `AttractionDetail` pattern

**Build order is constrained:** ProviderAdapterBase → ConnectionPort → MetricsCacheRepository → CrmLifecycleService → CrmInternalAdapter → external adapters → MetricsService stage methods → API endpoints → frontend panels.

### Critical Pitfalls

1. **Meta API v19.0 hardcoded — already deprecated.** The existing `MetaAdapter` uses `API_VERSION = "v19.0"`. Meta deprecated v19 on September 9, 2025 (minimum is now v22.0). Every Meta API call in production is currently broken. Fix immediately and move the version to `settings.META_API_VERSION`.

2. **Meta SDK global singleton causes cross-tenant token contamination.** `FacebookAdsApi.init()` sets a process-level global. In async FastAPI with concurrent requests, Tenant A's token will be used for Tenant B's API calls. Never call `FacebookAdsApi.init()`. Instantiate `FacebookAdsApi(FacebookSession(app_id, app_secret, token))` per request, per adapter call.

3. **GA4 Data API not implemented — only Admin API exists.** The current `GoogleAnalyticsAdapter` builds an `analyticsadmin` service (property management only). It cannot call `runReport()`. Zero organic traffic data will ever appear without adding `google-analytics-data` package and a new `GA4DataAdapter` class. This is a prerequisite for Stage 0 real data.

4. **Attribution double-counting inflates Stage 4 conversion totals by 150-200%.** Meta, Google Ads, and TikTok each claim the same conversion. Summing platform-reported conversions produces meaningless numbers. The authoritative conversion count must come from `lifecycle_stage = CUSTOMER` transitions in the internal CRM. Never sum ad-platform conversion fields for any stage metric.

5. **Meta long-lived token expiry (60 days) not handled — silent data gaps.** No token refresh job exists. After 60 days, every tenant's Meta connection silently fails with `error_subcode 463`. Store `expires_in` + creation timestamp in credentials; implement a daily background check that flags connections approaching expiry as `reauth_required`.

6. **`move_stage()` is a `pass` placeholder — all stages 1-7 return zero counts.** All downstream stage counts derive from `lifecycle_stage` transitions. Building 7 detail panels before implementing `CrmLifecycleService.move_stage()` with automated rules produces panels that always show zero regardless of real CRM data.

---

## Implications for Roadmap

### Phase 1: Data Infrastructure Foundation

**Rationale:** Six of the eleven critical pitfalls must be resolved before any real API data can flow. These are not enhancements — they are correctness and security prerequisites. Building provider adapters on top of a broken Meta API version, a missing GA4 Data client, and a `move_stage()` stub will produce panels that are technically "working" but permanently wrong.

**Delivers:**
- Meta API version updated to v22.0+; moved to settings
- Meta SDK instantiation pattern fixed (per-request `FacebookAdsApi`, not global singleton)
- `google-analytics-data` package added; `GA4DataAdapter` class created
- `google-ads` package added; Google Ads adapter scaffolded with multi-account query pattern
- `ProviderAdapterBase` ABC + `RawMetrics` dataclass defined
- `ConnectionPort` implemented (read-only connection credential lookup)
- `MetricsCacheRepository` implemented (Redis TTL, per-tenant/stage/date-range key pattern)
- `CrmLifecycleService.move_stage()` implemented with automated rules (scoring thresholds, sale events)
- Meta token expiry tracking added to `ChannelConnectionModel`; daily expiry check job created
- Timezone normalization layer established in base adapter interface
- All webhook handlers confirmed to return 200 within 500ms and enqueue asynchronously

**Addresses pitfalls:** Meta v19.0 (Pitfall 1), Meta token expiry (Pitfall 2), GA4 Data API missing (Pitfall 4), Google OAuth invalidation (Pitfall 5), Meta SDK singleton contamination (Pitfall 6), timezone mismatch (Pitfall 7), Google Ads MCC aggregation misconception (Pitfall 11)

**Research flag:** Standard patterns well-documented — no additional research phase needed. Codebase inspection confirms exact gaps.

---

### Phase 2: Pre-Sale Stage Implementations (Stages 1-4)

**Rationale:** Stages 1-4 cover the acquisition funnel (Captura → Nutrición → Oportunidad → Ventas). They depend on Phase 1 infrastructure and deliver the highest visible business value. Stage 4 (Ventas/revenue) is always highest priority for business owners. Stages 1-3 build the causal chain that explains how revenue was generated. CRM-as-source-of-truth for conversion counts (Pitfall 3) must be enforced here.

**Delivers:**
- `CrmInternalAdapter` fully implemented (reads `customer_profiles`, `journey_events`, `sales` tables)
- `MetaAdsAdapter` fully implemented (async insights jobs for >7-day ranges; rate-limit header logging)
- `MailerliteAdapter` with batch webhook processing and idempotency
- Stage 1 (Captura): AI SDR leads vs. web form leads; source channel breakdown
- Stage 2 (Nutrición): email engagement metrics (Mailerlite open/click rates); per-channel cost tracking
- Stage 3 (Oportunidad): abandoned-cart data with Shopify reconciliation job; opportunity count from CRM
- Stage 4 (Ventas): revenue with CONVERSION vs. EXPANSION split; "Source: CRM (verified)" label; Offer Ladder breakdown; never sum ad-platform conversions
- All 4 panels follow ChannelGroup + ChannelRow + ConnectionBadge pattern from AttractionDetail
- `MetricsService` stage methods for stages 1-4
- Backend endpoints: `/metrics/capture`, `/metrics/nurturing`, `/metrics/opportunity`, `/metrics/sales`

**Addresses pitfalls:** Attribution double-counting (Pitfall 3), Meta rate limiting (Pitfall 8), Shopify webhook missed events (Pitfall 9), Mailerlite webhook blocking (Pitfall 10)

**Research flag:** Mailerlite webhook batching and Shopify reconciliation patterns are niche — consider a focused research spike on event deduplication patterns if the team hasn't built this before.

---

### Phase 3: Post-Sale Stage Implementations (Stages 5-7)

**Rationale:** Stages 5-7 (Adopción, Expansión, Evangelización) are the product's primary competitive differentiator. No competitor tool shows post-sale retention metrics alongside acquisition in a single dashboard. Stage 6 must be stable before Stage 7 (K-Factor requires knowing retained customers). Building these after Stage 4 is validated ensures the conversion-to-retention handoff is based on clean CRM data.

**Delivers:**
- Stage 5 (Adopción): active vs. inactive customer cohort; onboarding engagement indicator
- Stage 6 (Expansión): MRR retained vs. lost; subscription renewal data; LTV field on `customer_profiles` updated on EXPANSION events
- Stage 7 (Evangelización): referral count + K-Factor estimate (Shopify referral coupons + Mailerlite NPS); viral loop visibility
- `TikTokAdsAdapter` and `YouTubeAnalyticsAdapter` wired in (post-sale attribution for organic growth channels)
- GA4 `runReport()` fully integrated into Stage 0 Atracción (organic sessions, traffic sources, direct/AI-search breakdown)
- Stage 0 updated to replace all `value=0` placeholders with real GA4 + Google Ads data
- `ShopifyAdapter` activated behind feature flag when Shopify connection is repaired

**Research flag:** K-Factor calculation methodology and referral code tracking via Shopify coupons may need a targeted research spike — the exact implementation approach depends on whether referral codes are already being captured in the CRM.

---

### Phase 4: Validation, Polish, and v1.x Additions

**Rationale:** Once all 8 stages return real data, a validation pass is required before claiming the dashboard is "done." Silent mock data, stale cache, and misattributed metrics are only discoverable by comparing panel values against ground-truth sources. This phase also delivers the post-validation v1.x additions.

**Delivers:**
- Side-by-side validation of each stage's metrics against source platform dashboards for at least one real tenant
- Date range selector added (deferred anti-feature — safe to build now that all 8 stages return validated data)
- Attribution window normalization UI hint ("Data synced to UTC. Meta reports in America/New_York.")
- GA4 preliminary data indicator for metrics < 48h old ("Datos preliminares — se actualizan en 24-48h")
- "Looks Done But Isn't" checklist items verified: Meta v22.0 in production, `runReport()` returns real sessions, Stage 4 source is CRM not ad platform, Shopify reconciliation job active, multi-tenant isolation verified by parallel request test, rate-limit headers logged

**Research flag:** Standard validation patterns — no research phase needed.

---

### Phase Ordering Rationale

- Phase 1 before everything: broken Meta API version, missing GA4 Data client, and `move_stage()` stub are not technical debt items to tolerate — they make all downstream phases produce incorrect output.
- Phase 2 before Phase 3: post-sale stages (5-7) depend on lifecycle transitions from CUSTOMER state (set in Stage 4). Stage 6 MRR data requires Stage 4 EXPANSION detection to be stable. K-Factor in Stage 7 requires Stage 6 retention counts.
- Stage 4 (Ventas) is the highest-priority panel in Phase 2: revenue visibility is what business owners check first; delivering it validates the CRM-as-source-of-truth pattern before building the remaining stages.
- Date range selector is explicitly deferred until Phase 4: adding it before all 8 stages have validated data doubles query complexity on an unvalidated foundation.

---

### Research Flags

**Needs research spike during planning:**
- **Phase 2 — Mailerlite webhook batch deduplication:** The team may not have built high-volume webhook idempotency before. A focused spike on the Redis dedup pattern and batch event processing is warranted.
- **Phase 3 — K-Factor and referral code tracking in Stage 7:** Whether Shopify coupon codes are already being stored in the CRM affects the implementation path significantly. Verify CRM schema before Phase 3 planning.

**Standard patterns (skip research-phase):**
- **Phase 1 — Provider adapter ABC pattern:** Well-documented in ARCHITECTURE.md with code examples. Implementation is straightforward given the existing codebase.
- **Phase 1 — Redis TTL caching:** Existing Redis infrastructure in Docker Compose; caching pattern is standard.
- **Phase 2 — Detail panel frontend components:** AttractionDetail.tsx is the exact template. The 7 new panels are mechanical implementations of the same pattern.
- **Phase 4 — Validation pass:** Checklist-driven process, no novel patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified via PyPI official pages. Existing codebase confirms what is already installed. The only uncertainty is whether `recharts` is needed (depends on final UX decision on trend charts). |
| Features | HIGH | Competitor analysis (HubSpot, Triple Whale, Northbeam, Databox) is cross-referenced against the existing codebase. Table stakes features are well-established. Differentiators (Bowtie post-sale, K-Factor, Offer Ladder) are verified as absent from competitors. |
| Architecture | HIGH | Architecture research is primarily derived from codebase inspection of existing `analytics`, `connections`, `crm` modules — not assumptions. Build order dependencies are concrete, not speculative. |
| Pitfalls | HIGH | All critical pitfalls are verified against official API documentation AND codebase inspection. Meta v19.0 hardcode, GA4 Admin-vs-Data API confusion, and SDK singleton pattern are confirmed findings, not hypothetical risks. |

**Overall confidence:** HIGH

### Gaps to Address

- **Shopify connection repair timeline:** The Shopify adapter is explicitly gated behind `ENABLE_MOCKS`. Phase 3 (Stage 6 Expansión) partially depends on Shopify subscription renewal data. The reconciliation job can be built, but real data depends on when the Shopify connection is fixed. Flag for validation during Phase 3 planning.
- **CRM scoring rules specifics:** `CrmLifecycleService.move_stage()` requires defined scoring thresholds (e.g., "lead score > 70 = Oportunidad"). These business rules need input from the product side before Phase 1 implementation. Research has confirmed the pattern but not the specific threshold values.
- **TikTok short-term token refresh (24h expiry):** TikTok access tokens expire in 24 hours. A token refresh job is needed for TikTok that differs from the Google and Meta patterns. The connections module's existing TikTok OAuth flow must be verified to handle refresh before the TikTok adapter can sustain overnight data pulls.
- **Stage 7 referral code presence in CRM:** K-Factor requires referral codes from Shopify coupons to be tracked against `customer_profiles`. Whether this linkage exists in the current CRM schema needs verification before Phase 3 planning.

---

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/src/modules/analytics/`, `connections/`, `crm/` modules — confirmed existing state, gaps, and broken patterns
- [Meta Graph API Changelog 2025](https://developers.facebook.com/docs/marketing-api/out-of-cycle-changes/occ-2025/) — v19.0 deprecation date confirmed
- [Meta Marketing API Rate Limiting](https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/) — async job pattern, rate-limit headers
- [GA4 Data Freshness](https://support.google.com/analytics/answer/11198161) — 24-48h preliminary data window
- [Google Ads API Credential Management](https://developers.google.com/google-ads/api/docs/oauth/credential-management) — per-account query requirement confirmed
- [Shopify Webhook Best Practices](https://shopify.dev/docs/apps/build/webhooks/best-practices) — reconciliation job pattern
- [PyPI: google-analytics-data](https://pypi.org/project/google-analytics-data/) — v0.20.0 confirmed
- [PyPI: google-ads](https://pypi.org/project/google-ads/) — v29.2.0 confirmed
- [PyPI: APScheduler](https://pypi.org/project/APScheduler/) — v3.11.2 stable, v4 alpha confirmed
- [OWASP Multi-Tenant Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html) — SDK singleton contamination pattern
- [Bowtie Funnel Model — RevPartners](https://blog.revpartners.io/en/revops-articles/bowtie-funnel) — post-sale stage model

### Secondary (MEDIUM confidence)
- [Triple Whale vs Northbeam 2026 Comparison](https://www.headwestguide.com/triple-whale-vs-northbeam) — competitor feature matrix
- [Attribution Window Best Practices 2026 — Cometly](https://www.cometly.com/post/attribution-window-best-practices) — double-counting risk
- [TikTok Attribution Overview](https://ads.tiktok.com/help/article/attribution-overview) — multi-session vs UTM tracking differences
- [LogRocket: Best React chart libraries 2025](https://blog.logrocket.com/best-react-chart-libraries-2025/) — Recharts vs visx positioning
- [GA4 APIs Limitations 2025 — OWOX](https://www.owox.com/blog/articles/google-analytics-api-comparison) — sampling metadata behavior

---

*Research completed: 2026-03-15*
*Ready for roadmap: yes*
