# Phase 10: Stage 7 Evangelizacion - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the Evangelization detail panel (Stage 7) showing the viral growth loop: who is referring, how referrals convert, overall K-Factor, and reputation metrics (NPS + UGC). Backend endpoint `/metrics/evangelization` tracking referral-attributed sales, evangelist profiles, and NPS survey responses. **Additionally**: complete NPS survey system (model, trigger UI, customer-facing survey form with channel-agnostic delivery), referral code management (auto-generation + Shopify extraction), and evangelist promotion workflow.

Stage 7 focuses on **viral growth and reputation** — are customers actively promoting your business, and how effective is that promotion?

</domain>

<decisions>
## Implementation Decisions

### Referral Tracking (Multi-Source)
- **Combined tracking**: Shopify coupon codes (high confidence) + UTM parameters (broader reach). K-Factor uses combined data
- **Source-agnostic design**: ReferralCode model supports `source` field (internal, shopify, external). Prepared for WooCommerce and future platforms
- **App-as-single-point mentality**: progressively this app becomes the only sales touchpoint — architecture must support multiple referral sources with proper technical design

### Referral Code Management
- **Auto-generated codes**: system generates unique referral codes per customer
- **Manual assignment by owner**: owner decides WHO gets a referral code (not every customer automatically). Gives control over which customers are trusted referrers
- **Shopify extraction (read-only)**: implement Shopify Admin API read to extract existing discount codes and import them as referral codes. Do NOT push codes to Shopify yet
- **Model in CRM module**: ReferralCode model with fields: code, customer_id (referrer), tenant_id, source (internal/shopify/external), created_at, is_active
- **Referral attribution**: when a sale has a referral code or utm_source=referral, link the sale to the referrer customer via referred_by field

### Panel Structure (Two Groups)
- **Group 1 — Referidos**: referral conversions, revenue attributed, top referrer cards
- **Group 2 — Reputacion**: NPS aggregated score, promoter count, UGC/testimonials
- **Evangelist cards** (not rows) in Referidos group: each evangelist gets a card showing name, referral code, referrals sent, conversions, revenue attributed. Consistent with offer card pattern from Phases 8-9
- **Candidatos a Evangelista section**: badge/section showing customers with NPS >= 9 who haven't been promoted yet. Owner clicks to promote

### Header KPIs (Two Rows — 5 Total)
- **Primary row (3 KPIs)**: K-Factor | Referidos (conversion count) | NPS Score
- **Secondary row (2 KPIs)**: Revenue Referido (monetary amount) | Evangelistas (active count)
- Follows the 3+2 header pattern from Phase 9
- User-friendly Spanish labels with tooltip hints (carried from Phase 9)
- Dual currency on Revenue Referido (carried from Phase 8-9)

### MiniFunnel
- **Clientes Activos (N) → Evangelistas (M) = X%** — shows what percentage of customer base is actively referring
- Continues funnel chain from Stage 6 (Expansion)

### NPS Survey System (Complete in This Phase)
- **Channel-agnostic delivery design**: survey delivery decoupled from survey content. Any channel adapter can send the survey
- **Two initial delivery mechanisms**:
  1. **Universal link**: unique URL per survey instance, works in any medium (email, WhatsApp, Manychat, DM, social, etc.)
  2. **WhatsApp conversational native**: using WhatsApp interactive controls (buttons, lists) so client responds without leaving the chat interface
- **Researcher MUST investigate**: startups doing WhatsApp conversational surveys (SurveySparrow, Typeform WhatsApp, Delighted, AskNicely, etc.) and copy best practices for the conversational flow
- **Researcher MUST investigate**: Salesforce NPS module, and SaaS startups excelling at NPS/satisfaction surveys, to propose the minimal viable essence — dynamic and simple
- **Survey trigger**: owner decides when to launch survey — per offer (all customers of that offer) or individually (specific customer). UI for triggering surveys in the evangelization panel
- **Survey fields**: researcher proposes optimal fields based on best practices. MUST include testimonial capture (written or audio format — researcher investigates how others have achieved this and proposes approach)
- **Consent mechanism**: researcher proposes based on best practices (for using testimonials publicly on web/marketing)
- **NPS scoring on CRM profile**: each customer's NPS response mapped to their profile for service differentiation (know how they rated you to inform how you serve them)

### UGC Definition
- **Researcher proposes** what counts as UGC based on what reference startups track
- Must include testimonials from NPS surveys at minimum
- Social mentions, reviews, etc. — researcher determines what's viable for micro-business context

