# T-prompts-1 — Implementation Log

**Story:** luana-comunify-bootstrap
**Ticket:** T-prompts-1 — Prompt slot architecture 10 slots + Slot 4 NEW + cache_control + micro_anchor
**Surface:** AGENTIC (production_code: true)
**Owner:** Opus 4.7 (R23 — agentic production = Opus exclusive)
**Estimate:** 4h
**Date:** 2026-05-14

---

## Skills Consulted (Step 0 GATE)

Per role HARD GATE, declared skills upfront, invoked via skill format, captured decisions:

| Skill | Why invoked | Decision applied |
|---|---|---|
| `copilot-expert` | Touches AGENTIC observability surfaces in spirit (prompt slots → cache hit telemetry will land at `copilot_llm_call.cache_read_input_tokens` per spec § 8.5). Read § "Anti-duplication cardinal" first. | Anti-duplication audit performed pre-write — sibling pattern (Vitalia compose.py), NOT shared abstraction. Documented in compose.py docstring (~30 lines audit trail). |
| `sales-agent-expert` | Slot 5 BRAND_VOICE is the `personality_profiles.system_instruction` SSoT per `.claude/rules/sales-agent-brand-voice.md`. § 5 invariance is the cardinal cache-prefix rule. | Slot 5 treated as opaque per-tenant string; NOT interpolated into other slots; LLM-side substitution markers used in Slot 4 (`{brand_name}`, `{creator_name}`, `{creator_email}`, `{emergency_line_by_country}`) — model fills at gen time. NO `{tenant_name}` mid-block. NO timestamps. NO conversation_id. Enforced by `test_comunify_no_pii_in_cacheable_slots.py`. |
| `tessl__langgraph` | Listed in role description as mandatory when any graph node/state/edge touched. T-prompts-1 produces pure compose data — NO StateGraph touched. | Verified scope = pure data (no graph nodes / no state / no edges). Skill knowledge consulted preventively but not consumed (no graph code shipped this ticket). |
| `tessl__graceful-degradation` | Listed as mandatory for any new external call. T-prompts-1 introduces zero external calls — pure compose data + file reads. | Verified: NO HTTP, NO LLM call, NO DB query, NO Qdrant call. Skill knowledge consulted preventively; not applicable to this scope. LLM call happens at orchestrator level (downstream tickets), where graceful-degradation will be wired (timeout + fallback + circuit breaker). |
| `tessl__pytest-api-testing` | New tests with parametrize + fixtures. | Used `@pytest.mark.parametrize` for slot-level + prohibition-keyword iteration; per-function scope (default) for cache-stat fixtures; no async client needed (pure-data tests). |
| `tessl__fastapi` | No FastAPI route in scope. | NOT applicable — no router / no `response_model=`. |
| `claude-api` | Anthropic SDK / prompt cache patterns. Slot 4 uses sandbox markers DQ2 + `cache_control: ephemeral`; Slot 5 uses `prompt_cache_key=tenant_id`. | Applied verbatim per spec § 8.2 + § 10.2 — Anthropic native content-block `cache_control: {"type": "ephemeral"}` per cacheable slot. `prompt_cache_key(tenant_id)` helper returns `str(tenant_id)` for LiteLLM cache scoping. NO live Anthropic SDK call (downstream orchestrator wiring). |

---

## Step 0.5 — Default-flip pre-audit

**Not applicable.** T-prompts-1 does NOT touch `backend/src/core/config.py` defaults nor any feature flag side-effect path. Pure new module (`modules/comunify/agentic/prompts/`). No `USE_OUTBOX_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` flips.

---

## Cross-Module Audit (NO-NEW-LAYER)

Per `.claude/rules/anti-duplication.md` § 0 + agent role guard, performed Step 0 GATE before any `Write`:

```bash
# Step 1: filesystem search
$ find /home/chris/luana-platform/comunify/backend/src -name "compose.py" -o -name "*prompt*" -o -name "slot_*"
# → no match (clean slate in comunify)

# Step 2: cross-codebase grep for existing composers
$ grep -rn "compose_messages|cacheable_prefix_blocks|prompt_cache_key" /home/chris/luana-platform/comunify/backend/src/ tests/
# → no match (no parallel implementations)

# Step 3: shared SDK inspection
$ ls /home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/prompts/
# compose.py + slot_3_sales_playbook_vertical_medical.j2 + slot_4_medical_safety_rails.j2 + micro_anchor_per_turn.j2
```

**Match (Vitalia sibling) — decision:** keep per-brand `compose.py`, NOT LIFT to shared.

Rationale (documented verbatim in `compose.py` docstring):

- Slot 3 + Slot 4 templates are **vertical-specific text** (medical vs creator-economy). Lifting would force a generic abstraction that adds complexity without saving any line beyond the `compose_messages` wrapper.
- Slot 1 STATIC_IDENTITY differs (vertical role description).
- Anthropic content-block + cache_control structure is identical (~30 lines of boilerplate) but those 30 lines are well-justified to repeat per-brand for code-locality + each brand reads its own slot files.

