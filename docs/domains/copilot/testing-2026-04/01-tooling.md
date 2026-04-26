# Tooling — Stack research-backed (abril 2026)

## Decisión final

| Tool | Rol | Por qué |
|---|---|---|
| **DeepEval** (open source, pytest-native) | Eval-as-code de escenarios + métricas multi-turn + tracking de cost/latency. | 60+ métricas built-in (G-Eval, ConversationCompleteness, ToolCorrectness, ConversationRelevancy, RAG triad). Pytest decorator `@deepeval.assert_test`. Soporta multi-turn `ConversationalTestCase`. Free, sin vendor lock. Fits `backend/tests/quality/` ya existente. |
| **Chrome DevTools MCP** (skill `chrome-devtools-verify`) | Validación UX live en `dev-app.nicolify.com` (CF tunnel local). | Reproduce flow real de user sin mock. Mide TTFB browser, captura console errors, screenshots, network panel para ver SSE frames. Skill ya configurada en el repo (heredado pre-redesign). |
| **Infraestructura interna** | Ground truth para cost/latency/quality vs targets. | `copilot_trace_event` (SSoT timeline), `copilot_routing_log` (tier + classifier), `copilot_workflow_metric` (judge avg), admin Streamlit `/trazas`+`/copilot-routing`+`/copilot-quality`+`/marketing-kb`. Ya construida en F8/F9/F10/F11. |
| **`CopilotJudge`** (in-process, F9) | Judge multi-dim para calidad de output sin SaaS dep. | NANO + 4 dims canónicos. Reusable con `dimensions=` custom para sub-rúbricas. Stub default + `RUN_LLM_JUDGE=1` opt-in. |

---

## Por qué DeepEval (research abril 2026)

Comparación documentada en `/blog/deepeval-alternatives-compared` y `/blog/promptfoo-alternatives` (Confident AI + ZenML, abril 2026):

| Tool | Pros | Contras | Veredicto Nicolify |
|---|---|---|---|
| **DeepEval** | 60+ metrics, multi-turn nativo, pytest, agent eval (`ToolCorrectnessMetric`, `TaskCompletionMetric`), free, in-process. | Curva inicial menor que LangSmith. | ✅ Elegido. |
| **Promptfoo** | YAML scenarios, CI-friendly, fácil arranque. | Recién acquired por OpenAI ($86M, vendor lock futuro). Métricas limitadas comparado a DeepEval. | ❌ Vendor risk + menos metrics. |
| **Phoenix (Arize)** | OTel-native, vendor-neutral, observability-first. | Pivot a SaaS Arize AX, eval no es foco. | ❌ Solapa con admin Streamlit interno. |
| **LangSmith** | Native LangGraph trajectory eval, integra pytest/CI. | Vendor lock LangChain, costo recurrente prod. | ❌ Existing infra cubre trajectory via `node_enter`/`node_exit` F9. |

DeepEval gana 3-0 en los criterios Nicolify: pytest-native (existing infra) + free + multi-turn first-class.

---

## DeepEval setup

Install (native venv, NUNCA docker exec):

```bash
cd backend && .venv/bin/pip install deepeval
```

> **Importante:** instalación en `requirements-dev.txt` ó `pyproject.toml` `[project.optional-dependencies] testing` — NO en runtime deps. Cualquier eval LLM usa NANO/MINI; vale la pena medir el bump de install size antes de promover a CI default.

### Config mínima

`backend/tests/quality/deepeval/conftest.py`:

```python
import os
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, ConversationalTestCase
from deepeval.metrics import (
    GEval,
    ConversationCompletenessMetric,
    ToolCorrectnessMetric,
    AnswerRelevancyMetric,
    FaithfulnessMetric,
)

# DeepEval lee OPENAI_API_KEY del env. NANO para todos los judges en CI.
os.environ.setdefault("DEEPEVAL_JUDGE_MODEL", "gpt-4o-mini")  # ajustar al NANO real catálogo
```

### Patrón eval-as-test (ejemplo TP1)

```python
def test_routing_short_msg_picks_nano(streamed_turn):
    """User msg corto sin tools → NANO tier seleccionado."""
    case = LLMTestCase(
        input="hola",
        actual_output=streamed_turn.assistant_text,
        retrieval_context=[streamed_turn.routing_decision.tier],
    )
    metric = GEval(
        name="routing_correctness",
        evaluation_steps=[
            "El tier seleccionado debe ser NANO o MINI para mensajes <50 chars sin tool calls.",
            "Penalizar si tier=HEAVY sin justificación clara.",
        ],
        evaluation_params=["actual_output", "retrieval_context"],
    )
    assert_test(case, [metric])
```

### Multi-turn (TP3, TP4, TP5)

```python
case = ConversationalTestCase(
    turns=[
        LLMTestCase(input="hola", actual_output="..."),
        LLMTestCase(input="dame una idea de campaña", actual_output="..."),
        LLMTestCase(input="ahora para WhatsApp", actual_output="..."),
    ],
    chatbot_role="Marketing copilot Nicolify"
)
metric = ConversationCompletenessMetric(threshold=0.8)
assert_test(case, [metric])
```

---

## Chrome DevTools MCP setup

