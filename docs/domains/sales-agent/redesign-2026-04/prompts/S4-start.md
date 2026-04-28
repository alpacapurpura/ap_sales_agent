# Handoff prompt · S4 start

> **Refinado al cierre de S3 (2026-04-28).** S4 puede ir paralelo a S5 si recursos. Cache_boundary refactor (S3) ya cerrado — específicamente: el switch a Kimi/DeepSeek en S4 va a beneficiarse del prefix estable ≥1024 tokens YA presente.

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S4 — ChatModelSpec + per-role multi-provider adoption
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S4-chatmodelspec-tier.md
📝 Aprendizajes previos: learnings/S0, S1, S2, S3.

CONTEXTO post-S3 (cerrado 2026-04-28):
- S3 cerrada: `compose_system_prompt(fragments) -> str` mirror F8 copilot pattern. Single string con `CACHE_BOUNDARY_MARKER`. Slot order: static_identity → tools_hint → playbook → agent_identity → offer (S7 placeholder) → channel (S5 placeholder) → [BOUNDARY] → stage → signals → session_continuity → tool_format. Specialists qualifier/product_expert/closer migrados via `build_specialist_system_prompt(state, role)`. Supervisor fuera de scope (max_output_tokens=10).
- Prefix realista ~2700 tokens (>2× threshold OpenAI 1024).
- Arch test `tests/architecture/test_sales_agent_system_prompt_order.py` congela slot order (5 invariants).
- Hot path: `nodes.py::node_qualifier/product_expert/closer` ya llaman `build_specialist_system_prompt` y pasan single string a `LLMFactory.get_service().generate_response(system_prompt=...)`. **NO requieren cambio de signature en S4** — el contract sigue `system_prompt: str`.
- Branch: development limpio. Último commit S3: {HASH}
- Tests: 1613 passed quality gates (sales_agent + arch + admin + shared + copilot/observability).

HOOKS LISTOS PARA S4:
- `compose.py::SpecialistRole(StrEnum)` — QUALIFIER / PRODUCT_EXPERT / CLOSER. Si S4 introduce un nuevo specialist (improbable según §3), agregar entry + Jinja template + arch test snapshot.
- `compose.py::build_specialist_system_prompt(state, role)` — wrapper. S4 lo invoca igual; el output sigue siendo single string compatible con cualquier provider.
- `sales_agent_llm_call.cached_read_tokens` y `input_tokens` columnas (S1 migración 078) — métrica directa de hit rate post-deploy. Query: `SUM(cached_read_tokens) / NULLIF(SUM(input_tokens), 0) AS hit_rate FROM sales_agent_llm_call WHERE tenant_id=:t AND occurred_on >= :start;`.
- `CrossAgentCostAggregator(db).tenant_breakdown(tenant_id, start, end)` (S2) — disponible para verificar reducción de costo post-S4.

DEUDA REMANENTE para S4:
- DEFERRED-S4: adoptar `settings.get_provider_for_role(role)` + `ChatModelSpec` en sales_agent specialists. Hoy `LLMFactory.get_service().generate_response(model_type=ModelRole.X)` enruta global (vía `MultiRoleLLMRouter`) — S4 alinea con multi-provider per-role env vars (`AI_PROVIDER_AGENT=kimi`, `AI_PROVIDER_REASONING=deepseek`).
- DEFERRED-S4 hot wins:
  - **closer → ModelRole.AGENT (Kimi K2.6)**: cierres largos con manejo de objeciones + cache automático Kimi (75-83% savings) + prefix estable ya presente.
  - **product_expert / qualifier → ModelRole.REASONING (DeepSeek V4)**: razonamiento sobre product context + DeepSeek auto-cache disk-based (1/10 de costo input post 2026-04 price reduction).
  - **supervisor → ModelRole.NANO**: hoy es FAST. NANO si el classifier disponible (paridad con copilot F8).
- DEFERRED-S4 verifications:
  - LangChain normaliza `prompt_cache_hit_tokens` (DeepSeek) y `cached_read_tokens` (OpenAI/Kimi) en `usage_metadata.input_token_details.cache_read`. **Verificar empíricamente** post-deploy con turn real Kimi y DeepSeek; si NO normaliza, ajustar `SalesAgentCallbackHandler._extract_usage`.
