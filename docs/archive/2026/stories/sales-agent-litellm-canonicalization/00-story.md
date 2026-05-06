---
story_id: sales-agent-litellm-canonicalization
type: service-story
module: sales_agent                              # surface principal; toca también shared/agent_observability/cost/, shared/infrastructure/llm/, iam (tenant model)
capability: sales-observability-cost-tracking    # cost recorder canonicalization es el outcome principal
po_version: 2                                    # v1 = scope acotado deepseek-fix; v2 = canonicalization + cleanup zero-tech-debt (ratificado Chris 2026-05-04)
links:
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-observability-cost-tracking.yaml"
  module_doc: "../../../../../../product/modules/sales-agent.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

# Story — LiteLLM Canonicalization + Zero Tech Debt Cleanup

## Job-To-Be-Done

**Como** owner del producto + tech lead que mira reportes de costo, lee tracebacks y mantiene el SSoT de routing LLM
**Quiero** que LiteLLM sea el ÚNICO camino de ejecución LLM en Nicolify (6 adaptadores legacy → 0, 1 flag muerto, 4 columnas tenant API key droppeadas, pricing snapshot como ledger de auditoría únicamente)
**Para** confiar en `cost_usd` (LiteLLM lo computa nativo via `kwargs["response_cost"]`), eliminar deuda técnica hoy en lugar de en 6 meses, y reducir el costo cognitivo de agregar un nuevo modelo de "tocar 4 archivos + flag" a "1 entrada YAML".

## Por qué importa

Hoy el codebase tiene 2 caminos de ejecución LLM compitiendo: los adaptadores per-provider legacy (`openai.py`, `deepseek.py`, `kimi.py`, `qwen.py`, `gemini.py` + `_openai_compat.py`) y el wrapper canónico nuevo `litellm.py`. El flag `LITELLM_PROXY_ENABLED` mantiene los adaptadores vivos como fallback. Síntomas heredados:

- **Bug de provider tag:** DeepSeek se taggea como `provider="openai"` en `model_pricing_snapshot` porque hereda el alias del adaptador legacy. Pricing resolver no encuentra match → `cost_usd=0`. Reporting roto.
- **Deuda técnica activa:** 6 archivos adapter + 1 flag side-effect + 4 columnas tenant API key + ~20 tests con mocks per-provider — todo redundante con LiteLLM.
- **Multitenant complexity falsa:** las columnas `tenant.{openai,deepseek,kimi,dashscope}_api_key` modelan un mundo donde tenants traen sus propias API keys. Modelo real Nicolify 2026: **suscripción + Nicolify paga LLM con master key LiteLLM**. Los columns nunca se usaron en producción.
- **Friction agregar modelo nuevo:** hoy = 1 adaptador + 1 entrada router + 1 fallback + tests per provider. Con LiteLLM canonical = 1 entrada `litellm_config.yaml`.

Decisión Chris 2026-05-04: aprovechar este sprint S1 para el cleanup completo, NO solo el fix puntual de DeepSeek. Pricing snapshot pasa a ser **ledger de auditoría únicamente** — el costo runtime sale de `kwargs["response_cost"]` (computado nativo por LiteLLM con tarifas in-memory `model_cost`). Sync job (`make sync-pricing`) corre nightly + en CI para mantener el ledger fresco.

## Outcome esperado

Post-merge:
- Solo `LiteLLMService` ejecuta llamadas LLM. Adaptadores legacy NO existen como módulos importables.
- `copilot_llm_call.provider` siempre canónico (derivado via `litellm.get_llm_provider(model)[1]`).
- `copilot_llm_call.cost_usd > 0` para todo turn que toca LLM (consume `kwargs["response_cost"]` via `CustomLogger` callback wired en `BaseAgentCallbackHandler`).
- `tenants` table sin columnas `*_api_key` (Alembic migration idempotente).
- `LITELLM_PROXY_ENABLED` flag eliminado de `core/config.py`. `router.py` simplificado (sin `build_provider_service` rollback). `main.py` sin warning condicional. `admin/modules/llm_virtual_keys.py` sin fallback message.
- `make sync-pricing` actualiza `model_pricing_snapshot` con tarifas LiteLLM `model_cost` registry + entries de `litellm_config.yaml model_list` (pricing snapshot como ledger inmutable, NO source of truth runtime).
- Arch fitness `test_llm_routing_ssot.py` con `KNOWN_LEGACY_LLM_FILES = set()` + assertions explícitas que falla si alguien re-importa un módulo legacy borrado.
- Documentación `docs/domains/llm-routing.md` y `docs/domains/tech_module_shared.md` purgadas de referencias legacy + deprecation timeline.
- Métrica post-deploy: `SELECT COUNT(*) FROM copilot_llm_call WHERE provider IN ('deepseek','kimi','qwen','gemini') AND cost_usd = 0 AND created_at > NOW() - INTERVAL '1 day'` → 0.

