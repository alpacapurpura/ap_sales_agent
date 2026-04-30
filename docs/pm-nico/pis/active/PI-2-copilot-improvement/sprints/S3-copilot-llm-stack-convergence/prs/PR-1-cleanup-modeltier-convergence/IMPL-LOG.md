# IMPL-LOG — PR-1-cleanup-modeltier-convergence

> Owner: PM main thread takeover post builder truncate (L-PROC-MAIN-THREAD-TAKEOVER cementado en S2 — PRs L+ scope ~25 archivos truncan).

## Builder progress (truncated)

Builder agent (id `a0a7cb64b662d1af9`) corrió ~9 min, 87 tool uses, truncó mid-task con "Now delete the dead files. First confirm they exist:" — sin commits propios.

Builder accomplished (4 files modified, uncommitted):
- `backend/src/modules/copilot/application/orchestrator/chat.py` — 4× `decision.tier.value` → `decision.role.value` (D-3 partial)
- `backend/src/modules/copilot/domain/events.py` — `RoutingDecided.create(tier_selected=...)` → `role_selected=...` + payload `"tier"` → `"role"` (D-3 partial)
- `backend/src/modules/copilot/infrastructure/models/routing_log_model.py` — Column `tier_selected` → `role_selected` (D-5 partial — Python model only, NO migration yet)
- `backend/src/modules/copilot/infrastructure/repositories/routing_log_repository.py` — param `tier_selected` → `role_selected` (D-5 partial)

Estado intermedio = NO compila: `decision.role.value` referenciado pero `RoutingDecision.role` field aún no existía (RoutingDecision aún tenía `.tier`).

## PM main thread takeover

### Commit `d079f13b` — refactor(copilot): ModelTier→ModelRole consumers refactor (D-3, D-4, D-5)

14 archivos refactorizados (4 builder partial + 10 nuevos):

Domain (5): routing_policy.py + hooks/copilot_events.py + skills/skill_metadata.py + ports.py (DELETE LLMProvider Protocol + LLMEvent; KEEP LLMMessage VO; ConversationSummaryVO.last_tier_used: ModelRole | None) + events.py.

Application (5): rule_classifier.py + llm_classifier.py + model_router.py + memory/rolling_summarizer.py + memory/title_generator.py (D-4: refactor a `BaseChatModel` directo via `LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)` — pattern judge/intent_classifier dominante).

API (1): conversation_dto.py — ModelTierLiteral → ModelRoleLiteral.

Orchestrator + infra (3): chat.py + routing_log_model.py + routing_log_repository.py builder partial validado.

### Commit `773604ab` — DELETE legacy + migration 115 + tests refactor + .env.example

DELETE legacy:
- copilot/infrastructure/llm/{model_config, provider_factory, providers/deepseek, providers/__init__, __init__}.py (D-1)
- copilot/domain/model_tier.py (D-2)
- tests/modules/copilot/infrastructure/llm/* + tests/modules/copilot/domain/test_model_tier.py
- tests/architecture/test_pr3_no_sales_agent_imports.py (D-8)

CREATE migration alembic 115 idempotente:
- ALTER TABLE copilot_routing_log RENAME tier_selected → role_selected (IF EXISTS)
- UPDATE copilot_routing_log.role_selected: 'mini'→'fast', 'heavy'→'agent'
- UPDATE copilot_conversation.last_tier_used: same value migration
- downgrade implementado (D-5)

Tests refactor (8 files): bulk sed ModelTier→ModelRole + tier→role + JSON keys + value mapping + golden snapshot routing_policy_shape.json.

Arch fitness (D-9): KNOWN_LEGACY_LLM_FILES allowlist 19 → **0 entries** (target alcanzado). 3/3 verde.

`.env.example` (D-10): NANO+FAST → deepseek-v4-flash (provider deepseek). 4-15x cost reduction. Eval gate S5 = guardrail forward.

## Quality gates

```
tests/architecture/test_llm_routing_ssot.py: 3/3 verde + allowlist 0
tests/architecture/: 766/766 verde
tests/modules/copilot/: 1702 passed, 21 failed (pre-existing voice/offer/outbox/suggestions
unrelated a S3 PR-1, M8 — paralela session)
```

## Decisiones builder D-MAIN-N

| ID | Decisión | Razón |
|---|---|---|
| D-MAIN-1 | KEEP LLMMessage VO en ports.py (CONTRACT D-4 dijo DELETE) | 3 production consumers: context_window_builder + rolling_summarizer + title_generator. CONTRACT subset orphan = LLMProvider Protocol + LLMEvent (esos sí DELETE). |
| D-MAIN-2 | Bulk sed para test refactor (5+ archivos) | 100+ refs ModelTier → ModelRole + values mapping. Safer mecánico que manual line-by-line. |
| D-MAIN-3 | Allowlist target 0 alcanzado | Post-DELETE grep src/ retorna 0 hits ModelTier. CONTRACT D-9 ratchet target. |
| D-MAIN-4 | Migration 115 UPDATE values en 2 tablas | DTO ModelRoleLiteral rechaza "mini"/"heavy" — sin UPDATE values, deploy rompe FE GET conversations. |

## Outcome vs CONTRACT aceptación

- ✅ Tests verde (refactor + nuevos)
- ✅ Lint/type check verde
- ✅ IMPL-LOG.md completo
- ✅ Allowlist shrunk a 0 entries (target D-9 alcanzado)
- ✅ `grep ModelTier backend/src/modules/copilot/` = 0
- ✅ `find backend/src/modules/copilot/infrastructure/llm/` = no such dir
- ✅ Arch fitness SSoT 3/3 verde
- 🔜 REVIEW.md auditor + RESULT.md PM
- 🔜 current-state/copilot.md lineage + decisions.md PI-2 + PR.md shipped
