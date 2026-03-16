# Roadmap: Nicolify Growth Studio — 8-Stage Metrics Dashboard

## Overview

This roadmap takes the Growth Studio dashboard from ~10% (partial Stage 0 only) to all 8 stages showing real, validated data with detail drill-down panels. The build order is constrained: critical bug fixes and infrastructure must land before any real data can flow, CRM lifecycle automation must work before any stage counts are meaningful, and pre-sale stages (0-4) must be validated before post-sale stages (5-7) can trust the conversion-to-retention handoff. The final phase unifies the frontend experience across all 8 stages.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Critical Bug Fixes** - Fix broken Meta API v19.0, Meta SDK multi-tenant data leak, and missing GA4 Data API client (completed 2026-03-15)
- [ ] **Phase 2: Provider Adapter Infrastructure** - Build the adapter base class, connection port, Redis cache, cost type system, and mock/fallback mechanism
- [ ] **Phase 3: CRM Lifecycle Automation** - Implement move_stage() with automated rules, sale-triggered transitions, inactivity and churn detection
- [x] **Phase 4: Stage 0 Attraction Fix & Validate** - Wire real API data into the existing Attraction panel and prove the infrastructure works end-to-end (completed 2026-03-15)
- [x] **Phase 5: Stage 1 Captura** - Build the Capture detail panel with web infrastructure leads and AI Agent conversational leads (completed 2026-03-16)
- [x] **Phase 6: Stage 2 Nutricion** - Build the Nurturing detail panel with retargeting and automation metrics (completed 2026-03-16)
- [ ] **Phase 7: Stage 3 Oportunidad** - Build the Opportunity detail panel with transactional friction and high-ticket qualification
- [ ] **Phase 8: Stage 4 Ventas** - Build the Sales detail panel with Offer Ladder breakdown and CONVERSION vs EXPANSION revenue
- [ ] **Phase 9: Stages 5-6 Adoption & Expansion** - Build the post-sale retention panels covering customer health, MRR, and churn
- [ ] **Phase 10: Stage 7 Evangelizacion** - Build the viral loop panel with referrals, K-Factor, and NPS
- [ ] **Phase 11: Frontend Unification & Dashboard Polish** - Ensure consistent UX across all 8 stages with real KPIs, conversion rates, and proper icons

## Phase Details

### Phase 1: Critical Bug Fixes
**Goal**: External API integrations stop failing silently and stop leaking data between tenants
**Depends on**: Nothing (first phase)
**Requirements**: BUGFIX-01, BUGFIX-02, BUGFIX-03
**Success Criteria** (what must be TRUE):
  1. Meta API calls use v22.0+ and return valid responses instead of HTTP 400 errors
  2. Two concurrent requests for different tenants never receive each other's Meta data (per-request SDK instantiation verified)
  3. GA4 Data API client can execute a `runReport()` call and return real session data for a connected property
**Plans**: 2 plans

Plans:
- [x] 01-01: Meta API version update and SDK per-tenant fix
- [x] 01-02: GA4 Data API client implementation

### Phase 2: Provider Adapter Infrastructure
**Goal**: A uniform, cached, fault-tolerant data pipeline exists that all 8 stages can plug into
**Depends on**: Phase 1
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. A new provider adapter can be added by implementing one ABC without modifying service or API layers
  2. Analytics module retrieves decrypted OAuth credentials from connections module without importing connection application services
  3. Repeated metric requests within TTL window return cached results from Redis (no duplicate API calls)
  4. Every channel metric DTO carries a cost_type field (NEUTRAL, EXPENSE, or REVENUE)
  5. Disconnected providers show "Configurar" badge in the UI instead of errors or broken layouts
**Plans**: 5 plans

