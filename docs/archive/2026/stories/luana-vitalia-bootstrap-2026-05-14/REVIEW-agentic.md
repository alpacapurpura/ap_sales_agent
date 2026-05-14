<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# REVIEW-agentic.md — Story 11 luana-vitalia-bootstrap

## Verdict: PASS (with informational notes)

- **Date:** 2026-05-14
- **Auditor:** auditor-agentic Opus 4.7 (Sesion 5 sample audit)
- **Scope:** 17 AGENTIC tickets — time-boxed ~30 min sample (4 result.md anchors + 6 code paths spot-check + V-AE-18 verification + R23 + R10 anti-duplication + R3 downstream regression)
- **Knowledge cutoff:** Opus 4.7 = Jan 2026. Audit performed natively on local repos at 2026-05-14 (live ETL not consulted; canonical doc anchors verified via local rule files).

---

## C1 — Code: PASS

- **Test counts (consumed from per-ticket result.md, NOT re-executed):**
  - T-prompts-1: 51/51 (12 slot-4 markers + 35 PII-in-slots + 4 cache hit)
  - T-rubric-1: 39/39 + 19/19 regression
  - T-extractors-1: 25/25 (`medical_kb_extractor.py` extends `BaseExtractionOrchestrator`)
  - T-extractors-2: 10/10 + 353/353 downstream
  - T-workflow-1: 12/12 V-AE-7 + 510/510 vitalia downstream regression GREEN
  - T-kb-1/2/3: 13/13 + 19/19 + 37/37 (joint kb_packs 32+69 GREEN)
  - T-guards-1: 47/47 + 99/99 V-AE-8 + 18/18 downstream (`tests/unit/test_extensions_register_all.py`)
  - T-guards-2: GREEN (count per Sesion 4 close)
  - T-guards-3: 64/64 + 367 regression
  - T-tools-1: 38/38 + 100/100 core regression
  - T-tools-2: 13/13 + 121 downstream
  - T-tools-3: 15/15 (A1+A2+A3)
  - T-tools-4: 24/24 + 62/62 V-AE-5
  - T-eval-1: **132/132 PASS** (full agentic eval suite incl. smoke + grader + cost_budget + observability + arch fitness)
- **LangGraph 2.0 patterns** — `treatment_followup_workflow.py` lines 42-49 (`from langgraph.graph import END, StateGraph`), line 58 (`TreatmentFollowupState(TypedDict, total=False)` with `tenant_id` required + `iterations` anti-loop guard), line 98 (`CheckpointerProtocol` structural typing for runtime swap MemorySaver→RedisSaver per D10). Conditional edges per node + 17 transitions + entry router. No subagents (deepagents `task` not used — pure StateGraph is correct shape for cron-driven cadence workflow).
- **Guardrails composition** — `medical_safety_no_diagnosis.py:74-83` exposes 8 public symbols + structural Protocols (`_LLMClassifierLike`, `_AuditLogLike`) — NARROWER than sibling LLM service surface (single `aclassify_bool` method) per anti-duplication §0 cardinal.
- **Lint + format:** all per-ticket result.md cite `ruff check` + `ruff format --check` PASS native.

## C2 — Spec: PASS

