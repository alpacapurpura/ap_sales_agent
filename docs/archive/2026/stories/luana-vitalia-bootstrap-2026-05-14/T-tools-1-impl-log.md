# T-tools-1 — Implementation Log

**Ticket:** Tool `prepaid_payment_check` — deterministic SQL read-only payment verification.
**State:** developing → developed
**R23:** production_code=true AGENTIC tool, Opus 4.7 (Sonnet ban absolute).
**Builder:** Claude Opus 4.7 (1M context)
**Date:** 2026-05-13
**Sesion:** /pm Sesion 3 W5 (last ticket in Q1=D batch)

---

## Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision |
|---|---|---|
| `copilot-expert` | Touching AGENTIC tool surface; observability + tenant isolation patterns required | Consume `sanitize_payload` from `luana_core_observability` shared lib (anti-duplication §0). Tool wraps trace_event_repo with try/except + structlog warning (R23 best-effort observability). Logger uses `event_name=` kwarg pattern. |
| `sales-agent-expert` | Tool dispatched by sales_agent runtime — must respect `LLM_ROLE_BY_SITE` SSoT + tenant isolation cardinal | `tenant_id` MUST NEVER appear in tool input schema (§ 3 cardinal). Repos receive `tenant_id` at construction via tenant-scoped binding. Tool consumes T-be-3 repos (no raw SQL). |
| `tessl__langgraph` | Tool will be consumed as LangChain `Tool` from a LangGraph node (future ticket) | Tool is async; returns Pydantic schema; idempotent natural (read-only). Aligns with LangGraph's `bind_tools()` + structured-output expectations. |
| `tessl__graceful-degradation` | Tool has observability write (trace_event_repo) and 2 repo calls | Trace emission wrapped in try/except — `_RaisingTraceRepo` test confirms turn does NOT break on observability failure. No retry needed for read-only repo lookups (repository layer's responsibility). |
| `tessl__pytest-api-testing` | 10 unit tests with async fixtures + parametrized status modes | Fakes in-memory mirror real `_FakeBookingRepo` / `_FakePaymentIntentRepo` surface. Asyncio_mode=AUTO honored from `pyproject.toml`. p99 latency test = 100 iterations + statistical assertion. |

## Step 0 — Anti-duplication GATE (mandatory per anti-duplication.md §0)

Executed grep audit BEFORE writing implementation:

```bash
# 1. register_tool decorator API
grep -rn "@register_tool\|def register_tool" /home/chris/luana-platform/core/luana-core-extension-sdk/src/
# → No @register_tool decorator — registration is via registry.sales_agent_tool_register(ToolDef(...))
#   in extensions.py. ToolDef.handler is `Callable[..., Any]` (fully flexible signature).

# 2. ToolContext Protocol
grep -rn "class ToolContext\|class ToolBase" /home/chris/luana-platform/core/
# → No ToolContext exists. Tool handlers are plain async callables; tenant_id + session
#   passed as kwargs from caller (sales_agent dispatcher, future ticket).

# 3. sanitize_payload location
grep -rn "def sanitize_payload" /home/chris/luana-platform/core/
# → CANONICAL: luana_core_observability.recording.sanitization::sanitize_payload (line 196)
#   CONSUME via `from luana_core_observability.recording.sanitization import sanitize_payload`

# 4. BaseTraceEventRepoProtocol
grep -rn "BaseTraceEventRepoProtocol" /home/chris/luana-platform/core/
# → CANONICAL: luana_core_observability.persistence.base_trace_event_repo (Protocol)
#   Tool accepts ANY repo implementing this protocol (Structural typing via _TraceEventRepoLike)

# 5. Existing repos for booking + payment_intent
ls /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/repositories/
# → booking_repository.py + payment_intent_repository.py (BOTH T-be-3) consumed via Protocols
#   (decouple from concrete SQLA types — tool tests use fakes)

# 6. Extensions.py wiring
cat /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py | grep "prepaid_payment_check"
# → T-extensions-1 already registered ToolDef with placeholder. This ticket SHIPS the
#   real handler. extensions.py will be wired to import + reference the real handler in
#   T-extensions-2 (future) — placeholder pattern preserves Story 9 frozen contract.
```

**Audit result:** NO mirror risk. All shared abstractions (sanitize_payload, trace repo protocol) consumed from canonical paths. Repositories from T-be-3 consumed via structural Protocol (not concrete SQLA dependency — testable in isolation).

NEW tool (no existing equivalent in `luana-core/`): vertical-medical specific, couples bookings + payment_intents + tenant context. Per 02-design § 6.1: "NEW tool — vertical-medical specific (couples bookings + payment_intents + tenant context). NO equivalente en @luana/core/scheduling (core scheduling doesn't know about payment yet)."

## Implementation

### Files created

| Path | Purpose |
|---|---|
| `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/tools/prepaid_payment_check.py` | Pydantic schemas + async handler + helper functions |
| `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/tools/__init__.py` | Package marker (NEW directory) |
| `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/__init__.py` | Package marker (NEW directory) |
| `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/tools/test_prepaid_payment_check.py` | 10 unit tests (TDD RED → GREEN) |

### Files extended (M8 — extend, no destroy)

| Path | Change |
|---|---|
| `/home/chris/luana-platform/vitalia/backend/conftest.py` | Added `luana_core_extension_sdk/src` + `luana_core_observability/src` to sys.path (same pattern as T-be-1 added for `luana_core_platform`) — workspace packages not pip-installed |

## Tool design decisions

### 1. Handler signature — keyword-only deps (no global registry)

```python
async def prepaid_payment_check(
    input: PrepaidPaymentCheckInput,
    *,
    tenant_id: uuid.UUID,
    booking_repo: _BookingRepoLike,
    payment_intent_repo: _PaymentIntentRepoLike,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> PrepaidPaymentCheckOutput:
```

**Rationale:**
- `tenant_id` keyword-only enforces "NEVER from input" boundary (R12 tenant-isolation).
- `*_repo` parameters via structural Protocol (NOT concrete `BookingRepository` import) — tool is testable in isolation without spinning up SQLAlchemy / Postgres.
- `trace_event_repo` optional — call sites without observability wiring still work (eval/dev).
- Tool composes with the future sales_agent tool dispatcher which injects ctx (tenant_id) + binds repos to tenant.

### 2. Output uniformity — no exception escape from happy paths

Per 02-design § 6.1 error modes (a-c), all "no-result" branches return `PrepaidPaymentCheckOutput(no_payment_initiated=True)` — including foreign-tenant attempts. This is intentional (don't leak booking existence cross-tenant).

DB timeouts >2s land at the repository layer (per 02-design § 6.1 error mode (a)). Repos bubble exceptions; tool does not swallow them — caller decides retry policy.

### 3. Latency p99 budget

10ms typical on fake repos (in-memory). Real production target p99 250ms per spec § 6.1 — measured in integration tests + production trace_event monitoring (V-AE-18, future).

### 4. Currency NEVER hardcoded (currency-handling.md R5)

`PrepaidPaymentCheckOutput.currency` populated from `payment_intents.currency` (ISO 4217 from data source). Never defaults to 'USD'. Test `test_processing_retry_returns_retry_after` asserts ARS currency preserved.

### 5. Gateway normalization

`_normalize_gateway()` validates against `_KNOWN_GATEWAYS` (mercadopago / stripe_connect / tokenized_recurring — mirrors EP-8 channel adapters in `extensions.py`). Unknown gateways → returns `None` (defensive, not exception — logged warning).

## Iteration log

| Iter | RED tests | GREEN tests | Lint | Format | Notes |
|---|---|---|---|---|---|
| 1 | 10/10 fail (module not found) | n/a | n/a | n/a | TDD RED phase — confirmed test scaffolding correct |
| 2 | n/a | 0/10 (sys.path) | n/a | n/a | Conftest extended for `luana_core_observability` + `luana_core_extension_sdk` workspace paths |
| 3 | n/a | 7/10 (Pydantic) | n/a | n/a | `paid` field required → set default False (output ALWAYS has shape) |
| 4 | n/a | **10/10 GREEN** | clean | reformatted | ruff applied: I001 import sort + 2 file reformat |

Final result:

```
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_tenant_id_not_in_schema PASSED [ 10%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_paid_true_succeeded_payment PASSED [ 20%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_processing_retry_returns_retry_after PASSED [ 30%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_failed_payment_returns_failure_reason PASSED [ 40%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_no_payment_initiated_returns_flag PASSED [ 50%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_booking_not_found_returns_flag PASSED [ 60%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_cross_tenant_attempt_returns_no_payment PASSED [ 70%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_trace_event_recorded_when_repo_supplied PASSED [ 80%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_trace_event_failure_does_not_break_turn PASSED [ 90%]
tests/agentic_evals/tools/test_prepaid_payment_check.py::test_latency_p99_under_250ms PASSED [100%]

============================== 10 passed in 0.08s ==============================
```

## Acceptance coverage (per 06-tickets.yaml T-tools-1)

| Acceptance | Test | Result |
|---|---|---|
| A1 — paid_true (succeeded payment_intent → paid=True + amount + currency populated) | `test_paid_true_succeeded_payment` | PASS |
| A2 — processing_retry (processing payment_intent → paid=False + retry_after_seconds) | `test_processing_retry_returns_retry_after` | PASS |
| A3 — tenant_id_not_in_schema (security boundary) | `test_tenant_id_not_in_schema` | PASS (asserts `'tenant_id' not in PrepaidPaymentCheckInput.model_fields`) |
| A4 — latency_p99 (100 invocations, p99 <250ms) | `test_latency_p99_under_250ms` | PASS (in-memory fakes; real DB p99 measured separately V-AE-18 future ticket) |

Plus 6 additional defensive tests:
- failed payment → failure_reason populated
- no payment intent → no_payment_initiated flag
- booking not found / soft-deleted → same flag (no existence leak)
- cross-tenant booking → no_payment_initiated (tenant isolation enforced by repo)
- trace_event recorded with sanitized payload when repo supplied
- trace_event repo raising does NOT break tool turn (R23 best-effort)

## Validators

| ID | Status | Cmd |
|---|---|---|
| V-AE-5 (tools test suite) | **GREEN — 10/10 passed** | `cd backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short` |
| V-AE-18 (trace invariants) | N/A (file does not exist) | Deferred to future observability integration ticket (full Postgres + production trace repo wiring) |

## Patterns honored (per 05-guidelines.md § 1.10 + R23)

- ✅ `try/except + structlog.warning("...persist_failed", exc=str(e))` on observability write (line 295 of tool)
- ✅ `sanitize_payload(...)` BEFORE persist — line 287
- ✅ `tenant_id` from kwarg (caller's ctx injection) NEVER from input schema
- ✅ Idempotency natural (read-only, no side-effects)
- ✅ Async throughout (`async def prepaid_payment_check`)
- ✅ Currency from data source (no hardcoded 'USD')
- ✅ PaymentRepository (T-be-3) consumed — no raw SQL
- ✅ Structlog (no `print()` / `logging.*`)
- ✅ No shared abstraction mirrored

## Decisions honored

- **D1** — Vitalia subdir at `luana-platform/vitalia/` (no separate repo): tool lives in `modules/vitalia/agentic/tools/prepaid_payment_check.py` (per 02-design § 6.1 path).
- All other ticket-relevant decisions (D5 Slot 4 MEDICAL_SAFETY_RAILS, D7 HIPAA-lite, D8 voice cloning, D9 Spanish neutro) are upstream — this ticket's scope is deterministic SQL only (no LLM, no prompts, no voice).

## Halt triggers — none tripped

- ✅ H4 spec drift: SDK contract honored (ToolDef.handler is `Callable[..., Any]` — flexible signature)
- ✅ H5 tenant isolation: tenant_id kwarg-only; repos enforce filter; cross-tenant test PASS
- ✅ H6 PII leak: sanitize_payload consumed (NOT re-implemented), trace payload sanitized pre-persist
- ✅ H10 anti-duplication: no mirror — shared abstractions consumed from canonical paths

## Tech debt / follow-ups

1. **extensions.py wiring** — current registration passes a `_not_implemented_yet()` placeholder. The real handler `prepaid_payment_check` lives in `agentic/tools/prepaid_payment_check.py`. Wiring requires the sales_agent tool dispatcher to:
   - Construct tenant-scoped `BookingRepository` + `PaymentIntentRepository` from `tenant_id` + `AsyncSession`
   - Construct tenant-scoped trace_event_repo + correlation IDs from current turn
   - Call `await prepaid_payment_check(input, tenant_id=..., booking_repo=..., payment_intent_repo=..., trace_event_repo=..., turn_id=..., span_id=...)`

   This wiring is a follow-up ticket (T-extensions-2 or sales_agent dispatcher composition ticket), NOT this ticket's scope. The handler itself is complete + tested.

2. **Integration test (V-AE-18)** — real Postgres + production trace_event repo invariants test (cost_usd > 0 not applicable here — tool is $0 LLM; tokens accounted N/A; PII sanitized check applicable). To be authored once V-AE-18 test file is scaffolded (currently absent).

3. **Latency monitoring** — p99 250ms budget is in-memory only. Production p99 monitoring via copilot_trace_event analytics post-deploy (separate observability ticket).
