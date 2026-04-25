# Prompt — F9 Quality + Observability

Copiar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F9 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: detectás degradación antes que el user. Concretamente: (1) golden tests semánticos para 20 conversaciones canónicas con LLM-judge corriendo weekly en CI; (2) trace recorder completo con `node_enter`/`node_exit` por cada node del deep agent + subagents; (3) admin Streamlit `/admin/copilot/quality` con LLM-as-judge eval sobre sample de 50 conversaciones; (4) eval framework por workflow con tabla nueva `copilot_workflow_metric` (completion rate, accept rate, satisfaction proxy); (5) weekly cron (GitHub Actions o ARQ) que corre todo + reporta a Slack/email.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§topología destino)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md
11. docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md
12. docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-unification.md
13. docs/domains/copilot/redesign-2026-04/learnings/F7-channel-formatter.md
14. docs/domains/copilot/redesign-2026-04/learnings/F8-routing.md  ← APRENDIZAJES F8 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 3 queries del mandate F9):
    - "LLM-as-judge eval framework 2026 best practices"
    - "LangChain evaluation patterns deep agents 2026"
    - "golden tests semantic similarity LLM regression 2026"
  - Confirmar: rúbrica multi-dimension (utility/accuracy/brand_coherence/tone) o single-score con CoT? Threshold semantic similarity (≥85%)?
  - Tessl tiles: `tessl__fastapi`, `tessl__langgraph`, `tessl__pytest-api-testing`. Si sale tile sobre LangSmith / Phoenix / Ragas, evaluar.

- **Foco — no scope creep.** F9 entrega 5 piezas específicas del §1. NO mezcla F10 (RAG marketing kb). NO toca el sales_agent. La cobertura del LLM-judge es sobre el copilot, no sobre channels adapters.

- **Paso 4 — TDD obligatorio.**
  - Tests por capa: golden runner (entrada fija → LLM-judge → score), workflow_metric repository, trace_event ingestion del nuevo `node_enter`/`node_exit`, admin page contract.
  - Arch test: cada workflow declarado en `WorkflowProvider` debe tener KPIs trackeados (`copilot_workflow_metric` row con `workflow_id`).
  - Golden snapshot F1+F2+F3+F4+F5+F6+F7+F8 verde ANTES de empezar (~3019 backend tests + 245 FE).

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F8.
  - Después de cada bloque: ruff + golden + arch.
  - Si tocás trace recorder: correr `tests/modules/copilot/test_trace_recorder.py` aislado.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end (F8 §5.4 cement).
  - Cards (proposal/clarify/preview_update/plan_card) renderean.
  - Multimodal blocks (TextBlock, ImageBlock, etc.) intactos.
  - Ratchet `copilot → módulo` sigue en 22.
  - Anchor budget capa 30/30 (F8 dejó 3 anchors); F9 si agrega bumpea con justificación.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (LLM-judge prompt design; threshold elegido; CoT o single-score; LangChain Eval vs custom; LangSmith/Phoenix decisión).
  - Gotchas reales: LLM-judge bias documentados (positional, length-bias), cuántos golden bastan (20 ya plan; en práctica?), qué pasa si OpenAI cambia modelo y golden cae 5%.
  - Hooks listos para F10 (RAG retrieval golden + judge).

- **Paso 8 — Generar `prompts/F10-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f9): quality + observability`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F9-quality.md` y `prompts/F10-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F9 no aplica por aprendizajes F8 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4 + F5 + F6 + F7 + F8). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F9 (de aprendizajes F8)

### Aprendizajes F8 que F9 debe asumir

- **F8 §5.2 reorden cementado**: el sistema prompt arranca con `STATIC_IDENTITY` + `STATIC_TOOLS_HINT` + `LIGHTHOUSE` + `EDITABLE_CATALOG` + `MODULES_LIST` (cacheable) seguido de `CACHE_BOUNDARY_MARKER` + `STUDIO_SNAPSHOT` + `WORKFLOW_STATE` + `INSPIRATIONS` (volatile). El orden está congelado en `tests/architecture/test_system_prompt_order.py`. Si F9 quiere insertar un fragment nuevo (ej. golden_test_marker), debe slotearlo en la lista correcta.
- **`UsageAccumulator.cached_input_tokens` + `cache_hit_rate`** ahora se persisten en `copilot_trace_event.data` cada `turn_end`. F9 LLM-judge dashboard puede correlacionar quality scores vs cache hit rate cross-tabulado.
- **`build_default_router()` factory listo** pero NO está wired al chat orchestrator todavía. El admin `/copilot-routing` muestra empty-state hasta que F9 (o F-pos cutover) llame `router.select(req)` antes del graph stream y persista vía `RoutingLogRepository`. Esto es WIN-WIN para F9: si lo wirea como parte del trace event work, llena el admin page de paso.
- **ReAct legacy + flag `COPILOT_DEEP_AGENT_V2` borrados**. Deep agent harness es el único graph runtime. Trace recorder ya no debe referenciar `agent_node`/`tool_executor_node` (F8 actualizó la docstring). F9 que extienda trace events tiene UN solo grafo que cubrir.
- **`_handle_tool_end_v2` emite `block_append`** + tool_result + ui_action. Si F9 introduce judge cards (e.g. "este turn fue judged como low-quality") puede emitir como `block_append` con un nuevo `card_kind="judge_feedback"`.
- **`text_chunk` BE/FE removed** — protocolo SSE es solo v2 ahora. Cualquier nueva métrica streaming debe usar `block_*` o un nuevo SSE event type registrado en `SSEEventType`.
- **`ModelRole.NANO` agregado al enum + config**. F9 LLM-judge debe usar NANO (cheap + fast) — copia el patrón `LLMClassifier._resolve_llm` para invocar.
- **`ModelTier.NANO` exists** desde F0 en `domain/model_tier.py` — cualquier tool nuevo del judge harness puede declarar su tier sin tocar el enum.

