# S4 · Adopt ChatModelSpec + per-role routing

> **Actualizado 2026-04-28**: scope recortado. `ChatModelSpec`, multi-provider per-role, DeepSeek native, reasoning-budget trap, kwarg normalizer SSoT YA EXISTEN (commits c60197fa, 9d63c0da, 7dcc5db4, dfc57716). Esta fase = **adopción** en sales_agent, no diseño. Sí incluye mapping ROLE→TIER semantic per-specialist.

## Objetivo

Sales_agent adopta el routing multi-provider per-role + ChatModelSpec ya implementado. Specialists usan tier semántico (NANO/FAST/REASONING/AGENT). Aprovecha Kimi-K2.6 (AGENT) en specialists con loops largos y DeepSeek-Reasoner (REASONING) en manejo de objeciones complejas — costo ~5-10x menor con paridad de calidad para sales conversion.

## Dependencias

- S1 cerrado: callback handler graba `provider`/`model_responded` para validar resolver.
- (Independiente de S2/S3/S5 — paralelo OK.)

## Criterios de éxito

1. Sales_agent specialists consumen `LLMFactory.get_service(role=ModelRole.X)` que internamente resuelve `settings.get_provider_for_role(role)`.
2. Mapping per-specialist documentado:
   - `supervisor` → `ModelRole.NANO` (decisión rápida)
   - `buffer_completeness_check` → `ModelRole.NANO`
   - `qualifier` → `ModelRole.FAST`
   - `product_expert` → `ModelRole.AGENT` (Kimi K2.6 — explicaciones largas)
   - `closer` → `ModelRole.AGENT` (Kimi K2.6 — manejo objeciones, idempotente con cache)
   - `objection_handler` (si emerge) → `ModelRole.REASONING` (DeepSeek-Reasoner)
3. `domain/model_tier.py` declara mapping `SPECIALIST_TO_ROLE` semantic, no hardcoded models.
4. Reasoning-budget trap respetado: si DeepSeek-V4 o equivalente, `max_output_tokens` cuenta el reserve de 4000 tokens (provider-side) — verificar via integration test.
5. Tenant API keys (deepseek/kimi/dashscope) ya soportadas por `Tenant` domain (migration 073) — sales_agent puede consumir vía `get_service_for_tenant(tenant_id, role)`.
6. Test arch `test_no_hardcoded_models_sales_agent` pasa.
7. Test integration: same input invocado con env `AI_PROVIDER_AGENT=kimi` vs `=openai` → kwargs normalizados correcto en cada caller; outputs no-equivalentes pero válidos.
8. Quality gates verdes.

## Research mandate

> **Recortado.** Mucho del research se hizo en abril (commits c60197fa, 7dcc5db4, dfc57716, a3f65d04). Verificar drift desde abril.

### Queries WebSearch obligatorias

1. `Kimi K2.6 thinking-disabled mode temperature recommended 2026` — verificar si los defaults clamp temp 0.6 siguen vigentes.
2. `DeepSeek V4 reasoning_token_reserve change 2026` — si valor por defecto de 4000 cambió.
3. `LangChain langchain-deepseek package latest 2026` — version + breaking changes.

### Tessl tiles

- `tessl__langgraph` — verify SystemMessage cache compatibility cross-provider.

### Lectura obligatoria

- `learnings/S1-*.md`.
- `backend/src/shared/infrastructure/llm/factory.py`.
- `backend/src/shared/infrastructure/llm/providers/_kwargs.py` — `normalize_openai_protocol_kwargs`.
- `backend/src/shared/infrastructure/llm/providers/_chat_model_resolver.py` — `ChatModelSpec`.
- `backend/src/shared/infrastructure/llm/providers/deepseek.py`.
- `backend/src/shared/infrastructure/llm/providers/kimi.py`.
- `backend/src/modules/copilot/domain/model_tier.py` — pattern reference.
- `backend/src/core/config.py` — `AI_PROVIDER_*` env + `get_provider_for_role`.
- Commits 9d63c0da, c60197fa, 7dcc5db4, dfc57716, a3f65d04, 222bd54a (rationale).

### Hallazgos research (2026-04-28)

