# Codebase Concerns

**Analysis Date:** 2026-03-15

---

## Tech Debt

**Synchronous SQLAlchemy in Async FastAPI (Critical, Systemic):**
- Issue: The entire database layer uses a synchronous `create_engine` + `sessionmaker`, while 221 FastAPI route handlers are declared `async def`. This means every DB call blocks the event loop, eliminating the performance benefit of async I/O.
- Files: `backend/src/core/database.py`, all modules using `Session = Depends(get_db)`
- Impact: Degrades throughput under concurrent load. Under high traffic, the event loop stalls on every DB operation. This is a foundational architectural mismatch.
- Fix approach: Migrate to `create_async_engine` + `async_sessionmaker` + `AsyncSession`. Update all repositories and services to use `await session.execute(...)`. Requires replacing `SessionLocal()` with `async with AsyncSession() as session:` everywhere.

**Legacy SQLAlchemy 1.x Query Syntax in Multiple Modules:**
- Issue: Several modules still use the deprecated `db.query(Model).filter(...)` syntax instead of the required SQLAlchemy 2.0 `select(Model)` style.
- Files:
  - `backend/src/modules/assets/infrastructure/repositories/asset_repository.py` (lines 60, 66, 73, 77)
  - `backend/src/modules/assets/infrastructure/repositories/gallery_repository.py` (lines 51, 57, 61, 65)
  - `backend/src/modules/assets/application/assets_service.py` (line 131)
  - `backend/src/modules/scheduling/infrastructure/repositories/appointment_repository.py` (line 37)
  - `backend/src/modules/scheduling/application/services/availability_service.py` (lines 64, 368)
  - `backend/src/modules/scheduling/api/public_links.py` (multiple lines)
  - `backend/src/modules/connections/api/webhook.py` (line 23)
  - `backend/src/modules/connections/api/calendar.py` (line 125)
  - `backend/src/modules/crm/infrastructure/repositories/lead_metrics_repository.py` (lines 40, 51, 175)
  - `backend/src/modules/sales_agent/infrastructure/external/safety_service.py` (line 23)
  - `backend/src/modules/sales_agent/infrastructure/memory/audit_repository.py` (line 105)
- Impact: Inconsistent codebase; these will break or require workarounds when migrating to fully async SQLAlchemy 2.0.
- Fix approach: Replace `db.query(Model).filter(...)` with `select(Model).where(...)` pattern consistently across all modules.

**Duplicate ClerkService Implementation:**
- Issue: Two identical 220-line `ClerkService` classes exist in separate files. Both are independent copies with no shared parent.
- Files: `backend/src/shared/infrastructure/external/clerk.py` and `backend/src/modules/sales_agent/infrastructure/external/clerk.py`
- Impact: Bug fixes or API changes must be applied in two places. The `sales_agent` copy appears unused (no imports found pointing to it), creating dead code confusion.
- Fix approach: Delete `backend/src/modules/sales_agent/infrastructure/external/clerk.py`. All modules should import from `backend/src/shared/infrastructure/external/clerk.py`.

**PromptLoader In-Memory Cache Has No TTL:**
- Issue: The `PromptLoader._cache` and `_tenant_config_cache` dictionaries grow indefinitely at runtime with no eviction strategy. The code even contains a comment: `# Simple TTL logic could be added here`.
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (lines 38–47)
- Impact: Memory leak in long-running production containers. Stale prompts/config served after updates without a restart.
- Fix approach: Add TTL-based expiry (e.g., check `loaded_at` timestamp on every read; evict entries older than N minutes). Alternatively use a bounded LRU cache (`functools.lru_cache` with `maxsize`).

**SessionLocal() Manually Opened Inside Application Services:**
- Issue: `assets_service.py` opens a raw `SessionLocal()` manually inside a background task callback, bypassing FastAPI's dependency injection lifecycle. This creates unmanaged connections.
- Files: `backend/src/modules/assets/application/assets_service.py` (lines 95–97)
- Impact: Connection pool exhaustion under load; exceptions won't properly close the session if not handled carefully.
- Fix approach: Pass the `db` session into background tasks via dependency injection or use a context manager pattern: `async with AsyncSession() as db:` (after async migration).

