# TP0 — Baseline + Observability + Tooling Setup

**F# que valida:** ninguno directamente. Habilitador para TP1-TP11.
**Tiempo estimado:** 30-60 min.
**Pre-req hard:** branch `development`, containers up, tenant test creado.

---

## Misión

Dejar listo el harness de testing antes de tocar cualquier escenario funcional:

1. DeepEval instalado + smoke test pasa.
2. Chrome DevTools MCP responde + screenshot smoke OK.
3. Admin Streamlit `/trazas`, `/copilot-routing`, `/copilot-quality`, `/marketing-kb` abren sin 500.
4. Snapshot baseline de métricas observadas hoy en producción dev (cost, latencia, judge avg) para comparar contra TPs siguientes.
5. Dataset baseline: 5 conversaciones hand-crafted que cubren los flujos canónicos (chat short, audit, design, ask data, RAG query) — usadas como golden cross-TP.

---

## Research mandate (paso 2 protocolo)

Queries OBLIGATORIAS (mínimo 2):

- `"deepeval pytest setup 2026 best practices"` — confirmar API + config actual.
- `"deepeval gpt-4o-mini judge model environment variable"` — confirmar nombre exacto del env var.
- `"openai api pricing nano mini opus 2026 latest"` — pricing snapshot para `03-metrics-and-targets.md §Cost estimation`.

Si pricing cambió desde abril 2026, **bumpear la tabla** en `03-metrics-and-targets.md` antes de cualquier cálculo de TP siguiente.

---

## Scenarios

### S0.1 — DeepEval install + smoke

```bash
cd backend && .venv/bin/pip install deepeval
.venv/bin/python -c "from deepeval import assert_test; from deepeval.test_case import LLMTestCase; from deepeval.metrics import GEval; print('ok')"
```

Crear `backend/tests/quality/deepeval/test_smoke.py`:

```python
import os
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval

os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"

def test_smoke_geval_runs():
    case = LLMTestCase(
        input="What is 2+2?",
        actual_output="4",
        expected_output="4",
    )
    metric = GEval(
        name="correctness",
        evaluation_steps=["Output must contain '4' as the answer."],
        evaluation_params=["actual_output", "expected_output"],
        threshold=0.5,
    )
    assert_test(case, [metric])
```

Run: `cd backend && .venv/bin/pytest tests/quality/deepeval/test_smoke.py -v -o addopts=""`.

**Pass criteria:** 1 passed. Si requiere OPENAI_API_KEY y no lo tenemos en el venv, documentar el setup en `01-tooling.md` (no en este TP).

### S0.2 — Chrome DevTools MCP smoke

Skill `chrome-devtools-verify` (heredada). Ejecutar:

1. `mcp__chrome-devtools__new_page` → `https://dev-app.nicolify.com`.
2. `mcp__chrome-devtools__list_console_messages` — esperado: zero errors.
3. `mcp__chrome-devtools__take_screenshot` — guardar en `/tmp/tp0-smoke.png`.
4. `mcp__chrome-devtools__close_page`.

**Pass criteria:** screenshot tomado, zero console errors, dev-app cargó.

### S0.3 — Admin Streamlit pages smoke

Browser to:
- `http://localhost:8502/trazas` → renderiza, muestra "Sin trazas todavía" o turns recientes.
- `http://localhost:8502/copilot-routing` → renderiza tabs "Distribución de tier" + "Classifier breakdown" + "Cache hit rate".
- `http://localhost:8502/copilot-quality` → renderiza KPIs + sección "RAG retrieval" (puede estar vacío post-F11).
- `http://localhost:8502/marketing-kb` → renderiza overview/search/upload/reseed tabs.

**Pass criteria:** las 4 abren sin 500. Capturar screenshots en `results/TP0-{fecha}/`.

### S0.4 — Baseline dataset (5 conv canónicas)

Crear `tests/quality/deepeval/datasets/baseline_canonical.yaml`:

```yaml
- id: chat_short
  prompt: "hola"
  expected_intent: "greeting"
  expected_tier: NANO
- id: audit_brand
  prompt: "audita mi marca completa y dame puntos de mejora"
  expected_intent: "audit"
  expected_tier: HEAVY
- id: design_offer
  prompt: "diseña una oferta nueva para mi curso de cocina"
  expected_intent: "design"
  expected_tier: REASONING
- id: ask_data
  prompt: "cuántas personas me escribieron esta semana"
  expected_intent: "ask_tenant_data"
  expected_tier: MINI
- id: rag_query
  prompt: "explícame el patrón hero/guide de StoryBrand para mi marca"
  expected_intent: "rag"
  expected_tier: MINI
  expected_kb_doc: "01_storybrand_framework.md"
```

Estos 5 son **fixtures cross-TP**. No los modifiques sin actualizar este doc.

### S0.5 — Snapshot baseline métricas pre-TPs

SQL probes contra DB local (con tenant test cargado pero sin tráfico nuevo aún):

```sql
-- Cost / latencia promedio últimos 7d (si hay tráfico previo)
SELECT
  COUNT(*) AS turns,
  AVG((data->>'total_tokens')::int) AS avg_tokens,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
  AVG((data->>'cache_hit_rate')::numeric) AS avg_cache_hit
FROM copilot_trace_event
WHERE event_type = 'turn_end' AND created_at >= NOW() - INTERVAL '7 days';

-- Judge avg último weekly run
SELECT period_start, judge_avg_score, judge_sample_size
FROM copilot_workflow_metric
ORDER BY period_start DESC LIMIT 5;
```

Snapshotear resultados en `results/TP0-baseline-{fecha}.md` para comparación cross-TP.

---

## Tools / queries

- `deepeval` CLI: `.venv/bin/deepeval` (después del install).
- `mcp__chrome-devtools__*` skill suite.
- SQL probes via `docker exec -i visionarias_postgres psql -U postgres -d visionarias_logs`.

---

## Targets

| Métrica | Target |
|---|---|
| DeepEval smoke pass | 1/1 |
| Chrome DevTools smoke | screenshot OK + 0 console errors |
| Admin pages smoke | 4/4 abren sin 500 |
| Baseline dataset committeado | `tests/quality/deepeval/datasets/baseline_canonical.yaml` existe |
| Métricas baseline snapshot | `results/TP0-baseline-{fecha}.md` con 7d stats |

---

## Failure playbook

| Síntoma | Investigar primero | Fix probable |
|---|---|---|
| DeepEval install falla con OPENAI_API_KEY missing | env vars del venv | `cd backend && cat .env \| grep OPENAI`. Si falta, documentar y NO seguir. |
| Smoke DeepEval timeout | red OpenAI o NANO mal configurado | check `core/enums.py::ModelRole.NANO` + `.env AI_MODEL_NANO` |
| Chrome DevTools "no se conecta" | bridge WSL2↔Windows | memory `feedback_chrome_devtools_verify_fe.md` |
| Admin /trazas tira 500 | Postgres down o tabla missing | `docker logs visionarias_admin_dev --tail 50` + `\dt copilot_trace_event` |
| Admin /copilot-routing vacío | F11.1 wire no llegó | confirmar commit `45f0e16e` en `git log` |

---

## Lo que necesito de Chris

- [ ] Confirmar OPENAI_API_KEY válido en `backend/.env` (sino DeepEval falla).
- [ ] Confirmar tenant de testing creado (UUID + algún brand_summary + algún offer publicado).
- [ ] Confirmar dev-app.nicolify.com tunneled OK (`curl -I https://dev-app.nicolify.com` → 200).
- [ ] Si pricing OpenAI cambió, pasar URL pricing actual.

Sin estas 4, TP0 NO arranca.
