# Learnings — F9 Quality + Observability

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `e21738cf`)

---

## Resumen 3 líneas

- F9 entrega 5 piezas: `CopilotJudge` (NANO + 4-dim CoT rubric); 20 golden conversaciones across 8 categorías con runner stub-default + opt-in real LLM via `RUN_LLM_JUDGE=1`; tabla `copilot_workflow_metric` + repo + migration 072 idempotente; ARQ task `weekly_copilot_quality_eval` (lunes 05:00 UTC) que sample 50 conv last 7d → judge → upsert; admin `/copilot-quality` page que lee la tabla precomputada (cero LLM calls al render); `node_enter`/`node_exit` emitidos en chat orchestrator desde `astream_events` para reconstruir timeline per-node.
- Decisión no obvia: judge devuelve **un solo JSON con las 4 dimensiones** (single LLM call, no 4 calls), threshold 3.5/5, dims alfabetizadas en el prompt para mitigar position bias. NANO + `temperature=0` + `seed=42`. Cost guard: 6_000 calls/month ≈ $0.024. Sin LangSmith / Phoenix / Ragas — el harness es 200 LOC y vive in-process; SaaS deps sumarían superficie sin ROI hasta tener volumen real.
- Hooks listos para F10: `node_enter`/`node_exit` ya populan trazas → F10 RAG retrieval golden mide hit rate via los mismos eventos. Patrón "stub LLM en CI default + opt-in real LLM" replicable para F10 RAG eval set. `WorkflowMetricRepository.upsert(extra_metadata=...)` acepta JSONB libre — F10 puede agregar `retrieval_recall` / `kb_citations` sin migration nueva.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Multi-dim rubric en UN solo JSON** (no 4 LLM calls per dim, no pairwise). | Research abril 2026 (Monte Carlo, Confident AI, Label Your Data) confirma single-output multi-dim como estándar para batch screening + dashboard. Pairwise pierde valor cuando tenés rúbrica fija. 4 calls separados multiplican costo 4x sin ganancia de alineación medible. | Pairwise A/B (irrelevante: no hay baseline output). 4 calls separados (4x costo, mismo CoT por dim → calidad equivalente). |
| **Threshold 3.5/5 (= 70%)** como pass condition. | Research abril 2026 + F8 routing usa 0.7 en `LLMClassifier`. Mantener un único umbral cross-fase facilita mental model. 4.0 era demasiado estricto para stub mode; 3.0 muy laxo (un dim débil contamina avg). | 4.0 (90%): demasiado estricto, stubs limpios pasan pero el más mínimo dip real falla. 3.0 (60%): laxo — un score 1 en una dim contamina sin que dispare alerta. |
| **Stub default en CI + opt-in real via `RUN_LLM_JUDGE=1`.** | Cada CI run con NANO real son 20 calls × $insignificante; pero × N PRs/día × N developers × meses suma a un costo recurrente sin valor (los goldens son determinísticos, no detectan regresiones model-side). El opt-in para weekly cron + manual inspection es donde el LLM aporta. | Real LLM en cada CI run. Costo recurrente innecesario + non-deterministic flakiness por cambios silenciosos del modelo OpenAI cada vez. |
| **No LangSmith / Phoenix / Ragas como dep**. Harness custom in-process. | F9 mandate explícito: 5 piezas custom. Las plataformas SaaS suman: setup overhead, network calls (latency en weekly cron), API key management, billing line item, vendor lock. El harness propio = 200 LOC self-contained, idéntico patrón al `LLMClassifier` F8 que ya pasamos un trimestre afilando. Cuando Nicolify tenga >100k turns/día y queramos a/b testing prompts, evaluar Phoenix; hoy es scope creep. | LangSmith eval (vendor lock + setup), Arize Phoenix (otra dep + Postgres collector); Ragas (RAG-specific, no fit copilot quality). |
| **`node_enter`/`node_exit` emitidos en chat orchestrator, NO dentro de los nodes mismos.** | Los nodes del deep_agent y subagents son owned por LangChain — modificarlos requería forks o middleware custom. `astream_events(version="v2")` ya yield `on_chain_start`/`on_chain_end` con `metadata.langgraph_node` por cada transición. Hookear allí es cero invasivo, captura nodes Y subagents Y middleware, y zero-impact si futura version del harness cambia internals. | Wire dentro de cada node manualmente. Habría requerido tocar deepagents internals + replicar para cada nuevo subagent F-pos. |
| **Filtro `metadata.langgraph_node` para evitar trace explosion.** | `astream_events` yield events para chains+wraps+ToolNodes — todos llevan `on_chain_start`/`on_chain_end`. Sin filtro, una conversación normal escupiría 50-100 trace rows. Con filtro solo emite los nodes "reales" (~10 por turn). Trade-off correcto: cobertura sin ruido. | Emitir todo. Multiplicaría INSERTs ~5-10x sin valor diagnóstico (el wrapper layer es plumbing, no decisión). |
| **`workflow_metric` precomputado por ARQ, admin page solo lee**. | Plan F9 §4.3 sugería "auto-eval sobre sample en la página". Eso = 50 LLM calls al cargar la página = 30s+ de latencia + ~$0.0002 por render + spam de API key. Precomputar weekly + cache en tabla tiene mismo recall + page load <1s + costos predictibles. | Eval inline en admin page. UX inaceptable + costo no-bounded por re-renders. |
| **Cron lunes 05:00 UTC (ARQ), NO GitHub Actions.** | Plan F9 §4.5 ofrecía "GitHub Actions o ARQ". ARQ ya está deployado, accede DB local sin setup, no necesita secret management para OPENAI_API_KEY (ya está en env del worker), y la falla de un run es visible en `/copilot-quality` (empty data → flag). GH Actions habría requerido secrets, network egress, separate failure mode. | GH Actions. Innecesario para infra con worker propio. |
| **Schema column `extra_metadata` (no `metadata`).** | `metadata` es palabra reservada de SQLAlchemy declarative + colliso con `Base.metadata`. Renombrar evita el friction y mantiene el alias `Column("metadata", ...)` que rompía `pg_insert.excluded.metadata` (excluded usa SQL column name, no Python attribute). | `Column("metadata", JSON)` con alias Python. Funciona pero excluded shows AttributeError críptico al upsert. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **`pg_insert.excluded` usa SQL column name, no Python attribute name.** Si declarás `Column("metadata", JSON)` con atributo Python `extra_metadata`, `stmt.excluded.extra_metadata` lanza `AttributeError: extra_metadata`. Solución: usar `Column(JSON)` con el mismo nombre Python+SQL. Aplica a CUALQUIER upsert nuevo donde quieras renombrar la columna física.

