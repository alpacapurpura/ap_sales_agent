# Learnings — F11 Housekeeping post-Redesign 2026-04

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `4ed279f4`)

---

## Resumen 3 líneas

- F11 cierra **4 de las 5 deudas heredadas** del plan F0-F10: drop legacy KB residue (`infrastructure/knowledge/`, `application/services/knowledge_ingestion.py` borrados; admin `home_dashboard.py` swap a `MarketingKbStore`); `build_default_router` wireado al chat orchestrator (`copilot_routing_log` ahora se popula por turn — admin `/copilot-routing` recibe data real); weekly `weekly_copilot_rag_eval` ARQ task (lunes 06:00 UTC) que evalúa los 8 RAG goldens contra el KB curado y persiste recall + latencia + judge multi-dim en `copilot_workflow_metric.extra_metadata`; fix definitivo del flaky `test_no_cross_domain_duplicates` (synthetic modules `test_module_fixture` + `test_find` pollutaban `_MODULE_CONTRACTS` con paths duplicados — agregada `teardown_module` que limpia ambos registries).
- Decisión no obvia: **F11.2 cutover `procedure_state` → `workflow_state` queda diferido a F12 dedicado** con plan estructurado en 3 sub-fases (`docs/domains/copilot/redesign-2026-04/phases/F12-procedure-state-cutover.md`). Razón: 9+ archivos en 4 sistemas paralelos (guided/extraction/orchestrator/tools) escribiendo a `procedure_state` con shape libre — riesgo de regresión durante cutover incompatible con scope de housekeeping atómico. F12 separa dual-write (F12a) → switch read path (F12b) → drop column (F12c) con quality gate por sub-fase.
- `test_streaming_integration` flaky NO se pudo reproducir tras F11.4-F11.5; standalone PASS en todas las corridas. Fix sin reproducer = adivinar — documentado como riesgo abierto. Anchor budget: 36/36 con 2 nuevos (`COPILOT-ROUTING-WIRE-F11`, `COPILOT-RAG-EVAL-F11`) — hit el cap.

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **F11.2 (cutover procedure_state) diferido a F12 con plan separado.** | El prompt F11 explicita "alta superficie. Si scope creep — split en 2-3 fases F11a/b/c". 9+ archivos en 4 sistemas paralelos + dual-read fallback existente + drop migration + backfill batch script = riesgo de breakage de conversaciones live durante cutover. Split en 3 sub-fases (F12a dual-write → F12b read switch → F12c drop) permite rollback granular por sub-fase. | Hacer cutover en F11. Bundling con F11.4/F11.1/F11.5 expone toda la deuda heredada al mismo riesgo de regresión + dificulta diagnóstico si la suite full falla. |
| **`build_default_router()` invocado como **telemetría únicamente**, NO swap del modelo bound al graph.** | F11.1 prompt: "Sin esto, `copilot_routing_log` queda vacío en producción. Esto invalida la value prop del page". El gap actual = falta de data en admin Streamlit; la decisión NO es promover el tier seleccionado al `LLMFactory.get_service().get_client(...)` que el deep_agent usa. Esa promoción cambia comportamiento — F-pos que mida costo/calidad por tier antes. | Wire end-to-end (router decide → swap LLMFactory). Cambia comportamiento productivo en F11 sin baseline de comparación. F8 ya dejó hooks de cache_hit_rate; mejor medir un trimestre antes de cambiar. |
| **Lazy module singleton (`_DEFAULT_ROUTER_CELL: list[ModelRouter]`) en lugar de `global` o instance per request.** | Constructor cheap pero resuelve `LLMFactory` en el path de NANO settings — no queremos pagar al boot. Singleton elimina costo per-request. List-as-cell evita PLW0603 sin perder lazy init (heredado patrón que ruff prefiere over `global`). | `global _DEFAULT_ROUTER` con `if None: build`. Funciona pero ruff bloquea + obliga `# noqa`. Alternativa per-request: 1ms de construcción pero al hacer 100 conversations/min suma sin razón. |
| **F11.5 RAG eval persiste row con `tenant_id = UUID(int=0)` (sentinel) + `workflow_id = "_rag_eval"`.** | `copilot_workflow_metric.tenant_id` es `nullable=False`. RAG corpus es global cross-tenant, no hay tenant real al que asociar. UUID nil es la convención; el sentinel marca "no aplica" sin requerir migration que añada `nullable=True`. | `nullable=True` migration. Mejor mantener invariant tenant_id obligatorio + sentinel explícito que dilatar el shape para un caso edge. |
| **`RagGolden` + `RAG_GOLDENS` extraídos a `src/modules/copilot/application/observability/rag_goldens.py`.** | F11.5 cron necesita iterar el corpus desde production code. Importar de `tests/quality/golden/test_rag_retrieval.py` cruza la línea src→tests (anti-pattern + arch test prohibe). Mover a src/ + re-exportar via test mantiene SSoT. | Duplicar los goldens en src/. Drift garantizado: dos fuentes a mantener. Importar desde tests/ en src/. Production code dependiendo de tests = arch violation. |
| **Per-golden failure isolation en F11.5 (try/except por golden, no per-run).** | Single golden con bug de chunk shape NO debe matar la corrida entera (perdiendo telemetría de los 7 OK). Patrón heredado F9 quality eval: `_judge_sample` log-and-skip por turn. Aggregate emite `failed_golden_ids` en metadata para diagnóstico. | Failure per-run con re-raise. Una corrida "envenenada" por un golden = data loss del resto + alerta confusa en admin. |
| **Cron lunes 06:00 UTC (1h después del quality eval).** | F11 prompt: "1h después del weekly_quality_eval para evitar load spike". NANO API rate limits + Qdrant load + log volume picos. Bunchear ambos eval en un slot único = riesgo de timeouts cascade. 1h gap es suficiente para que el quality eval termine (50 conv * 1 NANO call ≈ 30s típico). | Mismo slot 05:00 UTC. Stack de carga sin razón. Slot late (e.g. 23:00 UTC) sin baseline de cuánto tarda el RAG eval; 06:00 mantiene la cadena weekly visible al primer review del lunes. |
| **F11.3 fix solo via `teardown_module` (no autouse fixture global).** | El bug es claramente local a `test_field_contract_platform.py` — no necesita un fixture cross-suite. Un autouse en conftest agrega overhead a cada test del proyecto (~1500). Local teardown es: scope-correct + zero overhead + grep-discoverable. | Conftest fixture global. Más invasivo + el cleanup correría en tests que no necesitan el reset. |
| **Limpiar BOTH `_MODULE_CONTRACTS` AND `editable_fields._CATALOGS` en teardown.** | `_CATALOGS` cachea projecciones derivadas. Sin clear ahí, futuras llamadas a `get_catalog("test_module_fixture")` siguen retornando el catalog cacheado aún después de `register_module_contracts(..., ())`. Verificado en repro manual (`FAIL_BEFORE_TEARDOWN`/`AFTER_TEARDOWN`). | Solo limpiar `_MODULE_CONTRACTS`. Funciona standalone pero NO funciona si algún test entre el populate y el cleanup llamó `get_catalog` (caso real bajo pytest-randomly). |

