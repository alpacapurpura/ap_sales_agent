# Architecture Research

**Domain:** Multi-provider marketing metrics aggregation (8-stage funnel dashboard)
**Researched:** 2026-03-15
**Confidence:** HIGH — derived primarily from existing codebase inspection, not training data assumptions

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js 14 / Feature-Sliced Design)                         │
│  features/marketing-studio/                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ AttractionD. │  │ CaptureD.    │  │ NutritionD.  │  │ ... +5     │  │
│  │ (exists)     │  │ (build)      │  │ (build)      │  │ panels     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│         └─────────────────┴─────────────────┴────────────────┘         │
│                            TanStack Query hooks                         │
│                            useAttractionDetail / useStageMetrics        │
│                            metricsApi.get*() — fetchClient wrapper      │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ HTTP  X-Tenant-ID + Bearer
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND  analytics module  (FastAPI / DDD)                             │
│  backend/src/modules/analytics/                                         │
│                                                                         │
│  api/metrics.py                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  GET /metrics/attraction  (exists)                               │   │
│  │  GET /metrics/capture     (build)                                │   │
│  │  GET /metrics/nurturing   (build)   ... /opportunity /sales      │   │
│  │  GET /metrics/adoption    (build)   ... /expansion /evangeliz.   │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│  application/services/      ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  MetricsService (orchestrates — one per stage endpoint)          │   │
│  │    ├── resolves active connections via ConnectionPort            │   │
│  │    ├── invokes per-provider ProviderAdapter.fetch_metrics()      │   │
│  │    ├── merges partial results (some providers disconnected)      │   │
│  │    └── maps to stage-specific response DTO                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             │                                           │
│  infrastructure/providers/  ▼     (NEW layer — build here)             │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ MetaAds │ │ GoogleAds│ │GA4DataAPI │ │TikTokAds │ │ Mailerlite  │  │
│  │ Adapter │ │ Adapter  │ │ Adapter   │ │ Adapter  │ │ Adapter     │  │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘ └──────┬──────┘  │
│       │           │             │             │              │          │
│  ┌────┴───────────┴─────────────┴─────────────┴──────────────┴──────┐  │
│  │  ProviderAdapterBase  (ABC — defines fetch_metrics interface)     │  │
│  └────────────────────────────────────────────────────────────────────  │
│                             │                                           │
│  infrastructure/cache/      ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  MetricsCacheRepository  (Redis — TTL-based, per tenant+stage)   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             │                                           │
│  Cross-module reads (read-only, through domain ports):                  │
│  ┌────────────────┐  ┌────────────────────┐  ┌───────────────────────┐  │
│  │  connections   │  │       crm          │  │   sales_agent / offer │  │
│  │  module        │  │  module            │  │   (future sources)    │  │
│  │  ChannelConn   │  │  CustomerProfiles  │  │                       │  │
│  │  Repository    │  │  JourneyEvents     │  │                       │  │
│  └────────────────┘  └────────────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                      │            │
          ┌───────────┘            └──────────────┐
          ▼                                       ▼
┌─────────────────────┐               ┌──────────────────────┐
│  External APIs      │               │  PostgreSQL           │
│  Meta Marketing API │               │  + Redis cache        │
│  Google Ads API     │               │  + Qdrant (future)    │
│  GA4 Data API       │               └──────────────────────┘
│  TikTok Ads API     │
│  YouTube Analytics  │
│  Mailerlite API     │
│  Shopify API        │
└─────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `api/metrics.py` | FastAPI router — one endpoint per funnel stage; injects auth + tenant | `analytics/api/metrics.py` |
| `MetricsService` | Orchestration — resolves connections, calls adapters, merges results, returns DTO | `analytics/application/services/` |
| `ProviderAdapterBase` | ABC defining `fetch_metrics(tenant_id, connection, date_range) -> RawMetrics` | `analytics/infrastructure/providers/base.py` |
| `MetaAdsAdapter` | Calls Meta Marketing API, normalizes to `RawMetrics` | `analytics/infrastructure/providers/meta_ads.py` |
| `GA4DataAdapter` | Calls `analyticsdata v1beta` `runReport()`, normalizes to `RawMetrics` | `analytics/infrastructure/providers/ga4_data.py` |
| `MailerliteAdapter` | Calls Mailerlite API for open_rate / subscriber counts | `analytics/infrastructure/providers/mailerlite.py` |
| `CrmInternalAdapter` | Reads `customer_profiles` + `journey_events` tables directly (no HTTP) | `analytics/infrastructure/providers/crm_internal.py` |
| `MetricsCacheRepository` | Redis TTL cache keyed by `{tenant_id}:{stage}:{date_range}` | `analytics/infrastructure/cache/metrics_cache.py` |
| `ConnectionPort` | Read-only interface to `connections` module — looks up active credentials | `analytics/infrastructure/ports/connection_port.py` |
| Detail panel components | Frontend React components per stage (one file per stage) | `marketing-studio/components/metrics-dashboard/detail-panels/` |
| `useStageMetrics` hook | TanStack Query wrapper — one hook per stage or generic hook parameterized by stage | `marketing-studio/hooks/` |

