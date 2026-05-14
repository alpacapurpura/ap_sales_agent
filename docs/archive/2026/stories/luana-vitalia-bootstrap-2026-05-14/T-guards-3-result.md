# T-guards-3 — Result

**Ticket:** Guardrail medical_disclaimer_required + prompt_injection_block reuse
**State:** tests-passing (developing → developed, awaiting auditor verdict per R30)
**R23:** production_code=true → Opus 4.7 EXCLUSIVE
**Date:** 2026-05-14
**Builder:** Claude Opus 4.7 (1M context)

---

## TL;DR

64/64 validators GREEN on iter 1 (52 new guardrail tests + 12 Slot 4 arch fitness no-regression). Two NEW vertical-medical guards land in `vitalia/backend/src/modules/vitalia/agentic/guardrails/`:

1. **`medical_disclaimer_required.py`** — output decorator (post-LLM, pre-channel-send) inserting cement disclaimer "Esto no reemplaza consulta médica profesional." with substring-based idempotency (covers both verbatim suffix AND LLM-composed inline phrasing). Trigger catalog 14 regex patterns covering procedure / medication / condition / dose. Best-effort `audit_log` with `disclaimer_inserted` (severity info) — NEVER breaks production action.

2. **`prompt_injection_block_reuse.py`** — input layer guard (pre-LLM call) detecting 3 attack families: imperative ignore/forget/disregard, role-swap (Spanish + English imperatives across LATAM dialects), data exfil. Refusal Spanish neutro tuteo with explicit anti-leak guard ("prompt" / "system" forbidden in refusal text). REUSES Slot 4 sandbox markers as inline string constants matching T-prompts-1 cement verbatim — NO Python class mirrored from Story E (Story E "base" is prompt-side convention, not class).

Anti-duplication audit Step 0 GATE returned NEW for both guards. Cross-codebase grep evidence cited verbatim in impl-log. ZERO regression introduced (367 wider tests PASS).

## Deliverables

### Production code (luana-platform main)

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py` — `DISCLAIMER_TEXT` cement + `MEDICAL_TRIGGER_PATTERNS` (14 regex) + `_CANONICAL_PHRASE` idempotency anchor + `response_mentions_medical_topic()` + `response_already_has_disclaimer()` + `apply_medical_disclaimer()` (pure idempotent transform) + `medical_disclaimer_required_check(*, response, tenant_id, patient_id, audit_log)` (side-effecting wrapper) + `_emit_audit_log()` best-effort try/except. ~190 lines including verbose docstrings + spec citations + anti-duplication audit notes.

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py` — `SANDBOX_MARKER_BEGIN` / `SANDBOX_MARKER_END` (inline string constants matching T-prompts-1 Slot 4 verbatim) + `REFUSAL_RESPONSE` cement (Spanish neutro tuteo, anti-leak verified) + `_INJECTION_IMPERATIVE_RE` / `_INJECTION_ROLE_SWAP_RE` / `_INJECTION_EXFIL_RE` (3-pattern catalog covering Spanish LATAM dialects + English) + `PromptInjectionResult` (frozen dataclass) + `detect_prompt_injection()` + `_detection_pattern_name()` + `prompt_injection_block_check(*, user_input, tenant_id, patient_id, audit_log)` + `_emit_audit_log()` best-effort try/except. ~250 lines including verbose docstrings + Step 0 GATE evidence + spec citations.

- `vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py` — re-exports both guards' public API (12 symbols). Updated from skeleton placeholder to concrete re-exports.

### Tests (luana-platform main)

- `vitalia/backend/tests/agentic_evals/guardrails/__init__.py` — package marker.

