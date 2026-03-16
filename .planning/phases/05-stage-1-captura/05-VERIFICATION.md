---
phase: 05-stage-1-captura
verified: 2026-03-15T12:00:00Z
status: passed
score: 9/9 must-haves verified
gaps: []
resolved_gaps:
  - truth: "Lead counts are tenant-isolated and accurate to the selected date range"
    status: resolved
    reason: "Fixed in cfabae7 — added CustomerProfileModel.is_inactive == False filter to count_leads_by_source WHERE clause"
human_verification:
  - test: "Visual panel render — click CAPTURA stage card"
    expected: "Panel opens showing TOTAL LEADS / CONVERSION / COSTO POR LEAD KPIs, MiniFunnel arrow (Visitantes -> Leads = X%), Infraestructura Web group with landing-form + mailerlite channels, Agente AI Conversacional group with ig-dm / fb-messenger / tiktok-dm / whatsapp-inbound channels, each AI Agent row showing 'de X conversaciones' secondary line. Unconfigured costs render '---' with 'Configurar costo' link."
    why_human: "Component routing and layout require browser verification; TypeScript compiles clean but visual correctness and layout cannot be confirmed programmatically."
---

# Phase 05: Stage 1 Captura — Verification Report

**Phase Goal:** Build Stage 1 (Captura) detail panel with real metrics from CRM + cost configuration
**Verified:** 2026-03-15T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /metrics/capture returns lead counts grouped by web_infrastructure and ai_agent | VERIFIED | `@router.get("/capture", response_model=CaptureDetailDTO)` in `metrics.py:64`; `get_capture_metrics` in `metrics_service.py:392` uses `_CAPTURE_GROUP_MAP` with form/email->web_infrastructure, messaging->ai_agent |
| 2 | LeadCapturedEvent is emitted when ChatOrchestrator creates a new profile with extracted contact info | VERIFIED | `chat.py:259` unpacks `customer, was_created = identity_service.get_or_create_customer(...)`; `chat.py:269-271` emits `LeadCapturedEvent.create(...)` inside `if was_created` guard |
| 3 | Business owner can configure monthly costs per channel from Growth Studio settings | VERIFIED | `ChannelCostSettingModel` in `channel_cost_model.py` with tenant_id, channel_slug, cost_type, monthly_amount columns; Alembic migration `f5a6b7c8d9e0` creates `channel_cost_settings` table |
| 4 | CAL is calculated as total configured costs divided by total leads | VERIFIED | `CaptureCostService.calculate_cal(total_costs, total_leads)` in `capture_cost_service.py:84-92`; returns `None` for zero-leads guard; called from `metrics_service.py` |
| 5 | Lead counts are tenant-isolated and accurate to the selected date range | VERIFIED | tenant_id, date range, and `is_inactive == False` filters present (fixed in cfabae7) |
| 6 | Clicking CAPTURA stage card opens the CaptureDetail panel instead of PlaceholderDetail | VERIFIED | `MetricsDashboard.tsx:41-43`: `activeStage === 'CAPTURA' ? <CaptureDetail /> : <PlaceholderDetail .../>` |
| 7 | CaptureDetail shows mini funnel arrow: Visitantes (N) -> Leads (N) = X% | VERIFIED | `MiniFunnel.tsx` (32 lines) renders ArrowRight between source/target values with `conversionRate.toFixed(1)%` in text-primary; `CaptureDetail.tsx:65` passes `data.miniFunnel` |
| 8 | CaptureDetail shows two collapsible groups: Infraestructura Web and Agente AI Conversacional | VERIFIED | `CaptureDetail.tsx:68-81` renders `<ChannelGroup title="Infraestructura Web" groupType="web_infrastructure" ...>` and `<ChannelGroup title="Agente AI Conversacional" groupType="ai_agent" ...>` |
| 9 | Panel header shows 3 KPIs: TOTAL LEADS, CONVERSION, COSTO POR LEAD | VERIFIED | `CaptureDetail.tsx:47-62` renders three labeled `<div>` blocks with the exact uppercase text strings |

**Score: 9/9 truths verified**

---

## Required Artifacts

