# RESULT — PR-6-consumers-cutover

> Owner: `/pm`. Cierre del loop.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-30 |
| Commits | f8a4b3e5 (Sub-A), 7b2de359 (Sub-B), 8d2aed36 (Sub-C), 97780627 (Sub-D), fb2683d0 (Sub-E), 6b8fcb11 (Sub-F), d3fbe665 (Sub-G fixes), 03d423c7 (REVIEW iter-2 PASS) |
| Branch merged a | development |
| Verdict auditor | iter-1 WARN → iter-2 PASS post Sub-G |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| 3 flags `USE_OUTBOX_PATTERN_*` ON | sales_agent + copilot + brand | 3 ON default | ✅ |
| BudgetGuard wired pre-LLM call sites | sales_agent + copilot + brand | sales_agent ✅ + copilot ✅ + brand DIFERIDO DR-7 | ⚠️ parcial |
| 20 emisores legacy retired | retire callsites | NO direct calls (todos usan adapter); allowlist seeded clean | ✅ |
| Tests integration F-7 sin mocks | smoke per módulo | 29 verde (13 SA + 12 copilot + 4 brand) | ✅ |
| Cero regresión 13 gates | gates verde flag ON | 766 arch + ruff/format/mypy domain verde | ✅ |
| Wiring single point per módulo (D27 ext) | wrappers en factory | 2 wiring points (SA pipeline + copilot deep_agent) + brand DEFERRED | ⚠️ parcial |

Veredicto: ✅ cumplido (PASS iter-2 con DR-7 brand BudgetGuard documented scope-cut).

## Surface entregada

| Tipo | Path | Notas |
|---|---|---|
| Wrapper | `shared/billing/application/llm_guards.py` | BudgetGuardingChatModel + BudgetGuardingLLMService (NEW Sub-A) |
| Cost estimator | `shared/billing/application/cost_estimator.py` | estimate_llm_cost + _messages_to_prompt (NEW Sub-A) |
| Exception | `shared/billing/application/exceptions.py` | BudgetExceeded (NEW Sub-A) |
| Pricing async | `shared/billing/infrastructure/pricing_snapshot_repo_async.py` | LRU TTL cache 256/300s (NEW Sub-A) |
| Wiring SA | `modules/sales_agent/application/orchestrator/conversation_pipeline.py:321` | budget_guard DI (MOD Sub-B) |
| Wiring copilot | `modules/copilot/application/orchestrator/deep_agent.py:210-267` | budget_guard + tenant_id DI + wrap (MOD Sub-C) |
| Config flags | `core/config.py:209-211` | 3 USE_OUTBOX_PATTERN_* default True (MOD Sub-B/C/D) |
| Tests integration | `tests/modules/{sales_agent,copilot,brand}/integration/` | 29 tests F-7 sin mocks |
| Arch tests | `tests/architecture/test_{budget_guard_pre_llm_call,no_legacy_event_bus_publish}.py` | 2 nuevos verde, ratchet shrink-only |

## Capacidades agregadas (lineage current-state)

```md
### Cap: Outbox cutover ON sales_agent + BudgetGuard wiring single point
- Introducida: PR-6 Sub-B (PI-1, S2, commit 7b2de359, 2026-04-30)
- Estado: live
- Operable copilot: no (infra cutover)

### Cap: Outbox cutover ON copilot + BudgetGuard wiring single point deep_agent
- Introducida: PR-6 Sub-C (PI-1, S2, commit 8d2aed36, 2026-04-30)
- Estado: live

### Cap: Outbox cutover ON brand
- Introducida: PR-6 Sub-D (PI-1, S2, commit 97780627, 2026-04-30)
- Estado: live (BudgetGuard wiring brand DIFERIDO DR-7 → Sub-D-2/S3)

### Cap: Architecture ratchet — BudgetGuard pre-LLM + no legacy event_bus
- Introducida: PR-6 Sub-E (PI-1, S2, commit fb2683d0, 2026-04-30)
- Estado: live (KNOWN_UNGUARDED 5 entries shrink-only; KNOWN_DIRECT_LEGACY_EMITTERS empty)
```

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D26 | Cutover order secuencial sales_agent → copilot → brand | blast radius bajo + rollback 1 line change | PR.md + CONTRACT |
| D27 | BudgetGuard estimation via model_pricing_snapshot | reservación 50% SA pool invariante | CONTRACT |
| D27 ext | Wrapper pattern `BudgetGuardingChatModel`/`Service` (3 wiring points vs 18 callsites) | 1000 clientes — single enforcement, callsite nuevo gates auto | PM (3 open Qs resolved) |
| D28 | Retire policy = flag flip + cero direct emit | emisores YA usan adapter — flag flip ya retire effectively | CONTRACT |
| D29 | Brand BudgetGuard wiring DIFERIDO Sub-D-2 | sync LLMFactory.generate_response requiere per-callsite refactor | PM (out of timebox) |
| D30 | sales_agent + copilot quality_eval workers en KNOWN_UNGUARDED | separate cron path no DI via __init__ | builder |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests integration F-7 nuevos | 0 | 29 | +29 |
| Tests architecture global | 758 (post-PR-5) | 766 | +8 |
| Flag USE_OUTBOX_PATTERN_SALES_AGENT | False | True | flip |
| Flag USE_OUTBOX_PATTERN_COPILOT | False | True | flip |
| Flag USE_OUTBOX_PATTERN_BRAND | False | True | flip |
| Cost estimator coverage | n/a | shared/billing escalable | new |
| Wiring single points BudgetGuard | 0 | 2 (SA + copilot) | +2 |

## Deuda residual flagged

| Item | Razón | Sprint destino |
|---|---|---|
| DR-7 Brand BudgetGuard wiring 7 LLM callsites | sync LLMFactory.generate_response requiere per-callsite refactor | Sub-D-2 / S3 |
| DR-8 sales_agent + copilot quality_eval workers BudgetGuard | separate cron path | Sub-G follow-up |
| DR-9 nest_asyncio dep | LangGraph dep ya pinned, OK por ahora | tracking |
| Audit obs F | 4 stale assertions `test_outbox_adapter_integration.py FlagOff` | follow-up no bloqueante (heredado PR-1) |

## Update obligatorios hechos

- [x] `current-state/{sales-agent,copilot,brand}.md` lineage updated
- [ ] `decisions.md` PI-1 appendear D26-D30 (PM cierre sprint)
- [ ] `learnings.md` S2 (PM cierre sprint)
- [x] PR-6 = última PR sprint S2 — handoff.md S3 sigue al cerrar S2

## Próximo paso PM

Cerrar sprint S2-orchestrator:
1. `handoff.md` S3-mvp-telegram (surface S2 → S3)
2. `learnings.md` S2 (4 PRs shipped: PR-3/PR-4 S1 + PR-5/PR-6 S2 con findings + Sub-G fixes)
3. `sprint.md` Estado → done
4. Commit `docs(pm): cerrar sprint S2-orchestrator + handoff S3 + learnings`

---

PR-6 **shipped** post Sub-G fix iter-2 PASS. PM cierra archivo. Loop completo.
