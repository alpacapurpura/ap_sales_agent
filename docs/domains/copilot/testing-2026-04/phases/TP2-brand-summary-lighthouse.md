# TP2 — Brand Summary Lighthouse (F3)

**F# que valida:** F3 (brand_summary tabla + auto-inject system prompt + event-driven regen).
**Tiempo estimado:** 1-2 hs.
**Pre-req hard:** TP0 + tenant test con `BrandIdentity` populated (mínimo: name, voice_tone, narrative).

---

## Misión

Confirmar que:

1. `brand_summary` se genera correctamente cuando un tenant tiene Brand Studio mínimo poblado.
2. El summary aparece en el system prompt de cada turn (sin que el user lo pida).
3. Las respuestas suenan coherentes con la voz/tono del tenant (judge `brand_coherence` ≥4.0).
4. Cuando se actualiza una sección de Brand, el summary regenera (event-driven F3 §5).
5. Si el tenant NO tiene brand_summary, el copilot responde sin error (graceful degradation).

---

## Research mandate

Queries:

- `"brand voice consistency LLM evaluation rubric 2026"` — best practices para juzgar voice coherence.
- `"LLM system prompt injection user-invisible context 2026 patterns"` — confirmar que el patrón "lighthouse" sigue siendo recomendado vs RAG-on-demand.
- `"prompt caching cross-tenant universal blocks 2026"` — validar que F8 puso brand summary en posición correcta dentro del cacheable prefix.

---

## Scenarios

### S2.1 — Brand summary se genera tras seed mínimo

Pre-condición: tenant test con `brand_identity` populated (`name`, `voice_tone="cálido y directo"`, `narrative` mínimo).

Trigger regen manual:
```bash
docker exec visionarias_brain_dev .venv/bin/python -c "
from src.shared.workers.brand_summary_regen import regen_brand_summary
import asyncio
asyncio.run(regen_brand_summary({'db_factory': ..., 'tenant_id': '<uuid>'}))
"
```

SQL probe:
```sql
SELECT id, summary_es, voice_tone_short, last_regen_at
FROM brand_summary WHERE tenant_id = '<uuid>';
```

**Pass:** row creada con `summary_es` no vacío + `voice_tone_short` derivado.

### S2.2 — Summary aparece en system prompt

Disparar turn vía API + capturar el system prompt construido.

```sql
-- Ver el llm_call con su prompt input
SELECT data->'input_messages'->0->>'content' AS system_prompt
FROM copilot_trace_event
WHERE event_type='llm_call' AND conversation_id=:conv_id
ORDER BY created_at LIMIT 1;
```

**Pass:** `system_prompt` contiene el `summary_es` del tenant.

### S2.3 — Brand coherence judge ≥4.0

10 prompts variados sobre el mismo tenant:

```yaml
- "dame ideas de contenido para esta semana"
- "cómo mejoro mi headline"
- "escribime un email de bienvenida para nuevos suscriptores"
- "qué tono debo usar en mi nueva landing"
- "dame 3 ideas de stories"
- "armame el copy de un anuncio Meta"
- "qué le respondo a un cliente que me dice 'está caro'"
- "cómo posiciono mi nueva oferta"
- "dame el outline de un reel viral"
- "armá un caption corto para Instagram"
```

Por cada uno, capturar `assistant_text` + correr CopilotJudge con dim `brand_coherence`:

```python
judge = CopilotJudge(dimensions=("brand_coherence",))
result = judge.evaluate(
    user_input=prompt,
    assistant_output=assistant_text,
    context=brand_summary.summary_es,
)
```

**Pass:** avg score ≥4.0 across 10. Si <3.5 en cualquiera, drilldown qué dijo el copilot vs qué decía el summary.

### S2.4 — Update sección Brand → regen

Update brand_identity via API:
```bash
curl -X PATCH /api/v1/brand/identity \
  -d '{"voice_tone": "irreverente y desafiante"}'
```

Event `brand.section_updated` debería disparar `regen_brand_summary`. Esperar 5s.

```sql
SELECT last_regen_at FROM brand_summary WHERE tenant_id=:uuid;
```

**Pass:** `last_regen_at` updated within 5s del PATCH.

### S2.5 — Tenant SIN brand_summary → graceful

Crear tenant nuevo sin brand_identity. Disparar turn:
```
"hola"
```

**Pass:** copilot responde algo coherente + sin error en `copilot_trace_event` + system prompt simplemente no incluye brand block (no exception).

### S2.6 — Lighthouse en cacheable prefix (F8 §5.2)

Verificar orden:
```python
from src.modules.copilot.application.orchestrator.system_prompt_layout import (
    compose_system_prompt, PROMPT_FRAGMENT_ORDER
)
print([f.name for f in PROMPT_FRAGMENT_ORDER])
# Esperado: ['STATIC_IDENTITY', 'TOOLS_HINT', 'MARKETING_KB_HINT', 'LIGHTHOUSE', 'EDITABLE_CATALOG', 'MODULES_LIST', ...]
```

**Pass:** `LIGHTHOUSE` aparece en posición 4 (post-F10) o 3 (pre-F10), siempre dentro del bloque cacheable (antes de CACHE_BOUNDARY_MARKER).

---

## Tools / queries

- DeepEval test: `tests/quality/deepeval/test_tp2_brand_lighthouse.py`.
- CopilotJudge in-process via `src/modules/copilot/application/observability/judge.py`.
- SQL: `brand_summary` table + `copilot_trace_event` con `event_type='llm_call'`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Brand summary auto-generado | OK post-trigger | timeout 30s |
| Summary aparece en system prompt | 100% turns | <100% (regresión) |
| Brand coherence avg | ≥4.0/5 | <3.5 |
| Regen tras update sección | ≤10s | >60s |
| Graceful sin brand_summary | OK | exception en trace |
| Lighthouse posición invariant | OK | re-orden silente |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Summary no se genera | worker no enqueueado | `register_brand_summary_event_handlers` en boot | check `WorkerSettings.on_startup` |
| Brand coherence <3.5 | summary mal generado o no inyectado | abrir `brand_summary.summary_es` + system prompt usado | drilldown qué texto recibió el LLM |
| Voice tone ignorado en respuesta | LLM no respeta brand block | compresión semántica del summary muy larga | bumpar brand_summary.compress_if_too_long |
| Update no triggers regen | event handler missing | `BrandSectionUpdatedEvent` registrado en `register_brand_summary_event_handlers` | confirmar event bus subscription |
| Lighthouse fuera del cacheable prefix | F8 reordenó sin actualizar tests | `PROMPT_FRAGMENT_ORDER` cambió | revertir o bumpear cap |

---

## Lo que necesito de Chris

- [ ] Tenant test con BrandIdentity completo (`name`, `voice_tone`, `narrative`, ideal: archetype + buyer_persona).
- [ ] (Opcional) tenant secundario con brand vacío para S2.5.
