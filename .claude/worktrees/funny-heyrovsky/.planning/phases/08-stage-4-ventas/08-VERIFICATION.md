---
phase: 08-stage-4-ventas
verified: 2026-03-16T15:45:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Open MetricsDashboard in browser, click VENTAS stage, verify SalesDetail panel renders with mock data"
    expected: "Panel shows REVENUE TOTAL KPI, NUEVOS CLIENTES, CAC, MiniFunnel (Oportunidades->Ventas), Adquisicion group with tier accordions, and Expansion group"
    why_human: "Visual rendering, accordion behavior, dual-currency display formatting cannot be verified statically"
  - test: "Click a tier accordion (e.g. Low Ticket) to expand and see OfferCards"
    expected: "Cards show offer name, sales count, revenue with dual currency, source breakdown, and (for subscription offers) new/renewal split"
    why_human: "Interactive component behavior requires runtime testing"
  - test: "With no offers configured (empty Offer Studio), verify the empty state appears"
    expected: "Panel shows 'Sin ofertas configuradas' heading with 'Ir a Offer Studio' link"
    why_human: "Requires specific data state to trigger the branch; not exercised by mock data"
---

# Phase 8: Stage 4 Ventas Verification Report

**Phase Goal:** Business owner sees total revenue broken down by offer type, with clear separation of new vs recurring money
**Verified:** 2026-03-16T15:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Sales detail panel breaks down revenue by Offer Ladder position using type_offers from Offer Studio | VERIFIED | `SalesDetail.tsx` renders `RevenueGroupData.tiers` with `TierGroup`+`OfferCard` per offer; `offer_port.get_offers_by_tenant()` enriches `sales_dto.py` with `value_level`, `public_name` from `ProductModel` |
| 2 | `/metrics/sales` returns revenue with CONVERSION (new money) vs EXPANSION (recurring) split | VERIFIED | `backend/src/modules/analytics/api/metrics.py` line 119: `@router.get("/sales", response_model=SalesDetailDTO)`; `metrics_service.py` maps `CONVERSION->adquisicion`, `EXPANSION->expansion` groups |
| 3 | Subscription revenue is separated into new subscriptions vs renewals | VERIFIED | `get_subscription_labels()` in `sales_dto.py`; `metrics_service.py` assigns `new_subs`/`renewals` based on `stage_key == "adquisicion"` vs `"expansion"` for recurring pricing types |
| 4 | Offer Studio type_offers data accessed via shared service/read-only projection, not direct ORM join | VERIFIED | `OfferReadPort` ABC in `analytics/domain/ports.py`; `OfferReadPortImpl` in `offer/application/services/`; no `from src.modules.offer.domain` import anywhere in analytics module |
| 5 | CAC = total investment from Stages 0-3 / total new CONVERSION customers | VERIFIED | `stage_cost_service.py` line 146: `get_total_funnel_investment()` sums ad spend + manual costs + retargeting; `metrics_service.py` line 1288 divides by `new_customers` (CONVERSION count) |

**Score:** 5/5 truths verified

---

### Required Artifacts

#### Plan 08-00 (Wave 0 Test Stubs)

| Artifact | Status | Lines | Key Content |
|----------|--------|-------|-------------|
| `backend/tests/modules/analytics/test_offer_read_port.py` | VERIFIED | 68 | `test_offer_read_port_is_abstract`, `test_offer_read_dto_has_required_fields`, `test_impl_implements_port`, `test_impl_does_not_import_offer_domain` |
| `backend/tests/modules/analytics/test_sales_dto.py` | VERIFIED | 97 | `test_low_ticket_mapping`, `test_tier_mapping`, `TestSalesDetailDTOStructure`, `TestCurrencyConversion` (15 test stubs) |
| `backend/tests/modules/analytics/test_sales_endpoint.py` | VERIFIED | 79 | `test_sales_route_exists`, `test_metrics_service_has_sales_method`, `test_metrics_service_accepts_offer_port`, repository tests |
| `backend/tests/modules/analytics/test_subscription_split.py` | VERIFIED | 52 | `test_subscription_type_labels`, `test_payment_plan_labels`, `test_one_time_returns_none`, `test_recurring_service_labels` (5 stubs) |
| `backend/tests/modules/analytics/test_cac_calculation.py` | VERIFIED | 73 | `test_get_total_funnel_investment_exists`, `TestSalesMetricsRepository`, `TestBottleneckThresholds` (6 stubs) |
| `backend/tests/modules/analytics/conftest.py` | VERIFIED | 43 | `sample_offer_id` and `sample_customer_id` fixtures added (lines 34, 40) |