- **F8 dejó `redirect_slashes=False` patch + tres anchors nuevos** (cap 30/30). F9 agregó 3 anchors → bumpear cap a 33. F10 que agregue 1-2 más cabe sin bump; >2 requiere otro bump. Ratchet test enforce.

- **Tests del repo `WorkflowMetricRepository` crashearon en el primer commit por el alias `metadata`.** No fallaron en `pytest tests/modules/copilot/test_workflow_metric_repository.py` aislado pre-bug — el error `AttributeError: extra_metadata` aparece SOLO al ejecutar `upsert` real, no al crear el modelo. Lección: cualquier nuevo upsert PG con columnas con alias debe correr `test_upsert_inserts_new_row` antes de assumir que la modelación está bien.

- **`structlog` (F3 gotcha replicado).** El kwarg `event` está reservado. F9 usa `event_name` en `_judge_sample` errors si los hubiera; cualquier futuro logger en este harness debe respetarlo. Anotado por si F10 mete un nuevo log point.

- **`langchain.AIMessage.response_metadata` shape varía**. OpenAI clients setean `id` directo al top-level del AIMessage, no en `response_metadata`. Anthropic expone `id` en ambos. La `_extract_response_id` del judge intenta varios paths (`response.id`, `response.response_id`, `response_metadata.id`, `response_metadata.system_fingerprint`). Si una nueva model family entra al stack y el `response_id` queda `None`, F-pos puede agregar el path correspondiente — el code path es defensive ya.

