# T-tools-3 IMPL-LOG — `nurture_via_authority_content` tool

**Date:** 2026-05-14
**Surface:** AGENTIC (R23 — `production_code=true`, Opus 4.7 EXCLUSIVE)
**Ticket:** [T-tools-3](06-tickets.yaml#L642) Story 12 `luana-comunify-bootstrap`
**Estimate:** 3h | **Actual:** ~1.5h
**Validators passed:** V-AE-7 (55/55 GREEN; +23 net new tests)

## State on entry

- Branch: `development` (per `.claude/rules/parallel-safety.md`)
- Tree dirty with other-session WIP (story docs already created, untouched)
- Baseline `tests/agentic_evals/tools/`: **32 passed** (T-tools-1: 13, T-tools-2: 19)
- Dependencies confirmed: T-be-7 (AuthorityVaultService) done — see `T-be-7-result.md`. T-extensions-1 done — see `T-extensions-1-result.md`. EP-3 wiring placeholder visible at `extensions.py:283` (same `_not_implemented_yet` deferral as T-tools-1 + T-tools-2 siblings).

## Skills Consulted (R30 Step 0 GATE)

| Skill | Decision captured |
|---|---|
| `copilot-expert` | §0 anti-duplication cardinal: ran `find -name "nurture_via_authority_content.py"` + `grep -rn "class NurtureViaAuthority"` cross-codebase. No match. Authority-vault matcher pattern is comunify-vertical (creator economy nurture playbook) — no shared abstraction exists in `shared/agent_observability/` nor `luana_core_*` packages → N=1 inline OK for the tool body. Observability is best-effort try/except + structlog warning per `copilot-observability.md`. |
| `sales-agent-expert` | §0 anti-duplication: confirmed no mirror in sales_agent codebase. Schema cementation: `schema_version: Literal[1]` + `ConfigDict(frozen=True)` on both Input + Output. Cache-friendly prompt for ranking call: system block invariant (no `{tenant_id}` interpolation, no timestamps) — explicit T17 test asserts this invariance across tenants. Voseo: tool is structured-data only (no Spanish prose output to lead). |
| `tessl__langgraph` | N/A — tool returns Pydantic output; no StateGraph node ownership. Tool is consumed BY a graph (sales_agent/copilot orchestrator), not a graph itself. |
| `tessl__graceful-degradation` | LLM ranking call (`_rank_via_llm`) wrapped in `asyncio.wait_for(..., timeout=15s)` + deterministic kind-affinity + recency fallback (`_deterministic_rank`). Repo failures (`list_by_kind` / `list_all`) caught per-kind + per-call → routed to empty-vault terminal fallback. trace_event persistence wrapped try/except + warning (1 best-effort path × never break turn). Three fallback paths: (1) LLM exception → deterministic, (2) LLM invalid response shape → deterministic, (3) repo empty/down → empty terminal result. |
| `tessl__pytest-api-testing` | Factory-style fakes (`_FakeVaultItem`, `_FakeVaultRepo`, `_RaisingVaultRepo`, `_CapturingTraceRepo`, `_RaisingTraceRepo`, `_FakeLLMClient`). Function-scoped autouse fixture (`_reset_module_cache`) drops in-process idempotency cache between tests — prevents inter-test pollution. `_now` injection point for time-based testing (idempotency 1h window) without `time.sleep`. Response shape asserted (not just status) — `event_type`, `name`, `data`, `duration_ms`, `tenant_id` correlation. 23 distinct test cases isolated. |
| `tessl__fastapi` | N/A — pure tool module, no FastAPI route in T-tools-3 scope. |

## Step 0.5 — Default flip detection

N/A — no `backend/src/core/config.py` defaults flipped. New tool only + small refactor to share a single `ForbiddenToolContextError` across sibling tools.

## Step 0 — Anti-duplication audit (R-anti-dup cardinal)

```bash
# 1. find existing nurture_via_authority_content.py — none
find /home/chris/luana-platform -name "nurture_via_authority_content.py" 2>/dev/null
# → no output

# 2. class NurtureViaAuthority*
grep -rn "class NurtureViaAuthority" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# → only spec docs (03-arch-agentic.md § 4.3)

# 3. authority_vault matcher pattern
grep -rn "authority_vault.*match\|nurture_via_authority" \
  /home/chris/luana-platform/core/ /home/chris/AISALESHT/backend/src/shared/ 2>/dev/null
# → none

# 4. Verified candidate shared abstractions inventory:
#    - shared/agent_observability/: observability + cost only, no content matcher
#    - luana_core_observability: sanitization only
#    - luana_core_extension_sdk: ExtensionPointRegistry only
# Decision: N=1 inline → ok per `.claude/rules/anti-duplication.md`.
```

## Step 0 — N=3 trigger HONOURED (deferred lift from T-tools-2 executed)

`T-tools-2-result.md` § "Forward-looking notes" flagged:
> **`ForbiddenToolContextError` LIFT** — N=2 hit. T-tools-3 must NOT inline a third copy.

Verified that BOTH `qualify_for_cohort.py` AND `link_to_community.py` defined
identical `ForbiddenToolContextError(Exception)` classes inline. Adding a third
copy in `nurture_via_authority_content.py` would be N=3 — explicit
process-improvement case study per anti-duplication.md cardinal.

**Action taken (executed in this ticket — not deferred further):**

1. NEW `modules/comunify/agentic/tools/_exceptions.py` (62 lines) defines the
   canonical `ForbiddenToolContextError(context, *, tool_name=None)`. Signature
   is backward-compatible with the existing positional `context: str` call sites
   in `qualify_for_cohort.py:766` + `link_to_community.py:957`.
2. EXTEND `qualify_for_cohort.py` — removed inline class (10 lines), replaced
   with `from ._exceptions import ForbiddenToolContextError`. Public API
   preserved via re-export.
3. EXTEND `link_to_community.py` — same treatment as #2.
4. EXTEND `tools/__init__.py` — re-export the canonical class explicitly.
5. NEW `nurture_via_authority_content.py` imports `ForbiddenToolContextError`
   from `_exceptions.py` — NO inline copy.

Verified by T14 test (`test_forbidden_tool_context_error_lifted_from_shared_module`):

```python
assert CanonicalError is LinkError
assert CanonicalError is NurtureError
assert CanonicalError is QualifyError
```

All four references are the SAME class object (identity check). Lift complete.

**N=4 trigger flagged forward:** `_LLMClientLike` Protocol + `_PII_KEYS`/`_EMAIL_RE`/`_PHONE_RE`
inline PII scrub are now duplicated across all 3 tool files. Next refactor ticket
should lift these to `modules/comunify/agentic/tools/_pii_scrub.py` + lift Protocol
to shared agentic abstraction. See "Forward-looking notes" in result.md.

## Files written

| File | Action | Lines |
|---|---|---|
| `comunify/backend/src/modules/comunify/agentic/tools/_exceptions.py` | NEW (shared) | 56 |
| `comunify/backend/src/modules/comunify/agentic/tools/nurture_via_authority_content.py` | NEW (prod) | 614 |
| `comunify/backend/tests/agentic_evals/tools/test_nurture_via_authority_content.py` | NEW (test) | 727 |
| `comunify/backend/src/modules/comunify/agentic/tools/qualify_for_cohort.py` | EXTEND (-14, +5) | refactor only |
| `comunify/backend/src/modules/comunify/agentic/tools/link_to_community.py` | EXTEND (-14, +5) | refactor only |
| `comunify/backend/src/modules/comunify/agentic/tools/__init__.py` | EXTEND (+8 exports) | refactor + add |

## Files NOT touched (scope discipline)

- `comunify/backend/src/modules/comunify/extensions.py` — `_not_implemented_yet` handler for `nurture_via_authority_content` at `extensions.py:321` left in place. T-tools-1 + T-tools-2 siblings did the same. EP-3 wire-up is a separate concern (likely a single follow-up `T-wiring-N` per `T-tools-1-result.md` pattern, batching all 4 tools).
- `comunify/backend/src/modules/comunify/application/services/authority_vault_service.py` — read-only consumer of the repo, not modified.
- `comunify/backend/src/modules/comunify/infrastructure/repositories/authority_vault_repository.py` — consumed via Protocol surface, not modified.
- Any module outside `agentic/tools/` and the test mirror.
- AISALESHT-side files (story is cross-repo — comunify backend has the prod code; AISALESHT only holds story docs).

## Implementation notes

### Action contract & dispatch flow

Single async entry `nurture_via_authority_content()` does NOT have a multi-action
dispatcher (unlike T-tools-2's 4-action `link_to_community`). It's a single
read-only matcher. Flow:

1. **Forbidden-context guard** — currently empty frozenset; exposed for symmetry
   so future-proofing additions are a one-line change.
2. **1h idempotency cache** — keyed by `(tenant_id, lead_id, intent, preferred)`.
   On hit: re-wrap with `cache_hit=True` flag and return; emit trace event with
   `cache_hit=True`. No DB read, no LLM call.
3. **Vault fetch via Protocol** — `_AuthorityVaultRepoLike` exposes `list_by_kind`
   + `list_all`. Pre-filter by `preferred_content_type` (when pinned) OR
   `_INTENT_KIND_AFFINITY[intent]` (kind-affinity heuristic).
4. **Empty terminal fallback** — when vault is empty, return `fallback_used=True`
   + `confidence=0.0` + empty `content_url[]` + the `_DEFAULT_NEXT_STEP_BY_INTENT`
   for the intent. NO LLM call. NOT cached (cheap to re-evaluate; vault may fill).
5. **LLM ranking (Haiku)** — `_rank_via_llm` with 15s `asyncio.wait_for` timeout.
   Catalog cap 20 items, excerpt cap 200 chars per item (token budget).
6. **Deterministic fallback** — `_deterministic_rank` engages on any LLM
   exception OR invalid response (empty choices / non-JSON / unknown ids).
   Scoring = kind affinity weight × recency. Confidence = 0.4 (low).
7. **Result + cache + trace** — materialize `matched_items` (provenance) +
   `content_url` (URL-only subset). Store in cache (1h). Emit trace event with
   sanitized payload.

### Idempotency design

In-process dict cache (`_NURTURE_CACHE`). 1h window per ticket Constraints
(NOT the 5min cited in `03-arch-agentic.md § 4.3`'s decorator lambda —
ticket Constraints win). Multi-worker deploy may emit different rankings within
window across workers — acceptable for v1 (matches T-tools-2 pattern). Future
lift to Redis-backed shared cache when observed pain.

Cache key includes `preferred_content_type` — verified by T8c test
(`test_cache_key_includes_preferred_content_type`).

### Intent → kind affinity heuristic

Comunify-specific heuristic (creator economy authority vault classification).
NOT lifted to shared — vault kinds are vertical-specific. Documented in module
docstring + verified by T10 test (`imposter_syndrome` → `press_mentions` head).

```python
_INTENT_KIND_AFFINITY = {
    "pricing_guilt":     ("case_studies", "press_mentions", "awards"),
    "imposter_syndrome": ("press_mentions", "case_studies", "awards", "credentials"),
    "scaling_overload":  ("case_studies", "press_mentions", "awards"),
    "burnout_concern":   ("case_studies", "press_mentions"),
    "fear_first_client": ("case_studies", "press_mentions"),
    "general":           ("case_studies", "press_mentions", "awards", "credentials"),
}
```

### Read-only invariant

Tool is pure READ-ONLY. The `_AuthorityVaultRepoLike` Protocol intentionally
exposes ONLY `list_all` + `list_by_kind` — no `save`, no `soft_delete`. Verified
by T11 test which asserts `_FakeVaultRepo` lacks mutation methods (so any tool
attempt to mutate would `AttributeError`).

No audit log, no event emission, no domain event.

### LLM cache prefix safety

System message is invariant (no tenant_id, no timestamps, no PII). Verified by
T17 test (`test_llm_system_message_is_cache_friendly_invariant`) which calls
the tool from two different tenants and asserts the system message bytes are
identical.

User message contains the volatile catalog payload (vault excerpts + intent +
preferred type). Acceptable cache structure: cache prefix = system message
slot; user slot is the variable per-turn.

### PII scrub regex tightening (defect found + fixed)

While running T15 (`test_trace_event_emitted_with_expected_event_type`), the
initial implementation of `_PHONE_RE` was inherited verbatim from T-tools-1 /
T-tools-2:

```python
_PHONE_RE = re.compile(r"(?:\+?\d[\s\-\(\)]?){7,}\d")
```

This regex matched UUID substrings like `48b3-8951-68964a91ac7f` because the
character class accepts hyphens between digit-like chars. T15 detected the
issue by hard-asserting `data["lead_id"] == str(lead_id)`. The regex was
tightened to:

```python
_PHONE_RE = re.compile(
    r"(?<![\w-])"
    r"(?:"
    r"\+\d[\d\s\-().]{6,}\d"
    r"|"
    r"\(?\d{2,4}\)?[\s\-]\d{2,4}[\s\-]\d{2,4}(?:[\s\-]\d{2,4})?"
    r"|"
    r"\d{7,15}"
    r")"
    r"(?![\w-])"
)
```

Boundary anchors `(?<![\w-])` / `(?![\w-])` prevent matching INSIDE
alphanumeric tokens (UUIDs, identifier-like strings). All inline-phone PII
shapes still match (verified by T12 — `+1-555-123-4567`, `+44 207 123 4567`,
`alice@example.com` all redacted in the trace payload).

**Note:** the same bug exists in T-tools-1 + T-tools-2's inline `_PHONE_RE`
copies. They were not detected because their tests don't assert exact UUID
string preservation in the trace payload. The fix is local to this file (per
parallel-safety M8 "extend ajenos, don't replace"). Flagged for the N=4 PII
lift ticket — fixing all three files at once with a shared `_pii_scrub.py`.

### Output schema deviation from spec (acknowledged)

`content_url: list[str]` (the spec § 4.3 cites `list[HttpUrl]`). Rationale
mirrors T-tools-2 deviation #1 (T-tools-2-result.md § "Deviations from spec"):
Pydantic `HttpUrl` complicates exact-match testing (version-specific
normalization) + vault items may have `url=None` which we want to surface as
empty string. The URL is fully constructed by trusted code paths
(`AuthorityVaultRepository` returns straight DB column values).

Also added `matched_items: list[NurtureMatchedItemV1]` — NOT in spec but
captures provenance (id + kind + title + url) so callers can render rich UX
even when item has no URL (T18 test).

## Test suite summary

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
collected 55 items
tests/agentic_evals/tools/test_link_to_community.py ...................         [ 34%]
tests/agentic_evals/tools/test_nurture_via_authority_content.py ....... ........ [ 76%]
tests/agentic_evals/tools/test_qualify_for_cohort.py .............              [100%]
============================== 55 passed in 0.28s ==============================
```

- **T-tools-3 contribution:** 23 new tests, ALL PASS.
- **Sibling regression:** 0 (T-tools-1 13/13 PASS, T-tools-2 19/19 PASS).
- **Net total V-AE-7:** 55 passing (was 32 baseline).

**Full BE suite regression:** `pytest tests/` → 494 passed, 9 skipped, 0 fail.

## Validator V-AE-7 (acceptance)

```yaml
- id: V-AE-7
  category: agentic_eval
  type: pytest
  cmd: cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short
  must_pass: true
  timeout_sec: 300
  description: "4 tools tests — happy/edge/error per tool (02-design § 6)"
```

→ **GREEN** (`55 passed in 0.28s`; T-tools-3 contributes 23/23).

## Quality gates

| Gate | Result |
|---|---|
| `ruff check` (scoped to tools/ + tests/) | PASS (0 errors) |
| `ruff format --check` (scoped) | PASS (9 files clean) |
| `pytest tests/agentic_evals/tools/` | PASS (55/55) |
| `pytest tests/` (full BE suite) | PASS (494/494 + 9 skip) |
| `mypy` | N/A (not installed in comunify venv) |

## Skill-cited decisions per category

### Anti-duplication (cardinal — invoked first)
- **Action:** N=3 LIFT honoured. Created shared `_exceptions.py` + refactored 2 sibling tools to import + re-export.
- **Evidence:** T14 identity test asserts all 4 references → SAME class object.
- **Flagged forward:** `_LLMClientLike` Protocol + `_PII_KEYS`/`_EMAIL_RE`/`_PHONE_RE` are now 3× across tool files. Next ticket lift target.

### Tenant isolation
- `tenant_id` MUST NEVER appear in input schema — verified by T1 test (`test_tenant_id_not_in_schema`).
- Repo is tenant-scoped at construction — cross-tenant test (T6) populates `tenant_A` items into a `tenant_B`-scoped repo and asserts empty fallback (no leak).

### Schema cementation
- `schema_version: Literal[1]` on both Input + Output — verified by T2 test.
- `ConfigDict(frozen=True)` on Output — mutation raises (T2 final assert).

### Graceful degradation
- LLM timeout 15s + 3 fallback paths verified (T8/T8b/T8c/T8d tests).
- trace_event failures don't break turn (T13 test with `_RaisingTraceRepo`).
- Empty-vault terminal fallback (T5 test).

### Cache prefix safety
- T17 asserts system message bytes IDENTICAL across two different tenants.
- T7/T7b/T7c assert 1h idempotency window + cache key uniqueness per
  `preferred_content_type`.

### Observability best-effort
- T13 — `_RaisingTraceRepo` does not break tool turn.
- T15 — trace event has expected `event_type`, `name`, `status`, `tenant_id`,
  `turn_id`, `span_id`, `duration_ms`, `data` shape.

### PII defense-in-depth
- T12 asserts NO raw `john.smith@example.com`, `alice@example.com`,
  `+1-555-123-4567`, `+44 207 123 4567` in the trace event payload.
- Phone regex tightened to NOT match UUID substrings (defect found mid-build,
  fixed in same ticket).

### Read-only invariant
- T11 asserts `_FakeVaultRepo` has no `save` / `soft_delete` — tool would
  `AttributeError` if it tried to mutate.

## Cross-references

- Spec: `docs/product/stories/luana-comunify-bootstrap/03-arch-agentic.md` § 4.3
- Ticket: `docs/product/stories/luana-comunify-bootstrap/06-tickets.yaml::T-tools-3`
- Validator: `docs/product/stories/luana-comunify-bootstrap/04-validators.yaml::V-AE-7`
- Sibling impl-logs: `T-tools-1-impl-log.md`, `T-tools-2-impl-log.md` (pattern source)
- Rule: `.claude/rules/anti-duplication.md` (N=3 lift honoured)
- Rule: `.claude/rules/tenant-isolation.md`
- Rule: `.claude/rules/copilot-observability.md`

## Forward-looking notes

1. **`_LLMClientLike` Protocol N=3 LIFT trigger.** Defined inline in
   `qualify_for_cohort.py`, `link_to_community.py`, AND now
   `nurture_via_authority_content.py`. Next ticket touching tools should lift
   to shared agentic abstraction. Sensible home:
   `modules/comunify/agentic/tools/_llm_protocol.py`.

2. **PII scrub N=3 LIFT trigger.** `_PII_KEYS`, `_EMAIL_RE`, `_PHONE_RE`,
   `_scrub_pii` all duplicated across 3 tool files. Worse: the phone regex
   has a defect in T-tools-1 + T-tools-2 (matches UUID substrings) — only
   detected by T15 in T-tools-3 because it hard-asserts UUID preservation.
   Next ticket should lift to `_pii_scrub.py` with the **tightened** phone
   regex, then refactor sibling tools.

3. **`extensions.py` wiring** — replace `_not_implemented_yet("EP-3 comunify.nurture_via_authority_content", "T-tools-3")` at `extensions.py:321` with the real handler reference. Same deferral pattern as T-tools-1 + T-tools-2 siblings.

4. **Redis idempotency cache** — when scaling multi-worker, lift `_NURTURE_CACHE` to Redis (alongside `_INVITE_CACHE` from T-tools-2).

5. **AuthorityVaultExtractor (T-extractors-2)** — when that extractor lands,
   the vault content shape may grow new fields (parsed credentials, bio
   excerpts, etc.). The tool's excerpt serialization (`_item_to_excerpt`)
   uses `getattr` everywhere — gracefully tolerates new fields without code
   changes.

## Final return

```
done -> docs/product/stories/luana-comunify-bootstrap/T-tools-3-result.md
```

<!-- @pm: build phase done (state: tests-passing). Files: 6 (1 NEW shared exceptions module + 1 NEW prod tool + 1 NEW test file + 3 EXTEND refactors for the N=3 lift). Native ticket tests: 23/23 PASS (+32 sibling = 55/55 V-AE-7 total; +462 full BE suite = 494/494). V-AE-7 GREEN. Ruff lint + format clean. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->