**MetricsDashboard Hardcoded to Mock Data:**
- Issue: `MetricsDashboard` directly imports `STAGE_SUMMARIES` from `metrics-mock-data.ts` and renders it unconditionally, regardless of the `ENABLE_MOCKS` flag. No real API integration exists for stage summaries.
- Files:
  - `frontend/src/features/marketing-studio/components/metrics-dashboard/MetricsDashboard.tsx` (lines 6, 19, 25)
  - `frontend/src/features/marketing-studio/api/metrics-mock-data.ts`
- Impact: Growth Studio metrics dashboard always shows demo data to real users. No real funnel data is displayed.
- Fix approach: Wire `MetricsDashboard` to a real API call (or at minimum respect the `ENABLE_MOCKS` flag). Create backend endpoint for stage summaries.

**Sales Dashboard Service Is a Stub Returning Zeros:**
- Issue: `dashboardService.getStats()` and `dashboardService.getActivity()` return hardcoded zeros/empty arrays with `// TODO: implement when endpoints are ready` comments.
- Files: `frontend/src/features/sales/services/dashboardService.ts` (lines 22–37)
- Impact: Sales Studio dashboard always shows 0 sales, 0 appointments, 0 leads to real users.
- Fix approach: Implement the backend endpoints and wire the service to actual API calls.

**FSD Layer Violation: offer-studio Directly Imports from brand:**
- Issue: Multiple components inside `offer-studio` import types, hooks, API clients, and UI components directly from the `brand` feature slice, violating Feature-Sliced Design's prohibition on cross-feature imports.
- Files:
  - `frontend/src/features/offer-studio/components/editor/sections/instructors/instructors-selector.tsx` — imports `TeamManager` component and `KeyFigure` type from `brand`
  - `frontend/src/features/offer-studio/components/editor/sections/instructors/instructors-manager.tsx` — imports `brandApi` and `KeyFigure` from `brand`
  - `frontend/src/features/offer-studio/components/editor/components/widgets/instructors-widget.tsx` — same
  - `frontend/src/features/offer-studio/components/editor/sections/identity/identity-preview.tsx` — imports `useBrandSettings` hook from `brand`
  - `frontend/src/features/offer-studio/components/editor/sections/instructors/instructors-preview.tsx` — same
- Impact: Tight coupling between features; changes to `brand` types/API break `offer-studio` silently.
- Fix approach: Extract shared types (`KeyFigure`, brand-related offer fields) into a shared layer (e.g., `shared/types/`). Extract the `TeamManager` and instructor selection logic into a shared widget or shared entity.

**FSD Layer Violation: settings Imports Directly from connections:**
- Issue: `SettingsView.tsx` imports multiple items directly from the `connections` feature.
- Files: `frontend/src/features/settings/components/SettingsView.tsx` (7 cross-feature imports)
- Impact: Same tight coupling concern as above.
- Fix approach: Extract shared connection types/hooks to `shared/` or `entities/` layer.

---

## Known Bugs

**PromptVersion.is_active Used Without Equality Check (Potential Silent Query Bug):**
- Symptoms: `PromptVersion.is_active` passed as a SQLAlchemy `.where()` condition without explicit `== True`. With SQLAlchemy 2.0 strict mode, column objects used as bare clause elements may generate a warning or behave unexpectedly (treats the column as a truthy expression, not a proper boolean filter).
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (lines 70, 81)
- Trigger: Any call to `PromptLoader._get_from_db()` when `PROMPT_SOURCE` is `DB` or `Hybrid`.
- Workaround: Use `.where(PromptVersion.is_active == True, ...)` or `.where(PromptVersion.is_active.is_(True), ...)`.

