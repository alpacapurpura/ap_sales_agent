# Feature Research

**Domain:** Marketing/Sales Funnel Analytics Dashboard (multi-provider, 8-stage lifecycle)
**Researched:** 2026-03-15
**Confidence:** HIGH (competitor analysis verified via multiple sources; project-specific conclusions from codebase inspection)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Stage-by-stage funnel visualization | Every funnel tool (HubSpot, Databox) shows stages left-to-right with counts and conversion rates | MEDIUM | Already exists as StageSummaryRow + StageCard. Gap: 7 of 8 stages show PlaceholderDetail |
| Conversion rate between adjacent stages | Baseline expectation: "How many Capturas became Oportunidades?" | LOW | Calculated from CRM `lifecycle_stage` counts. Stage N→N+1 ratio is the minimum viable metric for each card |
| Per-stage absolute count (volume) | Raw numbers matter as much as rates — "500 leads, 50 opportunities" | LOW | Backend endpoints need to return both count and conversion_rate |
| Channel-level breakdown within each stage | HubSpot, Triple Whale, Databox all let you drill into "which source drove this?" | HIGH | AttractionDetail.tsx already models this pattern with ChannelGroup + ChannelRow. Must replicate across all 8 stages |
| Organic vs. paid split | Standard in every serious analytics product. Paid = budgeted cost; organic = time cost | MEDIUM | Already exists in Stage 0. Cost type system (NEUTRAL / EXPENSE / REVENUE) must apply to all stages |
| Connection status per channel | Users must know if data is live or missing. Dead channel = unknown gap | LOW | ConnectionBadge already built. Must be present in every detail panel |
| Cost tracking per stage / channel | CAC, CPL, cost-per-opportunity are expected by any business owner reviewing ad spend | MEDIUM | Cost type system exists in PROJECT.md. Stages 1-3 have explicit cost items (Manychat, LLM tokens, Meta/Google spend) |
| KPI summary cards (top of each stage) | All competitors show a header row of 3-5 KPIs before drill-down | LOW | StageSummaryRow exists but feeds from mock data for stages 1-7 |
| Mock/fallback when provider is disconnected | Data gaps should not break the view. Competitors show "no data" gracefully | LOW | ENABLE_MOCKS toggle already exists. Must apply consistently to all new panels |
| Revenue visibility in sales stage | Users need to see money, not just counts. HubSpot closed-won, Triple Whale ROAS — revenue is mandatory | MEDIUM | Stage 4 (Ventas) must surface total revenue, new vs. recurring split |
| Retention / churn indicators post-sale | Bowtie/AARRR frameworks make retention a first-class metric, not an afterthought | MEDIUM | Stages 5-7 (Adopción, Expansión, Evangelización). Missing = product treats sales as end-of-funnel |

### Differentiators (Competitive Advantage)

Features that set Nicolify apart. Not required by convention, but high value in this context.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 8-stage Bowtie funnel (pre-sale + post-sale unified) | HubSpot/Databox stop at Closed-Won. Northbeam focuses only on paid acquisition. Showing Adopción, Expansión, Evangelización in one view gives creators a full lifecycle picture they cannot get elsewhere | HIGH | Stages 5-7 are the true differentiator. The Bowtie model (RevOps-inspired) covering both acquisition and retention sides is rare in tools targeting SMB creators |
| Offer Ladder integration in Stage 4 | Sales broken down by core offer / subscription / upsell position on the Offer Ladder — unique to Nicolify's architecture | MEDIUM | Requires join between `analytics` module and Offer Studio `type_offers`. No competitor ties sales funnel metrics to an internal offer taxonomy |
| AI SDR contribution visibility | Stage 1 (Captura) shows AI Agent conversational leads separately from web form leads — operators can see the direct ROI of the AI agent | MEDIUM | Requires `source_channel` tagging on `customer_profiles`. Unique to AaaS platforms |
| Automatic lifecycle stage progression | CRM transitions triggered by scoring thresholds, sale events, and engagement rules — not manual tagging. Competitors require manual pipeline movement | HIGH | CRM `move_stage()` is currently a `pass` placeholder. Implementing scoring-based automation is the hardest piece and the highest differentiator |
| K-Factor and viral loop metrics (Stage 7) | Most analytics tools ignore referral as a quantified loop. Triple Whale tracks affiliate codes but not K-Factor calculation | HIGH | Requires referral code tracking (Shopify coupons) + NPS integration (Mailerlite). Stage 7 is the "Evangelización" that justifies the full bowtie model |
| LTV update on repeat customer profiles | `lifetime_value` field on `customer_profiles` updated on each EXPANSION event — gives creators a true per-customer revenue view over time | MEDIUM | Requires EXPANSION detection (already exists in sales module) to write back to CRM |
| Source-agnostic adapter architecture | Future sources (Sales Agent closings, generated Landing Pages, new integrations) will plug into the same metrics pipeline without rebuilding the dashboard | HIGH | Described in PROJECT.md as a constraint. Adapter/provider pattern in `analytics` module is a differentiator for long-term extensibility |

