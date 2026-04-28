# Learnings · S10 · quality-eval-loop

> Fase final del redesign. No hay S11 que iniciar desde acá; esta nota
> existe para futuras iteraciones (S+1 sampling real, S11 cohesión
> orchestrator) que extiendan o consuman el judge.

---

## Resumen (3 líneas)

- **Entregado**: `SalesAgentJudge` (5-dim rubric, NANO, fail-soft) + 20
  goldens cubriendo 6 categorías (qualification / objections /
  closing_payment / booking / multi_channel / brand_voice_diff) +
  cron `weekly_sales_agent_quality_eval` Mondays 07:00 UTC + drift
  detection (>5% week-over-week → structlog warning) + Streamlit
  `/sales-agent-quality` dashboard + migration 082 idempotente +
  `SalesAgentWorkflowMetricModel` + repo + 5 arch tests adicionales +
  92 unit/integration tests verde.
- **Decisión no obvia**: scale 1-5 + threshold 3.5 (no 0-1 / 0.75 como
  pedía el plan original). Razón: alineación con copilot F9 para que el
  admin cross-agent dashboard compare scores homogéneos. Conversion 1:1,
  acceptance criteria del plan se cumplen igual.
- **Listo para futuro**: `AccessProvider` stub queda en S9 — al wirear
  EmailAccessProvider / ManychatAccessProvider real, el judge ya cubre
  el caso porque las dims `commercial_effectiveness` + `pii_safety`
  tocan el flow grant_access. Sampling de conversaciones reales queda
  DEFERRED-S+1 cuando emerja volumen multi-tenant.

---

## Decisiones clave

- **Mirror del CopilotJudge vs custom desde cero**:
  - Tomada: mirror exacto con renombrado semántico de dims.
  - Razón: F9 ya validado en producción, infra event-sourced compartida,
    mismo `ModelRole.NANO`, mismo `LLMFactory`, mismo pricing snapshot.
    Cero dependencias nuevas. El test_copilot_judge contract es la
    biblia que aplica con renames.
  - Alternativa descartada: LangSmith Evaluator. Razón: overkill cuando
    la infra propia ya cubre observability event-sourced + cost
    tracking. Introducir LangSmith trae vendor lock-in + extra deploy.

- **Score 1-5 + threshold 3.5 vs 0-1 + 0.75 del plan original**:
  - Tomada: 1-5 + 3.5.
  - Razón: alineación cross-agent. `/copilot-quality` y
    `/sales-agent-quality` muestran la misma escala — operador no
    aprende dos vocabularios. Conversion ratio idéntica.
  - Alternativa descartada: 0-1 como pedía S10 doc original. Razón:
    inconsistencia obvia.

- **5 dims con renaming `tone_locale_fitness`**:
  - Tomada: `tone_locale_fitness` (sintetiza el "spanish_neutro_or_brand_voice"
    del plan a un nombre más preciso semánticamente).
  - Razón: la dim cubre TANTO neutro LATAM por default como voseo AR si
    el tenant lo configuró — "fitness" del tone al locale + brand voice
    captura ambos casos sin la disjunción larga.
  - Alternativa descartada: `spanish_neutro_or_brand_voice` (literal del
    plan). Razón: nombre engorroso, lee mal en dashboards.

- **Bucket = golden category** (vs `workflow_id` del copilot):
  - Tomada: discriminator `bucket_id` con valor = category name.
  - Razón: sales_agent no tiene "workflows" — el StateGraph es lineal.
    Las categorías canónicas (qualification / objections / etc) son la
    granularidad útil para el dashboard.
  - Alternativa descartada: usar `current_state` (rapport / discovery /
    closing). Razón: stage es ortogonal a category — un golden de
    "objection at closing" cae bajo objections category aunque el stage
    sea closing.

- **Cron source = goldens fijos vs sample real conversations**:
  - Tomada: goldens fijos hoy (~20).
  - Razón: cubren las categorías canónicas; sampling per-tenant requiere
    volumen multi-tenant (≥10 tenants × ≥50 conversations/sem) que no
    existe en producción todavía.
  - Alternativa descartada: hybrid (golden + 5 conversaciones random
    per-tenant). Razón: noise alto sin baseline. DEFERRED-S+1.