### Tests baseline que F9 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/ \
  tests/architecture/ \
  tests/admin/ \
  tests/modules/brand/ \
  tests/modules/offer/ \
  tests/modules/crm/ \
  tests/shared/ \
  -q -o addopts="" --timeout=120
```

Esperado: ~3019 passed, 4 skipped, 1 failure heredado (`test_editable_fields_ssot::test_no_cross_domain_duplicates` — order-dep, PASS aislado). Confirma flakies aislados:

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/test_streaming_integration.py \
  tests/architecture/test_editable_fields_ssot.py \
  -q -o addopts=""
```

Frontend:

```bash
cd frontend && npx vitest run src/features/copilot/ src/__tests__/architecture/
```

Esperado: 245 + 38 verde.

### Archivos clave que F9 modifica (a priori)

- `backend/src/modules/copilot/application/observability/trace_recorder.py` — extender con `node_enter`/`node_exit` per-node si no estaban.
- `backend/src/modules/copilot/application/observability/judge.py` — nuevo, LLM-judge runner (NANO + structured rubric output).
- `backend/src/modules/copilot/infrastructure/models/workflow_metric_model.py` — nueva tabla `copilot_workflow_metric`.
- `backend/alembic/versions/072_copilot_workflow_metric.py` — migración idempotente.
- `backend/tests/quality/golden/test_golden_conversations_semantic.py` — 20 goldens.
- `backend/tests/quality/conftest.py` — fixtures + LLM-judge stub.
- `backend/src/admin/pages/copilot-quality.py` + `backend/src/admin/modules/copilot_quality.py` — nueva admin page.
- `backend/src/modules/copilot/workers/quality_eval_task.py` — ARQ task para weekly run.
- `tests/architecture/test_workflow_metric_compliance.py` — fitness test.

### Riesgos que vigilar en F9

- **LLM-judge cost**: 50 conversaciones × NANO ≈ irrelevante; PERO si la rúbrica usa CoT con outputs ~500 tokens, costo escala. Medir al diseñar y poner cap mensual en GitHub Actions.
- **Golden flakiness**: LLM responses son non-deterministic. La rúbrica semántica debe tolerar variación; threshold ≥85% similarity puede ser volátil con `temperature=0`. Plan: `temperature=0` + `seed=42` + capturar response_id en la persistencia para detectar cuando OpenAI cambia el modelo silently.
- **Trace recorder crece**: añadir `node_enter`/`node_exit` per-node multiplica las filas por 5-10x por turn. F9 debe medir el impacto en write throughput + considerar batch insert. La tabla ya tiene `created_at` indexado pero el INSERT cost importa.
- **Admin page LLM-judge dashboard**: invocar 50 LLM-calls al cargar la página = 50s de latencia. Plan: precomputar nightly via ARQ + cache resultado en `copilot_workflow_metric` o tabla nueva; admin page lee solo lo precomputado.
- **`build_default_router` wiring**: si F9 wirea el router al orchestrator chat, debe correr `tests/modules/copilot/test_streaming_*.py` aislado pre+post (heredado flaky F0-F8).
- **Spanish neutro LatAm en LLM-judge prompt**: la rúbrica + el output del judge debe estar en español neutro per CLAUDE.md regla 11. Sin voseo. Si el judge produce voseo en sus reasonings, los reportes admin tendrán dejo argentino — bug user-facing.

### Hooks F8 disponibles para F9

- `backend/src/modules/copilot/application/router/__init__.py::build_default_router` — factory canónico, F9 puede invocarlo en el chat orchestrator + persistir routing decisions vía `RoutingLogRepository.insert(...)` para llenar el admin `/copilot-routing` page.
- `backend/src/modules/copilot/application/router/classifiers/llm_classifier.py::LLMClassifier` — patrón "NANO + structured JSON + threshold" replicable en F9 LLM-judge. Sync, fail-soft (None on exception), threshold configurable.
- `backend/src/modules/copilot/application/orchestrator/usage_tracking.py::UsageAccumulator` — ahora con `cache_hit_rate` y `cached_input_tokens`. F9 dashboard puede correlacionar quality vs cache hit.
- `backend/src/admin/modules/copilot_routing.py` — patrón completo de admin page con filtro por tenant + queries SQL agregadas a `copilot_trace_event`. F9 quality dashboard sigue el mismo molde.
- `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py::PromptFragment` — enum extendible si F9 necesita slotear un fragment nuevo (judge_feedback?).
- `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY` con cap 30. F9 anchors típicos: `COPILOT-LLM-JUDGE-F9`, `COPILOT-WORKFLOW-METRIC-F9`. Cap permite ambos sin bump.
- `tests/admin/conftest.py::_stub_session().mappings.return_value.all` — patrón para mockear queries SQL agregadas en smoke tests admin.
