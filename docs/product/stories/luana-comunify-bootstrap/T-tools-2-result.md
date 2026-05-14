# T-tools-2 RESULT — `link_to_community` tool

**Date:** 2026-05-14
**Verdict (build phase):** `tests-passing`
**Ticket:** [T-tools-2](06-tickets.yaml#L617) Story 12 `luana-comunify-bootstrap`
**Validators passed:** V-AE-7

## What shipped

A single async tool `link_to_community` with 4 actions (`generate_invite`,
`resend_invite`, `suggest_path`, `verify_access`), HMAC-SHA256 signed invite
URLs, 5-min idempotency cache, defense-in-depth cross-tenant rejection, and
best-effort audit + trace observability.

## Artifacts

| Path | Type | Lines |
|---|---|---|
| `comunify/backend/src/modules/comunify/agentic/tools/link_to_community.py` | NEW prod | 643 |
| `comunify/backend/tests/agentic_evals/tools/test_link_to_community.py` | NEW test | 678 |
| `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | EXTEND | +12 export lines |

## Acceptance criteria (from 06-tickets.yaml::T-tools-2)

| Criterion | Status |
|---|---|
| 4 actions: `generate_invite` \| `resend_invite` \| `suggest_path` \| `verify_access` | DONE — dispatcher in `link_to_community()` |
| Signed URL HMAC (`tenant_id + subscriber_id + expiry`) | DONE — `_hmac_token()` |
| Idempotency 5-min window | DONE — `_IDEMPOTENCY_WINDOW = timedelta(minutes=5)` + `_INVITE_CACHE` |
| Persists invite (cohort_member used per ticket allowance) | DONE — `_build_or_refresh_member` + `member_repo.save()` |
| Audit_log `community_access_granted_or_renewed` | DONE — `CommunityAccessAuditedV1` + best-effort persist |
| Cost $0 LLM for generate | DONE — verified T3 `assert llm_client.calls == []` |
| Cost $0.003 Haiku for suggest_path | DONE — Haiku model `anthropic/claude-haiku-4-5` (default; overridable) |
| Pydantic V1 frozen + `schema_version=1` | DONE — verified T2 |
| Test: generate_invite happy (URL + persist + audit) | T3 — PASS |
| Test: resend_invite reuses within 24h (spec said 5min idempotency window) | T4/T5 — PASS |
| Test: suggest_path Haiku → 1-3 tier suggestions | T6 — PASS |
| Test: verify_access validates HMAC + expiry → bool | T8/T9/T10 — PASS |
| Test: cross-tenant — tenant_A token NOT verifiable by tenant_B | T11 — PASS |

## Test suite

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
collected 32 items
tests/agentic_evals/tools/test_link_to_community.py ...................  [ 59%]
tests/agentic_evals/tools/test_qualify_for_cohort.py .............       [100%]
============================== 32 passed in 0.27s ==============================
```

**T-tools-2 contribution:** 19 new tests, ALL PASS.
**Regression:** 0 (sibling T-tools-1 still 13/13 PASS).

## Validator V-AE-7

```yaml
- id: V-AE-7
  cmd: cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
  must_pass: true
```

→ **GREEN** (`32 passed in 0.27s`).

## Quality gates

| Gate | Result |
|---|---|
| `ruff check` (scoped) | PASS (0 errors) |
| `ruff format --check` (scoped) | PASS (0 reformats) |
| `pytest tests/agentic_evals/tools/` | PASS (32/32) |
| `mypy` | N/A (not installed in comunify venv) |

## Key design decisions

1. **HMAC canonical message** = `f"{tenant_id}:{subscriber_id}:{exp}"`. Cross-tenant attempts inherently produce different signatures (test T11). Uses `hmac.compare_digest()` to avoid timing leaks.

2. **5-min in-process idempotency cache.** Multi-worker deploy may emit different URLs within window across workers — acceptable for v1. Future lift to Redis-backed shared cache when observed pain.

3. **`pending_first_access` is a UX-layer derived status**, not a DB column value. The persisted `cohort_member.status` stays in the canonical set `{active, suspended, dropped, waitlisted}`. The Output schema uses `pending_first_access` for UX clarity.

4. **`HttpUrl` → `str`**. Pydantic `HttpUrl` complicates exact-match testing (Pydantic-version-specific normalization). The URL is fully constructed by `_build_signed_url` with a configured base URL + HMAC — security guaranteed by signature, not by URL parsing.

5. **Best-effort observability** — `_emit_audit_best_effort` + `_emit_trace_event_best_effort` both `try/except + structlog.warning`. Per `.claude/rules/copilot-observability.md` cardinal, observability MUST NOT break the tool turn.

6. **PII defense-in-depth** — `_scrub_pii` removes `_PII_KEYS` + redacts inline email/phone via regex BEFORE `_sanitize_payload`. The `luana_core_observability` lazy import has a truncate-only fallback that does NOT redact PII; we never rely on it.

7. **Explicit `MissingHMACSecretError`** when `COMUNIFY_INVITE_SECRET` env var is unset. Silent fallback to empty key would defeat the entire URL signing scheme — explicit error forces deployment configuration.

## Deviations from spec

1. **Output schema `invite_url: str`** (ticket cited `HttpUrl`). Rationale documented in IMPL-LOG § Deviations #1.

2. **`@register_tool` decorator** — ticket spec used decorator syntax; actual EP-3 wire-up lives in `modules/comunify/extensions.py` via `registry.sales_agent_tool_register(ToolDef(...))` (T-extensions-1 pattern). Placeholder `_not_implemented_yet` in `extensions.py:283` remains — wiring is the same follow-up ticket as T-tools-1.

## Anti-duplication audit

- **N=1 trigger** (`link_to_community.py`, `LinkToCommunityInputV1`, `LinkToCommunityOutputV1`): no shared abstraction exists for HMAC URL signing in `shared/agent_observability/` nor `luana_core_*` packages. Inline OK.
- **N=2 trigger FLAGGED**: `ForbiddenToolContextError` is now defined in BOTH `qualify_for_cohort.py` (T-tools-1) and `link_to_community.py` (T-tools-2). Per `.claude/rules/anti-duplication.md` cardinal: deferred lift required. Recommended: `modules/comunify/agentic/tools/_exceptions.py` canonical class + import-and-reexport pattern. Trigger ticket: T-tools-refactor-N2 (PM ratification).

## Observability + cost recording

- **trace_event** emits to repo with event_type `tool.link_to_community.{action}` and sanitized payload (`subscriber_id`, `cohort_id`, `action`, `status`, `fallback_used`, `suggested_tiers`, PII-scrubbed profile).
- **audit_log** emits `CommunityAccessAuditedV1` for generate/resend (not suggest/verify) — actor_type=`sales_agent`, scrubbed payload with `exp_epoch`.
- **Cost trace** — `_emit_trace_event_best_effort` includes `duration_ms`; cost recording for the Haiku call should hook on the LLM client side per `.claude/rules/copilot-observability.md` (caller's responsibility — same pattern as T-tools-1).

## Forward-looking notes

- **`extensions.py` wiring** — replace `_not_implemented_yet("EP-3 comunify.link_to_community", "T-tools-2")` with the real handler reference. Same as T-tools-1 (still placeholder). Likely a small wiring ticket later.
- **`ForbiddenToolContextError` LIFT** — N=2 hit. T-tools-3 must NOT inline a third copy.
- **Redis idempotency cache** — when scaling multi-worker, lift `_INVITE_CACHE` to Redis.
- **`shared/luana_core_invite`** package — when a second vertical (vitalia + future) needs signed invite URLs, lift `_hmac_token` + `_build_signed_url` + `_verify_hmac` + idempotency cache there.
- **`MissingHMACSecretError` deployment** — `COMUNIFY_INVITE_SECRET` must be added to the comunify production env vars (rotate quarterly, 32+ random bytes).

## Final return

```
done -> docs/product/stories/luana-comunify-bootstrap/T-tools-2-result.md
```

<!-- @pm: build phase done (state: tests-passing). Files: 3 (link_to_community.py + test_link_to_community.py + __init__.py extension). Native ticket tests: 19/19 PASS (+13 sibling = 32/32 total). V-AE-7 GREEN. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->
