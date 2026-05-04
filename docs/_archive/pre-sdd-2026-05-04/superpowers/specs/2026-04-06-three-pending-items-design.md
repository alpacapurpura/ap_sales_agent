# Three Pending Items — Design Spec

**Date:** 2026-04-06
**Status:** Approved
**Scope:** Clerk E2E resilience, Meta token health banner, Ad-level metrics full stack

---

## 1. Clerk E2E Auth Resilience

### Problem
Clerk auth in E2E setup has no retry logic — a single transient failure (network, Clerk API latency) fails the entire suite. No documentation of required env vars.

### Solution

**File: `frontend/e2e/setup/clerk.setup.ts`**
- Wrap `clerk.signIn()` in a retry helper: 3 attempts, exponential backoff (2s → 4s → 8s)
- Log each attempt with context (attempt number, error message)
- Keep existing 60s timeout + 1 retry at Playwright level as outer safety net

**File: `frontend/.env.e2e.example`**
- Document all E2E environment variables with descriptions:
  - `E2E_CLERK_USER_EMAIL` — Test user email
  - `E2E_CLERK_USER_USERNAME` — Test user username
  - `E2E_CLERK_USER_PASSWORD` — Test user password
  - `E2E_TENANT_ID` — Tenant ID for test isolation
  - `CLERK_SECRET_KEY` — Clerk backend secret
  - `CLERK_TESTING_TOKEN` — Generated dynamically in CI
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk frontend key

### Out of scope
- Monthly credential health workflow (YAGNI)
- Fallback auth methods
- New tests (this IS test infrastructure)

---

## 2. Meta Token Health + Proactive Banner

### Problem
When the Meta access token dies (revoked, expired beyond refresh window), the ETL silently returns 0 metrics. The user has no visibility into connection health until they notice missing data.

### Solution

#### Backend

**New endpoint:** `GET /api/v1/connections/{channel_slug}/health`

**File: `backend/src/modules/connections/api/health.py`** (new)
- Router mounted in connections module
- Receives `tenant_id` from `X-Tenant-ID` header
- Calls `ConnectionService.check_health(tenant_id, channel_slug)`

**File: `backend/src/modules/connections/application/services/connection_service.py`** (extend)
- New method `check_health(tenant_id, channel_slug) -> ConnectionHealthDTO`
- Logic:
  1. Fetch connection by `channel_slug` + `tenant_id`
  2. If not found → `not_connected`
  3. If no `expires_at` in credentials → `healthy` (token without expiry)
  4. If `expires_at > now + 7 days` → `healthy`
  5. If `now < expires_at <= now + 7 days` → `expiring_soon`
  6. If `expires_at <= now` → `expired`

**Response DTO:** `ConnectionHealthResponse`
```python
class ConnectionHealthResponse(BaseModel):
    status: Literal["healthy", "expiring_soon", "expired", "not_connected"]
    channel_slug: str
    expires_at: datetime | None = None
    message: str  # Human-readable Spanish message
```

Messages:
- `healthy`: "Conexión activa"
- `expiring_soon`: "Tu conexión con Meta expira pronto. Reconecta para evitar interrupciones."
- `expired`: "Tu conexión con Meta expiró. Reconecta para reactivar la sincronización de datos."
- `not_connected`: "Meta no está conectado. Conecta tu cuenta para ver métricas."

#### Frontend

**New hook:** `features/analytics/hooks/use-connection-health.ts`
- `useConnectionHealth(channelSlug: string)` — React Query hook
- Calls `GET /api/v1/connections/{channelSlug}/health`
- `staleTime: 5 * 60 * 1000` (5 min cache)

**New component:** `features/analytics/components/connection-health-banner.tsx`
- Renders based on status:
  - `healthy` → nothing (no banner)
  - `expiring_soon` → yellow warning banner with "Reconectar" link to `/connections`
  - `expired` → red error banner with "Reconectar" link
  - `not_connected` → blue info banner with "Conectar" link
- Uses Shadcn Alert component
- Placed at top of Meta Ads dashboard layout (both sidebar and fullpage views)
- Reusable for any channel (receives `channelSlug` prop)

### Testing
- **Backend:** `test_connection_health_service.py` — unit tests for each status scenario
- **Backend:** `test_connection_health_endpoint.py` — API tests with response model validation
- **Frontend:** `connection-health-banner.test.tsx` — render tests per status

---

## 3. Ad-Level Metrics Full Stack

### Problem
The Creativos tab in the Meta Ads dashboard shows ad gallery + video retention, but has no per-ad performance metrics (ROAS, CPA, CTR). The mockup (`docs/mockups/meta-ads-dashboard-complete.html`) promises this to users.

### Solution

#### 3A. Backend ETL — Ad-Level Extraction