### Plan 01 (Backend)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/src/modules/analytics/application/dto/capture_dto.py` | CaptureDetailDTO, CaptureHeaderKpisDTO, MiniFunnelDTO | VERIFIED | All three classes present; imports TrafficGroupDTO/AvailableChannelsDTO from attraction_dto (no duplication) |
| `backend/src/modules/analytics/infrastructure/models/channel_cost_model.py` | ChannelCostSettingModel for per-tenant cost configuration | VERIFIED | Class present with all required columns; UniqueConstraint on (tenant_id, channel_slug, cost_type) |
| `backend/src/modules/analytics/infrastructure/repositories/capture_repository.py` | CRM-based lead count aggregation by lead_source | PARTIAL | SQLAlchemy 2.0 select() syntax used; tenant_id and date range filters present; group_by lead_source correct; missing `is_inactive == False` exclusion |
| `backend/src/modules/analytics/application/services/capture_cost_service.py` | Cost calculation, CAL computation, agency proration | VERIFIED | get_channel_costs, get_total_stage0_spend, calculate_cal, get_prorated_agency_costs all implemented with real DB queries |
| `backend/src/modules/crm/domain/events.py` | LeadCapturedEvent domain event | VERIFIED | `class LeadCapturedEvent(DomainEvent)` at line 96; `CHANNEL_TYPE_TO_CAPTURE_SLUG` dict at line 86 with instagram/facebook/tiktok/whatsapp keys |

### Plan 02 (Frontend)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/features/marketing-studio/components/metrics-dashboard/detail-panels/CaptureDetail.tsx` | Capture detail panel component (min 40 lines) | VERIFIED | 93 lines; full implementation with loading/error states, KPIs, MiniFunnel, two ChannelGroups |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/MiniFunnel.tsx` | Cross-stage conversion arrow component (min 15 lines) | VERIFIED | 32 lines; ArrowRight icon, locale-formatted numbers, conversion rate in text-primary |
| `frontend/src/features/marketing-studio/components/metrics-dashboard/channel-widgets/CostLink.tsx` | Configurar costo inline link (min 8 lines) | VERIFIED | 19 lines; renders "---" and "Configurar costo" anchor with text-primary hover:underline |
| `frontend/src/features/marketing-studio/hooks/useCaptureDetail.ts` | TanStack Query hook for capture data (min 10 lines) | VERIFIED | 18 lines; queryKey ['capture-detail'], staleTime 5 min, calls metricsApi.getCaptureDetail(token) |

---

## Key Link Verification

### Plan 01

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `analytics/api/metrics.py` | `MetricsService.get_capture_metrics` | GET /metrics/capture endpoint | WIRED | `metrics.py:64-77`: decorator + service call confirmed |
| `sales_agent/application/orchestrator/chat.py` | `EventBus.publish(LeadCapturedEvent)` | EventBus after profile creation | WIRED | `chat.py:258-278`: unpacks `was_created`, emits inside `if was_created` guard |
| `analytics/infrastructure/repositories/capture_repository.py` | `CustomerProfileModel.lead_source` | SQLAlchemy group_by query | WIRED | `capture_repository.py:51`: `.group_by(CustomerProfileModel.lead_source)` |
| `crm/application/event_handlers.py` | `EventBus.subscribe('lead_captured')` | register_event_handlers() at app startup | WIRED | `event_handlers.py:84`: `EventBus.subscribe("lead_captured", handle_lead_captured_event)` |

