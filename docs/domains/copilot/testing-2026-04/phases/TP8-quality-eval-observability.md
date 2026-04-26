# TP8 — Quality Eval + Observability (F9 + F11.5)

**F# que valida:** F9 (`CopilotJudge` + 20 goldens + `copilot_workflow_metric` + ARQ `weekly_copilot_quality_eval` + `node_enter`/`node_exit` + admin `/copilot-quality`) + F11.5 (RAG eval extiende este sistema).
**Tiempo estimado:** 1-2 hs.
**Pre-req hard:** TP0 + TP1 + TP7.

---

## Misión

Confirmar que la capa de quality + observability funciona end-to-end:

1. Manual run de `weekly_copilot_quality_eval` produce rows en `copilot_workflow_metric`.
2. CopilotJudge multi-dim devuelve scores coherentes (no todos 0 ni todos 5).
3. `node_enter`/`node_exit` emiten en cada turn → trace timeline reconstruible.
4. Admin `/copilot-quality` muestra KPIs + sección RAG retrieval (F11.5).
5. Re-run del judge sobre las mismas conversaciones produce scores estables (judge consistency).

---

## Research mandate

Queries:

- `"llm judge consistency reliability cronbach alpha 2026"` — confirmar metodología validation del judge.
- `"agent observability node trace langgraph 2026 patterns"` — validar `node_enter`/`node_exit` sigue siendo state-of-the-art.
- `"continuous evaluation production llm regression 2026"` — patrones para weekly eval + alerting.

---

## Scenarios

### S8.1 — Manual weekly_copilot_quality_eval

```bash
docker exec visionarias_brain_dev .venv/bin/python -c "
from src.shared.workers.copilot_quality_eval import run_weekly_quality_eval
from src.core.database import SessionLocal
db = SessionLocal()
n = run_weekly_quality_eval(db)
print(f'rows: {n}')
"
```

```sql
SELECT tenant_id, workflow_id, judge_avg_score, judge_sample_size, jsonb_pretty(extra_metadata)
FROM copilot_workflow_metric WHERE period_start >= NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;
```

**Pass:** ≥1 row written. judge_sample_size matches conversations en 7d.

### S8.2 — CopilotJudge consistency (re-run estable)

Mismas 5 conversaciones, judge corrido 3 veces:

```python
from src.modules.copilot.application.observability.judge import CopilotJudge
import os
os.environ['RUN_LLM_JUDGE'] = '1'
judge = CopilotJudge()
scores = []
for _ in range(3):
    score = judge.evaluate(user_input=user_msg, assistant_output=ai_msg)
    scores.append(score.avg_score)
print(f'mean={sum(scores)/3:.2f} stddev={pstdev(scores):.2f}')
```

**Pass:** stddev <0.5 across 3 runs. Si >1.0 → judge inestable (revisar `temperature=0` + `seed=42`).

### S8.3 — node_enter / node_exit emiten

Turn nuevo. Trace probe:

```sql
SELECT event_type, name, COUNT(*)
FROM copilot_trace_event WHERE turn_id=:tid AND event_type IN ('node_enter','node_exit')
GROUP BY event_type, name ORDER BY name;
```

**Pass:** ≥4 entries (deep_agent default nodes). En tareas multi-step ≥10.

### S8.4 — Trace timeline reconstruction

Conv con tarea multi-step. Probe:

```sql
SELECT event_type, name, status, duration_ms, parent_span_id, span_id
FROM copilot_trace_event WHERE turn_id=:tid
ORDER BY created_at;
```

**Pass:** Tree reconstruible (parent_span_id → span_id chain coherente). 1 turn_start + 1 turn_end + N llm_call/tool_call/card_emitted/node_*.

### S8.5 — Admin `/copilot-quality` muestra data

Después de S8.1 + S7.6 (TP7 weekly_rag_eval):

Browser to `http://localhost:8502/copilot-quality`:
- KPI cards muestran ≥1 workflow.
- Tabla "Últimas métricas semanales" con rows.
- Tab/section "RAG retrieval" con recall + latencia + judge dims.
- Tab "Eventos de traza" muestra breakdown por event_type.

Screenshot.

**Pass:** las 4 secciones populadas (no empty-state).

### S8.6 — Cost guard del judge

Per F9 docstring: cost_guard = 6_000 calls/month ≈ $0.024.

Real run: medir tokens del judge call:
```sql
SELECT data->>'tokens_total', data->>'model' FROM copilot_trace_event
WHERE event_type='llm_call' AND data->>'caller'='CopilotJudge'
ORDER BY created_at DESC LIMIT 5;
```

**Pass:** avg tokens ≤500 per call. Cost projection mensual ≤$0.05.

### S8.7 — Edge case: judge raises → result devuelto, no crash

Mock LLM que raise exception. Run judge.

**Pass:** `JudgeResult.passes_threshold=False` con `metadata.error` populated, NO exception bubbleada.

### S8.8 — Goldens 20 conversaciones (F9 baseline)

```bash
RUN_LLM_JUDGE=1 .venv/bin/pytest tests/quality/golden/test_golden_conversations_semantic.py -v -o addopts=""
```

**Pass:** 20/20 sobre el threshold (3.5).

---

## Tools / queries

- DeepEval no aplica directamente acá (este TP testea el judge interno + observability).
- SQL probes a `copilot_workflow_metric`, `copilot_trace_event`.
- Admin Streamlit `/copilot-quality`, `/trazas`.

---

## Targets

| Métrica | Target | Hard fail |
|---|---|---|
| weekly_quality_eval rows | ≥1 | 0 |
| Judge consistency stddev | <0.5 | >1.0 |
| node_enter/exit per turn | ≥4 | 0 |
| Timeline reconstruible | OK | broken span tree |
| Admin /copilot-quality populated | 4 sections OK | 1+ empty |
| Judge cost mensual proyectado | ≤$0.05 | >$0.50 |
| Goldens 20 pass | 20/20 | <19 |

---

## Failure playbook

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| 0 rows weekly run | sample empty | `_sample_recent_conversations` window | check `WINDOW_DAYS=7` + tenant has conv en ventana |
| Judge inestable | seed/temperature ignored | `CopilotJudge._invoke` LLM params | confirmar `temperature=0, seed=42` se pasa |
| node_enter missing | astream_events filter | `node_trace.py::emit_node_trace_event` | check `metadata.langgraph_node` filter |
| Span tree broken | parent_span_id wrong | `trace_recorder.py::_build_span` | unit test span chain |
| Admin section empty con data | query SQL en module | `_fetch_workflow_kpis` SQL | revisar WHERE clause |

---

## Lo que necesito de Chris

- [ ] Confirmar `RUN_LLM_JUDGE=1` se puede setear en tu env (sino S8.2 falla).
- [ ] (Opcional) si hay alerting wired (Sentry?) para judge avg <3.5 — sino nota como recommendation.