---

## Sorpresas / gotchas (críticos, no triviales)

- **`test_no_cross_domain_duplicates` flaky raíz: `test_field_contract_platform.py` registra 2 modules sintéticos (`test_module_fixture`, `test_find`) con misma path `"x"` y NO limpia `_MODULE_CONTRACTS`.** Bajo pytest-randomly, si se ejecuta antes del arch test, los 2 modules sintéticos aparecen en `get_registered_domains()` y la asserción de duplicados cross-domain ve `path="x" en test_module_fixture y test_find` → FAIL. F0-F10 documentaron como "flaky heredado" sin diagnosticar la causa. Reproducción 100% determinística mostrada en F11 con script:
  ```python
  register_module_contracts("test_module_fixture", (FieldContract(path="x", ...),))
  register_module_contracts("test_find", (FieldContract(path="x", ...),))
  # Después: get_catalog("test_module_fixture") → walk + hit duplicate vs test_find.
  ```
  Fix definitivo: `teardown_module` que limpia ambos registries (`_MODULE_CONTRACTS` + `editable_fields._CATALOGS`).

- **`test_streaming_integration` NO reproducido bajo F11.** Heredado F0-F10. Standalone PASS (26/26) post-F11. Combined runs (~30 tests con random seed 999) PASS. Sin reproducer determinístico no se puede fix. Hipótesis abiertas: (a) algún test con MagicMock leak entre `ConversationRepository.get_by_id` y `Repo.create` returns; (b) state-leak en `LLMFactory` cuando algún test previo monkeypatcha. F12 puede investigar con strace de imports + bisect del seed.

