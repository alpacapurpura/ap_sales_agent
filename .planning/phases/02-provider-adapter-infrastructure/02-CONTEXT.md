# Phase 2: Provider Adapter Infrastructure - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a uniform, cached, fault-tolerant data pipeline that all 8 funnel stages can plug into. This includes: provider adapter base class (ABC), cross-module credential access via ConnectionPort, Redis cache for aggregated queries, cost type system (4 types), mock/fallback mechanism for disconnected providers, and — critically — a **daily ETL pipeline** that extracts metrics from external providers into local PostgreSQL tables. The dashboard reads from local DB, not from APIs in real-time.

</domain>

<decisions>
## Implementation Decisions

### ETL Architecture (Core Design Change)
- **Batch-only model**: No real-time API calls from dashboard. All data comes from a nightly ETL pipeline that extracts, transforms, and loads metrics into PostgreSQL
- **Data up to yesterday**: The dashboard always shows data through the previous day. No same-day data.
- **Two-layer storage**: Staging tables (hybrid: core columns + JSONB extras) per provider → internal transformation → Official tables with specific typed columns
- **Staging retention**: 30 days (already transformed). Official tables: permanent
- **Pipeline is atomic**: Extract → Load staging → Transform → Load official all in the same job run
- **Initial load**: Last 7 days, triggered immediately when a user connects a provider (not waiting for next cron). Must support expanding historical window in future milestones
- **Pre-calculated aggregations**: daily, weekly (configurable cutoff day per tenant + week-to-date), monthly, last 30 days — all computed by the pipeline
- **Trazability for Action Triggers**: Store enough detail in staging (campaign IDs, ad set IDs, ad creative IDs) so future Action Triggers can modify campaigns without re-querying provider APIs
- **Research needed**: Investigate current best practices and modern ELT libraries/frameworks for this pattern (user noted it may have evolved beyond traditional ETL)

### Adapter Contract Shape
- **Source-agnostic, metric-agnostic, stage-agnostic design**: Adapters don't know about funnel stages. They extract and normalize data. The service layer maps data to stages
- **Drill-down: 2 levels**: Stage → Channel → Campaign/detail. Each metric carries enough metadata for a second detailed API call
- **Explicit units in DTO**: Every metric includes `unit` field ('currency', 'percentage', 'count', 'ratio'). Frontend formats automatically based on unit
- **Original provider currency**: No conversion. Each metric carries `currency` field ('USD', 'COP', etc.). Frontend displays as-is
- **Adapter registry**: Claude's discretion, prioritizing extensibility and scalability
- **Internal vs external adapters**: Claude's discretion — decide whether CRM (DB) and external (HTTP/OAuth) adapters share the same ABC or have separate interfaces, prioritizing security, extensibility, and scalability
- **Date range as parameter from the start**: Adapters accept start_date/end_date even though date picker is out of scope. Default: last 30 days. Future-proofs for v2

### Cross-Module Credential Access
- **ConnectionPort (ABC) in analytics module**: Analytics defines the interface, connections implements it. Analytics never imports from connections directly. Pure DDD boundary
- **Port always returns valid token**: ConnectionPort handles token refresh transparently. Analytics never deals with token expiry
- **Specific exception on failure**: `ConnectionRevokedException` or `TokenRefreshFailed` when token can't be refreshed. ETL catches, marks channel as failed, continues with others
- **ConnectionPort persists refreshed tokens**: When a token is refreshed during extraction, the port (in connections module) saves the new token. Analytics never writes credentials
- **Two methods on port**: `get_credentials(tenant_id, channel_type)` + `list_active_connections(tenant_id)`. Job only attempts extraction for active connections
- **DI pattern**: Claude's discretion, prioritizing extensibility and scalability of the system

### Revoked Connection UX
- **Notification**: Claude's discretion, prioritizing best user experience (likely in-app notification when a connection is revoked, not just badge change)

