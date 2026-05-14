# T-tools-1 Result — `qualify_for_cohort` AGENTIC tool

**Ticket:** T-tools-1 — Tool qualify_for_cohort (LLM scoring + lead_qualification_records)
**Surface:** AGENTIC, production_code=true, **Opus 4.7 EXCLUSIVE** (R23)
**Date:** 2026-05-14
**State:** `tests-passing` (awaiting orchestrator → gate-runner → auditor-agentic)
**Validators required:** V-AE-7

---

## § 1. Outcome

13 unit tests **GREEN** on first GREEN run (TDD: RED phase confirmed before
implementation per `.claude/rules/tdd-mandatory.md`).

```
tests/agentic_evals/tools/test_qualify_for_cohort.py .............       [100%]
============================== 13 passed in 0.26s ==============================
```

Full comunify backend regression: **452 passed, 9 skipped, 0 failed**.

Ruff lint + format on scoped files: clean (all checks passed).

---

## § 2. Files created

| Path | Lines | Role |
|---|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | 26 | Package marker — re-exports tool symbols |
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/tools/qualify_for_cohort.py` | ~620 | The tool (handler + Pydantic V1 schemas + protocols + helpers) |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/tools/__init__.py` | 5 | Test package marker |
| `/home/chris/luana-platform/comunify/backend/tests/agentic_evals/tools/test_qualify_for_cohort.py` | ~660 | 13 unit tests covering all T-tools-1 acceptance criteria |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-tools-1-impl-log.md` | n/a | Impl-log (skills consulted, plan, OOS, quality gates output) |
| `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-tools-1-result.md` | n/a | This file |

No files modified outside the ticket scope.

---

## § 3. Test coverage — 13 cases mapped to T-tools-1 acceptance criteria

| # | Test | T-tools-1 criterion | Status |
|---|---|---|---|
| 1 | `test_tenant_id_not_in_schema` | tenant_id NEVER in input (security boundary, ctx-injected) | PASS |
| 2 | `test_schema_version_frozen_v1` | Output Pydantic frozen + `schema_version: Literal[1]` | PASS |
| 3 | `test_happy_path_qualified` | qualified subscriber → record persisted + event emitted | PASS |
| 4 | `test_rejected_below_threshold` | score < threshold → record persisted with `decision='rejected'` + no event | PASS |
| 5 | `test_idempotent_replay_within_window` | same `(cohort_id, subscriber_id, criteria_hash)` → cached result (no new LLM call) | PASS |
| 6 | `test_forbidden_context_community_engagement` | `unqualified_persona`-equivalent ctx → raises `ForbiddenToolContextError` | PASS |
| 7 | `test_forbidden_context_subscriber_support` | additional forbidden context per 03-arch-agentic.md § 4.5 | PASS |
| 8 | `test_pii_sanitized_in_trace_event` | subscriber.email/phone masked in `trace_event` payload | PASS |
| 9 | `test_capacity_full_returns_waitlist_position` | cohort full → `cohort_full=True` + `waitlist_position` populated | PASS |
| 10 | `test_cohort_not_found_returns_not_fit` | cohort_id provided but missing → `fit=False` + gap `cohort_not_found` | PASS |
| 11 | `test_llm_failure_falls_back_to_deterministic` | LLM raises → `fallback_used=True` (graceful-degradation skill) | PASS |
| 12 | `test_trace_event_failure_does_not_break_turn` | trace_event repo raises → tool turn unaffected (best-effort observability) | PASS |
| 13 | `test_event_publisher_failure_does_not_break_turn` | event publisher raises → tool turn unaffected (best-effort emit) | PASS |

All 8 ticket "Test includes" bullets are covered; 5 additional safety/cement cases extend the surface (schema cement, secondary forbidden ctx, capacity, missing cohort, observability fault-tolerance).

---

## § 4. Architecture decisions

### 4.1 LLM client = DI protocol, NOT direct litellm import

**Why:** comunify backend venv currently has neither `litellm` nor `langchain_core` installed (verified via `import litellm` → ModuleNotFoundError). The 03-arch-agentic.md spec aspires to a `luana_core_sales_agent.tools.decorators.register_tool` decorator + a concrete LLM client — neither exists yet in luana-platform.

**Decision:** define `_LLMClientLike` Protocol inline. Caller (T-workflows-2 CohortEnrollmentWorkflow / sales_agent dispatcher) injects the concrete client (LiteLLM adapter, Anthropic SDK direct, etc.) at runtime. Tests use a fake `_FakeLLMClient` that returns canned JSON or raises configured exceptions.

**Anti-duplication threshold (N=2 per `.claude/rules/anti-duplication.md`):** when a SECOND comunify tool calls an LLM, lift `LLMClientProtocol` to a shared agentic abstraction. Today is N=1.

### 4.2 Domain event `LeadQualifiedV1` defined inline

**Why:** comunify has no `modules/comunify/domain/events.py` yet. Defining the
event class inside the tool keeps the surface self-contained and avoids
premature `domain/` layer creation.

**Decision:** Pydantic frozen `@dataclass` inside `qualify_for_cohort.py`.
Lift to `modules/comunify/domain/events.py` when T-workflows-2 introduces
subscribers (CohortEnrollmentWorkflow) OR when a second event type appears
(per N=2 anti-duplication rule).

### 4.3 Output score 0-100 INT (not 0-1 float)

**Why:** `ComunifyLeadQualificationRecordModel.fit_score` is `Integer` (0-100 per
T-be-3 model). 03-arch-agentic.md § 4.1 says `fit_score: float (0-1)` but the
T-tools-1 ticket says "Score range 0-100; threshold from
`comunify/config/brand.yaml cohort_qualification_threshold` default 70".

**Decision:** follow the ticket + DB column (canonical) — output `fit_score: int 0-100`. This avoids a lossy float↔int conversion at the persistence boundary. The spec's float was likely a writing oversight (the ticket explicitly mandates 0-100).

### 4.4 `cohort_qualification_threshold` is a DI parameter today

**Why:** `comunify/config/brand.yaml` does not yet have a
`cohort_qualification_threshold` field. Adding it requires a config schema
bump (out-of-scope per T-tools-1).

**Decision:** threshold default = 70 (per ticket) passed as `threshold` kwarg
to the handler. Caller can override per cohort/per tenant. The brand.yaml
field bump is filed for T-config-2 (out-of-scope notes in impl-log § 4.7).

### 4.5 PII boundary scrub IN TOOL (defense-in-depth)

**Why:** `compliance_event_service.py:55-69` shows the project pattern: lazy import `luana_core_observability.recording.sanitization.sanitize_payload`, fallback to a TRUNCATE-ONLY stub. The fallback does NOT remove email/phone — only truncates long strings. PII slipping through fallback would violate Tessl pii-sanitisation rule.

**Decision:** the tool scrubs PII keys (`email`, `phone`, `mobile`, `ssn`,
`national_id`, etc.) AND uses regex to redact inline emails/phones in free-text
values BEFORE invoking `_sanitize_payload`. Defense-in-depth: even if the
observability fallback runs, the trace payload is PII-free.

### 4.6 Idempotency via DB query, not external cache

**Why:** comunify has no Redis idempotency store wired up in this scope (would
require its own ticket). The LeadQualificationRepository already supports
`list_by_lead(lead_id, limit)`.

**Decision:** idempotency check = query the repo for recent records of this
lead, filter by `(cohort_id, criteria_hash)` where `criteria_hash` is SHA-256
of `lead_data` (stable JSON key order). 1h window enforced in-memory. The
`criteria_hash` is persisted into `lead_data["_criteria_hash"]` for replay
detection on subsequent calls.

This is durable (survives process restart) and matches T-be-5
`CohortService.enroll_member` 24h-window pattern (the qualification window is
shorter — 1h — because criteria/data may change rapidly during a sales call).

### 4.7 Graceful LLM degradation = deterministic rule-based scorer

**Why:** `tessl__graceful-degradation` skill rule: every external call needs
a timeout AND a fallback. The LLM call is wrapped in `asyncio.wait_for(...,
timeout=30)` AND any LLM exception triggers a deterministic scoring fallback.

**Decision:** rule-based scorer counts matched criteria over total criteria
keys. Result range still 0-100 (round to int). Marks `fallback_used=True` in
output + trace + persisted `lead_data` to surface the degraded path to
downstream consumers.

---

## § 5. Skills consulted (Step 0 GATE compliance)

| Skill | Decision captured |
|---|---|
| `sales-agent-expert` | tenant_id NEVER in input schema; ctx-injection; best-effort observability with `try/except + structlog warning + db.rollback()`. |
| `copilot-expert` | Domain event emission protocol; best-effort writes never break turn; PII sanitization mandatory at trace boundary. |
| `tessl__langgraph` | Tool returns Pydantic output, doesn't own LangGraph state — compatible with `Send`+reducer fan-out in T-eval-1+. |
| `tessl__graceful-degradation` | LLM call timeout (30s) + deterministic fallback + log fallback engagement. |
| `tessl__pytest-api-testing` | In-memory fakes (`_FakeCohortRepo`, `_FakeQualificationRepo`, `_FakeLLMClient`); factory pattern; `pytest.mark.asyncio` (`asyncio_mode=auto` from `pyproject.toml`). |

Full discussion in `T-tools-1-impl-log.md § 1`.

---

## § 6. Default-flip detection (Step 0.5)

N/A. No changes to `backend/src/core/config.py` defaults or any feature flag.

---

## § 7. Anti-duplication audit (Step 0 GATE compliance)

```bash
$ find /home/chris/luana-platform -name "qualify_for_cohort.py" 2>/dev/null \
    | grep -v __pycache__ | grep -v .venv
