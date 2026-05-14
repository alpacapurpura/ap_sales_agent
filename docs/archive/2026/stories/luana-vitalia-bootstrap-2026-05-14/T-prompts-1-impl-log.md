# T-prompts-1 — Implementation Log

**Ticket:** Prompt slot architecture 10 slots + Slot 4 NEW MEDICAL_SAFETY_RAILS + cache_control
**State:** developing → tests-passing
**R23:** production_code=true → Opus 4.7 EXCLUSIVE
**Date:** 2026-05-14
**Builder:** Claude Opus 4.7 (1M context)
**Validators:** V-AE-22 (cache hit rate ≥85%) — GREEN
**Iteration:** 1 (RED → GREEN single iter; one targeted slot-text fix mid-iter for forbidden-token literal slip)

---

## Skills Consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` (auto-loaded) | T-prompts-1 surface = AGENTIC R23 prompt slot architecture; consulted for §0 Anti-duplication cardinal + slot architecture conventions cross-tenant cache prefix rules | Followed § "Stop. Lee primero" — went to anti-duplication.md SSoT first; followed slot-layout cement (cacheable boundary marker, per-tenant slot 5, forbidden mid-block interpolation per F8 + F10 + F3 patterns mirrored via Anthropic-native protocol). |
| `sales-agent-expert` (auto-loaded) | Vitalia is SECOND consumer of slot architecture pattern (sales_agent first); per anti-duplication §0 second invocation triggers LIFT-TO-SHARED evaluation | Verified mismatch: existing `luana_core_sales_agent.application.prompts.compose` is OpenAI-compatible auto-cache via prefix-stability (Kimi/DeepSeek pattern); Vitalia targets Anthropic native `cache_control` content blocks (Messages API multi-block content). DIFFERENT PROTOCOL — NEW justified, NOT mirror. Documented file:line evidence in compose.py docstring. |
| `tessl__langgraph` | T-prompts-1 does NOT touch graph nodes/edges directly — but downstream T-tools-* + T-workflow-1 will consume the composer at orchestrator level | Consulted for state-shape conventions (cacheable_prefix_blocks return shape compatible with Anthropic Messages API; orchestrator wires LiteLLM with `cache={"prompt_cache_key": str(tenant_id)}`). |
| `tessl__graceful-degradation` | No external HTTP/LLM call introduced by T-prompts-1 (pure data composer, no I/O) — but downstream LiteLLM calls will need timeout+fallback | NOT directly applicable to T-prompts-1; logged as forward-reference for orchestrator-wiring ticket. |
| `tessl__pytest-api-testing` | New test fixtures for cache-hit-rate simulator | Followed convention: `function`-scoped fixtures, factory helpers, parametrize for edge cases (8 slot variants × 4 PII categories). |
| `tessl__fastapi` | NOT applicable — T-prompts-1 has no FastAPI routes | Skipped — no FastAPI surface introduced. |
| `claude-api` (declared in 06-tickets.yaml) | Anthropic prompt cache `cache_control: ephemeral` markers + per-tenant `prompt_cache_key` | Cement: 1h TTL is recommended for sales-agent-style sessions (>10 min between turns) — but spec § 8.2 + § 10.2 explicitly use `{"type": "ephemeral"}` (default 5min TTL) per Story 11 architect ratification. Honored architect decision; documented TTL choice rationale in compose.py docstring. Forward reference: future ticket may upgrade to `{"type": "ephemeral", "ttl": "1h"}` if production tracking shows long inter-turn gaps. |

---

## Step 0 — Anti-duplication GATE evidence

```bash
# 1. find slot_4_medical_safety_rails — NO match
find /home/chris/luana-platform -name "slot_4*" 2>/dev/null
find /home/chris/AISALESHT/backend -name "slot_4*" 2>/dev/null
# (no output)

# 2. grep MEDICAL_SAFETY_RAILS — only references in extensions.py (mounting comment, NOT impl)
grep -rn "MEDICAL_SAFETY_RAILS" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null | grep -v __pycache__
# /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py:38: comment
# /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py:49: comment

# 3. find compose.py prompts in luana-platform — TWO matches
find /home/chris/luana-platform -type f -name "compose.py" 2>/dev/null
# /home/chris/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py
# /home/chris/luana-platform/nicolify/backend/src/modules/sales_agent/application/prompts/compose.py
```

**Decision: NEW (not extend, not lift)** — documented file:line evidence:

- `core/luana-core-sales-agent/.../prompts/compose.py:1-32` — header explicitly says "OpenAI prompt cache (April 2026) requires ≥1024 contiguous tokens of unchanged prefix to activate. Kimi K2.6 and DeepSeek V3/V4 ship the same auto-cache contract over OpenAI-compatible APIs (no `cache_control` annotations, just prefix stability)." → DIFFERENT PROTOCOL.
- `core/luana-core-sales-agent/.../prompts/compose.py:79-94` — exposes 7 cacheable + 4 volatile **string fragments** with markdown protocol `[TOOL_REQUEST: ...]`. → DIFFERENT FRAGMENT MODEL.
- Vitalia spec § 8.2 + § 10.2 explicitly demands Anthropic native `cache_control` content blocks (Messages API multi-block content) with 6 cacheable slots + Slot 4 NEW vertical-medical overlay. → DIFFERENT REQUIREMENT.

**Lift-to-shared deferred** — would require:
- Abstracting OpenAI prefix-stability + Anthropic content-block-cache into common interface (≠80% same logic, the protocols are inverted: OpenAI auto-detects via prefix bytes; Anthropic requires explicit cache_control markers per block);
- Story 11 timeline blocks lift; PM didn't escalate the lift in PR/CONTRACT doc;
- Future Story 11.bis or general SDD task could lift if 3rd vertical brand (e.g. Comunify, Lupulo) adopts Anthropic native protocol.

**No anti-duplication violation** — Vitalia is brand-side consumer with NEW protocol; existing compose.py modules untouched.

---

## Cross-module audit (NO-NEW-LAYER rule)

Vitalia compose.py is brand-side consumer code; no new shared infrastructure layer introduced. Slot file paths bundled inside `vitalia/backend/src/modules/vitalia/agentic/prompts/`. Channel format hints (Slot 6) currently use static-text declarative variant pending T-channels-N integration with `luana_core_channels.format.get_channel_format` registry — when that integration lands, the static dict will be replaced by registry lookup (extension over duplication path).

---

## Iteration log

### Iter 1 (single — completed in single pass with 1 in-iter forbidden-token cleanup)

**Plan:**
1. Write 3 j2 templates (slot_3_sales_playbook_vertical_medical, slot_4_medical_safety_rails, micro_anchor_per_turn).
2. Write compose.py with `SLOT_*` constants, `load_slot_*` readers, `compose_messages`, `cacheable_prefix_blocks` (test helper), `prompt_cache_key`.
3. Write 3 test files (A1 markers, A2 PII/interpolation, A3 cache hit rate).
4. Run validators.

**Execution:**
- Wrote slot_4_medical_safety_rails.j2 with sandbox markers + ASÍ HABLAS / ASÍ NO + LLM-side substitution markers (`{doctor_specialty}`, `{doctor_name}`, `{clinic_name}`, `{emergency_line_by_country}`).
- Wrote slot_3_sales_playbook_vertical_medical.j2 with booking flow + cadence + cancellation + escalation + out-of-scope sections.
- Wrote micro_anchor_per_turn.j2 (~14 Spanish words ≈ ~28 tokens per spec § 11.5).
- Wrote compose.py (~280 lines including verbose docstrings + spec citations).
- Wrote 3 test files (51 tests total: 12 A1 markers, 35 A2 PII/interpolation, 4 A3 cache hit rate).

**First test run:**
- 50 PASS, 1 FAIL — `slot_3_sales_playbook` flagged for containing literal `{tenant_name}` in the documentation comment (the comment literally said "NO `{tenant_name}` mid-block.").
- Fix: rephrased comment to "NO tenant identifiers mid-block." (no literal forbidden token).
- Same issue triggered in slot 4 docstring — fixed with same approach.

**Second test run:** 51/51 PASS. Lint clean. Format clean.

**Acceptance criteria coverage:**

| AC | Test | Result |
|---|---|---|
| A1 (sandbox markers + ASÍ HABLAS/NO blocks) | `test_vitalia_slot_4_safety_markers_present.py` (12 tests including parametrize) | PASS |
| A2 (no PII / no dynamic interpolation in cacheable slots 1-4 + 6) | `test_vitalia_no_pii_in_cacheable_slots.py` (35 tests including 8-slot × 4-category parametrize) | PASS |
| A3 (cache hit rate ≥85% on slots 1-6) | `test_cache_hit_rate.py` (4 tests including aggregate hit-rate, cross-tenant isolation, within-tenant 100% hit, prompt_cache_key str coercion) | PASS — simulated hit rate computed deterministically (90% expected ratio: 9 read turns / 10 total per tenant × 3 tenants) |

