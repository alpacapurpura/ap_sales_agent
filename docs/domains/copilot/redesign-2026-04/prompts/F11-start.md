# F11 — Housekeeping del Redesign 2026-04 (post-cierre)

> El plan original cerró en F10. Este prompt cubre **housekeeping post-merge**:
> deuda heredada, cleanup de zombies del legacy, y wiring final que F8/F9
> dejaron expuesto pero no integrado.

---

## Contexto

El redesign Copilot 2026-04 entregó F0–F10 entre marzo y abril 2026. Cada
fase preservó el §3 (lo que NO se toca) y dejó hooks documentados para
fases siguientes. F10 cerró el plan: el copilot ahora cita método aplicado
desde el corpus curado `nicolify_marketing_kb`.

Quedan 5 deudas conocidas. F11 es opcional (no estaba en el plan
original). Decidir scope basado en presupuesto y prioridades:

1. **Wire `build_default_router` al chat orchestrator** (heredado F8 + F9).
2. **Cutover `procedure_state` → `workflow_state`** (heredado F6).
3. **Fix flakies heredados** (`test_streaming_integration`, `test_editable_fields_ssot`).
4. **Drop legacy `copilot_knowledge` collection + admin module/page borrados** (heredado F10).
5. **Real-LLM weekly RAG eval cron** (extensión natural de F9 + F10).

---

## Pre-lectura obligatoria

Antes de tocar código, releer en este orden:

1. `docs/domains/copilot/redesign-2026-04/README.md`
2. `docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md` — **§3 sigue intocable**.
3. `docs/domains/copilot/redesign-2026-04/learnings/F10-marketing-kb.md` — **secciones "Riesgos abiertos" + "Recomendaciones accionables para F-pos"**.
4. `docs/domains/copilot/redesign-2026-04/learnings/F8-routing.md` — `build_default_router` factory + admin `/copilot-routing`.
5. `docs/domains/copilot/redesign-2026-04/learnings/F9-quality.md` — `weekly_copilot_quality_eval` ARQ pattern.
6. `docs/domains/copilot/redesign-2026-04/learnings/F6-workflow-unification.md` — `procedure_state` vs `workflow_state` dual-read.
7. CLAUDE.md raíz + `.claude/rules/copilot-resilience.md`.

---

## Estado del branch al iniciar F11

Branch: `development`. Último commit del redesign: el commit F10 en `development`.

Ratchet `copilot → módulo`: **22 frozen**. Anchor budget: **34/36** (2 anchors libres).
Suite F0-F10: ~3112 verde + 4 skipped. Flakies aislados confirmados ortogonales.

---

## Tareas concretas (ordenadas por valor)

### 1. Wire `build_default_router` al chat orchestrator

**Por qué:** F8 dejó factory + admin page; F9 NO lo wireó. El admin
`/copilot-routing` muestra "Sin decisiones de routing" porque
`copilot_routing_log` queda vacío en producción. Esto invalida la value
prop del page.

**Archivos:**
- `backend/src/modules/copilot/application/orchestrator/chat.py` —
  llamar `router.select(req)` antes del graph stream + persistir vía
  `RoutingLogRepository`.
- `backend/tests/modules/copilot/test_chat_router_integration.py` —
  test que verifica que cada turn dispara una row en
  `copilot_routing_log`.

**Criterio de hecho:** admin Streamlit `/copilot-routing` muestra rows
reales después de un turn de prueba.

---

### 2. Cutover `procedure_state` → `workflow_state`

**Por qué:** F6 dejó dual-read fallback (`get_workflow_state(...,
fallback_to_procedure=True)`). Hoy el orchestrator chat sigue
consumiendo `procedure_state` para guided/procedure runners. Mientras
ese flujo siga, F6 no termina de aterrizar.

**Archivos:**
- `backend/src/modules/copilot/application/orchestrator/chat.py` +
  `application/guided/*` + `application/procedures/*` — leer/escribir
  `workflow_state` cuando aplique.
- `backend/alembic/versions/0XX_drop_procedure_state.py` — migration
  que dropea la columna legacy (idempotente con `IF EXISTS`).
- Script transformación batch para conversaciones legacy si necesario
  (F6 documentó que el shape `procedure_state` es libre).

**Criterio de hecho:** `procedure_state` borrada de DB, `workflow_state`
es la única fuente, todos los goldens F0-F10 verde.