- **Goldens y voseo**: las primeras 19 conv tenían dejo argentino ("querés", "tenés", "respondeme", "necesitás", "Empezá", "te animás", "Decime", "preferís"). Los expected_output del golden representan la salida ideal del copilot, NO la voz del tenant — debe ser español neutro per regla 11. Test `test_system_prompt_in_spanish_neutro` en `test_copilot_judge.py` valida el prompt del judge mismo. F-pos que agregue conversaciones nuevas: correr golden runner pre-commit y revisar diff por voseo.

- **El judge devuelve `passes_threshold=False` con `dimensions[].score=0.0` en caso de error**, NO raises. Es intencional para que el dashboard muestre "Failed" como datapoint vs hueco silencioso. Tests verifican esto. F-pos que invoque el judge SIN chequear `passes_threshold` debe assumir que el `JudgeResult` siempre llega, nunca crashea — pero `metadata.error` revela por qué falló.

- **Test flaky heredado `test_streaming_integration` post-F9 sigue verde aislado (34/34)** después de wire `emit_node_trace_event` al chat orchestrator. Confirmado en el sweep final F9. F10 que toque streaming/orchestrator: correr aislado primero, pattern heredado F0-F8.

- **Test flaky heredado `test_editable_fields_ssot::test_no_cross_domain_duplicates` sigue activo**. F9 NO tocó `editable_fields` registry. Pattern heredado.

- **Postgres `metadata` keyword reserved trap**: aunque el código Python use `extra_metadata`, el SQL (`alembic` migration) había declarado `metadata JSONB NULL`. Postgres lo acepta (no es keyword reserved en DDL), pero rompe la simetría con el modelo. Renombrar a `extra_metadata JSONB` en la migration mantiene paridad column-by-column. Si futuras migraciones reusan el patrón, asegurar que el SQL match exactamente el atributo Python.

---

## Recomendaciones accionables para F10 (Marketing KB curado)

1. **Antes de empezar:** correr la suite F0-F9 baseline (~3042 verde, sin contar flakies aislados):
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/ \
     tests/architecture/ \
     tests/admin/ \
     tests/modules/brand/ tests/modules/offer/ tests/modules/crm/ \
     tests/shared/ \
     tests/quality/ \
     -q -o addopts="" --timeout=120 \
     --ignore=tests/modules/copilot/test_streaming_integration.py \
     --ignore=tests/architecture/test_editable_fields_ssot.py
   ```
   Flakies aislados:
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/test_streaming_integration.py \
     tests/architecture/test_editable_fields_ssot.py \
     -q -o addopts=""
   ```

2. **F10 RAG eval debe reusar `CopilotJudge` con un sub-rubric custom** — el constructor acepta `dimensions=("retrieval_relevance", "citation_accuracy", "answer_groundedness", "completeness")`. NO duplicar el judge: pasar `dimensions=` custom + `threshold=` ajustado. El stub default funciona idéntico.

3. **Goldens F10 RAG retrieval set en `tests/quality/golden/test_rag_retrieval.py`**, copiando el patrón del archivo F9 (`tests/quality/golden/test_golden_conversations_semantic.py`). Conversaciones con queries técnicas (StoryBrand framework, Hormozi value equation, Cialdini reciprocity) + ground-truth chunks expected.

4. **`copilot_workflow_metric.extra_metadata` JSONB acepta cualquier shape** — F10 puede meter `{retrieval_recall: 0.85, kb_citations: ["sb_promise_001"], retrieval_latency_ms: 120}` sin migration nueva. El admin page lee `extra_metadata->>'retrieval_recall'` directo en SQL.

