# IMPL-LOG — PR-6-consumers-cutover

> Owner: builders. Append-only diario decisiones implementación.
> Sesión: 2026-04-30 — orchestrator main session + 9 builder sub-spawns.

## Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (750 LOC SSoT)
- Skills: `sales-agent-expert` ✓, `copilot-expert` ✓, `brand-expert` ✓, `tessl__graceful-degradation` ✓, `tessl__pytest-api-testing` ✓

## Decisiones implementación

### D26 — Cutover order secuencial sales_agent → copilot → brand (CONFIRMED)
- Razón: blast radius bajo. Si sales_agent rompe → revert flag = 1 line. Paralelo = 3 cosas rotas simultáneas.
- Aplicado: 1 commit por flag flip + smoke tests entre cada.

### D27 ext — Wrapper pattern `BudgetGuardingChatModel` + `BudgetGuardingLLMService` (CONFIRMED PM, drift detected vs PR.md)
- Razón: 1000 clientes — single enforcement point en factory level. Callsite nuevo gates auto.
- Aplicado: 3 wiring points (1 per módulo) en lugar de parchar 18 callsites individuales.
- Sub-A creó wrappers + `PricingSnapshotRepoAsync` minimal (LRU TTL cache 256/300s, evita asyncio.to_thread thread pool exhaustion).

### D28 — Retire policy = flag flip + drop dead import (CONFIRMED, ajustado vs PR.md)
- Razón: 22 emisores YA usan adapter (`event_bus_adapter`). "Retire" = flag flip + cero direct calls.
- Aplicado: tests arch verifican cero `publish_in_memory` direct calls post-cutover.
- Drift: `_LegacyEventBus` import en `copilot/observability/recording/domain_subscribers.py` NO es dead — uso real para dedup check `_handlers` class attribute. Skip retire.

### D29 — Brand BudgetGuard wiring DIFERIDO Sub-D-2 (DR-7)
- Razón: brand 7 callsites usan sync `LLMFactory.get_service().generate_response(...)`. Wrap requiere per-callsite refactor con `BudgetGuardingLLMService`. Out of timebox PR-6.
- Aplicado: Sub-D ship flag flip outbox-only + tests F-7 outbox. BudgetGuard wiring brand → DR-7 follow-up Sub-D-2 / S3.
- Compensación: arch test `test_budget_guard_pre_llm_call.py` `KNOWN_UNGUARDED` allowlist incluye brand callsites con TODO Sub-D-2.

### D30 — sales_agent + copilot quality eval workers en KNOWN_UNGUARDED
- Razón: workers cron `weekly_*_quality_eval` son separate path de ConversationPipeline / deep_agent. No pasan por `__init__` DI.
- Aplicado: 2 entries más en allowlist con TODO Sub-G follow-up.

## Sub-deliverables completados

### Sub-A — BudgetGuardingLLMService wrapper + PricingSnapshotRepoAsync
- Commit: `f8a4b3e5`
- Files NEW:
  - `backend/src/shared/billing/application/llm_guards.py` (BudgetGuardingChatModel + BudgetGuardingLLMService)
  - `backend/src/shared/billing/infrastructure/pricing_snapshot_repo_async.py` (LRU TTL 256/300s)
  - `backend/src/shared/billing/application/cost_estimator.py` (estimate_llm_cost + _messages_to_prompt)
  - `backend/src/shared/billing/application/exceptions.py` (BudgetExceeded)
  - Tests: `backend/tests/shared/billing/`
- Tests: unit tests verde RED→GREEN per file.

### Sub-B — sales_agent flag flip + BudgetGuard wiring single point
- Commit: `7b2de359`
- Files MOD:
  - `backend/src/core/config.py` (USE_OUTBOX_PATTERN_SALES_AGENT default True)
  - `backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py:321` (budget_guard DI param)
  - `backend/src/modules/sales_agent/application/agents/sales/nodes.py` (consume guarded LLM via state)
  - `backend/src/modules/sales_agent/application/orchestrator/state.py` (extended w/ _llm_service slot)
- Files NEW:
  - `backend/tests/modules/sales_agent/integration/test_outbox_cutover.py`
  - `backend/tests/modules/sales_agent/integration/test_budget_guard_wiring.py`
- Tests: 13/13 integration verde + 756 arch tests verde global.

### Sub-C — copilot flag flip + BudgetGuard wiring single point
- Commit: `8d2aed36`
- Files MOD:
  - `backend/src/core/config.py` (USE_OUTBOX_PATTERN_COPILOT default True)
  - `backend/src/modules/copilot/application/orchestrator/deep_agent.py:210` (budget_guard + tenant_id DI params, wrap llm con BudgetGuardingChatModel cuando provided)
- Files NEW:
  - `backend/tests/modules/copilot/integration/test_outbox_cutover.py`
  - `backend/tests/modules/copilot/integration/test_budget_guard_wiring.py`
- Tests: 12/12 integration verde + 759 arch tests verde global.
- Drift resolved: CONTRACT línea 283 mencionaba `provider_factory.build_chat_model(...)` que no existe; wiring real en `build_deep_agent_graph` (LLMFactory.get_service().get_client retorna BaseChatModel LangChain).