### Redis Cache
- **Role**: Cache for aggregated dashboard queries (not for raw metrics). The primary data store is PostgreSQL
- **Fallback**: Silent fallback to PostgreSQL when Redis is down. Redis is purely an optimization; user never sees cache errors
- **Invalidation**: Active invalidation when ETL completes for a tenant (delete that tenant's cache keys). Also has TTL as safety net
- **TTL**: Short (5 min) for dashboard queries

### ETL Resilience & Error Handling
- **Fibonacci (or similar) backoff**: Failed extractions are retried with increasing intervals following best practices
- **Accumulated failures**: If a provider/tenant fails, the rest continue. Failed tasks go to a retry queue
- **Keep extracting everything else**: One provider failure never blocks other providers or other tenants
- **Persistent error display**: When extraction exhausts retries, the channel shows dash (—) not zeros + error badge with friendly message + reason
- **Manual retry button**: User can trigger re-extraction of just the failed metric/segment. Executes like the cron (up to yesterday). Cooldown of 15 min per channel after retry
- **extraction_runs table**: `(tenant_id, provider, status, started_at, completed_at, error, metrics_count)` plus performance metrics (duration, rows extracted, rate limit headroom)
- **Smart extraction**: Research and implement provider-specific rate limit awareness to never get banned. Each provider has different policies
- **Timestamp visible**: Dashboard shows "Última actualización: [date/time]" so user knows data freshness

### Job Queue & Scheduling
- **Tick-based scheduler**: Evaluates every minute which tenants are due for their 3am local time extraction
- **Timezone per tenant**: Each tenant's extraction runs at 3am in their configured timezone
- **Priority by plan**: Infrastructure for tenant priority (premium tenants extract first). Field on tenant model even if plans don't exist yet
- **Separate containers**:
  - `visionarias_scheduler` — generates jobs (tick every minute)
  - `visionarias_worker` — processes extraction jobs
  - Both in docker-compose alongside existing `visionarias_brain_dev`
- **Technology**: Claude's discretion — research and choose the best task queue for FastAPI + Redis + Docker

### Cost Type System
- **4 types**: NEUTRAL, EXPENSE, INVESTMENT (ad spend with expected ROI), REVENUE
- **Variable by funnel stage**: Same channel can be EXPENSE in Attraction but REVENUE in Sales
- **Mapping in code**: Dict/config file mapping `(channel, stage) → cost_type`. Changes require deploy but are versioned in git
- **Pattern must allow easy updates**: User expects cost type names/values may change — design with extensibility patterns that don't break everything
- **Default for unmapped**: Warning in logs when a channel has no mapping. Frontend shows no cost icon
- **Visual representation**: Icons + color. ↓ red for EXPENSE, ↑ green for REVENUE, → blue for INVESTMENT, — gray for NEUTRAL. Accessible (not color-only)

### Mock/Fallback for Development
- **Seed fixtures in DB**: Script `seed_metrics.py` fills staging + official tables with realistic test data. `docker exec seed`. Frontend always talks to real API backed by seeded DB
- **ENABLE_MOCKS deprecated**: With ETL model, frontend mocks are no longer needed. Backend seeds replace them
- **Disconnected channels UX**: Active channels with data shown first. Collapsible "Canales disponibles" section below with relevant-to-stage unconnected channels showing "Configurar" badge

### Frontend Channel Rendering
- **Dynamic from backend**: The endpoint returns the channels that exist for that stage+tenant. Frontend renders what it receives. Adding a channel doesn't require frontend changes
- **Stage-contextual available channels**: The collapsible section only shows channels relevant to the current stage, not all possible channels

### Observability
- **Streamlit admin dashboard**: ETL monitoring visible in existing Streamlit admin (SSH access). Shows extraction status, failures, pending retries
- **Health endpoint**: `GET /health/etl` returns last successful run, pending tenants, active failures
- **Performance metrics**: Each extraction logs: duration, rows extracted, rate limit headroom, errors
- **Sentry SDK**: Implement across full stack (API + worker + scheduler). Captures unhandled exceptions, groups by type/frequency, performance monitoring

### Security
- **Same DB, same encryption**: Worker uses same PostgreSQL connection with EncryptedJSON for credentials. No separate secrets manager for now
- **Revenue fields encrypted**: Monetary fields (spend, revenue, cost) encrypted in staging/official tables. Other metrics in plain text
- **Tenant isolation**: All queries filter by tenant_id (existing pattern)

### Testing Strategy
- **Unit tests with mocks**: Each adapter tested with pre-recorded JSON responses. Fast, reliable, no external API dependency
- **TODO for integration tests**: Leave infrastructure and mark as TODO for adding real API integration tests later
- **E2E pipeline test**: Full flow test using test PostgreSQL + test Redis with mocked adapters. Verifies data flows correctly from extraction through to official tables
- **No real API calls in CI**: All CI tests use mocked responses

### Migration from Existing Code
- **Replace MetricsService**: Refactor to read from official ETL tables instead of ad-hoc journey_events queries. Same endpoint URLs, different data source. Frontend unchanged
- **Dynamic channel list from backend**: Frontend stops hardcoding 13 channels in AttractionDetail.tsx. Backend returns channel list dynamically based on what exists for that stage+tenant

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

</decisions>

<specifics>
## Specific Ideas

- "Deberíamos tener los valores necesarios guardados en nuestra base de datos en intervalos diarios" — the user is very clear about centralizing data locally, not calling APIs on-demand
- "Debes ser inteligente en la extracción de la data y debes leer sobre las políticas de extracción para jamás ser baneados" — anti-ban is a hard requirement, not a nice-to-have
- "Es muy probable que te pida en el siguiente milestone ampliar la cantidad de data histórica en la carga inicial" — initial load window (7 days) must be parameterizable
- "Si llegamos al click de una campaña específica, debo tener los datos que me permitan luego actualizar la campaña en un milestone futuro sin tener que ir hasta Meta" — staging data must include campaign/ad-level IDs for future Action Triggers
- "El usuario debe escoger el día de semana de 'corte' para el semanal" — weekly aggregation cutoff is per-tenant configurable
- Existing Streamlit admin dashboard exists for monitoring (SSH access)
- "Debes tener en mente que debes usar patrones de diseño que permitan variar eso de forma que no se rompa todo el código" — extensibility is a top-priority quality attribute across all design decisions

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EncryptedJSON` column type: Transparent credential encryption/decryption for staging monetary fields
- `ChannelConnectionRepository.get_active(tenant_id, channel_type)`: Basis for ConnectionPort implementation
- `ConnectionBadge` component: Already handles Conectado/Configurar states — extend for error badge
- `ENABLE_MOCKS` global toggle: Will be deprecated in favor of DB seed approach
- `BaseConnector` ABC in connections module: Existing ABC pattern (sync_contacts/events) — different concern but shows the codebase uses ABCs

### Established Patterns
- Per-request adapter instantiation (Meta): Safe pattern to follow for ETL adapters
- `asyncio.to_thread()` for sync SDK calls (from Phase 1)
- Tenant isolation via `tenant_id` filter on all queries
- Docker-first development with docker-compose
- Alembic for database migrations

### Integration Points
- `MetricsService` (analytics/application/services/metrics_service.py): Will be refactored to read from ETL tables
- `ChannelConnectionRepository` (connections/infrastructure/repositories/): ConnectionPort wraps this
- `AttractionDetail.tsx`: Will transition from hardcoded channels to dynamic backend-driven rendering
- `docker-compose.yml`: Needs new services for scheduler and worker containers
- `backend/src/core/config.py`: REDIS_URL already configured
- `backend/requirements.txt`: Will need new dependencies (task queue, Sentry SDK)

</code_context>

<deferred>
## Deferred Ideas

- **Real-time WebSocket updates**: Out of scope — batch model is the architecture decision
- **Date range picker UI**: v2 requirement (UX-01) — adapters accept dates but UI won't expose it yet
- **Vault/secrets manager**: Future security upgrade — current EncryptedJSON is sufficient for now
- **Integration tests against real APIs**: TODO left in test infrastructure
- **Action Triggers (campaign modification)**: Future milestone — but staging data schema accounts for it
- **Admin panel for cost_type configuration**: If mapping changes become frequent, consider DB-based config in the future

</deferred>

---

*Phase: 02-provider-adapter-infrastructure*
*Context gathered: 2026-03-15*
