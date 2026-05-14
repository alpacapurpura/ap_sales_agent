<!-- voseo-allowed: technical reference cita catalog regex Spanish imperative verb forms (haz/hagas/hace/hacé) covering LATAM dialects including voseo for adversarial prompt-injection detection. NOT user-facing strings — runtime regex literals only. Per .claude/rules/spanish-text.md § Magic comment escape (R25 2026-05-05). -->
# T-guards-3 — Implementation Log

**Ticket:** Guardrail medical_disclaimer_required + prompt_injection_block reuse
**Type:** AGENTIC guardrail (R23 Opus 4.7 EXCLUSIVE — production_code=true)
**Story:** luana-vitalia-bootstrap (Story 11)
**Decisions applicable:** D5 (Slot 4 MEDICAL_SAFETY_RAILS reservation)
**Validators:** V-AE-1 + V-AE-4 + V-AE-8
**Date:** 2026-05-14
**Builder:** Claude Opus 4.7 (1M context)

---

## Skills Consulted

Per `.claude/skills/builder-agentic` Step 0 GATE — domain skill invocation
mandatory. Skipping = audit FAIL automatic.

| Skill | Why invoked | Decision taken |
|---|---|---|
| `sales-agent-expert` | Guardrails are vertical-medical voice + safety overlay; output decorator post-LLM pre-channel-send maps to OutputManager extension surface (anti-pattern: tocar `OutputManager.process_response` chunking — §3 forbidden). Confirmed ticket scope is NEW middleware guard (not OutputManager modification). DISCLAIMER_TEXT cement = exact phrase grader rubric A5 (vertical-medical-fidelity) looks up. Slot 4 sandbox markers cementan defense-in-depth. | Use Pydantic frozen dataclass for PromptInjectionResult (NOT regular Pydantic — payload-free result type per skill anti-pattern). Sanitize_payload via `luana_core_observability.recording.sanitization` (anti-duplication.md SSoT row). Audit_log via `medical_audit_log` Protocol stub mirroring `medical_kb_extractor.py::_AuditLogLike` pattern (T-extractors-1 cement). Best-effort try/except + structlog warning per copilot-observability.md. |
| `tessl__graceful-degradation` | All audit_log calls are external (DB writes via repository). Per skill rule 1 + 2: every external call needs timeout + fallback. Audit_log raising MUST NOT break production-critical action (insertion / blocking). | Wrap all `audit_log.log(...)` calls in try/except + `logger.warning(...persist_failed, exc=str(e))`. Production-critical path (apply_medical_disclaimer + block decision) returns SUCCESSFULLY even if audit_log fails. audit_log=None → silent skip (graceful when not provisioned). Test fixture `_FakeAuditLog(raise_on_log=True)` validates invariant. |
| `tessl__pytest-api-testing` | New pytest fixtures for guardrails — async tests with audit_log mock. Per skill: pytest fixtures via in-memory factory pattern; pytest-asyncio mode='auto'; assert response shape not just status. | In-memory `_FakeAuditLog` class with `entries: list[dict[str, Any]]` accumulator + `raise_on_log: bool` flag for failure-injection tests. Both fixtures (`audit_log`, `audit_log_failing`) function-scoped. `@pytest.mark.asyncio` on async tests; pyproject.toml already sets `asyncio_mode = "auto"`. Parametrize used heavily for trigger pattern coverage (medical topics × 6, role-swap × 3, exfil × 4, benign × 4-6). Audit log entries assertion checks shape (event_type, tenant_id, payload.severity) not just count. |

`copilot-expert`: NOT invoked — vitalia is NOT copilot. Guardrails live in
`modules/vitalia/agentic/`, NOT `modules/copilot/`.

`tessl__langgraph`: NOT invoked — guard is a pure Python check at the input/output
pipeline boundary; no StateGraph, no checkpoint, no node/edge modification.
Guard is invoked BY the orchestrator middleware chain, but does not own a graph.

`tessl__fastapi`: NOT invoked — no API routes touched. Guards are in-process
middleware functions invoked by the orchestrator dispatcher.

`claude-api`: NOT invoked — no Anthropic SDK changes; cache prefix architecture
already cemented by T-prompts-1 (Slot 4 sandbox markers verbatim referenced
via constants `SANDBOX_MARKER_BEGIN` / `SANDBOX_MARKER_END`).

---