- DEFERRED-post-S6: tier pricing >200k tokens en `shared/agent_observability/cost/calculator.py` (S2 watchpoint). Si S4 + cache_boundary genera turns con >200k input → reconciliar pre-S5.
- DEFERRED-post-S6: `_BASE_IDENTITY` y `_TOOLS_HINT` constants en `compose.py` (~150+250 tokens). Promover a Jinja templates + tools registry-driven cuando S8/S9 agreguen tools (riesgo de drift).
- DEFERRED-S5: `agent_identity.j2` mezcla offer + channel rules. Slots `OFFER_SUMMARY` y `CHANNEL_FORMAT_HINT` reservados pero vacíos en S3. S5 popula CHANNEL_FORMAT_HINT desde channel registry; S7 popula OFFER_SUMMARY desde brand_voice_summary.
- DEFERRED-post-S6: `SalesAgentCallbackHandler` 6 callbacks duplica copilot — lift a `BaseAgentCallbackHandler` cuando copilot retrofitee.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca)
   - 01-master-plan.md
   - 02-architecture-target.md (§3.2 ChatModelSpec, §3.3 multi-provider per-role)
   - 03-phase-protocol.md (10 + Paso 11 code review)
   - 04-principles.md (§1.4 acoplamiento — sales NO debe importar copilot)
   - 05-tech-debt-log.md (entradas DEFERRED-S4)
   - learnings/S0, S1, S2, S3.
   - phases/S4-chatmodelspec-tier.md
   - audit/sales-agent-current-state.md (§2.B outbound — sales hoy NO importa shared/infrastructure/llm/providers/_chat_model_resolver.py).
   - .claude/rules/copilot-resilience.md + copilot-observability.md (cómo medir cache hit rate via cached_read_tokens — análogo en sales_agent).

2. Research mandate S4 (mínimo 3 queries):
   - `ChatModelSpec dataclass langchain_openai 2026 reasoning_token_reserve` — verificar shape vigente.
   - `OpenAI o3 o4 reasoning_effort kwarg 2026` — confirmar qué modelos exponen.
   - `Kimi K2.6 thinking parameter disabled OpenAI compat 2026` — confirmar el kwarg que cierra reasoning para que llegue como agent puro.
   - `DeepSeek V4 reasoning model max_tokens 384k 2026` — verificar el reasoning_token_reserve real.
   - `LangChain langchain-deepseek native package vs openai_compat 2026` — descartar/confirmar bridge.

3. Documenta hallazgos en phases/S4-*.md sección "Hallazgos research".

4. TaskCreate granular.

5. TDD: tests RED primero.
   - `test_settings_resolves_provider_per_role`: env vars `AI_PROVIDER_AGENT`, `AI_PROVIDER_REASONING`, `AI_PROVIDER_NANO` mapean a ChatModelSpec correcto.
   - `test_specialist_closer_uses_agent_role` (mock): node_closer invoca `LLMFactory.get_service().generate_response(model_type=ModelRole.AGENT, ...)` (cambio de REASONING → AGENT por escenario).
   - `test_kwargs_normalizer_kimi_disables_thinking`: el normalizer de Kimi setea `enable_thinking=False`.
   - `test_no_hardcoded_provider_in_sales_agent_nodes` (AST scan).
   - `tests/architecture/test_sales_agent_chat_model_spec_invariants.py` (ratchet).

6. Refactor:
   - `domain/model_tier.py` (nuevo) con mapeo ROLE → tier metadata si sales necesita override de copilot.
   - `nodes.py` specialists: model_type override según escenario (closer → AGENT, qualifier/product_expert → REASONING, supervisor → NANO).
   - **NO duplicar** `ChatModelSpec` o providers — adoptar `shared/infrastructure/llm/providers/_chat_model_resolver.py` directo.

7. Quality gates nativos:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/ruff format --check src/ tests/`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ -x -q --tb=short`
   - `cd backend && .venv/bin/pytest tests/modules/copilot/observability/ -x -q` (regression check S2/S3).

8. Verificación funcional:
   - 1 conversación dev sales_agent. Verificar 2do turno tiene `cached_read_tokens > 0` (S3 cache_boundary intacto).
   - Verificar `model_responded` correcto en `sales_agent_llm_call` post-S4 (Kimi/DeepSeek según role).
   - §3 NO roto: smart_debounce, OutputManager, follow_up, frozen_detection.
   - `costo-agentes` admin renderiza con costos reducidos (estimado 30-50% reducción al cierre + uso Kimi).

9. Tech debt log: si S4 detecta nuevos provider drift / kwargs hardcoded → log + scan rule.

10. Cierre:
    - learnings/S4-*.md (denso, accionable).
    - prompts/S5-start.md refinado.
    - Mark FIXED entradas DEFERRED-S4 que se hayan resuelto.
    - Comparar antes/después: snapshot `mv_daily_llm_cost_per_tenant_v2` agent_kind='sales_agent' pre-S4 vs post-S4 (24h después de deploy).

11. Code review final (Paso 11):
    - Callers no rotos (specialists nodes.py + cualquier worker que use LLMFactory).
    - Cohesión: NO duplicar ChatModelSpec o normalizers.
    - Acoplamiento: sales_agent consume `shared/infrastructure/llm/...` direct. NO copilot import.

12. Commit: `feat(sales-agent-redesign-s4): adopt ChatModelSpec + per-role multi-provider routing`

PRINCIPIOS:
- TDD: tests RED primero.
- Anti-parche: si Kimi/DeepSeek breaking change post-S4 → root cause en `_kwargs.py`, no parchar.
- Best-effort: callback handler debe seguir loggeando cualquier provider sin crashear.
- Tenant isolation: queries con tenant_id.
- Stage por nombre en commits.
- Spanish neutro LATAM en cualquier nuevo string user-facing.

Empieza con paso 1.
```
