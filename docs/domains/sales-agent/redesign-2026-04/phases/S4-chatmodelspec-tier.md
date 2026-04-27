# S4 · ChatModelSpec + tier adoption

## Objetivo

Sales_agent adopta `CHAT_MODEL_SPEC` per provider + tier system (NANO / MINI / REASONING / HEAVY). Hereda anti-incidente del 2026-04-27 (kwarg translation + reasoning-budget trap fix). Garantiza consistencia kwargs cross-provider y permite cache compatible.

## Dependencias

- S1 cerrado: callback handler graba `provider`/`model_responded` para validar resolver.
- (Independiente de S2 y S3 — puede ir en paralelo.)

## Criterios de éxito

1. `model_tier.py` declarado en `sales_agent/domain/` (mirror de copilot `domain/model_tier.py`).
2. `CHAT_MODEL_SPEC` tipado declarado para cada provider que sales_agent usa: OpenAI, Anthropic, DeepSeek, Gemini.
3. `LLMFactory.get_service(role=ModelRole.X)` resuelve spec via SSoT (no hardcoded en consumer).
4. Kwarg translation (`max_tokens` → `max_completion_tokens`, `max_output_tokens`, etc.) pasa por `providers/_kwargs.py::normalize_openai_protocol_kwargs` único.
5. Reasoning-budget trap fix verified: providers reasoning (o1, o3, etc.) no reciben kwargs incompatibles.
6. Tier mapping `ModelRole.FAST` → tier NANO/MINI; `ModelRole.REASONING` → REASONING. Documentado.
7. Tests existentes verdes. Nuevos tests cubren spec resolution + kwarg translation.
8. Sin hardcoded model names en `nodes.py` o specialist code.

## Research mandate

### Queries WebSearch obligatorias

1. `OpenAI o3 o4 reasoning model API kwargs 2026 incompatibilities` — verificar lista vigente.
2. `Anthropic Claude 4.7 message API max_tokens prompt cache integration` — confirmar shape.
3. `DeepSeek API protocol OpenAI compat 2026 differences` — DeepSeek diverge en algunas keys.
4. `Gemini chat API max_output_tokens convention 2026` — Gemini usa `maxOutputTokens` (camelCase).

### Tessl tiles

- `tessl__langchain` — convenciones de model abstractions en LangChain 0.3+.

### Lectura obligatoria

- `learnings/S1-*.md`.
- `backend/src/shared/infrastructure/llm/factory.py`.
- `backend/src/shared/infrastructure/llm/providers/_kwargs.py` (post-incidente 2026-04-27).
- `backend/src/shared/infrastructure/llm/providers/openai_compat.py`.
- `backend/src/modules/copilot/domain/model_tier.py`.
- Commits recientes que tocaron `llm-providers` (`7dcc5db4`, `c60197fa`, `dfc57716`, `222bd54a`).

### Hallazgos research

> COMPLETAR.

---

## Diseño

### `sales_agent/domain/model_tier.py`

```python
class SalesAgentModelTier(Enum):
    NANO = "nano"           # Routing decisions, intent classification, single-token outputs
    MINI = "mini"            # Buffer completeness check, channel intent detection
    REASONING = "reasoning"  # Specialists (qualifier, product_expert, closer)
    HEAVY = "heavy"          # Edge cases, high-stakes closer override

@dataclass(frozen=True)
class TierMetadata:
    tier: SalesAgentModelTier
    default_provider: str
    default_model: str
    max_input_tokens: int
    max_output_tokens: int
    supports_caching: bool
    cost_per_1m_input_usd: Decimal
    cost_per_1m_output_usd: Decimal

TIER_METADATA: dict[SalesAgentModelTier, TierMetadata] = {
    SalesAgentModelTier.NANO: TierMetadata(...),  # gpt-4o-mini default
    SalesAgentModelTier.MINI: TierMetadata(...),
    SalesAgentModelTier.REASONING: TierMetadata(...),  # gpt-4o or claude-sonnet-4-6
    SalesAgentModelTier.HEAVY: TierMetadata(...),  # claude-opus-4-7
}
```

