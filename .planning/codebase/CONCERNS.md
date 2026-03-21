# Codebase Concerns

**Analysis Date:** 2026-03-20
**North Star References:** `.trae/skills/backend-expert/references/` and `.trae/skills/frontend-expert/references/`

---

## Tech Debt

### [CRITICAL] Synchronous SQLAlchemy Session Used in Async FastAPI App

- Issue: 106 files in `backend/src/modules/` import `from sqlalchemy.orm import Session` instead of `AsyncSession`. The entire app is built on async FastAPI, but the `connections`, `assets`, `copilot`, `analytics` (repositories), `crm`, `scheduling`, `iam`, and `sales_agent` modules all block the event loop with synchronous DB calls.
- Files: `backend/src/modules/connections/api/whatsapp.py`, `backend/src/modules/connections/api/webhook.py`, `backend/src/modules/connections/api/mailerlite.py`, `backend/src/modules/connections/api/shopify.py`, `backend/src/modules/connections/api/youtube.py`, `backend/src/modules/analytics/infrastructure/repositories/sales_metrics_repository.py`, `backend/src/modules/analytics/infrastructure/repositories/capture_repository.py`, `backend/src/modules/analytics/infrastructure/repositories/nurture_repository.py`, `backend/src/modules/analytics/infrastructure/repositories/opportunity_repository.py`, `backend/src/modules/copilot/api/actions.py`, `backend/src/modules/assets/infrastructure/repositories/asset_repository.py` — and ~95 more.
- Impact: Thread starvation under concurrent load. Blocks I/O that should yield the event loop. Violates the standard: "Todo acceso a Base de Datos debe ser `async`."
- Fix approach: Replace `Session` with `AsyncSession`, convert `def` repository methods to `async def`, use `await session.execute(...)` patterns throughout. Prioritize `connections`, `analytics`, and `copilot` modules first as they have the highest usage.

---

### [CRITICAL] Hardcoded Business Logic and Prices in Sales Agent Semantic Router

- Issue: `SemanticRouter` has 30+ intent keywords AND live FAQ responses (including prices and dates) hardcoded as Python dicts. A `PromptLoader` system with Jinja2 templates exists but is bypassed. The `SUPERVISOR_PROMPT`, `QUALIFIER_PROMPT`, `EXPERT_PROMPT`, and `CLOSER_PROMPT` are also module-level constants.
- Files: `backend/src/modules/sales_agent/application/services/semantic_router.py`, `backend/src/modules/sales_agent/application/agents/sales/prompts.py`, `backend/src/modules/sales_agent/infrastructure/external/safety_service.py`, `backend/src/modules/sales_agent/infrastructure/prompts/semantic.py`
- Impact: Business-critical: prices and FAQ dates become stale without a redeploy. Multi-tenant overrides are impossible. No A/B testing. Violates "Nunca hardcodear" standard.
- Fix approach: See audit plan in `.claude/projects/-home-chris-AISALESHT/memory/audit_sales_agent_prompts.md`. Migrate 4 supervisor prompts to `supervisor_routing.j2`, FAQ responses to a `faqs` DB table, intent routes to `semantic_routes.j2`.

---

### [HIGH] Stdlib `logging` Used Instead of `structlog` Across 94+ Files

- Issue: The standard mandates "Logs estructurados con `structlog`. No usar `print`." However, 94 files use `import logging; logger = logging.getLogger(__name__)`. This includes all of `connections/infrastructure/channels/`, `scheduling/application/services/`, `analytics/infrastructure/providers/`, and others. Additionally, `mailerlite.py` uses raw `print()` calls.
- Files: `backend/src/modules/connections/infrastructure/channels/telegram.py`, `backend/src/modules/connections/infrastructure/channels/gmail.py`, `backend/src/modules/connections/infrastructure/channels/google_analytics.py`, `backend/src/modules/scheduling/application/services/availability_service.py`, `backend/src/modules/analytics/infrastructure/providers/google_analytics_provider.py`, `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py` — and ~88 more.
- Impact: Unstructured log output in production. No correlation IDs. Hard to query logs in Datadog/Loki/CloudWatch.
- Fix approach: Global search-replace `import logging` → `import structlog; logger = structlog.get_logger()`, replace `logging.getLogger(__name__)` with `structlog.get_logger()`. Use ruff to enforce.

