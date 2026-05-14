# T-voice-4 IMPL-LOG — Voice cloning end-to-end pipeline tests (3 fixtures AR/CL/MX + low_confidence + arch + cost budget)

**Ticket**: T-voice-4 (06-tickets.yaml line 562)
**State**: done
**Owner**: builder-agentic (Opus 4.7 per R23 — `production_code: false` so Sonnet eligible, but kept Opus for batch consistency since fixtures touch voice patterns)
**Estimate**: 4h
**Actual**: ~1h (within batch)
**Date**: 2026-05-14
**Validators GREEN**: V-AE-6, V-AE-9, V-AE-21, V-AE-28, V-AE-29, V-AE-30, V-F-12

## § Skills Consulted (Step 0 GATE)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Tests cover voice cloning pipeline end-to-end. § Spanish neutro rule: tests in AR voseo style use magic comment `<!-- voseo-allowed: AR persona fixture -->`. | Magic comment used in Anabella AR fixture file docstring. ✅ |
| `sales-agent-expert` | Fixtures synthesise 50-chat datasets per persona programmatically. Voseo allowed in `sales_agent` voice output → fixtures testing AR persona include voseo lexicon explicitly. Pre-commit hook honors magic comment. | ✅ |
| `tessl__pytest-api-testing` | 4 fixture files + 1 smoke + 1 cost budget — all use in-memory FakeLiteLLMService + parametrized assertions. | Pattern applied consistently across all 6 files. ✅ |
| `tessl__graceful-degradation` | Low confidence path test asserts orchestrator returns CompiledVoice + emits `VoiceDistillationFailedV1` or `completed_low_confidence` (graceful degradation, never raises). | ✅ Tested explicitly. |
| `tessl__langgraph` | NOT applicable. | Skipped. |
| `tessl__fastapi` | NOT applicable. | N/A. |

## § Files created

6 test files:

1. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_anabella_ar.py` — 5 tests (es-AR voseo natural; voseo-allowed magic comment)
2. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_trini_cl.py` — 4 tests (es-CL tuteo chileno; flags voseo as forbidden in asi_no)
3. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_pablo_mx.py` — 4 tests (es-MX neutro broad; no voseo, no chilenismos, no MX local slang)
4. `comunify/backend/tests/agentic_evals/voice_cloning/test_voice_distillation_low_confidence.py` — 4 tests (low confidence → `completed_low_confidence` or `failed`, audit + outbox carry low-confidence marker)
5. `comunify/backend/tests/agentic_evals/smoke/__init__.py` (anchor) + `smoke_voice_distillation.py` — 1 end-to-end smoke (distill → bridge → emit VoiceRatifiedV1 → handler invalidates cache)
6. `comunify/backend/tests/agentic_evals/cost_budget/__init__.py` (anchor) + `test_cost_budget_voice_distillation.py` — 4 tests (V-AE-21 ≤$0.18 USD/50 chats; happy path + exceeded + lower-budget override)

## § Design decisions

- **3 fixture personas in pure-test code**, not YAML loader. The 50-chat datasets are programmatic cycles over 10 base messages (per persona) to reach exactly 50. Persona signatures (vocabulario / asi_no / anclajes) hard-coded in wave fixture payloads.
- **Anabella AR**: voseo natural — "tenés que probarlo", "te lo bancás", "dale, vamos", "una banda", "obvio", "sos una capa". Voseo-allowed magic comment in module docstring.
- **Trini CL**: tuteo chileno — "po", "cachai", "bacán", "filete", "cuídate harto". `asi_no` flags voseo as forbidden ("NUNCA copies voseo argentino (sos / tenés)").
- **Pablo MX**: neutro broad — no MX-local slang (no "wey", "órale", "chido"). `asi_no` flags voseo + chilenismos + mexicanismos-locales. Asserts NO voseo conjugations survive into `compiled.vocabulario`.
- **Low-confidence path**: each wave returns ≤ 0.30 wave_confidence + wave_warnings. Tests assert final_status ∈ {`completed_low_confidence`, `failed`} + audit log `needs_manual_review=True` + outbox event carries low-confidence marker.
- **Smoke end-to-end**: stitches T-voice-1 (distill) → T-voice-3 bridge (compile + emit) → T-voice-3 handler (invalidate). Verifies the pipes between modules.
- **Cost budget tests**: happy path (0.015 + 3×0.045 = 0.150 USD ≤ 0.18); exceeded path (3×0.10 = 0.30 USD); lower kwarg override (default 0.18 → 0.10 → fail). Assert `DEFAULT_COST_BUDGET_USD == Decimal("0.18")` SSoT.

## § Tests audited

22 tests across 6 files:

- Anabella AR (5): dialect detection, 4 wave calls fired, cost within budget, compiles to system_instruction, no PII in compiled voice.
- Trini CL (4): tuteo chileno detected, voseo flagged as forbidden in asi_no, chilenismos in vocabulario, compiles to system_instruction.
- Pablo MX (4): neutro detected, asi_no excludes regional slang, NO voseo in compiled voice, compiles to system_instruction.
- Low confidence (4): confidence_score < threshold, status not just `failed`, audit log flags manual_review, outbox carries low-confidence marker.
- Smoke (1): distill → bridge → handler full chain.
- Cost budget (4): happy path under 0.18, default constant matches spec, exceeded surfaces warning, lower kwarg overrides default.

**Run result**: 22 tests GREEN.

## § Combined T-voice-1..4 test count

Full T-voice batch test count:
- T-voice-1: 23 smoke + 5 arch = 28
- T-voice-2: 22 PII/parser/worker + 3 arch = 25
- T-voice-3: 26 bridge + handler
- T-voice-4: 22 fixtures + smoke + cost budget

**Total: 101 tests GREEN** for voice cloning batch.

Full comunify suite regression: **815 passed, 9 skipped** (no regressions).

## § Default-flip detection (Step 0.5)

NOT triggered.

## § R23 enforcement

Tests authored by Opus 4.7 (batch consistency).

## § Out-of-scope (deferred)

- Real `RUN_LLM` integration tests against actual Anthropic API. Today: all LLM calls mocked via `FakeLiteLLMService`. Production opt-in via env var (mirrors `RUN_LLM_JUDGE=1` pattern in copilot quality eval).
- Per-fixture YAML loader (programmatic in-test synthesis kept — same pattern as existing eval simulator personas in nicolify, where archetype-aware personas YAML exists at `docs/specs/personas/`).
