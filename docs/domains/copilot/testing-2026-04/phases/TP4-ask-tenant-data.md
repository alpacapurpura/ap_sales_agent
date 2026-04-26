# TP4 — Ask Tenant Data Subgraph (F5)

**F# que valida:** F5 (`ask_tenant_data` tool: intent → resolve → query → state-check → synthesize, 2 LLM calls FAST).
**Tiempo estimado:** 3-4 hs.
**Pre-req hard:** TP0 + tenant test con data poblada en CRM (leads), Offer (productos), Connections (channels).

---

## Misión

El "salto cualitativo grande" del redesign (F5 learnings). Confirmar que:

1. Preguntas naturales sobre datos del tenant devuelven respuesta correcta (NO SQL crudo en prompt).
2. El subgraph resuelve fuzzy matching ("la oferta de cocina" → product "Curso de Cocina Vegetariana") + fechas relativas ("esta semana").
3. State-check intercepta cuando data falta + responde correctamente ("no encontré leads para este período").
4. Latencia ≤1.5s p50 (subgraph deterministic + 2 LLM FAST calls).
5. NO alucina números (groundedness ≥4.5).

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
- 1 `tool_call` `name='ask_tenant_data'`.
- Subgraph internal: intent_classifier → query_builder → executor → state_check → synthesizer.
- `assistant_text` con número correcto + período correcto.

```sql
SELECT COUNT(*) FROM crm_leads
WHERE tenant_id=:uuid AND created_at >= NOW() - INTERVAL '7 days';
```

**Pass:** assistant_text matches el COUNT(*) ground truth ±0.

### S4.2 — Fuzzy matching producto

Pre-condición: ofertas:
- "Curso de Cocina Vegetariana"
- "Mentoría 1-on-1 Premium"
- "Programa Avanzado de Repostería"

`"dame resumen de la oferta de cocina"`.

**Pass:** subgraph matchea "Curso de Cocina Vegetariana" (NO "Repostería") + responde con datos correctos.

### S4.3 — Fechas relativas

Set de prompts:
- `"qué pasó este mes"` → period: current month.
- `"comparame esta semana vs la pasada"` → 2 periods.
- `"y en los últimos 30 días?"` → period: -30d to now.

**Pass:** subgraph parsea fechas correctamente. Verificar via `data->'period_start'` en trace.

### S4.4 — State-check: no data

Tenant fresco sin leads. `"cuántas personas me escribieron"`.

**Pass:** assistant_text similar a "no encontré leads en este período" (NO inventa número), trace muestra state_check returned empty.

### S4.5 — Pregunta cross-tabla

`"cuáles son mis 3 ofertas top por inscripciones"`.

**Pass:** subgraph hace JOIN offer + enrollment. Top 3 correctos (ground truth via SQL directo). Latencia ≤2s.

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

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| Respuesta correcta sin alucinar | ≥9/10 | <8/10 |
| Fuzzy matching | matchea correcto | mismatch |
| Subgraph latencia p50 | ≤1500ms | >5000ms |
| FaithfulnessMetric | ≥0.85 avg | <0.70 |
| Tool args sin SQL crudo | 100% | 1+ con SQL |
| State-check intercepta empty | OK | inventa número |

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