---

### [HIGH] Repository Pattern Has No Domain Interfaces

- Issue: The standard requires repositories to implement an interface defined in `domain/interfaces.py` (`class UserRepository(IUserRepository)`). All 28+ repositories across the codebase are concrete classes with no abstract interface — they cannot be mocked for unit tests without patching internal implementations.
- Files: `backend/src/modules/brand/infrastructure/repositories/brand_repository.py`, `backend/src/modules/crm/infrastructure/repositories/customer_repository.py`, `backend/src/modules/offer/infrastructure/repositories/offer_repository.py`, `backend/src/modules/analytics/infrastructure/repositories/*.py` — and all other repository files.
- Impact: Unit tests are impossible without monkey-patching. Service constructors are tightly coupled to concrete classes. Violates the Dependency Inversion principle mandated in `architecture-rules.md`.
- Fix approach: Add `domain/interfaces.py` per module with ABC definitions. Make repository classes inherit from them. Inject interfaces in service constructors. Start with `crm` and `brand` (most tested modules).

---

### [HIGH] Cross-Module Boundary Violations (DDD Isolation Broken)

- Issue: The standard forbids direct imports between bounded contexts: "Un módulo NO puede importar directamente código de otro módulo." The `analytics` module imports directly from `crm` ORM models (not domain entities), `sales_agent` imports from `crm`, `connections`, `iam`, and `offer` internal models, and `copilot` imports from `brand` internal infrastructure.
- Files:
  - `backend/src/modules/analytics/infrastructure/repositories/capture_repository.py` imports `crm.infrastructure.models.customer_model`
  - `backend/src/modules/analytics/infrastructure/repositories/evangelization_repository.py` imports `crm.infrastructure.models.*`
  - `backend/src/modules/sales_agent/application/orchestrator/chat.py` imports `crm.infrastructure.repositories`, `connections.infrastructure.channels`, `iam.infrastructure.models`
  - `backend/src/modules/copilot/application/services/brand_ai_actions_service.py` imports `brand.application.extraction_service`
  - `backend/src/modules/copilot/application/agents/style_analyzer/nodes.py` imports `sales_agent.infrastructure.monitoring.tracing`
- Impact: Breaking one module silently breaks others. Schema changes ripple across boundaries. Makes independent module testing impossible.
- Fix approach: Introduce shared domain events or an anti-corruption layer. `analytics` should read from a dedicated read model or shared DTO. `sales_agent` should depend on `crm` via a public service interface, not repositories.

---

### [HIGH] `MetricsService` God Class (1930 Lines)

- Issue: `backend/src/modules/analytics/application/services/metrics_service.py` is 1930 lines. It contains all funnel-stage metric calculations in a single class. This directly violates the Single Responsibility Principle and makes the class untestable in isolation.
- Files: `backend/src/modules/analytics/application/services/metrics_service.py`
- Impact: Any change to one funnel stage requires touching this file. Merge conflicts are frequent. The class holds all 8 stage calculations plus caching logic.
- Fix approach: Split into per-stage services: `AttractionMetricsService`, `CaptureMetricsService`, etc., each in its own file under `analytics/application/services/`. Compose them via a `MetricsFacade` or route each endpoint to the appropriate service directly.

---

### [MEDIUM] Table Naming Convention Not Followed

- Issue: The standard requires module-prefixed table names (e.g., `iam_users`, `crm_leads`). The actual tables use generic names: `leads`, `sales`, `products`, `messages`, `assets`, `appointments`, `channel_connections`, `avatars`, etc. This risks future name collisions as the system scales.
- Files: All `__tablename__` definitions across `backend/src/modules/*/infrastructure/models/*.py`
- Impact: Risk of cross-module table name collision. Harder to understand DB ownership at a glance. Not a production bug today, but a migration cost tomorrow.
- Fix approach: Add module prefix to table names via Alembic `ALTER TABLE` migrations using the idempotent raw SQL pattern. Do this in bulk during a maintenance window.

