# Métricas + Targets cuantitativos

## Tabla maestra

Targets derivados de `01-master-plan.md §"Métricas éxito globales"` + ajustes post-F11 (lo que el redesign promete debe ser superable en testing).

### Latencia

| Métrica | Source | p50 target | p95 target | Hard fail |
|---|---|---|---|---|
| TTFB (time to first SSE block) | Chrome DevTools network panel + `copilot_trace_event.duration_ms` (turn_start → primer llm_call) | ≤800ms | ≤2000ms | >5s consistente |
| Total turn latency (chat <50 chars) | `turn_end.duration_ms` | ≤1500ms | ≤4000ms | >8s |
| Total turn latency (audit/design HEAVY) | `turn_end.duration_ms` | ≤8000ms | ≤20000ms | >30s |
| `knowledge_search` tool latency | `tool_call.duration_ms` filtered name='knowledge_search' | ≤500ms | ≤1500ms | >3s |
| `ask_tenant_data` end-to-end | `tool_call.duration_ms` filtered name='ask_tenant_data' | ≤1500ms | ≤4000ms | >8s |

### Tokens + cost

> Costos calculados con catálogo OpenAI abril 2026. Ajustar si hay updates.

| Métrica | Source | Target promedio | Target p95 | Notas |
|---|---|---|---|---|
| Total tokens / turn (chat short) | `turn_end.data.total_tokens` | ≤2,500 | ≤6,000 | NANO/MINI dominantes |
| Total tokens / turn (audit/design) | `turn_end.data.total_tokens` | ≤25,000 | ≤80,000 | HEAVY con planning |
| Cache hit rate (cached_input / input) | `turn_end.data.cache_hit_rate` | ≥60% | — | post-warmup, cache prefix F8 |
| Cost USD / turn (chat) | calc: tokens × pricing | ≤$0.005 | ≤$0.015 | NANO/MINI ~$0.05/$0.15 per 1M |
| Cost USD / turn (audit/design HEAVY) | calc | ≤$0.05 | ≤$0.15 | Opus 4.7 ~$15/M input |
| Cost USD / mes proyectado (10k turns/día) | calc | ≤$300 | ≤$900 | Sin incluir embeddings KB |

### Calidad (judge multi-dim 1-5)

| Dimensión | Source | TP que mide | Target promedio | Hard fail |
|---|---|---|---|---|
| `accuracy` (factual) | CopilotJudge | TP4, TP7 | ≥4.0 | <3.0 |
| `brand_coherence` (voz tenant) | CopilotJudge | TP2, TP6, TP11 | ≥4.0 | <3.0 |
| `tone` (neutro LatAm + canal) | CopilotJudge | TP6, TP11 | ≥4.0 | <3.5 (voseo = hard fail) |
| `utility` (resuelve intent) | CopilotJudge | todos | ≥4.0 | <3.0 |
| `retrieval_relevance` | RAG goldens (TP7) | TP7 | ≥4.0 | <3.0 |
| `citation_accuracy` | RAG goldens | TP7 | ≥4.0 | <3.0 |
| `answer_groundedness` | RAG goldens | TP7 | ≥4.0 | <3.5 (alucina = hard fail) |
| `completeness` | RAG goldens | TP7 | ≥4.0 | <3.0 |

### Flujo funcional (binary pass/fail)

| Capacidad | TP | Métrica | Target |
|---|---|---|---|
| Routing log populated post-turn | TP1 | rows in `copilot_routing_log` per turn | 1:1 |
| `node_enter`/`node_exit` per turn | TP9 | trace events | ≥4 (deep_agent default nodes) |
| `card_emitted` cuando aplique | TP5, TP9 | trace events | ≥1 cuando UI muestra card |
| Brand summary inyectado | TP2 | system_prompt contiene brand_summary | 100% turns con brand_summary populated |
| URL inspiration persiste cross-turn | TP3 | turn 7 referencia inspiration de turn 2 | OK |
| Workflow completion rate | TP5 | %workflows que terminan vs abortan | ≥70% |
| Marketing KB recall | TP7 | `retrieval_recall` per golden | ≥0.8 (1.0 stub mode) |
| Channel format integrity (no markdown roto en whatsapp) | TP6 | output passes regex check | 100% |

### UX heurística (TP11)

| Heurística Claude Code | Cómo se mide | Target |
|---|---|---|
| Respuesta visible <1.5s | Chrome DevTools network + screen recording | 100% short messages |
| Plan card en multi-step | Chrome DevTools DOM snapshot | aparece ≤3s en design tasks |
| No flash-of-empty cards | DOM diff antes/después | 0 flashes |
| Markdown sin JSON crudo | DOM text scan | 0 ocurrencias |
| Console clean post-turn | DevTools console | 0 errors, ≤2 warnings |
| Memoria viva (turn 5+ recuerda turn 1) | Manual + judge | 5/5 multi-turn scenarios |
| Tono natural neutro LatAm | Manual + judge `tone` | 0 voseo, 0 robotic |
| Citation appears en RAG | DOM scan response | 100% cuando knowledge_search corrió |

### Observabilidad (binary pass/fail)

| Componente | Cómo se valida | Target |
|---|---|---|
| Admin `/trazas` | abre y muestra turns recientes | OK |
| Admin `/copilot-routing` | muestra rows de tier distribution + classifier breakdown | OK con data populated tras TP1 |
| Admin `/copilot-quality` | muestra workflow_metric rows + tab "RAG retrieval" | OK con data tras TP8 |
| Admin `/marketing-kb` | muestra stats + search QA | OK con seed corpus |

---

## Diff vs baseline

Antes de cualquier TP, ejecutar baseline en TP0 y guardar snapshot en `results/TP0-baseline-{fecha}.md`. Cada TP posterior compara contra ese snapshot:

- **Regresión latencia >20%** → root cause obligatorio.
- **Regresión calidad ≥0.5 points** → root cause + posiblemente revertir cambio.
- **Bump cost >30%** → revisar si es cache miss + warm-up.

---

## Cuándo escalar a sesión nueva

Si dentro de un TP un fail requiere fix arquitectónico que toca >3 archivos en >1 módulo, **NO lo metas en el mismo TP**. Documenta plan en `results/` + abrí nuevo TP follow-up. Razón: el TP se vuelve commit-monstruo y se pierde traceability.

---

## Cost estimation rápida

OpenAI pricing snapshot (abril 2026 — verificar antes de cada corrida):

| Tier | Modelo asumido | Input USD/1M | Cached USD/1M | Output USD/1M |
|---|---|---|---|---|
| NANO | gpt-4o-mini (placeholder) | $0.15 | $0.075 | $0.60 |
| MINI | gpt-4o (snapshot Apr 2026) | $2.50 | $1.25 | $10.00 |
| REASONING | o4-mini (placeholder) | $3.00 | $1.50 | $12.00 |
| HEAVY | opus-4.7 (1M ctx) | $15.00 | $7.50 | $75.00 |

Fórmula:
```
cost_turn = (input_tokens - cached) * input_rate / 1e6
          + cached * cached_rate / 1e6
          + output_tokens * output_rate / 1e6
```

Cada `results/TP{#}-{fecha}.md` debe reportar **cost real total** + cost por escenario.