- **`MarketingKbStore` NO tiene método `list_documents` pero `CopilotKnowledgeStore` sí.** El admin home_dashboard usaba `store.get_collection_stats()` solo — refactor swap a `MarketingKbStore.stats()` directa. Si futuro admin necesita `list_documents` (e.g. browse curated docs), agregar `list_sources()` al MarketingKbStore (ya existe — devuelve `[{source_doc, chunks, category, methodology, domain}]`).

- **`tests/admin/conftest.py` autouse fixture monkeypatcha por path string.** Si el path no existe (e.g. F11.4 borró el módulo legacy), monkeypatch importa lazy → si la importación falla, TODOS los admin tests erroran en setup. F11.4 verificado funcionando: cero refs a `CopilotKnowledgeStore` queda + fixture redirigido a `MarketingKbStore`. Lección replicable: cualquier dropping de modulos requiere grep verboso EN tests, NO solo en src.

- **`pg_insert.excluded` con SQLite test DB devuelve diferente shape que en PostgreSQL.** F11.5 test usa SQLite in-memory; el `repo.upsert` con `extra_metadata=dict` se persiste como `JSON` (text). Postgres prod lo persiste como `JSONB`. Comportamiento equivalente en query path; diferencia surgiría si algún día queremos query-by-jsonpath sobre extra_metadata desde admin queries (Postgres OK, SQLite no).

- **Anchor budget hit cap: 36/36 con F11.** `test_copilot_anchors.py:96` cap `<= 36`. F11 agregó `COPILOT-ROUTING-WIRE-F11` + `COPILOT-RAG-EVAL-F11` → exactamente 36. F12 que agregue 1+ anchor REQUIERE bumpear el cap (`assert len(ANCHOR_REGISTRY) <= 38` o más). No bumpé profilácticamente — fail explícito da señal de "agregaste anchor sin actualizar registry".

- **`get_tools_for_context` se llama 2x por turn ahora** (F11.1 — una para routing, una para deep_agent build). Costo: ~10ms × 2 = 20ms (pure Python). Si futuro perf push lo flagea, cache el resultado en el state dict y leerlo del state en `build_deep_agent_graph`. Hoy es noise vs LLM call latencia (~500-2000ms).

- **F11.4 admin smoke tests pass standalone PERO 54 errors aparecieron en baseline pre-F11.1 con seed 4176249700.** Reproducción tras F11.1: combined run (`tests/admin/ + tests/modules/copilot/`) PASS 1215/1215. La conclusión: las 54 errors NO son F11-introducidas. Probablemente order-dep distinto. La trace truncada en pytest -q + tail -50 no muestra el actual ImportError. Hipótesis: bug pytest-randomly + autouse fixture importando un módulo que otro test deletea. Sin reproducer determinístico, F12 puede investigar.

- **Format ruff vs línea 120 cols con dict comprehension.** El auto-format reformateó `judge_dim_avg = {dim: round(...) for dim, scores in dim_totals.items()}` con `\n` agresivo en F11.5. Ya está OK pero tener cuidado con dict comprehensions largas: si pasan los 120, ruff format los rompe en posiciones a veces ilegibles.

---

## Recomendaciones accionables para F12 (cutover procedure_state) y futuras fases

