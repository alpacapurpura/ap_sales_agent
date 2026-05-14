# T-prompts-1 — Result

**Ticket:** Prompt slot architecture 10 slots + Slot 4 NEW MEDICAL_SAFETY_RAILS + cache_control
**State:** tests-passing (developing → developed, awaiting auditor verdict per R30)
**R23:** production_code=true → Opus 4.7 EXCLUSIVE
**Date:** 2026-05-14
**Builder:** Claude Opus 4.7 (1M context)

---

## TL;DR

51/51 validators GREEN on iter 1. 10-slot Anthropic-native cache architecture per spec § 8 + § 10. Slot 4 NEW vertical-medical overlay with sandbox markers DQ2 + ASÍ HABLAS/NO blocks. Cache prefix invariance enforced via parametrized PII/interpolation scan across 8 cacheable slot variants × 4 PII categories. Synthetic in-process cache simulator validates ≥85% hit rate without real Anthropic API call. Anti-duplication audit Step 0 GATE: NEW justified vs existing `luana_core_sales_agent.application.prompts.compose` (different protocol — Anthropic content blocks vs OpenAI prefix-stability). Lint clean, format clean, no regression introduced.

## Deliverables

### Production code (luana-platform main)

- `vitalia/backend/src/modules/vitalia/agentic/prompts/compose.py` — `SLOT_1_STATIC_IDENTITY`, `SLOT_2_STATIC_TOOLS_HINT`, `SLOT_6_CHANNEL_FORMAT_HINT[channel]` (4 variants: whatsapp/im_dm/email/web) constants + `load_slot_3_sales_playbook()` + `load_slot_4_medical_safety_rails()` + `load_micro_anchor(brand_name, clinic_name, voice_preset_key)` (~28 tokens per turn) + `compose_messages(...)` Anthropic Messages API content-block builder + `cacheable_prefix_blocks(channel, brand_voice_compiled)` test helper exposed in public API + `prompt_cache_key(tenant_id) -> str` for LiteLLM `cache={"prompt_cache_key": ...}`. ~280 lines including verbose docstrings + spec citations + anti-duplication audit notes.

- `vitalia/backend/src/modules/vitalia/agentic/prompts/slot_4_medical_safety_rails.j2` — NEW vertical-medical overlay template per D5. Sandbox markers DQ2 (`<<TRANSCRIPT_BEGIN>>` / `<<TRANSCRIPT_END>>` per 03-arch § 9.2 prompt-injection defense) + ASÍ HABLAS / ASÍ NO bullet sections per 02-design § 11.3 + LLM-side substitution markers (`{doctor_specialty}`, `{doctor_name}`, `{clinic_name}`, `{emergency_line_by_country}`, `{condición}`, `{medicación}`, `{alternativa}`).

- `vitalia/backend/src/modules/vitalia/agentic/prompts/slot_3_sales_playbook_vertical_medical.j2` — Cross-tenant cacheable playbook for dental/psychology/psychiatry/wellness clinics LatAm. Booking flow + treatment followup cadence + cancellation/reschedule + escalation triggers + out-of-scope sections.

- `vitalia/backend/src/modules/vitalia/agentic/prompts/micro_anchor_per_turn.j2` — Per-turn anti-drift micro-anchor template (~28 tokens). Lives in Slot 8 NOT cached (safe to interpolate per-tenant values).

### Tests (luana-platform main)

- `vitalia/backend/tests/architecture/test_vitalia_slot_4_safety_markers_present.py` — A1 (12 tests including 4-keyword parametrize): sandbox markers present + correct order + injection rationale + ASÍ HABLAS/NO sections + 4 critical safety prohibitions verbatim + disclaimer obligation.

- `vitalia/backend/tests/architecture/test_vitalia_no_pii_in_cacheable_slots.py` — A2 (35 tests including 8-slot × 4-category parametrize): no `{tenant_name}`/`{tenant_id}`/`{conversation_id}`/`{turn_*}`/`{request_id}`/`{patient_*}` etc. + no email regex match + no phone regex match + no ISO timestamp regex match + Slot 4 LLM-side markers limited to allowlist + cacheable prefix byte-equal across distinct tenants (slots 1-4 + 6) + every cacheable block has `cache_control: ephemeral` marker.

- `vitalia/backend/tests/agentic_evals/cache/test_cache_hit_rate.py` — A3 (4 tests): aggregate cache hit rate ≥85% across 3 tenants × 10 turns simulated (synthetic in-process cache simulator, no real Anthropic API) + cross-tenant isolation (Slot 5 BRAND_VOICE varies, prompt_cache_key isolates buckets) + within-tenant 100% hit rate on repeated turn + `prompt_cache_key` str coercion.

- `vitalia/backend/tests/agentic_evals/cache/__init__.py` — package marker.

### Docs (AISALESHT development)

- `docs/product/stories/luana-vitalia-bootstrap/T-prompts-1-impl-log.md` — implementation log with Skills Consulted (7 skills), Step 0 GATE evidence (3 grep commands + decision rationale), iteration log, anti-duplication file:line evidence, architecture decisions, cost analysis, R3 downstream regression scope.
- `docs/product/stories/luana-vitalia-bootstrap/T-prompts-1-result.md` — this file.

## Acceptance criteria coverage

| AC | Test file | Tests | Result |
|---|---|---|---|
| A1 (sandbox markers + ASÍ HABLAS/NO blocks) | `tests/architecture/test_vitalia_slot_4_safety_markers_present.py` | 12 (incl. 4-keyword parametrize) | PASS |
| A2 (no PII / no dynamic interpolation in cacheable slots 1-4 + 6) | `tests/architecture/test_vitalia_no_pii_in_cacheable_slots.py` | 35 (incl. 8-slot × 4-category parametrize) | PASS |
| A3 (cache hit rate ≥85% slots 1-6 via cache_read/cache_creation ratio) | `tests/agentic_evals/cache/test_cache_hit_rate.py` | 4 | PASS — simulated 90% hit rate (9/10 turns × 3 tenants) |