---

## Recommended Project Structure

```
backend/src/modules/analytics/
├── api/
│   ├── metrics.py                    # All 8 stage endpoints (extend existing)
│   └── dto/
│       ├── attraction_dto.py         # Exists
│       ├── capture_dto.py            # Build
│       ├── nurturing_dto.py          # Build
│       ├── opportunity_dto.py        # Build
│       ├── sales_dto.py              # Build
│       ├── adoption_dto.py           # Build
│       ├── expansion_dto.py          # Build
│       └── evangelization_dto.py    # Build
├── application/
│   ├── dto/
│   │   └── attraction_dto.py         # Exists — move remaining DTOs here too
│   └── services/
│       ├── metrics_service.py        # Extend existing — add stage methods
│       └── crm_lifecycle_service.py  # Build — move_stage() with automated rules
├── domain/
│   └── event.py                      # Exists — extend if needed
└── infrastructure/
    ├── providers/                    # NEW — entire directory
    │   ├── base.py                   # ProviderAdapterBase ABC
    │   ├── meta_ads.py               # MetaAdsAdapter
    │   ├── google_ads.py             # GoogleAdsAdapter
    │   ├── ga4_data.py               # GA4DataAdapter (uses analyticsdata v1beta)
    │   ├── tiktok_ads.py             # TikTokAdsAdapter
    │   ├── youtube_analytics.py      # YouTubeAnalyticsAdapter
    │   ├── mailerlite.py             # MailerliteAdapter
    │   ├── shopify.py                # ShopifyAdapter (test data for now)
    │   └── crm_internal.py           # CrmInternalAdapter (no HTTP — direct repo)
    ├── cache/                        # NEW
    │   └── metrics_cache.py          # Redis TTL repository
    ├── ports/                        # NEW
    │   └── connection_port.py        # Read-only connection lookup interface
    └── engines/
        ├── rfm.py                    # Exists
        └── scoring.py                # Exists

frontend/src/features/marketing-studio/
├── api/
│   ├── metrics-api.ts               # Extend — add get*Detail() per stage
│   └── metrics-mock-data.ts         # Extend — add mock data per stage
├── hooks/
│   ├── useAttractionDetail.ts       # Exists
│   ├── useCaptureDetail.ts          # Build (or generalize to useStageDetail)
│   └── useStageMetrics.ts           # Build — generic hook parameterized by stage
├── components/metrics-dashboard/
│   └── detail-panels/
│       ├── AttractionDetail.tsx     # Exists (validate data)
│       ├── CaptureDetail.tsx        # Build
│       ├── NutritionDetail.tsx      # Build
│       ├── OpportunityDetail.tsx    # Build
│       ├── SalesDetail.tsx          # Build
│       ├── AdoptionDetail.tsx       # Build
│       ├── ExpansionDetail.tsx      # Build
│       └── EvangelizationDetail.tsx # Build
└── types/
    └── metrics.ts                   # Extend per-stage type interfaces
```

---

## Architectural Patterns

### Pattern 1: Provider Adapter (Source-Agnostic Metrics)

**What:** Each external data source implements a common `ProviderAdapterBase` ABC. The `MetricsService` interacts only with the base interface. Adding a new provider (e.g., Sales Agent telemetry) means implementing the ABC — zero changes to service or API layer.

**When to use:** Any time a new external data source is added. The ABC is the contract.

**Trade-offs:** Slight indirection overhead; worth it because the project explicitly states future sources (Sales Agent, landing pages) will plug in.

