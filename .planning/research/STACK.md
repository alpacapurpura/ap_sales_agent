# Stack Research

**Domain:** Marketing analytics funnel dashboard — multi-provider API aggregation
**Researched:** 2026-03-15
**Confidence:** HIGH (core Python libraries verified via PyPI official pages; frontend recommendations verified via current ecosystem surveys)

---

## Context: What We Are Adding

This is a subsequent milestone on an existing FastAPI + Next.js 14 + PostgreSQL + Redis platform. The additions are:

1. **Backend data-pull layer** — Python services that call Meta, Google Ads, GA4, TikTok, YouTube Analytics, Mailerlite, and Shopify APIs and persist normalized metrics into PostgreSQL.
2. **Aggregation layer** — Per-tenant metrics aggregation in the `analytics` module following a provider/adapter pattern.
3. **Frontend columnar dashboard** — 8 stage panels showing real metrics, replacing mock/placeholder data using existing @visx libraries.

All existing infrastructure (auth, OAuth tokens, connection storage, Redis, PostgreSQL) is reused. This stack document covers **only the new additions**.

---

## Recommended Stack

### Core Backend — API Clients (New Additions)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `google-analytics-data` | `0.20.0` | GA4 Data API — `run_report()` for sessions, events, traffic sources | Dedicated GA4 reporting client (separate from `google-api-python-client`). Uses `BetaAnalyticsDataClient` which is the correct class for `analyticsdata v1beta`. The existing `google-api-python-client` only covers Admin API (property discovery), not data retrieval. |
| `google-ads` | `29.2.0` | Google Ads API — campaign spend, impressions, clicks, conversions | Official Google gRPC-based client. Supports GAQL (Google Ads Query Language). Handles OAuth refresh automatically. The `googleads` package (PyPI) is the old AdWords SDK — do not confuse them. |
| `facebook-business` | `25.0.0` | Meta Marketing API — ad account insights, reach, spend, CPM | **Already in `requirements.txt`**. This IS the correct SDK (`facebook-python-business-sdk`). Version 25.0.0 aligns with Graph API v22/Marketing API v22. Use `AdsInsights` object with async job pattern for heavy queries. |
| `google-api-python-client` | `2.189.0` | YouTube Analytics API v2 — `reports().query()` for channel views, watch time, subscribers | **Already in `requirements.txt`**. No separate package needed. Use `build('youtubeAnalytics', 'v2', credentials=creds)` then `service.reports().query(...)`. |
| `mailerlite` | `>=1.0.0` (official) | MailerLite API — subscriber counts, campaign open/click rates, automation triggers | Official SDK (`pip install mailerlite`) maintained by MailerLite team. Current connection module uses direct HTTP — replace with official SDK for cleaner error handling. Uses API key auth stored in `ChannelConnectionModel.credentials`. |

### Core Backend — Scheduling & Aggregation (New Additions)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `APScheduler` | `3.11.2` | Scheduled background polling of external APIs (hourly/daily jobs) | Production-stable v3.x (v4 is alpha, not production-ready as of March 2026). Use `AsyncIOScheduler` to stay in FastAPI's event loop. Avoid FastAPI `BackgroundTasks` for recurring jobs — they only fire once per request. |
| `httpx` | `>=0.27.0` | Async HTTP for Shopify Admin API and any provider without a Python SDK | **Already in ecosystem via FastAPI**. Use `httpx.AsyncClient` for Shopify REST calls. Shopify has a Python SDK (`ShopifyAPI`) but it's sync-only; httpx is the better fit for the async backend. |

### Frontend — Visualization (Additions to Existing @visx)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `recharts` | `^2.15.0` | Bar charts and sparklines for per-channel metric columns inside stage detail panels | The project already uses `@visx` for the Sankey/funnel diagram. For the **columnar metrics inside panels** (numbers with comparison bars, sparklines), Recharts provides faster implementation. Recharts is React-idiomatic, SSR-safe with `ResponsiveContainer`, and produces clean SVG. Visx requires wiring D3 scales manually for each chart — unnecessary overhead for simple column charts. |

> Note: Do NOT add Recharts if all charts can be represented as pure numbers + Tailwind progress bars. For simple "number + percentage change" displays, a Tailwind `<div>` is faster and lighter than any charting library. Only add Recharts when trend lines or comparative bars are genuinely needed.

---

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `redis` | `5.0.1` | Cache per-tenant metrics with TTL to avoid hammering external APIs | **Already installed.** Use `redis://redis:6379/1` (separate DB from session cache). Pattern: `metrics:{tenant_id}:{stage}:{date_range}` key, TTL 300s (5 min) for near-real-time feel. |
| `pydantic` | `v2 (>=2.10.0)` | `MetricDTO` schemas — validate and normalize cross-provider data shapes | **Already installed.** Define `NormalizedMetric(provider, metric_name, value, currency, date_range)` as the canonical internal DTO. Each provider adapter maps to this. |
| `structlog` | `>=24.1.0` | Log provider fetch errors, rate limit warnings, async job status | **Already installed.** Bind `tenant_id` and `provider` to each log call for traceability. |

