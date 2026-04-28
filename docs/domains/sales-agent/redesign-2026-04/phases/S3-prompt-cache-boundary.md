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

### Hallazgos research (2026-04-28)

#### OpenAI prompt cache (vigente abril 2026)
- Threshold mínimo **1024 tokens contiguos sin cambios** confirmado vigente. Por debajo, no hay cache (no degradado gradual).
- **Automático, sin annotations**. No `cache_control`, no `cache_breakpoint`. Solo dejar prefix estable.
- Telemetría: `usage_metadata.input_token_details.cache_read` (LangChain normaliza). Latencia −80% / cost −90% al hit.
- Optional: `prompt_cache_key` (routing hint para mejorar hit rate cuando hay múltiples replicas backend) y `prompt_cache_retention` (`in_memory` 5-10 min default vs `24h` extended).
- Fuente: [OpenAI Prompt Caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Cookbook 201](https://developers.openai.com/cookbook/examples/prompt_caching_201).

#### Anthropic Claude (NO en scope S3 — sales_agent hoy no enruta a Claude)
- Requiere `cache_control: {"type": "ephemeral"}` explícito en blocks.
- Cache write 1.25× input price (5 min TTL) o 2.0× (1 h TTL). Cache read 0.1× input.
- TTL default cambió a **5 minutos** (2026-03-06); 1 h es opt-in pago.
- Multi-message cacheable: cachea hasta el último block con `cache_control`; siguientes requests reusan prefix.
- **LangGraph v1.0** `create_agent` solo acepta `str` para `system_prompt` → incompatible con `cache_control` Anthropic. Workaround: pasar `SystemMessage(content=[blocks])` direct al LLM (no `create_agent`).
- Fuente: [Claude Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [LangChain Issue #33635](https://github.com/langchain-ai/langchain/issues/33635).

#### Kimi K2.6 (modelo target S4 AGENT role)
- API **OpenAI-compatible** confirmada (`/v1/chat/completions`). 256K context, 1T params (32B active).
- **Automatic prefix caching** confirmado, savings 75-83%. Input ~$0.60/M base, drops a $0.10-0.15/M con cache hit.
- Reusa el mismo pattern que OpenAI (string prefix estable). NO requiere annotations.
- Fuente: [Kimi K2.6 API Guide](https://help.apiyi.com/en/kimi-k2-6-api-integration-guide-en.html), [Kimi Platform Docs](https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart).

#### DeepSeek V3/V4 (modelo target S4 REASONING role para objeciones)
- **Disk-based context cache automático**, default-on, sin code changes.
- Telemetría tipada: `usage.prompt_cache_hit_tokens` / `usage.prompt_cache_miss_tokens` (no es el shape OpenAI `cached_tokens`; LangChain normaliza para que ambos lleguen a `input_token_details.cache_read`, pero verificar en producción).
- Storage units 64 tokens, best-effort. V4 1M context / 384K output max.
- Pricing 2026-04: input cache hits a 1/10 de original launch price; V4-Pro 25% off hasta 2026-05-05.
- Fuente: [DeepSeek Context Caching](https://api-docs.deepseek.com/guides/kv_cache), [V4 Caching Blog](https://wavespeed.ai/blog/posts/blog-deepseek-v4-context-caching/).

#### LangChain SystemMessage cache compatibility
- Para OpenAI/Kimi/DeepSeek (auto-cache): pattern correcto = **single string** con prefix estable. No requiere `cache_control`.
- Para Anthropic (manual): `SystemMessage(content=[{"type":"text","text":..., "cache_control":{"type":"ephemeral"}}, {"type":"text","text":...}])`. Multi-block dentro de **un solo SystemMessage**, no múltiples `SystemMessage`.
- LangGraph v1.0 `create_agent` solo string → si sales adopta create_agent en futuro, perdería cache_control Anthropic. Hoy `LLMFactory.generate_response(system_prompt=str)` es nuestro pattern → fits OpenAI/Kimi/DeepSeek perfecto.

---

## Ajustes vs plan original

**Original (S3 doc pre-research):** `compose_system_prompt(state) -> list[SystemMessage]` con 2 SystemMessages separados (cacheable + volatile).

**Ajustado:** `compose_system_prompt(fragments) -> str` mirror exacto del pattern F8 copilot (`backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py`):
- Single string con `CACHE_BOUNDARY_MARKER = "\n\n<!-- ==== CACHE BOUNDARY (S3) ==== -->\n\n"` insertado entre prefix cacheable y suffix volatile.
- Marker es greppable en trace (LLM lo ignora — HTML comment en markdown).
- `PromptFragment(StrEnum)` + `CACHEABLE_FRAGMENTS` tuple + `VOLATILE_FRAGMENTS` tuple = SSoT del orden.
- Compatible con `LLMFactory.generate_response(system_prompt: str, ...)` actual sin cambiar el contract.

**Razones del ajuste:**
1. **OpenAI/Kimi/DeepSeek son auto-cache** — no requieren múltiples SystemMessages. El cache se activa solo por prefix estable ≥1024 tokens.
2. **Single string es el pattern probado en producción copilot F8** — hit rate ya verificable en `copilot_routing` admin.
3. **List[SystemMessage] complica el contract** — hoy `LLMFactory.generate_response` acepta `system_prompt: str`. Cambiar a list rompería ~9 callsites en sales_agent + el contract con shared/infrastructure/llm.
4. **Para Anthropic (futuro post-S4 si enrutamos)** — el adapter local del provider puede splittear el string por marker y emitir blocks con `cache_control`. La SSoT del orden queda en compose.py independiente del provider.

**Consecuencias:**
- Tests originalmente "Output = exactamente 2 SystemMessages" → cambian a "Output contiene exactamente 1 CACHE_BOUNDARY_MARKER, prefix antes ≥1024 tokens".
- Slot 4 (`agent_identity_lighthouse`) hoy se rinde fresh per turn desde `tenant_config` (PromptLoader cachea 60s) — para S3 no migramos a `brand_voice_summary` table (eso es S7); en S3 garantizamos que el render NO incluya state-dependent vars (no `lead_score`, no `current_state`, no `recent_messages`). Si `tenant_config` cambia raro entre turns (lo esperado), prefix queda estable.
- PromptVersionModel override slot placement: identity overrides → slot 4 (cacheable per-tenant); skill overrides (qualifier/closer/product_expert) → slot 4-6 cacheable per-tenant si todo el specialist body NO depende de state, o slot 7+ volatile si tiene `{{ buying_signals }}` etc. Tests cubren ambos casos.

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

### Implementación (mirror F8 copilot)

```python
# src/modules/sales_agent/application/prompts/compose.py
from collections.abc import Mapping
from enum import StrEnum

class PromptFragment(StrEnum):
    # Cacheable prefix (≥1024 tokens contiguos)
    STATIC_IDENTITY       = "static_identity"
    STATIC_TOOLS_HINT     = "static_tools_hint"
    SALES_PLAYBOOK_HINT   = "sales_playbook_hint"
    AGENT_IDENTITY        = "agent_identity"          # per-tenant, S7 promovería a lighthouse cached
    OFFER_SUMMARY         = "offer_summary"
    CHANNEL_FORMAT_HINT   = "channel_format_hint"
    # Volatile tail (cambia per-turn)
    STAGE_HINT            = "stage_hint"
    LEAD_SIGNALS          = "lead_signals"
    RECENT_MESSAGES       = "recent_messages"
    TOOL_REQUEST_FORMAT   = "tool_request_format"

CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.SALES_PLAYBOOK_HINT,
    PromptFragment.AGENT_IDENTITY,
    PromptFragment.OFFER_SUMMARY,
    PromptFragment.CHANNEL_FORMAT_HINT,
)

VOLATILE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STAGE_HINT,
    PromptFragment.LEAD_SIGNALS,
    PromptFragment.RECENT_MESSAGES,
    PromptFragment.TOOL_REQUEST_FORMAT,
)

CACHE_BOUNDARY_MARKER = "\n\n<!-- ==== CACHE BOUNDARY (S3) ==== -->\n\n"

def compose_system_prompt(fragments: Mapping[PromptFragment, str]) -> str:
    """Pure data assembler. State + Jinja resolution viven afuera."""
    cache_parts = _take(fragments, CACHEABLE_FRAGMENTS)
    volatile_parts = _take(fragments, VOLATILE_FRAGMENTS)
    if not cache_parts and not volatile_parts:
        return ""
    if not volatile_parts:
        return "\n\n".join(cache_parts)
    if not cache_parts:
        return "\n\n".join(volatile_parts)
    return "\n\n".join(cache_parts) + CACHE_BOUNDARY_MARKER + "\n\n".join(volatile_parts)
```

Wrapper alto-nivel `build_specialist_system_prompt(state, role: SpecialistRole) -> str` resuelve cada fragment desde state + PromptLoader + tenant_config y llama a `compose_system_prompt`.

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