### Mapping `ModelRole` → tier

```python
ROLE_TO_TIER = {
    ModelRole.FAST: SalesAgentModelTier.MINI,
    ModelRole.REASONING: SalesAgentModelTier.REASONING,
    ModelRole.HEAVY: SalesAgentModelTier.HEAVY,
}
```

`ModelRole` legacy se preserva — sólo agrega capa tier interna.

### `CHAT_MODEL_SPEC` per provider

```python
# src/shared/infrastructure/llm/providers/openai.py
CHAT_MODEL_SPEC = ChatModelSpec(
    provider="openai",
    supported_models=["gpt-4o", "gpt-4o-mini", "o3-mini", "o4-mini"],
    kwargs_normalizer="openai_protocol",
    supports_caching=True,
    cache_block_threshold=1024,
    reasoning_models={"o3-mini", "o4-mini"},
    incompatible_kwargs_for_reasoning={"max_completion_tokens", "temperature"},
)
```

### Kwarg translation SSoT

`providers/_kwargs.py::normalize_openai_protocol_kwargs` ya existe (post-incidente). Verificar:
- `max_tokens` → `max_completion_tokens` (chat completions)
- `max_output_tokens` → strip si reasoning model
- `temperature` → strip si reasoning model
- Sales_agent consume vía LLMFactory; no llama directo.

### Provider-agnostic configuration

```python
# Tenant config DB
class SalesAgentLlmConfig:
    tenant_id: UUID
    fast_provider: str  # default "openai"
    fast_model: str  # default tier metadata
    reasoning_provider: str
    reasoning_model: str
    api_keys: dict  # encrypted
```

`get_service_for_tenant(tenant_id, role)` resuelve spec.

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/test_model_tier_resolution.py`:
   - `ROLE_TO_TIER[FAST]` = MINI.
   - Tier metadata completa per tier.
   - No tier sin pricing.

2. `tests/shared/llm/test_kwargs_normalizer_sales.py`:
   - `max_tokens=N` con OpenAI normal → `max_completion_tokens=N`.
   - `max_tokens=N` con o3-mini → strip + log warning.
   - DeepSeek → no traducción incorrecta.
   - Gemini → `maxOutputTokens` (camelCase).

3. `tests/architecture/test_no_hardcoded_models_in_sales_agent.py`:
   - AST scan: no `"gpt-4o"`, `"claude-*"`, `"deepseek-chat"` strings literal en `application/agents/sales/`.
   - Excepción: `domain/model_tier.py` (SSoT).

4. `tests/modules/sales_agent/test_provider_agnostic_kwargs.py`:
   - Mismo `state` invocado con OpenAI vs Anthropic vs DeepSeek → kwargs traducidos correctamente.

---

## Implementación step-by-step

1. `domain/model_tier.py` con enum + metadata.
2. `ROLE_TO_TIER` mapping.
3. Verificar `LLMFactory` consume spec; refactor si es directo.
4. Specialists nodes: reemplazar hardcoded `model_type=ModelRole.X` con `tier=SalesAgentModelTier.X` (semantic).
5. Wire tenant config (si existe) → spec resolution.
6. Tests + verificación.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Provider X spec falla en reasoning model | Test exhaustivo. Add to spec `incompatible_kwargs_for_reasoning`. |
| Tenant override breaks tier | Validar tenant config schema. Fallback a default si invalid. |
| Mapping ROLE→TIER pierde flexibility | Mantener ambos. Tier es interno; Role es contract público. |
| Spec drift entre copilot y sales_agent | Validar que `CHAT_MODEL_SPEC` vive en provider (compartido), no per-agent. |

---

## Tech debt watchpoints

- Hardcoded model strings detectados durante AST scan → fixed o documented.
- `LLMFactory.get_service` con kwargs sucios pasados al provider → refactor.
- Métricas de cost en `model_tier.py` deben venir de `model_pricing_snapshot` (no hardcoded). Si están hardcoded → flag.
- Tenant config sin encryption para api_keys → CRITICAL — escalar.

---

## Ajustes vs plan original

> COMPLETAR.