### Anti-Features (Commonly Requested, Often Problematic)

Features to deliberately NOT build in this milestone.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Date range picker / time period selector | "I want to see last 30 days vs. last 90 days" is a natural ask | Requires all 8 backend endpoints to accept date params + all frontend queries to pass them. Doubles query complexity. Risks showing misleading data before normalization is solid | Build with fixed trailing-30-day window first. Add date range once all 8 stages return validated data. Explicitly out-of-scope in PROJECT.md |
| Real-time / WebSocket updates | "I want live data as it comes in" sounds powerful | Creates polling infrastructure, connection management, and cache invalidation complexity that has no ROI when the underlying data refreshes hourly at best from external APIs | React Query 5-min staleTime is the correct answer here. Already decided in PROJECT.md |
| Custom goal/target setting per metric | "I want to set my own KPI targets and see red/green status" | Requires a separate goals schema, per-tenant target storage, and UI to manage targets — a product unto itself. Creates a maintenance burden before the metrics themselves are stable | Defer to v2. Show absolute values and rates clearly; let the user form their own judgment |
| Multi-attribution model selection | "Show me first-touch vs. last-touch vs. linear attribution" | Attribution modeling is a rabbit hole. Triple Whale has 7 models; Northbeam has 6 — neither makes users smarter without a data science background | Use last-touch as the default attribution model, document it clearly. Do not expose model selection in the UI for this milestone |
| Export / download of metrics data | "Can I download this as CSV?" | CSV export implies stable, well-defined schemas. Until all 8 stages have validated real data, exporting creates data quality liability | Explicitly out-of-scope per PROJECT.md. Add after data is validated |
| Action Triggers (click-to-act slider) | "I want to launch a retargeting campaign from the funnel node" | Requires a trigger/automation system that does not exist yet. The funnel visualization must be solid before attaching actions | Deferred to next milestone per PROJECT.md. Visualization-first is the right call |
| Sankey / flow diagram variant | "I want to see flows between stages" | Sankey was evaluated and rejected. Columnar metrics are clearer for actionable insights at this product stage | Already decided in PROJECT.md. The columnar detail panel pattern (ChannelGroup + ChannelRow) is the right UX |
| Cross-tenant benchmarking ("how do I compare to other creators?") | Sounds valuable — anonymized industry benchmarks | Requires aggregating cross-tenant data, which has multi-tenancy isolation implications. Premature before single-tenant experience is proven | Defer entirely. Focus on absolute metrics and internal cohort comparisons first |

---

## Feature Dependencies

```
[Stage N Detail Panel (UI)]
    └──requires──> [Backend /metrics/{stage} endpoint]
                       └──requires──> [CRM lifecycle_stage counts per tenant]
                       └──requires──> [Per-provider API data pull service]
                                          └──requires──> [Connections module OAuth token]

[Cost per channel display]
    └──requires──> [Cost type system (NEUTRAL/EXPENSE/REVENUE) applied to each channel]
                       └──requires──> [Backend cost aggregation per stage]

[CRM lifecycle auto-transitions (move_stage)]
    └──requires──> [Lead scoring rules implementation]
    └──requires──> [Sales module writing lifecycle_stage on CONVERSION/EXPANSION events]

[Stage 4 Ventas — Offer Ladder breakdown]
    └──requires──> [CRM lifecycle_stage = CUSTOMER counts]
    └──requires──> [Offer Studio type_offers joined to sales events]

[Stage 7 Evangelización — K-Factor]
    └──requires──> [Referral code tracking (Shopify coupons or custom)]
    └──requires──> [NPS data from Mailerlite integration]
    └──requires──> [Stage 6 Expansión data stable]

[LTV on customer_profiles]
    └──requires──> [EXPANSION detection in sales module writing back to CRM]
    └──enhances──> [Stage 6 Expansión MRR tracking]

[Mock/fallback display]
    └──enhances──> [Every detail panel]
    └──conflicts──> [Real data validation] (must be toggled off when validating real API responses)
```