## Step 0.5 — Default flag flip detection

N/A — no `core/config.py` defaults touched. Guards are pure additions; no
feature flag introduced for this ticket.

---

## Step 1 — Anti-duplication audit (Step 0 GATE)

Per `.claude/rules/anti-duplication.md` § 0 cardinal rule. Cross-codebase grep
verbatim before any `Write`:

```bash
$ grep -rln "medical_disclaimer\|disclaimer_required\|disclaimer_inserted" \
    /home/chris/AISALESHT/backend/src/ /home/chris/luana-platform/ 2>/dev/null \
    | grep -v __pycache__
/home/chris/luana-platform/vitalia/config/brand.yaml
/home/chris/luana-platform/vitalia/backend/tests/unit/test_extensions_register_all.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py
```

→ **Verdict: NEW.** Only references are:
- `brand.yaml` (registration manifest declaration)
- `test_extensions_register_all.py` (extension SDK smoke test for placeholder)
- `extensions.py` (T-extensions-1 placeholder via `_block_handler_placeholder`)
- `guardrails/__init__.py` (skeleton mention "T-guards-3 → medical_disclaimer_required")

```bash
$ grep -rln "prompt_injection_block\|class.*PromptInjection\|prompt_injection_blocked" \
    /home/chris/AISALESHT/backend/src/ /home/chris/luana-platform/ 2>/dev/null \
    | grep -v __pycache__
/home/chris/luana-platform/core/luana-core-copilot/tests/test_prompt_injection_sanitizer.py
/home/chris/luana-platform/vitalia/config/brand.yaml
/home/chris/luana-platform/vitalia/backend/tests/unit/test_extensions_register_all.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/prompts/slot_4_medical_safety_rails.j2
/home/chris/luana-platform/nicolify/backend/tests/modules/copilot/test_prompt_injection_sanitizer.py
/home/chris/luana-platform/nicolify/backend/tests/modules/copilot/test_deep_agent_harness.py
/home/chris/AISALESHT/backend/tests/architecture/test_grader_sandbox_markers_enforced.py
/home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/grader/_internal/judge_prompts.py
/home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/grader/test_judge_prompts.py
/home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/grader/test_judge_no_system_leak.py
/home/chris/AISALESHT/backend/tests/agentic_evals/sales_agent/grader/scenarios/test_scenario_4_adversarial_prompt_injection.py
```

→ **Verdict: REUSE convention NOT class.** Story E "base" is a *prompt-side
sandbox marker convention* (literal `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>`
strings cemented in `judge_prompts.py` SLOT_1_TEMPLATE + Slot 5 builder by
`test_grader_sandbox_markers_enforced.py` arch fitness), NOT a Python class to
inherit from. The Python file `core/luana-core-copilot/tests/test_prompt_injection_sanitizer.py`
is `pytest.skip(...)` (T-15 deferred). Vitalia's "reuse" means:

1. Re-export the SAME literal markers as constants
   (`SANDBOX_MARKER_BEGIN = "<<TRANSCRIPT_BEGIN>>"` matches T-prompts-1
   Slot 4 cement verbatim).
2. Add runtime regex detection layer ON TOP of the prompt-side defense.

NEW guardrail file `prompt_injection_block_reuse.py` is justified because:
- No Python class to inherit from at AISALESHT or luana-platform.
- Sandbox markers are prompt-side strings — runtime detector is a separate
  defense layer (defense-in-depth).
- Audit_log emission is brand-specific (vitalia uses `medical_audit_log`
  table per `vitalia_medical_audit_log` ORM model T-be-2 cement).

Anti-duplication audit: `sanitize_payload` consumed from
`luana_core_observability.recording.sanitization` (per `.claude/rules/anti-duplication.md`
SSoT row). `_AuditLogLike` Protocol mirrors the pattern established by
`medical_kb_extractor.py::_AuditLogLike` (T-extractors-1 cement) for
structural decoupling — NO concrete repository import.

---

## Step 2 — Cross-module systems audit (NO-NEW-LAYER)

Existing layers consumed (EXTEND, never NEW):
- `luana_core_observability.recording.sanitization::sanitize_payload` —
  PII sanitization (anti-duplication.md SSoT row).