Total test stubs: 42 across 5 files.

#### Plan 08-01 (Backend Production Code)

| Artifact | Status | Lines | Key Content |
|----------|--------|-------|-------------|
| `backend/src/modules/analytics/domain/ports.py` | VERIFIED | 76 | `class OfferReadPort(ABC)` with `get_offers_by_tenant`, `get_offer_by_id`; `class OfferReadDTO(BaseModel)` with all required fields |
| `backend/src/modules/offer/application/services/offer_read_port_impl.py` | VERIFIED | 66 | `class OfferReadPortImpl(OfferReadPort)`; `select(ProductModel)` (SQLAlchemy 2.0); imports from `analytics.domain.ports` only (no offer.domain cross-boundary) |
| `backend/src/modules/analytics/application/dto/sales_dto.py` | VERIFIED | 208 | All 5 DTOs (`OfferSaleDTO`, `TierGroupDTO`, `RevenueGroupDTO`, `SalesHeaderKpisDTO`, `SalesDetailDTO`); `VALUE_LEVEL_TO_TIER` (7 entries); `get_tier_for_value_level`; `DEFAULT_EXCHANGE_RATES`; `SUBSCRIPTION_LABELS`; `LOW_CONVERSION_THRESHOLDS`; `HIGH_CAC_THRESHOLDS` |
| `backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py` | VERIFIED | 103 | `class SalesMetricsRepository` with `get_sales_summary`, `get_total_conversion_customers`, `get_total_sql_count`; uses `SaleStatus.COMPLETED`, `SaleStage.CONVERSION` enums; SQLAlchemy 2.0 `select()` throughout |
| `backend/src/modules/analytics/application/services/stage_cost_service.py` | VERIFIED | contains `get_total_funnel_investment` at line 146 returning `tuple[float, bool]` |
| `backend/src/modules/analytics/application/services/metrics_service.py` | VERIFIED | 53932 bytes | `get_sales_metrics` at line 1078; `offer_port` param at line 151; full 10-step pipeline (cache, aggregation, enrichment, grouping, tier mapping, subscription split, KPIs, mini funnel, bottleneck detection, cache write) |
| `backend/src/modules/analytics/api/metrics.py` | VERIFIED | 200 | `@router.get("/sales", response_model=SalesDetailDTO)` at line 119; `OfferReadPortImpl(db)` instantiated and passed as `offer_port=` at lines 132-134 |

#### Plan 08-02 (Frontend)

