# Nicolify — Growth Studio: 8-Stage Metrics Dashboard

## What This Is

The complete Growth Studio metrics dashboard for Nicolify — an 8-stage funnel visualization (Atracción → Evangelización) that shows business owners their full marketing & sales lifecycle in real-time. Each stage drills down into channel-level metrics sourced from connected external platforms (Meta, Google, TikTok, Shopify, etc.) and internal CRM data. This milestone takes the dashboard from ~10% (partial Stage 1 only) to all 8 stages showing real, validated data with detail drill-down panels.

## Core Value

The business owner sees their entire customer lifecycle at a glance — from first impression to evangelist — and understands exactly where their funnel is healthy, where it's leaking, and what each metric means for their business growth.

## Requirements

### Validated

- ✓ 8-stage funnel card layout with horizontal scroll — existing
- ✓ Stage 0 (Atracción) detail panel with 13 channels (organic/paid split) — existing (needs data validation)
- ✓ Connection status badges per channel (Conectado/Configurar) — existing
- ✓ Mock data fallback system (ENABLE_MOCKS toggle) — existing
- ✓ Backend `/metrics/attraction` endpoint with connection status lookup — existing
- ✓ Connections module with OAuth for Meta, Google, TikTok, YouTube, etc. — existing
- ✓ CRM module with `customer_profiles` table and `lifecycle_stage` enum (8 stages) — existing
- ✓ `journey_events` table for tracking customer interactions — existing
- ✓ Sales module with CONVERSION vs EXPANSION detection — existing

### Active

**Data Infrastructure & Integration:**
- [ ] GA4 Data API integration — implement `runReport()` to pull real session/event data from Google Analytics
- [ ] CRM lifecycle stage transitions — implement `move_stage()` with automated rules (scoring thresholds, sale completion, engagement-based)
- [ ] Per-channel data aggregation services — pull real metrics from each connected platform's API (Meta Marketing API, Google Ads API, TikTok Ads API, YouTube Analytics API, etc.)
- [ ] Data consistency validation — verify that extracted data matches reality from each provider's API

**Stage 0 — Atracción (Fix & Complete):**
- [ ] Validate attraction data against real API responses from connected providers
- [ ] Implement real GA4 session data for organic search channels (google-organic, direct, ai-search)
- [ ] Map each channel metric to its correct API source with proper formulas

**Stage 1 — Captura:**
- [ ] Detail panel: Web infrastructure leads (forms, Mailerlite) + AI Agent conversational leads (IG DMs, FB Messenger, TikTok DMs, WhatsApp inbound)
- [ ] Backend endpoint `/metrics/capture` aggregating new `customer_profiles` by source channel
- [ ] Cost tracking per capture channel (Manychat licensing, LLM tokens, WhatsApp API costs)

**Stage 2 — Nutrición:**
- [ ] Detail panel: Retargeting omnichannel (Meta/Google/TikTok retargeting campaigns) + Automation (newsletters via Mailerlite, AI SDR engagement)
- [ ] Backend endpoint `/metrics/nurturing` tracking MQL conversion from lead scoring
- [ ] Integration with Mailerlite API for open_rate/engagement data

**Stage 3 — Oportunidad:**
- [ ] Detail panel: Web transactional friction (Shopify checkout-init, abandoned-cart) + High-ticket qualification (meetings booked via scheduling module)
- [ ] Backend endpoint `/metrics/opportunity` tracking SQL pipeline
- [ ] Shopify webhook integration for checkout events

**Stage 4 — Ventas:**
- [ ] Detail panel: Sales broken down by Offer Ladder type (core offer, subscription, upsell/expansion)
- [ ] Integration with Offer Studio `type_offers` to show sales by offer ladder position
- [ ] Backend endpoint `/metrics/sales` with revenue tracking (new money vs recurring)
- [ ] Distinction between CONVERSION (new customer) and EXPANSION (repeat) revenue

**Stage 5 — Adopción:**
- [ ] Detail panel: Customer health cohort (active vs inactive users) per service sold
- [ ] Backend endpoint `/metrics/adoption` tracking product usage via `journey_events`
- [ ] Inactivity detection (N days without engagement post-purchase)

**Stage 6 — Expansión:**
- [ ] Detail panel: Retention events (renewal-intent, upsell-intent) + Churn (cancellations)
- [ ] Backend endpoint `/metrics/expansion` tracking MRR retained vs lost
- [ ] Shopify/Stripe subscription webhook integration for renewal/cancellation events
- [ ] `lifetime_value` update on `customer_profiles` for repeat customers