Plans:
- [ ] 02-01-PLAN.md — Domain contracts, DB models, tenant priority field, cost type system, and Alembic migration
- [ ] 02-02-PLAN.md — ConnectionPort implementation (with token refresh), provider registry, Redis cache, and ETL pipeline
- [ ] 02-03-PLAN.md — ARQ workers, seed script, channel registry, ETL health endpoints, and router registration
- [ ] 02-04-PLAN.md — MetricsService refactor (ETL tables) and frontend dynamic channel rendering
- [ ] 02-05-PLAN.md — Gap closure: ChannelRegistry provider matching fix, per-stage cache TTL, ETL aggregation persistence

### Phase 3: CRM Lifecycle Automation
**Goal**: Customer profiles automatically progress through lifecycle stages based on scoring rules and business events
**Depends on**: Phase 2
**Requirements**: CRM-01, CRM-02, CRM-03, CRM-04, CRM-05
**Success Criteria** (what must be TRUE):
  1. A lead crossing the scoring threshold automatically transitions from SUBSCRIBER to LEAD to MQL to SQL without manual intervention
  2. When a CONVERSION sale completes, the customer profile's lifecycle_stage is set to CUSTOMER
  3. When an EXPANSION sale completes, the customer profile's lifetime_value is incremented and stage reflects repeat purchase
  4. Customers with no journey_events for N configurable days are detected as inactive
  5. Subscription cancellation events trigger lifecycle_stage = CHURNED on the corresponding profile
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md — EventBus infrastructure, scoring config, DB migration (new columns + lifecycle_transitions table), lifecycle repository
- [ ] 03-02-PLAN.md — Scoring engine (LifecycleService), threshold transitions, sale-triggered lifecycle changes via EventBus
- [ ] 03-03-PLAN.md — Batch inactivity detection with score decay, churn event handler, manual override API

### Phase 4: Stage 0 Attraction Fix & Validate
**Goal**: The existing Attraction panel shows real, validated metrics from connected providers instead of mock/zero data
**Depends on**: Phase 2 (adapter infrastructure), Phase 1 (fixed APIs)
**Requirements**: ATR-01, ATR-02, ATR-03, ATR-04, ATR-05
**Success Criteria** (what must be TRUE):
  1. Attraction metrics for tenant "Visionarias" match values visible in each provider's native dashboard (within attribution window tolerance)
  2. Organic search channels (google-organic, direct, AI-search) display real GA4 session data from runReport()
  3. Organic social channels (Instagram, YouTube, Facebook, TikTok) display real reach/impressions from their respective APIs
  4. Paid channels (Meta Ads, Google Ads, TikTok Ads) display real clicks and spend from their marketing APIs
  5. Cold Contact channel shows a response rate placeholder sourced from CRM data
**Plans**: 3 plans

Plans:
- [ ] 04-01-PLAN.md — Multi-metric DTO contracts, 6 provider adapters (Meta, GA4, Google Ads, TikTok, YouTube, CRM), connection clients, and unit tests
- [ ] 04-02-PLAN.md — MetricsService multi-metric aggregation, API update, and frontend ChannelRow/ChannelGroup/AttractionDetail redesign with error UX
- [ ] 04-03-PLAN.md — Validation script (ETL vs live API comparison with 5% tolerance) and end-to-end human verification

### Phase 5: Stage 1 Captura
**Goal**: Business owner sees exactly how many leads each channel captures and what each lead costs
**Depends on**: Phase 3 (CRM lifecycle for lead counts), Phase 4 (proven adapter pattern)
**Requirements**: CAP-01, CAP-02, CAP-03, CAP-04, CAP-05
**Success Criteria** (what must be TRUE):
  1. Capture detail panel shows two distinct groups: Web Infrastructure leads and AI Agent conversational leads
  2. `/metrics/capture` endpoint returns new customer_profiles aggregated by source channel with lead counts
  3. AI Agent leads are tracked by extraction events where the agent obtained email/phone from messaging channels
  4. Each capture channel displays its associated cost (Manychat, LLM tokens, WhatsApp API, Mailerlite)
  5. Cost of Acquisition per Lead is calculated and displayed as total Stage 0 investment divided by total Stage 1 leads
