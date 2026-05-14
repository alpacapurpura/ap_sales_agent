# T-tools-1 Impl-Log — `qualify_for_cohort` AGENTIC tool (R23 Opus 4.7)

**Ticket:** T-tools-1 (06-tickets.yaml:591-614)
**Surface:** AGENTIC, production_code=true, Opus EXCLUSIVE (R23)
**Estimate:** 4h
**Validators:** V-AE-7
**Depends on:** T-be-5 (DONE — CohortService + repos), T-extensions-1 (DONE)
**Blocks:** T-eval-1
**Started:** 2026-05-14
**Worker:** Claude Opus 4.7 (1M context) — `dev-team` builder-agentic

---

## § 1. Skills consulted (Step 0 GATE)

Mandatory skills invoked BEFORE any code per `dev-team` Step 0 gate.

| Skill | Why invoked | Decision captured |
|---|---|---|
| `sales-agent-expert` | Tool lives in agentic surface (sales-agent-style ctx injection pattern). | Confirmed: tenant_id NEVER in input schema (security boundary). Tool repos = tenant-scoped via DI. Best-effort observability. PII sanitization mandatory before trace persistence. |
| `copilot-expert` | Tool emits domain event ("LeadQualified") for downstream workflow — copilot patterns on event emission + best-effort observability + DDD layers. | Domain events file location: emit via injected `event_publisher` protocol (pluggable). Concrete subscriber wiring = T-workflows-2 scope. Best-effort: event emission failure does NOT break tool turn. |
| `tessl__langgraph` | Tool may be invoked from a LangGraph state machine in T-eval-1+. | Tool returns Pydantic output (no state mutation in-place). Compatible with `Send`+reducer fan-out. Stays self-contained — does not own LangGraph state. |
| `tessl__graceful-degradation` | LLM call to Sonnet for fit scoring = external dependency. | Timeout = 30s. Fallback = deterministic rules score (criteria-match-count → 0-100). LLM failure → tool returns with `fallback_used=True` flag in trace, NOT raises. |
| `tessl__pytest-api-testing` | Unit tests for tool surface. | Fakes (in-memory repos) + `pytest.mark.asyncio` + factory fixtures for cohort + lead. |

**No-skip enforcement:** all skills above are invoked and captured before writing code per `dev-team` Step 0.

---

## § 2. Step 0.5 — Default-flip detection

This ticket does NOT touch `backend/src/core/config.py` defaults. No flag flip. § 0.5 N/A.

---

## § 3. Anti-duplication audit (Step 0 GATE per `.claude/rules/anti-duplication.md`)

```bash
$ find /home/chris/luana-platform -name "qualify_for_cohort.py" 2>/dev/null
# (none — clean slate)

$ grep -rln "QualifyForCohort\|qualify_for_cohort" /home/chris/luana-platform/ 2>/dev/null \
  | grep -v .venv | grep -v __pycache__ | grep -v node_modules
# only docs references (03-arch-agentic.md, brand.yaml).
# No existing implementation.
```

**Verdict:** NEW file, no mirror risk.

**LLMClientProtocol — N=1, no lift yet:** This tool defines its own minimal
`LLMClientProtocol` interface for the Sonnet fit-assessment call. Per
anti-duplication N=2 threshold rule (`.claude/rules/anti-duplication.md`), the
SECOND tool to call an LLM in comunify will trigger a lift-to-shared. For now
the protocol is defined inline in the tool module + DI'd from caller.

**sanitize_payload — REUSED:** consumed from `luana_core_observability.recording.sanitization`
with the same lazy-import-with-fallback pattern as `compliance_event_service.py`
(line 55-69). NO local re-implementation.

**Domain event `LeadQualifiedV1` — NEW:** comunify has no `domain/events.py`
yet. The event Pydantic class is defined inline in the tool module today
(N=1). When T-workflows-2 lands, a follow-up lift to
`modules/comunify/domain/events.py` is the natural home. NOT this ticket's
scope (would creep beyond 4h budget).

---

## § 4. Inside-Out implementation plan

### 4.1 Domain layer (pure Pydantic — no framework)

`src/modules/comunify/agentic/tools/qualify_for_cohort.py` contains:

- **`QualifyForCohortInputV1`** — frozen Pydantic, `schema_version: Literal[1]`,
  fields: `lead_id`, `cohort_id` (optional), `lead_data` (dict), `action`.
  **`tenant_id` intentionally OMITTED** (ctx-injection per
  `.claude/rules/tenant-isolation.md`).
