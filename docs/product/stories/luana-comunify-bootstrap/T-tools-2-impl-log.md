# T-tools-2 IMPL-LOG — `link_to_community` tool

**Date:** 2026-05-14
**Surface:** AGENTIC (R23 — `production_code=true`, Opus 4.7 EXCLUSIVE)
**Ticket:** [T-tools-2](06-tickets.yaml#L617)
**Story:** luana-comunify-bootstrap
**Estimate:** 3h | **Actual:** ~1.5h

## State on entry

- Branch: `development` (per parallel-safety.md)
- Tree dirty with other-session WIP (untouched) — only my files staged
- Baseline `tests/agentic_evals/tools/`: **13 passed** (T-tools-1 only)

## Skills Consulted (R30 Step 0 GATE)

| Skill | Decision captured |
|---|---|
| `copilot-expert` | §0 anti-duplication cardinal: ran `find -name "link_to_community.py"` + `grep -rn "class LinkToCommunity"` cross-codebase. No match. HMAC signed-URL pattern is comunify-specific (subscriber invite). No shared abstraction exists in `shared/agent_observability/` nor in `luana_core_*` packages → N=1 inline OK. PII scrub uses lazy `luana_core_observability.sanitization.sanitize_payload` reuse pattern from T-tools-1 sibling. Observability is best-effort try/except + structlog warning. |
| `sales-agent-expert` | §0 anti-duplication: confirmed no mirror in sales_agent codebase. Schema cementation: `schema_version: Literal[1]` + `ConfigDict(frozen=True)` on Output. Reused PII scrub pattern from T-tools-1. Cache-friendly prompt for suggest_path: system block invariant (no tenant_id interpolation, no timestamps). |
| `tessl__langgraph` | N/A — tool returns dict-like Pydantic output; no StateGraph node ownership. Tool is consumed BY a graph (sales_agent/copilot orchestrator), not a graph itself. |
| `tessl__graceful-degradation` | LLM (`suggest_path` Haiku) wrapped in `asyncio.wait_for(..., timeout=15s)` + deterministic heuristic fallback (`_deterministic_tier_suggestion`). HMAC sign/verify is pure CPU — no timeout. audit + trace + member persistence ALL wrapped try/except + warning (3 best-effort paths × never break turn). `MissingHMACSecretError` raised explicitly when env unset (defense-in-depth: silent fallback would defeat URL signing). |
| `tessl__pytest-api-testing` | Factory-style fakes (`_FakeCohortMember`, `_FakeCohortMemberRepo`, `_FakeAuditLogRepo`, `_RaisingAuditLogRepo`, `_CapturingTraceRepo`, `_RaisingTraceRepo`, `_FakeLLMClient`). Function-scoped fixtures (`@pytest.fixture(autouse=True)` for HMAC env). `_now` injection point for time-based testing without `time.sleep`. Response shape asserted (not just status code) — URL parsing + HMAC recomputation + audit row content. parametrize not needed (13 distinct test cases isolated). |
| `tessl__fastapi` | N/A — pure tool module, no FastAPI route in T-tools-2 scope. |

## Step 0.5 — Default flip detection

N/A — no `backend/src/core/config.py` defaults flipped. New tool only.

## Step 0 — Anti-duplication audit (R-anti-dup cardinal)

```bash
# 1. find existing link_to_community.py — none
find /home/chris/luana-platform -name "link_to_community.py" 2>/dev/null
# → no output

# 2. class LinkToCommunity*
grep -rn "class LinkToCommunity\|class LinkToCommunityInput\|class LinkToCommunityOutput" \
  /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# → only spec docs (03-arch-agentic.md § 4.2)

# 3. HMAC signer + invite URL pattern
grep -rn "_hmac_token\|build_signed_url\|COMUNIFY_INVITE_SECRET" \
  /home/chris/luana-platform/core/ /home/chris/AISALESHT/backend/src/shared/ 2>/dev/null
# → none

# 4. Verified candidate shared abstractions inventory:
#    - shared/agent_observability/: observability + cost only, no URL signer
#    - luana_core_observability: sanitization only
#    - luana_core_extension_sdk: ExtensionPointRegistry, no crypto
# Decision: N=1 inline → ok per `.claude/rules/anti-duplication.md`.
# If future vertical (vitalia + future) needs signed URLs → trigger lift to
# `luana_core_invite` shared package.
```

## Step 0 — N=2 trigger flagged (deferred lift)

`ForbiddenToolContextError` is defined in BOTH:
- `modules/comunify/agentic/tools/qualify_for_cohort.py` (T-tools-1, N=1)
- `modules/comunify/agentic/tools/link_to_community.py` (T-tools-2, N=2 — trigger)

Per `.claude/rules/anti-duplication.md` cardinal: N=2 → LIFT. **Deferred** out of
T-tools-2 scope (would require editing T-tools-1's file). Recommended next:

- Create `modules/comunify/agentic/tools/_exceptions.py` with single canonical
  `ForbiddenToolContextError(Exception)`. Both tool files import + re-export.
- Update `__init__.py` to expose the canonical version.
- Trigger ticket: T-tools-refactor-N2 (PM ratification needed).

Flagged here so the next ticket (T-tools-3 nurture_via_authority_content) does
NOT inline a third copy. **N=3 trigger would be a process-improvement case study.**

## Files written

- `comunify/backend/src/modules/comunify/agentic/tools/link_to_community.py` (NEW, 643 lines)
- `comunify/backend/tests/agentic_evals/tools/test_link_to_community.py` (NEW, 678 lines)
- `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` (EXTEND, +12 exports)

## Files NOT touched (scope discipline)

- `comunify/backend/src/modules/comunify/extensions.py` — `_not_implemented_yet` handler for `link_to_community` left in place. T-tools-1 sibling did the same. EP-3 wire-up is a separate concern (likely a follow-up `T-wiring-N` per `T-tools-1-result.md` pattern).
- Any module outside `agentic/tools/` and the test mirror.

## Implementation notes

### 4-action dispatcher

Single `link_to_community()` entry point branches on `input.action` into:
- `_handle_invite_action` — `generate_invite` + `resend_invite` share the URL-minting + persistence machinery; only the idempotency cache key + audit action label differ. 5-min replay via in-process LRU.
- `_handle_verify_access` — HMAC compare_digest + expiry check + member.status defense-in-depth (`{dropped, suspended, revoked}` blocked even with valid HMAC).
- `_handle_suggest_path` — Haiku LLM call wrapped in `wait_for(..., 15s)` + deterministic `_deterministic_tier_suggestion` fallback (uses `business_stage` heuristic, existing membership upgrade path).

### HMAC URL signing

```python
hmac.new(
    key=COMUNIFY_INVITE_SECRET.encode("utf-8"),
    msg=f"{tenant_id}:{subscriber_id}:{exp}".encode("utf-8"),
    digestmod=hashlib.sha256,
).hexdigest()
```

Cross-tenant tokens produce different digests → `verify_access` under wrong tenant returns False (T7 explicit test). Uses `hmac.compare_digest()` to avoid timing leaks.

### Cache architecture

In-process module-level `_INVITE_CACHE` keyed by `(tenant_id, subscriber_id, cohort_id, action)`. 5-min TTL via `_CachedInvite.cached_at` + `now - cached_at >= _IDEMPOTENCY_WINDOW`. Matches T-tools-1's 1h pattern (different window per spec § 4.2).

Production note: in-process cache means a multi-worker deploy can produce 2 different URLs within window across workers. Acceptable for v1; if observed pain → lift to Redis-backed shared cache (Story 11 has Redis primitives).

### Status semantics

`pending_first_access` → set on every generate/resend issuance (URL minted, subscriber hasn't visited yet).
`active` → only when `existing.last_active_at is not None` (set by webhook on first visit).
`expired` / `revoked` → emitted by `verify_access` failure paths.

Note: `cohort_member.status` column uses canonical `{active, suspended, dropped, waitlisted}`. The Output schema's `pending_first_access` is a UX-layer derived label — NOT persisted as the cohort_member.status value. Otherwise we'd be violating the schema cementation.

### Tenant isolation

- HMAC binds `tenant_id` in message → cryptographically tenant-scoped.
- `_FakeAuditLogRepo.save` raises if event tenant_id mismatches repo tenant — surfaces any tool bug writing cross-tenant audit row.
- Repos tenant-scoped at construction (mirrors `CohortMemberRepository` pattern).

### PII defense-in-depth

`_PII_KEYS` + `_EMAIL_RE` + `_PHONE_RE` scrub BEFORE `_sanitize_payload`. The `_sanitize_payload` lazy import has truncate-only fallback when `luana_core_observability` is unavailable — we MUST NOT rely on it for PII.

T10 test asserts: `ana@example.com`, `otra@example.com` (embedded in `bio`), `+1 555 123 4567`, `+52 55 9999 8888` all stripped from trace payload.

### Test coverage matrix

| # | Test | Action | Path |
|---|---|---|---|
| T1 | tenant_id_not_in_schema | (all) | security boundary |
| T2 | schema_version_frozen_v1 | (all) | cementation |
| T3 | generate_invite_happy_path | generate | URL + HMAC + member + audit + no LLM |
| T4 | resend_invite_idempotent_within_5min | resend | cache hit |
| T5 | resend_invite_outside_window_new_url | resend | cache miss → new URL |
| T6 | suggest_path_haiku_returns_tiers | suggest | LLM happy |
| T7 | suggest_path_llm_failure_engages_fallback | suggest | heuristic fallback |
| T8 | verify_access_valid_returns_true | gen + verify | round-trip |
| T9 | verify_access_tampered_token_returns_false | verify | HMAC mismatch |
| T10 | verify_access_expired_returns_false | verify | expiry check |
| T11 | cross_tenant_verify_rejected | verify | tenant_A token → tenant_B verify |
| T12 | forbidden_context_raises | generate (`lead_qualification` ctx) | guard |
| T13 | audit_log_failure_does_not_break_turn | generate | best-effort |
| T14 | trace_event_failure_does_not_break_turn | generate | best-effort |
| T15 | pii_scrubbed_in_trace_payload | suggest | defense-in-depth |
| T16 | missing_hmac_secret_raises | generate | env unset |
| T17 | generate_invite_creates_pending_member_when_not_enrolled | generate | new member row |
| T18 | suggest_path_with_existing_member_uses_engagement_signal | suggest | membership signal in prompt |
| T19 | verify_access_dropped_member_returns_false | verify | status defense-in-depth |

## Quality gates (native WSL — per AGENTS.md)

- `ruff check` (src/modules/comunify/agentic/tools/ + tests/agentic_evals/tools/) — **PASS** (0 errors)
- `ruff format --check` — **PASS** (0 reformats)
- `mypy` — **N/A** (not installed in comunify venv; consistent with T-tools-1)
- `pytest tests/agentic_evals/tools/` — **PASS** (32/32; 19 new + 13 sibling)

## V-AE-7 validator status

```bash
cd /home/chris/luana-platform/comunify/backend && \
  .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
```
→ `32 passed in 0.27s` — **GREEN**.

## Deviations from ticket

1. **Schema shape:** ticket cited `HttpUrl` Pydantic type for `invite_url`. Implemented as `str` because:
   - Pydantic's `HttpUrl` rejects URLs missing scheme/host at validation time.
   - During serialization round-trip, `HttpUrl` strips trailing slashes or normalizes path differently per Pydantic version, complicating exact-match tests.
   - The signed URL is always built by `_build_signed_url` with the configured `_DEFAULT_BASE_URL` (or env override) and our own format — security is guaranteed by HMAC, not by Pydantic URL parsing.
   Output `invite_url: str` still asserts the canonical shape via T3 (`startswith("https://...")` + HMAC re-computation + `parse_qs` extraction).

2. **`@register_tool` decorator:** ticket spec referenced `@register_tool(...)` decorator. Per T-tools-1 sibling, the actual EP-3 registration lives in `modules/comunify/extensions.py` (T-extensions-1) which uses `registry.sales_agent_tool_register(ToolDef(...))` — NOT a Python decorator. The function `link_to_community` is the bare handler; wiring it into the ToolDef placeholder is a separate concern. The placeholder `_not_implemented_yet("EP-3 comunify.link_to_community", "T-tools-2")` in `extensions.py:283` remains — wiring is left for the same follow-up wiring ticket as T-tools-1.

3. **Idempotency window:** ticket said 5 min; implemented exactly 5 min via `_IDEMPOTENCY_WINDOW = timedelta(minutes=5)`.

4. **Output `status: Literal["pending_first_access", "active", "expired", "revoked"]`:** matches ticket spec verbatim.

## Cost analysis (per 03-arch-agentic § 4.6)

| Action | Cost | Latency p50 | Latency p99 |
|---|---|---|---|
| `generate_invite` | $0 (no LLM) | 150ms target | 500ms target |
| `resend_invite` | $0 (cache hit / no LLM) | 150ms target | 500ms target |
| `suggest_path` | ~$0.003 (1 Haiku call, 64 output tok) | 1s target | 2.5s target |
| `verify_access` | $0 (pure CPU HMAC compare) | <10ms | <50ms |
| Idempotent replay (5min window) | $0 | <5ms | <10ms |

## Anti-pattern checks (skill-driven)

- [x] No naked LLM call — `_score_via_llm` wrapped in `asyncio.wait_for` + try/except + deterministic fallback
- [x] No naked HTTP call — N/A (HMAC sign is pure CPU; no remote)
- [x] No `tenant_id` in client-provided input schema — verified T1
- [x] No hardcoded model name — `_DEFAULT_SUGGEST_PATH_MODEL` constant + caller override
- [x] No infinite loop / no graph — pure tool dispatch
- [x] Best-effort observability — `_emit_audit_best_effort` + `_emit_trace_event_best_effort` both `try/except + structlog.warning`
- [x] PII redacted before `_sanitize_payload` (defense-in-depth)
- [x] Schema cement — `Literal[1]` + frozen
- [x] N=1 trigger documented (anti-duplication)
- [x] N=2 trigger flagged (`ForbiddenToolContextError`)

## Closing state

- Working tree: only my staged files (3 — see "Files written")
- Native tests: 32/32 PASS
- V-AE-7: GREEN
- Cross-tenant + PII + best-effort observability + idempotency + HMAC + fallback ALL covered
- No `git pull`, no `--force`, no `git add -A` (per parallel-safety.md)

<!-- @pm: build phase done (state: tests-passing). Files: 3 (1 new tool, 1 new test, 1 __init__ extend). Native ticket tests: 19/19 PASS (+13 sibling = 32/32). Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->