Heredado: skill `chrome-devtools-verify` con bridge WSL2↔Windows ya configurado (`@dbalabka/chrome-wsl` + portproxy v4tov6 IPv6 ::1). Ver memory `feedback_chrome_devtools_verify_fe.md`.

### Flow standard por escenario UX

```
1. mcp__chrome-devtools__new_page → "https://dev-app.nicolify.com/dashboard"
2. mcp__chrome-devtools__list_console_messages (verificar zero errors antes de start)
3. mcp__chrome-devtools__performance_start_trace (label "TP{N}-scenario-{M}")
4. mcp__chrome-devtools__type_text en composer
5. mcp__chrome-devtools__click submit
6. mcp__chrome-devtools__wait_for {state: "completed", text: "done"} (SSE done event)
7. mcp__chrome-devtools__take_snapshot (DOM final)
8. mcp__chrome-devtools__list_network_requests (filter SSE) → TTFB + total duration
9. mcp__chrome-devtools__performance_stop_trace → TBT, LCP, INP
10. mcp__chrome-devtools__list_console_messages → check zero errors post
```

### Heurística UX cuando aplique (TP11 sobre todo)

- **Tiempo a primera respuesta visible** ≤ 1.5s (incluye TTFB + first block_delta render).
- **Plan card aparece** dentro de 3s para tareas multi-step.
- **Cards renderean sin parpadeo** (no flash-of-empty).
- **Markdown se sanitiza** (sin código JSON pelado en el bubble).
- **Console clean** (sin warnings React de keys, deps de hooks, etc.).

---

## Infraestructura interna — ground truth queries

### Cost / tokens por turn

```sql
SELECT
  conversation_id,
  turn_id,
  data->>'model' AS model,
  (data->>'total_tokens')::int AS tokens,
  (data->>'cached_input_tokens')::int AS cached,
  duration_ms
FROM copilot_trace_event
WHERE event_type = 'turn_end' AND conversation_id = :conv_id
ORDER BY created_at;
```

### Routing decisión por turn (F11.1)

```sql
SELECT tier_selected, classifier_used, confidence, reason, user_msg_length, tools_available
FROM copilot_routing_log
WHERE conversation_id = :conv_id
ORDER BY created_at DESC LIMIT 5;
```

### Cache hit rate p50/p95 (F8)

```sql
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (data->>'cache_hit_rate')::numeric) AS p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY (data->>'cache_hit_rate')::numeric) AS p95
FROM copilot_trace_event
WHERE event_type = 'turn_end' AND created_at >= NOW() - INTERVAL '1 hour';
```

### RAG eval row (F11.5)

```sql
SELECT period_start, started_count, judge_avg_score, jsonb_pretty(extra_metadata)
FROM copilot_workflow_metric
WHERE workflow_id = '_rag_eval'
ORDER BY period_start DESC LIMIT 1;
```

---

## Fuentes research consultadas

- [DeepEval AI Agent Evaluation Guide](https://deepeval.com/guides/guides-ai-agent-evaluation) — confirmó multi-turn `ConversationalTestCase` + `ToolCorrectnessMetric` agnóstico al provider.
- [DeepEval vs Promptfoo](https://deepeval.com/blog/deepeval-alternatives-compared) — confirmó 60+ metrics vs ~10 promptfoo + pytest-native.
- [Top 5 AI Agent Eval Tools After Promptfoo's Exit](https://dev.to/nebulagg/top-5-ai-agent-eval-tools-after-promptfoos-exit-576i) — confirmó que Promptfoo OpenAI acquisition cambia el riesgo vendor; DeepEval/Phoenix se vuelven defaults.
- [Multi-Turn LLM Evaluation in 2026 — Confident AI](https://www.confident-ai.com/blog/multi-turn-llm-evaluation-in-2026) — confirmó que multi-turn eval es mandatory en 2026 para cualquier agente conversacional.
- [Galileo — Agent Evaluation Framework 2026](https://galileo.ai/blog/agent-evaluation-framework-metrics-rubrics-benchmarks) — distinción trajectory-level vs outcome-level metrics; este plan usa AMBAS (trajectory via trace_event + outcome via judge).
- [Evaluating Deep Agents — LangChain blog](https://blog.langchain.com/evaluating-deep-agents-our-learnings/) — confirmó que LangSmith equivalente armable in-process; validó NO sumar SaaS dep.
- [LangSmith Evaluations](https://www.langchain.com/langsmith/evaluation) — referencia de "qué incluye" un platform pago: usamos como checklist, no como tool.

---

## Anti-patrones tooling

- **NO** instalar DeepEval en runtime deps (`requirements.txt`). Solo dev/test.
- **NO** correr el judge real en CI default. `RUN_LLM_JUDGE=1` opt-in (heredado patrón F9).
- **NO** mockear el LLM cuando el escenario exige medir cost/latency real (TP1 routing, TP9 deep-agent, TP11 e2e UX).
- **NO** usar Chrome DevTools MCP en CI. Solo en TPs UX (TP3/TP5/TP6/TP11) corridos manual.
- **NO** crear nueva infra observability — el redesign ya tiene `trace_event` + admin Streamlit. Cualquier query nueva va como SQL probe documentado, no nueva tabla.
