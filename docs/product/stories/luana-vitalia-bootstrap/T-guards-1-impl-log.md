<!-- voseo-allowed: cite spec § 17.1 + Slot 4 j2 verbatim per R25 -->
# T-guards-1 implementation log — `medical_safety_no_diagnosis`

**Ticket:** T-guards-1 (Story 11 luana-vitalia-bootstrap)
**Owner:** Opus 4.7 (R23 — production AGENTIC code)
**Started:** 2026-05-14
**Files in scope:**
- `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py`
- `/home/chris/luana-platform/vitalia/backend/tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py`

## Skills Consulted

- `copilot-expert` — best-effort observability (try/except + structlog warning), tenant_id propagation invariant, no-skip rule trazas first. Decision: audit_log emission via `try/except` swallowing exception with structlog warning, NEVER breaks turn. Sanitize_payload from shared before persist.
- `sales-agent-expert` — anti-duplication §0 cardinal: input/output guardrails are vertical-medical surface (NEW, no shared base in luana-core). Slot 4 BRAND_VOICE separation respected: regex + classifier ops are deterministic + cheap, no LLM voice impact. Tenant isolation on every audit_log write.
- `tessl__langgraph` — N/A: this guardrail is NOT a LangGraph node (it's middleware in input/output pipeline order 3+6 per § 17.5). Pure async functions composable in pre/post LLM call hooks. No state graph involved.
- `tessl__graceful-degradation` — Rules 1+2: Haiku classifier LLM call wrapped in `asyncio.wait_for(timeout=5s)` + try/except. On timeout/error: graceful degradation — guard fires conservatively if regex matched (block), else passes through (do not block on classifier failure when regex didn't match — false-positive cost > false-negative cost for OUTPUT layer). Rule 6: structured logging with context.
- `tessl__pytest-api-testing` — function-scoped fixtures default; in-memory `_FakeAuditLog` + `_FakeLLMClassifier` per test. parametrize for input/output regex coverage. Async tests require `pytest.mark.asyncio` (already configured per existing T-guards-3 tests).
- `claude-api` (skill not invoked — Haiku classifier consumes existing `_LiteLLMServiceLike` Protocol pattern from extractor; no new Anthropic SDK direct calls in this guardrail per LiteLLM Proxy canonicalization PI-12 S1 T-1).

## Step 0 GATE — anti-duplication grep

```bash
$ grep -rln "medical_safety_no_diagnosis\|MedicalSafetyNoDiagnosis" /home/chris/luana-platform/ 2>/dev/null
/home/chris/luana-platform/vitalia/config/brand.yaml                                       # BrandConfig declarative reference
/home/chris/luana-platform/vitalia/backend/tests/unit/test_extensions_register_all.py      # EP-13 registry test
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py               # EP-13 registry placeholder
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py  # adversarial grader cross-ref comment
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py  # T-guards-1 placeholder

$ grep -rln "medical_safety_no_diagnosis\|MedicalSafetyNoDiagnosis" /home/chris/AISALESHT/backend/src/ 2>/dev/null
(empty)
```

**Verdict:** zero collisions. NEW vertical-medical surface. NO mirror risk per anti-duplication.md.

## Step 0.5 — default-flip detection

N/A — Story 11 greenfield, NO flag flips touched. Commit body NEED NOT include `## Flag flipped` section.

## Cross-module audit (NO-NEW-LAYER, EXTEND > REPLACE > NEW)

- ✅ `sanitize_payload` — CONSUMED from `luana_core_observability.recording.sanitization` (per anti-duplication.md SSoT row).
- ✅ `_LiteLLMServiceLike` Protocol — REUSED structural typing from sibling T-extractors-1 `medical_kb_extractor.py:120-134`. NEW `_LLMClassifierLike` Protocol below is a NARROWER subset (single method `aclassify_bool`) rather than mirror — explicit because guardrail only needs bool classification, not text generation.
- ✅ `_AuditLogLike` Protocol — REUSED structural typing pattern from sibling T-guards-3 (medical_disclaimer_required.py:108-124 + prompt_injection_block_reuse.py:148-163). Identical surface (tenant_id + patient_id + event_type + payload).
- ✅ Slot 4 reference — CONSUMED via static comment + spec citation. Slot 4 j2 file NOT modified by this ticket (T-prompts-1 cement immutable).
- ✅ Forced disclaimer reference (T-kb-3) — INPUT layer action mentions Slot 4 reminder + emergency line; downstream RAG retrieval handled by KB pack pipeline (out of guardrail scope).
- ❌ NO new Python class hierarchy created. Plain async functions + frozen dataclass result type, mirroring T-guards-3 `prompt_injection_block_reuse.py` shape.

## Inside-Out implementation order

1. Domain — pure helpers (`fires_input_regex`, `fires_output_regex`, `_FALLBACK_RESPONSE_TEMPLATE`).
2. Infrastructure — `_LLMClassifierLike` Protocol + `_AuditLogLike` Protocol.
3. Application — async `medical_safety_no_diagnosis_input_check` + `medical_safety_no_diagnosis_output_check` (composing regex + classifier + audit_log + best-effort observability + graceful degradation).
4. Result types — frozen dataclasses (`InputGuardrailResult`, `OutputGuardrailResult`).

API: NOT exposed via FastAPI router (this is middleware pipeline component, not endpoint).

## State machine

N/A — guardrail is stateless middleware. Each invocation independent.

## Tool implementation

N/A — guardrail is NOT a LangChain tool, it's middleware that wraps tool/LLM dispatch.

## Prompt cache slot architecture

N/A — guardrail does NOT compose system prompts. Slot 4 already cemented by T-prompts-1.

## Observability writes

- `audit_log` event_type=`medical_safety_no_diagnosis_fired` (severity medium per § 17.1).
- Payload sanitized via `sanitize_payload` BEFORE write (lengths + classifier confidence + detection_pattern only — NEVER user_msg / llm_response verbatim).
- `try/except + structlog.warning("medical_safety_no_diagnosis.audit_log_failed", exc=str(e))` per `.claude/rules/copilot-observability.md`.
- LLM call to Haiku classifier — separate cost recording surface via LiteLLM Proxy CustomLogger bridge (PI-12 S1 T-1 cement). This guardrail does NOT directly call `cost_recorder.pop_cost` — caller's existing observability hooks (sales_agent callback handler) capture the Haiku call cost. We just delegate via `_LLMClassifierLike.aclassify_bool` Protocol.

## RAG / Qdrant

N/A — guardrail does NOT issue RAG queries. INPUT layer mentions "Slot 4 + disclaimer + derive to doctor + emergency line" as augmentation hint passed to caller (not retrieved by this module).

## Eval goldens

A3 (adversarial pass^5 ≥0.95) is OUT OF SCOPE per ticket: "Adversarial diagnosis persona pass^5 ≥0.95 — DEFER (grader scenario file is T-eval-1 W17 cross-ticket, document gap in result.md)". Documented gap in result.md.

This guardrail unit test suite (T-guards-1 in scope) covers A1 + A2 + observability + graceful-degradation + tenant isolation invariants. The adversarial pass^k bar is exercised end-to-end by V-AE-11 (T-eval-1 W17).

## Commands run

```bash
date -u +%Y-%m-%d                                                # → 2026-05-14
cd /home/chris/luana-platform/vitalia/backend
uv run pytest tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py -v --tb=short
uv run ruff check src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py
uv run ruff format --check src/modules/vitalia/agentic/guardrails/medical_safety_no_diagnosis.py tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py
```

## Iter 1 — RED then GREEN

- RED: 47-test test file authored. `uv run pytest tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py` → ImportError (module doesn't exist) — RED confirmed.
- GREEN: implementation written; first run revealed regex test case `Te diagnostico un cuadro depresivo mayor` not covered by spec subject list. Resolution: extend OUTPUT subject list APPEND-ONLY (`diabetes` + `cuadro` Spanish clinical idiom — true positives rise; false positives bounded by 80-char non-greedy gap). Documented inline with rationale comment per safety-ratchet protocol.
- Second-pass GREEN run: 47/47 PASS in 0.08s. Wider guardrails suite (V-AE-8): 99/99 PASS in 0.12s. Downstream regression `tests/unit/test_extensions_register_all.py`: 18/18 PASS.
- Lint + format: `ruff check` + `ruff format --check` clean post auto-format adjustment.

## Parallel-session commit collision (2026-05-14, post-build)

During final commit on `/home/chris/luana-platform/`, a concurrent agent was running T-tools-4 / T-tools-3 commits. My `git add` + `git commit` operations interleaved with that agent — final HEAD is commit `7dc63a3` whose message attribution reads `feat(story-11/T-tools-4)` but whose contents include MY 3 T-guards-1 files (medical_safety_no_diagnosis.py + __init__.py + test_medical_safety_no_diagnosis.py) ALONGSIDE the other agent's T-tools-4 + T-tools-3 files.

Verification at HEAD post-collision:
```bash
$ git show HEAD --stat | grep medical_safety_no_diagnosis
.../guardrails/medical_safety_no_diagnosis.py      |  629 +++++++++++
.../guardrails/test_medical_safety_no_diagnosis.py |  652 +++++++++++
$ git show HEAD --stat | grep guardrails/__init__
.../modules/vitalia/agentic/guardrails/__init__.py |   21 +-
$ uv run pytest tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py -v
47 passed in 0.06s
```

T-guards-1 work IS preserved at HEAD; tests GREEN; lint clean. Only the commit message attribution is misleading (the message says T-tools-4 but the diff contains 5 files spanning 3 tickets).

Per `.claude/rules/parallel-safety.md` M5: "Push falla → STOP, reportar Chris. NO `git pull`." Decision: DO NOT `git push`. The orchestrator should reconcile the commit attribution (either rebase to split commits or accept the multi-ticket commit with a follow-up clarification commit). Builder's responsibility is bounded — work persisted, tests green, no destructive recovery attempted.

**Action for orchestrator:** review commit `7dc63a3` on luana-platform/main HEAD. Decide whether to:
(a) Push as-is and follow up with `docs(story-11): clarify commit 7dc63a3 spans T-tools-3 + T-tools-4 + T-guards-1` clarification, OR
(b) Rebase to split the commit into per-ticket commits (per Conventional Commits + per-ticket attribution discipline), OR
(c) Escalate to Chris for ratification of the collision recovery path.