**Plans**: 2 plans

Plans:
- [ ] 05-01-PLAN.md -- Backend: DTOs, cost model, CRM lead repository, LeadCapturedEvent, capture endpoint
- [ ] 05-02-PLAN.md -- Frontend: CaptureDetail panel, MiniFunnel, CostLink, types, hook, and MetricsDashboard wiring

### Phase 6: Stage 2 Nutricion
**Goal**: Business owner sees which nurturing activities are converting leads into marketing-qualified prospects
**Depends on**: Phase 5 (Stage 1 lead data feeds Stage 2 conversion rates)
**Requirements**: NUT-01, NUT-02, NUT-03, NUT-04, NUT-05
**Success Criteria** (what must be TRUE):
  1. Nurturing detail panel shows two groups: Retargeting Omnichannel and Automation
  2. `/metrics/nurturing` endpoint returns MQL conversion count based on lead_score threshold crossing
  3. Retargeting metrics are sourced from Meta/Google/TikTok APIs filtered to MOFU campaigns only
  4. Mailerlite newsletter engagement data (open_rate, click_rate) is integrated and contributes to lead scoring
  5. Conversion rate (Leads to MQLs) and cost of nurturing per MQL are calculated and displayed
**Plans**: 3 plans

Plans:
- [x] 06-01-PLAN.md — Backend: NurtureDetailDTO, NurtureMetricsRepository, StageCostService, provider stage filtering, Mailerlite webhook, GET /metrics/nurturing endpoint
- [x] 06-02-PLAN.md — Frontend: NurtureDetail panel, CampaignDrillDown, types, hook, ChannelGroup/ChannelRow modifications, MetricsDashboard wiring
- [ ] 06-03-PLAN.md — Gap closure: Implement MailerLiteConnector.get_recent_campaign_activity for ETL backup sync

### Phase 7: Stage 3 Oportunidad
**Goal**: Business owner sees their sales pipeline: who is about to buy and where friction is causing drop-off
**Depends on**: Phase 6 (Stage 2 MQL data feeds Stage 3 conversion rates)
**Requirements**: OPO-01, OPO-02, OPO-03, OPO-04, OPO-05
**Success Criteria** (what must be TRUE):
  1. Opportunity detail panel shows two groups: Web Transactional Friction and High-Ticket Qualification
  2. `/metrics/opportunity` endpoint returns SQL pipeline count from checkout initiations and meeting bookings
  3. Shopify checkout events are handled via test data (given known connection issues) with proper mock fallback
  4. Meeting booked count is sourced from the internal scheduling module via CRM journey_events
  5. High abandoned-cart vs checkout-init ratio is flagged visually as a bottleneck indicator
**Plans**: TBD

Plans:
- [ ] 07-01: Opportunity backend endpoint with Shopify test data and scheduling integration
- [ ] 07-02: Opportunity detail panel frontend component

### Phase 8: Stage 4 Ventas
**Goal**: Business owner sees total revenue broken down by offer type, with clear separation of new vs recurring money
**Depends on**: Phase 3 (CRM CONVERSION/EXPANSION detection), Phase 7 (complete pre-sale funnel)
**Requirements**: VEN-01, VEN-02, VEN-03, VEN-04, VEN-05
**Success Criteria** (what must be TRUE):
  1. Sales detail panel breaks down revenue by Offer Ladder position (core offer, subscription, upsell/expansion) using type_offers from Offer Studio
  2. `/metrics/sales` endpoint returns revenue with clear CONVERSION (new money) vs EXPANSION (recurring) split
  3. Subscription revenue is separated into new subscriptions vs renewals
  4. Offer Studio type_offers data is accessed via shared service or read-only projection without direct ORM join
  5. CAC is calculated as total investment from Stages 0-3 divided by total new CONVERSION customers
