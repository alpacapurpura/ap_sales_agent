# Requirements: Nicolify Growth Studio — 8-Stage Metrics Dashboard

**Defined:** 2026-03-15
**Core Value:** Business owner sees their entire customer lifecycle at a glance and understands where the funnel is healthy, leaking, or needs action.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Infrastructure — Data Foundation

- [x] **INFRA-01**: Provider adapter base class (ABC) in `analytics/infrastructure/providers/` with normalized metric output, so all providers conform to one interface
- [x] **INFRA-02**: `ConnectionPort` service that retrieves decrypted OAuth credentials from `connections` module without violating DDD boundaries
- [x] **INFRA-03**: Redis-based metrics cache in `analytics` with per-provider TTL (paid ads = 1h, CRM = 5min) to respect API rate limits
- [x] **INFRA-04**: Cost type system (NEUTRAL, EXPENSE, REVENUE) applied as a field on every channel metric DTO across all 8 stages
- [x] **INFRA-05**: Mock/fallback mechanism consistent across all 8 stages — disconnected providers show "Configurar" badge, not broken UI

### Infrastructure — Critical Bug Fixes

- [x] **BUGFIX-01**: Update Meta API version from deprecated `v19.0` to `v22.0+` (Meta stopped accepting v19.0 requests Sept 2025)
- [x] **BUGFIX-02**: Fix Meta SDK singleton pattern (`FacebookAdsApi.init()`) — must be per-request/per-tenant, not process-global, to prevent multi-tenant data leaks
- [x] **BUGFIX-03**: Implement GA4 Data API client (`google-analytics-data` package, `BetaAnalyticsDataClient.runReport()`) — current code only has Admin API for property discovery

### CRM Lifecycle Automation

- [x] **CRM-01**: Implement `move_stage()` with automated rules — lead scoring thresholds trigger SUBSCRIBER->LEAD->MQL->SQL transitions
- [x] **CRM-02**: Sales module writes `lifecycle_stage = CUSTOMER` on `customer_profiles` when a CONVERSION sale completes
- [x] **CRM-03**: Sales module writes `lifecycle_stage = EVANGELIST` (or updates `stage_repeat_customer`) on EXPANSION sale events and increments `lifetime_value`
- [x] **CRM-04**: Inactivity detection — mark customers as inactive after N days without `journey_events` (configurable threshold)
- [x] **CRM-05**: Churn detection — `lifecycle_stage = CHURNED` triggered by subscription cancellation events (Shopify/Stripe webhooks)

### Stage 0 — Atraccion (Fix & Validate)

- [x] **ATR-01**: Validate attraction data against real API responses from connected providers (Meta, Google, TikTok) for tenant "Visionarias"
- [x] **ATR-02**: Implement GA4 `runReport()` for organic search channels: google-organic (clicks from Search Console), direct traffic, AI-search (referrers from perplexity.ai, chatgpt.com, claude.ai)
- [x] **ATR-03**: Pull real reach/impressions from Instagram Graph API, YouTube Analytics API, Facebook Graph API, TikTok for Business API for organic social channels
- [x] **ATR-04**: Pull real clicks and spend from Meta Marketing API, Google Ads API, TikTok Ads API for paid channels
- [x] **ATR-05**: Cold Contact channel (outbound) shows response rate from CRM data (placeholder until outbound tools are integrated)

### Stage 1 — Captura

- [x] **CAP-01**: Detail panel showing two groups: Web Infrastructure leads (forms, Mailerlite) and AI Agent conversational leads (IG DMs, FB Messenger, TikTok DMs, WhatsApp inbound)
- [x] **CAP-02**: Backend endpoint `/metrics/capture` aggregating new `customer_profiles` by source channel with lead count and conversion rate from Stage 0
- [x] **CAP-03**: AI Agent leads tracked by extraction events where the agent successfully obtained email/phone from each messaging channel
- [x] **CAP-04**: Cost tracking per capture channel — Manychat licensing, LLM token consumption, WhatsApp API costs, Mailerlite subscription
- [x] **CAP-05**: Cost of Acquisition per Lead calculated as: Total Stage 0 investment / Total Stage 1 leads

### Stage 2 — Nutricion

- [x] **NUT-01**: Detail panel showing two groups: Retargeting Omnichannel (Meta/Google/TikTok retargeting campaigns) and Automation (newsletters via Mailerlite, AI SDR engagement)
- [x] **NUT-02**: Backend endpoint `/metrics/nurturing` tracking MQL conversion — profiles crossing lead_score threshold (e.g., >75 pts)
- [x] **NUT-03**: Retargeting metrics from Meta/Google/TikTok APIs filtered to MOFU campaigns (Custom Audiences, remarketing audiences)
- [x] **NUT-04**: Mailerlite API integration for newsletter engagement (open_rate, click_rate) contributing to lead scoring
- [x] **NUT-05**: Conversion rate: Leads -> MQLs with cost of nurturing per MQL