**Threshold rule:** 2 consumers (Vitalia + Comunify) → sibling pattern. If a 3rd brand consumer appears (Pulse / Plenum / future vertical), reconsider lift to `luana_core_agentic_prompts`. Documented as forward-looking note in compose.py audit-trail block.

Also audited:
- `luana_core_sales_agent.application.prompts.compose` (Story 9 core) — DIFFERENT PROTOCOL (string-based markdown for OpenAI-compatible auto-cache; Comunify uses Anthropic Messages API native content blocks). Cannot extend.
- `format_for_channel` from `luana_core_channels` — would consume that registry; Slot 6 here uses static-text declarative variant pending T-channels-N integration with shared registry. Forward note.

---

## Files Touched

| Path | Action | Notes |
|---|---|---|
| `comunify/backend/src/modules/comunify/agentic/__init__.py` | CREATE (empty) | Package marker |
| `comunify/backend/src/modules/comunify/agentic/prompts/__init__.py` | CREATE (empty) | Package marker |
| `comunify/backend/src/modules/comunify/agentic/prompts/compose.py` | CREATE | Main composer — SLOT_1, SLOT_2, SLOT_6 constants + Slot 3/4 loaders + `compose_messages()` + `cacheable_prefix_blocks()` + `prompt_cache_key()` + `load_micro_anchor()`. Anti-duplication audit-trail in module docstring. |
| `comunify/backend/src/modules/comunify/agentic/prompts/slot_3_sales_playbook_creator_economy.j2` | CREATE | Vertical-creator-economy playbook (qualification + ladder nurture + cohort enrollment + community engagement + discovery call booking + escalation triggers + out-of-scope). No Jinja control flow. |
| `comunify/backend/src/modules/comunify/agentic/prompts/slot_4_community_safety_rails.j2` | CREATE | NEW slot per D5. ASÍ HABLAS / ASÍ NO blocks + 4 safety prohibitions (spam/nsfw/doxxing/injection) + sandbox markers `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` + edge-case handoff guidance. 4 LLM-side substitution markers (allowlist-enforced by tests). |
| `comunify/backend/src/modules/comunify/agentic/prompts/micro_anchor_per_turn.j2` | CREATE | ~30 tokens. Per-turn anti-drift envelope in Slot 8 (NOT cached). voseo-allowed magic comment (renders per-tenant dialect — voseo OK when es-AR Anabella). |
| `comunify/backend/tests/architecture/test_comunify_slot_4_safety_markers_present.py` | CREATE | 13 tests. Sandbox markers presence + order + injection rationale + ASÍ HABLAS/NO sections + 4 prohibition keywords + disclaimer obligation + creator handoff. |
| `comunify/backend/tests/architecture/test_comunify_no_pii_in_cacheable_slots.py` | CREATE | 35 parametrized tests across 8 cacheable-slot fixtures × 4 PII categories + slot-4 allowlist + cross-tenant byte-equal + cache_control marker presence. |
| `comunify/backend/tests/agentic_evals/__init__.py` | CREATE (empty) | Package marker |
| `comunify/backend/tests/agentic_evals/cache/__init__.py` | CREATE (empty) | Package marker |
| `comunify/backend/tests/agentic_evals/cache/test_cache_hit_rate.py` | CREATE | 4 tests synthetic Anthropic cache simulator. 3 fixture tenants × 10 turns = ≥85% hit rate proof (actual ratio 90% on slots 1-6). |

**Out of scope (forward note):** orchestrator wiring of `compose_messages()` into LiteLLM `acompletion()` call lands at downstream tickets (T-tools-1..4, T-voice-3 bridge, eventual `application/orchestrator/`). T-prompts-1 ships compose data + arch invariants only.

---

## Native test results

```
cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest \
  tests/architecture/test_comunify_slot_4_safety_markers_present.py \
  tests/architecture/test_comunify_no_pii_in_cacheable_slots.py \
  tests/agentic_evals/cache/test_cache_hit_rate.py -v

=== 52 passed in 0.06s ===
```

Full comunify backend suite:

```
cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/

=== 389 passed, 9 skipped in 1.12s ===
```

9 skipped = integration tests requiring live Postgres (pre-existing, NOT introduced by this ticket). Zero downstream regression.

Lint + format clean:

```
$ .venv/bin/ruff check src/modules/comunify/agentic/ tests/...
All checks passed!

$ .venv/bin/ruff format --check src/modules/comunify/agentic/ tests/...
6 files already formatted
```

---

## Compliance Checklist