---

### [MEDIUM] `PromptLoader` Cache Is Process-Level (Not Tenant-Safe in Multi-Worker Deployments)

- Issue: `PromptLoader` uses an in-process Python dict for its cache (`self._cache`). In a multi-worker Gunicorn/Uvicorn deployment, each worker has its own cache. An `invalidate_cache()` call on one worker has no effect on others. The code itself notes this: "Limpia para TODOS los tenants por seguridad o solo uno?"
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (lines 38-172)
- Impact: Stale prompts may be served for up to indefinite time if worker-level caches diverge. A tenant config update is not immediately reflected across all workers.
- Fix approach: Move cache to Redis with a shared key space and TTL. Use `redis.delete(f"prompt:{key}:{tenant_id}")` in `invalidate_cache()`.

---

### [MEDIUM] `tenant_router.py` Exposes Admin Endpoint Without Auth

- Issue: The `/api/v1/tenants/` endpoint has a documented TODO: "Admin only - TODO: Add admin protection." Currently it has no authentication or authorization guard — any request can list all tenants or create new ones.
- Files: `backend/src/modules/iam/api/routers/tenant_router.py`
- Impact: Critical security hole. Any unauthenticated caller can enumerate all tenants in the system or create arbitrary tenants.
- Fix approach: Add `Depends(get_current_user)` + admin role check immediately. Use the existing `iam/api/dependencies.py` patterns. Move this endpoint behind an admin Clerk organization check or internal API key.

---

### [MEDIUM] Shopify GDPR Compliance Webhooks Are Stubs

- Issue: The Shopify GDPR compliance endpoints (`/customers/data_request`, `/customers/redact`, `/shop/redact`) always return `{"status": "received"}` without executing any actual data export or deletion. These are legal obligations for Shopify app approval.
- Files: `backend/src/modules/connections/api/shopify_compliance.py`
- Impact: Legal/compliance risk. If the Shopify app is reviewed, stub responses may result in rejection or revocation. Customer data is never actually deleted on request.
- Fix approach: Implement actual data export (query all customer data by `shop_domain`, return a structured export) and deletion (soft-delete all CRM records associated with the shop) workflows. Wire them to background tasks.

---

### [MEDIUM] MailerLite Connector Sync Methods Are Stubs With `print()` Calls

- Issue: `sync_contacts()` and `sync_events()` in the MailerLite connector return empty lists and use `print()` for logging. These methods are called from ETL tasks but produce no data.
- Files: `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py` (lines 151-159)
- Impact: MailerLite data never flows into the analytics pipeline. Growth Studio metrics for email channels will always show zeros.
- Fix approach: Implement real MailerLite API calls using the existing `httpx` client pattern. Replace `print()` with `structlog`. Add to the ETL task queue.

---

## Security Considerations

### [CRITICAL] Unprotected Tenant Admin Endpoint

- Risk: `/api/v1/tenants/` (GET and POST) has zero auth. Any actor with network access can read all tenant data or create tenants.
- Files: `backend/src/modules/iam/api/routers/tenant_router.py`
- Current mitigation: None. The endpoint is not behind any auth dependency.
- Recommendations: Add `get_current_user` dependency + admin role check as immediate hotfix before any public exposure.

---

### [HIGH] Hardcoded Prices in Sales Agent Code

- Risk: FAQ prices are embedded as Python string literals in `semantic_router.py`. If prices change and the code is not updated, the AI agent will quote wrong prices to prospects — a direct business and compliance risk.
- Files: `backend/src/modules/sales_agent/application/services/semantic_router.py` (lines 174-182)
- Current mitigation: None.
- Recommendations: Move FAQ responses to a `faqs` DB table with per-tenant overrides. See audit plan in `.claude/projects/-home-chris-AISALESHT/memory/audit_sales_agent_prompts.md`.