| Validator | Test path | Sesion 4 status |
|---|---|---|
| V-AE-1 prompt injection | `tests/agentic_evals/smoke/smoke_prompt_injection.py` | PASS |
| V-AE-3 cross-tenant isolation | `tests/agentic_evals/smoke/smoke_cross_tenant.py` | PASS |
| V-AE-4 HIPAA disclaimer | `tests/agentic_evals/smoke/smoke_hipaa_disclaimer.py` | PASS |
| V-AE-5 follow-up adherence | tools/treatment_followup_check tests | PASS (T-tools-4 62/62) |
| V-AE-7 D0→D90 workflow | T-workflow-1 12/12 | PASS |
| V-AE-8 guardrails 4-guard layer | T-guards-* 99/99 | PASS |
| V-AE-10 medical fidelity happy | grader/test_vertical_medical_fidelity_happy.py | PASS |
| V-AE-11 medical fidelity adversarial | grader/test_vertical_medical_fidelity_adversarial.py | PASS |
| V-AE-12 voice fidelity per fixture | grader/test_voice_fidelity_per_fixture.py | PASS |
| V-AE-13 no hallucination | grader/test_no_hallucination.py | PASS |
| V-AE-14/15/16 cost budgets | cost_budget/*.py | PASS |
| V-AE-17 cost bucket invariant | `tests/architecture/test_vitalia_cost_bucket_invariant.py` | PASS |
| V-AE-18 trace invariants | `tests/agentic_evals/observability/test_trace_invariants.py` | **PASS** (test exists, verified inline) |
| V-AE-19 adversarial combined | smoke + grader adversarial | PASS |
| V-AE-22 cache hit rate ≥85% | `tests/agentic_evals/cache/test_cache_hit_rate.py` | PASS (simulated 0.90) |

### V-AE-18 absent-diagnosis verification — classification (C): **NOT A GAP**

The orchestration prompt posed V-AE-18 as a conditional "absent → diagnosis (A) spec drift / (B) typo / (C) legitimate gap." Verification:
- `04-validators.yaml:608-614` — V-AE-18 IS defined with `must_pass: true`, points to `tests/agentic_evals/observability/test_trace_invariants.py`.
- `06-tickets.yaml:1785` — T-eval-1 carries V-AE-18 in its `validators_pass:` list.
- File present at `luana-platform/vitalia/backend/tests/agentic_evals/observability/test_trace_invariants.py` (read 120 lines — 7 invariants I1-I7 documented inline; covers cost_usd > 0, tokens accounted, PII sanitized, medical_audit_log linked, eval_kind sentinel cost bucket separation).
- T-eval-1-result.md cites 132/132 PASS which includes this file.

→ V-AE-18 is implemented + green. No spec drift, no typo, no gap. Move on.

## C3 — Architecture: PASS

- **LangGraph state machine** — `treatment_followup_workflow.py:58-91` `TreatmentFollowupState` TypedDict with `tenant_id` REQUIRED, partial-state convention (`total=False`), `iterations` anti-loop guard, `cost_accumulated_usd` per-node accumulator, `safety_triggered` + `paused_reason` for escalation routing. 10 nodes (`d0_init` / `d5_check` / `d5_complete` / `d14_check` / `d14_complete` / `d90_check` / `completed` + 3 paused branches + 1 dropped terminal) + 17 transitions + entry router.
- **Prompt slot architecture (10-slot)** — `compose.py:14-28` cement diagram: 6 cacheable slots (1-6) + CACHE BOUNDARY + 4 volatile slots (7-10). Slot 5 BRAND_VOICE is the ONLY per-tenant cacheable slot — Slots 1-4 + 6 invariant cross-tenant. Anthropic native `cache_control: {"type": "ephemeral"}` per content block; LiteLLM `cache={"prompt_cache_key": str(tenant_id)}` for per-tenant isolation.
- **Cache TTL + PII hygiene** — `compose.py:35-45` forbidden creep guard documented:
  - ❌ `{tenant_name}` interpolated mid-block in slots 1-4
  - ❌ Timestamps / conversation_id / turn_counter in slots 1-6
  - ❌ Patient name / phone / email in any cacheable slot
  - ❌ KB chunks in cacheable slots (Slot 7 NOT cached)
  - LLM-side substitution markers (`{doctor_specialty}`, `{doctor_name}`, `{clinic_name}`, `{emergency_line_by_country}`) live in Slot 4 raw text but are NEVER Python-side interpolated pre-compose — model fills them at generation time. This is correct per Anthropic prompt cache contract.
  - Arch fitness `test_vitalia_no_pii_in_cacheable_slots.py` 35 parametrized tests cement (8 slots × 4 PII categories).
- **Anti-duplication R10** — strict compliance verified file-by-file:
  - `medical_kb_extractor.py:66+212` — `from luana_core_extraction.base_orchestrator import BaseExtractionOrchestrator` + `class MedicalKBExtractor(BaseExtractionOrchestrator)` — EXTEND, not mirror.
  - `dental_history_extractor.py:181` — `class DentalHistoryExtractor(BaseExtractionOrchestrator)` — EXTEND.
  - `medical_safety_no_diagnosis.py:81` — `from luana_core_observability.recording.sanitization import sanitize_payload` — CONSUME shared, never re-implement.
  - `prompt_injection_block_reuse.py:20-39` — Story E "base" is prompt-side convention (sandbox markers), NOT a Python class — vitalia adds runtime regex detector ON TOP of cement markers + audit_log emitter. "reuse" = reference + extend, not mirror. NEW vertical-medical guard.
  - `treatment_followup_workflow.py:19-23` — `TreatmentFollowupWorkflow` class — NEW, no collision (grep cross-codebase: zero). RedisSaver runtime D10 ratified as TARGET, package not yet installed.
  - `compose.py:47-61` — anti-duplication audit cited verbatim: `luana_core_sales_agent.application.prompts.compose` exists BUT uses OpenAI-compatible auto-cache via prefix stability — DIFFERENT PROTOCOL (Anthropic native `cache_control` content blocks). NEW justified, lift-shared deferred per protocol mismatch.
- **Tools Pydantic schema** — `prepaid_payment_check.py:76-79` cement: "tenant_id intentionally OMITTED (ctx injection)" + repos enforce tenant_id filter natively. Tool Pydantic input schema has `booking_id` only.

## C4 — Cross-cutting: PASS

- **Tenant isolation (cardinal)** — verified across all 4 agentic tools:
  - `prepaid_payment_check.py:21-24, 149, 167, 200-208, 270, 299, 329` — tenant_id required kw param, repos enforce filter intrinsically
  - `treatment_followup_check.py:46-48, 209-212, 355, 368, 386, 401, 417, 450` — same pattern, tenant_id NEVER in input schema
  - `medical_consent_request.py` + `appointment_reschedule_with_doctor.py` — same pattern documented in result.md
  - `treatment_followup_workflow.py:30-33` — state carries tenant_id, checkpointer thread_id composite = `(tenant_id, treatment_id)` per 02-design § 4.4
  - `medical_safety_no_diagnosis.py` — tenant_id required `kw_only` on both entry points + 2 dedicated tests assert audit_log propagation
- **Brand voice** — Slot 5 BRAND_VOICE per-tenant via `personality_profiles.system_instruction` (sales-agent SSoT cement preserved). Slot 3 sales playbook uses voseo (`querés`, `Tenés`) — OK per `sales-agent-brand-voice.md` exception ("voz del agente respeta voz del tenant"). Guardrail refusal strings (chrome) stay Spanish neutro tuteo (`prompt_injection_block_reuse.py:53-60` — "No puedo seguir esa instrucción. ¿En qué te puedo ayudar con tu consulta?") per spec § 17.4 cement.
- **Spanish neutro / voseo separation** — correct split:
  - Chrome (refusal strings, audit_log human-readable) = neutro tuteo
  - Agent voice output = Slot 5 BRAND_VOICE (may be voseo if tenant Aurora/AR)
  - Slot 3 sales playbook examples = voseo demonstrating tenant voice (LLM consumed, not user-facing string per se)
- **PII sanitization** — `sanitize_payload` consumed from shared `luana_core_observability.recording.sanitization` per `.claude/rules/anti-duplication.md` SSoT row. NEVER re-implemented. T-guards-1 result.md cites 2 dedicated tests asserting no verbatim text leaks (INPUT + OUTPUT layers).
- **Cost bucket invariant** — verified at `tests/architecture/test_vitalia_cost_bucket_invariant.py:99-202`:
  - Production source code MUST NOT reference `eval_simulator_llm_call` (production writes `copilot_llm_call` ONLY)
  - Eval test code MUST NOT INSERT into `copilot_llm_call` (eval writes `eval_simulator_llm_call` ONLY)
  - Eval smoke tests MUST NOT import `copilot_llm_call` repository
  - Production/Eval table name constants asserted as cement (V-AE-17 PASS)

## C5 — Trace: PASS

- **Observability writes (best-effort try/except)** — `medical_safety_no_diagnosis.py` `_emit_audit_log()` per-result.md: `try/except + sanitize_payload + structlog warning, NEVER breaks safety verdict` (R23 production-critical invariant). 6 dedicated test cases (4 input + 2 output) covering audit_log raising AND classifier raising paths.
- **Eval cost bucket separation** — `test_trace_invariants.py:54-55, 73, 153, 372-377` — `eval_kind: str | None` field on synthetic records; `eval_kind=None` for production, `"eval"` for eval runs; arch fitness gate V-AE-17 enforces production source code NEVER references `eval_simulator_llm_call` and eval test code NEVER writes to `copilot_llm_call`.
- **R3 downstream regression** — `.claude/rules/auditor-downstream-regression.md:83-88` carries 5 vitalia/agentic surface rows:
  - `vitalia/backend/src/modules/vitalia/agentic/guardrails/` → 4 downstream tests
  - `vitalia/backend/src/modules/vitalia/agentic/prompts/compose.py` → 4 downstream tests
  - `vitalia/backend/src/modules/vitalia/agentic/tools/` → 2 downstream tests
  - `vitalia/backend/src/modules/vitalia/agentic/extractors/` → 3 downstream tests (incl. `test_extraction_orchestrator_inheritance.py` arch gate)
  - `vitalia/backend/src/modules/vitalia/copilot/workflows/treatment_followup_workflow.py` → 2 downstream tests
  - + `tests/agentic_evals/grader/_internal/` → 4 grader tests
  R3 SSoT coverage = COMPLETE. T-eval-1-result.md cites the append commit (`d65d2bbe`) as the SSoT update mechanism.
- **W9 race postmortem** — verified via `cd /home/chris/luana-platform && git show 8d38c1a --stat`:
  - Commit `8d38c1a` "feat(story-11/T-guards-1): vitalia medical_safety_no_diagnosis input+output guardrail (R23 Opus)" — author alpacapurpura, 3 files clean: `guardrails/__init__.py` (+21/-1) + `guardrails/medical_safety_no_diagnosis.py` (+629/-0) + `tests/agentic_evals/guardrails/test_medical_safety_no_diagnosis.py` (+652/-0). 1301 insertions, 1 deletion total. **No collision artifacts.**
  - T-guards-1 result.md describes a "commit attribution caveat" but the orchestrator recovery into `8d38c1a` is byte-clean — the caveat is historical context, not a current defect.
  - **Mitigation forward (recommendation):** SESSION-4-CLOSE-2026-05-14.md:260 already proposes "serialize git push step via Haiku worker (one push at a time per wave) OR adopt git worktrees per builder." Worktrees currently forbidden per `parallel-safety.md` — would require Chris ratification. Sequencing git push step inside `dev-team` orchestrator (per-wave mutex via Haiku worker) is the lower-risk path; recommend for PI-12 future story / process improvement R34.
- **Cost recording** — T-tools-4 (`treatment_followup_check`) wires real LLM observability via LiteLLM Proxy CustomLogger bridge per PI-12 S1 T-1 cement (consumed from `cost_recorder` via `pop_cost(litellm_call_id)`). Workflow-level cost accumulator (`treatment_followup_workflow.py:196-199 _NODE_COST_USD`) is a deterministic stub until T-tools-4 hot-path lands real per-call recording — V-AE-15 cost budget validation uses real measurements.

---

## R23 compliance (100%) — 14/14 production_code:true → builder-agentic Opus 4.7 EXCLUSIVE

Verified at SESSION-4-CLOSE-2026-05-14.md:82-101:

| Ticket | production_code | Spawned with | R23 status |
|---|---|---|---|
| T-prompts-1 | true | builder-agentic Opus 4.7 | compliant |
| T-payment-1 (lift-shared) | true | builder-agentic Opus 4.7 | compliant |
| T-extractors-1/2 | true | builder-agentic Opus 4.7 | compliant |
| T-workflow-1 | true | builder-agentic Opus 4.7 | compliant |
| T-tools-1/2/3/4 | true | builder-agentic Opus 4.7 | compliant |
| T-kb-1/2/3 | true | builder-agentic Opus 4.7 | compliant |
| T-guards-1/2/3 | true | builder-agentic Opus 4.7 | compliant |

Sonnet exempt tickets (R23 production_code:false): T-rubric-1 (docs), T-e2e-1 (tests-over-agentic), T-eval-1 (tests-over-agentic). Zero Sonnet/opencode/general-purpose violations.

---

## Outstanding follow-ups status

- **V-AE-18 absent diagnosis**: classification **(C) NOT A GAP** — V-AE-18 defined in 04-validators.yaml:608, test file present at `tests/agentic_evals/observability/test_trace_invariants.py`, included in T-eval-1 132/132 PASS. No drift, no typo, no gap.
- **W9 parallel git race**: PASS — commit `8d38c1a` (verified `git show --stat`) is byte-clean orchestrator recovery; T-guards-1 result.md "caveat" is historical context. Mitigation forward recommendation: serialize git push step via Haiku worker per-wave (lower-risk than worktrees ratification).
- **R23 compliance**: PASS 14/14 production_code:true → builder-agentic Opus EXCLUSIVE.
- **Anti-duplication R10**: PASS 0 mirrors + 1 justified NEW with protocol-mismatch citation (compose.py vs luana-core sales_agent OpenAI-cache variant) + 2 EXTEND inheritance (extractors → BaseExtractionOrchestrator) + 1 EXTEND convention (T-guards-3 sandbox markers reuse, not class mirror).

---

## Findings (file:line)

### info (no blocker)
- [Cat 9 cost optimization] `treatment_followup_workflow.py:196-220` — `_NODE_COST_USD` deterministic stub map intentional until T-tools-4 wires real `copilot_llm_call.cost_usd` per-node accumulator at workflow level. V-AE-15 cost budget (`tests/agentic_evals/cost_budget/test_cost_budget_followup_turn.py`) uses real measurements — no observability gap, only workflow-level redundant accounting. **Recommendation**: post-T-tools-4 cutover, drop the stub map and read accumulated cost from `copilot_llm_call` rollup per workflow run; defer to future maintenance ticket.
- [Cat 3 prompt cache] `slot_3_sales_playbook_vertical_medical.j2:10` — Slot 3 sales playbook example uses voseo (`querés`, `Tenés`). Confirmed OK per `.claude/rules/sales-agent-brand-voice.md` exception — sales_agent voice respects tenant voice, NOT chrome neutro. Documented to forestall future false-positive auditor flag.
- [Cat 4 deepagents] No deepagents `task` subagent usage in workflow — pure LangGraph StateGraph is the correct shape for cron-driven cadence workflows. Not a finding, recorded for shape provenance.

### WARN (none)
### FAIL (none)

---

## Skill routing compliance

- `copilot-expert` invoked: YES (best-effort observability + tenant isolation patterns verified in workflow + tools + guardrails)
- `sales-agent-expert` invoked: YES (anti-duplication §0 cardinal + brand voice slot 5 separation + sales-agent-brand-voice.md exception verified)
- `tessl__langgraph` invoked: YES (TypedDict state schema + conditional edges + checkpointer protocol patterns verified in `treatment_followup_workflow.py`)
- `tessl__graceful-degradation` invoked: YES (timeout + fallback on classifier outage verified in `medical_safety_no_diagnosis.py:99-100` + `_consult_classifier_input/output` wrappers)

---

## Sample audit limitation note

Time-boxed ~30 min. Sample basis:
- **Result.md anchors read in full:** 4 (T-workflow-1, T-guards-1, T-eval-1, T-prompts-1)
- **Code paths spot-checked:** 6 (treatment_followup_workflow.py partial, compose.py partial, medical_safety_no_diagnosis.py partial, prepaid_payment_check.py grep, medical_kb_extractor.py grep, prompt_injection_block_reuse.py partial)
- **Targeted greps:** tenant_id across all 4 tools, eval_kind/cost_bucket invariants, R3 SSoT coverage, R23 routing table verification, W9 race commit verification
- **NOT re-executed:** 132 eval tests + 64 guards tests + 47 + 99 + 510 downstream regression — consumed verbatim from per-ticket result.md (all GREEN per cited evidence)
- **Drift detection:** read-only diff vs CONTRACT/specs not performed — relied on per-ticket "Decisions honored" sections + Sesion 4 close R23 ratification table

If full audit required: spawn dedicated `auditor-agentic` per-ticket with gate-runner downstream regression scope per R3 SSoT.

---

## Drift detection: NO

No CONTRACT-vs-code drift detected within sample scope. All decisions honored per per-ticket result.md cite sections (D3 + D5 + D6 + D9 + D10 verbatim verified). No `@pm: DRIFT` escalation required.

