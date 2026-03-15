# Phase 2: Provider Adapter Infrastructure - Research

**Researched:** 2026-03-15
**Domain:** ETL pipeline, task queue, provider adapters, Redis caching, DDD cross-module ports
**Confidence:** HIGH

## Summary

Phase 2 builds the foundational data pipeline: provider adapters extract metrics from external APIs (Meta, Google, TikTok, etc.) into PostgreSQL via a nightly ETL process, with Redis caching for dashboard query optimization. The architecture is a batch-only model where the dashboard reads exclusively from local DB tables, never from live APIs.

The core infrastructure involves: (1) an ABC-based adapter system for provider extraction, (2) a ConnectionPort abstraction for cross-module credential access following DDD boundaries, (3) ARQ as the async task queue for scheduling and executing extraction jobs, (4) a two-layer staging/official table design with pre-computed aggregations, (5) Redis cache with active invalidation, and (6) a cost type enum system with stage-channel mapping.

**Primary recommendation:** Use ARQ (v0.27.0) as the task queue -- it is native asyncio, uses Redis (already in the stack), supports cron scheduling and retry with backoff, and requires minimal configuration. Build the ETL pipeline as plain Python with SQLAlchemy -- no external ETL framework needed for this scale.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Batch-only model**: No real-time API calls from dashboard. All data comes from a nightly ETL pipeline that extracts, transforms, and loads metrics into PostgreSQL
- **Data up to yesterday**: The dashboard always shows data through the previous day. No same-day data
- **Two-layer storage**: Staging tables (hybrid: core columns + JSONB extras) per provider -> internal transformation -> Official tables with specific typed columns
- **Staging retention**: 30 days (already transformed). Official tables: permanent
- **Pipeline is atomic**: Extract -> Load staging -> Transform -> Load official all in the same job run
- **Initial load**: Last 7 days, triggered immediately when a user connects a provider (not waiting for next cron). Must support expanding historical window in future milestones
- **Pre-calculated aggregations**: daily, weekly (configurable cutoff day per tenant + week-to-date), monthly, last 30 days -- all computed by the pipeline
- **Trazability for Action Triggers**: Store enough detail in staging (campaign IDs, ad set IDs, ad creative IDs) so future Action Triggers can modify campaigns without re-querying provider APIs
- **Source-agnostic, metric-agnostic, stage-agnostic design**: Adapters don't know about funnel stages. They extract and normalize data. The service layer maps data to stages
- **Drill-down: 2 levels**: Stage -> Channel -> Campaign/detail. Each metric carries enough metadata for a second detailed API call
- **Explicit units in DTO**: Every metric includes `unit` field ('currency', 'percentage', 'count', 'ratio'). Frontend formats automatically based on unit
- **Original provider currency**: No conversion. Each metric carries `currency` field ('USD', 'COP', etc.). Frontend displays as-is
- **Date range as parameter from the start**: Adapters accept start_date/end_date even though date picker is out of scope. Default: last 30 days
- **ConnectionPort (ABC) in analytics module**: Analytics defines the interface, connections implements it. Analytics never imports from connections directly. Pure DDD boundary
- **Port always returns valid token**: ConnectionPort handles token refresh transparently. Analytics never deals with token expiry
- **Specific exception on failure**: `ConnectionRevokedException` or `TokenRefreshFailed` when token can't be refreshed
- **ConnectionPort persists refreshed tokens**: When a token is refreshed during extraction, the port (in connections module) saves the new token
- **Two methods on port**: `get_credentials(tenant_id, channel_type)` + `list_active_connections(tenant_id)`
- **Redis cache role**: Cache for aggregated dashboard queries (not for raw metrics). Primary data store is PostgreSQL
- **Redis fallback**: Silent fallback to PostgreSQL when Redis is down. Redis is purely an optimization
- **Redis invalidation**: Active invalidation when ETL completes for a tenant (delete that tenant's cache keys). Also has TTL as safety net
- **Redis TTL**: Short (5 min) for dashboard queries
- **4 cost types**: NEUTRAL, EXPENSE, INVESTMENT (ad spend with expected ROI), REVENUE
- **Cost type variable by funnel stage**: Same channel can be EXPENSE in Attraction but REVENUE in Sales
- **Cost type mapping in code**: Dict/config file mapping `(channel, stage) -> cost_type`. Changes require deploy but are versioned in git
- **Seed fixtures in DB**: Script `seed_metrics.py` fills staging + official tables with realistic test data. `docker exec seed`. Frontend always talks to real API backed by seeded DB
- **ENABLE_MOCKS deprecated**: With ETL model, frontend mocks are no longer needed. Backend seeds replace them
- **Disconnected channels UX**: Active channels with data shown first. Collapsible "Canales disponibles" section below with relevant-to-stage unconnected channels showing "Configurar" badge
- **Dynamic channel list from backend**: The endpoint returns the channels that exist for that stage+tenant. Frontend renders what it receives
- **Tick-based scheduler**: Evaluates every minute which tenants are due for their 3am local time extraction
- **Timezone per tenant**: Each tenant's extraction runs at 3am in their configured timezone
- **Priority by plan**: Infrastructure for tenant priority (premium tenants extract first). Field on tenant model even if plans don't exist yet
- **Separate containers**: `visionarias_scheduler` (generates jobs) + `visionarias_worker` (processes extraction jobs)
- **Fibonacci backoff**: Failed extractions retried with increasing intervals
- **Accumulated failures**: If a provider/tenant fails, the rest continue. Failed tasks go to a retry queue
- **extraction_runs table**: `(tenant_id, provider, status, started_at, completed_at, error, metrics_count)` plus performance metrics
- **Smart extraction**: Provider-specific rate limit awareness to never get banned
- **Manual retry button**: User can trigger re-extraction of just the failed metric/segment. Cooldown of 15 min per channel
- **Streamlit admin dashboard**: ETL monitoring in existing Streamlit admin
- **Health endpoint**: `GET /health/etl` returns last successful run, pending tenants, active failures
- **Same DB, same encryption**: Worker uses same PostgreSQL connection with EncryptedJSON for credentials
- **Revenue fields encrypted**: Monetary fields encrypted in staging/official tables
- **Tenant isolation**: All queries filter by tenant_id
- **Replace MetricsService**: Refactor to read from official ETL tables instead of ad-hoc journey_events queries
- **Unit tests with mocks**: Each adapter tested with pre-recorded JSON responses
- **E2E pipeline test**: Full flow test using test PostgreSQL + test Redis with mocked adapters

### Claude's Discretion
- ELT library/framework selection (after research)
- Task queue technology (Celery, ARQ, Dramatiq, etc.)
- Adapter registry pattern (explicit dict vs auto-discovery)
- Internal vs external adapter ABC design
- DI container/pattern selection
- Exact Fibonacci vs exponential backoff implementation
- Notification approach for revoked connections
- Staging table schema per provider (which columns are core vs JSONB)
- Official table design (universal vs per-stage)
- Redis cache key structure

### Deferred Ideas (OUT OF SCOPE)
- Real-time WebSocket updates
- Date range picker UI
- Vault/secrets manager
- Integration tests against real APIs
- Action Triggers (campaign modification)
- Admin panel for cost_type configuration

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Provider adapter base class (ABC) in `analytics/infrastructure/providers/` with normalized metric output, so all providers conform to one interface | Adapter ABC design with `extract_metrics()` method, adapter registry pattern, existing `BaseConnector` ABC as reference pattern |
| INFRA-02 | `ConnectionPort` service that retrieves decrypted OAuth credentials from `connections` module without violating DDD boundaries | Port/Adapter pattern in analytics domain, connections module implements it, existing `ChannelConnectionRepository` wraps cleanly |
| INFRA-03 | Redis-based metrics cache in `analytics` with per-provider TTL to respect API rate limits | Redis already in stack (redis:7-alpine), `redis_client` exists in `core/database.py`, 5-min TTL for dashboard queries with active invalidation on ETL completion |
| INFRA-04 | Cost type system (NEUTRAL, EXPENSE, INVESTMENT, REVENUE) applied as a field on every channel metric DTO across all 8 stages | CostType enum in analytics domain, stage-channel mapping dict, ChannelMetricDTO extended with `cost_type` and `unit` fields |
| INFRA-05 | Mock/fallback mechanism consistent across all 8 stages -- disconnected providers show "Configurar" badge, not broken UI | Seed script replaces ENABLE_MOCKS, dynamic channel list from backend, existing `ConnectionBadge` component handles states |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| arq | 0.27.0 | Async task queue for ETL jobs | Native asyncio, uses Redis (already in stack), built-in cron + retry, minimal config. Stable despite maintenance-only status |
| redis | 5.0.1 | Cache + ARQ broker | Already installed and configured in the project |
| sqlalchemy | 2.0.27 | ORM for staging/official tables + models | Already the project standard |
| alembic | >=1.13.1 | DB migrations for new ETL tables | Already the project standard |
| sentry-sdk | latest | Error tracking across API + worker + scheduler | Auto-detects FastAPI integration, minimal setup |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.10.0 | DTOs for metric normalization, adapter output typing | Already installed; use for all data contracts |
| httpx | 0.26.0 | HTTP client for providers without official SDKs | Already installed; use for TikTok, Mailerlite API calls |
| facebook-business | >=22.0,<26.0 | Meta Marketing API extraction | Already installed; use via asyncio.to_thread() |
| google-analytics-data | >=0.20.0 | GA4 Data API extraction | Already installed from Phase 1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ARQ | Celery | Celery is more battle-tested for large scale, but is sync-first (requires bridging for asyncio), heavier (needs separate broker like RabbitMQ or Redis), and much more complex config. Overkill for this use case |
| ARQ | Dramatiq | Good balance of simplicity/reliability, but not natively async. Would need async bridging for the existing FastAPI async codebase |
| Plain Python ETL | Apache Airflow | Airflow is for complex multi-step DAGs with dozens of sources. This project has ~5-8 provider adapters. Airflow adds massive infra overhead (webserver, scheduler, metadata DB). Complete overkill |
| Plain Python ETL | Singer.io (taps/targets) | Good for pre-built connectors, but the project needs custom extraction logic (campaign IDs for Action Triggers, rate limit awareness). Singer abstractions would constrain more than help |

**Installation:**
```bash
pip install arq==0.27.0 sentry-sdk
```

**No external ETL framework needed.** The extraction logic is custom per-provider (Meta SDK, Google SDK, httpx for others). A framework would add abstraction without value at this scale. Plain Python functions called by ARQ jobs are the right pattern.

## Architecture Patterns

### Recommended Project Structure
```
backend/src/modules/analytics/
├── domain/
│   ├── enums.py                    # CostType, MetricUnit, ExtractionStatus enums
│   ├── ports.py                    # ConnectionPort ABC (analytics owns the interface)
│   ├── models.py                   # Domain entities for metrics
│   └── exceptions.py              # ConnectionRevokedException, TokenRefreshFailed
├── infrastructure/
│   ├── providers/
│   │   ├── base.py                 # BaseMetricsProvider ABC
│   │   ├── registry.py            # Provider registry (explicit dict)
│   │   ├── meta_provider.py       # Meta Marketing API adapter
│   │   ├── google_analytics_provider.py  # GA4 Data API adapter
│   │   ├── tiktok_provider.py     # TikTok for Business API adapter
│   │   └── crm_provider.py        # Internal CRM data adapter
│   ├── etl/
│   │   ├── pipeline.py            # Orchestrates extract->stage->transform->official
│   │   ├── transformers.py        # Staging -> official table transformation
│   │   └── aggregations.py        # Pre-computed daily/weekly/monthly aggregations
│   ├── cache/
│   │   └── metrics_cache.py       # Redis cache with fallback to PostgreSQL
│   ├── models/
│   │   ├── staging_metrics_model.py    # Staging table (core cols + JSONB extras)
│   │   ├── official_metrics_model.py   # Official table (typed columns)
│   │   ├── extraction_run_model.py     # extraction_runs tracking table
│   │   └── metric_aggregation_model.py # Pre-computed aggregations
│   └── repositories/
│       ├── staging_repository.py
│       ├── official_metrics_repository.py
│       └── extraction_run_repository.py
├── application/
│   ├── dto/
│   │   ├── channel_metric_dto.py  # Extended DTO with cost_type, unit, currency
│   │   └── extraction_dto.py      # DTOs for extraction status/results
│   ├── services/
│   │   ├── metrics_service.py     # Refactored: reads from official tables
│   │   ├── etl_service.py         # Application-level ETL orchestration
│   │   └── channel_registry.py    # Maps stages to available channels
│   └── cost_type_mapping.py       # (channel, stage) -> CostType config
├── api/
│   ├── metrics.py                 # Existing routes, refactored data source
│   └── etl_admin.py               # Health endpoint, manual retry
└── workers/
    ├── settings.py                # ARQ WorkerSettings
    ├── scheduler.py               # Tick-based scheduler (cron every minute)
    └── tasks.py                   # ETL job functions

backend/src/modules/connections/
├── application/
│   └── services/
│       └── connection_port_impl.py  # Implements analytics.domain.ports.ConnectionPort
```

### Pattern 1: Provider Adapter ABC (BaseMetricsProvider)

**What:** Abstract base class that all provider adapters implement. Source-agnostic, metric-agnostic, stage-agnostic.
**When to use:** Every external or internal data source that provides metrics.

```python
# analytics/infrastructure/providers/base.py
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class ExtractedMetric(BaseModel):
    """Normalized metric output from any provider."""
    provider: str           # "meta", "google_analytics", "tiktok"
    channel_slug: str       # "meta-ads", "google-organic", etc.
    metric_name: str        # "impressions", "clicks", "spend"
    value: float
    unit: str               # "count", "currency", "percentage", "ratio"
    currency: Optional[str] = None  # "USD", "COP" - only for currency units
    date: date
    # Drill-down metadata for Action Triggers
    campaign_id: Optional[str] = None
    ad_set_id: Optional[str] = None
    ad_id: Optional[str] = None
    extra: dict = {}        # Provider-specific data preserved in JSONB

class BaseMetricsProvider(ABC):
    """ABC for all metric providers. Adapters extract and normalize data.
    They know nothing about funnel stages - the service layer maps to stages."""

    @abstractmethod
    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract and normalize metrics for a date range."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier, e.g. 'meta', 'google_analytics'."""
        ...

    @abstractmethod
    def rate_limit_config(self) -> dict:
        """Provider-specific rate limit configuration.
        Returns: {"max_requests_per_second": N, "backoff_factor": N, ...}
        """
        ...
```

### Pattern 2: Explicit Provider Registry

**What:** A simple dict mapping provider names to adapter classes. No auto-discovery magic.
**When to use:** When resolving which adapter to use for a given channel type.

```python
# analytics/infrastructure/providers/registry.py
from typing import Dict, Type
from .base import BaseMetricsProvider
from .meta_provider import MetaMetricsProvider
from .google_analytics_provider import GoogleAnalyticsProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseMetricsProvider]] = {
    "meta": MetaMetricsProvider,
    "google_analytics": GoogleAnalyticsProvider,
    # "tiktok": TikTokMetricsProvider,  # Add as implemented
}

def get_provider(provider_name: str) -> BaseMetricsProvider:
    cls = PROVIDER_REGISTRY.get(provider_name)
    if cls is None:
        raise ValueError(f"Unknown provider: {provider_name}")
    return cls()
```

**Why explicit dict over auto-discovery:** Predictable, debuggable, git-versioned. Adding a provider is one line in the dict + the implementation file. Auto-discovery (via `__subclasses__` or entrypoints) is magical and breaks when imports are missing.

### Pattern 3: ConnectionPort (DDD Cross-Module Port)

**What:** Analytics defines the interface, connections implements it. Zero import coupling.
**When to use:** Every time analytics needs credentials or connection status.

```python
# analytics/domain/ports.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

class ConnectionCredentials(BaseModel):
    channel_type: str
    credentials: dict
    config: dict

class ConnectionPort(ABC):
    """Port defined in analytics domain. Implemented by connections module."""

    @abstractmethod
    async def get_credentials(
        self, tenant_id: UUID, channel_type: str
    ) -> ConnectionCredentials:
        """Returns decrypted credentials. Handles token refresh transparently.
        Raises ConnectionRevokedException if token cannot be refreshed."""
        ...

    @abstractmethod
    async def list_active_connections(
        self, tenant_id: UUID
    ) -> List[ConnectionCredentials]:
        """Returns all active connections for a tenant."""
        ...
```

```python
# connections/application/services/connection_port_impl.py
from src.modules.analytics.domain.ports import ConnectionPort, ConnectionCredentials
from src.modules.analytics.domain.exceptions import ConnectionRevokedException

class ConnectionPortImpl(ConnectionPort):
    """Connections module implements the analytics port."""

    def __init__(self, db: Session):
        self.repo = ChannelConnectionRepository(db)

    async def get_credentials(self, tenant_id, channel_type):
        conn = self.repo.get_active(tenant_id, ChannelType(channel_type))
        if not conn:
            raise ConnectionRevokedException(f"No active {channel_type} for tenant")
        # EncryptedJSON handles decryption transparently
        return ConnectionCredentials(
            channel_type=channel_type,
            credentials=conn.credentials,
            config=conn.config,
        )
```

**DI wiring** (at API/app level):
```python
# In FastAPI dependency or startup
def get_connection_port(db: Session = Depends(get_db)) -> ConnectionPort:
    return ConnectionPortImpl(db)
```

### Pattern 4: ARQ Worker + Scheduler

**What:** Two separate Docker containers -- scheduler generates jobs, worker processes them.
**When to use:** The ETL pipeline execution.

```python
# analytics/workers/settings.py
from arq import cron
from arq.connections import RedisSettings
from .tasks import run_tenant_extraction, run_tick_scheduler

class WorkerSettings:
    functions = [run_tenant_extraction]
    cron_jobs = [
        cron(run_tick_scheduler, minute={0, 1, 2, ...59})  # Every minute
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    on_startup = startup
    on_shutdown = shutdown

async def startup(ctx):
    """Initialize DB session factory and Sentry for worker."""
    ctx["db_factory"] = sessionmaker(...)
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

async def shutdown(ctx):
    pass
```

```python
# analytics/workers/tasks.py
from arq import Retry

async def run_tenant_extraction(ctx, tenant_id: str, provider: str):
    """Extract metrics for one tenant+provider. Atomic pipeline."""
    try:
        # 1. Get credentials via ConnectionPort
        # 2. Extract via provider adapter
        # 3. Load staging
        # 4. Transform to official
        # 5. Compute aggregations
        # 6. Invalidate Redis cache for this tenant
        pass
    except ConnectionRevokedException:
        # Mark channel as failed, don't retry
        raise
    except RateLimitExceeded:
        # Fibonacci backoff: 1, 1, 2, 3, 5, 8, 13...
        fib = [1, 1, 2, 3, 5, 8, 13]
        wait = fib[min(ctx["job_try"] - 1, len(fib) - 1)] * 60
        raise Retry(defer=wait)
```

### Pattern 5: Redis Cache with PostgreSQL Fallback

**What:** Cache aggregated dashboard queries in Redis. Fall back silently to PostgreSQL on cache miss or Redis failure.

```python
# analytics/infrastructure/cache/metrics_cache.py
import json
from typing import Optional
from redis import Redis

class MetricsCache:
    TTL = 300  # 5 minutes

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _key(self, tenant_id: str, stage: str, period: str) -> str:
        return f"metrics:{tenant_id}:{stage}:{period}"

    async def get(self, tenant_id, stage, period) -> Optional[dict]:
        try:
            data = self.redis.get(self._key(tenant_id, stage, period))
            return json.loads(data) if data else None
        except Exception:
            return None  # Silent fallback

    async def set(self, tenant_id, stage, period, data: dict):
        try:
            self.redis.setex(
                self._key(tenant_id, stage, period),
                self.TTL,
                json.dumps(data),
            )
        except Exception:
            pass  # Redis is optimization only

    async def invalidate_tenant(self, tenant_id: str):
        """Active invalidation after ETL completes."""
        try:
            pattern = f"metrics:{tenant_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception:
            pass
```

### Pattern 6: Cost Type System

**What:** Enum + mapping dict that assigns cost types per (channel, stage) pair.

```python
# analytics/domain/enums.py
from enum import Enum

class CostType(str, Enum):
    NEUTRAL = "neutral"
    EXPENSE = "expense"
    INVESTMENT = "investment"
    REVENUE = "revenue"

class MetricUnit(str, Enum):
    COUNT = "count"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    RATIO = "ratio"

class ExtractionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
```

```python
# analytics/application/cost_type_mapping.py
from ..domain.enums import CostType

# (channel_slug, stage_slug) -> CostType
# Same channel can have different cost types in different stages
COST_TYPE_MAP: dict[tuple[str, str], CostType] = {
    # Attraction stage
    ("meta-ads", "attraction"): CostType.INVESTMENT,
    ("google-ads", "attraction"): CostType.INVESTMENT,
    ("ig-organic", "attraction"): CostType.NEUTRAL,
    # Capture stage
    ("manychat", "capture"): CostType.EXPENSE,
    # Sales stage
    ("shopify", "sales"): CostType.REVENUE,
    # ... extend as needed
}

def get_cost_type(channel_slug: str, stage_slug: str) -> CostType | None:
    """Returns cost type for a channel+stage pair.
    Returns None for unmapped pairs (logs warning)."""
    ct = COST_TYPE_MAP.get((channel_slug, stage_slug))
    if ct is None:
        import logging
        logging.warning(f"No cost_type mapping for ({channel_slug}, {stage_slug})")
    return ct
```

### Anti-Patterns to Avoid
- **Direct cross-module imports**: MetricsService currently imports `ChannelConnectionRepository` from connections. This MUST be replaced with the ConnectionPort pattern
- **Sync DB sessions in async workers**: The existing `ChannelConnectionRepository` uses sync Session. Worker tasks must use `asyncio.to_thread()` or async sessions
- **Global Redis client**: The existing `redis_client` singleton in `core/database.py` is fine for the API process. ARQ workers will get their own Redis connection via WorkerSettings
- **Hardcoded channel lists**: The current `MetricsService.get_attraction_metrics()` hardcodes 13 channels. Must be replaced with dynamic registry driven by `list_active_connections()` + channel registry

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task queue | Custom Redis-based job system | ARQ (v0.27.0) | Handles retries, cron, concurrency, job status, dead letter queue. ~700 lines of code, battle-tested |
| Credential encryption | Custom Fernet wrapper | Existing `EncryptedJSON` TypeDecorator | Already handles encrypt/decrypt transparently on read/write. Supports legacy plaintext fallback |
| Rate limit tracking | Custom sliding window counter | Provider-specific `rate_limit_config()` + ARQ retry with backoff | Each provider has different limits. Backoff + configurable delay per provider is sufficient |
| Cache invalidation | Custom pub/sub system | Redis key pattern deletion + TTL safety net | Simple, effective, no additional infrastructure |
| Timezone handling | Manual UTC offset calculation | `zoneinfo` (stdlib) or `pytz` | Timezone math is notoriously complex. Use stdlib `zoneinfo` (Python 3.9+) |
| Fibonacci sequence | Custom generator | Simple lookup list `[1, 1, 2, 3, 5, 8, 13]` | Max 5 retries means max 7 values needed. A list is clearer than a generator |

**Key insight:** The complexity in this phase is in the architecture (adapters, ports, pipeline orchestration) not in any single library. There is no magical ETL framework that solves the custom extraction + staging + transformation + aggregation pipeline. Plain Python with good abstractions is the right approach.

## Common Pitfalls

### Pitfall 1: Sync Session in Async Worker
**What goes wrong:** ARQ worker functions are `async def`. Using the existing sync `Session` from `core/database.py` directly will block the event loop.
**Why it happens:** The existing codebase uses sync SQLAlchemy sessions (`Session` not `AsyncSession`).
**How to avoid:** Wrap all sync DB operations in `asyncio.to_thread()`, or create an `AsyncSession` factory specifically for workers. The `asyncio.to_thread()` pattern is already established from Phase 1 (GA4 adapter).
**Warning signs:** Worker processes appearing to hang, low throughput despite async architecture.

### Pitfall 2: Meta API Rate Limiting / Account Ban
**What goes wrong:** Excessive or rapid API calls trigger rate limits or account suspension.
**Why it happens:** Meta rate limits are per-ad-account, based on active ads. Headers `X-Ad-Account-Usage` and `X-Business-Use-Case` track quota consumption.
**How to avoid:** (1) Monitor rate limit headers on every response. (2) Use `async=true` parameter for large dataset pulls. (3) Schedule extractions during off-peak hours (3am is already good). (4) Implement per-provider delay between requests. (5) Store rate limit headroom in `extraction_runs` table.
**Warning signs:** HTTP 613 or 80004 error codes from Meta API.

### Pitfall 3: GA4 Quota Exhaustion
**What goes wrong:** GA4 Data API has token-based quotas per property per day. Heavy extraction burns through quota.
**Why it happens:** Each `runReport()` call consumes tokens proportional to date range and dimensions requested.
**How to avoid:** (1) Request `returnPropertyQuota: true` in every request to monitor remaining tokens. (2) Minimize date ranges (only extract yesterday's data in daily runs). (3) Batch multiple metrics into single report requests where possible.
**Warning signs:** 429 responses or `quotaExhausted` errors.

### Pitfall 4: Staging Table JSONB Performance
**What goes wrong:** Queries on JSONB `extra` column become slow as data grows.
**Why it happens:** JSONB queries without GIN indexes are full-scan.
**How to avoid:** (1) Keep core/frequent query columns as typed columns, not in JSONB. (2) Add GIN index on `extra` column if queried. (3) The 30-day retention policy on staging mitigates growth. (4) Official tables should have ALL typed columns.
**Warning signs:** Slow staging-to-official transformation queries.

### Pitfall 5: Pipeline Atomicity Failure
**What goes wrong:** Partial data in official tables if pipeline crashes mid-transform.
**Why it happens:** Without transaction management, staging data might load but transform fails.
**How to avoid:** Wrap the entire pipeline (staging load + transform + official load + aggregation) in a single DB transaction. If any step fails, the whole pipeline rolls back. Mark `extraction_run` as FAILED.
**Warning signs:** Mismatched row counts between staging and official tables.

### Pitfall 6: Token Refresh Race Condition
**What goes wrong:** Multiple worker tasks refresh the same OAuth token simultaneously, causing one to fail.
**Why it happens:** If two tenants share a Meta user token (e.g., agency scenario) or if multiple providers use the same Google auth.
**How to avoid:** Use Redis-based distributed lock on credential refresh: `SET credential_refresh:{tenant_id}:{provider} NX EX 30`. If lock exists, wait and read the refreshed token.
**Warning signs:** Intermittent `TokenRefreshFailed` errors that succeed on retry.

## Code Examples

### Staging Table Model
```python
# analytics/infrastructure/models/staging_metrics_model.py
from sqlalchemy import Column, String, Float, Date, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from src.shared.domain.base_entity import Base
from src.shared.infrastructure.database.types import EncryptedJSON
import uuid

class StagingMetricModel(Base):
    __tablename__ = "staging_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)  # "meta", "google_analytics"
    channel_slug = Column(String, nullable=False)           # "meta-ads", "ig-organic"
    metric_name = Column(String, nullable=False)            # "impressions", "clicks"
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)                   # "count", "currency", etc.
    currency = Column(String, nullable=True)                # "USD", "COP"
    metric_date = Column(Date, nullable=False, index=True)
    # Encrypted monetary values
    spend = Column(EncryptedJSON, nullable=True)
    revenue = Column(EncryptedJSON, nullable=True)
    # Drill-down IDs for future Action Triggers
    campaign_id = Column(String, nullable=True)
    ad_set_id = Column(String, nullable=True)
    ad_id = Column(String, nullable=True)
    # Provider-specific extras
    extra = Column(JSONB, default={})
    # Metadata
    extraction_run_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Extraction Run Tracking
```python
# analytics/infrastructure/models/extraction_run_model.py
class ExtractionRunModel(Base):
    __tablename__ = "extraction_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # ExtractionStatus enum
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(String, nullable=True)
    metrics_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    rows_extracted = Column(Integer, default=0)
    rate_limit_headroom = Column(Float, nullable=True)  # % remaining quota
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Docker Compose Services
```yaml
# docker-compose.yml additions
  scheduler:
    image: visionarias_brain_dev:latest
    build: ./backend
    container_name: visionarias_scheduler
    restart: unless-stopped
    command: arq src.modules.analytics.workers.settings.SchedulerSettings
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    networks:
      - internal_net

  worker:
    image: visionarias_brain_dev:latest
    build: ./backend
    container_name: visionarias_worker
    restart: unless-stopped
    command: arq src.modules.analytics.workers.settings.WorkerSettings
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    networks:
      - internal_net
```

### Sentry Initialization
```python
# backend/src/main.py (addition)
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1,  # 10% of transactions for performance
    environment=settings.ENVIRONMENT,  # "dev", "prod"
)
# FastAPI + Starlette integrations are auto-detected
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Real-time API calls on page load | Nightly ETL to local PostgreSQL | This phase | Dashboard reads from DB, not APIs. Eliminates rate limit risks, enables pre-computed aggregations |
| `ENABLE_MOCKS` global toggle | Seed fixtures in DB | This phase | Frontend always talks to real API. Test data is seeded, not mocked |
| Direct cross-module imports | Port/Adapter pattern (DDD) | This phase | Analytics defines ConnectionPort ABC, connections implements it |
| Sync-only SQLAlchemy sessions | Async workers via `asyncio.to_thread()` | Phase 1 pattern | Established in GA4 adapter, reuse for all sync SDK calls in ETL workers |

**Deprecated/outdated:**
- `ENABLE_MOCKS` feature flag: Replaced by seed script approach
- Direct `ChannelConnectionRepository` import in `MetricsService`: Replaced by `ConnectionPort`
- Hardcoded channel lists in `get_attraction_metrics()`: Replaced by dynamic backend-driven channel registry

## Open Questions

1. **Tenant timezone storage**
   - What we know: Each tenant needs a timezone for 3am scheduling. The tenant model exists.
   - What's unclear: Whether the tenant model already has a timezone field or if one needs to be added.
   - Recommendation: Check the tenant model during planning. If missing, add `timezone` field (default 'America/Bogota' for Colombian users) with an Alembic migration.

2. **Weekly aggregation cutoff day storage**
   - What we know: User wants configurable weekly cutoff day per tenant (e.g., "Monday" or "Sunday").
   - What's unclear: Where to store this preference -- tenant model, analytics preferences, or a dedicated config table.
   - Recommendation: Add `weekly_cutoff_day` (Integer, 0=Monday ... 6=Sunday) to tenant model or a new `analytics_preferences` table.

3. **Async vs sync SQLAlchemy in workers**
   - What we know: The project currently uses sync `Session`. ARQ workers are async. Phase 1 used `asyncio.to_thread()` for sync calls.
   - What's unclear: Whether to migrate to `AsyncSession` for workers or continue the `asyncio.to_thread()` pattern.
   - Recommendation: Continue `asyncio.to_thread()` pattern for consistency with Phase 1 and to avoid a large refactor. The ETL jobs are I/O-bound against external APIs, not against the DB -- so DB calls being sync is acceptable.

4. **Multiple ad accounts per tenant per provider**
   - What we know: A tenant could have multiple Meta ad accounts or GA4 properties.
   - What's unclear: Whether `list_active_connections` returns one connection per channel_type or multiple.
   - Recommendation: The existing `ChannelConnectionModel` stores one row per (tenant_id, channel_type). If multiple accounts are needed, the adapter should extract from the account info in `config` JSONB. Handle this per-provider in the adapter.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0.0 + pytest-asyncio >= 0.23.5 |
| Config file | `backend/tests/conftest.py` (exists, uses SQLite in-memory) |
| Quick run command | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| Full suite command | `docker exec -t visionarias_brain_dev pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | Provider adapter ABC enforces interface; new adapter works by implementing ABC | unit | `pytest tests/modules/analytics/test_provider_adapter.py -x` | No -- Wave 0 |
| INFRA-02 | ConnectionPort returns decrypted credentials without importing connections directly | unit | `pytest tests/modules/analytics/test_connection_port.py -x` | No -- Wave 0 |
| INFRA-03 | Redis cache returns cached data within TTL; falls back to DB when Redis down | unit | `pytest tests/modules/analytics/test_metrics_cache.py -x` | No -- Wave 0 |
| INFRA-04 | CostType enum on DTOs; mapping returns correct type per (channel, stage) pair | unit | `pytest tests/modules/analytics/test_cost_type.py -x` | No -- Wave 0 |
| INFRA-05 | Disconnected providers return "Configurar" badge; seed script populates test data | unit+smoke | `pytest tests/modules/analytics/test_channel_fallback.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **Per wave merge:** `docker exec -t visionarias_brain_dev pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/modules/analytics/conftest.py` -- shared fixtures (mock credentials, test tenant, mock Redis)
- [ ] `tests/modules/analytics/test_provider_adapter.py` -- covers INFRA-01
- [ ] `tests/modules/analytics/test_connection_port.py` -- covers INFRA-02
- [ ] `tests/modules/analytics/test_metrics_cache.py` -- covers INFRA-03
- [ ] `tests/modules/analytics/test_cost_type.py` -- covers INFRA-04
- [ ] `tests/modules/analytics/test_channel_fallback.py` -- covers INFRA-05
- [ ] `tests/modules/analytics/test_etl_pipeline.py` -- E2E pipeline test with mocked adapters
- [ ] Framework install: pytest + pytest-asyncio already in requirements.txt

## Sources

### Primary (HIGH confidence)
- Existing codebase: `backend/src/modules/analytics/` -- current structure, MetricsService, DTOs
- Existing codebase: `backend/src/modules/connections/` -- ChannelConnectionRepository, BaseConnector ABC, ChannelConnectionModel, ChannelType enum, EncryptedJSON
- Existing codebase: `backend/src/core/database.py` -- Redis client, sync Session factory
- [ARQ official docs v0.27.0](https://arq-docs.helpmanual.io/) -- cron, retry, WorkerSettings, RedisSettings

### Secondary (MEDIUM confidence)
- [Meta Marketing API Rate Limiting](https://developers.facebook.com/docs/marketing-api/overview/rate-limiting/) -- X-Ad-Account-Usage headers, error codes 613/80004
- [GA4 Data API Quotas](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas) -- token-based quota system, returnPropertyQuota flag
- [Sentry FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/) -- auto-detection, traces_sample_rate, StarletteIntegration

### Tertiary (LOW confidence)
- ARQ maintenance-only status from [GitHub issue #437](https://github.com/python-arq/arq/issues/437) -- stable but no new features. v0.27.0 released 2026-02-02. Acceptable risk given the project's scale

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- ARQ is well-documented, Redis already in stack, all core libraries already installed
- Architecture: HIGH -- DDD patterns well-established in codebase, Port/Adapter is textbook DDD, ETL pipeline is straightforward
- Pitfalls: HIGH -- Rate limiting docs are from official provider sources, sync/async pitfall is from direct codebase analysis
- Cost type system: HIGH -- Simple enum + mapping, no external dependency

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable infrastructure patterns, unlikely to change)