### Plan 02

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `MetricsDashboard.tsx` | CaptureDetail component | `activeStage === 'CAPTURA'` conditional render | WIRED | `MetricsDashboard.tsx:41-43` confirms routing |
| `hooks/useCaptureDetail.ts` | `/api/v1/analytics/metrics/capture` | `metricsApi.getCaptureDetail(token)` | WIRED | `useCaptureDetail.ts:14` calls `metricsApi.getCaptureDetail`; `metrics-api.ts:107` fetches correct URL |
| `api/metrics-api.ts` | backend GET /metrics/capture | fetchClient with snake_case to camelCase mapping | WIRED | `metrics-api.ts:101-114`: `getCaptureDetail` method with `mapCaptureResponse` mapper |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CAP-01 | Plan 02 | Detail panel showing Web Infrastructure and AI Agent lead groups | SATISFIED | `CaptureDetail.tsx` renders both ChannelGroup components with correct group types and channel breakdowns |
| CAP-02 | Plan 01 | Backend endpoint `/metrics/capture` aggregating customer_profiles by source channel | SATISFIED | `metrics.py:64` endpoint; `capture_repository.py:29-54` count_leads_by_source with group_by lead_source |
| CAP-03 | Plan 01 | AI Agent leads tracked by extraction events where agent obtained email/phone | SATISFIED | `chat.py:258-278` emits LeadCapturedEvent only on new profile creation with extracted contact info |
| CAP-04 | Plan 01 | Cost tracking per capture channel — Manychat licensing, LLM, WhatsApp, Mailerlite | SATISFIED | `ChannelCostSettingModel` + `CaptureCostService.get_channel_costs` supports per-channel cost types |
| CAP-05 | Plan 01 | Cost of Acquisition per Lead = Total Stage 0 investment / Total Stage 1 leads | SATISFIED | `CaptureCostService.calculate_cal()` implements the formula; called from `MetricsService.get_capture_metrics` |

All 5 requirement IDs from plan frontmatter accounted for. No orphaned requirements detected.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `capture_repository.py` | 40-54 | Missing `is_inactive == False` filter in `count_leads_by_source` | Warning | Inflates lead counts when tenants have deactivated profiles; does not crash but produces inaccurate metric values |
| `capture_repository.py` | 72 | `# TODO: Add session tracking to JourneyEventModel for more accurate counts.` | Info | Known limitation; conversation count uses distinct profile_id approximation. Documented in SUMMARY.md decisions. |

No blocking anti-patterns. The is_inactive gap is a data accuracy issue, not a crash or stub.

---

## Human Verification Required

### 1. CaptureDetail Panel Visual Render

**Test:** Start `docker compose up -d`, navigate to Growth Studio dashboard, click the CAPTURA stage card.
**Expected:** Panel opens (not PlaceholderDetail). Shows "Ultima actualizacion" timestamp, three header KPIs (TOTAL LEADS / CONVERSION / COSTO POR LEAD), MiniFunnel arrow "Visitantes (N) -> Leads (N) = X%", "Infraestructura Web" group with landing-form and mailerlite rows, "Agente AI Conversacional" group with ig-dm / fb-messenger / tiktok-dm / whatsapp-inbound rows. Each AI Agent row shows "de X conversaciones" in small muted text below the lead count.
**Why human:** Component routing wiring is verified programmatically, but visual layout, collapsible behavior, and correct mock data rendering require a browser.

### 2. CostLink Renders for Zero-Cost Channels

**Test:** In the panel (mock data has non-zero costs), temporarily set `costPerLead: null` in MOCK_CAPTURE_DETAIL and refresh. Or configure a channel with cost=0 against the real backend.
**Expected:** Cost cell shows "---" with a "Configurar costo" link beneath it in primary color.
**Why human:** `ChannelRow.tsx:182-184` has the CostLink logic but the condition (`m.value === 0 && channel.connected`) needs visual confirmation against real data.

---

## Gaps Summary

One gap was found: the `count_leads_by_source` method in `CaptureMetricsRepository` does not exclude deactivated profiles. `CustomerProfileModel` uses `is_inactive: Boolean` for soft deactivation (not `deleted_at` — that column does not exist on the model). The plan's acceptance criteria referenced `deleted_at.is_(None)` which was based on an incorrect assumption about the model schema. The fix is a single WHERE clause addition: `CustomerProfileModel.is_inactive == False`.

This is a data accuracy issue rather than a functional breakage — the endpoint works, the panel renders, costs calculate — but inflated lead counts would result in incorrect CAL values and misleading conversion rates for tenants with deactivated profiles.

All other truths are fully verified. Backend endpoint is wired end-to-end. Frontend panel is wired with correct routing, type-safe API layer, and complete component tree.

---

_Verified: 2026-03-15T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