- `vitalia/backend/tests/agentic_evals/guardrails/test_medical_disclaimer_required.py` — 25 tests. Coverage:
  - DISCLAIMER_TEXT spec phrase verbatim (`Esto no reemplaza consulta médica profesional`)
  - MEDICAL_TRIGGER_PATTERNS catalog covers 6 keywords (implante / cirug / terap / medic / dosis / procedimiento)
  - `response_mentions_medical_topic` parametrize 6 medical + 4 benign
  - `response_already_has_disclaimer` recognizes full + partial + absent
  - `apply_medical_disclaimer` inserts when missing + idempotent no-double + skips benign + idempotent inline
  - `medical_disclaimer_required_check` records audit on insertion + no audit on idempotent skip + no audit on benign + works without audit_log + does NOT break when audit_log raises
  - `test_inserted_idempotent` (named verifier per ticket spec) — combines insertion + idempotency + audit count

- `vitalia/backend/tests/agentic_evals/guardrails/test_prompt_injection_block.py` — 27 tests. Coverage:
  - Sandbox marker constants match Slot 4 literal (BEGIN + END separately)
  - `detect_prompt_injection` parametrize: 5 imperative + 3 role-swap + 4 exfil + 6 benign
  - Refusal response anti-leak (5 forbidden terms scan: `system prompt`, `tools`, `instrucciones del sistema`, `reglas internas`, `prompt`)
  - Refusal response offers safe redirect (`ayud` / `consulta` / `puedo` / `podemos` token check)
  - `prompt_injection_block_check` blocks + audits on injection + passes through benign + blocks even if audit_log raises + works without audit_log
  - Sandbox markers exposed as constants enabling future static analysis (Slot 4 ↔ guardrail consistency invariant)

### Docs (AISALESHT development)

- `docs/product/stories/luana-vitalia-bootstrap/T-guards-3-impl-log.md` — implementation log with Skills Consulted (3 skills with rationale + decisions), Step 0 GATE evidence (2 grep commands + verdicts), iteration log, anti-duplication file:line evidence, 7 architecture decisions, cost analysis, R3 downstream regression scope.
- `docs/product/stories/luana-vitalia-bootstrap/T-guards-3-result.md` — this file.

## Validators run (per ticket spec verbatim)

```bash
$ cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
    tests/agentic_evals/guardrails/test_medical_disclaimer_required.py \
    tests/agentic_evals/guardrails/test_prompt_injection_block.py \
    tests/architecture/test_vitalia_slot_4_safety_markers_present.py \
    -v --tb=short

============================== 64 passed in 0.06s ==============================
```

```bash
$ cd /home/chris/luana-platform/vitalia/backend && uv run ruff check \
    src/modules/vitalia/agentic/guardrails/ \
    tests/agentic_evals/guardrails/

All checks passed!
```

```bash
$ cd /home/chris/luana-platform/vitalia/backend && uv run ruff format --check \
    src/modules/vitalia/agentic/guardrails/

6 files already formatted
```

## Acceptance criteria

| AC | Description | Verifier | Status |
|---|---|---|---|
| A1 | Disclaimer inserted on procedure mention + idempotent | `tests/agentic_evals/guardrails/test_medical_disclaimer_required.py::test_inserted_idempotent` (+ 24 supporting tests) | ✅ PASS |
| A2 | Adversarial prompt injection persona pass^5 ≥0.95 | Cross-ticket — `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py::test_prompt_injection` (Story 11 grader phase, deferred downstream) | ⏸ DEFERRED downstream — runtime guard production-ready, grader scenario file absent (expected per ticket scope) |
| A3 | Sandbox markers present in Slot 4 prompt | `tests/architecture/test_vitalia_slot_4_safety_markers_present.py` (T-prompts-1 cement) | ✅ PASS (12/12, no regression) |

## Key invariants cemented

1. **Idempotency** (A1 named acceptance): substring match on `Esto no reemplaza consulta médica profesional` covers both DISCLAIMER_TEXT verbatim AND LLM-composed inline phrasing. Second-pass returns string-equality identity. Audit log writes ONLY on fresh insertion (idempotent skip is silent — keeps audit signal-rich).