### Stage 3 — Oportunidad

- [x] **OPO-01**: Detail panel showing two groups: Web Transactional Friction (Shopify checkout-init, abandoned-cart) and High-Ticket Qualification (meetings booked via scheduling module)
- [x] **OPO-02**: Backend endpoint `/metrics/opportunity` tracking SQL pipeline — checkout initiations + meeting bookings
- [x] **OPO-03**: Shopify webhook integration for checkout events (use test data given known Shopify connection issues)
- [x] **OPO-04**: Meeting booked count from internal scheduling module (CRM leads with `meeting_booked` events)
- [x] **OPO-05**: Abandoned cart as bottleneck indicator — high abandoned-cart vs checkout-init ratio flagged visually

### Stage 4 — Ventas

- [x] **VEN-01**: Detail panel showing sales broken down by Offer Ladder position (core offer, subscription, upsell/expansion) using `type_offers` from Offer Studio
- [x] **VEN-02**: Backend endpoint `/metrics/sales` with revenue tracking — new money (CONVERSION) vs recurring (EXPANSION) split
- [x] **VEN-03**: Subscription revenue separated into: new subscriptions (`subscription_create`) vs renewals (`subscription_cycle`)
- [x] **VEN-04**: Cross-module read of Offer Studio `type_offers` via shared service or read-only projection (not direct ORM join)
- [x] **VEN-05**: CAC (Customer Acquisition Cost) calculated as: Total investment (Stages 0-3) / Total new customers (Stage 4 CONVERSION)

### Stage 5 — Adopcion

- [x] **ADO-01**: Detail panel showing customer health cohort per service sold: active users vs inactive users
- [x] **ADO-02**: Backend endpoint `/metrics/adoption` tracking product usage via `journey_events` post-purchase
- [x] **ADO-03**: Time-to-Value indicator — days from purchase to first meaningful engagement event
- [x] **ADO-04**: Inactivity as bottleneck — high inactive ratio predicts churn in next 30 days, flagged visually

### Stage 6 — Expansion

- [x] **EXP-01**: Detail panel showing: renewal events (MRR retained), upsell events (revenue expansion), and churn (MRR lost)
- [x] **EXP-02**: Backend endpoint `/metrics/expansion` tracking MRR retained vs lost, and upsell revenue
- [x] **EXP-03**: `lifetime_value` updated on `customer_profiles` for each EXPANSION event
- [x] **EXP-04**: Churn rate calculated — subscription cancellations / total active subscriptions; >5% flagged as critical bottleneck

### Stage 7 — Evangelizacion

- [x] **EVA-01**: Detail panel showing: referral conversions (purchases with `utm_source=referral` or assigned coupon), UGC count, and K-Factor
- [x] **EVA-02**: Backend endpoint `/metrics/evangelization` tracking referral-attributed sales and evangelist profiles
- [x] **EVA-03**: K-Factor calculation: (referrals sent per customer) x (conversion rate of referrals)
- [x] **EVA-04**: NPS integration via Mailerlite surveys — identify promoters (score 9-10) as potential evangelists

### Frontend — Detail Panel UX

- [x] **UI-01**: Consistent detail panel pattern across all 8 stages following ChannelGroup + ChannelRow + ConnectionBadge from AttractionDetail
- [x] **UI-02**: Each stage card in StageSummaryRow shows real KPI values (main + secondary) from backend, not hardcoded mock data
- [x] **UI-03**: Conversion rate between adjacent stages displayed on each stage card (Stage N->N+1 ratio)
- [ ] **UI-04**: Provider-specific channel icons and labels matching the channel definitions from the product spec

## v2 Requirements

Deferred to future releases. Tracked but not in current roadmap.

### UX Enhancements

- **UX-01**: Date range picker / time period selection across all stages
- **UX-02**: Action Triggers — click-to-act slider on funnel nodes to launch campaigns, adjust copy
- **UX-03**: Custom KPI goal/target setting per metric with red/green status
- **UX-04**: Export/download metrics data as CSV

### Advanced Analytics

- **ADV-01**: Multi-attribution model selection (first-touch, last-touch, linear)
- **ADV-02**: Cross-tenant benchmarking (anonymized industry comparisons)
- **ADV-03**: Real-time WebSocket updates for live data streams
- **ADV-04**: Strategy Canvas (Sankey diagram) integrated with metrics dashboard

### Integrations

- **INT-01**: Google Search Console API for detailed SEO keyword data
- **INT-02**: Meta Conversion API (server-side events) for landing pages
- **INT-03**: Outbound tool integrations (Apollo.io, Instantly) for Cold Contact metrics

