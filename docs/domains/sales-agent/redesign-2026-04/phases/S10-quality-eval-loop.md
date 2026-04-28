# S10 · Quality eval loop (judge + goldens)

## Objetivo

Bloquear regresiones de calidad. Judge multi-rubric NANO evalúa respuestas del sales_agent en 5 dimensiones: voz de marca, eficacia comercial, ausencia de PII leak, formato canal correcto, Spanish neutro/respetando voz tenant. Goldens fijos representativos. Stub default + opt-in `RUN_LLM_JUDGE=1` real. Cron weekly mide drift y abre issue si baja >5%.

## Dependencias

- S7, S8, S9 cerrados (features completas para evaluar).
- S6 ratchet (no introducir test debt durante S10).

## Criterios de éxito

1. `tests/quality/sales_agent_goldens/` con ~20 goldens cubriendo:
   - Calificación de lead (rapport → discovery)
   - Manejo de objeciones (objection_history + closer)
   - Cierre + payment link
   - Booking link generation
   - Multi-canal (whatsapp, telegram, ig, web, sms, email)
   - Voz de marca tenant A vs B (diferenciación)
2. `SalesAgentJudge` clase en `application/quality/judge.py`:
   - 5-dim rubric, single JSON output, NANO model.
   - Modo STUB default + opt-in real.
3. Cron `weekly_sales_agent_quality_eval` ARQ lunes 06:00 UTC, opt-in via env.
4. Dashboard Streamlit `/sales-agent-quality` con histórico scores.
5. Threshold alert: si score baja >5% week-over-week → notificación admin.
6. Test arch: cada nuevo tool en sales_agent debe tener al menos 1 golden cubriéndolo (eventual cap, opt-in).
7. RAG-style goldens si aplican (eventualmente).

## Research mandate

### Queries WebSearch obligatorias

1. `LLM judge multi-rubric sales conversation evaluation 2026` — best practice.
2. `LangChain Evaluator chain BLEU ROUGE BERTScore vs LLM-judge 2026` — qué usa la industria.
3. `golden test set creation sales chatbot maintainability 2026` — tamaño + diversidad.
4. `prompt cache invariance brand voice differentiation eval` — cómo aislar variable bajo test.

### Tessl tiles

- `tessl__langchain` — Evaluator API si aplica.

### Lectura obligatoria

- Aprendizajes S7-S9.
- `backend/src/modules/copilot/application/observability/judge.py` (F9 implementación).
- `backend/tests/quality/golden/` (copilot golden patterns).
- `docs/domains/copilot/redesign-2026-04/learnings/F9-quality.md`.

### Hallazgos research

- **G-Eval (DeepEval / Confident AI 2026)** — CoT + form-filling + score 1-5 por
  dim + razón ≤80 chars baja variance del judge ~10-15% vs zero-shot. Mirror
  exacto del CopilotJudge F9: probado, alineado.
- **arXiv 2604.00022 (2026)** — eval de SDR conversacional confirma que las
  dims con mayor correlación con conversion son **Need Elicitation + Pacing
  Strategy**. Mapeo a 1 dim agregada: `commercial_effectiveness`.
- **LangSmith Evaluators vs custom (Apr 2026)** — LangSmith infra ergonomic
  pero overkill cuando ya hay event-sourced observability + pricing snapshot.
  Custom mirror del CopilotJudge da control + cero dependencias nuevas.
- **Golden test set creation 2026** — 10-20 inicial OK, escalar a 100+ cuando
  hay tenants reales con conversaciones aprobadas. S10 lanza con 20.
- **Prompt cache invariance brand voice** — research valida que routing
  `prompt_cache_key=tenant_id` (S7 SSoT) es mecanismo correcto para que el
  judge detecte diferenciación tenant A vs B con mismo input. Goldens
  `brand_voice_diff` exercitan eso (4 entries / 2 pares con mismo
  `user_input` + voces distintas).

---

## Diseño

### Rubric

```python
class SalesAgentRubric(BaseModel):
    brand_voice_fidelity: float  # 0-1, ¿suena como la marca? (slot 4 lighthouse cumplido)
    commercial_effectiveness: float  # 0-1, ¿avanza el funnel correctamente para el stage?
    pii_safety: float  # 0-1, 0 si filtró PII; 1 si limpio
    channel_format_correctness: float  # 0-1, ¿respetó max_chars + markdown_allowed + emoji_allowed?
    spanish_neutro_or_brand_voice: float  # 0-1, neutro default OR voseo si tenant lo requiere
    overall: float  # weighted avg
    rationale: str  # short
```

### Judge

```python
class SalesAgentJudge:
    async def evaluate(
        self,
        input_state: AgentState,
        actual_output: str,
        ideal_output: str | None = None,
    ) -> SalesAgentRubric:
        if os.getenv("RUN_LLM_JUDGE") != "1":
            return _stub_rubric()  # for unit tests, no LLM call
        prompt = _build_judge_prompt(...)
        response = await llm_factory.get_service(role=ModelRole.FAST).generate_structured(
            prompt=prompt, schema=SalesAgentRubric,
        )
        return response
```