### Dependency Notes

- **Detail panels require backend endpoints:** No panel should be built without a corresponding `/metrics/{stage}` endpoint returning real or mock-structured data. Building UI against undefined shapes wastes time.
- **CRM move_stage() must be implemented before stages 2-7 show meaningful counts:** All post-Captura stages derive their counts from lifecycle_stage transitions. The placeholder `pass` implementation makes all downstream stages return zero.
- **Stage 4 Offer Ladder requires cross-module query:** The `analytics` module must query Offer Studio data without violating DDD module boundaries — use a shared service or read-only projection, not a direct ORM join.
- **Stage 7 depends on Stage 6 stability:** K-Factor calculation requires knowing retained customers (Stage 6) before computing how many they referred. Build and validate Stage 6 first.
- **Attribution window differences between providers create discrepancy:** Meta (7-day click / 1-day view), Google (30-day click), TikTok (7-day click / 1-day view) all count the same conversion differently. The backend must normalize to a single attribution window and document which one is used.

---

## MVP Definition

### Launch With (v1 — this milestone)

Minimum to replace all 7 PlaceholderDetail panels with real, validated panels.

- [ ] CRM `move_stage()` implemented with automated rules — without this, stages 1-7 show zero counts regardless of data quality
- [ ] All 8 backend `/metrics/{stage}` endpoints returning real or validated-mock data with consistent DTO shape
- [ ] All 8 detail panels following the ChannelGroup + ChannelRow + ConnectionBadge pattern from AttractionDetail
- [ ] Cost type system (NEUTRAL / EXPENSE / REVENUE) applied consistently across all channels in all panels
- [ ] Stage 4 Ventas shows revenue with new vs. recurring split (CONVERSION vs. EXPANSION)
- [ ] Stage 5 Adopción shows active vs. inactive customer cohort
- [ ] Stage 6 Expansión shows MRR retained vs. lost
- [ ] Stage 7 Evangelización shows referral count and K-Factor (even if K-Factor is estimated)
- [ ] Connection status badges present in every panel (Conectado / Configurar)
- [ ] Mock fallback active for all Shopify-dependent metrics (known broken connection)

### Add After Validation (v1.x)

- [ ] GA4 `runReport()` for real organic search session data in Stage 0 — trigger: real Meta/Google Ads data is validated first
- [ ] LTV write-back to `customer_profiles` on EXPANSION events — trigger: Stage 6 data is stable
- [ ] Attribution window normalization UI hint — show users which window is used, trigger: discrepancies are reported by real users
- [ ] Date range selector — trigger: all 8 stages return validated real data consistently

### Future Consideration (v2+)

- [ ] Action Triggers (click-to-act automation launch from funnel node) — deferred to next milestone by design
- [ ] Custom KPI goal setting — defer until PMF is established
- [ ] Cross-tenant benchmarking — defer; multi-tenant data aggregation is a separate architectural concern
- [ ] Multi-attribution model selection — defer; requires data science background to use correctly
- [ ] Export/download — defer until data schemas are stable and validated

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| CRM move_stage() automated rules | HIGH | HIGH | P1 — blocker for all other stages |
| Backend endpoints for stages 1-7 | HIGH | HIGH | P1 — nothing else renders without this |
| Detail panels for stages 1-3 (Captura, Nutrición, Oportunidad) | HIGH | MEDIUM | P1 — pre-sale funnel is core |
| Stage 4 Ventas with revenue + offer ladder | HIGH | MEDIUM | P1 — money is always highest priority |
| Connection status badges in all panels | HIGH | LOW | P1 — prevents silent data gaps |
| Stage 5 Adopción (active vs. inactive) | MEDIUM | MEDIUM | P2 — retention signal, builds toward churn |
| Stage 6 Expansión (MRR retained/lost) | MEDIUM | MEDIUM | P2 — churn visibility is critical for creator businesses |
| Stage 7 Evangelización (K-Factor, referrals) | MEDIUM | HIGH | P2 — differentiator but complex |
| Cost tracking per channel across all stages | HIGH | MEDIUM | P1 — creators need to know their ad spend ROI per stage |
| Mock fallback consistency across all panels | MEDIUM | LOW | P1 — prevents broken UI during development |
| Attribution window normalization | MEDIUM | MEDIUM | P2 — prevents user confusion when numbers don't match platform reports |
| GA4 runReport() organic data | MEDIUM | HIGH | P2 — Stage 0 works with mock; real data is an improvement |
| LTV write-back on EXPANSION | LOW | MEDIUM | P3 — valuable but not blocking milestone delivery |