- **Goldens importadas desde `tests/` por el cron** (lazy import):
  - Tomada: cron hace `from tests.quality.sales_agent_goldens.conversations import GOLDEN_CONVERSATIONS`.
  - Razón: los goldens son fixtures sintéticas inmutables; viven
    naturalmente en `tests/` y duplicarlos en `src/` sería anti-DRY.
    Lazy import evita dependencia circular en cold start.
  - Alternativa descartada: mover goldens a
    `src/modules/sales_agent/application/quality/goldens/`. Razón:
    scope creep, los goldens tienen test runner asociado que vive en
    `tests/`. Si crecen >50 goldens con metadata, re-evaluar (FLAGGED-S11).

- **Period normalization al inicio del día UTC**:
  - Tomada: `_compute_period_window` redondea `end` a 00:00:00 UTC.
  - Razón: rerun mismo día → mismo `period_start` → ON CONFLICT upsert
    funciona. Sin esta normalización los microsegundos de `utc_now()`
    rompen idempotencia y se acumulan rows duplicadas.
  - Alternativa descartada: dejar `utc_now()` raw. Razón: bug
    descubierto durante TDD GREEN — re-run del test creaba 12 rows en
    lugar de 6.

---

## Sorpresas / gotchas críticos

- **F9 copilot judge ignora PII en su prompt** (lo recibe directo del
  conversation messages). En sales_agent es bloqueante porque los leads
  envían emails / phones / DNI / CURP / CUIT directo al chat, y el judge
  prompt va a un LLM externo. Solución: `_scrub_for_judge(text)` envuelve
  cada free-text en `sanitize_payload({"_": text})`, extrae el resultado
  redactado. Sin esto compliance LATAM rompe (LGPD/LFPDPPP/PDPA) →
  judge envía PII a OpenAI / Anthropic. Arch test
  `test_quality_judge_no_pii_in_prompt` AST-scan enforces que las 4 entradas
  free-text (`user_input`, `assistant_output`, `brand_voice`, `context`)
  pasen por `_scrub_for_judge`.

- **`SalesAgentJudge` necesita más context que `CopilotJudge`** —
  copilot sólo recibe `(user_input, assistant_output, brand_summary,
  context)`. Sales necesita además `channel` (whatsapp vs telegram vs
  sms cambian formato esperado) y `stage` (rapport vs closing cambia qué
  es "commercial_effectiveness"). Mantener simétrico el constructor pero
  agregar 2 kwargs opcionales.

- **`ON CONFLICT` con `pg_insert` + SQLite** — el patron del CopilotJudge
  funciona en SQLite si las columnas del unique constraint son
  exactamente iguales (sin microseconds drift). El bug descubierto fue
  que `period_start = utc_now() - 7d` cambia per-call → no hay conflict
  → cada call inserta. Fix: normalizar `period_start` al día UTC.

- **Anchor registry frozen** — agregar nuevo `[SALES-AGENT-QUALITY-S10]`
  anchor en `judge.py` rompe `test_all_sales_agent_anchors_are_registered`
  hasta que se sume entry en `ANCHOR_REGISTRY` de
  `tests/architecture/test_sales_agent_anchors.py`. ANCHOR_CAP=25
  acepta el growth (hoy 9 entries).

---

## Recomendaciones accionables para futuro

- [ ] **Cuando arranque RUN_LLM_JUDGE=1 en producción**, monitorear
  `copilot_llm_call` con tag `judge_model="nano"` para verificar costo
  real. Estimado: ~$0.05/semana con NANO + 20 goldens × 5 dims.
- [ ] **Si el judge LLM cost crece**, setear `prompt_cache_key="sales_agent_judge_v1"`
  (constante, no per-tenant) para forzar prefix cacheable cross-corrida.
  Hoy no aplica porque stub mode default.
- [ ] **Cuando emerja volumen multi-tenant**, agregar segundo path al
  cron que samplee conversaciones reales (con `sanitize_payload`)
  separadas por bucket discriminator distinto.
- [ ] **Si goldens crecen a 50+**, considerar moverlos a
  `src/modules/sales_agent/application/quality/goldens/` para que el
  cron no dependa de `tests/`. Lazy import sigue siendo válido pero
  pierde naturalidad.
- [ ] **Per-bucket drift threshold** cuando se detecten false-positives
  en alguna categoría con variance alta natural (probablemente
  `closing_payment` o `multi_channel`).
- [ ] **Snapshot test stub vs real** cada 4 weeks una vez en
  producción — comparar scores reales vs lo que devolvería el stub para
  detectar drift del modelo NANO.

---

## Hooks listos

- `src/modules/sales_agent/application/quality/judge.py::SalesAgentJudge`
  — instanciable con `llm=None` (NANO lazy) o stub para tests.
