# S3 · Prompt cache_boundary refactor

## Objetivo

Refactorizar el system prompt de los specialists de sales_agent (qualifier / product_expert / closer / supervisor) a fragments ordenados con `cache_boundary` explícito. Target: prefix cacheable ≥1024 tokens contiguos → cache hit rate ≥60% → reducción ~25-30% LLM cost.

## Dependencias

- S1 cerrado: callback handler captura `cached_read_tokens` para medir hit rate real.
- S4 paralelo o cerrado: tier system + ChatModelSpec definidos para que cache funcione consistente entre providers.

## Criterios de éxito

1. `compose_system_prompt(state) → list[SystemMessage]` en `sales_agent/application/prompts/compose.py`.
2. Slot order documentado y enforced por arch test (mirror de copilot `test_system_prompt_order.py`).
3. Prefix cacheable (slots 1-6) ≥1024 tokens en tenant promedio.
4. Volatile (slots 7-10) sin entrelazarse con cacheable.
5. Cache hit rate medido en `sales_agent_llm_call.cached_read_tokens / input_tokens` ≥60% post-deploy 7 días.
6. Specialists nodes (`nodes.py`) usan `compose_system_prompt(state)` en vez de Jinja render directo.
7. **PromptVersionModel multi-tenant override sigue funcionando**: el override DB-backed se inyecta en el slot apropiado (4 cacheable per-tenant para identity, o 7+ volatile para overrides exoticos).
8. Quality gates verdes.

## Research mandate

### Queries WebSearch obligatorias

1. `OpenAI prompt caching threshold 1024 tokens 2026 minimum prefix` — verificar threshold vigente (puede haber bajado/subido).
2. `Anthropic Claude prompt cache_control blocks placement strategy 2026` — sales_agent puede usar Claude tier — verificar API.
3. `LangChain SystemMessage prompt cache compatibility OpenAI Anthropic Gemini` — diferencias por provider.
4. `prompt engineering progressive disclosure cacheable static dynamic split 2026` — patterns.

### Tessl tiles

- `tessl__langgraph` — verificar invariantes de SystemMessage en StateGraph nodes.

### Lectura obligatoria

- `learnings/S1-*.md`, `learnings/S2-*.md` (si S2 cerró antes).
- `backend/src/modules/copilot/application/orchestrator/graph.py` — `build_system_prompt` cacheable de copilot (F8 implementación).
- `backend/src/modules/sales_agent/application/agents/sales/nodes.py` — `_build_system_prompt` actual.
- `backend/src/modules/sales_agent/infrastructure/prompts/templates/specialist_*.j2`.
- `backend/src/modules/sales_agent/infrastructure/prompts/base.py` — `PromptLoader`.
- `.claude/rules/copilot-resilience.md` — sección "System prompt order".
- `docs/domains/copilot/redesign-2026-04/learnings/F8-routing.md`.

### Hallazgos research

> COMPLETAR.

---

## Diseño

### Slot order (S3 target)

Slots cacheable (cross-tenant + per-tenant pre-renderizados):

| # | Fragment | Origen | Cache scope | Tamaño aprox |
|---|---|---|---|---|
| 1 | `static_identity` | Constante código | Cross-tenant | 200 tokens |
| 2 | `tools_hint` | Generado de tools registry | Cross-tenant (cambia raro) | 300 tokens |
| 3 | `sales_playbook_hint` | Constante (rapport→discovery→presentation→closing) | Cross-tenant | 400 tokens |
| 4 | `agent_identity_lighthouse` | `brand_voice_summary` table (S7 lo poblará) | Per-tenant cacheable | 300-500 tokens |
| 5 | `offer_summary` | `offer_summary` table cacheable | Per-tenant cacheable | 200-400 tokens |
| 6 | `channel_format_hint` | `ChannelFormat` registry (S5) | Per-tenant cacheable (raro cambia) | 100 tokens |

**[CACHE_BOUNDARY_MARKER]** ← split de SystemMessage acá.

Slots volatile:

| # | Fragment | Origen | Tamaño aprox |
|---|---|---|---|
| 7 | `stage_hint` | state.current_state | 50 tokens |
| 8 | `lead_signals` | state.buying_signals + objection_history | 100-300 tokens |
| 9 | `recent_messages_summary` | últimos N mensajes | 200-500 tokens |
| 10 | `tool_request_format` | suffix con sintaxis `[TOOL_REQUEST: ...]` | 100 tokens |