---

## Installation (New Packages Only)

```bash
# Inside visionarias_brain_dev container
docker exec -it visionarias_brain_dev bash

pip install google-analytics-data==0.20.0
pip install google-ads==29.2.0
pip install APScheduler==3.11.2
pip install mailerlite
```

Add to `backend/requirements.txt`:
```
google-analytics-data==0.20.0
google-ads==29.2.0
APScheduler==3.11.2
mailerlite>=1.0.0
```

Frontend (only if columnar charts need trend lines):
```bash
docker exec -it visionarias_client_dev bash
npm install recharts@^2.15.0
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `google-analytics-data` | `google-api-python-client` with `analyticsdata` discovery | Discovery API for GA4 data is undocumented and unofficial. `google-analytics-data` is the dedicated, supported client with typed request/response objects. |
| `google-ads` | `googleads` (PyPI, old AdWords SDK) | `googleads` is the deprecated AdWords era library. Google Ads API requires the new `google-ads` package with GAQL support. Different package, same confusion. |
| `APScheduler 3.11.2` | Celery + Redis broker | Celery adds a broker, worker process, and significant operational complexity. APScheduler runs inside the existing FastAPI process with `AsyncIOScheduler` — no extra infra needed. For 8 provider polling jobs, Celery is overkill. |
| `APScheduler 3.11.2` | FastAPI `BackgroundTasks` | `BackgroundTasks` fires once per HTTP request — cannot schedule recurring hourly/daily jobs. Not suitable for polling. |
| `APScheduler 3.11.2` | APScheduler 4.x alpha | v4 is alpha (latest: 4.0.0a6, April 2025). API is unstable. Production systems should stay on 3.11.2. |
| `httpx` for Shopify | `ShopifyAPI` official Python SDK | `ShopifyAPI` is synchronous-only. The async backend requires `httpx.AsyncClient` to avoid blocking the event loop. |
| `recharts` (if needed) | `@visx` for column charts | `@visx` is already used for the Sankey. For simple bar charts inside panels, the low-level D3 primitives in visx require 3x the implementation effort vs Recharts for identical output. Reuse visx only if the chart shares layout with the Sankey. |
| `mailerlite` official SDK | Direct HTTP (`httpx`) | Current implementation uses direct HTTP. Official SDK adds proper rate-limit handling, typed responses, and campaign statistics methods. Swap is low-effort. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `google-analytics-data` Admin API (`analyticsadmin v1alpha`) for reporting | Admin API is for property management (list properties, create streams). It does NOT return session/event/traffic data. The project already calls this — it's the wrong API for metrics. | `BetaAnalyticsDataClient.run_report()` from `google-analytics-data` package |
| `googleads` (PyPI, old package) | This is the deprecated AdWords SDK. The endpoint it calls (`adwords.google.com`) was shut down. Completely different from Google Ads API. | `google-ads` package, GAQL queries |
| TikTok official SDK (`tiktok-business-api-sdk` on GitHub) | Poorly maintained, massive generated codebase, sparse documentation, no PyPI release with proper versioning. The minimal `TikTok-Business-API` package (PyPI 1.9, MIT) is lighter and sufficient. | `TikTok-Business-API==1.9` or direct `httpx` calls to `business-api.tiktok.com/open_api/v1.3/reports/integrated/get` |
| Meta Insights synchronous API for heavy queries | Synchronous Insights requests with many breakdowns or long date ranges will time out. Meta officially recommends async job pattern for reporting. | `AdsInsights` with `async_=True`, poll `AsyncJob.get_result()` |
| `APScheduler 4.x` | Alpha software — API changes expected, not production-ready as of March 2026 | `APScheduler 3.11.2` |
| Celery for metrics polling | Requires separate broker + worker processes. Disproportionate complexity for 8 recurring polling jobs that have zero user-facing latency requirement. | `APScheduler 3.11.2` with `AsyncIOScheduler` |
| D3.js directly in React | Bypasses React's rendering lifecycle, causes DOM conflicts. Both visx and Recharts are already the correct abstraction layer. | `recharts` or existing `@visx` |

---

## Data Normalization Pattern

This is the critical architectural decision. Every provider returns different field names, currencies, date formats, and attribution windows. The backend must normalize before storing.

### Canonical DTO (Pydantic v2)

```python
# backend/src/modules/analytics/domain/metrics.py
from decimal import Decimal
from datetime import date
from pydantic import BaseModel
from enum import StrEnum