## Antecedentes / Contexto

- **Origen v1 (scope acotado):** `docs/process/gap-report-2026-05-04-group-c.md` — bug DeepSeek mis-tag detectado durante migración SDD.
- **Reframe Chris 2026-05-04:** scope expandido a canonicalization completa + zero tech debt cleanup. 9 sub-tickets (T1..T9) a definir por `/architect` en `04-tickets.yaml`.
- **Stack afectado:**
  - `backend/src/shared/agent_observability/recording/base_callback_handler.py` (extender — anti-duplication: NO mirror)
  - `backend/src/shared/agent_observability/cost/calculator.py`
  - `backend/src/shared/agent_observability/pricing/litellm_sync.py` (extender)
  - `backend/src/shared/infrastructure/llm/router.py`
  - `backend/src/shared/infrastructure/llm/factory.py`
  - `backend/src/shared/infrastructure/llm/providers/{openai,deepseek,kimi,qwen,gemini,_openai_compat}.py` (DELETE)
  - `backend/src/shared/infrastructure/llm/providers/{_chat_model_resolver,_response_validation}.py` (verify still consumed by `litellm.py` post-T1; delete si no)
  - `backend/src/main.py` (remove conditional warning)
  - `backend/src/admin/modules/llm_virtual_keys.py` (remove fallback message)
  - `backend/src/admin/modules/copilot_routing.py` (verify `build_provider_service` consumer)
  - `backend/src/core/config.py` (delete flag `LITELLM_PROXY_ENABLED`)
  - `backend/src/modules/iam/infrastructure/models/tenant_model.py` (drop columns)
  - `backend/src/modules/iam/domain/tenant.py` (drop fields)
  - `backend/src/modules/iam/infrastructure/repositories/tenant_repository.py` (no-op `_extract_tenant_key` → return master)
  - `backend/src/modules/iam/api/settings.py` (drop API key endpoints if exist)
  - `backend/alembic/versions/` (2 migrations: snapshot repair + drop tenant API key columns)
  - `backend/tests/architecture/test_llm_routing_ssot.py` (shrink + harden)
  - `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py` (NEW)
  - `backend/tests/shared/billing/` (audit existing mocks)
  - `docs/domains/llm-routing.md` + `docs/domains/tech_module_shared.md` + docstrings en `sales_agent/domain/model_tier.py`, `sales_agent/application/agents/sales/nodes.py`
- **LiteLLM canonical 2026 patterns aplicados:**
  - `kwargs["response_cost"]` = SSoT runtime cost (LiteLLM lo computa nativo, no recomputar)
  - `litellm.get_llm_provider(model)[1]` = canonical `custom_llm_provider` (4-tuple, position 1)
  - `litellm.callbacks = [CustomLogger()]` = canonical hook (NOT legacy `litellm.success_callback` list)
  - LangGraph + LiteLLM bridging: extender `BaseAgentCallbackHandler.on_llm_end` ya lifted shared (anti-duplication.md). 1 trace, 1 cost source.
  - `model_pricing_snapshot` = audit ledger inmutable (NOT runtime pricing).
  - `litellm_config.yaml` = SSoT model registry (agregar modelo = 1 yaml entry).
- **Decisión Chris 2026-05-04 — owner pool:** `claude-opus-4-7` (escala el scope, toca callback shared cross-agent + Alembic destructivo + flag deletion + tests audit ~20 archivos). qwen-opencode **NO eligible** acá — la story original era qwen-eligible cuando era patch, post-reframe **Opus obligatorio**.
- **Skills cargados:** `backend-expert`, `sales-agent-expert`, `copilot-expert` (callback handler shared toca ambos agentes), `tessl__pytest-api-testing`, `tessl__fastapi`.
- **Reglas mandatorias aplicables:** `.claude/rules/anti-default-flip-audit.md` (T5 elimina flag — 4-step audit), `.claude/rules/anti-duplication.md` (BaseAgentCallbackHandler shared), `.claude/rules/backend-migrations.md` (T3 + T6 idempotentes), `.claude/rules/tdd-mandatory.md` (default-flag-flip section), `.claude/rules/architectural-fitness.md` (T8 ratchet shrink), `.claude/rules/tenant-isolation.md` (T6 toca tenants table — verify queries).

## Resumen sub-tickets (definidos en detalle por /architect en 04-tickets.yaml)