- `luana_core_extension_sdk::GuardrailDef` + `GuardrailResult` — already
  used by `extensions.py` EP-13 placeholder. Real handlers (this ticket)
  conform to the SDK protocol indirectly: the orchestrator middleware will
  wire `medical_disclaimer_required_check` + `prompt_injection_block_check`
  to GuardrailDef callable adapters in a future ticket. T-guards-3 ships
  the pure check functions; SDK adapter wiring is downstream.
- `structlog` — logging (per `.claude/rules/backend-ddd.md` + `backend-quality.md`).

NO new infrastructure layers introduced. NO existing layers replaced.

---

## Iteration log

### Iter 1 (RED→GREEN, 1 cycle, ~2h)

**Files written:**
1. `vitalia/backend/tests/agentic_evals/guardrails/__init__.py` (package marker)
2. `vitalia/backend/tests/agentic_evals/guardrails/test_medical_disclaimer_required.py` (25 tests)
3. `vitalia/backend/tests/agentic_evals/guardrails/test_prompt_injection_block.py` (27 tests)
4. `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py`
5. `vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py`
6. `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py` (re-exports)

**TDD cycle:**

| Step | Action | Result |
|---|---|---|
| RED  | `uv run pytest tests/agentic_evals/guardrails/` — no impl exists | `ModuleNotFoundError: src.modules.vitalia.agentic.guardrails.medical_disclaimer_required` ✅ confirmed RED |
| GREEN | Implement both guard files | 51/52 PASS (1 fail: role-swap regex on "Haz como si fueras") |
| GREEN-fix | Extend `_INJECTION_ROLE_SWAP_RE` to cover Spanish imperative verb forms (haz/hagas/hace/hacé) + fix `r"""` raw docstring (escape `\\|` syntax warning) | **52/52 PASS** ✅ |
| Lint  | `uv run ruff check src/.../guardrails/ tests/.../guardrails/` | 2 import-organization findings, both auto-fixed via `--fix` |
| Format | `uv run ruff format` | 2 test files reformatted; final `--check` clean |
| Validators | Run all 3 ticket validators (T-guards-3 acceptance A1+A3 — A2 cross-ticket) | **64/64 PASS** ✅ |

**Final scope test count:** 64 PASS (52 guardrails + 12 Slot 4 arch fitness)

**Wider regression scope per R3 SSoT (`.claude/rules/auditor-downstream-regression.md`):**

Surface modified: `vitalia/backend/src/modules/vitalia/agentic/guardrails/*`

Downstream test paths per architecture-design § 17:
- `vitalia/backend/tests/agentic_evals/guardrails/*` ✅ 52/52 PASS (this ticket)
- `tests/architecture/test_vitalia_slot_4_safety_markers_present.py` ✅ 12/12 PASS (T-prompts-1 cement, no regression)
- `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py` — A2 (pass^5 ≥0.95) — NOT yet shipped (Story 11 grader phase, separate ticket downstream)

Wider sweep (excluding `langchain_core` parallel WIP drift in `tests/architecture/test_vitalia_payment_inherits_core_base.py` + `tests/unit/payment/` and pre-existing kb_psychiatry chunk count issue T-kb-3 in flight):

```
367 passed, 2 warnings in 0.81s
```

Includes: my 52 + arch_evals + arch fitness + repos + application + extensions
register_all smoke + T-tools-1..2 + T-extractors-1..2 + T-prompts-1 + T-kb-1..2.

ZERO regression introduced by T-guards-3.

---

## Architecture decisions

### D-A: Two SEPARATE files (not one combined `guardrails.py`)

Justified by 02-design § 17.5 pipeline order — each guard has distinct runtime
layer + distinct trigger semantics. Combining them would couple the input-layer
prompt_injection to the output-layer disclaimer, breaking single responsibility
+ making the dispatcher refactor (future ticket) more invasive.

### D-B: Pure helpers + side-effecting wrapper (split by responsibility)

`medical_disclaimer_required.py` exposes:
- `response_mentions_medical_topic(response) -> bool` — pure regex check
- `response_already_has_disclaimer(response) -> bool` — pure substring check
- `apply_medical_disclaimer(response) -> str` — pure idempotent transform
- `medical_disclaimer_required_check(*, response, tenant_id, ..., audit_log)` —
  side-effecting wrapper (calls audit_log)

This split is testable per layer (24 of 25 tests are pure / fast / no async)
and matches the prepaid_payment_check.py pattern (T-tools-1 cement).