### Evangelist Triggers (Combined: Auto + Manual)
- **NPS >= 9 auto-suggests**: when a customer responds with score 9-10 (NPS promoter), they appear in "Candidatos a Evangelista" section in the panel
- **Owner manually promotes**: owner clicks to confirm promotion to EVANGELIST lifecycle stage
- **Owner can also manually promote** any customer regardless of NPS (direct promotion without survey)
- **Permanent status**: once EVANGELIST, always EVANGELIST. If they cancel subscription → CHURNED (not back to CUSTOMER). No degradation mechanism

### Bottleneck Visualization
- Follows dual pattern from Phases 7-9: panel-level banner + inline badge
- **Low K-Factor**: K-Factor below threshold triggers warning banner
- **Low NPS response rate**: if few customers have responded to surveys, suggest sending more
- Context-aware tips based on data patterns (researcher calibrates thresholds and tip library)

### Claude's Discretion
- Evangelist card component design (spacing, shadows, badge styling)
- Referral code format (alphanumeric, length, prefix)
- NPS survey form visual design (web page for universal link)
- WhatsApp interactive message structure (buttons vs list vs quick replies)
- Bottleneck threshold calibration (after researcher investigates)
- UGC display format in Reputacion group
- Error/empty states for evangelization-specific scenarios
- K-Factor formula implementation details (after researcher investigates viral loop best practices)
- Audio testimonial storage approach (if researcher recommends audio)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Analytics Pattern (Phase 8-9 reference)
- `backend/src/modules/analytics/api/metrics.py` — All /metrics/* endpoint patterns (capture through expansion)
- `backend/src/modules/analytics/application/services/metrics_service.py` — MetricsService pattern (cache, connection_port, channel registry)
- `backend/src/modules/analytics/application/dto/adoption_dto.py` — AdoptionDetailDTO (header KPIs, health bar, offer cards, bottlenecks)
- `backend/src/modules/analytics/application/dto/expansion_dto.py` — ExpansionDetailDTO (3 groups, churn, MRR)
- `backend/src/modules/analytics/application/dto/sales_dto.py` — SalesDetailDTO (most comprehensive: offer cards, tiers, dual currency)
- `backend/src/modules/analytics/application/services/channel_registry.py` — STAGE_CHANNEL_MAP (has "referral" stub — add evangelization entries)

### CRM Data Sources
- `backend/src/modules/crm/infrastructure/models/customer_model.py` — CustomerProfileModel: lifecycle_stage, lifetime_value, is_inactive, first_conversion_at
- `backend/src/modules/crm/domain/enums.py` — LifecycleStage enum (EVANGELIST already defined)
- `backend/src/modules/crm/application/services/lifecycle_service.py` — handle_sale_completed, handle_churn_event (add evangelist promotion logic)
- `backend/src/modules/crm/infrastructure/models/sale_model.py` — SaleModel: stage, amount, customer_id, offer_id, source (referral attribution source)

### Cross-Module Ports
- `backend/src/modules/analytics/domain/ports/connection_port.py` — ConnectionPort ABC pattern
- `backend/src/modules/analytics/domain/ports/offer_read_port.py` — OfferReadPort ABC (reuse from Phase 8)

### Frontend Components
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/AdoptionDetail.tsx` — Latest detail panel with offer health cards
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/ExpansionDetail.tsx` — Group-based panel with churn
- `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/BottleneckBanner.tsx` — Shared bottleneck component
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/MiniFunnel.tsx` — Reusable mini funnel
- `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/KpiTooltip.tsx` — Tooltip hints
- `frontend/src/features/marketing-studio/hooks/useAdoptionDetail.ts` — Hook pattern (useQuery + Clerk + fetchClient)
- `frontend/src/features/marketing-studio/types/metrics.ts` — StageId (includes EVANGELIZACION), StageSummary
- `frontend/src/features/marketing-studio/api/metrics-api.ts` — API client with mock fallback
- `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` — Mock data (EVANGELIZACION entry exists with hasDetail: false)
- `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` — Stage routing (add EVANGELIZACION case)

### Shopify Integration
- `backend/src/modules/connections/` — Existing Shopify connection with OAuth tokens (reuse for Admin API discount code read)

### Domain Documentation
- `docs/domains/INDEX.md` — Business domain index (anti-hallucination reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MiniFunnelDTO` + `MiniFunnel.tsx`: Reuse for Clientes → Evangelistas conversion
- `BottleneckDTO` + `BottleneckBanner.tsx`: Reuse for low K-Factor and low NPS response rate alerts
- `KpiTooltip.tsx`: Reuse for user-friendly Spanish labels with hints
- `OfferHealthCard.tsx`: Adapt pattern for evangelist cards (similar card-based layout)
- `MetricsCache` with per-stage TTL: evangelization uses 300s default
- `OfferReadPort` + `OfferReadPortImpl`: Reuse for offer-level survey targeting
- `LifecycleStage.EVANGELIST`: Already defined in CRM enums — no migration needed
- Shopify connection OAuth tokens: reuse existing connection for Admin API calls
- Dual currency formatting: carry from Phase 8-9

### Established Patterns
- ETL batch model: extract → stage → transform → official → aggregate → cache (Phase 2)
- 3+2 header KPIs pattern (Phase 9 — primary row + secondary row)
- MiniFunnel at panel top (Phases 5-9)
- Bottleneck banners with severity and context-aware tips (Phases 7-9)
- Cross-module port pattern: ABC in analytics, impl in source module (Phase 2, 8)
- ENABLE_MOCKS fallback in frontend API layer
- React Query with 5-min staleTime for dashboard hooks
- Evangelist card pattern adapted from offer cards (Phases 8-9)

### Integration Points
- `MetricsDashboard.tsx`: Add EVANGELIZACION stage routing (replace PlaceholderDetail)
- `STAGE_SUMMARIES` mock data: Set `hasDetail: true` for EVANGELIZACION
- `metrics.py` router: Register `/metrics/evangelization` endpoint
- `STAGE_CHANNEL_MAP`: Add "evangelization" entries
- `analytics/application/dto/`: Add `evangelization_dto.py`
- `analytics/infrastructure/repositories/`: Add `evangelization_repository.py`
- `crm/infrastructure/models/`: Add `ReferralCodeModel` and `NpsSurveyModel` / `NpsResponseModel`
- `crm/application/services/`: Add evangelist promotion logic to lifecycle_service
- `crm/application/services/`: Add `referral_service.py` (code generation, assignment, Shopify extraction)
- `crm/application/services/`: Add `nps_service.py` (survey creation, response handling, NPS calculation)

</code_context>

<specifics>
## Specific Ideas

- "Ambos, pero adicionalmente el sistema debe tener su propio mecanismo para generar coupon codes para compartir al sales agent" — internal referral code generation, shareable with Sales Agent
- "Todo lead, customer, en 'proveniencia' debe permitir edición para indicar que es referido y quién lo refirió" — CRM profiles need referred_by tracking (deferred: UI editing)
- "La mentalidad es que progresivamente esta app será el único punto de contacto para las ventas" — design for app-as-single-source, multiple referral origins
- "Autogenerado pero con la capacidad de extraer de Shopify. Considera que más tarde puede ser WooCommerce u otra plataforma" — Shopify read now, platform-agnostic model for future
- "Dame un clon de Shopify en este punto" — K-Factor tracking should follow Shopify's proven referral model
- "Lanzar una encuesta de NPS genérica que permita: saber cómo nos va (retroalimentación) y tener 'Palabras de motivación' para usar en web" — NPS dual purpose: feedback + testimonial capture
- "En el CRM poder mapear como nos ha calificado para saber como atenderlo" — NPS score visible on CRM profiles for service differentiation
- "Debe ser algo dinámico y sencillo. Busca alguna startup que haya hecho esto súper bien y copiemos solo esta parte, la esencia" — researcher must find the simplest, most effective NPS/survey implementation and replicate its core
- "Investiga la forma de que podamos crear la encuesta usando los controles que da WhatsApp para encuestas, completamente conversacional sin salir de esa interfaz" — WhatsApp native survey using interactive controls (buttons, lists). Researcher must find startups doing this well
- "Incluir testimonio de alguna forma, sea escrito o por audio" — testimonial capture supports text and audio. Researcher investigates how others have achieved audio testimonials
- Channel-agnostic survey delivery: universal link + WhatsApp conversational as two initial channels, designed so any future channel can be added

</specifics>

<deferred>
## Deferred Ideas

- **Full CRM profile edit for provenance** — editing "referred by" on customer profile page. New CRM editing capability, belongs in its own phase or CRM enhancement milestone
- **Push referral codes TO Shopify** — currently read-only extraction. Writing codes to Shopify via Admin API is future scope
- **WooCommerce coupon extraction** — model is platform-ready but only Shopify implemented in this phase
- **Sales Agent as survey delivery channel** — model supports it, but actual Sales Agent integration is a future milestone (Sales Agent still in construction)
- **Social media mention tracking as UGC** — monitoring IG tags, stories, etc. requires social listening infrastructure
- **Automated survey scheduling** — owner manually triggers for now. Auto-send after X days post-purchase is a future enhancement
- **Revenue trend indicators** — Phase 11 (Frontend Unification & Dashboard Polish)
- **Configurable bottleneck thresholds per tenant** — use researched defaults

</deferred>

---

*Phase: 10-stage-7-evangelizacion*
*Context gathered: 2026-03-16*