**Example:**
```python
# analytics/infrastructure/providers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import date

@dataclass
class RawMetrics:
    """Normalized output of any provider fetch. Unused fields default None."""
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    reach: Optional[int] = None
    spend: Optional[float] = None
    leads: Optional[int] = None
    conversions: Optional[int] = None
    revenue: Optional[float] = None
    open_rate: Optional[float] = None
    # Extend as new stages require new fields

class ProviderAdapterBase(ABC):
    @abstractmethod
    async def fetch_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        config: dict,
        date_from: date,
        date_to: date,
    ) -> RawMetrics:
        """Fetch and normalize metrics. Raise ProviderUnavailableError on failure."""
        ...
```

### Pattern 2: Connection Port (Cross-Module Read)

**What:** The `analytics` module must NOT import repositories directly from `connections`. Instead, a `ConnectionPort` in `analytics/infrastructure/ports/` holds a minimal read interface. In practice for a modular monolith this is a thin wrapper around `ChannelConnectionRepository.get_active()` — not an HTTP call. The port boundary makes future extraction to a microservice trivial.

**When to use:** Every time `analytics` needs to know whether a provider is connected and retrieve decrypted credentials.

**Trade-offs:** One extra file vs. direct cross-module import. Acceptable cost for boundary clarity.

**Example:**
```python
# analytics/infrastructure/ports/connection_port.py
from uuid import UUID
from typing import Optional
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)
from src.modules.connections.domain.enums import ChannelType

class ConnectionPort:
    """Read-only view of the connections module for analytics use."""
    def __init__(self, repo: ChannelConnectionRepository):
        self._repo = repo

    def get_credentials(self, tenant_id: UUID, channel_type: ChannelType) -> Optional[dict]:
        conn = self._repo.get_active(tenant_id, channel_type)
        if conn is None:
            return None
        return conn.credentials  # Decrypted by EncryptedJSON transparently
```

### Pattern 3: Partial-Data Merge (Graceful Degradation)

**What:** `MetricsService` calls all relevant providers concurrently (`asyncio.gather`). If a provider returns `None` (not connected) or raises `ProviderUnavailableError`, the service substitutes zeros for numeric fields and sets `connected=False` on the corresponding channel DTO. The frontend already renders `ConnectionBadge` using the `connected` flag — it handles the "not connected" state visually.

**When to use:** Every stage endpoint. Tenants will never have all providers connected simultaneously.

**Trade-offs:** Soft failure hides real errors if not logged. Mitigation: always log the `ProviderUnavailableError` at `WARNING` level with `tenant_id` and `provider` fields via structlog.

**Example:**
```python
# Pseudocode in MetricsService
async def get_attraction_metrics(self, tenant_id: UUID) -> AttractionDetailDTO:
    results = await asyncio.gather(
        self._fetch_safe(MetaAdsAdapter, tenant_id, ChannelType.META_ADS_ACCOUNT),
        self._fetch_safe(GA4DataAdapter, tenant_id, ChannelType.GOOGLE_ANALYTICS),
        self._fetch_safe(TikTokAdsAdapter, tenant_id, ChannelType.TIKTOK_ADS),
        # ...
    )
    # results is list[RawMetrics | None] — merge into DTO
```

### Pattern 4: Redis TTL Cache (Rate-Limit Shield)

**What:** Before calling any provider adapter, `MetricsService` checks Redis for a cached `RawMetrics` blob keyed by `f"{tenant_id}:{stage}:{date_from}:{date_to}"`. On cache miss, it calls providers, stores the result with a TTL, and returns it. TTL values per provider category:

| Provider Category | TTL | Rationale |
|-------------------|-----|-----------|
| Paid ads (Meta, Google, TikTok) | 1 hour | Daily budgets, low refresh needed |
| Organic social / YouTube | 6 hours | Updates once or twice daily |
| GA4 Data API | 1 hour | Reports are sampled; quota is limited |
| Mailerlite | 4 hours | Email stats rarely change intraday |
| Internal CRM (PostgreSQL) | 5 minutes | Near-real-time data expected |
| Internal CRM (journey_events counts) | 5 minutes | Same |

**When to use:** All external provider adapters. Not needed for `CrmInternalAdapter` (PostgreSQL is already fast with indexed queries).

**Trade-offs:** Stale data within TTL window. Acceptable for a dashboard refreshing every 5 minutes via React Query's `staleTime`.

### Pattern 5: CRM Internal Adapter (No HTTP Boundary)

**What:** Metrics for stages 1–7 that come from internal CRM data (`customer_profiles`, `journey_events`, `sales`) bypass the HTTP adapter pattern entirely. `CrmInternalAdapter` takes a SQLAlchemy `Session` and calls the CRM repositories directly. This is correct in a modular monolith — the "adapter" interface is maintained for future extraction, but the implementation uses direct DB access.