**Priority key:**
- P1: Must have for milestone completion
- P2: Should have, add when P1s are stable
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | HubSpot | Triple Whale | Northbeam | Databox | Nicolify Approach |
|---------|---------|--------------|-----------|---------|-------------------|
| Funnel stage visualization | Lifecycle stages (Subscriber → Customer) — stops at close | Acquisition to purchase (Shopify-only) | Paid acquisition focused | Configurable pipeline stages | 8-stage Bowtie including post-sale Adopción, Expansión, Evangelización |
| Post-sale retention metrics | Separate "Service Hub" product, not integrated | Limited — LTV calculation only | Not present | Not present | First-class stages 5-7 in same dashboard |
| Organic vs. paid split | Yes, by source/medium in traffic analytics | No — paid only (that's its purpose) | No — paid only | Yes, via GA4 integration | Yes — ChannelGroup pattern with cost type per channel |
| Multi-provider aggregation | HubSpot-native only; integrates via connectors | Meta + Shopify core; Google and TikTok added | Meta, Google, TikTok, YouTube, podcasts | 100+ connectors via Databox | Meta, Google, TikTok, YouTube, Mailerlite, Shopify via existing connections module |
| Offer/product-level sales breakdown | Deal pipeline stages | Product-level ROAS | Not present | Configurable | Offer Ladder position (core / subscription / upsell) — unique |
| AI agent contribution visibility | Not present | Not present | Not present | Not present | Stage 1 shows AI SDR leads separately from web form leads — unique to AaaS |
| K-Factor / viral loop metrics | Not present | Affiliate tracking only | Not present | Not present | Stage 7 K-Factor — differentiator |
| Attribution model | Last-touch default; multi-touch in Marketing Hub Pro | 7 models | 6 models + MMM | Depends on source | Last-touch default; normalize attribution windows across providers |
| Real-time data | Near-real-time | Near-real-time | Hourly | Depends on source (hourly/daily) | React Query 5-min staleTime — adequate for creator business cadence |

---

## Sources

- [HubSpot Funnel Reports — Knowledge Base](https://knowledge.hubspot.com/reports/create-new-custom-funnel-reports) — HIGH confidence
- [7 Essential HubSpot Marketing Dashboard Examples for 2026](https://www.3andfour.com/articles/hubspot-marketing-dashboard-examples) — MEDIUM confidence
- [Triple Whale vs Northbeam 2026 Comparison](https://www.headwestguide.com/triple-whale-vs-northbeam) — MEDIUM confidence
- [Databox Funnel Report Guide](https://databox.com/funnel-report) — HIGH confidence
- [Bowtie Funnel Model — RevPartners](https://blog.revpartners.io/en/revops-articles/bowtie-funnel) — HIGH confidence
- [SaaSTrack — How to Define Bowtie Metrics](https://www.saastrack.ai/blog/how-to-define-your-bowtie-metrics) — MEDIUM confidence
- [AARRR Metrics — Shopify Guide 2026](https://www.shopify.com/blog/aarrr-metrics) — HIGH confidence
- [10 Must-Track Metrics for Marketing Dashboards in 2026](https://analyticsbeyond.com/10-must-track-metrics-for-marketing-dashboards-in-2026/) — MEDIUM confidence
- [Marketing Dashboard Best Practices 2025 — Dataslayer](https://www.dataslayer.ai/blog/marketing-dashboard-best-practices-2025) — MEDIUM confidence
- [Attribution Window Best Practices 2026 — Cometly](https://www.cometly.com/post/attribution-window-best-practices) — MEDIUM confidence
- [Data Discrepancies in Marketing — Databeats](https://databeats.community/p/data-discrepancies-in-marketing) — MEDIUM confidence
- [The 7 Best Marketing Dashboard Tools for 2026 — Funnel.io](https://funnel.io/blog/marketing-dashboard-tools) — MEDIUM confidence
- [11 Marketing Measurement Mistakes — inBeat 2025](https://inbeat.agency/blog/marketing-measurement-mistakes) — MEDIUM confidence

---

*Feature research for: Nicolify Growth Studio — 8-Stage Funnel Metrics Dashboard*
*Researched: 2026-03-15*