1. **Antes de empezar F12:** correr la suite F0-F11 baseline (~3057 + 14 + 6 ≈ 3077 verde, sin contar flakies):
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/ tests/architecture/ tests/admin/ \
     tests/modules/brand/ tests/modules/offer/ tests/modules/crm/ \
     tests/shared/ tests/quality/ tests/scripts/ tests/api/ \
     -q -o addopts="" --timeout=120 \
     --ignore=tests/modules/copilot/test_streaming_integration.py
   ```
   Flaky aislado:
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/test_streaming_integration.py \
     -q -o addopts=""
   ```
   `test_editable_fields_ssot` ya NO requiere ignore — fix de F11.3 confirmado.

2. **F12 debe seguir el plan en `docs/domains/copilot/redesign-2026-04/phases/F12-procedure-state-cutover.md`.** 3 sub-fases. Cada una mergeable independiente. F12c (drop column) NO debe ejecutarse hasta confirmar zero-write desde producción real ≥1 semana.

3. **F12 que agregue anchor `[COPILOT-WORKFLOW-CUTOVER-F12]`** (o similar) DEBE bumpear cap en `tests/architecture/test_copilot_anchors.py:96`. Sugerencia: bump a 40 para dar margen a F13+.

4. **`build_default_router` está module-singleton via `_DEFAULT_ROUTER_CELL`.** F12 que necesite swap del router para tests puede pasar `router=` explícito a `_record_routing_decision`. Producción usa el singleton.

5. **F11.5 cron poblará `copilot_workflow_metric` con `tenant_id=UUID(int=0)` + `workflow_id="_rag_eval"`.** Admin queries que filtran por tenant_id real DEBEN excluir el sentinel: `WHERE tenant_id != '00000000-0000-0000-0000-000000000000'` o similar. El `_fetch_workflow_kpis` actual NO filtra — F-pos de admin que muestre KPIs por tenant debe agregar el filter.

6. **`MarketingKbStore.stats()` accept network failure silently** (returns `{collection, error}`). F12 admin dashboard que confíe en `kb_docs` debe handle el caso `kb_docs == "?"` (heredado del path home_dashboard).

7. **F11.3 NO touched `test_streaming_integration`.** F12 puede investigar reproduciendo con `pytest --collect-only -q | shuf` para encontrar el order que falla, luego bisect.

8. **Drop legacy KB collection `copilot_knowledge` en Qdrant prod (manual runbook):** F11.4 borró código local pero la collection en Qdrant sigue dangling. Comando:
   ```bash
   ssh ... 'docker exec visionarias_qdrant curl -X DELETE http://localhost:6333/collections/copilot_knowledge'
   ```
   F12 NO necesita esto a menos que el dashboard muestre stats inconsistentes. Low risk.

9. **Variable `_DEFAULT_ROUTER_CELL` es shared cross-test si los tests no la resetean.** Si F12 introduce tests que monkeypatch `build_default_router`, el cell preserva la instancia OLD entre tests. Hook: `chat._DEFAULT_ROUTER_CELL.clear()` antes de cada test que dependa de un router diferente. O usar `router=` injection (preferido).

---

## Riesgos abiertos

- **`test_streaming_integration` order-dep no resuelto.** Heredado F0+. Sin reproducer determinístico tras F11. Riesgo: bajo — el test pasa standalone, NO bloquea CI cuando se aísla. Alto si futuro change touch streaming protocol y el flaky enmascara una regresión real.

- **`copilot_routing_log` puede crecer rápido.** F11.1 wire = 1 row por turn. ~100k turns/mes en producción ya = 100k rows. La tabla NO tiene job de cleanup. F12 considerar `cleanup_old_events`-style worker que dropea rows >90 días.

- **`weekly_copilot_rag_eval` real-LLM en NANO sin probar en producción.** Stub mode (CI default) verifica el pipeline; real NANO solo corre el primer lunes post-deploy. Si OpenAI throttle / NANO API cambia silenciosamente, el ARQ task swallow + log → admin shows "Sin runs". Mitigación: revisar logs del ARQ worker primer lunes (`grep "copilot_rag_eval_complete"`).

