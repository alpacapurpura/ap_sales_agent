# TP4 — Ask Tenant Data Subgraph (F5)

**F# que valida:** F5 (`ask_tenant_data` tool: intent → query_builder → executor → state_check → synthesize, **1 NANO + 1 FAST LLM calls** post F8 hook activado).
**Tiempo estimado:** 3-4 hs.
**Pre-req hard:** TP0 + tenant test con data poblada en CRM (leads), Offer (productos `products` table) + multi-provider router habilitado (Sprint 0 commits `9d63c0da` + `ae30d4f9`).

**Post sanity-check 2026-04-26:** intent_classifier ahora invoca `ModelRole.NANO` (no FAST) — F8 hook activado en `intent_classifier.py:127`. Provider routing TP4 esperado: ambos calls (intent NANO + synth FAST) → OpenAI gpt-4o-mini. Si el `ask_tenant_data` se ejecuta dentro del subagent `data_query`, el main loop AGENT corre Kimi K2.6 (el subagent hereda la tool con sus 2 internal LLM calls intactos).

**Tenant test post seed 2026-04-26:** Visionarias `6347e21e-8112-4aa1-80d3-6adaa73bf6f9`. Counts:
- leads totales: 15 / últimos 7d: 8 / últimos 30d: 15
- products active: 7 (catálogo Visionarias coaching/mentoring) / total no-deleted: 12
- enrollments: 4 (3 paid PEN 197 + 1 pending)
- brand_summary: 0 rows (TP4 no requiere lighthouse — F5 no consume brand)

`alpaca-2` (`c67c9845`) heredado TP3 sin productos/leads — usable como tenant "fresco sin data" para S4.4.

## Setup multi-provider (Sprint 0 obligatorio)

`.env` mínimo para correr TP4 con la arquitectura post-Sprint 0:

```bash
# OpenAI (NANO/FAST/VISION/EMBEDDING — UX-crítico TTFB LATAM)
OPENAI_API_KEY=sk-...

# DeepSeek (REASONING — main deep_agent + ask_tenant_data synthesizer + intent_classifier)
DEEPSEEK_API_KEY=sk-...
AI_PROVIDER_REASONING=deepseek
AI_MODEL_REASONING=deepseek-reasoner

# Kimi / Moonshot (AGENT — deepagents harness + subagentes data_query)
KIMI_API_KEY=sk-...
AI_PROVIDER_AGENT=kimi
AI_MODEL_AGENT=kimi-k2-6

# Qwen / DashScope intl (integrado pero default OFF; flip on-demand)
DASHSCOPE_API_KEY=sk-...
# AI_PROVIDER_VISION=qwen        # opt-in
# AI_MODEL_VISION=qwen-vl-max
# AI_PROVIDER_EMBEDDING=qwen     # opt-in
# AI_MODEL_EMBEDDING=text-embedding-v3
```

Verificar boot pre-TP4:
```bash
cd backend && .venv/bin/python -c "
from src.shared.infrastructure.llm.factory import LLMFactory
from src.core.enums import ModelRole
r = LLMFactory.get_service()
for role in ModelRole:
    print(role.name, '→', r.get_provider_for_role(role).value)
"
```
Output esperado: `NANO → openai`, `FAST → openai`, `REASONING → deepseek`, `AGENT → kimi`, `VISION → openai`, `EMBEDDING → openai`.

---

## Misión

El "salto cualitativo grande" del redesign (F5 learnings). Confirmar que:

1. Preguntas naturales sobre datos del tenant devuelven respuesta correcta (NO SQL crudo en prompt).
2. El subgraph resuelve fuzzy matching ("la oferta de propósito" → "Programa: De Propósito a Prosperidad" via pg_trgm) + fechas relativas ("esta semana").
3. State-check intercepta cuando data falta + responde correctamente ("no encontré nadie en esa ventana") via short-circuit `empty_window` (sin LLM call).
4. Latencia ≤2.5s p50 (subgraph deterministic + 1 NANO intent + 1 FAST synth, ambos OpenAI; bumped from 1.5s post Sprint 0 LATAM TTFB realistic).
5. NO alucina números (DeepEval `FaithfulnessMetric` ≥0.85 avg).
6. Provider routing per-role correcto vía `copilot_trace_event.data->>'model'` (Sprint 0 gate).

---

## Research mandate

Queries:

- `"text to SQL agent evaluation 2026 fuzzy matching benchmark"` — patrones de eval para Q&A sobre data.
- `"deepagents text-to-sql-agent example 2026"` — confirmar pattern sigue siendo el actual de la lib.
- `"natural language data query LLM hallucination groundedness 2026"` — métricas para detectar alucinaciones de números.

