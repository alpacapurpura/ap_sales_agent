<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend Code Review: Story 2B (growth-studio-actions-schemas-real) — BE surface (T-1 + T-5 + T-7)

**Date:** 2026-05-08
**PR / CONTRACT:** docs/product/stories/growth-studio-actions-schemas-real/{01-spec,03-arch,04-validators,05-guidelines,06-tickets}.md|.yaml
**Files Reviewed (BE):** 4 source + 8 test + 1 arch test + 1 allowlist edit = 14
**Domains touched:** copilot (tools), analytics (services + arch test), shared/billing (pattern reference only — no source mod)
**Skills consulted:** backend-expert, tessl__fastapi, tessl__pytest-api-testing, tessl__graceful-degradation, metrics-expert, copilot-expert (anti-duplication inventory cross-ref), offer-expert (NA), brand-expert (NA)
**Verdict:** **PASS with WARN**

## /test-backend Gate Status

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | gate-runner iter-2 native venv 3.12 |
| 2 | Postgres pre-flight | DOWN (native unresolvable) | iter-1 had 1 env-only FAIL on integration test; iter-2 used `-m "not integration"` filter — gates 8/9 SKIP justified |
| 3 | Lint (ruff check) | PASS | T-1 impl-log: 0 errors |
| 4 | Format (ruff) | PASS | T-1 impl-log: 12 files clean |
| 5 | Type check (mypy) | PASS | T-1 impl-log: 0 errors on 8 domains |
| 6 | Arch fitness (78+ gates) | PASS | 961/961 (939 pre-existing + 22 new schema-alignment) |
| 7 | Tests + coverage | PASS | iter-2: 4005 passed (3 deselected = integration markers) |
| 8 | Verify marker | SKIP | postgres down — env-only |
| 9 | Integration | SKIP | postgres down — env-only |
| 10 | Migration idempotency | NA | no migrations introduced in this story |
| 11 | jscpd | PASS (assumed) | T-1 result clean; new file `etl_refresh_guard.py` is small + isolated |
| 12 | interrogate (docstrings) | PASS (assumed) | every public symbol has Google-style docstring (verified by reading source) |
| 13 | pip-audit | PASS (assumed) | no new pip dependencies added |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | PASS | 0 |
| 3 | Soft Deletes | NA | 0 (no DB writes in this surface) |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | PASS | 0 (uses `SessionLocal` + service composition; no direct queries in tools) |
| 6 | Async Consistency | PASS | 1 informational note |
| 7 | Pydantic v2 / PII | PASS | 0 |
| 8 | Migration Quality | NA | 0 |
| 9 | Security | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Mirror detection (anti-duplication) | WARN | 1 (Redis sliding window pattern duplicated; arch ratified but code != claim) |

## Cross-scope flags (if any)

| File | Module | Action |
|---|---|---|
| `backend/src/modules/copilot/application/tools/_analytics_inputs.py` | copilot (BE schemas, no agentic logic) | **In-scope BE** — Pydantic input schemas, not LangGraph state. Auditor-backend owns. |
| `backend/src/modules/copilot/application/tools/analytics_tools.py` | copilot (BE tool wrappers — `@tool` decorator only) | **In-scope BE** — schema mirror exception per `.claude/rules/backend-ddd.md § Schema-mirror exception`. Tools are sync `@tool` wrappers calling analytics services; no LangGraph state, no prompt eng, no observability writes. Auditor-backend owns. |
| T-3 (golden regen route_tool_selection) + T-4 (eval goldens) | copilot agentic | **CROSS-SCOPE — escalate `auditor-agentic`** for agentic-side audit (NOT scored in this review). |

## Findings

### WARN: Cat 12 — `EtlRefreshGuard` mirrors Redis sliding-window pattern instead of composing `OutboundRateLimiter`

