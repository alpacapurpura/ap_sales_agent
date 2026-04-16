# Remaining Technical Debt — Action Plan

> Updated 2026-04-15. Baseline: commit `5dc27a66`.
> All tests pass: 2806 backend + 1063 frontend. 0 lint errors.

---

## Cleanup history

### Session 1 (commit `5dc27a66`)

| Category | Before | After | How |
|----------|--------|-------|-----|
| USD hardcoded defaults | 13 files | 0 | `FALLBACK_CURRENCY` constant in `shared/domain/currency.py` |
| `datetime.utcnow()` | 1 file | 0 | Already using `func.now()` |
| Stray DDD files | 1 | 0 | `landing/schemas.py` → `landing/api/schemas.py` |
| Catalog-contract gaps | 17 | 0 | Derived metrics → `providers=()` |
| BLE001 broad exceptions | 148 | 126 | 22 replaced with specific types; 126 are correct error boundaries |
| `@ts-ignore` | 8 | 1 | → `@ts-expect-error` with comments |
| `@explicit-any` | 46 | 11 | Typed API responses; 8 ReactFlow/RHF justified |
| `exhaustive-deps` | 20 | 7 | Fixed or audited as intentional |
| `cognitive-complexity` | 27 | 13 | 4 refactored; 13 documented irreducible |
| Arch test parser | catches TC imports | skips TC | `conftest.py` now has `_type_checking_line_ranges()` |
| Cross-module imports | 65 | 62 | 3 TYPE_CHECKING-only removed |

### Session 2 (current)

| Category | Before | After | How |
|----------|--------|-------|-----|
| `@next/next/no-img-element` | 20 | **0** | `next.config.js` remotePatterns + all `<img>` → `<Image>` with `unoptimized` |
| `no-alert` | 2 | **0** | `window.confirm()` → AlertDialog (shadcn); `prompt()` → Dialog + Input |
| `no-explicit-any` (unjustified) | 3 files | **0** | Test files: removed unnecessary file-wide disable (warn in tests). Config: consolidated to 1 type alias |
| Backend `# type: ignore` | 14 | **4** | `cast()` with TYPE_CHECKING imports (5), `Callable` typing fix (4), proper annotation (1) |

---

## REMAINING DEBT — ordered by impact

### 1. Cross-Module Imports (58 violations)

**File:** `backend/tests/architecture/test_ddd_boundaries.py` → `KNOWN_CROSS_MODULE_IMPORTS`
**Test:** `test_no_new_cross_module_imports`
**Status:** Ratchet test prevents new violations. Existing 58 entries need phased port creation.

#### Distribution

```
analytics → connections: 11  (providers need credentials/adapters)
analytics → crm:        12  (repositories JOIN crm tables for stage metrics)
analytics → brand:       1  (BrandReadPort DI)
analytics → offer:       2  (OfferReadPort DI, ETL product mapping)
connections → analytics:  3  (channel_info, webhooks, connection_port_impl)
connections → crm:        2  (calendar Lead, webhook lifecycle)
connections → offer:      1  (webhook product mapping)
connections → sales_agent: 4 (message routing: meta, telegram, webhook, whatsapp)
connections → scheduling:  1  (calendar booking)
offer → copilot:          1  (offer_ai)
offer → crm:              1  (product_mappings JourneyEvent/Sale)
offer → advertising:      2  (OfferCampaignsReadAdapter DI)
sales_agent → brand:      1  (knowledge_builder)
sales_agent → connections: 3  (orchestrator, channel_resolver, channel_service)
sales_agent → crm:        5  (audit, closer_studio, orchestrator, closer service, follow_up)
sales_agent → offer:      2  (knowledge_builder, business_repo)
sales_agent → scheduling:  2  (dto/public_links, sales tools)
scheduling → connections:  1  (availability_service GmailAdapter)
scheduling → crm:         2  (agenda, availability_service Lead)
scheduling → tenant_domains: 1 (booking_url)
```

#### Fix strategies

**Strategy A — Already correct DI (7 violations, KEEP):**
Ports & adapters pattern. Import at API layer for DI wiring — architecturally correct.
- `analytics/api/metrics.py` → ConnectionPortImpl, OfferReadPortImpl, BrandReadPortImpl
- `offer/api/campaigns.py` → OfferCampaignsReadAdapter
- `offer/api/counts.py` → AdvertisingReadAdapter

**Strategy B — Create shared ports (15-20 violations):**
Port interfaces in `shared/links/ports/`. Pattern: `shared/links/ports/advertising.py`.

| Priority | Port | Unblocks |
|----------|------|----------|
| 1 | `CrmReadPort` (Lead, Customer, JourneyEvent) | analytics repos (7), connections/calendar, scheduling/agenda+availability |
| 2 | `MessageRoutingPort` | connections → sales_agent (4) |
| 3 | `ChannelCredentialPort` | analytics providers → connections (partial) |