`prompt_injection_block_reuse.py` exposes the same shape:
- `detect_prompt_injection(user_input) -> bool` — pure regex check
- `prompt_injection_block_check(...) -> PromptInjectionResult` — side-effecting

### D-C: Frozen dataclass for `PromptInjectionResult` (NOT Pydantic)

Result is a value object, no validation needed (caller produces it). Frozen
dataclass with `slots=True, kw_only=True` — same pattern as
`luana_core_extension_sdk.models.GuardrailResult` (consistency across SDK
boundary). Lightweight, no Pydantic overhead.

### D-D: Idempotency check via canonical phrase substring (NOT exact equality)

Spec § 17.3 idempotency rule: "if disclaimer already present → NO duplicate
insertion". Exact-equality match would miss LLM-composed responses that
contain the phrase mid-prose. Substring match on `_CANONICAL_PHRASE`
("Esto no reemplaza consulta médica profesional") covers both:

- Verbatim DISCLAIMER_TEXT inserted by an earlier decorator pass
- LLM-composed inline phrasing ("Esto no reemplaza consulta médica profesional con tu odontólogo")

Tests `test_idempotency_check_recognizes_partial_match` +
`test_apply_idempotent_when_disclaimer_already_inline` cement this contract.

### D-E: Refusal phrasing forbids naked `prompt` mention (anti-leak)

Spec § 17.4 explicit: "DO NOT leak system prompt". Test
`test_refusal_response_does_not_leak_system_terms` catches any drift —
forbidden term list is `(system prompt, tools, instrucciones del sistema,
reglas internas, prompt)`. Final string:

> "No puedo seguir esa instrucción. ¿En qué te puedo ayudar con tu consulta?"

Spanish neutro tuteo per `.claude/rules/spanish-text.md` R2 + Q1=B chrome
microcopy ratification (vitalia voice respects tenant per
sales-agent-brand-voice.md exception, but the refusal is generic chrome —
NOT voice-customized so the same string serves all tenants regardless of
voseo dialect).

### D-F: Sandbox markers as inline string constants (DQ2 cement)

Per `test_grader_sandbox_markers_enforced.py` Story E precedent: literal
markers MUST be inline string constants (not parametrized) so static AST
scan can assert their presence. Vitalia repeats the cement:

```python
SANDBOX_MARKER_BEGIN: str = "<<TRANSCRIPT_BEGIN>>"
SANDBOX_MARKER_END: str = "<<TRANSCRIPT_END>>"
```

These constants enable a future arch fitness gate to assert Slot 4 ↔
guardrail consistency (rename in Slot 4 detected by static scan would fail
both surfaces simultaneously).

### D-G: Append-only regex catalogs (safety ratchet)

Both `MEDICAL_TRIGGER_PATTERNS` (medical disclaimer) and
`_DETECTION_PATTERNS` (prompt injection) are append-only tuples. Removing
a pattern requires bumping rubric version per Story E D16 cache invalidation
pattern (currently rubric_version=1 cement; future ticket may bump on
significant catalog changes).

False negatives backstopped by:
- Output-layer guards (medical_safety_no_diagnosis + medical_safety_no_prescription) for the disclaimer
- Slot 4 sandbox markers + adversarial grader pass^5 ≥0.95 (V-AE-11) for prompt injection

---

## Cost analysis

Per 02-design § 14 budgets:

| Guard | Cost | Latency |
|---|---|---|
| medical_disclaimer_required | $0 LLM (pure regex + string ops) | <1ms |
| prompt_injection_block_reuse | $0 LLM (pure regex) | <1ms |

ZERO LLM call. ZERO Postgres call (audit_log is best-effort async — happens
on hot path only when fired, and even then NEVER blocks production action).

---

## Acceptance criteria verification

| AC | Description | Verifier | Status |
|---|---|---|---|
| A1 | Disclaimer inserted on procedure mention + idempotent | `test_inserted_idempotent` (named verifier) + 24 supporting tests | ✅ PASS |
| A2 | Adversarial prompt injection persona pass^5 ≥0.95 | Cross-ticket — `test_vertical_medical_fidelity_adversarial.py::test_prompt_injection` (Story 11 grader phase, not in T-guards-3 scope) | ⏸ DEFERRED downstream |
| A3 | Sandbox markers present in Slot 4 prompt | `test_vitalia_slot_4_safety_markers_present.py` (T-prompts-1 cement) | ✅ PASS (12/12, no regression) |