**Kimi K2.6 (Moonshot, released 2026-04-20)**
- 1T params, 32B activated, 256K context. Open-weight + native multimodal. Beats GPT-5.4 + Claude Opus 4.6 + Gemini 3.1 Pro en SWE-Bench Pro.
- OpenAI compat full (chat.completions, streaming, tools, tool_choice, temperature, top_p, max_tokens).
- Thinking-disabled (`thinking={"type": "disabled"}`) requiere `temperature=0.6` (server-enforced). Thinking-enabled requiere `temperature=1.0`.
- Sales_agent ya tiene esta lógica correcta en `KimiService._get_chat_model` (auto-clamp temp + force `extra_body.thinking={"type":"disabled"}`).
- **Conclusión S4**: switch closer→AGENT (Kimi) es seguro. Auto-cache 75-83% savings ya documented. NO hay cambio de kwargs adicional necesario.

**DeepSeek V4 (released April 2026)**
- V4-Pro: 1.6T params (49B activated). V4-Flash: 284B (13B activated). 1M context window.
- Reasoning + visible content comparten `max_tokens` budget (mismo trap original V3-V4). Reserve 4000 sigue válido.
- **Migration deadline Jul 24 2026**: `deepseek-chat` y `deepseek-reasoner` aliases retiran → migrar explícito a `deepseek-v4-pro`/`deepseek-v4-flash`. **NO bloquea S4** (env-var `AI_MODEL_REASONING` resuelve dinámico). Tech-debt entry para refresh pre-Jul 2026.
- `langchain-deepseek` package native expone `prompt_cache_hit_tokens` raw + LangChain normaliza a `usage_metadata.input_token_details.cache_read` standard.
- **Conclusión S4**: qualifier/product_expert quedan REASONING. DeepSeek V4 disk-based auto-cache ya activo via `AI_PROVIDER_REASONING=deepseek` env var. No code change adicional.

**OpenAI o3 / o4-mini (2026)**
- o3 tiene `reasoning_effort` (low/medium/high) — funciona via `_kwargs.py::normalize_openai_protocol_kwargs`.
- **o4-mini NO expone `reasoning_effort`** (solo o3). NANO/FAST que ruteamos a OpenAI no necesitan reasoning_effort.
- **Conclusión S4**: supervisor→NANO (gpt-5.4-nano si OpenAI catalog actualiza, hoy gpt-4o-mini fallback) seguro. Sin cambios al normalizer.

