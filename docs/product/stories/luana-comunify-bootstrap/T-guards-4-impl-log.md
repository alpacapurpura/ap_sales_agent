# T-guards-4 — prompt_injection_block (reuse Story E sandbox markers)
<!-- voseo-allowed: regex attack vector patterns (pretendé/hacé) cited verbatim from technical regex docstring; not user-facing copy -->

**Ticket**: T-guards-4 — Guardrail prompt_injection_block reuse Story E base.
**R23**: AGENTIC production_code=true → Opus 4.7 EXCLUSIVE.
**Estimate vs actual**: 2h estimate / ~25min actual (smallest of batch, mirrors vitalia surface).

## Skills Consulted

- **copilot-expert**: best-effort audit_log + structlog warning on failure.
- **sales-agent-expert**: anti-duplication §0 — grep verified ZERO `class.*PromptInjection` / `prompt_injection_block` outside Slot 4 j2 + EP-13 placeholder + vitalia sibling. **Mirror analysis**: vitalia surface mirrored intentionally per module docstring rationale — surface (regex catalog + Protocol + 1 check function) small enough that lift would cost more than it saves. Documented for re-litigation when 3rd vertical needs same. Alternative lift to `core/luana-core-guardrails/` deferred.
- **tessl__graceful-degradation**: pure regex (no LLM call); only graceful degradation needed on audit_log raise (try/except + structlog).
- **tessl__pytest-api-testing**: 30 test cases — most cases per file in batch. Parametrize 5 imperative + 4 role-swap + 5 exfil attack vectors + 6 benign queries.

## Step 0 GATE — Anti-duplication audit (2026-05-14)

```bash
grep -rln "class.*PromptInjection\|prompt_injection_block" \
  /home/chris/luana-platform/comunify /home/chris/luana-platform/core
```

Returns:
- Slot 4 j2 sandbox marker reference (T-prompts-1 cement)
- EP-13 placeholder
- Vitalia sibling at `vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py`

Mirror to vitalia INTENTIONAL — see module docstring. Constants `SANDBOX_MARKER_BEGIN` / `SANDBOX_MARKER_END` re-exported with byte-equal match to Slot 4 j2 literals so future arch-fitness gate can assert Slot 4 ↔ guard consistency (defense-in-depth DQ2 cement).

## Step 0.5 — Default flip detection

N/A.

## Files created

1. `agentic/guardrails/prompt_injection_block_reuse.py` (~270 lines)
2. `tests/agentic_evals/guardrails/test_prompt_injection_block.py` (~280 lines, 30 test cases)

## Implementation summary

- **3 attack pattern families** (regex):
  1. **Imperative**: `(ignora|olvida|disregard|forget)` + `.{0,80}?` non-greedy gap + `(prompt|system|reglas|instrucciones|instructions|rol)`. Catches Spanish (tildes + voseo "Ignorá"), English ("Disregard / Forget").
  2. **Role-swap**: `(actúa como|pretendé ser|hacé como si fueras)` + target `(otro asistente|otro modelo|creator|coach|mentor|sin filtros)`. Comunify-specific targets: creator/coach/mentor (vs vitalia médico/psiquiatra).
  3. **Exfil**: `(repetí|mostrame|dame|quiero ver|show me)` + target `(prompt|system prompt|reglas|datos de otros|otros miembros|otros leads)`. Comunify-specific exfil targets: "otros miembros" + "otros leads".
- **Refusal phrasing**: cement `REFUSAL_RESPONSE` = "No puedo seguir esa instrucción. ¿En qué te puedo ayudar con tu consulta?" — Spanish neutro tuteo + safe redirect (no system prompt leak per spec § 17.4).
- **Severity HIGH** per 03-arch § 10.2 (community vertical bar — adversarial pass^5 ≥0.95 at V-AE-11). Vs vitalia medium — difference reflects creator-economy adversarial corpus is community-amplified (one injected post visible to all members).
- **Audit event**: `prompt_injection_blocked` (byte-equal vitalia + Story E grader expectations).

## Validators

- **V-AE-1** (5 injection patterns blocked + audit_log): exceeded — 14 attack vectors caught (5 imperative + 4 role-swap + 5 exfil). 6 benign community queries pass-through. Refusal phrasing safety (no system_prompt/tools/prompt leak) verified in dedicated test.
- **V-AE-11** (audit_log severity high + tenant isolation): cross-tenant test asserts audit row carries calling tenant_id.

## Quality gates run

```
.venv/bin/pytest tests/agentic_evals/guardrails/test_prompt_injection_block.py -v
30/30 PASS

.venv/bin/ruff check + format --check: clean.
```

## Deferred / gaps

- Arch fitness gate `test_comunify_slot_4_safety_markers_present.py` (Slot 4 ↔ guard constants cross-ref): deferred to Story 12 arch fitness ticket.
- EP-13 extensions.py replacement (replace `_block_handler_placeholder` with real `prompt_injection_block_check` adapter wrapping BrandContext): deferred.
- Adversarial pass^5 ≥0.95 grader benchmark: cross-ticket (T-eval-1 W17).
