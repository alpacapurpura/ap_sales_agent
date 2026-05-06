# Learnings — sales-agent-litellm-canonicalization (PI-12 S1 Story A)

**Story outcome:** LiteLLM Proxy quedó como camino canónico único para todo dispatch LLM en runtime. Per-provider adapters legacy eliminados físicamente. Cost runtime captura vía `CustomLogger` pattern bridge LangChain↔LiteLLM. Tenant API keys deprecadas (Phase 1 expand-contract). Tests audit migrado al path canónico.

Este documento captura tres decisiones que merecen documentación durable, citadas frecuentemente durante el sprint y relevantes para futuros sprints LLM-routing.

---

## 1. CostRecorderCustomLogger — clase NUEVA justificada (T-1, commit `5856be4d`)

### Contexto

T-1 introdujo `backend/src/shared/agent_observability/recording/cost_recorder.py::CostRecorderCustomLogger`. Per `.claude/rules/anti-duplication.md`, antes de crear cualquier archivo nuevo en `shared/` el builder ejecuta Step 0 grep cross-codebase. La preocupación natural: el módulo `shared/agent_observability/recording/` ya tiene `BaseAgentCallbackHandler` (LangChain) — agregar otro callback parece duplicación.

### Decisión

`CostRecorderCustomLogger` es clase **NUEVA**, **no mirror**. Justificación ratificada por architect en `03-arch-be.md` § 10:

- LiteLLM `CustomLogger` y LangChain `BaseCallbackHandler` viven en superficies conceptualmente distintas (proxy-side vs runtime-side) y se invocan en lifecycle points diferentes.
- Coexisten por diseño: el handler LangChain captura el span LangChain (provider/model/tokens), el `CustomLogger` captura `kwargs["response_cost"]`. Se enlazan vía `litellm_call_id`.
- Esta es una abstracción nueva en una frontera nueva (callback de proxy LiteLLM), no un duplicado de la abstracción shared existente.

### Por qué importa

Sin `CustomLogger`, no hay forma de obtener el costo USD nativo que LiteLLM ya calcula en `kwargs["response_cost"]`. La alternativa era seguir corriendo `cost/calculator.py` en runtime — pero eso depende de `model_pricing_snapshot` que sufre drift respecto al pricing que LiteLLM realmente aplicó (Decision X2 BINDING T-1 hizo a `calculator.py` utility de reconciliación post-hoc, nunca runtime path).

### Mecánica

- TTL cache 60s keyed por `litellm_call_id` (`Decimal | None` value).
- `pop_cost(call_id)` es single-use — drena la entrada.
- Best-effort: cada mutación dentro de `try/except` + `structlog.warning`. Nunca bloquea el turn.
- Tenant-agnostic: cache process-wide. Tenant context vive en `BaseAgentCallbackHandler`.
- NFR p95 < 50ms verificado en micro-benchmark.

### Bridge end-to-end

```
LiteLLM proxy completion
   ↓ kwargs["response_cost"] (float, USD)
CostRecorderCustomLogger.log_success_event
   ↓ stash_cost(litellm_call_id, Decimal)
   ↓ TTL cache 60s
BaseAgentCallbackHandler.on_llm_end
   ↓ litellm_call_id ← response.response_metadata
   ↓ pop_cost(call_id) → Decimal | None
   ↓ persist
copilot_llm_call.cost_usd  /  sales_agent_llm_call.cost_usd
```

### Referencias

- Implementación: commit `5856be4d`
- Audit review: `06-audit/T-1-review.md` (APPROVED, 11/12 categories PASS)
- Contract: `03-arch-be.md` § 10 (architect ratification anti-duplication)
- Doc operacional: `docs/domains/llm-routing.md` § "CustomLogger pattern (cost recorder)"

---

## 2. T-6b operational gate — 1d wall-clock pre-clientes (R7, 2026-05-05)

### Contexto

T-6a deprecó las columnas `tenants.{openai,deepseek,kimi,dashscope}_api_key` (Phase 1 expand-contract). T-6c hace el `DROP COLUMN` definitivo. Entre ambos, el architect insertó **T-6b operational gate** — un ticket sin código cuyo único propósito es verificar que la migración T-6a se desplegó a producción antes de borrar columnas físicamente.

### Decisión original

Spec inicial pedía **5 días hábiles** de ventana zero-read (mirror de patterns expand-contract de equipos con tráfico productivo). Razonamiento: durante 5 días, la métrica `count(deprecated_cols WHERE NOT NULL) = 0` se mantiene → confirma que ninguna ruta de código activa lee las columnas legacy → safe to DROP.

### Re-escalación: pre-clientes 1d (R7 process-improvement 2026-05-05)

Nicolify aún no tiene clientes en producción. **No existe tráfico real**. La invariante zero-read se satisface trivialmente — no hay rutas activas porque no hay usuarios disparándolas.

R7 acordó:

- Reducir ventana T-6b a **1 día hábil pre-clientes**.
- El gate sigue existiendo, pero ya no protege contra "regresiones invisibles del cliente". Su función ahora: **verificar que la migración T-6a se desplegó efectivamente a prod** (vía Streamlit `admin/llm_virtual_keys.py` query → count(non-NULL) = 0) **antes** del DROP COLUMN T-6c.
- Auto-promote `awaiting-ops → pushed` post-pase-produccion + verificación Streamlit.
- Re-escalable a 5 días post-clientes activos. Cuando exista tráfico real, T-6b vuelve al spec original.

### Por qué importa

Documentado para evitar el anti-pattern "ventana de seguridad cargo-cult". Las ventanas de T+N días tienen sentido cuando hay tráfico que validar. Pre-clientes, el costo (semana congelada, dependencia bloqueada) supera el beneficio (verificación de un invariante ya cumplido por construcción).

La pieza que **no** cambia: el gate sigue siendo obligatorio. La diferencia es solo en el wall-clock window y en lo que el gate prueba (deployment-deployed, no zero-traffic-confirmed).

### Referencias

- Spec ticket: `04-tickets.yaml` § T-6b (state=`awaiting-ops`, ops_window_start=2026-05-06T00:30Z)
- Process learning: R7 process-improvement-handoff-2026-05-05
- Checkpoint: `checkpoint.md` 2026-05-06 00:30 entry

---

## 3. Gemini audit results — 6/6 PASS pre-delete (T-4, commit `429913a3`)

### Contexto

T-4 borraba 6 archivos legacy adapters. Cinco eran wrappers triviales (`openai.py`, `kimi.py`, `deepseek.py`, `qwen.py`, `_openai_compat.py`). El sexto, `gemini.py`, tenía contratos no triviales que LiteLLM debía replicar correctamente para evitar regresión silenciosa. Decisión A3 BINDING (T-4) dejó el delete bloqueado hasta que un **mandatory audit checklist 6/6** confirmara cobertura de cada contrato.

### Checklist auditado

| # | Contrato Gemini | Verificación | Resultado |
|---|---|---|---|
| 1 | Function calling vía `extra_body` | Test `test_function_calling_via_extra_body` propaga `tools` + `tool_choice` por `extra_body` y assertea round-trip | PASS |
| 2 | `safety_settings` vía `extra_body` | Test `test_safety_settings_via_extra_body` propaga el array `[{category, threshold}]` por `extra_body` | PASS |
| 3 | `system_instruction` conversion | Test `test_system_instruction_conversion` confirma que el primer mensaje role=`system` se mapea correctamente a `system_instruction` Gemini | PASS |
| 4 | `generation_config` mapping | Test `test_generation_config_mapping` confirma que `temperature`, `max_tokens`, `top_p`, `top_k` se traducen al shape `generation_config` que Gemini espera | PASS |
| 5 | Vision multipart payload | Test `test_vision_multipart_payload` confirma que `image_url` (data URL o https) se serializa multi-part correctamente | PASS |
| 6 | Streaming chunk normalization | Test `test_streaming_chunk_normalization` confirma que los chunks LangChain se generan con el mismo shape que el adapter previo | PASS |

### Tamaño real vs estimación

El context-validator inicial estimó `gemini.py` en ~320 LOC; medición efectiva mostró **99 LOC** simple wrapper. La diferencia no afectó el alcance — el audit exige cobertura por contrato, no por línea.

### Helpers retenidos

`_chat_model_resolver.py` y `_response_validation.py` quedaron **retenidos** post-T-4 (corrección del context-validator, ratificada por architect en CONTRACT § _kwargs RETAIN). Razón: ambos archivos son consumidos por `litellm.py` canónico — borrar = romper el adapter sobreviviente. Lo mismo aplica a `_kwargs.py` (normalización cross-provider).

### Por qué importa

Patrón replicable cuando un adapter se borra y el provider tiene contratos especiales (function calling, safety, system instruction). El delete sigue siendo seguro **solo** si el adapter sucesor (LiteLLM) soporta cada contrato — y los tests deben probar cada uno explícitamente, no por conjunto agregado.

Si en el futuro un adapter Anthropic (o cualquier provider con contratos no triviales) entra al codebase y se decide migrar al proxy, este checklist se replica: 6 categorías = function calling, safety, system instruction, generation params, vision, streaming. Falta de cobertura en cualquiera bloquea el delete.

### Referencias

- Implementación T-4: commit `429913a3`
- Tests: `backend/tests/shared/infrastructure/llm/test_litellm_gemini_function_call.py` (9 tests, 6 audit + 3 supporting)
- Audit review: `06-audit/T-4-review.md` (APPROVED, R3 downstream regression verified)
- Decision A3 BINDING: `01-spec.md` PO ratification 2026-05-04

---

## Cross-references

- Story spec: `01-spec.md`
- Architect contract BE: `03-arch-be.md`
- Tickets: `04-tickets.yaml`
- Checkpoint: `checkpoint.md`
- Doc canónico LLM routing: `docs/domains/llm-routing.md`
- Rule anti-duplication: `.claude/rules/anti-duplication.md`
- Rule anti-default-flip: `.claude/rules/anti-default-flip-audit.md`
- Rule schema-mirror exception: `.claude/rules/backend-ddd.md` § "Schema-mirror exception"