**Strategy C — Domain events (5-8 violations):**
Webhook handlers creating CRM records across modules. Requires event bus in `shared/domain/events/`.

**Strategy D — Intentional cross-cuts (3-5 violations, DOCUMENT):**
Inherent business coupling. Document with inline comments.
- `connections → sales_agent` (message routing hub)
- `sales_agent → crm` (agent needs customer data at runtime)

#### Execution plan

Phase 1: Create `CrmReadPort` in `shared/links/ports/crm.py` (~10 violations)
Phase 2: Create `MessageRoutingPort` (~4 violations)
Phase 3: Create `ChannelCredentialPort` (~5 violations)
Phase 4: Event-driven webhooks (~5 violations)

---

### 2. Frontend eslint-disable (53 remaining — all justified)

Every remaining suppression has a documented justification comment.

| Rule | Count | Status |
|------|-------|--------|
| `sonarjs/cognitive-complexity` | 14 | Documented irreducible — each has comment |
| `@typescript-eslint/no-explicit-any` | 9 | 7 ReactFlow (genuine need), 1 RHF resolver, 1 plugin registry |
| `react-hooks/exhaustive-deps` | 7 | Audited — intentional dep exclusions |
| `react-hooks/set-state-in-effect` | 7 | SSR hydration patterns — legitimate |
| `max-params` | 7 | Public API signatures — all have justification comments |
| `react-hooks/static-components` | 5 | Dynamic registry patterns |
| `react-hooks/immutability` | 2 | Browser navigation — legitimate |
| `max-depth` | 1 | SSE parsing — legitimate |
| `@typescript-eslint/consistent-type-imports` | 1 | Framework constraint |

**No actionable items remain.** All suppressions are either:
- Technically irreducible (cognitive-complexity in complex orchestrators)
- Framework-mandated (ReactFlow types, SSR hydration, Next.js navigation)
- Audited and intentional (exhaustive-deps, set-state-in-effect)

---

### 3. Backend `# type: ignore` (4 remaining — all justified)

| File | Code | Justification |
|------|------|---------------|
| `copilot/application/orchestrator/context_budget.py:21` | `[misc]` | Function redefinition in `except` block — standard tiktoken fallback pattern |
| `brand/application/agents/style_analyzer/nodes.py:345` | `[misc]` | `_style_store` is injected infra dependency, intentionally absent from TypedDict |
| `analytics/application/dto/attraction_dto.py:68` | `[misc]` | Pydantic v2 `@computed_field` + `@property` — known mypy limitation |
| `analytics/application/services/stage_services/overview_stage.py:174` | `[arg-type]` | MetricsService uses legacy sync Session; rare on-demand fallback path |

**No actionable items remain.** Each is a genuine type system limitation with documented reason.

---

### 4. Backend `# noqa` comments — NOT DEBT

| Type | Count | Reason |
|------|-------|--------|
| `F401` (unused imports) | ~40 | SQLAlchemy model registration side-effects |
| `ANN401` (dynamic typing) | ~35 | LLM/SDK types genuinely need `Any` |
| `TRY301` (tryceratops) | ~11 | Style preference |
| `BLE001` (broad except) | 126 | Correct error boundaries |
| `PLC0415` (import not at top) | ~383 | Circular dependency avoidance |

**Intentional suppressions. Do not try to remove.**

---

### 5. Ruff global ignores (45 rules) — NOT DEBT

**File:** `backend/pyproject.toml` → `[tool.ruff.lint]` → `ignore`

All justified: `B008` (FastAPI Depends), `PLR2004/PLR0913` (DDD patterns), `E712/E711` (SQLAlchemy), `S105-S108` (OAuth), etc.

**Intentional configuration. Do not try to enable.**

---

## Quick verification commands

```bash
# Backend lint (must be 0 errors)
cd backend && .venv/bin/ruff check src/ tests/ --no-cache

# Architecture tests (must all pass — currently 71)
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short

# Frontend type check (must be 0 errors)
cd frontend && npx tsc --noEmit

# Frontend lint (0 new errors — warnings OK)
cd frontend && npx eslint src/ --cache --cache-location .eslintcache

# Full test suites
cd backend && .venv/bin/pytest -x -q --tb=short  # 2806 pass
cd frontend && npx vitest run                      # 1063 pass
```

---

## Only remaining work: Cross-Module Imports (Section 1)

The only actionable debt left is the 58 cross-module import violations — a phased architectural refactoring requiring shared ports. Everything else is either fixed or documented as intentionally kept.

### Files to read before starting port work

1. `backend/tests/architecture/test_ddd_boundaries.py` — the allowlist
2. `backend/tests/architecture/conftest.py` — TYPE_CHECKING parser
3. `shared/links/ports/advertising.py` — existing port pattern
4. `.claude/rules/backend-ddd.md` — DDD boundary rules
