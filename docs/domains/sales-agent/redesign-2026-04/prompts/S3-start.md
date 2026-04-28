# Handoff prompt · S3 start

> **Refinado al cierre de S2 (2026-04-28).** Pin al commit hash del cierre tras `git log` post-commit.

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S3 — Prompt cache_boundary refactor (sales_agent)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
📝 Aprendizajes previos: learnings/S0, learnings/S1, learnings/S2.
   (S4 puede correr en paralelo con S3; si ya cerró, leer learnings/S4 también.)

CONTEXTO post-S2 (cerrado 2026-04-28):
- S2 cerrada: registry pasivo `shared/agent_observability/registry.py` (passive registry pattern + bootstrap externo `shared/infrastructure/agent_observability_bootstrap.py`). Cada modules/*/observability/__init__.py registra su spec via `register_agent_observability(spec)`.
- CostAggregator parametrizado por `(db, llm_call_model)` + `CrossAgentCostAggregator(db)` que itera el registry. `top_leads_by_cost` para sales_agent (verifica `_has_lead_id`); `top_conversations_by_cost` para copilot.
- cost_alert_service cross-agent en `shared/agent_observability/application/cost_alert_service.py`. Emite structlog `cost_alert_threshold_exceeded` con `breakdown_usd_by_agent` (dict `{copilot, sales_agent}`).
- Workers cross-agent en shared: `aggregate_refresh_task` refresca **ambas** MVs (legacy + v2) con per-MV best-effort; `retention_task` itera registry con env vars per-agent (`COPILOT_*` y `SALES_AGENT_*`); `cost_alert_task` envuelve `check_cost_alerts`.
- Migración 079 aplicada: `mv_daily_llm_cost_per_tenant_v2 (agent_kind, tenant_id, occurred_on)` UNION ALL idempotente con UNIQUE INDEX. CONCURRENT refresh verificado.
- Streamlit `costo-agentes`: tabs Total (cross-agent + stacked bar) y Por agente (selector `_shared.render_agent_kind_selector` + drill-down por modelo + serie 60d + top leads cuando `spec.has_lead_id`).
- 2970 tests passed; ruff/format clean.
- Branch: development limpio. Último commit S2: `a5dbf3ab`

HOOKS LISTOS PARA S3:
- `sales_agent_llm_call.cached_read_tokens` y `cached_write_tokens` columnas ya existen (migración 078). Callback handler S1 los popula desde `usage_metadata.input_token_details.cache_read`.
- `compose_system_prompt` slot order target en `02-architecture-target §3.4`. Ahora con cost cross-agent disponible, podemos medir cache hit rate post-deploy y compararlo con baseline pre-S3 (~0%).
- `CrossAgentCostAggregator(db).tenant_breakdown(tenant_id, start, end)` lo lee directo cualquier dashboard analytics.
- `agent_observability_registry()` está disponible en code paths nuevos — NO hardcodear strings de agente.

DEUDA REMANENTE para S3 / posterior:
- DEFERRED-S3: cache_boundary refactor de sales_agent prompts (sales/nodes.py, infrastructure/prompts/templates/*.j2). Target: prefix cacheable ≥1024 tokens, hit rate ≥60%, costo reducido ~25-30%.
- DEFERRED-S4 (paralelizable): adoptar `settings.get_provider_for_role(role)` + ChatModelSpec en sales_agent specialists. Hoy llaman `LLMFactory.get_service(ModelRole.X)` directo. Kimi=AGENT (closer) y DeepSeek=REASONING (objeciones complejas) son los wins.
- DEFERRED-post-S6: tier pricing >200k tokens en `shared/agent_observability/cost/calculator.py`. Si S3 incrementa context size → reconciliar pre-S4.
- DEFERRED-post-S6: lift `SalesAgentCallbackHandler` 6 callbacks a `BaseAgentCallbackHandler` (Template Method) cuando copilot retrofitee.
- DEFERRED-post-S6: PII async post-write worker (Presidio + spaCy NER).
- DEFERRED-S6: docs (tech-debt-log + admin-migration-plan) menciones a `agent_log_model.py` que no existe — la legacy real es `llm_logs` con clase `LLMLog`.
- DEFERRED-S6: drop tablas legacy `agent_trace_model` + `LLMLogModel` post cutover dual-write.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca)
   - 01-master-plan.md
   - 02-architecture-target.md (§3.4 compose_system_prompt slot order)
   - 03-phase-protocol.md (10 + Paso 11 code review)
   - 04-principles.md (especialmente §3 TDD obligatorio + §5 PII safety)
   - 05-tech-debt-log.md (entradas DEFERRED-S3)
   - learnings/S0-*.md + S1-*.md + S2-*.md
   - phases/S3-prompt-cache-boundary.md
   - audit/sales-agent-current-state.md
   - .claude/rules/copilot-resilience.md (Phase 8 cache_boundary copilot reference)
   - .claude/rules/copilot-observability.md (cómo medir cache hit rate via copilot_llm_call.cached_read_tokens — análogo en sales_agent_llm_call)

2. Research mandate S3 (mínimo 3 queries):
   - `OpenAI prompt caching minimum tokens 1024 cache_control 2026` — confirmar threshold actual.
   - `Anthropic Claude cache_control blocks system_prompt 2026` — sintaxis para Sonnet/Haiku 4.x cuando se enrute.
   - `Kimi K2.6 prompt cache support OpenAI-compatible API 2026` — verificar que el pattern funciona con providers chinos.
   - `DeepSeek-V4 prompt cache reasoning model 2026` — DeepSeek soporta cache desde V3, confirmar V4.
   - `LangChain SystemMessage cache_control multi-message pattern 2026` — patrón de doble SystemMessage (cacheable prefix + volatile suffix).

3. Documenta hallazgos en phases/S3-*.md sección "Hallazgos research".

4. TaskCreate granular para implementación.

5. TDD: tests RED primero.
   - `test_compose_system_prompt_returns_two_messages`: 1 SystemMessage cacheable + 1 SystemMessage volatile.
   - `test_compose_system_prompt_slot_order`: identity → tools_hint → playbook → lighthouse → offer → channel_format → CACHE_BOUNDARY → stage → signals → recent → tool_format.
   - `test_cache_prefix_token_count_at_least_1024`: con tiktoken o approximation, ≥1024 tokens en el prefix.
   - `test_no_per_turn_data_in_cacheable_prefix`: lead state, recent_messages, stage, signals NO aparecen en el primer SystemMessage.
   - `test_prompt_version_override_lands_in_lighthouse_slot`: si tenant tiene PromptVersion override, vive en slot 4 (cacheable per-tenant) — NO suffix.
   - `tests/architecture/test_sales_agent_system_prompt_invariants.py`: ratchet sobre slot order.

6. Refactor:
   - Agregar `compose_system_prompt(state)` en `application/prompts/compose.py` (nuevo).
   - Migrar `sales/nodes.py` specialists para llamar `compose_system_prompt(state)` y pasar la lista al LLM.
   - Mantener `PromptLoader` actual; `compose_*` orquesta los fragments.
   - PromptVersionModel override sigue funcionando — solo cambia DÓNDE se inyecta.

7. Quality gates nativos:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/ruff format --check src/ tests/`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ -x -q --tb=short`
   - `cd backend && .venv/bin/pytest tests/modules/copilot/observability/ -x -q` (asegurar S2 no regresivo).
   - Si S4 cerró: also `cd backend && .venv/bin/pytest tests/modules/sales_agent/orchestrator/ -x -q --tb=short`.

8. Verificación funcional:
   - Disparar 1 conversación sales_agent en dev (curl al webhook o admin). Verificar 2do LLM call del turn tiene `cached_read_tokens > 0`:
     ```sql
     SELECT turn_id, model_responded, input_tokens, cached_read_tokens, cost_usd
     FROM sales_agent_llm_call
     WHERE tenant_id = :tenant AND turn_id = :recent
     ORDER BY started_at;
     ```
   - §3 NO roto: smart_debounce, OutputManager, follow_up, frozen_detection.
   - `costo-agentes` admin sigue renderizando (no queremos que cache_boundary haya tocado nada del cost path).

9. Tech debt log: si S3 detecta nuevos prompts hardcoded (voseo, copilot-style) durante refactor → log + scan rule.

10. Cierre:
    - learnings/S3-*.md (denso, accionable, métricas reales de hit rate post-deploy).
    - prompts/S4-start.md refinado (si S4 no cerró aún) o S5-start.md.
    - Mark FIXED entradas DEFERRED-S3 que se hayan resuelto.
    - Comparar antes/después: snapshot de `mv_daily_llm_cost_per_tenant_v2` agent_kind='sales_agent' pre-S3 vs post-S3 (24h después de deploy). Hit rate target ≥60%.

11. Code review final (Paso 11):
    - Callers no rotos (specialists nodes.py + LLMFactory.get_service consumers).
    - Cohesión: `compose.py` solo orquesta — no toca PromptLoader internals.
    - Acoplamiento: si S3 introduce dependency a brand_summary_lighthouse (S7 territory), parar y preguntar.

12. Commit: `feat(sales-agent-redesign-s3): cache_boundary refactor sales_agent prompts`

PRINCIPIOS:
- TDD: tests RED primero. Goldens-style snapshots ayudan.
- Anti-parche: si cache hit rate <60% post-deploy → root cause (slot order incorrecto / tokens insuficientes / provider no soporta) → re-medir, no parchar.
- Best-effort: cualquier cache miss debe loguear motivo (no solo `cached_read_tokens=0`).
- Tenant isolation: cualquier query nuevo filter `tenant_id`.
- Stage por nombre en commits (`.claude/rules/parallel-safety.md`).
- Spanish neutro LATAM en system prompts user-facing (sin voseo) — respeta override de Brand Studio si tenant configuró otro tono.

Empieza con paso 1.
```