**Nota:** alta superficie. Si scope creep — split en 2-3 fases F11a/F11b/F11c.

---

### 3. Fix flakies heredados

**Por qué:** `test_streaming_integration` (F0+) + `test_editable_fields_ssot::test_no_cross_domain_duplicates` (F3+) son order-dep con pytest-randomly. Cada fase del redesign los aisló con `--ignore`. Es technical debt acumulada.

**Archivos:**
- `backend/tests/modules/copilot/test_streaming_integration.py` —
  identificar el state-leak source. F2 learnings sugieren:
  `LeadModel→TenantModel` lazy fail cuando algún test posterior
  commitea sin haber importado TenantModel.
- `backend/tests/architecture/test_editable_fields_ssot.py` —
  identificar la order-dep en seed.

**Criterio de hecho:** `pytest -p randomly --randomly-seed=last -x -q`
sobre suite full pasa 5 corridas seguidas con seeds aleatorias distintas.

---

### 4. Drop legacy KB residue

**Por qué:** F10 dejó `infrastructure/knowledge/vector_store.py` +
`application/services/knowledge_ingestion.py` legacy intactos como
"redirección suave" del refactor. Hoy NO los usa nadie (verificable con
grep) — son confusion debt.

**Archivos:**
- `backend/src/modules/copilot/infrastructure/knowledge/` (dir) — borrar.
- `backend/src/modules/copilot/application/services/knowledge_ingestion.py` — borrar.
- Verificar no hay imports residuales: `grep -r CopilotKnowledgeStore backend/src/`.
- Drop collection `copilot_knowledge` en Qdrant productivo (manual, runbook).

**Criterio de hecho:** árbol limpio + collection `copilot_knowledge`
eliminada de Qdrant prod.

---

### 5. Real-LLM weekly RAG eval cron

**Por qué:** F10 dejó goldens RAG + judge stub default. El weekly cron
F9 evalúa conversaciones (`weekly_copilot_quality_eval`). NO evalúa
RAG goldens. Sin telemetría real, regresiones de retrieval pasan
desapercibidas.

**Archivos:**
- `backend/src/shared/workers/copilot_rag_eval.py` (nuevo) — siguiendo
  patrón `copilot_quality_eval.py`. Corre `RUN_LLM_JUDGE=1` sobre los
  RAG goldens, persiste en `copilot_workflow_metric.extra_metadata` con
  shape `{retrieval_recall, kb_citations, retrieval_latency_ms}`.
- `backend/src/shared/workers/scheduler.py` — agregar al `cron_jobs`
  array. Sugerencia: lunes 06:00 UTC (1h después del `weekly_quality_eval`
  para evitar load spike).
- `backend/src/admin/modules/copilot_quality.py` — agregar tab "RAG
  retrieval" leyendo `extra_metadata->>'retrieval_recall'`.

**Criterio de hecho:** primer lunes post-deploy, admin muestra rows
reales con scores; cost OpenAI estimado <$0.10/run.

---

## Reglas de F11

- **Anchor budget:** 34/36 al cierre F10. Si F11 introduce nuevos
  anchors, cabe 2 sin bump. >2 requiere bump explícito de
  `tests/architecture/test_copilot_anchors.py:90`.
- **Ratchet `copilot → módulo`:** 22 frozen. Cualquier cleanup que
  shrinkee es bienvenido (e.g. migrar `offer_section_tools.py` o
  `crm_tools.py` a sus providers).
- **§3 sigue intocable.** F11 NO toca SSE v2 / cards / multimodal.
- **Spanish neutro LatAm** sigue obligatorio (regla 11).
- **TDD obligatorio** (regla 13).
- **Native dev tools** (NUNCA `docker exec` para lint/tests).
- **Stage por nombre** (parallel-safety).
- **Branch único `development`**.

---

## Cierre F11

Cuando F11 termine (sea con las 5 tareas o con un subset), generar
`learnings/F11-housekeeping.md` siguiendo el template — útil, no
plantilla rellenada.

Si F11 cierra sin agregar features visibles al user, mencionarlo
explícito al usuario: "el plan F0–F10 ya estaba cerrado; F11 es deuda
técnica que mejora estabilidad y observabilidad pero no agrega
capability nueva al copilot".