| Artifact | Status | Lines | Key Content |
|----------|--------|-------|-------------|
| `frontend/src/features/marketing-studio/types/metrics.ts` | VERIFIED | `GroupType` includes `'adquisicion'\|'expansion'`; `OfferSaleData`, `TierGroupData`, `RevenueGroupData`, `SalesHeaderKpis`, `SalesBottleneck`, `SalesDetail` all defined |
| `frontend/src/features/marketing-studio/api/metrics-api.ts` | VERIFIED | `mapSalesResponse` at line 126; `getSalesDetail` at line 285 calling `/api/v1/analytics/metrics/sales` with Bearer auth and mock fallback |
| `frontend/src/features/marketing-studio/api/metrics-mock-data.ts` | VERIFIED | `MOCK_SALES_DETAIL` at line 528; VENTAS stage has `hasDetail: true` (line 48) |
| `frontend/src/features/marketing-studio/hooks/useSalesDetail.ts` | VERIFIED | 19 | `useSalesDetail()` via `useAuth` + `metricsApi.getSalesDetail(token)` pattern; `queryKey: ['sales-detail']`; `staleTime: 5 min` |
| `frontend/.../channel-widgets/OfferCard.tsx` | VERIFIED | 114 | Tier indicator (`$`/`$$`/`$$$`/`RefreshCw`), dual currency via `Intl.NumberFormat`, source breakdown, conditional subscription split line |
| `frontend/.../channel-widgets/TierGroup.tsx` | VERIFIED | 41 | `Accordion`/`AccordionContent`/`AccordionTrigger` from shadcn; `defaultValue` set when `offers.some(o => o.salesCount > 0)` |
| `frontend/.../channel-widgets/RevenueGroupHeader.tsx` | VERIFIED | 63 | `groupLabel`, `subtitle`, `totalRevenue`, `revenuePercentage`, `customerCount` all rendered |
| `frontend/.../detail-panels/SalesDetail.tsx` | VERIFIED | 189 | `useSalesDetail()` hook; Header KPIs (`REVENUE TOTAL`, `NUEVOS CLIENTES`, `CAC` with incomplete indicator); `MiniFunnel`; `SalesBottleneckBanner`; `RevenueSection` with `TierGroup`; empty state "Sin ofertas configuradas" + "Ir a Offer Studio"; loading skeleton; error state |

---

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `api/metrics.py` | `services/metrics_service.py` | `service.get_sales_metrics()` | WIRED | Line 138: `return await service.get_sales_metrics(user.tenant_id, start_date, now)` |
| `services/metrics_service.py` | `domain/ports.py` | `OfferReadPort` dependency injection | WIRED | Line 151: `offer_port: Optional[OfferReadPort] = None`; line 1117: `self.offer_port.get_offers_by_tenant(tenant_id)` |
| `offer/application/services/offer_read_port_impl.py` | `offer/infrastructure/models/product_model.py` | SQLAlchemy query | WIRED | Line 29: `stmt = select(ProductModel).where(...)` |
| `MetricsDashboard.tsx` | `detail-panels/SalesDetail.tsx` | VENTAS case routing | WIRED | Line 50-51: `activeStage === 'VENTAS' ? <SalesDetail />` |
| `detail-panels/SalesDetail.tsx` | `hooks/useSalesDetail.ts` | `useSalesDetail` hook | WIRED | Line 5: `import { useSalesDetail }...`; line 93: `const { data, isLoading, error } = useSalesDetail()` |
| `hooks/useSalesDetail.ts` | `api/metrics-api.ts` | `getSalesDetail` API call | WIRED | Line 14: `return metricsApi.getSalesDetail(token)` |
| `api/metrics-api.ts` | `backend GET /metrics/sales` | `fetchClient` with Bearer auth | WIRED | Line 291: `fetchClient(\`${API_URL}/api/v1/analytics/metrics/sales\`, {headers: {Authorization: ...}})` |