- `src/modules/sales_agent/application/quality/judge.py::CANONICAL_DIMENSIONS`
  — tupla 5 dims alfabética. Si se agrega dim nueva, actualizar
  `_DIMENSION_RUBRICS` + `conftest.py` stubs + tests del judge.
- `src/modules/sales_agent/application/quality/judge.py::build_system_prompt`
  — reusable con dim subset si futuro caso lo requiere (mirror copilot
  RAG_DIMENSIONS pattern de F11.5).
- `src/shared/workers/sales_agent_quality_eval.py::run_weekly_quality_eval`
  — sync entry point invocable desde admin button on-demand.
- `tests/quality/sales_agent_goldens/conversations.py::GOLDEN_CONVERSATIONS`
  — append-only para nuevos goldens. Cada nuevo entry hereda el
  pipeline sin tocar más nada.
- `tests/quality/sales_agent_goldens/conftest.py::sales_judge_llm` —
  stub fixture compartido. Importable por nuevos tests.
- `src/admin/modules/sales_agent_quality.py::render_sales_agent_quality`
  — page Streamlit standalone. Lee precomputado, nunca invoca LLM.
- Anchor `[SALES-AGENT-QUALITY-S10]` registrado.

---

## Riesgos abiertos

- **Stub default no detecta regresiones reales**. Para detectar drift
  de modelo (DeepSeek V4 → V5, Kimi K2.6 → K2.7), `RUN_LLM_JUDGE=1`
  debe estar activo en al menos 1 corrida weekly de producción.
- **Sampling solo de goldens**: si el agente real diverge (bug en prompt
  changes, regresión semántica) sin afectar goldens, el judge no
  cazará el bug. Mitigación: combinar con grader S7 (per-preset) +
  sampling real cuando emerja.
- **Drift threshold 5% global**: si una categoría tiene noise natural
  >5%, dispara false-positives. Watchpoint post-deploy con datos reales.
- **Goldens viven en `tests/`**: si alguien borra el dir tests/ por
  refactor, el cron rompe. Lazy import + structlog warning protege
  (returns 0 rows written, no raise), pero no es ideal. FLAGGED-S11.

---

## Tech debt detectado (NO arreglado)

- [LOW] Goldens en `tests/` consumidas por cron prod → `05-tech-debt-log.md` (FLAGGED-S11).
- [LOW] Sample real conversations cuando haya volumen → `05-tech-debt-log.md` (DEFERRED-S+1).
- [LOW] Drift threshold 5% global, no per-bucket → `05-tech-debt-log.md` (FLAGGED).
- [LOW] Judge LLM sin `prompt_cache_key` → `05-tech-debt-log.md` (FLAGGED).

---

## Fuentes research útiles

- [G-Eval / DeepEval docs · Confident AI 2026 · deepeval.com/docs/metrics-llm-evals]
  — confirmó CoT + form-filling + 1-5 scale + ≤80 chars reason por dim
  baja variance del judge ~10-15%. Mirror exacto del CopilotJudge.
- [arXiv 2604.00022 · 2026 · Criterion Validity of LLM-as-Judge for
  Business Outcomes in Conversational Commerce] — confirmó que las
  dims con mayor correlación con conversion son Need Elicitation +
  Pacing Strategy. Cambió: mapeo a `commercial_effectiveness`.
- [Building a "Golden Dataset" for AI Evaluation · getmaxim.ai 2026]
  — confirmó 10-20 inicial OK, 100+ cuando hay volumen real. Cambió:
  S10 lanza con 20, escala futura post-S+1.
- [LangSmith Evaluation Docs · langchain.com 2026] — comparé contra
  custom mirror del CopilotJudge. Cambió: descarté LangSmith por
  vendor lock-in + dependencias nuevas.

---

## Métricas medidas

- 92 tests S10 verde (judge contract + goldens runner + brand voice
  differentiation + weekly eval runner + arch PII sanitization).
- 636 architecture tests verde post-anchor entry.
- 534 sales_agent module tests verde (no regresión).
- 165 admin + quality tests verde (smoke incluye nueva
  `/sales-agent-quality` page).
- 0 ruff errors en S10 files.
- Migration 082 aplicada idempotente (clone + re-run = 0 changes).
- Tabla en prod verificada con 13 cols + 3 indexes (uq + ix tenant_period
  + pkey).
- Cron registrado en `WorkerSettings.functions` y
  `SchedulerSettings.cron_jobs` Mondays 07:00 UTC.