## Out of Scope

| Feature | Reason |
|---------|--------|
| Sales Agent completion | Separate milestone; current AI SDR is in construction |
| Landing page generation from Offer Studio | Separate milestone; will feed analytics once built |
| Shopify connection repair | Known issues; use test data for Shopify-dependent metrics |
| New external connection OAuth flows | Reuse existing connections module; don't build new integrations |
| Sankey/flow diagram visualization | Already decided: columnar metrics are clearer for actionable insights |
| Multi-attribution model UI | Last-touch normalized across providers; exposing model selection adds complexity without value for target users |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUGFIX-01 | Phase 1: Critical Bug Fixes | Complete |
| BUGFIX-02 | Phase 1: Critical Bug Fixes | Complete |
| BUGFIX-03 | Phase 1: Critical Bug Fixes | Complete |
| INFRA-01 | Phase 2: Provider Adapter Infrastructure | Complete |
| INFRA-02 | Phase 2: Provider Adapter Infrastructure | Complete |
| INFRA-03 | Phase 2: Provider Adapter Infrastructure | Complete |
| INFRA-04 | Phase 2: Provider Adapter Infrastructure | Complete |
| INFRA-05 | Phase 2: Provider Adapter Infrastructure | Complete |
| CRM-01 | Phase 3: CRM Lifecycle Automation | Complete |
| CRM-02 | Phase 3: CRM Lifecycle Automation | Complete |
| CRM-03 | Phase 3: CRM Lifecycle Automation | Complete |
| CRM-04 | Phase 3: CRM Lifecycle Automation | Complete |
| CRM-05 | Phase 3: CRM Lifecycle Automation | Complete |
| ATR-01 | Phase 4: Stage 0 Attraction Fix & Validate | Complete |
| ATR-02 | Phase 4: Stage 0 Attraction Fix & Validate | Complete |
| ATR-03 | Phase 4: Stage 0 Attraction Fix & Validate | Complete |
| ATR-04 | Phase 4: Stage 0 Attraction Fix & Validate | Complete |
| ATR-05 | Phase 4: Stage 0 Attraction Fix & Validate | Complete |
| CAP-01 | Phase 5: Stage 1 Captura | Complete |
| CAP-02 | Phase 5: Stage 1 Captura | Complete |
| CAP-03 | Phase 5: Stage 1 Captura | Complete |
| CAP-04 | Phase 5: Stage 1 Captura | Complete |
| CAP-05 | Phase 5: Stage 1 Captura | Complete |
| NUT-01 | Phase 6: Stage 2 Nutricion | Complete |
| NUT-02 | Phase 6: Stage 2 Nutricion | Complete |
| NUT-03 | Phase 6: Stage 2 Nutricion | Complete |
| NUT-04 | Phase 6: Stage 2 Nutricion | Complete |
| NUT-05 | Phase 6: Stage 2 Nutricion | Complete |
| OPO-01 | Phase 7: Stage 3 Oportunidad | Complete |
| OPO-02 | Phase 7: Stage 3 Oportunidad | Complete |
| OPO-03 | Phase 7: Stage 3 Oportunidad | Complete |
| OPO-04 | Phase 7: Stage 3 Oportunidad | Complete |
| OPO-05 | Phase 7: Stage 3 Oportunidad | Complete |
| VEN-01 | Phase 8: Stage 4 Ventas | Complete |
| VEN-02 | Phase 8: Stage 4 Ventas | Complete |
| VEN-03 | Phase 8: Stage 4 Ventas | Complete |
| VEN-04 | Phase 8: Stage 4 Ventas | Complete |
| VEN-05 | Phase 8: Stage 4 Ventas | Complete |
| ADO-01 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| ADO-02 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| ADO-03 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| ADO-04 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| EXP-01 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| EXP-02 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| EXP-03 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| EXP-04 | Phase 9: Stages 5-6 Adoption & Expansion | Complete |
| EVA-01 | Phase 10: Stage 7 Evangelizacion | Complete |
| EVA-02 | Phase 10: Stage 7 Evangelizacion | Complete |
| EVA-03 | Phase 10: Stage 7 Evangelizacion | Complete |
| EVA-04 | Phase 10: Stage 7 Evangelizacion | Complete |
| UI-01 | Phase 11: Frontend Unification & Dashboard Polish | Complete |
| UI-02 | Phase 11: Frontend Unification & Dashboard Polish | Complete |
| UI-03 | Phase 11: Frontend Unification & Dashboard Polish | Complete |
| UI-04 | Phase 11: Frontend Unification & Dashboard Polish | Pending |

**Coverage:**
- v1 requirements: 54 total
- Mapped to phases: 54
- Unmapped: 0

---
*Requirements defined: 2026-03-15*
*Last updated: 2026-03-15 after roadmap creation*