**CRM Lead Search Endpoint Returns Empty List Always:**
- Symptoms: `GET /api/v1/crm/leads/search?q=...` always returns `[]`, regardless of query string. The actual search logic is commented out.
- Files: `backend/src/modules/crm/api/leads.py` (lines 24–30)
- Trigger: Any frontend or API call to the lead search endpoint.
- Workaround: None — search is non-functional.

**Sales Agent Scheduler Node Disabled (Routes to Closer Fallback):**
- Symptoms: When the AI router decides to route to `scheduler`, the graph silently falls back to `closer` instead. The scheduler node is commented out.
- Files: `backend/src/modules/sales_agent/application/agents/sales/graph.py` (lines 18, 31)
- Trigger: Any conversation where the agent determines scheduling intent.
- Workaround: The `closer` node handles it, but without actual calendar booking capability.

**Shopify Shop Lookup Loads All Active Connections Then Filters in Python:**
- Symptoms: `get_active_shopify_by_shop()` fetches ALL active Shopify connections from the DB across all tenants, then iterates in Python to match by shop domain.
- Files: `backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py` (lines 114–138)
- Trigger: Any inbound Shopify webhook.
- Impact: Scales O(n) with number of tenants using Shopify. A JSONB index on `config->>'shop_url'` would fix this.

---

## Security Considerations

**Tenant Admin Endpoint Has No Access Control:**
- Risk: `GET /api/v1/tenants/` lists all tenants in the system. `POST /api/v1/tenants/` creates new tenants. Neither endpoint has admin-role protection — any authenticated user can call them.
- Files: `backend/src/modules/iam/api/routers/tenant_router.py` (entire file, comment reads "Admin only - TODO: Add admin protection")
- Current mitigation: None. Authentication (Clerk) is required, but no authorization check.
- Recommendations: Add an admin role check dependency (e.g., `Depends(require_admin_role)`) to both endpoints immediately. This is a tenant data exposure risk.

**GDPR Compliance Webhooks Are No-Op Stubs:**
- Risk: Shopify sends GDPR `customers/redact`, `customers/data_request`, and `shop/redact` webhooks. All three endpoints acknowledge receipt but do not perform any actual data export or deletion.
- Files: `backend/src/modules/connections/api/shopify_compliance.py` (entire file)
- Current mitigation: Webhooks are acknowledged (returns 200) so Shopify doesn't retry, but no data action is taken.
- Recommendations: Implement actual data deletion/export workflows. This is a legal compliance requirement for Shopify app listings.

**PromptLoader Cache Shared Across All Tenants (Potential Data Leak):**
- Risk: The `PromptLoader` is a module-level singleton. If a prompt is cached for one tenant and a bug causes incorrect cache key resolution, another tenant could receive another tenant's custom prompts.
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (lines 36–38, cache key is `(key, tenant_id)` tuple)
- Current mitigation: Cache key includes `tenant_id`, so this is partially mitigated. However, the comment in `clear_cache()` reads: "Limpia caché (OJO: Limpia para TODOS los tenants por seguridad o solo uno?)" — indicating uncertainty about the intended isolation behavior.
- Recommendations: Audit `clear_cache()` call sites. Clarify that cache is always keyed by `(key, tenant_id)` and document this explicitly.

---

## Performance Bottlenecks

**Synchronous DB Calls Block the Async Event Loop:**
- Problem: As documented under Tech Debt, all 221 `async def` route handlers call synchronous SQLAlchemy. In production under load, this serializes requests through the thread pool.
- Files: `backend/src/core/database.py` + all route/service files
- Cause: `create_engine` (sync) used instead of `create_async_engine`.
- Improvement path: Full async SQLAlchemy migration (see Tech Debt section).

**OutputManager Blocks Response Delivery with asyncio.sleep:**
- Problem: For every outgoing AI sales agent message, `OutputManager.process_response()` holds an async task open for 1.5–6 seconds per message chunk to simulate typing. A multi-chunk response can hold a worker slot for 10–20+ seconds.
- Files: `backend/src/modules/sales_agent/infrastructure/external/output_manager.py` (lines 46, 66)
- Cause: Intentional "human typing simulation" with hardcoded `CPM_SPEED`, `MIN_TYPING_TIME`, `MAX_TYPING_TIME` constants.
- Improvement path: Move typing simulation to a background task or offload to a queue (e.g., Celery/Redis). Constants are not configurable per-tenant or per-environment.