### Sub-D — brand flag flip (BudgetGuard wiring DIFERIDO DR-7)
- Commit: `97780627`
- Files MOD:
  - `backend/src/core/config.py` (USE_OUTBOX_PATTERN_BRAND default True)
- Files NEW:
  - `backend/tests/modules/brand/integration/__init__.py`
  - `backend/tests/modules/brand/integration/test_outbox_cutover.py`
- Tests: 4/4 brand integration verde + 758 arch tests verde global.
- Scope cut: BudgetGuard wiring brand 7 callsites diferido Sub-D-2 / DR-7 (sync `LLMFactory.get_service().generate_response` requiere per-callsite refactor).

### Sub-E — 2 architecture fitness gates
- Commit: `fb2683d0`
- Files NEW:
  - `backend/tests/architecture/test_budget_guard_pre_llm_call.py` (sentinel KNOWN_UNGUARDED 5 entries shrink-only)
  - `backend/tests/architecture/test_no_legacy_event_bus_publish.py` (KNOWN_DIRECT_LEGACY_EMITTERS allowlist seeded empty post-cutover)
- Tests: 8/8 nuevos verde + 766 arch tests verde global.
- Decisión: AST scan source files (no inspect.signature) porque ConversationPipeline.__init__ tiene `*args, **kwargs` decorator-wrapped — source-level AST es check confiable.

### Sub-F — IMPL-LOG + current-state (este commit)
- Commit: pending
- Files NEW: este `IMPL-LOG.md`
- Files MOD: `docs/pm-nico/current-state/{sales_agent,copilot,brand}.md`

## Quality gates final

- [x] Ruff verde
- [x] Ruff format verde
- [x] Mypy strict scope (domain only) — 0 errors campaigns/sales_agent/copilot/brand domain
- [x] Pytest verde scope cutover (13 SA + 12 copilot + 4 brand integration)
- [x] Arch fitness tests verde (766 global, 8 nuevos PR-6)
- [x] No regresión otros tests (758→766 ratchet expand)

## Bloqueadores encontrados

- **B-1 (resolved):** stash drop accidental builder Sub-C iter perdió WIP Sub-C wiring chat.py + deep_agent.py. PI-2 paralela WIP también afectado pero recuperable (files M en working dir intactos). Recovery: re-implementación deep_agent.py wrap from scratch (chat.py NO necesita cambios — single point en deep_agent es suficiente).
- **B-2 (resolved):** ConversationPipeline.__init__ decorator-wrapped `*args, **kwargs` — inspect.signature no expone budget_guard. Switch a AST scan source file.
- **B-3 (resolved):** `EventBus.publish` legacy path attaches SQLA event listener — MagicMock falla. Mock con `patch("src.shared.domain.events.EventBus.publish", side_effect=...)`.

## Decisiones diferidas durante implementación

- **DR-7 brand BudgetGuard wiring** — Sub-D-2 / S3.
- **DR-8 sales_agent + copilot quality_eval workers BudgetGuard wiring** — Sub-G follow-up.

## Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| Wrapper | `shared/billing/application/llm_guards.py` | shipped Sub-A |
| Cost estimator | `shared/billing/application/cost_estimator.py` | shipped Sub-A |
| Exceptions | `shared/billing/application/exceptions.py` | shipped Sub-A |
| PricingSnapshot async | `shared/billing/infrastructure/pricing_snapshot_repo_async.py` | shipped Sub-A |
| Wiring sales_agent | `modules/sales_agent/application/orchestrator/conversation_pipeline.py:321` | shipped Sub-B |
| Wiring copilot | `modules/copilot/application/orchestrator/deep_agent.py:210` | shipped Sub-C |
| Flag flips | `core/config.py:209-211` | shipped Sub-B/C/D |
| Tests integration | `tests/modules/{sales_agent,copilot,brand}/integration/` | shipped 29 tests |
| Arch gates | `tests/architecture/test_{budget_guard_pre_llm_call,no_legacy_event_bus_publish}.py` | shipped Sub-E |

## Commits

- `f8a4b3e5` — feat(billing): BudgetGuardingLLMService wrapper + PricingSnapshotRepoAsync (PR-6 Sub-A)
- `7b2de359` — feat(sales_agent): outbox cutover ON + BudgetGuard wiring single point (PR-6 Sub-B)
- `8d2aed36` — feat(copilot): outbox cutover ON + BudgetGuard wiring (PR-6 Sub-C)
- `97780627` — feat(brand): outbox cutover ON (PR-6 Sub-D)
- `fb2683d0` — test(architecture): PR-6 budget_guard + no_legacy_event_bus arch gates (PR-6 Sub-E)
- `<this>` — docs(pm): PR-6 IMPL-LOG + current-state cutover shipped (PR-6 Sub-F)

## Deuda residual flagged

| ID | Item | Razón | Sprint destino |
|---|---|---|---|
| DR-7 | Brand BudgetGuard wiring 7 callsites | sync LLMFactory.generate_response requiere per-callsite refactor | Sub-D-2 / S3 |
| DR-8 | sales_agent + copilot quality_eval workers BudgetGuard | separate cron path, no DI via __init__ | Sub-G follow-up |
| DR-9 | nest_asyncio dependency en `_check_sync_bridge` | LangGraph dep ya pinned, OK por ahora | tracking |

---

<!-- @pm: PR-6 implementation done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-6 builder done" para review. -->
