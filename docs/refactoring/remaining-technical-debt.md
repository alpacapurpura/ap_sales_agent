# Remaining Technical Debt — Action Plan

> Generated 2026-04-15 after massive debt cleanup session.
> Commit `5dc27a66` is the baseline. All tests pass (2806 backend + 1063 frontend).

---

## What was ALREADY fixed (for context)

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

---

## REMAINING DEBT — ordered by impact

### 1. Cross-Module Imports (62 violations)

**File:** `backend/tests/architecture/test_ddd_boundaries.py` → `KNOWN_CROSS_MODULE_IMPORTS`
**Test:** `test_no_new_cross_module_imports`

#### What they are

62 places where one DDD module imports from another's internals. The ratchet test prevents NEW violations but doesn't fix existing ones.

#### Distribution

```
analytics → connections: 10  (providers need credentials/adapters)
analytics → crm:        15  (repositories JOIN crm tables for stage metrics)
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
sales_agent → crm:        6  (audit, closer_studio, orchestrator, closer service, audit_repo, follow_up)
sales_agent → offer:      2  (knowledge_builder, business_repo)
sales_agent → scheduling:  2  (dto/public_links, sales tools)
scheduling → connections:  1  (availability_service GmailAdapter)
scheduling → crm:         2  (agenda, availability_service Lead)
scheduling → tenant_domains: 1 (booking_url)
```

#### Fix strategies (from audit)

**Strategy A — Already correct DI (7 violations, KEEP):**
These use the ports & adapters pattern correctly. The import is at the API layer for DI wiring.
- `analytics/api/metrics.py` → ConnectionPortImpl, OfferReadPortImpl, BrandReadPortImpl
- `offer/api/campaigns.py` → OfferCampaignsReadAdapter
- `offer/api/counts.py` → AdvertisingReadAdapter

**Strategy B — Create shared ports (estimated 15-20 violations):**
Create port interfaces in `shared/links/ports/` that target modules implement.

Priority ports to create:
1. `shared/links/ports/crm.py` → `CrmReadPort` (Lead, Customer, JourneyEvent read access)
   - Unblocks: analytics repos (7), connections/calendar, scheduling/agenda, scheduling/availability
2. `shared/links/ports/message_routing.py` → `MessageRoutingPort`
   - Unblocks: connections → sales_agent (4 files)
3. `shared/links/ports/channel.py` → `ChannelCredentialPort`
   - Unblocks: analytics providers → connections (partial)

Pattern to follow (already exists):
```
# shared/links/ports/advertising.py — EXISTING example
class AdvertisingReadPort(ABC):
    @abstractmethod
    async def get_campaigns(...) -> list[...]: ...

# offer/api/campaigns.py — wires the adapter via Depends()
from src.modules.advertising.application.services.offer_campaigns_read_adapter import OfferCampaignsReadAdapter
```

**Strategy C — Domain events (estimated 5-8 violations):**
For webhook handlers that create CRM records across modules.
- `connections/api/marketing_webhooks.py` → emit events instead of calling CRM directly
- `analytics/application/services/etl_service.py` → emit OrderProcessedEvent for Shopify backfill
- Requires: event bus infrastructure (check if `shared/domain/events/` exists)

**Strategy D — Intentional cross-cuts (3-5 violations, DOCUMENT):**
Some coupling is inherent to the business domain. Document with inline comments.
- `connections → sales_agent` (message routing hub)
- `sales_agent → crm` (agent needs customer data at runtime)

#### Execution plan

Phase 1 (lowest risk): Create `CrmReadPort` in `shared/links/ports/crm.py`
- Define read-only interface for Lead, Customer, JourneyEvent queries
- Implement in `crm/infrastructure/repositories/` 
- Update analytics repos to use port instead of direct model imports
- Remove fixed entries from `KNOWN_CROSS_MODULE_IMPORTS`
- Run `pytest tests/architecture/test_ddd_boundaries.py -x`

Phase 2: Create `MessageRoutingPort` for connections → sales_agent
Phase 3: Create `ChannelCredentialPort` for analytics → connections
Phase 4: Event-driven webhooks (connections → crm, offer)

---

### 2. Frontend eslint-disable (76 remaining)

**Breakdown:**