---

## Scenarios

### S4.1 — Pregunta canónica fácil

`"cuántas personas me escribieron esta semana"`.

Trace expected:
- 1 `tool_call` `name='ask_tenant_data'` (visible via `copilot_trace_event`).
- Internal: 1 `llm_call` NANO (intent_classifier) + 1 `llm_call` FAST (synthesizer). Ambos con tag `copilot:internal` (TP3 B1).
- `assistant_text` con número correcto.

Ground truth (Visionarias post seed):
```sql
-- Note: F5 lead_count usa last_interaction_date, NOT created_at
SELECT COUNT(*) FROM leads
WHERE tenant_id='6347e21e-8112-4aa1-80d3-6adaa73bf6f9'
  AND last_interaction_date >= NOW() - INTERVAL '7 days';
-- Expected: 8 (post seed 2026-04-26)
```

**Pass:** assistant_text reporta "8" (o equivalente NL) ±0.

### S4.2 — Fuzzy matching producto

Catálogo real Visionarias (`products` table):
- "Programa: De Propósito a Prosperidad" (active)
- "Programa de Proposito a Prosperidad" (draft, sin tilde — duplicado real)
- "Mentoría Privada: Visión Clara" (active)
- "Círculo Visionarias Elite" (active)
- "Pack Meditaciones: Abundancia" (active)
- "Retiro Visionarias: Tulum 2026" (active)
- "Agencia Visionarias DFY" (active)
- "Visionarias Corporate Leadership" (draft)
- "Diseña tu 2026" (draft, ×2 duplicado)
- "Guía: Liberar la Mente" (active)
- "Nuevo producto" (draft)

Pregunta TP4: `"dame un resumen del programa de propósito"`.

**Pass:** subgraph matchea "Programa: De Propósito a Prosperidad" (active preferido) o ambos duplicados; NO matchea "Mentoría" ni "Tulum". Validar via `copilot_trace_event.data->'rows'` o `metadata.matched_name`.

### S4.3 — Fechas relativas

Set de prompts:
- `"cuántas personas me escribieron en los últimos 30 días"` → period -30d→now. Ground truth: 15.
- `"cuántas conversaciones tuve en los últimos 30 días"` (kind=conversation_count) → 30d window. Ground truth: 45 (copilot_conversations).
- `"cuántas personas me hablaron por whatsapp esta semana"` → channel filter `whatsapp` + 7d. Ground truth: 7.

**Pass:** subgraph parsea fechas correctamente. Verificar via `data->'plan'->'filters'->'since'/'until'` en trace.

### S4.4 — State-check: no data (short-circuit empty_window)

Tenant `alpaca-2` (`c67c9845-6cf7-4aee-beba-7e177e84d167`) — heredado TP3, 0 leads. Question: `"cuántas personas me escribieron esta semana"`.

**Pass:**
- intent → `lead_count` con period_phrase="esta semana".
- query_builder pone `since/until` → has_window True.
- executor returns count=0.
- state_check sets `empty_window=True`.
- synthesizer **short-circuit estático** (NO LLM call): respuesta estilo "No encontré ningún registro en esa ventana de tiempo. Si querés, probemos con un período más amplio." Validar que `copilot_trace_event` muestra **1 llm_call (intent NANO) + 0 llm_call (synth)** para este turn.

### S4.5 — Kind unsupported (graceful degradation)

`"cuáles son mis 3 ofertas top por inscripciones"` — F5 actual NO tiene kind cross-tabla ranking (`SUPPORTED_KINDS = {offer_lookup, lead_count, conversation_count}`).

**Pass:** intent_classifier devuelve `kind="unknown"` con confidence baja → `build_plan` returns None → synthesizer short-circuit `_unknown_intent_reply` ("No entendí del todo la pregunta. ¿Podés reformularla con otras palabras?"). Trace muestra **0 LLM call al synthesizer** (short-circuit).

> Nota arquitectónica: si TP4 evidencia que esta pregunta es común, agregar a `SUPPORTED_KINDS` un kind `offer_ranking_by_enrollments` + accessor en `OfferDataAccessProvider` es F-pos legítimo. NO hacerlo en TP4 (scope creep).

### S4.6 — Alucinación check

`"cuántas ventas hice en marzo de 2025"` (período sin data).

**Pass:** "no tengo data de ese período" en lugar de "tuviste 47 ventas" inventado.

DeepEval `FaithfulnessMetric` over response vs DB ground truth.

### S4.7 — Latencia subgraph

10 preguntas variadas (S4.1-S4.6). Medir:

```sql
SELECT AVG(duration_ms), PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms),
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)
FROM copilot_trace_event
WHERE event_type='tool_call' AND name='ask_tenant_data'
  AND created_at >= NOW() - INTERVAL '15 minutes';
```

**Pass:** p50 ≤1500ms, p95 ≤4000ms.

### S4.8 — DeepEval `FaithfulnessMetric` cross-scenarios

Para los 10 prompts de S4.7, capturar `assistant_text` + ground truth SQL + correr:

```python
metric = FaithfulnessMetric(threshold=0.85)
case = LLMTestCase(
    input=prompt,
    actual_output=assistant_text,
    retrieval_context=[ground_truth_summary],
)
assert_test(case, [metric])
```

**Pass:** ≥9/10 above threshold.

### S4.9 — Tool args sin SQL crudo

```sql
SELECT data->'args' FROM copilot_trace_event
WHERE name='ask_tenant_data' AND turn_id IN (...);
```

**Pass:** args contienen campos NL natural (`question`, `period`, `entity`) NUNCA strings SQL.

---

## Tools / queries

- DeepEval: `tests/quality/deepeval/test_tp4_ask_tenant_data.py`.
- SQL probes a `crm_leads`, `offers`, `enrollments` para ground truth.
- `copilot_trace_event` para subgraph internal nodes.

---

## Targets (post Sprint 0 multi-provider)

| Métrica | Target | Hard fail | Nota |
|---|---|---|---|
| Respuesta correcta sin alucinar | ≥9/10 | <8/10 | — |
| Fuzzy matching | matchea correcto | mismatch | — |
| Subgraph latencia p50 | ≤2500ms | >5000ms | bumped from 1500ms — DeepSeek REASONING from LATAM adds ~+300-700ms TTFB vs OpenAI baseline; aceptable para data Q&A no-UX-crítica. Si OpenAI baseline existía y mostraba <1500ms, comparar y reportar diff. |
| Subgraph latencia p95 | ≤5000ms | >8000ms | — |
| FaithfulnessMetric | ≥0.85 avg | <0.70 | DeepSeek-reasoner debería igualar o mejorar GPT-4o en groundedness por design (chain-of-thought explícito). |
| Cost / turn ask_tenant_data | ≤$0.0008 p50 | >$0.005 | bajado ~85% vs all-OpenAI baseline. DeepSeek $0.55/$2.19 per M (cache 90%) → ~$0.0005-0.0010 per intent+synth combo. |
| Tool args sin SQL crudo | 100% | 1+ con SQL | — |
| State-check intercepta empty | OK | inventa número | — |
| Provider routing per-role correcto | trace muestra calls a deepseek + kimi | OpenAI en REASONING/AGENT | nuevo gate post Sprint 0. Verificar via `copilot_trace_event.data->>'model'` ó `data->>'provider'`. |
| Judge parity vs OpenAI baseline | ≤0.3 puntos diff | >0.5 abajo | si baseline F0 tiene scores OpenAI puro, comparar. Si DeepSeek/Kimi caen >0.5 → revertir el role afectado a OpenAI. |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Alucinación números | groundedness | trace executor.output | LLM ignoró state_check, prompt synthesizer falló |
| Fuzzy mismatch | resolver entity | query_builder logs | bumpear similarity threshold o rule |
| Latencia >5s | network OpenAI o subgraph mal optimizado | trace per-node duration | revisar 2-call FAST budget |
| SQL en args | violation contract | tool docstring + LLM prompt | refinar tool description prohibiendo SQL |
| Fecha relativa wrong | parser dates | `application/tools/ask_tenant_data/date_parser.py` | unit test path edge cases |

---

## Lo que necesito de Chris

- [ ] Tenant test con CRM populated (≥10 leads, mix de fechas últimos 30d).
- [ ] Tenant test con ≥3 ofertas distintas (para S4.2 fuzzy).
- [ ] Tenant test con ≥5 enrollments cross-offers (para S4.5).
- [ ] Confirmar `ChannelConnection` con webhooks activos si querés validar S4.1 vs Manychat real.
- [ ] **DeepSeek API key** (https://platform.deepseek.com/api_keys) en `DEEPSEEK_API_KEY`.
- [ ] **Kimi/Moonshot API key** (https://platform.moonshot.ai/console/api-keys) en `KIMI_API_KEY`.
- [ ] **OpenAI recargado** (NANO/FAST/Whisper/embeddings siguen OpenAI).
- [ ] (opt) **DashScope intl key** (https://bailian.console.alibabacloud.com/) en `DASHSCOPE_API_KEY` para flips Qwen on-demand.