**Plans**: TBD

Plans:
- [ ] 08-01: Offer Studio cross-module read and sales backend endpoint
- [ ] 08-02: Sales detail panel frontend component with Offer Ladder breakdown

### Phase 9: Stages 5-6 Adoption & Expansion
**Goal**: Business owner sees customer health post-purchase and understands retention: who is active, who is expanding, who is churning
**Depends on**: Phase 8 (Stage 4 must set CUSTOMER lifecycle_stage before post-sale stages are meaningful)
**Requirements**: ADO-01, ADO-02, ADO-03, ADO-04, EXP-01, EXP-02, EXP-03, EXP-04
**Success Criteria** (what must be TRUE):
  1. Adoption panel shows active vs inactive customer cohort per service sold
  2. `/metrics/adoption` endpoint tracks product usage via journey_events post-purchase with time-to-value indicator
  3. High inactive ratio is flagged visually as a churn predictor
  4. Expansion panel shows MRR retained vs lost and upsell revenue
  5. `/metrics/expansion` endpoint tracks churn rate and updates lifetime_value on customer_profiles for EXPANSION events
**Plans**: TBD

Plans:
- [ ] 09-01: Adoption backend endpoint and detail panel
- [ ] 09-02: Expansion backend endpoint and detail panel

### Phase 10: Stage 7 Evangelizacion
**Goal**: Business owner sees their viral growth loop: who is referring, how referrals convert, and overall K-Factor
**Depends on**: Phase 9 (retention data needed for K-Factor denominator)
**Requirements**: EVA-01, EVA-02, EVA-03, EVA-04
**Success Criteria** (what must be TRUE):
  1. Evangelization panel shows referral conversions, UGC count, and K-Factor
  2. `/metrics/evangelization` endpoint tracks referral-attributed sales and evangelist profiles
  3. K-Factor is calculated as (referrals sent per customer) x (conversion rate of referrals)
  4. NPS integration via Mailerlite surveys identifies promoters (score 9-10) as potential evangelists
**Plans**: TBD

Plans:
- [ ] 10-01: Evangelization backend endpoint with referral and NPS tracking
- [ ] 10-02: Evangelization detail panel frontend component

### Phase 11: Frontend Unification & Dashboard Polish
**Goal**: All 8 stages present a consistent, polished experience with real summary KPIs and inter-stage conversion rates
**Depends on**: Phases 4-10 (all stage backends must exist)
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. All 8 detail panels follow the same ChannelGroup + ChannelRow + ConnectionBadge pattern consistently
  2. Every stage card in StageSummaryRow shows real KPI values from its backend endpoint, not hardcoded mock data
  3. Each stage card displays the conversion rate to the next stage (Stage N count / Stage N+1 count)
  4. Provider-specific channel icons and labels match the channel definitions from the product spec across all panels
**Plans**: TBD

Plans:
- [ ] 11-01: Summary row KPI integration and conversion rate display
- [ ] 11-02: Cross-stage UX audit and icon/label consistency pass

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Critical Bug Fixes | 2/2 | Complete   | 2026-03-15 |
| 2. Provider Adapter Infrastructure | 0/4 | Not started | - |
| 3. CRM Lifecycle Automation | 2/3 | In Progress|  |
| 4. Stage 0 Attraction Fix & Validate | 3/3 | Complete   | 2026-03-15 |
| 5. Stage 1 Captura | 2/2 | Complete   | 2026-03-16 |
| 6. Stage 2 Nutricion | 2/3 | Gap closure | - |
| 7. Stage 3 Oportunidad | 0/2 | Not started | - |
| 8. Stage 4 Ventas | 0/2 | Not started | - |
| 9. Stages 5-6 Adoption & Expansion | 0/2 | Not started | - |
| 10. Stage 7 Evangelizacion | 0/2 | Not started | - |
| 11. Frontend Unification & Dashboard Polish | 0/2 | Not started | - |