### Implementación

```python
# src/modules/sales_agent/application/prompts/compose.py
from langchain_core.messages import SystemMessage

CACHE_BOUNDARY = "<<<CACHE_BOUNDARY_MARKER>>>"

def compose_system_prompt(state: AgentState) -> list[SystemMessage]:
    cacheable_fragments = _build_cacheable_fragments(state)
    volatile_fragments = _build_volatile_fragments(state)
    return [
        SystemMessage(content="\n\n".join(cacheable_fragments)),  # 1 message = 1 cacheable block
        SystemMessage(content="\n\n".join(volatile_fragments)),
    ]

def _build_cacheable_fragments(state: AgentState) -> list[str]:
    return [
        _static_identity(),
        _tools_hint(state.active_tools),
        _sales_playbook_hint(),
        _agent_identity_lighthouse(state),  # uses brand_voice_summary cache
        _offer_summary(state),
        _channel_format_hint(state),
    ]
```

### PromptVersionModel override

Si `PromptLoader.get(key="sales_specialist_qualifier", tenant_id=X)` devuelve override → inyectar en slot **7** (volatile, post-cache_boundary). Razón: overrides son raros pero específicos al tenant; mezclarlos en cacheable rompe la hit rate per turn.

Excepción: override del campo `agent_identity` → va en slot 4 (lighthouse) — ese override SÍ es cacheable.

### Anti-patrones a evitar

- Insertar `state.current_state` en slot 1-6 (rompe cache).
- Usar `datetime.now()` o `f"timestamp: {now}"` en cacheable.
- Concatenar cacheable+volatile en single SystemMessage (rompe boundary detection del provider).

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/prompts/test_compose_system_prompt.py`:
   - Output = exactamente 2 SystemMessages.
   - Cacheable fragments en orden 1-6.
   - Volatile fragments en orden 7-10.
   - State volátil cambia → cacheable bytes idénticos.
   - State volátil cambia → volatile bytes diferentes.

2. `tests/modules/sales_agent/prompts/test_no_volatile_in_cacheable.py`:
   - Cacheable fragments NO contienen `current_state`, `lead_score`, mensajes recientes, timestamps.

3. `tests/modules/sales_agent/prompts/test_prompt_version_override_placement.py`:
   - Override de `agent_identity` → slot 4.
   - Override de `qualifier_skill_prompt` → slot 7.

4. `tests/architecture/test_sales_agent_system_prompt_order.py`:
   - Mirror de `test_system_prompt_order.py` de copilot.
   - Falla si alguien reordena slots.

5. `tests/modules/sales_agent/prompts/test_cache_prefix_size.py`:
   - Prefix cacheable rendered tenant-fixture ≥1024 tokens (use `tiktoken` count).

---

## Implementación step-by-step

1. Crear `application/prompts/compose.py` con `compose_system_prompt`.
2. Implementar fragment builders (`_static_identity`, etc.). Reusar Jinja para los que ya existen — solo split.
3. Refactor specialists `nodes.py` para usar `compose_system_prompt(state)` en vez de Jinja render directo.
4. Test cache prefix size con tenant fixture real.
5. Deploy dev environment + medir 24h con tenant test → verificar `cached_read_tokens` populado.
6. Verificar quality (no regresiones en goldens existentes).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Cache hit rate <60% en producción | Investigar slot que rompe contiguidad. Probable culprit: tenant config volátil filtrándose en cacheable. |
| Reordering rompe goldens | Re-generar goldens con `UPDATE_GOLDEN=1` solo si cambio intencional. |
| Provider X (Anthropic) no soporta 2 SystemMessages | Verificar en research. Workaround: 1 SystemMessage con `cache_control` block (Anthropic-specific). |
| PromptVersionModel override pone override en slot equivocado → break cache | Test específico cubre placement. |

---

## Tech debt watchpoints

- Si Jinja templates `specialist_*.j2` tienen lógica condicional volátil (ej: `{% if buying_signals %}`) → extraer al fragment volatile correspondiente.
- Si specialist nodes tienen `system_prompt = f"..."` con state interpolado → refactor obligatorio.
- Si `agent_identity` se renderiza fresh per turn aunque tenant no cambió Brand Studio → cache miss garantizado. Loggear como dependencia para S7.

---

## Ajustes vs plan original

> COMPLETAR.