**LangChain `usage_metadata.input_token_details.cache_read` (2026)**
- Standard cross-provider: OpenAI / DeepSeek / Kimi / Gemini normalizan correcto.
- **Anthropic conocido bug**: 2× counts en `message_delta` streaming (issue #32818). NO afecta sales_agent (no rutea a Claude).
- DeepSeek raw key `prompt_cache_hit_tokens` se mapea a `cache_read` por el partner package nativo.
- **Conclusión S4**: el callback handler S1 (`SalesAgentCallbackHandler._extract_usage`) lee `usage_metadata.input_token_details.cache_read` → trabaja correcto post-S4 sin ajuste para Kimi/DeepSeek. Watchpoint S3 ya cubierto.

### Inventory de specialists con LLM (sales_agent)

| Site | Path | Hoy | Post-S4 | Razón |
|---|---|---|---|---|
| supervisor | `nodes.py:108` | `FAST` | **`NANO`** | classifier 10-token output; paridad copilot F8. |
| qualifier | `nodes.py:140` | `REASONING` | `REASONING` | DeepSeek V4 auto-cache + razonamiento sobre lead context. Sin cambio. |
| product_expert | `nodes.py:154` | `REASONING` | `REASONING` | DeepSeek V4 auto-cache + razonamiento sobre offer context. Sin cambio. |
| closer | `nodes.py:168` | `REASONING` | **`AGENT`** | Kimi K2.6 cierres largos + cache 75-83% + manejo objeciones. Cambio principal S4. |

Fuera de SPECIALIST_TO_ROLE scope (mantenidos):
- `safety_service.py:120` (FAST): PII/jailbreak detection — apropiado FAST.
- `chat.py:550` (FAST): summary generator — candidato NANO post-S4 (DEFERRED).
- `follow_up_engine.py:83` (FAST): nudge message gen — candidato NANO post-S4 (DEFERRED).

---

## Diseño

### `sales_agent/domain/model_tier.py`

```python
# Reuse ModelRole from shared (NO duplicate enum).
from src.shared.domain.model_role import ModelRole

# Specialist → Role mapping (SSoT).
SPECIALIST_TO_ROLE: dict[str, ModelRole] = {
    "supervisor": ModelRole.NANO,
    "buffer_completeness_check": ModelRole.NANO,
    "qualifier": ModelRole.FAST,
    "product_expert": ModelRole.AGENT,
    "closer": ModelRole.AGENT,
    "objection_handler": ModelRole.REASONING,  # if specialist exists
    "summary_generator": ModelRole.NANO,
    "tool_executor": ModelRole.FAST,
    "signal_accumulator": ModelRole.NANO,
}
```

NO duplicar `ChatModelSpec` ni `TIER_METADATA` — viven en `shared/`. Sales_agent solo declara mapping semantic.

### Refactor specialists

ANTES:
```python
service = LLMFactory.get_service()
response = await service.generate_response(
    model_type=ModelRole.FAST,
    temperature=0.2, max_output_tokens=700, ...
)
```

DESPUÉS:
```python
role = SPECIALIST_TO_ROLE["qualifier"]
service = LLMFactory.get_service(role=role)
# settings.get_provider_for_role(role) → resolves provider
response = await service.generate_response(
    temperature=0.2, max_output_tokens=700, ...
)
```

### Test integration cross-provider

```python
@pytest.mark.parametrize("provider_env", ["openai", "kimi", "deepseek"])
async def test_specialist_qualifier_provider_agnostic(provider_env, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_FAST", provider_env)
    state = build_state(...)
    output = await run_specialist(state, "qualifier")
    assert output.role == "assistant"
    assert len(output.content) > 0
    # NO comparar exact tokens — providers difieren.
```

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/test_specialist_role_mapping.py`:
   - `SPECIALIST_TO_ROLE` cubre todos los specialists.
   - No hardcoded model names en specialist files.

2. `tests/modules/sales_agent/test_specialist_provider_agnostic.py`:
   - Each specialist runs OK con provider override.
   - Kimi K2.6 specialista AGENT → `model_responded='kimi-k2.6'` en `sales_agent_llm_call`.

3. `tests/architecture/test_no_hardcoded_models_sales_agent.py`:
   - AST scan: no `"gpt-*"`, `"claude-*"`, `"deepseek-*"`, `"kimi-*"` strings literales en `application/agents/sales/`.
   - Excepción: `domain/model_tier.py` (SSoT mapping).

4. `tests/modules/sales_agent/test_reasoning_budget_respected.py`:
   - Specialist con `ModelRole.REASONING` y `max_output_tokens=2000` → kwargs normalizados con reserve aplicado al wire param correcto del provider.

---

## Implementación step-by-step

1. Verificar `ModelRole` enum existe en `shared/` (post-commits abril). Si en `copilot/domain/model_tier.py` solamente → mover a `shared/domain/model_role.py`.
2. `domain/model_tier.py` con `SPECIALIST_TO_ROLE` mapping.
3. Refactor specialists nodes.py para usar `SPECIALIST_TO_ROLE[name]` resolución.
4. Tenant config wire (si aplica): `get_service_for_tenant(tenant_id, role)` ya disponible vía Tenant domain (migration 073).
5. Tests integration cross-provider.
6. Verificación: `sales_agent_llm_call.provider` distribución debe reflejar mapping post-deploy.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Specialist closer con Kimi K2.6 difiere notable de gpt-4o → conversiones bajan | A/B canary 10% antes 100%. Goldens (S10) detectan drift. |
| Reasoning budget trap silencioso (DeepSeek output truncated) | Test integration verifica output coherente con `max_output_tokens` declarado. |
| Tenant config no propaga API key per-role | Verificar `get_service_for_tenant(tenant_id, role)` resuelve correctamente. Test con tenant fixture. |
| Provider X spec falla | `_kwargs.py::normalize_openai_protocol_kwargs` SSoT ya cubre — verificar test cubre cross-provider. |

---

## Tech debt watchpoints

- Hardcoded model strings detectados → fix en archivo tocado (Paso 11.5 cleanup oportunista).
- Si tenant config no encryption-at-rest para api_keys → CRITICAL — escalar.
- Si `LLMFactory.get_service` con kwargs sucios pasados al provider → refactor en archivo tocado.
- Si `ModelRole` enum duplicado entre copilot y sales → mover a shared (DRY).

---

## Ajustes vs plan original

> **Ajuste 2026-04-28**: scope recortado significativamente. Diseño de ChatModelSpec, multi-provider routing, reasoning-budget trap, pricing aliases YA están en codebase post-abril 2026. Esta fase es **adopción** + mapping ROLE→specialist semantic. Tiempo estimado bajó de 2-3 días a 1-2 días.