# (none — clean slate)

$ grep -rln "qualify_for_cohort\|QualifyForCohort" /home/chris/luana-platform/ 2>/dev/null \
    | grep -v node_modules | grep -v __pycache__ | grep -v .venv
# only spec docs (03-arch-agentic.md, brand.yaml).
```

Outcome: NEW tool, no mirror risk. New abstractions (LLMClientProtocol, LeadQualifiedV1) defined inline at N=1; lift threshold N=2 honored.

Reused (no mirror):
- `sanitize_payload` from `luana_core_observability.recording.sanitization`
  via the lazy-import-with-fallback pattern (mirrors
  `compliance_event_service.py:55-69`).
- `ComunifyLeadQualificationRecordModel` from existing
  `infrastructure/models/lead_qualification_record_model.py`.
- `LeadQualificationRepository` shape from existing
  `infrastructure/repositories/lead_qualification_repository.py` (via Protocol DI).

---

## § 8. Quality gates output

### 8.1 Pytest (V-AE-7 scope)

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short

tests/agentic_evals/tools/test_qualify_for_cohort.py::test_tenant_id_not_in_schema PASSED [  7%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_schema_version_frozen_v1 PASSED [ 15%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_happy_path_qualified PASSED [ 23%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_rejected_below_threshold PASSED [ 30%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_idempotent_replay_within_window PASSED [ 38%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_forbidden_context_community_engagement PASSED [ 46%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_forbidden_context_subscriber_support PASSED [ 53%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_pii_sanitized_in_trace_event PASSED [ 61%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_capacity_full_returns_waitlist_position PASSED [ 69%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_cohort_not_found_returns_not_fit PASSED [ 76%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_llm_failure_falls_back_to_deterministic PASSED [ 84%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_trace_event_failure_does_not_break_turn PASSED [ 92%]
tests/agentic_evals/tools/test_qualify_for_cohort.py::test_event_publisher_failure_does_not_break_turn PASSED [100%]

============================== 13 passed in 0.27s ==============================
```