class MetricProvider(StrEnum):
    META = "meta"
    GOOGLE_ADS = "google_ads"
    GA4 = "ga4"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    MAILERLITE = "mailerlite"
    SHOPIFY = "shopify"
    INTERNAL_CRM = "internal_crm"

class NormalizedMetric(BaseModel):
    tenant_id: str
    provider: MetricProvider
    channel: str           # e.g. "meta-paid", "google-organic", "email"
    metric_name: str       # e.g. "impressions", "sessions", "leads", "revenue"
    value: Decimal
    currency: str | None   # ISO 4217, None for dimensionless metrics
    date_from: date
    date_to: date
    fetched_at: datetime
```

### Provider Adapter Interface

```python
# backend/src/modules/analytics/infrastructure/providers/base.py
from abc import ABC, abstractmethod

class MetricsProviderAdapter(ABC):
    @abstractmethod
    async def fetch(
        self,
        tenant_id: str,
        date_from: date,
        date_to: date,
    ) -> list[NormalizedMetric]:
        """Fetch and normalize metrics for a given tenant and date range."""
        ...
```

Each provider (`MetaMetricsAdapter`, `GA4MetricsAdapter`, `GoogleAdsMetricsAdapter`, etc.) implements this interface. The aggregation service calls all adapters and aggregates by `channel` and `metric_name`. New providers (Sales Agent, generated landing pages) plug in without touching aggregation logic.

---

## Provider-Specific Implementation Notes

### GA4 (`google-analytics-data`)

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric
)

# credentials = OAuth2Credentials from ChannelConnectionModel
client = BetaAnalyticsDataClient(credentials=credentials)
request = RunReportRequest(
    property=f"properties/{property_id}",
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
    dimensions=[Dimension(name="sessionDefaultChannelGroup")],
    metrics=[Metric(name="sessions"), Metric(name="newUsers")],
)
response = client.run_report(request)
```

OAuth token for GA4 is stored in `ChannelConnectionModel` under the Google connection. The `connections` module manages refresh — do not duplicate token logic in analytics.

### Meta (`facebook-business` 25.0.0)

Use async job pattern for all Insights queries to avoid timeouts:

```python
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi

FacebookAdsApi.init(access_token=token)
account = AdAccount(f"act_{account_id}")
async_job = account.get_insights_async(
    params={
        "level": "account",
        "fields": ["impressions", "reach", "spend", "clicks"],
        "date_preset": "last_7d",
        "async": True,
    }
)
# Poll async_job.get_result() with exponential backoff
```

Rate limits: 200 calls/hour per token at standard access. Cache results in Redis with 5-min TTL to stay within limits.

### Google Ads (`google-ads` 29.2.0)

Uses GAQL (Google Ads Query Language), not REST JSON:

```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_dict(config_dict)
service = client.get_service("GoogleAdsService")
query = """
    SELECT campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros
    FROM campaign
    WHERE segments.date DURING LAST_7_DAYS
"""
response = service.search_stream(customer_id=customer_id, query=query)
```

`cost_micros` must be divided by 1,000,000 to get real currency value — a common normalization trap.

### TikTok (`TikTok-Business-API` 1.9 or direct httpx)

The official TikTok SDK is heavy and unmaintained. For this milestone, direct `httpx` calls are simpler and more reliable:

```python
# Endpoint: GET https://business-api.tiktok.com/open_api/v1.3/reports/integrated/get
params = {
    "advertiser_id": advertiser_id,
    "report_type": "BASIC",
    "dimensions": ["stat_time_day"],
    "metrics": ["spend", "impressions", "clicks", "reach"],
    "start_date": date_from.isoformat(),
    "end_date": date_to.isoformat(),
}
headers = {"Access-Token": access_token}
```

Access token stored in `ChannelConnectionModel.credentials`. TikTok uses OAuth 2.0 authorization code flow — token refresh handled by `connections` module.

### Shopify (direct `httpx`, test data for now)

Per PROJECT.md constraint: "Shopify connection fix — use test data for Shopify-dependent metrics." Build the adapter with httpx but gate it behind a feature flag:

```python
# Use mock data until Shopify connection is fixed
if settings.ENABLE_MOCKS or not shopify_connection:
    return mock_shopify_metrics()
```

Shopify checkout events: `checkouts/create`, `checkouts/update` webhooks already route to `/api/v1/connections/shopify`. Parse stored webhook payloads from the database rather than polling the API.

---

## Scheduling Strategy

Use `APScheduler 3.11.2` `AsyncIOScheduler`, initialized at FastAPI startup:

```python
# backend/src/modules/analytics/application/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        func=refresh_all_tenant_metrics,
        trigger=IntervalTrigger(minutes=30),
        id="metrics_refresh",
        replace_existing=True,
    )
    scheduler.start()
```

**TTL strategy for Redis cache:**
- Paid ad metrics (Meta, Google Ads, TikTok): 30-minute TTL (refresh every 30 min)
- GA4 sessions/organic: 60-minute TTL (data is not real-time anyway)
- CRM-internal metrics (lifecycle stages, captures): 5-minute TTL (near-real-time)
- Mailerlite campaign stats: 6-hour TTL (campaign stats update infrequently)

Cache key pattern: `metrics:{tenant_id}:{provider}:{stage}:{YYYY-MM-DD}`

---

## Stack Patterns by Variant

**If a provider has no Python SDK (e.g. TikTok, Shopify):**
- Use `httpx.AsyncClient` with stored OAuth credentials from `ChannelConnectionModel`
- Implement retry with exponential backoff (3 attempts, 1s/2s/4s delays)
- Store raw response in a `provider_raw_cache` Redis key for debugging

**If a provider returns async jobs (Meta Insights):**
- Submit job, store job ID in Redis: `meta_job:{tenant_id}:{date_range}`
- APScheduler polls every 2 minutes until completion
- On completion, normalize and persist to PostgreSQL

**If a tenant has no connection for a provider:**
- Return `MetricStatus.NO_CONNECTION` rather than an error
- Frontend renders "Configurar" badge (already implemented in AttractionDetail.tsx)
- Never block the full stage render because one provider is disconnected

**If ENABLE_MOCKS=true (dev environment):**
- All adapters return mock data — no external API calls
- Mock data is shaped identically to `NormalizedMetric` DTO
- Existing mock system in growth studio frontend is preserved

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `google-analytics-data==0.20.0` | `google-auth>=2.15.0`, `grpcio>=1.49.1` | Uses gRPC transport. Ensure gRPC is available in Docker. |
| `google-ads==29.2.0` | Python `>=3.9,<3.15`, `protobuf>=4.21.0` | Also uses gRPC. Compatible with existing `google-api-python-client`. |
| `facebook-business==25.0.0` | Python 2/3 compatible, no conflicting deps | Version 25 deprecates Advantage+ ASC/AAC creation endpoints. For reading Insights, no breaking change. |
| `APScheduler==3.11.2` | FastAPI `>=0.100`, Python `>=3.8` | Use `AsyncIOScheduler`, NOT `BackgroundScheduler` (which spawns a thread). |
| `mailerlite` (official) | Python `>=3.7`, `requests` or `httpx` | No conflict with existing stack. |
| `recharts@^2.15.0` | React `>=18`, Next.js `>=14` (App Router) | Must use `"use client"` directive — Recharts is not SSR-safe by default. Wrap in dynamic import if needed. |

---

## Sources

- [PyPI: google-analytics-data](https://pypi.org/project/google-analytics-data/) — version 0.20.0 confirmed (HIGH confidence)
- [PyPI: google-ads](https://pypi.org/project/google-ads/) — version 29.2.0 confirmed (HIGH confidence)
- [PyPI: facebook-business](https://pypi.org/project/facebook-business/) — version 25.0.0 confirmed (HIGH confidence)
- [PyPI: APScheduler](https://pypi.org/project/APScheduler/) — version 3.11.2 stable, v4 alpha confirmed (HIGH confidence)
- [TikTok Business API SDK — GitHub](https://github.com/tiktok/tiktok-business-api-sdk) — SDK structure reviewed (MEDIUM confidence)
- [PyPI: TikTok-Business-API](https://pypi.org/project/TikTok-Business-API/) — version 1.9 confirmed (MEDIUM confidence, minor third-party package)
- [MailerLite Python SDK — GitHub](https://github.com/mailerlite/mailerlite-python) — official SDK confirmed (HIGH confidence)
- [Meta Marketing API Rate Limiting](https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/) — rate limit behavior, async job pattern (HIGH confidence)
- [Google Ads API Python client docs](https://developers.google.com/google-ads/api/docs/client-libs/python) — GAQL pattern confirmed (HIGH confidence)
- [YouTube Analytics API reference](https://developers.google.com/youtube/analytics/reference/reports/query) — `reports().query()` method confirmed (HIGH confidence)
- [LogRocket: Best React chart libraries 2025](https://blog.logrocket.com/best-react-chart-libraries-2025/) — Recharts vs visx positioning (MEDIUM confidence)
- [Redis.io: FastAPI caching](https://redis.io/learn/develop/python/fastapi) — TTL caching pattern with Redis (HIGH confidence)

---

*Stack research for: Growth Studio 8-Stage Metrics Dashboard — multi-provider API aggregation*
*Researched: 2026-03-15*