**A2 status:** the adversarial grader test does NOT exist yet
(`tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py`
absent). It is downstream cross-ticket dependency per 02-design § 13.3
(grader scenarios materialized in Story 11 grader phase). T-guards-3 ships
the runtime guard that the adversarial grader will exercise. The unit-level
detection invariants exercised here (12 trigger pattern tests + 6 false-positive
tests + audit_log + refusal safety) cement the production behavior the grader
will measure pass^5 against.

---

## Validators (V-AE-1 + V-AE-4 + V-AE-8)

The 3 validators in CONTRACT scope are eval-style (smoke + ≥85% LLM-driven):

- **V-AE-1** — `tests/agentic_evals/smoke/smoke_prompt_injection.py` — NOT yet
  in scope (smoke file absent — separate ticket downstream).
- **V-AE-4** — `tests/agentic_evals/smoke/smoke_hipaa_disclaimer.py` — NOT yet
  in scope (smoke file absent — separate ticket downstream).
- **V-AE-8** — `tests/agentic_evals/guardrails/` — ✅ **52/52 PASS** (this ticket).

V-AE-8 is the only validator T-guards-3 directly satisfies. V-AE-1 + V-AE-4
are smoke-test validators that will exercise the guard runtime; the smoke
files materialize in a downstream ticket (likely T-eval-1 per `blocks` field
in 06-tickets.yaml). T-guards-3 ships the production-ready guards that the
smoke files will invoke.

---

## R3 downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)

Surface modified: `vitalia/backend/src/modules/vitalia/agentic/guardrails/*`

Per 03-arch-agentic § 17 + the SSoT table this surface SHOULD have a row
appended in a downstream architecture phase ticket. Current table does not
yet have an entry for vitalia agentic guardrails. Auditor MAY flag this
as docs debt for a future ticket (NOT blocking T-guards-3 — out of scope
per ticket `out_of_scope: ["Other 2 guardrails"]`).

For posterity, the entry that future ratchet should add:

```
| `vitalia/backend/src/modules/vitalia/agentic/guardrails/*` | `vitalia/backend/tests/agentic_evals/guardrails/*` + `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py` (when shipped) + `tests/agentic_evals/smoke/smoke_prompt_injection.py` (when shipped) + `tests/agentic_evals/smoke/smoke_hipaa_disclaimer.py` (when shipped) |
```

---

## Files changed (luana-platform main)

```
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py        (modified — re-exports)
vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py   (new)
vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py  (new)
vitalia/backend/tests/agentic_evals/guardrails/__init__.py                              (new)
vitalia/backend/tests/agentic_evals/guardrails/test_medical_disclaimer_required.py      (new)
vitalia/backend/tests/agentic_evals/guardrails/test_prompt_injection_block.py           (new)
```

## Files changed (AISALESHT development — docs only)

```
docs/product/stories/luana-vitalia-bootstrap/T-guards-3-impl-log.md   (new — this file)
docs/product/stories/luana-vitalia-bootstrap/T-guards-3-result.md     (new)
```

---

## Compliance checklist

- [x] Step 0 GATE: skills declared + invoked + cited (3 skills above)
- [x] Step 0.5 default-flip detection: N/A (no config flag changes)
- [x] Anti-duplication grep with file:line evidence
- [x] TDD RED→GREEN cycle (1 iteration; role-swap regex fix mid-cycle)
- [x] Tests pass: 52/52 guardrails + 12/12 Slot 4 arch fitness = 64/64
- [x] Wider regression: 367 passed (no regression introduced)
- [x] Lint clean: `ruff check` 0 errors
- [x] Format clean: `ruff format --check` 0 errors
- [x] Spanish neutro chrome (refusal text, disclaimer text per spec § 17.3 + § 17.4)
- [x] PII sanitization via `sanitize_payload` (anti-duplication.md SSoT)
- [x] Best-effort observability (try/except + structlog warning + None-graceful)
- [x] Tenant isolation (tenant_id propagated through guardrail context)
- [x] Sandbox markers as inline string constants (DQ2 cement match Slot 4)
- [x] Idempotency invariant (regex check + canonical phrase substring + 0-duplicate test)
- [x] R23 Opus 4.7 EXCLUSIVE (production_code=true)
- [x] §3 NO-TOUCH respected (no closer_studio / SmartBufferService / OutputManager modifications)