- **F11.2 cutover diferido = `procedure_state` JSONB sigue siendo SSoT live + `workflow_state` solo poblado vía F6 backfill (no live escritos).** Riesgo: cualquier conversación NUEVA post-F6 pero pre-F12 tiene `workflow_state IS NULL` (nadie escribe). El fallback `fallback_to_procedure=True` cubre la lectura. Riesgo materializa si F-pos que asume workflow_state populated se ejecuta antes de F12b.

- **Anchor budget exhausto.** F12 + F13 requieren bump del cap de 36. Olvido = test fail al primer anchor nuevo.

- **F11.5 sentinel tenant collision.** Si ALGÚN tenant productivo tiene UUID(int=0) (improbable, generan UUID4), F11.5 row se mezcla con sus métricas. Defensa: UUID v4 collision con int=0 = ~0%. Si paranoid, F-pos puede usar UUID(int=1) reservado o hash determinístico.

---

## Hooks listos para próximas fases

- `backend/src/modules/copilot/application/orchestrator/chat.py::CopilotOrchestrator._record_routing_decision(..., router=None)` — injectable para tests, default singleton. F12 que cambie behaviour del routing (e.g. promover el tier al LLMFactory) modifica este helper.

- `backend/src/modules/copilot/application/orchestrator/chat.py::_get_default_router()` — module singleton lazy. Reusable desde otros call sites del orchestrator si F-pos necesita decisiones de routing antes/después del chat (e.g. async post-turn analytics).

- `backend/src/modules/copilot/application/observability/rag_goldens.py::RAG_GOLDENS` — frozenset de goldens. Agregar `RagGolden(...)` actualiza tanto el test runner como el cron sin tocar nada más. SSoT del corpus.

- `backend/src/shared/workers/copilot_rag_eval.py::run_weekly_rag_eval(db, *, store=, judge=, goldens=)` — sync entry point. F-pos puede llamar manualmente desde admin button (siguiendo patrón `run_weekly_quality_eval`) o pasar subset via `goldens=`.

- `backend/src/admin/modules/copilot_quality.py::_render_rag_eval_section(rag_row)` — render presentacional aislado. F-pos puede crear dashboard separado leyendo el mismo `_fetch_latest_rag_eval`.

- `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY` — 36/36 con F11. F12 necesita bumpear `assert len(...) <= 36` antes de agregar anchor nuevo.

- `tests/shared/test_field_contract_platform.py::teardown_module` — patrón replicable para cualquier futuro test que mutate `_MODULE_CONTRACTS` o `_CATALOGS`. F12 que agregue tests mutating contracts debe replicar.

- `docs/domains/copilot/redesign-2026-04/phases/F12-procedure-state-cutover.md` — plan completo F12 con 3 sub-fases. Listo para iniciar.

---

## Fuentes research útiles

- Ninguna research nueva fue necesaria — F11 reusó patrones cementados en F8 (router factory), F9 (quality eval ARQ + JSONB upsert + judge multi-dim), F10 (KB store + RAG goldens). Tessl tiles consultados: ninguno (todo el stack ya documentado en F0-F10 learnings).

- F8 learnings (`learnings/F8-routing.md`) — re-leídas para diseñar el wire de routing telemetry. Confirmaron que `cache_hit_rate` instrumentation existe pero el router NO está wired (F11.1 cierra ese gap).

- F9 learnings (`learnings/F9-quality.md`) — re-leídas para `weekly_*_eval` ARQ pattern + stub default + opt-in real LLM. F11.5 mirror exacto del patrón.

- F10 learnings (`learnings/F10-marketing-kb.md`) — re-leídas para `MarketingKbStore.stats()` + decisión de drop legacy KB. Recomendación 2 ("Drop collection `copilot_knowledge` legacy") y 3 ("Borrar `infrastructure/knowledge/` + `knowledge_ingestion.py`") ejecutadas en F11.4.

- F6 learnings (`learnings/F6-workflow-unification.md`) — re-leídas para diseñar el plan F12. Confirmaron dual-read fallback ya activado + migration backfill ya ejecutada — F12 solo necesita switch read path + drop column.