| # | Goal | Touches | Owner |
|---|---|---|---|
| T1 | Cost recorder canonicalization (kwargs["response_cost"] + get_llm_provider derive) | base_callback_handler.py + cost/calculator.py | Opus |
| T2 | `make sync-pricing` extiende litellm_sync.py — lee config yaml + model_cost registry → upsert snapshot | pricing/litellm_sync.py + Makefile + cron | Opus |
| T3 | Alembic migración idempotente repair historical snapshot (provider re-tag) | alembic/versions/ + backup table | Opus |
| T4 | DELETE legacy adapters (6 archivos + helpers) | providers/{openai,deepseek,kimi,qwen,gemini,_openai_compat,_chat_model_resolver,_response_validation}.py | Opus |
| T5 | Kill flag `LITELLM_PROXY_ENABLED` (anti-default-flip-audit 4-step) | core/config.py + router.py + main.py + admin/llm_virtual_keys.py + factory.py | Opus |
| T6 | Drop tenant API key columns (Alembic + domain + repo + factory stub) | iam/* + alembic/versions/ | Opus |
| T7 | Tests audit ~20 files (migrate per-provider mocks → LiteLLM mock) | backend/tests/{shared,modules,architecture}/ | Opus |
| T8 | Arch fitness shrink: KNOWN_LEGACY_LLM_FILES = set() + new explicit forbidden-import test | tests/architecture/test_llm_routing_ssot.py | Opus |
| T9 | Docs purge legacy refs | docs/domains/{llm-routing,tech_module_shared}.md + 2 docstrings | Opus |

## Out of scope (explícito)

- Cambios a `litellm_config.yaml` model_list (agregar/quitar modelos). Esa decisión es operativa, no parte de cleanup.
- Migrar el costo histórico de tenants ya facturados — el repair migration arregla provider tag SOLO en snapshot, NO recalcula bills pasados. Si afecta billing, escalar Chris ANTES de aplicar.
- Refactor `BudgetGuard` o pool isolation (SA bucket vs Others) — `sales-cost-tracking-cycle-billing.yaml` cubre eso.
- Cualquier cambio al runtime del agente (latency, routing, prompts, voice).
- Hot-swap admin UI para `litellm_config.yaml` — eso es S4 PI-12 separado.
- Migrar a deepagents/`task` harness (otro PI futuro).

## Riesgos / Asunciones

- **Riesgo R1 — Rollback no posible:** post-cleanup NO hay path legacy. Si LiteLLM tiene bug crítico runtime, el fallback es revert commit (no flag-based). **Mitigación:** evaluación T2 (sync-pricing job ya en CI) confirma estabilidad antes de DELETE T4. Tests audit T7 ANTES de T4 — si hay test que dependa de un adapter legacy specifically para validar capability legacy, magic comment + bypass o decisión Chris.
- **Riesgo R2 — Migración destructiva tenant API keys:** dropear `tenant.{openai,deepseek,kimi,dashscope}_api_key` columnas borra data. Si algún tenant en prod tiene non-null values (legacy importado o test), esa data se pierde. **Mitigación:** Q2 abierta — Chris decide drop directo en T6 vs 2-step (null first → drop next migration rolling deploy). Default propuesto: 2-step. Backup `tenant` table snapshot pre-migration.
- **Riesgo R3 — Tests stale post-cleanup:** ~20 tests mockean `OpenAIService.generate_response`/`KimiService`/etc. Sin migración correcta a `LiteLLMService` mock, tests pasan silenciosamente probando path muerto. **Mitigación:** T7 + arch fitness test (T8) que falla en CI si re-import. Aplica `.claude/rules/anti-default-flip-audit.md` 4-step audit.
- **Riesgo R4 — Gemini SDK quirks:** Gemini está vivo (no deprecated en flag) — verificar que LiteLLM maneja function-calling shape Gemini específicamente (Q3). **Mitigación:** Chris confirma o T4 hace audit pre-delete `gemini.py`.
- **Riesgo R5 — Pricing snapshot stale durante sync:** llamada LLM que aterriza durante `make sync-pricing` mid-commit puede ver snapshot viejo. **Mitigación:** runtime cost viene de `kwargs["response_cost"]` (LiteLLM-native), NO depende del snapshot — snapshot es solo ledger reconciliación. Cubierto en Scenario 3 del spec.
- **Asunción A1:** `BaseAgentCallbackHandler` ya está lifted shared (post anti-duplication.md). Verify en grep step 0.
- **Asunción A2:** `litellm_config.yaml` model_list es exhaustivo respecto a modelos en uso prod. Si hay modelo en `model_tier.py` mappings que NO está en yaml → bug pre-existente, levantar separado.

## Próximo paso

`→ Chris ratifica este 00-story.md + 01-spec.md (a continuación) → /architect lee + spawnea /architect-be para producir 03-arch-be.md + 04-tickets.yaml con T1..T9 detallados.`