**When to use:** Any metric derived from PostgreSQL tables in `crm`, `sales_agent`, or `offer` modules.

**Trade-offs:** Tight coupling to DB schema. Acceptable because these are internal modules owned by the same team.

---

## Data Flow

### External Provider Flow (Stages 0, 2, 3, 4, 6, 7 — partially)

```
[Frontend Detail Panel]
    ↓ useStageMetrics(stage) TanStack Query
[metricsApi.getStageDetail(token)] fetchClient
    ↓ GET /api/v1/analytics/metrics/{stage}  X-Tenant-ID
[FastAPI router handler]
    ↓ MetricsService(db, redis_client)
[MetricsService.get_{stage}_metrics(tenant_id)]
    ↓ Check Redis cache
    ├── HIT  → return cached DTO immediately
    └── MISS → ConnectionPort.get_credentials(tenant_id, ChannelType.*)
                ↓
              [asyncio.gather() — all providers in parallel]
               ├── MetaAdsAdapter.fetch_metrics()  → Meta Marketing API
               ├── GA4DataAdapter.fetch_metrics()  → GA4 Data API (runReport)
               ├── TikTokAdsAdapter.fetch_metrics()→ TikTok Ads API
               └── ... (others return None if not connected)
                ↓
              Merge RawMetrics → stage DTO
              Store in Redis (TTL per provider category)
                ↓
[JSON response]
    ↓
[Frontend: ChannelGroup renders each channel with value + ConnectionBadge]
```

### Internal CRM Flow (Stages 1, 4, 5 — primarily)

```
[Frontend Detail Panel]
    ↓
[GET /api/v1/analytics/metrics/{stage}]
    ↓ MetricsService
[CrmInternalAdapter(db)]
    ├── CustomerRepository.count_by_stage(tenant_id, LifecycleStage.*)
    ├── JourneyEventRepository.get_by_source(tenant_id, channel, date_range)
    └── SaleRepository.aggregate_by_offer_type(tenant_id, date_range)
        ↓
[Stage DTO — no cache needed for sub-5-minute freshness]
    ↓
[JSON response]
```

### CRM Lifecycle Transition Flow (supporting data quality)

```
[Sale completed event OR lead score threshold reached]
    ↓ SaleService / LeadService
[CrmLifecycleService.move_stage(profile_id, new_stage, reason)]
    ├── UPDATE customer_profiles SET lifecycle_stage = ?
    ├── INSERT journey_events (type=STAGE_TRANSITION, metadata={from, to, reason})
    └── Audit trail in place — analytics queries see correct stages immediately
```

---

## Build Order (Phase Dependencies)

The components have hard dependencies that determine implementation order:

```
1. ProviderAdapterBase ABC + RawMetrics dataclass
        (No deps — pure Python, write first)
   ↓
2. ConnectionPort
        (Depends on: ProviderAdapterBase, ChannelConnectionRepository — already exists)
   ↓
3. MetricsCacheRepository (Redis wrapper)
        (Depends on: Redis client already in Docker Compose)
   ↓
4. CrmLifecycleService (move_stage automation)
        (Depends on: CRM repositories — already exist. Must work before CrmInternalAdapter
         returns accurate stage counts)
   ↓
5. CrmInternalAdapter
        (Depends on: ProviderAdapterBase, CRM repos, CrmLifecycleService being wired)
   ↓
6. GA4DataAdapter  (analyticsdata v1beta — runReport)
        (Depends on: ProviderAdapterBase, ConnectionPort for Google credentials
         Note: existing GoogleAnalyticsAdapter only has Admin API. New class needed.)
   ↓
7. MetaAdsAdapter / TikTokAdsAdapter / MailerliteAdapter (parallel work)
        (Depends on: ProviderAdapterBase, ConnectionPort. Existing MetaAdapter in
         connections/ has OAuth/token logic but NO metrics fetch — extend or delegate.)
   ↓
8. MetricsService methods per stage (attraction → evangelization)
        (Depends on: all adapters, ConnectionPort, MetricsCacheRepository)
   ↓
9. API endpoints + response DTOs per stage
        (Depends on: MetricsService methods)
   ↓
10. Frontend detail panel components per stage
        (Depends on: API endpoints returning real data)
```

**Stage 0 (Atracción)** can be validated in step 8 since its endpoint already exists — it just needs the adapters wired in to replace the `value=0` placeholders.

---

## Anti-Patterns