## Validators V-AE-22

```
cd /home/chris/luana-platform/vitalia/backend && \
  .venv/bin/pytest tests/agentic_evals/cache/test_cache_hit_rate.py -v
```

Result: 4/4 PASS, threshold cache_hit_rate_min: 0.85 satisfied (simulated 0.90).

## Quality gates (vitalia native)

| Gate | Command | Result |
|---|---|---|
| Lint | `.venv/bin/ruff check src/modules/vitalia/agentic/prompts/ tests/architecture/test_vitalia_slot_4_*.py tests/architecture/test_vitalia_no_pii_*.py tests/agentic_evals/cache/ --no-cache` | PASS |
| Format | `.venv/bin/ruff format --check src/modules/vitalia/agentic/prompts/ tests/architecture/test_vitalia_slot_4_*.py tests/architecture/test_vitalia_no_pii_*.py tests/agentic_evals/cache/` | PASS (6 files already formatted) |
| Targeted tests (51 tests) | `.venv/bin/pytest tests/architecture/test_vitalia_slot_4_safety_markers_present.py tests/architecture/test_vitalia_no_pii_in_cacheable_slots.py tests/agentic_evals/cache/test_cache_hit_rate.py -v` | 51/51 PASS |
| Full vitalia suite (regression check) | `.venv/bin/pytest tests/ -v` | 246 PASS / 16 SKIP / 3 FAIL — 3 pre-existing failures in `test_vitalia_personas_yaml_completeness.py` (T-personas-N ticket out of T-prompts-1 scope; failures pre-existed). T-prompts-1 introduces 0 new failures. |

## Anti-duplication Step 0 GATE evidence

Decision: NEW justified.

- Existing `luana_core_sales_agent.application.prompts.compose:1-32` header explicitly says: "OpenAI prompt cache (April 2026) requires ≥1024 contiguous tokens of unchanged prefix to activate. Kimi K2.6 and DeepSeek V3/V4 ship the same auto-cache contract over OpenAI-compatible APIs (no `cache_control` annotations, just prefix stability)." → DIFFERENT PROTOCOL.
- Existing module exposes 7 cacheable + 4 volatile **string fragments** with markdown protocol `[TOOL_REQUEST: ...]`. Vitalia spec § 8.2 + § 10.2 demands Anthropic native `cache_control` content blocks (Messages API multi-block content) with 6 cacheable slots + Slot 4 NEW vertical-medical overlay.
- Lift-to-shared deferred — protocols inverted (OpenAI auto-detects via prefix bytes; Anthropic requires explicit cache_control markers per block). Future Story 11.bis or general SDD task can lift if 3rd Anthropic-native vertical brand emerges.

## Decisions honored (per 05-guidelines.md § 6)

- **D5** (Slot 4 MEDICAL_SAFETY_RAILS NEW prompt slot): vertical-medical overlay implemented as cacheable Slot 4 with sandbox markers DQ2 + ASÍ HABLAS/NO blocks.
- **D9** (Chrome UI Spanish neutro pure tuteo): N/A to internal LLM slot prompts. Vitalia internal slot architecture does NOT inherit chrome UI Spanish neutro tuteo cement — slot prompts are LLM-internal sales-agent voice; voice diversity (voseo OK Aurora, neutro CL Mindful, neutro broad MX Sanaré) lives in Slot 5 BRAND_VOICE per-tenant via `personality_profiles.system_instruction` (sales-agent SSoT cement preserved).

## Out-of-scope (per ticket spec)

- ❌ Guardrails (T-guards-* — separate tickets).
- ❌ Tools (T-tools-* — separate tickets).
- ❌ Orchestrator wiring (T-workflow-1 will consume `compose_messages(...)` + LiteLLM cache parameters).
- ❌ Real Anthropic API integration test (downstream T-workflow-1 + observability ticket).

## Cost analysis (production projection)

Cacheable region (slots 1-6) approx token count:
- Slot 1 STATIC_IDENTITY: ~53 tokens
- Slot 2 STATIC_TOOLS_HINT: ~188 tokens
- Slot 3 SALES_PLAYBOOK: ~475 tokens
- Slot 4 MEDICAL_SAFETY_RAILS: ~375 tokens
- Slot 5 BRAND_VOICE: ~800 tokens (typical PersonalityProfile compiled v2)
- Slot 6 CHANNEL_FORMAT_HINT: ~63 tokens
- **Total cacheable ≈ 1,950 tokens** (≥1,024 token Anthropic minimum cement; well over).

At 85% target hit rate, steady-state per-turn input cost dominated by Slots 7-10 volatile + cache_read on Slots 1-6 (~$0.002 per turn at Sonnet pricing).

## Next steps (downstream tickets)

- T-tools-2..4 (R23 Opus): consume `compose_messages` for tool-context injection.
- T-workflow-1 (R23 Opus): wire `compose_messages` to LiteLLM `acompletion(model=..., messages=..., cache={"prompt_cache_key": prompt_cache_key(tenant_id)})` + observability instrumentation for real production cache hit rate measurement (`copilot_llm_call.cache_read_input_tokens` + `cache_creation_input_tokens` columns).
- T-guards-1..3 (R23 Opus): consume Slot 4 sandbox markers `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` for prompt-injection guardrail middleware.

## Last-line return contract

```
done -> docs/product/stories/luana-vitalia-bootstrap/T-prompts-1-result.md
```