- [x] **Step 0 GATE skills invoked** — copilot-expert + sales-agent-expert + langgraph + graceful-degradation + pytest-api-testing + fastapi + claude-api consulted; decisions captured.
- [x] **Anti-duplication cross-module audit** — Step 0 GATE evidence in compose.py docstring (~30 lines audit trail).
- [x] **State machine** — N/A (pure compose data; no StateGraph).
- [x] **Tools** — N/A (this ticket; tools land at T-tools-1..4 which depend on T-prompts-1).
- [x] **External calls wrapped** — N/A (zero external calls; pure file reads + string composition).
- [x] **LLM observability** — N/A (no LLM call this ticket).
- [x] **Cache prefix architecture** — `cache_control: ephemeral` on slots 1-6 + `prompt_cache_key=tenant_id` per spec § 8.2 + § 10.2. NO timestamps / NO mid-block tenant_name / NO PII enforced by arch tests.
- [x] **Cache TTL choice documented** — default Anthropic 5min (per spec § 8 + claude-api skill). Per-tenant LiteLLM `cache={"prompt_cache_key": str(tenant_id)}` isolates per-tenant cache buckets. 1h opt-in deferred to orchestrator-level wiring (downstream ticket may justify).
- [x] **Cache hit metrics validated** — synthetic Anthropic cache simulator in `test_cache_hit_rate.py` proves ratio ≥85% (actual 90% across 3 tenants × 10 turns). Production telemetry lands when orchestrator wires LiteLLM client (per spec § 8.5).
- [x] **Eval goldens** — N/A (V-AE-27 cache hit rate via synthetic simulator is the validator; voice fidelity goldens land at T-rubric-1 + T-eval-*).
- [x] **RAG** — N/A (Slot 7 KB_CONTEXT_RAG NOT cached; lives in `task_specific` per orchestrator-level wiring).
- [x] **AsyncPostgresSaver** — N/A (no checkpointer in T-prompts-1; lands at orchestrator).
- [x] **PII sanitization** — 4 PII categories (email regex + phone regex + timestamp regex + forbidden-token list) enforced on cacheable slots by `test_comunify_no_pii_in_cacheable_slots.py`. Tessl rule honored via dataload pipeline (no `response_model=` here since no FastAPI route).
- [x] **Spanish neutro** — Slot 1 + Slot 2 + Slot 3 + Slot 4 templates use tuteo neutro tense ("respondes", "puedes", "tienes", "haces") with strict NO voseo enforcement. Exception: Slot 5 BRAND_VOICE per-tenant (voz tenant respeta dialecto — Anabella es-AR voseo distilled OK per sales-agent voice SSoT). Micro-anchor template carries voseo-allowed magic comment because it renders per-tenant dialect.
- [x] **Tenant isolation** — `prompt_cache_key=tenant_id` isolates per-tenant cache buckets; Anthropic prompt cache `cache_control` markers do NOT cross tenant bucket. Test `test_cross_tenant_cache_isolation_slot_5_varies()` cements.
- [x] **Conventional commits** — to apply at commit step.

---

## Risks / Forward Notes

| Item | Note |
|---|---|
| Slot 5 cache invalidation event wiring | When `voice_cloning_ratified` domain event fires (Story 12 T-voice-3), orchestrator MUST bump per-tenant LiteLLM cache (e.g., new `prompt_cache_key` salt or explicit invalidation). Out of scope for T-prompts-1 (downstream T-voice-3 bridge). |
| LLM-side substitution markers list | Slot 4 has 4 placeholders (`{brand_name}`, `{creator_name}`, `{creator_email}`, `{emergency_line_by_country}`). Adding a 5th REQUIRES extending `_ALLOWED_LLM_SIDE_MARKERS` in test + verifying orchestrator/specialist runtime fills it AT generation time (NOT Python-side pre-compose). Arch test cements. |
| Real production cache hit rate measurement | Synthetic simulator proves COMPOSE PIPELINE is byte-stable. Real V-AE-27 production threshold (`copilot_llm_call.cache_read_input_tokens / cache_creation_input_tokens` ratio per tenant per spec § 8.5) comes online when orchestrator wires LiteLLM. Forward note. |
| Slot 6 channel registry decoupling | Currently uses static `SLOT_6_CHANNEL_FORMAT_HINT` dict. T-channels-N integration may replace with `format_for_channel(...)` from `luana_core_channels`. Static variant is intentional for now (per-channel cache prefix invariance + 4 fixed channels). |
| Pattern lift to luana_core_agentic_prompts | Decision pending 3rd brand consumer. If Pulse/Plenum/future brand introduces compose.py with same Slot 1/2/6 boilerplate, threshold met → lift compose_messages + cacheable_prefix_blocks to shared, keep slot-3/4/5 per-brand. Audit-trail in compose.py docstring. |

---

## State after this ticket

- 8 dependent tickets unblocked: T-tools-1..4 (4 tools), T-guards-1..4 (4 guardrails), T-voice-3 (voice compiler bridge).
- Cache hit rate target ≥85% validated synthetically (90% actual).
- 4 LLM-side substitution markers in Slot 4 ready for orchestrator runtime fill.