All 7 key links verified as WIRED.

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VEN-01 | 08-00, 08-01, 08-02 | Detail panel showing sales broken down by Offer Ladder position (core offer, subscription, upsell/expansion) using `type_offers` from Offer Studio | SATISFIED | `TierGroup`/`OfferCard` components render per-offer revenue; `VALUE_LEVEL_TO_TIER` maps 7 `value_level` values to 4 display tiers; offer data sourced from Offer Studio via `OfferReadPortImpl` |
| VEN-02 | 08-00, 08-01, 08-02 | Backend endpoint `/metrics/sales` with revenue tracking — new money (CONVERSION) vs recurring (EXPANSION) split | SATISFIED | `GET /metrics/sales` registered at `metrics.py:119`; `SalesDetailDTO` contains `adquisicion` (CONVERSION) and `expansion` (EXPANSION) `RevenueGroupDTO` fields |
| VEN-03 | 08-00, 08-01, 08-02 | Subscription revenue separated into new subscriptions vs renewals | SATISFIED | `get_subscription_labels()` in `sales_dto.py`; `OfferSaleDTO` has `new_subscriptions`/`renewals` fields; `metrics_service.py` assigns split by stage key; `OfferCard.tsx` renders conditional subscription split line |
| VEN-04 | 08-00, 08-01 | Cross-module read of Offer Studio `type_offers` via shared service or read-only projection (not direct ORM join) | SATISFIED | `OfferReadPort` ABC in `analytics/domain/ports.py`; `OfferReadPortImpl` in `offer/application/services/` queries `ProductModel` only; zero `from src.modules.offer.domain` imports in analytics module |
| VEN-05 | 08-00, 08-01 | CAC calculated as Total investment (Stages 0-3) / Total new customers (Stage 4 CONVERSION) | SATISFIED | `StageCostService.get_total_funnel_investment()` sums Stages 0-3 costs; `metrics_service.py:1288`: `cac = round(total_investment / new_customers, 2)`; `SalesHeaderKpisDTO.cac_incomplete` signals missing cost data |

All 5 requirements satisfied. No orphaned requirements found (REQUIREMENTS.md table confirms all 5 mapped to Phase 8 with status "Complete").

---

### Anti-Patterns Found

None detected across all phase files. No TODOs, FIXMEs, placeholders, empty return stubs, or legacy `db.query()` calls found.

---

### Human Verification Required

#### 1. SalesDetail Panel Visual Rendering

**Test:** Open the Growth Studio metrics dashboard in the browser. Select the VENTAS stage button.
**Expected:** Panel renders with REVENUE TOTAL KPI (dual currency), NUEVOS CLIENTES count, CAC field (with asterisk and note if `cacIncomplete=true`), MiniFunnel (Oportunidades -> Ventas with %, Adquisicion and Expansion revenue group sections with tier accordions.
**Why human:** Visual layout correctness, typography, color contrast (emerald-600 for revenue), and responsive layout cannot be verified statically.

#### 2. Tier Accordion Interaction

**Test:** Click a tier label (e.g., "LOW TICKET") in the Adquisicion section to expand/collapse.
**Expected:** Accordion expands to show OfferCards. Each card displays: tier indicator symbol ($/$$/$$$/refresh icon), offer name, "X ventas" count, formatted revenue with dual currency, source breakdown ("SHOPIFY: 60 | MANUAL: 15"), and conditional subscription split line.
**Why human:** Accordion interactivity, defaultOpen behavior (opens tiers with sales > 0), and dynamic content rendering require runtime testing.

#### 3. Empty State Rendering

**Test:** Configure a tenant with no products in Offer Studio, then navigate to the VENTAS stage.
**Expected:** Panel shows "Sin ofertas configuradas" heading with descriptive text and a clickable "Ir a Offer Studio" link pointing to `/offer-studio`.
**Why human:** Requires specific data state (empty offer catalog) to trigger; mock data always has offers configured.

---

### Gaps Summary

No gaps. All 5 phase must-haves are verified at all three levels (exists, substantive, wired).

The implementation is complete:
- Wave 0: 42 pytest stubs covering all 5 VEN requirements
- Backend: Full data pipeline from `SalesMetricsRepository` aggregation through `OfferReadPort` enrichment, tier grouping, subscription split, CAC calculation, bottleneck detection, to `GET /metrics/sales` endpoint returning `SalesDetailDTO`
- Frontend: Complete component hierarchy (`OfferCard` -> `TierGroup` -> `RevenueGroupHeader` -> `SalesDetail`) with React Query hook, API client, mock data, and `MetricsDashboard` VENTAS routing

DDD boundary is intact: `analytics` module never imports from `offer.domain` directly. All offer data flows through `OfferReadPort` ABC.

---

_Verified: 2026-03-16T15:45:00Z_
_Verifier: Claude (gsd-verifier)_