**File: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`** (extend)

New method `_extract_meta_ads_by_ad()`:
- Calls Meta Graph API: `GET /act_{ad_account_id}/insights`
  - `level=ad`
  - `fields=ad_id,ad_name,impressions,clicks,spend,actions,cost_per_action_type,purchase_roas,ctr,cpc,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p100_watched_actions`
  - `time_range={"since":"YYYY-MM-DD","until":"YYYY-MM-DD"}`
  - `limit=500`
- Parses response into `ExtractedMetric` objects with `ad_id` populated
- Handles pagination (Meta returns max 500 per page)

Wire into `extract_metrics_period()`:
- Add call after existing campaign extraction
- Follows same pattern as `_extract_meta_ads_campaigns()`

#### 3B. Backend API — Ad Performance Endpoints

**File: `backend/src/modules/analytics/api/ad_performance.py`** (new)

**Endpoint 1:** `GET /api/v1/analytics/campaigns/ads/performance`
- Query params: `channel_slug`, `period` (7d/30d/90d), `limit` (default 10)
- Returns top ads sorted by spend (descending)
- Response model:

```python
class AdPerformanceItem(BaseModel):
    ad_id: str
    ad_name: str
    campaign_name: str
    campaign_external_id: str
    format_type: str  # "video" | "carousel" | "image" | "unknown"
    thumbnail_url: str | None = None
    spend: float
    impressions: int
    clicks: int
    conversions: int
    roas: float | None = None
    cpa: float | None = None
    ctr: float | None = None
    cpc: float | None = None
    performance_tag: str  # "top_performer" | "average" | "underperformer"

class AdPerformanceResponse(BaseModel):
    ads: list[AdPerformanceItem]
    period: str
    total_ads: int
```

**Endpoint 2:** `GET /api/v1/analytics/campaigns/ads/format-comparison`
- Query params: `channel_slug`, `period`
- Aggregates metrics by format type
- Response model:

```python
class FormatComparisonItem(BaseModel):
    format_type: str  # "video" | "carousel" | "image"
    emoji: str  # "🎬" | "🖼" | "📷"
    ad_count: int
    avg_ctr: float
    avg_cpa: float | None = None
    avg_roas: float | None = None
    total_spend: float
    performance_score: float  # 0-100 normalized

class FormatComparisonResponse(BaseModel):
    formats: list[FormatComparisonItem]
    period: str
```

**File: `backend/src/modules/analytics/application/services/ad_performance_service.py`** (new)
- `get_top_ads(tenant_id, channel_slug, period, limit)` — queries `official_metrics` WHERE `ad_id IS NOT NULL`, aggregates by ad_id
- `get_format_comparison(tenant_id, channel_slug, period)` — aggregates by format_type derived from ad metadata
- Uses existing `CampaignService` patterns for query structure

#### 3C. Frontend — Creativos Tab Matching Mockup

**File: `frontend/src/features/analytics/components/meta-ads/CreativosTab.tsx`** (rewrite)

Sections (matching mockup exactly):

1. **Top Anuncios por Rendimiento** — 3-column grid of ad cards
   - Each card: thumbnail placeholder, ad name, campaign + ad set, 3 KPIs (ROAS, Ventas, CPA), performance badge, format badge
   - Color coding: emerald for top, amber for average, red for underperformer
   - Border highlight for worst performer (red border)

2. **Rendimiento por Formato** + **Retención de Video** — 2-column layout
   - Left: format comparison bars (Video, Carrusel, Imagen) with CTR/CPA/ROAS per format
   - Right: video retention funnel (already exists — keep as-is)

3. **Video KPIs** — 4-column grid
   - Video Views, Vistas 30s+, Completados (with completion rate), Duración promedio
   - Already partially implemented — enhance with real data

**New hooks:**
- `use-ad-performance.ts` — `useAdPerformance(channelSlug, period, limit)`
- `use-format-comparison.ts` — `useFormatComparison(channelSlug, period)`

### Testing
- **Backend ETL:** `test_meta_provider_ad_level.py` — mock Graph API responses, verify ad_id populated
- **Backend API:** `test_ad_performance_service.py` — unit tests for aggregation logic
- **Backend API:** `test_ad_performance_endpoint.py` — API tests with response validation
- **Frontend:** `creativos-tab.test.tsx` — render tests with mock data

---

## Data Distribution (from mockup design notes)

| Data | Sidebar | Resumen | Campañas | Creativos | Audiencia | Costos |
|------|---------|---------|----------|-----------|-----------|--------|
| Ad performance (per-ad KPIs) | — | — | — | **NEW** | — | — |
| Format comparison | — | — | — | **NEW** | — | — |
| Video retention | — | — | — | exists | — | — |
| Video KPIs | — | — | — | enhance | — | — |
| Connection health banner | — | all tabs | — | — | — | — |

## Dependencies
- Items 1, 2, 3 are independent — can be implemented in parallel
- Item 3B depends on 3A (need data before API)
- Item 3C depends on 3B (need API before UI)
- Item 2 frontend depends on 2 backend

## Reference
- Mockup: `docs/mockups/meta-ads-dashboard-complete.html` (tab Creativos)
- Existing creatives endpoint: `GET /api/v1/analytics/campaigns/creatives`
- Meta provider: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`
- Campaign service pattern: `backend/src/modules/analytics/application/services/campaign_service.py`