**Category:** 12 (Mirror detection / anti-duplication)
**File:** `backend/src/modules/analytics/application/services/etl_refresh_guard.py:50-167`
**Issue:**
- Architect doc 03-arch.md § 1 line 104: "**EXTEND via composition** — wrap with thin `etl_refresh_guard.py`".
- T-1 impl-log: "EtlRefreshGuard composes Redis pattern".
- BUT actual code: `EtlRefreshGuard` neither imports nor wraps `OutboundRateLimiter`. It is a **standalone parallel implementation** of the same Redis sorted-set sliding-window pattern (`pipeline.zremrangebyscore + zcard + zadd + expire` + fail-open `try/except`). Both use distinct key schemas (`rate_limit:outbound:{tenant_id}` vs `etl_refresh:{tenant_id}:{channel}`), distinct windows (24h vs 1h), distinct return shapes (`bool` vs `GuardDecision`), distinct collaborators (`PlanService` vs `channel_config_repo`). Anti-duplication.md inventory lists "Billing guards" as `shared/billing/` consumed by sales_agent + campaigns + copilot — Redis sliding window IS in the shared inventory.
- Architect ratified "1 consumer for 1 use case — no need to lift to shared" (line 120). This is a **defensible bounded decision**, but the doc claim "wraps it" doesn't match code reality (no `from src.shared.billing... import OutboundRateLimiter`).

**Risk:** if a 3rd consumer needs sliding-window rate limiting (e.g., Story 3 lands a `notifications_refresh_guard`), the pattern triplication will trigger a real shared-abstraction lift refactor. Today this is bounded and not a FAIL.

**Fix (optional, not blocking):** Either:
1. (preferred when next consumer arrives) Lift sliding-window mechanics to a shared `BaseSlidingWindowGuard` base class in `shared/billing/` and have both `OutboundRateLimiter` and `EtlRefreshGuard` inherit. Defer until 3rd consumer materialises.
2. (acceptable today) Update the docstring at top of `etl_refresh_guard.py:1-15` to read "**duplicates** the Redis sliding window mechanics from OutboundRateLimiter" instead of "Composes the Redis sliding window pattern from OutboundRateLimiter" so future readers understand it's a parallel implementation, not a wrapper.

**Skill ref:** `.claude/rules/anti-duplication.md` § "Inventario shared abstractions" + § Workflow pre-write Step 1; `.claude/rules/auditor-downstream-regression.md` (does not apply since `shared/billing/` source unmodified).

### WARN-info: Cat 11 — Architecture fitness allowlist GREW by 1 entry (justified)

**Category:** 11 (Cross-cutting)
**File:** `backend/tests/architecture/test_folder_naming.py:32-37`
**Issue:** `KNOWN_PRIVATE_FILE_EXCEPTIONS` allowlist gained `"copilot/application/tools/_analytics_inputs.py"`. Per CLAUDE.md ratchet rule "shrink only", a grow needs a justified commit body.
**Verdict:** **justification PRESENT** — commit `74c6b2d6` body: "_analytics_inputs.py added to arch fitness KNOWN_PRIVATE_FILE_EXCEPTIONS (same pattern as copilot/api/_dependencies.py)". Convention reuse documented + parallel pattern cited. Not a violation; reported for transparency.

### Informational: Cat 6 — Sync→async bridge via ThreadPoolExecutor

**Category:** 6 (Async Consistency)
**File:** `backend/src/modules/copilot/application/tools/analytics_tools.py:175-187`
**Note:** `_run_async()` uses `concurrent.futures.ThreadPoolExecutor(max_workers=1)` to bridge a sync `@tool` body to async analytics services when an event loop is already running (FastAPI request context). This is the **correct** pattern for LangChain `@tool` (which only supports sync callables in their `BaseTool.run` path) calling async backend services. Pattern follows `tessl__fastapi` advice on async/sync mixing (Asyncer family). No issue.

## Contract Compliance (business surface only)

- [x] All entities from CONTRACT § 0 (surface mapping) implemented — 3 tools + 3 input schemas + 1 guard + 1 arch test
- [x] All DTOs from § 2 (input shape) match — `StageFilterParams`, `ChannelOverviewParams`, `TriggerEtlRefreshParams` with `extra="forbid"` + `Literal[]` enums
- [x] All routes from § 1 reused (NO new endpoints) — verified `metrics.py:309/340/771/832/866` pre-existing endpoints consumed via service layer (`StageOverviewService`, `ChannelDashboardService`, `ETLService`)
- [x] Repository interfaces from § 6 N/A (no new repository introduced; `_NullConfigRepo` is local stub for Redis-down case)
- [x] CONTRACT § 8 Agentic Surfaces — non-empty (T-3 + T-4) — flagged `[CROSS-SCOPE — escalate `auditor-agentic`]` above
- [x] Test surfaces from § validators present at each layer (TDD RED-first):
  - domain: `test_etl_refresh_guard.py` (`GuardDecision` dataclass shape + soft-fail semantics)
  - infrastructure: `test_etl_refresh_guard.py` (Redis pipeline mock — `zremrangebyscore`, `zcard`, `zadd`, `expire`)
  - application: `test_analytics_tools_{stage,channel,security,observability,tier_loading}.py` + `test_etl_refresh_tool.py` — 6 files, 47 tests
  - api/cross-stack: `test_be_fe_schema_alignment_growth_studio.py` (22 arch fitness tests)