**Stage 7 — Evangelización:**
- [ ] Detail panel: Viral loop metrics (UGC, referrals) + K-Factor calculation
- [ ] Backend endpoint `/metrics/evangelization` tracking referral conversions
- [ ] NPS survey integration (Mailerlite) and referral code tracking (Shopify coupon codes)

**Cross-cutting:**
- [ ] Consistent detail panel UX pattern across all 8 stages (replace PlaceholderDetail with real panels)
- [ ] Cost type system (NEUTRAL, EXPENSE, REVENUE) applied consistently per channel
- [ ] Provider-specific API casuistry documented and handled (rate limits, data formats, attribution windows)

### Out of Scope

- Action Triggers (click-to-act slider on funnel nodes) — future milestone, focus on visualization first
- Date range picker / time period selection — future enhancement
- Real-time refresh / WebSocket updates — React Query 5-min staleTime is sufficient
- Strategy Canvas (Sankey diagram) integration — separate component exists, not part of this milestone
- Export/download of metrics data — future feature
- Custom goal/target setting per metric — future feature
- Shopify connection fix — use test data for Shopify-dependent metrics
- New external connections — reuse existing connections module, don't create new integrations

## Context

**Existing Architecture:**
- Frontend: Next.js 14 (App Router) with Feature-Sliced Design. Growth Studio lives in `frontend/src/features/marketing-studio/`
- Backend: FastAPI with DDD. Analytics module at `backend/src/modules/analytics/`, CRM at `backend/src/modules/crm/`, Connections at `backend/src/modules/connections/`
- The connections module already has OAuth flows for Meta, Google (incl. Analytics admin), TikTok, YouTube, Mailerlite, Shopify, etc.
- Tenant "Visionarias" in the database has real connections configured for testing

**Current State (Atracción only, ~10%):**
- 8-stage card row renders with mock summary KPIs
- Only AttractionDetail.tsx has a real implementation (13 channels, organic/paid split)
- Stages 1-7 show PlaceholderDetail.tsx with "Próximamente" badge
- Backend has only `/metrics/attraction` endpoint
- Mock data fallback exists for development

**Technical Gaps Discovered:**
- GA4 Data API (`analyticsdata v1beta`) not implemented — only Admin API for property discovery
- CRM `move_stage()` is a placeholder (`pass`) — no automatic lifecycle transitions
- No transition audit trail for lifecycle changes
- Sales module detects CONVERSION vs EXPANSION but doesn't update `lifecycle_stage` on the profile

**Critical Architecture Rules:**
- Connections logic stays in `connections` module — don't duplicate API auth/token management
- Shared utilities go in `shared` module
- Growth metrics aggregation lives in `analytics` module
- Follow `backend-expert` and `frontend-expert` skill methodologies (reference `docs/domains/INDEX.md`)
- All queries must filter by `tenant_id` (multi-tenant isolation)

## Constraints

- **Module boundaries**: Strict DDD — connections in `connections`, metrics in `analytics`, customer data in `crm`. No cross-module shortcuts.
- **Docker-first**: All development and testing inside Docker containers (`visionarias_brain_dev`, `visionarias_client_dev`)
- **Existing connections**: Reuse what's built in the connections module. Don't create new connection infrastructure.
- **Provider API casuistry**: Each provider (Meta, Google, TikTok) delivers data differently — document and handle per-provider specifics.
- **Offer Ladder integration**: Stage 4 (Ventas) must reflect the Offer Studio's `type_offers` structure, not arbitrary product categories.
- **Soft deletes only**: Use `lifecycle_stage = CHURNED`, never hard-delete customer data.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Columnar metrics over Sankey diagram | Sankey was too complex for MVP; columns are clearer for actionable insights | — Pending |
| GA4 Data API needed for organic search metrics | Current Google connection only does Admin API; need `runReport()` for sessions/events | — Pending |
| CRM lifecycle transitions must be automated | Manual stage tracking won't scale; need scoring-based and event-based triggers | — Pending |
| Action Triggers deferred to next milestone | Focus on getting all 8 stages showing real data first | ✓ Good |
| Shopify uses test data | Known issues with Shopify connection; use mock/test data for Shopify-dependent stages | — Pending |

---
*Last updated: 2026-03-15 after initialization*