---

## Architecture decisions

1. **`cacheable_prefix_blocks(...)` test helper exposed in compose.py public API** — tests need to assert byte-equality of slots 1-6 in isolation without composing the full message. Public surface enables both production code (caller consumes via `compose_messages`) and tests (caller consumes via `cacheable_prefix_blocks`).
2. **LLM-side substitution markers (`{doctor_specialty}` etc.) live in slot 4 raw text** — model fills at generation time using slot 8 task-specific data. NEVER Python-side `.format()` pre-compose (would invalidate cache prefix). `_ALLOWED_LLM_SIDE_MARKERS` allowlist in test cement protects against accidental new placeholder slipping in.
3. **Slot 6 channel format = static dict** — pending T-channels-N integration with `luana_core_channels.format.get_channel_format`. When that integration lands, replace static dict with registry lookup (no test changes needed — assertions check byte-equality of slot 6 text per channel, registry returns same text for same channel).
4. **Synthetic in-process cache simulator (no real Anthropic API)** — A3 test must validate cache PIPELINE produces stable byte-equal prefixes; real LLM would cost $$ + introduce flakiness from network/rate limits. Simulator hashes block payloads under per-tenant cache_key bucket; matches Anthropic's actual prefix-byte-comparison contract. Real production hit rate measured via `copilot_llm_call.cache_read/cache_creation` columns when orchestrator wires LiteLLM (downstream ticket). This test = pre-wiring contract.
5. **No Jinja2 dep at runtime** — `.j2` extension is convention only; `Path.read_text(encoding="utf-8")` direct read. Per-tenant placeholders are LLM-side substitution markers (not Python-side jinja `{{ var }}` templating). Avoids adding jinja2 to vitalia venv (currently minimal: pytest + ruff + sqlalchemy + pydantic + asyncpg).
6. **TTL choice = ephemeral 5min default** — per spec § 8.2 + § 10.2 architect ratification. Future upgrade to `"ttl": "1h"` available if production observability shows >10min inter-turn gaps for sales-agent sessions.
7. **`prompt_cache_key(tenant_id) -> str`** — coerces UUID/int/str to canonical string for LiteLLM `cache={"prompt_cache_key": ...}`. Per-tenant cache_key isolates Slot 5 BRAND_VOICE so one tenant's voice doesn't invalidate another's cache prefix.

---

## State-of-the-art validation

- **WebSearch / WebFetch on Anthropic prompt caching:** consulted skill `copilot-expert` § state-of-the-art reference + `claude-api` skill — both anchored on canonical docs `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`. Skill knowledge cutoff Jan 2026 + 2026-05 update sources. Pattern consumed: per-block `cache_control: {"type": "ephemeral"}` markers + per-tenant `prompt_cache_key` + 5min default TTL OR explicit `"ttl": "1h"`. accessed 2026-05-14.
- **LangGraph 2.0 cement:** state TypedDict + reducers + `AsyncPostgresSaver` checkpointer — applies downstream at workflow level (T-workflow-1), NOT to T-prompts-1 surface (pure data composer, no graph nodes).
- **deepagents pattern:** subagent context isolation via `SubAgentMiddleware` — applies downstream at orchestrator level if Vitalia adopts deepagents pattern (currently using LangGraph 2.0 plain StateGraph per design § 8.1 + 03-arch decisión D3); not relevant to T-prompts-1.

---

## Cost analysis

