# T-prompts-1 — Result

**Story:** luana-comunify-bootstrap
**Ticket:** T-prompts-1 — Prompt slot architecture 10 slots + Slot 4 NEW + cache_control + micro_anchor
**Surface:** AGENTIC (production_code: true) · Opus 4.7
**Estimate:** 4h · **Date:** 2026-05-14

---

## Status

**tests-passing** (52/52 ticket tests GREEN, full suite 389 PASS / 9 skipped no regression). Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict per R30).

---

## Artifacts

### Production code (1 module, 4 files)

| File | Purpose |
|---|---|
| `comunify/backend/src/modules/comunify/agentic/prompts/compose.py` | Anthropic Messages API 10-slot composer. `compose_messages()` + `cacheable_prefix_blocks()` + `prompt_cache_key()` + `load_micro_anchor()` + Slot 3/4 loaders + SLOT_1/2/6 constants. Anti-duplication audit-trail in docstring. |
| `comunify/backend/src/modules/comunify/agentic/prompts/slot_3_sales_playbook_creator_economy.j2` | Vertical-creator-economy playbook (qualification + Offer Ladder 4-level + cohort enrollment + community engagement + discovery call booking + escalation + out-of-scope). |
| `comunify/backend/src/modules/comunify/agentic/prompts/slot_4_community_safety_rails.j2` | **NEW slot per D5.** ASÍ HABLAS / ASÍ NO + 4 prohibitions (spam/nsfw/doxxing/injection) + sandbox markers DQ2 `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` + edge-case handoff. |
| `comunify/backend/src/modules/comunify/agentic/prompts/micro_anchor_per_turn.j2` | ~30 token anti-drift envelope, Slot 8 (NOT cached). voseo-allowed magic comment (renders per-tenant dialect). |

### Tests (3 files, 52 tests)

| Test file | Tests | Validators |
|---|---|---|
| `tests/architecture/test_comunify_slot_4_safety_markers_present.py` | 13 (sandbox markers presence/order/rationale + ASÍ HABLAS/NO sections/order + 4 prohibition keywords + disclaimer + creator handoff) | A1 acceptance |
| `tests/architecture/test_comunify_no_pii_in_cacheable_slots.py` | 35 (8 slot fixtures × 4 PII categories parametrized + slot-4 allowlist + cross-tenant byte-equal + cache_control marker presence) | A2 acceptance |
| `tests/agentic_evals/cache/test_cache_hit_rate.py` | 4 (cache hit rate ≥85% across 3 tenants × 10 turns + cross-tenant isolation + within-tenant 100% read + canonical str coercion) | **V-AE-27** (cache hit rate ≥0.85) |

---

## Validator coverage

**V-AE-27** (cache_hit_rate_min: 0.85) — covered by `tests/agentic_evals/cache/test_cache_hit_rate.py::test_cache_hit_rate_target_85_percent_min` (synthetic Anthropic cache simulator across 3 fixture tenants × 10 turns proves 90% actual ratio).

---

## Native test evidence

```bash
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest \
    tests/architecture/test_comunify_slot_4_safety_markers_present.py \
    tests/architecture/test_comunify_no_pii_in_cacheable_slots.py \
    tests/agentic_evals/cache/test_cache_hit_rate.py -v

============================== 52 passed in 0.06s ==============================
```

Full backend suite (downstream regression check):

```bash
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/

======================== 389 passed, 9 skipped in 1.12s ========================
```

Lint + format clean:

```bash
$ .venv/bin/ruff check src/modules/comunify/agentic/ tests/...
All checks passed!

$ .venv/bin/ruff format --check src/modules/comunify/agentic/ tests/...
6 files already formatted
```

---

## Decisions applied

| Decision | Application |
|---|---|
| **D5** — Slot 4 COMMUNITY_SAFETY_RAILS NEW (vs Vitalia MEDICAL_SAFETY_RAILS) | NEW `slot_4_community_safety_rails.j2` template. 4 community-specific prohibitions (spam/nsfw/doxxing/injection) + sandbox markers DQ2 + edge-case handoff. Sibling-pattern to Vitalia (NOT shared abstraction; documented audit-trail). |
| **Sales-agent voice SSoT** | Slot 5 BRAND_VOICE passed-through as opaque per-tenant string; NEVER mid-block interpolated. LLM-side substitution markers used in Slot 4. |
| **Anthropic native cache_control** | All 6 cacheable slots carry `cache_control: {"type": "ephemeral"}`. Per-tenant scoping via `prompt_cache_key(tenant_id)` returning `str(tenant_id)` for LiteLLM. |
| **Voseo discipline** | Slots 1-4 + 6 templates tuteo neutro strict (no voseo in cache prefix). Slot 5 + micro-anchor honor per-tenant voice dialect (voseo OK when es-AR). Magic comment on micro_anchor only. |
| **Anti-duplication** | Step 0 GATE evidence: filesystem search + cross-codebase grep + decision (sibling pattern Vitalia, NOT lift). Threshold rule: 3rd consumer → reconsider lift. |

---

## Forward notes (downstream tickets)

- **T-tools-1..4** (4 tools) — `qualify_for_cohort`, `link_to_community`, `nurture_via_authority_content`, `book_discovery_call` will consume `compose_messages()` at specialist invocation. Tool descriptions ALREADY listed lexically in Slot 2 STATIC_TOOLS_HINT for cache-stable inclusion.
- **T-guards-1..4** (4 guardrails) — input/output middleware chain references Slot 4 sandbox markers DQ2 for prompt-injection detection (anything outside `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` = adversarial).
- **T-voice-3** (voice compiler integration bridge) — when `voice_cloning_ratified(tenant_id)` event fires, orchestrator MUST bump per-tenant LiteLLM cache for Slot 5 invalidation. T-prompts-1 exposes `prompt_cache_key()` helper as the wiring seam.
- **Orchestrator wiring (later ticket)** — `compose_messages()` will be called by `application/orchestrator/` specialist nodes with `cache={"prompt_cache_key": prompt_cache_key(tenant_id)}` kwarg passed to `litellm.acompletion(...)` per spec § 10.2.
- **Production telemetry (later)** — `copilot_llm_call.cache_read_input_tokens / cache_creation_input_tokens` ratio per tenant (per spec § 8.5) will validate the synthetic V-AE-27 simulator in real prod.

---

## Commit

`b0b19d9` in `alpacapurpura/luana-platform` (main branch).

```
feat(comunify/T-prompts-1): 10-slot Anthropic prompt architecture + Slot 4 community-safety overlay
11 files changed, 1305 insertions(+)
```