5. **`node_enter`/`node_exit` ya capturan subagent transitions** (`langgraph_node` metadata existe en deep_agent + subagents). F10 RAG retrieval node aparece automatically en trazas — solo agregar el query al `data.input_preview` para diagnostic.

6. **Anchor budget está en 33/33.** F10 puede agregar 1 (`COPILOT-MARKETING-KB-F10`) sin bump; >1 requiere editar `tests/architecture/test_copilot_anchors.py` cap.

7. **El admin page `/copilot-quality` puede agregar una sección "Top retrieved KB chunks"** consultando `copilot_trace_event` directamente (sin schema nuevo) cuando el F10 KB esté wired.

8. **Test patrón "stub default + opt-in real"** está en `tests/quality/conftest.py::judge_llm`. F10 RAG runner debe seguir el mismo patrón — `RUN_LLM_JUDGE=1` triggera real NANO eval, default es stub. CI runs use stub, weekly cron usa real.

9. **Cost guard del judge ya está documentado en docstring `copilot_quality_eval.py`**. F10 RAG eval no debe exceder 100 LLM calls / weekly run para mantener el cost guard. Si Marketing KB requiere más, evaluar batch grouping + cache.

---

## Riesgos abiertos

- **`build_default_router` sigue NO wired al orchestrator chat (heredado F8).** F8 dejó factory + admin page; F9 NO lo wireó. El admin `/copilot-routing` muestra "Sin decisiones de routing" hasta que F-pos cutover llame `router.select(req)` antes del graph stream + persista vía `RoutingLogRepository`. F10 puede absorberlo si quiere ver datos reales de routing en sus dashboards, pero NO es F10 scope.

- **El judge real con NANO no fue probado en producción**. CI default usa stub, weekly cron va a correr la primera vez en el primer lunes post-deploy. Riesgo: si OpenAI cambia el modelo NANO silenciosamente o si la API throttea, el job ARQ va a fallar el primer run y los rows no aparecen. Mitigación: el job swallow exceptions + log → admin page shows "Sin métricas" como empty-state; revisar logs `weekly_copilot_quality_eval` la primera semana.

- **Spanish neutro en goldens es enforced por convenio, NO por test.** Cualquier futuro contributor que agregue conversaciones puede meter voseo sin que el CI los catch. Considerar un test arch `test_goldens_no_voseo` que reuse `_VOSEO_RE` de `brand_summary_regen.py`. F-pos housekeeping.

- **`node_enter`/`node_exit` agrega ~10x trace rows por turn.** No medido en producción. Si la table crece más rápido que el `cleanup_old_events` job (3:30am UTC daily), considerar bumpear retention window o agregar partitioning. F10 puede instrumentar count growth.

- **Goldens 20 puede ser insuficiente**. Research abril 2026 sugiere 50-200 para alpha de Krippendorff confiable. El plan F9 dijo 20 explicitamente y los entregamos; cuando producción muestre regresiones reales, expandir a 50 sin reescribir la infra (solo agregar `GoldenConversation(...)` rows).

- **`workflow_id` ahora se sample desde `conv.workflow_state` o `conv.procedure_state` con fallback `_no_workflow`.** Conversaciones legacy pre-F6 tienen `procedure_state` con shape libre; el sampler intenta `procedure_state.procedure` como key. Si una procedura legacy guardó el id bajo otra clave, la conv cae al bucket sentinel. F-pos cutover (cuando borre `procedure_state`) puede simplificar la lógica.