| Rule | Count | Status |
|------|-------|--------|
| `sonarjs/cognitive-complexity` | 13 | Documented irreducible — each has comment explaining why |
| `@next/next/no-img-element` | 19 | External/CDN images — needs `next.config.js` remotePatterns |
| `@typescript-eslint/no-explicit-any` | 11 | 8 ReactFlow (genuine need), 3 fixable |
| `react-hooks/exhaustive-deps` | 7 | Audited — intentional dep exclusions |
| `react-hooks/set-state-in-effect` | 7 | SSR hydration patterns — legitimate |
| `max-params` | 5 | Public API signatures — use options objects |
| `react-hooks/static-components` | 5 | Dynamic registry patterns |
| `no-alert` | 2 | Replace with AlertDialog |
| `react-hooks/immutability` | 2 | Browser navigation — legitimate |
| `max-depth` | 1 | SSE parsing — legitimate |

#### Actionable items (not justified suppressions)

**A. `no-img-element` (19) — Configure next/image:**
```js
// next.config.js → images.remotePatterns
{ protocol: 'https', hostname: '**.cloudflare.com' },
{ protocol: 'https', hostname: '**.r2.cloudflarestorage.com' },
// Add patterns for CDN domains used in the app
```
Then replace `<img>` with `<Image>` from `next/image`.

**B. `no-alert` (2):**
Files: `event-type-form.tsx`, one other.
Replace `window.confirm()` with AlertDialog from shadcn (already installed).

**C. `max-params` (5):**
Group function params into options objects. Files:
- `offer-studio/api/index.ts`
- `growth-studio/hooks/useStageDetail.ts`  
- 3 others (check with `grep -rn "max-params" frontend/src/`)

**D. `no-explicit-any` (3 fixable):**
- `-- API payload type mismatch` → define `Partial<FormSchema>`
- 2 without justification → use `unknown` + type guards

---

### 3. Backend `# type: ignore` (35 remaining)

**File:** scattered across `backend/src/`
**Find:** `grep -rn "# type: ignore" backend/src/ --include="*.py"`

Most are in copilot module (union-attr for protocol access). The type:ignore agent started fixing these but introduced a runtime error in `style_analyzer/state.py` that was reverted.

**Key rule:** NEVER move imports to TYPE_CHECKING if the type is used in a TypedDict field or at runtime. Only pure function-signature annotations (with `from __future__ import annotations`) are safe.

Categories:
- `union-attr` (16): Protocol attribute access in copilot — need type narrowing or `cast()`
- `arg-type` (7): SDK type mismatches — use `cast()` with comment
- `assignment` (4): Dynamic function builders — add explicit annotations
- `misc` (3): Reflection/dynamic dispatch
- Others (5): Various

---

### 4. Backend `# noqa` comments (beyond BLE001)

| Type | Count | Action |
|------|-------|--------|
| `F401` (unused imports) | ~40 | Model registration side-effects — KEEP (SQLAlchemy needs them) |
| `ANN401` (dynamic typing) | ~35 | LLM/SDK types — KEEP (genuinely need `Any`) |
| `TRY301` (tryceratops) | ~11 | Style preference — KEEP |
| `BLE001` (broad except) | 126 | Correct error boundaries — KEEP |
| `PLC0415` (import not at top) | ~383 | Circular dep avoidance — KEEP |

**These are NOT debt.** They're intentional suppressions for patterns that ruff flags but are correct in context (FastAPI, SQLAlchemy, LLM orchestration).

---

### 5. Ruff global ignores (45 rules)

**File:** `backend/pyproject.toml` → `[tool.ruff.lint]` → `ignore`

All justified:
- `B008`: FastAPI `Depends()` is not a mutable default
- `PLR2004/PLR0913`: Magic numbers and many-arg functions inherent to DDD
- `E712/E711`: SQLAlchemy requires `== True/None` syntax
- `S105-S108`: OAuth credential patterns, not real secrets
- etc.

**NOT debt. Do not try to enable these.**

---

## Quick verification commands

```bash
# Backend lint (must be 0 errors)
cd backend && .venv/bin/ruff check src/ tests/ --no-cache

# Architecture tests (must all pass)
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short

# Frontend type check (must be 0 errors)
cd frontend && npx tsc --noEmit

# Frontend lint (check for new errors only — warnings are OK)
cd frontend && npx eslint src/ --cache --cache-location .eslintcache

# Full test suites
cd backend && .venv/bin/pytest -x -q --tb=short  # 2806 pass
cd frontend && npx vitest run                      # 1063 pass
```

---

## Files to read before starting

1. This document
2. `backend/tests/architecture/test_ddd_boundaries.py` — the allowlist
3. `backend/tests/architecture/conftest.py` — the smart parser (skips TYPE_CHECKING)
4. `shared/links/ports/advertising.py` — existing port pattern to follow
5. `.claude/rules/backend-ddd.md` — DDD boundary rules