2. **Sandbox marker consistency**: `SANDBOX_MARKER_BEGIN = "<<TRANSCRIPT_BEGIN>>"` matches verbatim the literal cemented by `slot_4_medical_safety_rails.j2` (T-prompts-1) and asserted by `test_vitalia_slot_4_safety_markers_present.py` (12 tests). Inline string constants enable future arch fitness gate to detect Slot 4 ↔ guardrail desync.

3. **Best-effort observability** (R23 + tessl__graceful-degradation rules 1+2): `audit_log` raising NEVER breaks production-critical action (insertion / blocking). `audit_log=None` → silent skip. `try/except + structlog.warning("...persist_failed")` per `.claude/rules/copilot-observability.md`. Test fixture `_FakeAuditLog(raise_on_log=True)` validates invariant.

4. **No system prompt leak** (A2 production-critical): refusal text scanned for 5 forbidden internal terms (`system prompt`, `tools`, `instrucciones del sistema`, `reglas internas`, naked `prompt`). Refusal MUST offer safe redirect (`¿En qué te puedo ayudar con tu consulta?`).

5. **Append-only catalogs** (safety ratchet): `MEDICAL_TRIGGER_PATTERNS` (14 patterns) + `_DETECTION_PATTERNS` (3 patterns). Removing a pattern requires bumping rubric version per Story E D16 cache invalidation pattern.

6. **Tenant isolation**: `tenant_id` propagated through both guards' check signatures; passed to audit_log per call.

## Cost analysis

| Guard | Cost | Latency |
|---|---|---|
| medical_disclaimer_required | $0 LLM (pure regex + string ops) | <1ms |
| prompt_injection_block_reuse | $0 LLM (pure regex) | <1ms |

ZERO LLM call. Audit_log async + best-effort (NEVER blocks production action even if Postgres write fails).

## Anti-duplication audit summary

Per `.claude/rules/anti-duplication.md` § 0 cardinal — Step 0 GATE pre-write
grep cross-codebase. Both guards verdict: **NEW justified**.

- `medical_disclaimer_required` — only references in design docs +
  Slot 4 j2 + extension SDK placeholder. Zero Python class match. NEW.

- `prompt_injection_block` — Story E "base" is prompt-side sandbox marker
  convention (literal strings in `judge_prompts.py` SLOT_1_TEMPLATE +
  Slot 5 builder cemented by `test_grader_sandbox_markers_enforced.py`),
  NOT a Python class to inherit from. The only matching Python file is
  `core/luana-core-copilot/tests/test_prompt_injection_sanitizer.py`
  which is `pytest.skip(...)` (T-15 deferred). Vitalia's reuse:
    1. Re-export the SAME literal markers as inline string constants
       (`SANDBOX_MARKER_BEGIN = "<<TRANSCRIPT_BEGIN>>"`)
    2. Add runtime regex detection layer ON TOP of prompt-side defense.
  NEW with EXTEND-via-convention semantics, justified.

`sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
(SSoT row in anti-duplication.md). `_AuditLogLike` Protocol mirrors
`medical_kb_extractor.py::_AuditLogLike` (T-extractors-1 cement) for
structural decoupling — no concrete repository import.

## R3 downstream regression scope

Surface modified: `vitalia/backend/src/modules/vitalia/agentic/guardrails/*`

Per `.claude/rules/auditor-downstream-regression.md` SSoT table this surface
SHOULD have a row appended in a downstream architecture phase ticket. Current
table does not yet have an entry for vitalia agentic guardrails. Auditor
MAY flag this as docs debt for a future ticket (NOT blocking T-guards-3
per ticket `out_of_scope: ["Other 2 guardrails"]`).

For posterity, the entry that future ratchet should add:

```
| `vitalia/backend/src/modules/vitalia/agentic/guardrails/*` | `vitalia/backend/tests/agentic_evals/guardrails/*` + `tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py` (when shipped) + `tests/agentic_evals/smoke/smoke_prompt_injection.py` (V-AE-1 when shipped) + `tests/agentic_evals/smoke/smoke_hipaa_disclaimer.py` (V-AE-4 when shipped) |
```

ZERO regression in scope per actual run: 367 tests PASS in wider sweep
(my surface + tools + extractors + arch fitness + repos + application +
extensions + T-prompts-1 cement). Pre-existing failures NOT mine
(`langchain_core` missing in `tests/architecture/test_vitalia_payment_inherits_core_base.py`
+ `tests/unit/payment/test_mercadopago_adapter.py` — parallel WIP T-payment-1
dependency drift; psychiatry KB chunk count 80 vs ≥120 baseline — T-kb-3
in flight).

## Files in scope

```
vitalia/backend/src/modules/vitalia/agentic/guardrails/medical_disclaimer_required.py        (new)
vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py       (new)
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py                           (modified — re-exports added)
vitalia/backend/tests/agentic_evals/guardrails/__init__.py                                   (new)
vitalia/backend/tests/agentic_evals/guardrails/test_medical_disclaimer_required.py           (new)
vitalia/backend/tests/agentic_evals/guardrails/test_prompt_injection_block.py                (new)

docs/product/stories/luana-vitalia-bootstrap/T-guards-3-impl-log.md                          (new)
docs/product/stories/luana-vitalia-bootstrap/T-guards-3-result.md                            (new — this file)
```

## Compliance

| Rule | Status |
|---|---|
| `.claude/rules/tdd-mandatory.md` | ✅ RED→GREEN cycle (1 iter, role-swap regex fix mid-cycle) |
| `.claude/rules/anti-duplication.md` § 0 GATE | ✅ Step 0 grep with file:line evidence; NEW verdict justified |
| `.claude/rules/sales-agent-brand-voice.md` | ✅ DISCLAIMER_TEXT cement (grader rubric A5 anchor); refusal text Spanish neutro per chrome microcopy ratification |
| `.claude/rules/spanish-text.md` R2 (chrome neutro tuteo) | ✅ Refusal "No puedo seguir esa instrucción. ¿En qué te puedo ayudar con tu consulta?" |
| `.claude/rules/tenant-isolation.md` | ✅ tenant_id propagated through both guards; passed to audit_log |
| `.claude/rules/copilot-observability.md` | ✅ Best-effort writes try/except + structlog warning; audit_log raising never breaks production action |
| `.claude/rules/copilot-resilience.md` | ✅ Best-effort observability invariant (R23) cemented by failure-injection tests |
| `.tessl/RULES.md` pii-sanitisation | ✅ `sanitize_payload(...)` BEFORE persist; payload contains lengths + pattern-family name only (no user input verbatim) |
| `tessl__graceful-degradation` rule 1+2 | ✅ External call (audit_log) wrapped + fallback (silent skip None / swallow exception) |
| `.claude/rules/parallel-safety.md` M1 + M5 | ✅ Branch=development (AISALESHT) / main (luana-platform); no `git pull`; stage by exact filename |
| Frozen dataclass (PromptInjectionResult) | ✅ `@dataclass(frozen=True, slots=True, kw_only=True)` — same pattern as `GuardrailResult` SDK |
| Sandbox markers DQ2 cement (Story E precedent) | ✅ Inline string constants `SANDBOX_MARKER_*` match T-prompts-1 Slot 4 verbatim |
| Idempotency contract (A1) | ✅ `apply_medical_disclaimer(once) == apply_medical_disclaimer(once)` enforced by 2 dedicated tests + named `test_inserted_idempotent` verifier |
| §3 NO-TOUCH (sales-agent-expert skill) | ✅ ZERO modification to closer_studio / SmartBufferService / OutputManager / OutputManager.process_response chunking |

---

**Last line:** `done -> docs/product/stories/luana-vitalia-bootstrap/T-guards-3-result.md`