### Anti-Pattern 1: Duplicating Auth/Token Logic in Analytics Module

**What people do:** Implement Meta API calls directly in `analytics/infrastructure/` by copying the OAuth token handling from `connections/`.

**Why it's wrong:** Token refresh, long-lived token exchange, and encrypted credential storage are all owned by `connections`. Duplicating them creates two code paths that drift.

**Do this instead:** `ProviderAdapters` in `analytics/infrastructure/providers/` receive pre-decrypted `credentials: dict` from `ConnectionPort`. They never touch token management — they only call the external API with the token they're given. If token refresh is needed, delegate back to `connections` module services.

### Anti-Pattern 2: Calling External APIs Synchronously in Request Handler

**What people do:** Call `requests.get(meta_api_url)` inside a FastAPI async endpoint, blocking the event loop.

**Why it's wrong:** A single slow Meta API call (p95 ~800ms) blocks all other requests on the same worker thread.

**Do this instead:** Use `httpx.AsyncClient` for all external calls. Use `asyncio.gather()` in `MetricsService` to fan out all provider calls in parallel. The existing `MetaAdapter` already uses `httpx` — follow that pattern.

### Anti-Pattern 3: Hardcoding Channel-to-ChannelType Mapping in Service Layer

**What people do:** Put `_CHANNEL_CONNECTION_MAP: Dict[str, ChannelType]` directly in `metrics_service.py` (this already exists in the current code).

**Why it's wrong:** When a new channel is added, you must find and edit the service file. The mapping belongs in the adapter registry, not the service.

**Do this instead:** Each `ProviderAdapterBase` subclass declares its `CHANNEL_SLUGS: list[str]` and `CHANNEL_TYPE: ChannelType` as class attributes. The `MetricsService` iterates a registry of registered adapters. The existing `_CHANNEL_CONNECTION_MAP` in `metrics_service.py` should be migrated when the adapter layer is built.

### Anti-Pattern 4: Fetching All 8 Stages in One API Call

**What people do:** Build a single `/metrics/all` endpoint that fires all adapters for all stages, then have the frontend show everything at once.

**Why it's wrong:** Some providers are slow (GA4 can take 2–4s). A single endpoint compounds latency. If one provider errors, the whole response fails.

**Do this instead:** One endpoint per stage (`/metrics/attraction`, `/metrics/capture`, etc.). Frontend loads each detail panel independently with its own TanStack Query cache key. Panels that haven't been opened yet don't trigger their API call.

### Anti-Pattern 5: Returning Zero-Value Metrics Without a `connected` Flag

**What people do:** Return `{"impressions": 0}` when a provider is not connected.

**Why it's wrong:** The dashboard becomes meaningless — 0 impressions looks the same as "Meta not connected." The business owner thinks their campaign is dead.

**Do this instead:** Every `ChannelMetricDTO` carries `connected: bool`. The existing `AttractionDetail.tsx` already renders a `ConnectionBadge` when `connected=False`. All new DTOs must include this field. When `connected=False`, the frontend shows "Conectar" not "0."

---

## Integration Points

### External Services

| Service | Integration Pattern | Rate Limit / Quota | Notes |
|---------|---------------------|--------------------|-------|
| Meta Marketing API | `facebook_business` SDK + `httpx` (existing `MetaAdapter`) | 200 calls/hour per ad account | Cache 1h; batch insight requests with `time_range` param |
| GA4 Data API (`analyticsdata v1beta`) | `google-analytics-data` Python client or direct REST | 10 property requests/hour free tier | `runReport()` not implemented yet — critical gap |
| Google Ads API | `google-ads-python` SDK | 15k ops/day | Separate from GA4; needs own `ChannelType.GOOGLE_ADS` |
| TikTok Ads API | `httpx` REST calls | 1000 calls/day per app | Short-term token (24h) — needs refresh logic |
| YouTube Analytics API | Existing `youtube_analytics.py` in connections | 10k queries/day | Already has adapter stub |
| Mailerlite API | Existing `mailerlite.py` in connections marketing_connectors | No published rate limit; be conservative | REST v2 API; subscribers + campaign stats |
| Shopify | Existing `shopify.py` in connections marketing_connectors | 40 req/min per store | Use test data per PROJECT.md constraint |
| Internal CRM | Direct SQLAlchemy — no HTTP | PostgreSQL limits | Indexed `(tenant_id, lifecycle_stage)` needed |
| Redis | `redis.asyncio` client | Local Docker — no limit | TTL keys, JSON-serialized `RawMetrics` |

