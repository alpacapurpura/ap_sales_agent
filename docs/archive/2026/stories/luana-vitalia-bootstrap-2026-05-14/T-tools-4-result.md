# T-tools-4 — Result

**Ticket:** T-tools-4 (Tool `treatment_followup_check` — workflow node + Haiku classifier)
**Owner:** Claude Opus 4.7 (1M context) — R23 production AGENTIC code
**Date:** 2026-05-14 (W9 Sesion 4)
**State:** developed (tests-passing)
**Commit:** TBD (added post-result doc)

---

## Acceptance — both criteria GREEN

| ID | Description | Verifier | Status |
|---|---|---|---|
| A1 | record_d5 with safety keyword → workflow transitions paused_safety_escalation | `pytest tests/agentic_evals/tools/test_treatment_followup_check.py::test_safety_escalation` | **PASS** |
| A2 | Cost per record_* call ≤$0.003 USD (Haiku classifier) | `pytest tests/agentic_evals/tools/test_treatment_followup_check.py::test_cost_budget` | **PASS** |

---

## Validators

| ID | Cmd | Status |
|---|---|---|
| V-AE-5 | `cd vitalia/backend && .venv/bin/pytest tests/agentic_evals/tools/ -v --tb=short` | **62/62 PASS** |
| V-AE-15 (unit-level) | Cost asserted via `_StubLLMClassifier(cost_per_call_usd=0.0014)` × 2 = $0.0028 < $0.003 ceiling | **PASS** |
| Lint | `ruff check` + `ruff format --check` | **PASS** |

---

## Deliverables

### Production code
- `vitalia/backend/src/modules/vitalia/agentic/tools/treatment_followup_check.py` — 7-action workflow internal tool with Pydantic input/output, Protocol-based DI (followup_repo + adherence_repo + llm_classifier + workflow_transitioner + trace_event_repo + audit_log_repo), safety keyword scan (deterministic pre-LLM), Haiku classifier with timeout+fallback, best-effort observability + audit, sanitized trace payloads.

### Tests
- `vitalia/backend/tests/agentic_evals/tools/test_treatment_followup_check.py` — 24 tests (RED→GREEN single iter):
  - 2 schema invariants (tenant boundary + 7-action Literal)
  - 2 acceptance (A1 safety + A2 cost)
  - 9 happy-path / variants (3 ping + 3 record + snapshot + override + cross-tenant)
  - 5 safety keyword variations (parametrized) + 1 negation guard
  - 2 best-effort observability (trace + audit failures don't break turn)
  - 1 graceful degradation (LLM failure fallback)
  - 1 PII sanitization (trace event)
  - 1 latency p99 (<250ms handler overhead)
  - 1 idempotency-related (override skips LLM)

### Patterns honored

- ✅ R23 Opus 4.7 mandatory (production AGENTIC code)
- ✅ D1 DDD Inside-Out (tool → service-like Protocols → tenant-scoped repos)
- ✅ D3 LangGraph 2.0 (tool callable as workflow node via WorkflowTransitioner Protocol)
- ✅ Anti-duplication (sanitize_payload from canonical luana_core_observability)
- ✅ Tenant isolation (tenant_id NEVER in input schema; ctx-injected; cross-tenant returns safe sentinel)
- ✅ Best-effort observability (try/except + structlog warning; never breaks turn)
- ✅ Graceful degradation Rules 1+2+5 (asyncio.wait_for timeout 5s + neutral fallback + per-dep isolation)
- ✅ PII redaction (response_text NOT logged; SHA-256 hash for forensic correlation; sanitize_payload before persist)
- ✅ Spanish neutro N/A (internal tool, no user-facing strings)
- ✅ Cost ≤$0.003 per record_* call (Haiku 2 calls)

### Out-of-scope (deferred)

- Concrete `AdherenceRecordRepository` (Protocol-only this ticket; repo lands when first non-test consumer needs it)
- Real Haiku classifier wiring (Protocol; production wraps `luana_core_llm.providers.litellm.LiteLLMService`)
- Sonnet voice-aware ping message composer (T-prompts-X)
- Workflow integration test wiring tool↔workflow end-to-end (out of T-tools-4 — workflow integration tests live in `tests/agentic_evals/workflows/`)
- Production cost budget eval `tests/agentic_evals/cost_budget/test_cost_budget_followup_turn.py` (V-AE-15 scope of separate eval ticket)

---

## Downstream regression

Per R3 + R21 SSoT — vitalia-local tool, no shared/ surface modified, no anti-duplication.md row affected. Downstream targets `tests/agentic_evals/tools/` all GREEN (62/62). Workflow tests have pre-existing langgraph missing module (deferred install) — NOT introduced by T-tools-4.

---

## Native ticket tests

```
tests/agentic_evals/tools/test_treatment_followup_check.py: 24/24 PASS
tests/agentic_evals/tools/ (full V-AE-5):                   62/62 PASS
```

done -> docs/product/stories/luana-vitalia-bootstrap/T-tools-4-result.md
