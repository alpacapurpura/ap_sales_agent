# T-1-result.md — Cost recorder canonicalization

---
ticket_id: T-1
story_id: sales-agent-litellm-canonicalization
state: tests-passing
finished_by: claude-opus-4-7
finished_at: 2026-05-05T06:30Z
push_commit_sha: pending
push_branch: development
---

## Resumen 1-frase

Cost recorder canonical creado (`shared/agent_observability/recording/cost_recorder.py`) consume `kwargs["response_cost"]` desde LiteLLM `CustomLogger`, deriva provider via `litellm.get_llm_provider(model)[1]`, persiste a través de `BaseAgentCallbackHandler` con bridge TTL 60s; `calculate_cost()` removido del runtime path (X2); `cost_usd` ahora nullable (provider unknown → null, distinto de 0).

## Acceptance criteria — auto-verificación

| ID | Criterio | Verifier output | Estado |
|---|---|---|---|
| A1 | Provider canonical derivado de model string slashed | `test_canonical_provider_and_cost_from_kwargs PASSED` | ✅ |
| A2 | Modelo desconocido → provider="unknown" + cost=null | `test_unknown_model_records_unknown_provider_and_null_cost PASSED` | ✅ |
| A3 | Callback p95 < 50ms | `test_callback_p95_under_50ms PASSED` (micro-bench) | ✅ |
| A4 | `calculate_cost()` NO invocado en runtime path | `test_calculate_cost_not_called_in_runtime_path PASSED` | ✅ |
| A5 | Bridge LiteLLM↔LangChain end-to-end | `test_cost_recorder_cache_hit_under_real_litellm_call PASSED` | ✅ |
| A6 | TTL 60s purge orphan entries | `test_cost_recorder_orphan_entry_warning PASSED` | ✅ |
| A7 | Bootstrap registra callback | `test_bootstrap_registers_cost_recorder_callback PASSED` | ✅ |
| A8 | Runtime cost independiente del snapshot | `test_runtime_cost_independent_of_snapshot_during_sync PASSED` | ✅ |
| A9 | Cobertura no baja | (gate completo pre-push) | pending push gate |

## Diff resumen

```
backend/src/shared/agent_observability/recording/cost_recorder.py        NEW
backend/alembic/versions/086_llm_call_cost_usd_nullable.py               NEW
backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py  NEW (13 tests)
backend/src/shared/agent_observability/recording/base_callback_handler.py   modified — provider derivation + pop_cost bridge + slashed model preservation
backend/src/shared/agent_observability/cost/calculator.py                modified — docstring marca como reconciliation utility only
backend/src/main.py                                                      modified — `litellm.callbacks = [CostRecorderCustomLogger()]` en startup
backend/src/workers/settings.py                                          modified — registro callback en Worker + Scheduler on_startup
backend/src/modules/copilot/observability/persistence/models/llm_call_model.py     modified — cost_usd nullable
backend/src/modules/sales_agent/observability/persistence/models/llm_call_model.py modified — cost_usd nullable
backend/tests/shared/agent_observability/test_callback_handler_litellm_strip.py   modified — A1 slashed preservación
backend/tests/modules/copilot/observability/test_callback_handler.py     modified — adapt to new provider derivation
backend/tests/modules/copilot/observability/test_e2e_isolated.py         modified — pre-stash cost via recorder pattern
backend/tests/snapshots/callback_handler/copilot_handler_baseline.json   regen
backend/tests/snapshots/callback_handler/sales_handler_baseline.json     regen
backend/requirements-runtime.txt                                         +litellm>=1.50.0,<1.83
```

## Quality gates output

```
$ .venv/bin/ruff check src/shared/agent_observability/ src/main.py src/workers/settings.py tests/shared/agent_observability/
All checks passed!

$ .venv/bin/ruff format --check ...
61 files already formatted

$ .venv/bin/pytest tests/shared/agent_observability/ tests/architecture/ tests/modules/copilot/observability/test_callback_handler.py tests/modules/copilot/observability/test_e2e_isolated.py --override-ini="addopts=" -q
1015 passed, 1 warning in 23.66s

$ .venv/bin/pytest tests/shared/agent_observability/cost/test_litellm_canonicalization.py -v
13 passed in 10.60s
```

## Anti-duplication grep evidence (Step 0)

```
$ find /home/chris/AISALESHT/backend/src -name "cost_recorder.py"  → no output
$ grep -rn "CustomLogger\|cost_recorder\|CostRecorder" backend/src/  → no output
$ grep -rn 'kwargs\["response_cost"\]\|response_cost' backend/src/  → no output
```

`cost_recorder.py` es nuevo surface (LiteLLM `CustomLogger`), conceptualmente distinto de `BaseAgentCallbackHandler` (LangChain). Bridge TTL 60s + `pop_cost(litellm_call_id)` extiende handler shared (no mirror). `BaseAgentCallbackHandler` lifted en S11A se reusa.

## Decisiones técnicas concretas (per arch doc)

- **`litellm` SDK pinned** `>=1.50.0,<1.83` para compat `langchain-openai==1.1.11` (1.83+ pinea openai 2.24, romper langchain).
- **Bridge cache TTL 60s**: `(litellm_call_id, cost_usd, provider)` en thread-safe dict, pop on consume. Orphan entries → warning `cost_recorder.orphan_entry` + auto-purge.
- **Cache miss → cost_usd=null** (NO 0 — distinguible de zero-cost legitimate).
- **Migration 086**: `ALTER TABLE copilot_llm_call ALTER COLUMN cost_usd DROP NOT NULL` + same for sales_agent_llm_call. Idempotente. Backfill no requerido (existing rows ya tienen cost numérico).
- **A1 slashed model preserved**: `BaseAgentCallbackHandler` ya no strippea `/`. Snapshots regenerados.
- **X2 calculate_cost() docstring**: marca explícita "reconciliation utility only — NOT used in runtime cost recording path". Future T-2/T-3 sync-pricing puede reusarla manualmente para auditoría.

## Notas para /auditor

- Modificaciones a `modules/copilot` y `modules/sales_agent` son **modelos de persistencia** (`cost_usd` nullable schema mirror). NO cambia lógica agentic. Architect doc Section 5 lo aprueba como cross-cutting schema change required by T-3 migration; T-1 hace el schema change para no bloquear callback registration.
- Tests modificados en `modules/copilot/observability/` cubren regression del callback handler shared (consumido por copilot). Cambios mínimos.
- Snapshot baseline regenerados — diff es solo `model` field (slashed vs stripped).
- Ratchet allowlist arch fitness inalterada (no se introdujeron violaciones).

## Riesgos conocidos / deuda

- ⚠️ T-2 sync-pricing requiere rever que migration 086 + A1 slashed son consumibles sin breakage por reconciliation drift detection.
- ⚠️ T-3 migration de repair (re-tag historical `provider="openai"` → canonical) DEPENDE de T-1 callback registrado en producción primero.
- ⚠️ Pin `litellm<1.83` debe revisarse cuando langchain-openai actualice openai pin (Q3 2026 estimado).

## Output al orchestrator

```
done -> docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/05-impl/T-1-result.md
state: tests-passing (commit pending — controller commits + pushes)
ready for /auditor
```