### Goldens structure

```python
# tests/quality/sales_agent_goldens/test_qualification_flow.py
@pytest.mark.golden
def test_qualifier_advances_to_discovery():
    state = build_fixture_state(stage="rapport", lead_message="hola, vi tu video")
    output = run_specialist(state, specialist="qualifier")
    rubric = judge.evaluate(state, output)
    assert rubric.overall >= 0.75
    assert rubric.brand_voice_fidelity >= 0.7
```

### Cron weekly

```python
async def weekly_sales_agent_quality_eval(ctx):
    results = []
    for golden in load_goldens():
        rubric = await judge.evaluate(...)
        results.append(rubric)
    avg_score = sum(r.overall for r in results) / len(results)
    history.append(avg_score)
    if drift_detected(history, threshold=-0.05):
        alert_admin(...)
```

### Streamlit dashboard

`/sales-agent-quality`:
- Línea temporal scores avg + per-rubric.
- Filter per tenant (anonimizado).
- Drill-down a goldens individuales.

---

## Plan TDD

### RED tests

1. `tests/quality/test_sales_agent_judge_stub.py`:
   - Stub default returns deterministic rubric.
   - `RUN_LLM_JUDGE=1` invokes real LLM.

2. `tests/quality/test_golden_runner.py`:
   - 20 goldens correr standalone.
   - Average score ≥0.75 baseline.

3. `tests/quality/test_brand_voice_differentiation_goldens.py`:
   - Tenant A formal vs B casual: rubrica detecta diferencia (`brand_voice_fidelity` distinto entre fixtures).

4. `tests/architecture/test_quality_judge_no_pii_in_prompt.py`:
   - Judge prompt no incluye PII raw del input state — sanitiza primero.

5. `tests/modules/sales_agent/test_quality_dashboard_smoke.py`:
   - Streamlit page renderiza.

---

## Implementación step-by-step

1. `application/quality/judge.py` con stub default.
2. Goldens initial set (~20) cubriendo categorías clave.
3. Pytest marker `golden` + `make sales-agent-goldens` target.
4. Cron weekly task + drift detection logic.
5. Streamlit page + history table.
6. Alert mechanism (email + structlog warning).
7. Verificar `RUN_LLM_JUDGE=1` en CI weekly (opt-in).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Judge LLM falibilidad / drift | Multi-rubric + JSON schema + temperature 0. Validate consistency monthly manual. |
| Goldens caen out-of-date con cambios producto | Marca golden como "desactualizado" → review humana. |
| Cost del judge weekly | NANO + 20 goldens × 5 dims = $0.05 weekly. Negligible. |
| Stub deriva del comportamiento real | Snapshot test stub vs real cada N semanas. |

---

## Tech debt watchpoints

- Si goldens revelan bugs de fases anteriores → log as DEFERRED + documentar.
- Si judge prompt es largo → cachear (mismo cache_boundary pattern).
- Si dashboard Streamlit lento → MV.
- Si goldens tienen PII reales → REPLACE inmediato con fixtures sintéticas.

---

## Ajustes vs plan original

- **Score scale 1-5 (no 0-1)** como dijo el plan original. Razón: alineación
  con copilot F9 para que el admin cross-agent dashboard compare scores
  homogéneos. Threshold 3.5 (70%) en lugar de 0.75. Los acceptance
  criteria del plan se cumplen igual — la conversion ratio es 1:1.
- **5 dims** con naming refinado vs lista del plan:
  - `brand_voice_fidelity` (idem plan).
  - `commercial_effectiveness` (idem plan).
  - `pii_safety` (idem plan).
  - `channel_format_correctness` (idem plan).
  - `tone_locale_fitness` (refinamiento de
    `spanish_neutro_or_brand_voice` — mismo intent, mejor naming).
  Sin campo separado `overall` — el plan lo pedía pero `avg_score`
  derivado cumple igual y es consistente con CopilotJudge.
- **Bucket = `category`** (golden category) en lugar de `workflow_id` del
  copilot. Razón: sales_agent no tiene "workflows" — agrupa por tipo de
  conversación canónica. Schema mirror pero columna renombrada
  (`workflow_id → bucket_id`).
- **Source = goldens fijos** en lugar de samplear conversaciones reales.
  Razón: los goldens cubren las categorías canónicas; sampling per-tenant
  surgirá en una fase futura cuando haya volumen multi-tenant que
  warrant sampling. Esa decisión queda flagged para revisión en S+1.
- **Cron 07:00 UTC** Mondays (no 06:00 como dice el plan) — para evitar
  stacking con `weekly_copilot_rag_eval` (06:00 UTC).
- **Goldens viven en `tests/quality/sales_agent_goldens/`** y son
  importadas por el cron via lazy import. No bloquea la importación del
  paquete `sales_agent.application.quality`. Funciona porque las
  goldens son fixtures sintéticas inmutables.
- **Tech debt detectado durante S10**: ninguno bloqueante. Pre-existing
  issues no entran al log nuevo (siguen los DEFERRED-S11/S12 ya
  asignados).