### Internal Module Boundaries

| Boundary | Communication Pattern | Constraint |
|----------|-----------------------|------------|
| `analytics` → `connections` | `ConnectionPort` wrapping `ChannelConnectionRepository` | analytics must NOT import connections application services — repositories only |
| `analytics` → `crm` | Direct repository imports via `CrmInternalAdapter` | Read-only; no writes to CRM from analytics |
| `analytics` → `offer` | Direct repository read for Stage 4 (Ventas by offer type) | Read `type_offers` table to group sales by Offer Ladder position |
| `analytics` → `sales_agent` | Future — not in this milestone | Will surface via `CrmInternalAdapter` once sales_agent writes `journey_events` |
| `crm` → `analytics` | None — CRM does not call analytics | One-way dependency only |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0–50 tenants (current) | Synchronous Redis cache + async provider calls is sufficient. Single FastAPI worker handles all. |
| 50–500 tenants | Add background refresh job (Celery beat or APScheduler): pre-warm Redis cache for active tenants during off-peak hours. Reduces cold-miss latency for high-traffic tenants. |
| 500+ tenants | Extract provider adapters to a dedicated "data collection" worker pool. Decouple HTTP API (read from cache only) from background data fetch. Consider per-provider rate-limit queues. |

### Scaling Priorities

1. **First bottleneck:** GA4 and Meta API rate limits per tenant, not PostgreSQL. The 1-hour cache TTL is the primary mitigation. If a tenant hits rate limits, the `ProviderUnavailableError` handler returns cached stale data rather than failing.

2. **Second bottleneck:** Cold start latency when cache is empty (first dashboard load after TTL expiry). Mitigation: background pre-warm job that refreshes cache before TTL expires (refresh at 80% of TTL).

---

## Key Architecture Decisions (with rationale)

| Decision | Rationale |
|----------|-----------|
| Providers in `analytics/infrastructure/providers/` not in `connections/` | `connections` owns auth/OAuth. `analytics` owns metrics logic. The providers in analytics receive credentials, call APIs, return normalized `RawMetrics`. Separation is clean. |
| `ProviderAdapterBase` ABC with `RawMetrics` dataclass | Allows future sources (Sales Agent telemetry, landing page pixel events) to plug in without touching service/API layers. Explicitly required by PROJECT.md. |
| One endpoint per funnel stage | Independent loading, independent caching, independent error isolation. Frontend detail panels open on demand — no need to load all 8 stages upfront. |
| Redis TTL cache in `analytics` module | Provider rate limits are the constraint, not DB. Cache is owned by analytics, not shared infra, to avoid TTL policy conflicts with other modules. |
| `CrmInternalAdapter` follows same `ProviderAdapterBase` interface | Uniform interface in `MetricsService`. Future: if CRM becomes a separate service, only the adapter implementation changes — the service layer is untouched. |
| `move_stage()` automation before adapters | CRM lifecycle transitions must work first. All internal metrics (stage counts by lifecycle_stage) depend on accurate stage data. Building adapters before this wastes effort if the underlying counts are wrong. |

---

## Sources

- Codebase inspection: `backend/src/modules/analytics/` — confirmed existing state (attraction endpoint only, value=0 placeholders, MetricsService structure)
- Codebase inspection: `backend/src/modules/connections/infrastructure/channels/meta.py` — confirmed MetaAdapter has OAuth but no metrics fetch
- Codebase inspection: `backend/src/modules/connections/infrastructure/channels/google_analytics.py` — confirmed only Admin API (`analyticsadmin v1beta`), not Data API (`analyticsdata v1beta`)
- Codebase inspection: `backend/src/modules/connections/infrastructure/marketing_connectors/base.py` — confirmed `BaseConnector` ABC exists but is scoped to contact/event sync, not metrics
- Project constraint: `PROJECT.md` line 129 — "Source-agnostic design: Metrics aggregation must use provider/adapter pattern"
- Web search verification: Adapter pattern, Redis TTL caching strategy, and `asyncio.gather` for parallel API calls are well-established patterns — [FastAPI Caching Guide](https://blog.greeden.me/en/2025/09/17/blazing-fast-rock-solid-a-complete-fastapi-caching-guide-redis-http-caching-etag-rate-limiting-and-compression/) — MEDIUM confidence (confirms approach)

---

*Architecture research for: Nicolify Growth Studio — Multi-provider Metrics Aggregation*
*Researched: 2026-03-15*