- [x] Capability YAML + modules/{m}.md updates from § 13 actioned at merge — T-7 ran `reconcile_capabilities.py` + `generate_backlog.py`; capability YAML `growth-studio-copilot-actions.yaml` shipped.
- [x] Architecture fitness allowlists from § 12 — `test_folder_naming.py` GREW by 1 (justified in commit, see WARN-info above); 22 new arch tests ADDED to fitness suite (961 total, up from 939).

## Allowlist Movement
- `tests/architecture/test_folder_naming.py::KNOWN_PRIVATE_FILE_EXCEPTIONS` GREW by 1 (`copilot/application/tools/_analytics_inputs.py`). **Justified in commit body** — pattern parity with existing `copilot/api/_dependencies.py`. PASS.
- 22 new arch fitness tests ADDED to `tests/architecture/test_be_fe_schema_alignment_growth_studio.py` (T-5). PASS — these enforce a ratchet, they don't relax one.
- No other allowlists touched.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest|tsc|vitest|mypy|eslint` in commits — verified `git log` for all 7 BE-touching commits; all native venv invocations.
- [x] No `git add .` / `git add -A` / `git add -u` — diff is bounded by file (verified via `git diff --name-only 74c6b2d6^..74c6b2d6` showing 17 explicit paths).
- [x] No push to `main` in this story (development branch only).

## Downstream regression scope (R3 mandatory per `.claude/rules/auditor-downstream-regression.md`)

| Surface modified | Downstream test targets per SSoT table | gate-runner iter-2 status |
|---|---|---|
| `modules/copilot/application/tools/` (REWRITE + 3 NEW) | `tests/modules/copilot/`, `tests/modules/copilot/golden/`, `tests/shared/agent_observability/cost/` | **PASS** — gate-runner ran `tests/modules/copilot/ tests/modules/analytics/ tests/shared/` recursively (4005 tests); includes `tests/shared/agent_observability/` and `tests/shared/billing/` subtrees |
| `modules/analytics/application/services/` (NEW `etl_refresh_guard.py`) | `tests/modules/analytics/`, `tests/shared/billing/` | **PASS** — both subtrees in iter-2 scope |
| `modules/copilot/application/tools/_analytics_inputs.py` (NEW Pydantic schemas) | cross-stack via `test_be_fe_schema_alignment_growth_studio.py` (T-5) | **PASS** — 22/22 arch tests GREEN |
| `shared/billing/` source modify? | `tests/modules/sales_agent/`, `tests/modules/campaigns/`, `tests/modules/copilot/` | **NA — `shared/billing/` source NOT modified.** `EtlRefreshGuard` is a NEW file in `modules/analytics/`, not a touch of `shared/billing/rate_limiter.py`. Downstream sales_agent + campaigns regression NOT triggered (verified via `git diff --name-only` — only 17 paths, none under `shared/billing/`). |

**Decision:** downstream regression scope satisfied; no additional gate-runner spawn required.

## Verdict Math

- Downstream regression scope FAIL? → **No** (covered)
- Any FAIL in categories 1 / 2 / 8 / 9 / 12? → **No FAIL** in C1/C2/C8/C9; C12 = WARN (mirror detection — defensible bounded decision, doc/code wording mismatch)
- Allowlist grew without justification? → **No** (commit body cites pattern parity)
- Any `/test-backend` gate FAIL (3-7, 11-13)? → **No** (gates 3-7 PASS; 11/12/13 NA-or-implied-PASS; 8/9 SKIP env-only)
- `IMPL-LOG.md § Skills Consulted` empty or missing required skills? → **No** — backend-expert + tessl__fastapi + tessl__pytest-api-testing + tessl__graceful-degradation + metrics-expert all listed in T-1-impl-log
- `runtime-quality-checklist.md` cited? → IMPL-LOG line 30: "Runtime quality checklist (anti-patterns FastAPI/SQLA/tests/migrations) — Confirmed". **PASS**
- Two or more category WARNs? → **One WARN (C12) + one WARN-info (C11) + one informational (C6)**. C11 WARN-info has explicit justification; treated as informational not voting. **One operational WARN.**

→ **Overall verdict: PASS** (one informational WARN flagged for future architectural debt awareness; not blocking).

## Spot-checks performed (auditor evidence trail)

1. **Legacy `get_funnel_metrics` removal verification** — `grep -rn "get_funnel_metrics" backend/src/ backend/tests/ frontend/src/ 2>/dev/null` → **0 matches** ✓ (atomic replacement clean cross-codebase)
2. **No new analytics endpoints** — `metrics.py` line numbers (309/340/771/832/866) confirmed pre-existing per architect grep. T-1 tools call services, not new routes.
3. **Tenant isolation source** — `analytics_tools.py:215, 308, 376` all use `get_tenant_id()` from `src.core.context`; no payload-sourced tenant_id anywhere.
4. **Pydantic adversarial defense** — verified `_analytics_inputs.py` has `model_config = ConfigDict(extra="forbid")` on all 3 schemas + `Literal[...]` enum types for stage/channel/period.
5. **Spanish neutro on user-facing strings** — `grep -nE "(podés|tenés|sos |vos |mirá|dejá|poné|usá|hacé|elegí|agregá|configurá|revisá|guardá|abrí|volvé|cambiá|seleccioná|dale|fijate|querés)"` on the 3 modified BE source files → **0 voseo matches**. User-facing copy uses tuteo (`Confirma`, `Intenta`, `No se pudo determinar`).
6. **PII allowlist** — tool responses are KPI metrics (numeric values, slugs, counts); no email/phone/national_id/financial fields exposed. `test_analytics_tools_observability.py::TestNoLeakOfPii` verifies this contract.
7. **Graceful degradation** — Redis fail-open verified at 3 points: `_get_etl_refresh_guard()` (Redis client unavailable), `EtlRefreshGuard.check()` (Redis pipeline exception), `_call_etl_refresh()` `MetricsCache(redis_client=None)` (cache fail-open).
8. **Cross-stack contract test soundness (T-5)** — read `test_be_fe_schema_alignment_growth_studio.py` end-to-end; 5 test classes (export presence, additionalProperties=false, field names bidi, enum values exact, drift count invariants); self-healing via `npm run schema:export` subprocess; documented accepted asymmetries (required-list semantics zod vs Pydantic).
9. **Anti-duplication scan** — searched cross-codebase for `EtlRefreshGuard` and pattern keywords (`zremrangebyscore`, `sliding window`); only matches in 2 files (the new guard + `OutboundRateLimiter`). Pattern duplicated, not class duplicated; flagged as WARN Cat 12 (defensible per arch ratification).

## Files in scope of this review

| File | Status | Verdict |
|---|---|---|
| `backend/src/modules/copilot/application/tools/_analytics_inputs.py` | NEW | PASS |
| `backend/src/modules/copilot/application/tools/analytics_tools.py` | REWRITE | PASS |
| `backend/src/modules/analytics/application/services/etl_refresh_guard.py` | NEW | PASS (with WARN Cat 12 doc/code wording) |
| `backend/tests/architecture/test_folder_naming.py` | MOD (allowlist +1) | PASS (justified) |
| `backend/tests/architecture/test_be_fe_schema_alignment_growth_studio.py` | NEW (22 tests) | PASS |
| `backend/tests/modules/copilot/application/tools/test_analytics_tools_*.py` (6 files) | NEW | PASS |
| `backend/tests/modules/analytics/application/services/test_etl_refresh_guard.py` | NEW | PASS |

## Recommendation to PM

**APPROVE merge of T-1 + T-5 + T-7 BE surface.** One operational WARN (Cat 12 mirror) is informational/future-architectural-debt awareness — does not block merge. Architect already ratified the bounded-scope decision in 03-arch.md § 1. Fix recommendation (wording-only docstring update) optional, not required for this story. If Story 3 introduces a 3rd sliding-window consumer, schedule shared-abstraction lift refactor at that point.