- **Compose pipeline cost: $0** (deterministic Python file reads + dict lookups, no LLM call).
- **Production cache cost projection (per spec § 8.5 + V-AE-22 threshold):**
  - Cacheable region (slots 1-6) approx token count:
    - Slot 1: ~210 chars / 4 ≈ 53 tokens
    - Slot 2: ~750 chars / 4 ≈ 188 tokens
    - Slot 3: ~1900 chars / 4 ≈ 475 tokens
    - Slot 4: ~1500 chars / 4 ≈ 375 tokens
    - Slot 5: variable per tenant — assume avg 800 tokens (PersonalityProfile compiled v2)
    - Slot 6: ~250 chars / 4 ≈ 63 tokens
    - **Total cacheable ≈ 1,950 tokens** (≥1,024 token Anthropic minimum cement; well over).
  - At 85% hit rate, per-turn input cost dominated by SLOT 7-10 (volatile) + cache_read on slots 1-6 (~10% of write cost).
  - Concrete calc per Anthropic May 2026 pricing (Sonnet $3/M input, $0.3/M cache_read, $3.75/M cache_creation):
    - Per turn cache READ: 1,950 tokens × $0.3/M = $0.000585
    - Per turn cache CREATION (1st turn only per tenant): 1,950 × $3.75/M = $0.0073125
    - Per turn slot 7-10 volatile: ~500 tokens × $3/M = $0.0015
    - Steady-state per turn (post-warmup): $0.000585 + $0.0015 = **$0.002085/turn** (well within budget).
- **Cache invalidation triggers:**
  - Slot 1-4, 6: ~quarterly (deploy time, not runtime) → minimal cache churn.
  - Slot 5: per `PersonalityProfileUpdated` event per active tenant, ~weekly → minor cache churn.

---

## Files changed (luana-platform main)

```
vitalia/backend/src/modules/vitalia/agentic/prompts/
├── compose.py                                       NEW (~280 lines including verbose docstrings)
├── slot_3_sales_playbook_vertical_medical.j2        NEW (~50 lines)
├── slot_4_medical_safety_rails.j2                   NEW (~40 lines including sandbox markers)
└── micro_anchor_per_turn.j2                         NEW (1 line, ~28 tokens)

vitalia/backend/tests/architecture/
├── test_vitalia_slot_4_safety_markers_present.py    NEW (~150 lines, 12 tests)
└── test_vitalia_no_pii_in_cacheable_slots.py        NEW (~205 lines, 35 tests)

vitalia/backend/tests/agentic_evals/cache/
├── __init__.py                                      NEW (1-line docstring)
└── test_cache_hit_rate.py                           NEW (~280 lines, 4 tests)
```

Total: 8 files, 51 tests, 0 mods to existing files.

---

## R3 downstream regression scope

T-prompts-1 introduces:
- `vitalia/backend/src/modules/vitalia/agentic/prompts/compose.py` — first consumer is downstream T-tools-* + T-workflow-1 (orchestrator wiring). No existing consumers within Story 11 — no R3 regression risk introduced this ticket.

Per `.claude/rules/auditor-downstream-regression.md`, surface tabla SSoT row to be APPENDED in 03-arch-agentic.md § 17 by architect on next iteration:

```
| modules/vitalia/agentic/prompts/compose.py + .j2 templates | downstream T-tools-* + T-workflow-1 orchestrator wiring (not yet wired Story 11 W1) | First consumer arrives downstream — no regression scope this ticket. |
```

No `# downstream-regression-na: <reason>` magic comment needed (the file path is OUTSIDE `backend/src/shared/` so pre-commit hook Section 4 does NOT block).

---

## Halt triggers — none triggered

H1-H13 per 05-guidelines.md § 7: no cost variance >100%, no validators blocked >max_iter, no arch fitness violation, no spec drift, no tenant isolation regression, no PII leak detected, no Spanish neutro user-facing violation (slot prompts are LLM-internal, NOT chrome UI), no Alembic conflict, no cross-module import boundary violation, no anti-duplication detection (NEW protocol justified), no flag flip, no hot-fix repro requirement (greenfield), no spawn refusal.

---

## Decisions honored (per 05-guidelines.md § 6)

- **D5** (Slot 4 MEDICAL_SAFETY_RAILS NEW prompt slot): cement — vertical-medical overlay implemented as cacheable Slot 4 with sandbox markers DQ2 + ASÍ HABLAS/NO blocks per 02-design § 10.1 + § 11.3.
- **D9** (Chrome UI Spanish neutro pure tuteo): N/A to internal LLM slot prompts (Vitalia chrome UI is operator-facing — slot prompts are LLM-internal sales-agent voice). Vitalia internal slot architecture does NOT inherit `personality_profiles` — vertical-medical specific. Voice diversity (voseo OK Aurora, neutro CL Mindful, neutro broad MX Sanaré) lives in Slot 5 BRAND_VOICE per-tenant via `personality_profiles.system_instruction` (sales-agent SSoT cement preserved).

---

## Last-line return contract

```
done -> docs/product/stories/luana-vitalia-bootstrap/T-prompts-1-result.md
```