**WhatsApp Connection Verification Has Hardcoded Sleeps:**
- Problem: WhatsApp connection flow contains `await asyncio.sleep(5)` and `await asyncio.sleep(2)` directly in an API endpoint handler.
- Files: `backend/src/modules/connections/api/whatsapp.py` (lines 122, 131)
- Cause: Polling workaround rather than event-driven acknowledgment.
- Improvement path: Replace polling with a webhook/callback confirmation or at minimum move to a background task.

**PromptLoader Opens a New DB Session Per Prompt Load (No Connection Reuse):**
- Problem: `_get_from_db()` and `_get_tenant_config()` each call `SessionLocal()` directly and close it manually. This creates a new connection from the pool on every cache miss.
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (lines 56–62, 74–91)
- Cause: `PromptLoader` operates outside the FastAPI dependency injection lifecycle.
- Improvement path: Pass the request-scoped DB session to the loader, or implement proper TTL caching to minimize DB calls.

---

## Fragile Areas

**`instructors-selector.tsx` Renders a Full `TeamManager` Widget Inline:**
- Files: `frontend/src/features/offer-studio/components/editor/sections/instructors/instructors-selector.tsx`
- Why fragile: Directly renders `TeamManager` from the `brand` feature. Any prop signature change or internal refactor of `TeamManager` breaks `offer-studio` with no compile-time guard.
- Safe modification: Do not change `TeamManager` props without auditing all cross-feature imports. Long-term: extract to `shared/widgets/`.
- Test coverage: No tests for this component.

**`PromptLoader` Is a Module-Level Singleton with Shared Mutable State:**
- Files: `backend/src/modules/sales_agent/infrastructure/prompts/base.py`
- Why fragile: The singleton pattern with mutable `_cache` and `_tenant_config_cache` dicts means any concurrency issue (simultaneous writes) could corrupt cache state. No lock mechanism exists.
- Safe modification: Do not add writes to cache without verifying thread-safety. Consider using a `threading.Lock` or moving to Redis-backed cache.
- Test coverage: Not covered in the 3 total backend test files.

**`get_active_shopify_by_shop()` Falls Back to Sequential In-Memory Scan:**
- Files: `backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py` (lines 114–138)
- Why fragile: Relies on iterating all Shopify connections in memory. If config JSON structure changes (e.g., field rename from `shop_url`), the lookup silently returns `None` and webhooks are silently dropped.
- Safe modification: Do not rename config keys without updating this method and adding a DB migration.
- Test coverage: Not covered.

**`CustomerService.identify()` Does Not Update Existing Profile Traits:**
- Files: `backend/src/modules/crm/application/services/customer_service.py` (line 31, `# TODO: Implement update logic in repo`)
- Why fragile: If a returning customer provides new information (e.g., updated email), the system finds the existing profile but silently discards the new trait data. CDP merge logic is incomplete.
- Safe modification: When touching customer identity resolution, be aware that existing profiles are returned unmodified.
- Test coverage: Covered in `backend/src/tests/test_telegram_flow.py` for creation only, not trait-update path.

**`legacy-landing-editor.tsx` Is Orphaned Dead Code:**
- Files: `frontend/src/features/offer-studio/components/landing/components/editor/legacy-landing-editor.tsx` (533 lines)
- Why fragile: The only export `LegacyLandingPageEditor` has no confirmed import anywhere in the codebase. It is a 533-line component that may have stale logic/types.
- Safe modification: Verify no dynamic import exists before deletion. Deleting it will reduce bundle size and remove maintenance burden.

---

## Scaling Limits