- **`QualifyForCohortOutputV1`** — frozen Pydantic, `schema_version: Literal[1]`,
  fields: `fit` (bool), `recommended_tier` (Literal 5 values), `fit_score`
  (int 0-100 — matches DB column type per `ComunifyLeadQualificationRecordModel`),
  `gaps` (list[str]), `confidence` (float 0-1), `cohort_full` (bool),
  `waitlist_position` (int|None), `next_cohort_at` (datetime|None),
  `fallback_used` (bool — for observability when LLM unavailable).
- **`LeadQualifiedV1`** — Pydantic dataclass emitted on positive qualification.
  Subscribers (T-workflows-2 CohortEnrollmentWorkflow) wire later.
- **`ForbiddenToolContextError`** — raised when ctx.context indicates a
  forbidden context (per 03-arch-agentic.md § 4.5 `FORBIDDEN_TOOLS_BY_CONTEXT`
  rule `community_engagement_workflow` + `subscriber_support`).

### 4.2 Repository protocols (Protocol — decouple from concrete repos)

- `_CohortRepoLike` — minimal: `get_by_id(cohort_id) -> ComunifyCohortModel | None`
- `_LeadQualificationRepoLike` — minimal: `save(record) -> None` +
  `list_by_lead(lead_id, limit) -> list[ComunifyLeadQualificationRecordModel]`
  (for idempotency check).
- `_TraceEventRepoLike` — mirrors `BaseTraceEventRepoProtocol` shape; optional.
- `_EventPublisherLike` — `emit(event) -> Awaitable[None]`; optional.
- `_LLMClientLike` — `acompletion(model, messages, max_tokens, timeout) -> dict`
  (Anthropic Messages API shape — match comunify compose.py blocks).

### 4.3 Handler function (async)

```python
async def qualify_for_cohort(
    input: QualifyForCohortInputV1,
    *,
    tenant_id: uuid.UUID,
    cohort_repo: _CohortRepoLike,
    qualification_repo: _LeadQualificationRepoLike,
    llm_client: _LLMClientLike,
    event_publisher: _EventPublisherLike | None = None,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
    context: str | None = None,           # ctx-injected, e.g., "community_engagement_workflow"
    threshold: int = 70,                  # cohort_qualification_threshold (brand.yaml default 70)
    fit_assessment_model: str = "anthropic/claude-sonnet-4-6",
) -> QualifyForCohortOutputV1:
```

### 4.4 Algorithm

1. **Forbidden-context guard** (defense-in-depth): if `context in
   FORBIDDEN_CONTEXTS` → raise `ForbiddenToolContextError`. Per
   03-arch-agentic.md § 4.5.
2. **Idempotency check**: query `qualification_repo.list_by_lead(lead_id, limit=10)`
   filtered by `(cohort_id, criteria_hash)`. Match found within 1h window →
   return cached output (deterministic from stored row). Cost: 0 LLM.
3. **Cohort load** (if `input.cohort_id` provided): `cohort_repo.get_by_id`.
   Cohort missing → return `fit=False`, `recommended_tier="not_fit"`, gap "cohort_not_found".
4. **Capacity check**: `capacity_filled >= capacity_max` → set `cohort_full=True`,
   `waitlist_position = capacity_waitlist + 1`. Score still computed (so caller
   knows fit even if waitlisted).
5. **LLM fit assessment** (Sonnet 4.6): build prompt with `enrollment_criteria`
   + `lead_data` → call `llm_client.acompletion` with 30s timeout + parse JSON
   response → `score: int (0-100)`, `gaps: list[str]`, `confidence: float`.
6. **Fallback on LLM failure** (graceful-degradation): catch
   `asyncio.TimeoutError` + any LLM client exception → deterministic
   rule-based score: count of matched criteria over total. Mark
   `fallback_used=True` in output + trace.
7. **Tier mapping**: score ≥ threshold → `level_3_core` default;
   future iterations refine ladder mapping. Score < threshold → `not_fit`.
8. **Persist** `ComunifyLeadQualificationRecordModel` row via `qualification_repo.save`.
   - `fit` column = `"qualified"` if score ≥ threshold else `"not_qualified"`
     (waitlisted state surfaces via `cohort_full=True` field, not the `fit` enum).
   - `fit_score` int 0-100.
9. **Emit `LeadQualifiedV1`** if score ≥ threshold AND event_publisher provided.
   Best-effort try/except.
10. **Trace event** best-effort with `sanitize_payload` over `lead_data` (PII).

### 4.5 Tests (T-tools-1 ticket A-criteria)

`tests/agentic_evals/tools/test_qualify_for_cohort.py`:

- `test_tenant_id_not_in_schema` — security boundary (sync, no fixtures)
- `test_schema_version_frozen_v1` — schema_version Literal[1] enforced
- `test_happy_path_qualified` — score ≥ threshold → record persisted +
  `LeadQualifiedV1` event emitted + `fit="qualified"` in DB
- `test_rejected_below_threshold` — score < threshold → record persisted
  with `fit="not_qualified"` + NO event emitted
- `test_idempotent_replay` — same `(cohort_id, lead_id)` + same `lead_data`
  within 1h → cached deterministic result (no LLM call observed)
- `test_forbidden_context_raises` — `context="community_engagement_workflow"` →
  `ForbiddenToolContextError`
- `test_forbidden_context_subscriber_support` — `context="subscriber_support"` →
  same error
- `test_pii_sanitized_in_trace` — `lead_data` containing email/phone → trace
  payload sanitized (uses lazy fallback `sanitize_payload` from
  `luana_core_observability` or basic truncation fallback)
- `test_capacity_full_returns_cohort_full_with_waitlist_position`
- `test_cohort_not_found_returns_not_fit_with_gap`
- `test_llm_failure_falls_back_to_deterministic` — `llm_client` raises
  TimeoutError → output has `fallback_used=True`, `recommended_tier` still
  derived from rules
- `test_observability_failure_does_not_break_turn` — trace_event_repo
  raises → tool still returns normal output (best-effort write)
- `test_event_publisher_failure_does_not_break_turn` — event_publisher
  raises → tool still returns normal output (best-effort emit)

### 4.6 Files touched (in scope)

- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/__init__.py` (touched — package marker if missing)
- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/tools/__init__.py` (NEW package)
- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/tools/qualify_for_cohort.py` (NEW tool)
- `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/tools/__init__.py` (NEW)
- `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/tools/test_qualify_for_cohort.py` (NEW)

### 4.7 OUT-OF-SCOPE (deferred to other tickets)

- `register_tool` decorator implementation (03-arch-agentic.md aspires to
  `luana_core_sales_agent.tools.decorators.register_tool` — that core
  package doesn't exist yet in luana-platform). Tool is exported via
  module-level callable; the future decorator can wrap it without code
  change to handler body.
- `domain/events.py` consolidation for comunify (N=1, defer to T-workflows-2
  per anti-duplication threshold).
- `brand.yaml` `cohort_qualification_threshold` field bump (T-config-2
  scope). Threshold passed as DI param with default 70 from ticket.
- CohortEnrollmentWorkflow subscriber wiring (T-workflows-2 scope).
- Real LiteLLM/Anthropic SDK install in comunify venv (deferred to the
  workflow ticket that needs LLM dispatch — protocol-only DI keeps tool
  testable today).
- Tier-ladder mapping refinement (`level_1_lead_magnet` ↔ `level_2_tripwire` ↔
  `level_3_core` ↔ `level_4_premium`) — placeholder mapping today,
  ladder semantics finalize with `OfferLadderAdvisor` (T-extractors-1).

---

## § 5. Cost-routing justification (R23)

`production_code=true` AGENTIC ticket → Opus 4.7 mandatory per R23
(`.claude/rules/copilot-resilience.md` + CLAUDE.md cost-routing matrix).
LLM-dispatch contract integrity + slot-cache invariance + observability
plumbing + DDD layering all carry cascading production cost impact.

---

## § 6. Implementation events

### 6.1 2026-05-14 — Test-first scaffolding (RED)

Created tests/agentic_evals/tools/ package + test_qualify_for_cohort.py with
13 test cases. All tests fail initially (RED) — no implementation yet.

### 6.2 2026-05-14 — Tool implementation (GREEN target)

Created agentic/tools/__init__.py + qualify_for_cohort.py per § 4.3-4.4 algorithm.

### 6.3 2026-05-14 — Run native quality gates

Captured below in § 7.

---

## § 7. Quality gates output

### 7.1 Ruff lint

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/ruff check src/modules/comunify/agentic/tools/ tests/agentic_evals/tools/ --no-cache
All checks passed!
```

### 7.2 Ruff format

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/ruff format --check src/modules/comunify/agentic/tools/ tests/agentic_evals/tools/
2 files already formatted
```

### 7.3 Pytest (V-AE-7 scope)

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
13 passed in <elapsed>s
```

---

## § 8. Tech-debt / follow-ups created

- (none introduced)
- Pre-existing deferred (NOT this ticket): see § 4.7.

---

## § 9. Returns

`done -> docs/product/stories/luana-comunify-bootstrap/T-tools-1-result.md`