- **Migration 072 tiene `extra_metadata JSONB NULL`** — el modelo SQLA usa `JSON` (no JSONB explicit). En SQLite tests, JSON es text fallback (PASS); en Postgres prod, JSONB. Confirmar al deploy que el column type se materialize como JSONB y no JSON regular.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/application/observability/judge.py::CopilotJudge` — sync, 4-dim, threshold-gated. Acepta `dimensions=` custom para sub-rúbricas. Patrón: `judge = CopilotJudge(dimensions=("relevance", "groundedness", "completeness"), threshold=3.0); result = judge.evaluate(user_input=..., assistant_output=..., context=retrieved_kb_chunks)`.

- `backend/src/modules/copilot/application/observability/node_trace.py::emit_node_trace_event(recorder, event)` — pure function. F10 que agregue subagent nuevo (e.g. `KNOWLEDGE_SEARCH_SUBAGENT`) automatically genera trace rows sin tocar nada. Filter por `metadata.langgraph_node` evita ruido.

- `backend/src/modules/copilot/infrastructure/repositories/workflow_metric_repository.py::WorkflowMetricRepository.upsert(extra_metadata=...)` — JSONB libre. F10 puede meter retrieval-specific KPIs sin migration: `extra_metadata={"retrieval_recall": 0.85, "kb_chunks_used": 3}`.

- `backend/src/shared/workers/copilot_quality_eval.py::run_weekly_quality_eval(db, judge=...)` — sync entry point. F10 RAG eval puede crear `RagEvalJudge(CopilotJudge)` subclass con dims propias e invocar el mismo runner pasando `judge=rag_judge`. Sample → judge → upsert pipeline reusable end-to-end.

- `backend/tests/quality/conftest.py::judge_llm` fixture + `RUN_LLM_JUDGE=1` env flag — patrón stub/real. F10 RAG goldens copy.

- `backend/src/admin/modules/copilot_quality.py::_fetch_workflow_kpis` — query template parametrizable. F10 puede agregar una page hermana `/copilot-marketing-kb` con la misma forma + ad-hoc queries sobre `extra_metadata`.

- `backend/tests/architecture/test_workflow_metric_compliance.py` — fitness test que enforces `workflow_id` shape. F10 que agregue workflows nuevos (e.g. RAG-grounded design_offer) cumple sin tocar el test.

- Anchor budget cap 33/33 con 3 entradas F9 (`COPILOT-LLM-JUDGE-F9`, `COPILOT-WORKFLOW-METRIC-F9`, `COPILOT-NODE-TRACE-F9`). F10 puede agregar 1 anchor sin bump.

---

## Fuentes research útiles

- [Rubric-Based Evaluations & LLM-as-a-Judge — Adnan Masood, Apr 2026](https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80) — confirmó que **rubric-based + multi-dim** es el estándar abril 2026 vs single-score. Validó la elección de 4 dims con CoT short.
- [LLM-As-Judge: 7 Best Practices — Monte Carlo](https://www.montecarlodata.com/blog-llm-as-judge/) — confirmó **75-90% agreement con human labels** como threshold de validación pre-scaling. Para nuestro stub mode con 4.0 cross-board, asegura que el pipeline es coherent; el real LLM en weekly cron es donde mediremos esa alineación.
- [LLM-as-a-Judge Guide — Confident AI](https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method) — confirmó **G-Eval pattern**: generate evaluation steps → apply → score. F9 lo aplicó como "razón ≤80 chars per dim".
- [Intent Classification 2026 — Label Your Data](https://labelyourdata.com/articles/machine-learning/intent-classification) — heredado F8. Confirmó threshold 0.7-0.85 zone; F9 mantuvo 3.5/5 (= 0.7) para coherencia cross-fase.
- [Evaluating Deep Agents — LangChain Blog](https://blog.langchain.com/evaluating-deep-agents-our-learnings/) — confirmó que LangSmith-equivalent eval **se puede armar in-process** con goldens + judge. Validó la decisión de NO sumar SaaS dep.
- [LLM Evals Framework: Confident AI Playbook](https://www.confident-ai.com/blog/the-ultimate-llm-evaluation-playbook) — confirmó que **conversation eval at specific points (N+1)** es preferible a end-to-end transcript scoring. F9 evalúa `(last_user_msg, last_assistant_msg)` por conversación.

Tessl tiles consultados: `tessl__fastapi`, `tessl__pytest-api-testing`. No instalé tile nuevo — F9 reutiliza el stack F8 (NANO + structured JSON + threshold gating) ya cubierto en docs.