**In-Memory PromptLoader Cache Does Not Scale Horizontally:**
- Current capacity: Single container; cache is process-local.
- Limit: In a multi-replica deployment, each replica maintains its own independent cache, causing inconsistent prompt delivery and excessive DB load.
- Scaling path: Move prompt cache to Redis (already present in the stack) using `redis_client` from `backend/src/core/database.py`.

**EventBus Is In-Process Only:**
- Current capacity: Single process; events are handled within the same Python process.
- Limit: `backend/src/modules/sales_agent/application/event_bus.py` — the EventBus uses in-memory asyncio subscriptions. No persistence, no retry, no cross-process delivery.
- Scaling path: Replace with a Redis Streams or Celery queue-backed event bus for durability and horizontal scaling.

---

## Dependencies at Risk

**No Rate Limiting on Any API Endpoint:**
- Risk: The FastAPI application has no rate limiting middleware. Any authenticated user can hammer any endpoint without throttling.
- Impact: Susceptible to accidental or deliberate DoS. LLM endpoints (which call external paid APIs) are particularly at risk of cost amplification.
- Migration plan: Add `slowapi` or a Redis-backed rate limiter middleware in `backend/src/main.py`.

---

## Missing Critical Features

**Shopify GDPR Data Deletion/Export:**
- Problem: Three GDPR compliance webhook endpoints exist but contain no implementation — only `# TODO: Trigger data deletion workflow`.
- Blocks: Required for Shopify app store listing and legal compliance with GDPR/CCPA.

**MailerLite Sync Is Non-Functional:**
- Problem: `MailerliteConnector.sync_contacts()` and `sync_events()` return empty lists with `print()` debug calls instead of real MailerLite API calls.
- Files: `backend/src/modules/connections/infrastructure/marketing_connectors/mailerlite.py` (lines 33–41)
- Blocks: Any Growth Studio analytics that depends on email subscriber/event data from MailerLite.

**Marketing Webhook Handlers Do Nothing with Payloads:**
- Problem: Shopify and MailerLite webhook endpoints acknowledge receipt but contain `# TODO: Use Communication Service or Event Bus to handle this`.
- Files: `backend/src/modules/connections/api/marketing_webhooks.py`
- Blocks: Automated marketing trigger workflows (cart abandon, purchase events, etc.).

---

## Test Coverage Gaps

**Backend Has Near-Zero Test Coverage:**
- What's not tested: All domain logic, all API endpoints, all repositories, all application services, all external integrations (Clerk, Qdrant, OpenAI, Meta, etc.)
- Files: Only `backend/src/tests/test_telegram_flow.py` (368 lines, integration test) and one additional test file exist.
- Risk: Any refactor silently breaks functionality. No regression safety net.
- Priority: High

**Frontend Has Minimal Test Coverage (7 Test Files, ~8,000+ Lines of Components):**
- What's not tested: All connection views, all brand studio sections except validation utils, sales features, Growth Studio metrics, scheduling flows, admin views, public landing pages.
- Files: 7 test files covering `label.tsx`, brand validation utils, offer-studio dashboard logic, offer card rendering, program form, session schedule builder, and strategy canvas.
- Risk: Core user flows (brand setup, offer creation, connections) have no automated coverage.
- Priority: High

**No Tests for Multi-Tenant Isolation Logic:**
- What's not tested: The core security invariant — that no tenant can access another tenant's data — is not tested anywhere. All queries that filter by `tenant_id` are untested.
- Files: All repositories in `backend/src/modules/*/infrastructure/repositories/`
- Risk: A regression in tenant filtering would be a critical data breach with no automated detection.
- Priority: Critical

**No Tests for Sales Agent Graph / LLM Orchestration:**
- What's not tested: The LangGraph sales agent routing (qualifier → product_expert → closer), prompt loading, output chunking, safety service, memory/context retrieval.
- Files: `backend/src/modules/sales_agent/application/agents/sales/graph.py`, `backend/src/modules/sales_agent/application/orchestrator/chat.py`
- Risk: Regressions in AI routing or prompt loading fail silently in production.
- Priority: High

---

*Concerns audit: 2026-03-15*