### 8.2 Ruff lint (scoped to my files)

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/ruff check src/modules/comunify/agentic/ tests/agentic_evals/tools/ --no-cache
All checks passed!
```

### 8.3 Ruff format (scoped to my files)

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/ruff format --check src/modules/comunify/agentic/ tests/agentic_evals/tools/
7 files already formatted
```

### 8.4 Full comunify backend regression (downstream R3 check)

```
$ cd /home/chris/luana-platform/comunify/backend && \
    .venv/bin/pytest tests/ --tb=short -p no:cacheprovider --override-ini="addopts=" -q
452 passed, 9 skipped in 1.20s
```

Zero downstream regressions. Pre-existing lint warnings in
`tests/integration/test_payment_adapters.py` (unrelated to this ticket — left
intact per `parallel-safety.md` M8).

---

## § 9. OUT-OF-SCOPE (filed for future tickets)

All filed in `T-tools-1-impl-log.md § 4.7`:

1. `register_tool` decorator implementation (depends on
   `luana_core_sales_agent.tools` package — not yet in luana-platform).
2. `modules/comunify/domain/events.py` consolidation (lift `LeadQualifiedV1`
   when T-workflows-2 introduces 2nd event consumer).
3. `comunify/config/brand.yaml::cohort_qualification_threshold` field add
   (T-config-2 scope).