---

## Performance Bottlenecks

### [HIGH] Sync Session Blocks Event Loop Under Concurrent Requests

- Problem: 106+ files use synchronous `Session` in async FastAPI handlers. Each DB call blocks the event loop thread, preventing other requests from being processed concurrently.
- Files: Primarily `backend/src/modules/connections/api/`, `backend/src/modules/analytics/infrastructure/repositories/`, `backend/src/modules/assets/`
- Cause: Legacy synchronous code was not migrated when the app moved to async.
- Improvement path: Migrate to `AsyncSession` + `await session.execute()`. This is the single highest-impact performance fix available.

---

### [MEDIUM] `MetricsService` (1930 Lines) Loads All Stage Data Sequentially

- Problem: The 1930-line `metrics_service.py` aggregates 8 funnel stages in a single service with sequential queries. Requests for the Growth Studio dashboard trigger all stage calculations in series.
- Files: `backend/src/modules/analytics/application/services/metrics_service.py`
- Cause: Monolithic design with no parallelism between stage calculations.
- Improvement path: Split into per-stage services (see Tech Debt section). Frontend already calls per-stage endpoints in parallel via React Query; backend should match with independent async service methods.

---

### [MEDIUM] In-Process Prompt Cache — No Shared State

- Problem: Prompt cache is per-process. In multi-worker deployments, cache invalidation does not propagate across workers, potentially causing stale prompt serving.
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py`
- Cause: In-memory Python dict used instead of Redis.
- Improvement path: Replace with Redis-backed cache using existing Redis infrastructure.

---

## Fragile Areas

### `MetricsDashboard` Component Uses Hard-Wired Mock Data for Stage Summaries

- Files: `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` (line 185), `frontend/src/features/marketing-studio/api/metrics-mock-data.ts`
- Why fragile: `const baseSummaries = STAGE_SUMMARIES` always pulls from the mock data file — the stage names, primary KPI labels, and secondary KPIs are never fetched from the API. Only the numeric values within each stage are overridden by real data. If the funnel stages change (names, order, count), the mock file must be manually updated.
- Safe modification: Any change to funnel stage structure requires updating both the backend API response schema AND `metrics-mock-data.ts`. Always update both together.
- Test coverage: Tests for `StageCard` exist but are TODO stubs — none are currently asserting real behavior.

---

### Sales Dashboard Service Is a Complete Stub

- Files: `frontend/src/features/sales/services/dashboardService.ts`
- Why fragile: `getStats()` and `getActivity()` return hardcoded zeros and empty arrays. Any component that renders these values will show an empty/zeroed dashboard with no error indication.
- Safe modification: Do not build UI features that depend on this service until the backend endpoints are implemented.
- Test coverage: None.

---

### `iam/api/routers/tenant_router.py` Uses Synchronous Session

- Files: `backend/src/modules/iam/api/routers/tenant_router.py`
- Why fragile: Uses `Session` (sync) from `src.core.database` — a pattern from legacy code. The router is `async def` but calls sync services underneath. Will break under async middleware changes.
- Safe modification: Do not add new endpoints to this router without migrating it to `AsyncSession` first.
- Test coverage: None found.

---

### `copilot` Module Imports from `sales_agent` Internal Infrastructure

- Files: `backend/src/modules/copilot/application/agents/style_analyzer/nodes.py`, `backend/src/modules/copilot/application/agents/style_analyzer/nodes_research.py`
- Why fragile: Both import `from src.modules.sales_agent.infrastructure.monitoring.tracing import trace_node`. A change to `tracing.py` in `sales_agent` will silently break the copilot agents.
- Safe modification: Tracing utilities should be moved to `shared/infrastructure/` before modifying `sales_agent`.
- Test coverage: Limited. Copilot module tests focus on prompt extraction, not agent graph execution.

---

## Test Coverage Gaps

### Backend: 7 of 13 Modules Have Zero Test Coverage

- What's not tested: `iam`, `sales_agent`, `landing`, `assets`, `advertising`, `social_media`, `crm` (no unit tests, only integration tests for CRM)
- Files: `backend/src/modules/iam/`, `backend/src/modules/sales_agent/application/`, `backend/src/modules/assets/`, `backend/src/modules/landing/`
- Risk: Core authentication (`iam`), the main revenue-generating AI agent (`sales_agent`), and asset management (`assets`) can silently regress. The sales agent orchestrator (`chat.py`, 462 lines) has no test.
- Priority: **Critical** — `sales_agent` and `iam` are the highest-business-value modules.

---

### Frontend: Most Test Files Are TODO Stubs

- What's not tested: All `marketing-studio` tests under `__tests__/` contain only TODO comments — no assertions execute. `StageCard.test.tsx`, `MetricSidebar.test.tsx`, `DetailSkeleton.test.tsx`, `useAttractionDetail.test.ts` are all skeleton files.
- Files: `frontend/src/features/marketing-studio/components/metrics-dashboard/__tests__/StageCard.test.tsx`, `frontend/src/features/marketing-studio/components/metrics-dashboard/sidebar/__tests__/MetricSidebar.test.tsx`, `frontend/src/features/marketing-studio/hooks/__tests__/useAttractionDetail.test.ts`
- Risk: Growth Studio metrics dashboard has no verified behavior. UI regressions will not be caught.
- Priority: **High** — this is a newly built feature with no safety net.

---

### `useEffect`-Based Data Fetching Across 46+ Files

- What's not tested: `useEffect` data fetching in `connections` components (`meta-view.tsx`, `whatsapp-view.tsx`, `gmail-view.tsx`, `google-calendar-view.tsx`, `shopify-view.tsx`, `youtube-view.tsx`) and several brand section forms.
- Files: 46 frontend files use `useEffect` for data fetching instead of TanStack Query (26 files use Query). The standard prohibits `useEffect` for server state fetching.
- Risk: Loading states and error states in these components are uncontrolled and untested. Race conditions on fast navigation are possible.
- Priority: **Medium** — refactor connections components to React Query as the component count is manageable.

---

## Scaling Limits

### `MetricsService` Single-Tenant Query Design

- Current capacity: Works for individual tenant requests.
- Limit: No query batching or background aggregation for high-traffic tenants. All analytics are computed on-demand from raw CRM data.
- Scaling path: The ETL/worker architecture already exists in `analytics/workers/tasks.py`. Ensure all metrics are pre-aggregated via ETL and served from `official_metrics` + `metric_aggregations` tables. Remove on-demand raw computation paths.

---

## Dependencies at Risk

### `connection_router.py` and Several Connection APIs Use `Session` from Legacy `src.core.database`

- Risk: `src.core.database` provides a synchronous session factory. This is a legacy entry point. If the core DB setup is migrated fully to async, these callers will break silently.
- Impact: All of `connections`, `assets`, and `copilot` module endpoints.
- Migration plan: Migrate all callers to `shared/infrastructure/db/session.py` async session factory before any core DB refactor.

---

## Missing Critical Features

### Domain Exceptions Missing in Most Modules

- Problem: Only `analytics` and `sales_agent` have `domain/exceptions.py`. The standard requires custom domain exceptions. Without them, services raise generic Python exceptions or untyped HTTP errors that don't express business intent.
- Blocks: Proper error differentiation at the API layer. `try/except Exception` anti-patterns are widespread as a result.

---

### No Module-Level `conftest.py` for Database Fixtures

- Problem: The standard requires `src/modules/{module}/tests/conftest.py` with module-specific fixtures. These do not exist. All tests in `backend/tests/` share a single `conftest.py` without transactional isolation between tests.
- Blocks: Test isolation. Tests that write to DB may affect other tests in the same run.

---

*Concerns audit: 2026-03-20*