4. CohortEnrollmentWorkflow subscriber wiring of `LeadQualifiedV1`
   (T-workflows-2 scope).
5. Real LiteLLM/Anthropic SDK install in comunify venv (depends on the
   workflow ticket that needs LLM dispatch — caller-layer concern).
6. OfferLadder tier-mapping refinement (currently placeholder
   `level_1..level_4` from score buckets; T-extractors-1
   `OfferLadderAdvisor` finalizes).
7. Pre-existing lint warnings in `tests/integration/test_payment_adapters.py`
   (8 errors, unused-imports) — NOT in T-tools-1 scope.

---

## § 10. Commits

To be committed by the orchestrator's commit-push delegate (Haiku per
`.claude/rules/git-haiku-delegation.md`). Suggested message:

```
feat(comunify/agentic): T-tools-1 add qualify_for_cohort tool + 13 unit tests

- Pydantic V1 frozen schemas (Input/Output) with schema_version: Literal[1]
- tenant_id NEVER in input — ctx-injected per tenant-isolation.md
- LLM client via Protocol DI (N=1; lift to shared at N=2)
- Idempotency 1h window via criteria_hash in lead_data JSONB
- Graceful LLM degradation → deterministic rule-based scorer
- PII boundary scrub (defense-in-depth) before sanitize_payload
- LeadQualifiedV1 domain event emit (best-effort, no break on failure)
- Persists ComunifyLeadQualificationRecordModel via injected repo
- 13/13 tests GREEN; ruff clean; 452 regression tests still green

Story: luana-comunify-bootstrap
Ticket: T-tools-1 (R23 Opus 4.7 exclusive — production_code=true agentic)
Validators: V-AE-7
```

Files to stage:
- `luana-platform/comunify/backend/src/modules/comunify/agentic/tools/__init__.py`
- `luana-platform/comunify/backend/src/modules/comunify/agentic/tools/qualify_for_cohort.py`
- `luana-platform/comunify/backend/tests/agentic_evals/tools/__init__.py`
- `luana-platform/comunify/backend/tests/agentic_evals/tools/test_qualify_for_cohort.py`
- `docs/product/stories/luana-comunify-bootstrap/T-tools-1-impl-log.md`
- `docs/product/stories/luana-comunify-bootstrap/T-tools-1-result.md`

---

## § 11. Return

`done -> docs/product/stories/luana-comunify-bootstrap/T-tools-1-result.md`
