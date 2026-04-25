# Learnings — F3 Brand summary lighthouse

**Fecha cierre:** 2026-04-25 · **Modelo:** Claude Opus 4.7 (1M context) · **Branch:** `development @ <ver git log -1>` (parent `d9557ab7`)

---

## Resumen 3 líneas

- Tabla `brand_summary` (PK tenant_id, ≤800 chars, version+model_used+last_section_changed) + ARQ task `regen_brand_summary` con dedupe `_job_id` + debounce 30s. `BrandRepository.save_settings` emite `BrandSectionUpdatedEvent` después del commit (after-commit listener); handler async encola la regen. Judge sync (length cap + 100-token voseo regex) bloquea voseo antes del UPSERT, retry una vez con suffix estricto.
- Hook único de inyección = `build_system_prompt(state)` en `graph.py`. Aggregator nuevo `_collect_context_injectors_prefix` itera todos los providers descubiertos y prepende fragmentos como **prefix cacheable** (ANTES del base prompt). El sufijo deep-agent F2 sigue al final → orden: `lighthouse → completion_snapshot/behavior/guided/studio → deep-agent suffix`.
- Modelo + repo viven en `brand/` (no `copilot/`), porque brand-summary es un cache derivado de brand → DDD inside-out preservado, ratchet `copilot → módulo` queda en 22 entradas (sin shrink, sin grow).

---

## Decisiones clave

| Decisión | Razón | Alternativa descartada |
|---|---|---|
| **Modelo + repo en `brand/`, no `copilot/`.** | brand_summary es cache derivado de brand. Ponerlo en copilot/ generó violación DDD (`brand → copilot` import en summary.py). Mover invierte la dirección — solo `shared/workers/brand_summary_regen.py` toca ambos módulos, lo cual es legal (shared es fan-in libre). | Allowlist en `KNOWN_CROSS_MODULE_IMPORTS` para `brand → copilot`. Habría diluido la señal del ratchet y fijado el patrón inverso ("módulo importa cache que vive en otro módulo"). |
| **`pg_insert.on_conflict_do_update` en upsert** con `index_elements=["tenant_id"]`. | Heredado de gotcha F2 documentado. SQLite test conftest no entiende `ON CONFLICT (constraint_name)` — `index_elements` genera `ON CONFLICT (col)` portable. Aplica a TODO upsert PG nuevo. | `constraint="brand_summary_pkey"`. Funciona en PG, rompe los tests con `IntegrityError: ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE constraint`. |
| **EventBus existente, no broker externo.** | `src/shared/domain/events.py::EventBus` ya tenía dispatch after-commit via SQLAlchemy listener + handler exception isolation. Reusar = cero infra nueva. | `fastapi-events` o Kafka. Para una fan-out single-event single-consumer es overkill; cualquier disco rota antes de que escale el bus actual. |
| **Debounce + dedupe en `_job_id` + `_defer_by`, no Redis SETNX.** | ARQ rechaza nuevo enqueue mientras un job con el mismo `_job_id` esté queued/running, y `_defer_by=30` colapsa flurry-saves. La feature ya está en arq 0.27.0 — sin lock-per-tenant manual. | Redis SETNX con TTL en el handler. Habría duplicado lo que ya enforce ARQ a nivel queue, con doble race condition (lock-then-enqueue). |
| **Judge sync con regex voseo, NO LLM-judge segundo pase.** | Length + voseo son chequeos puramente sintácticos; un segundo LLM call es lento y caro para reglas que un regex resuelve en microsegundos. Regla 11 de CLAUDE.md (Spanish neutro) define el glosario, lo traduje 1:1. | LLM-judge con `gpt-4o-mini` validando "does this match brand voice?". Habría duplicado el costo de la regen y agregado dependency en LLM availability para una validación que NO es semántica. F-pos puede agregar judge semántico si surge necesidad. |
| **Aggregator `_collect_context_injectors_prefix` antes del base prompt, no en `_build_combined_system_prompt` del harness.** | F2 learnings recomendaron explícitamente: inyectar en `build_system_prompt` para cubrir legacy + harness con un único punto. Si lo hubiera hecho en deep_agent.py, las requests con flag OFF (default) no verían el lighthouse. | Inyectar en deep_agent.py wrapper. Cobertura solo cuando flag está ON; prefix cacheable no se sostiene en el legacy path. |
| **`_await_sync` con ThreadPoolExecutor para correr awaitables desde sync.** | `build_system_prompt` es sync (lo llama `agent_node` legacy y `_build_combined_system_prompt` deep-agent), pero `ContextInjector.inject_for` es async (F4+ va a hacer fan-out a la red). Cuando la sync function se ejecuta dentro de un loop activo (FastAPI request) `asyncio.run` rompe; el executor cumple sin reescribir todo el orchestrator a async. | Reescribir `build_system_prompt` a async. Requería propagar await a `agent_node` + el harness y revisar cada test con golden snapshot. ROI bajo para F3; la complejidad real está en F4/F5. |
| **`db_factory` en ARQ ctx, no SessionLocal directo dentro del task.** | El patrón ya existe en F0 (`brand/workers/tasks.py::run_brand_extraction`). Worker startup setea `ctx["db_factory"] = SessionLocal`; el task abre/cierra session. Garantiza cleanup en errores y test friendly. | Llamar `SessionLocal()` dentro del task. Funciona pero replicar el patrón ahorra "por qué este task no cierra la session?" como riesgo en F-pos. |

---

## Sorpresas / gotchas (críticos, no triviales)

- **structlog reserva el kwarg `event`.** Loggear `logger.info("brand_summary_event_handlers_registered", event="brand_section_updated")` revienta con `TypeError: meth() got multiple values for argument 'event'`. Usar `event_name=`. Vale para CUALQUIER fase futura que loguee structlog con un campo "event" — está documentado pero fácil de perder.

- **`N999 Invalid module name` para slugs admin con guión.** Ruff exige nombres válidos como módulo Python (`[a-z_][a-z0-9_]*`). Pero los slugs Streamlit usan kebab-case (`brand-summaries`) por el contrato `slug == file stem` que enforce `tests/admin/test_admin_contract.py`. Solución: agregué `"N999"` al per-file ignore `"src/admin/**/*.py"` en `pyproject.toml`. Cualquier nuevo admin con slug multi-palabra pega el mismo error.

- **`build_system_prompt` abre `SessionLocal()` dentro de `_get_completion_snapshot` y `_get_behavior_summary`.** Los tests en F0/F1/F2 stubean el prompt entero precisamente por esto. F3 necesita el prompt REAL para verificar el orden de fragmentos, así que tests stubean los helpers DB-touching individuales. Si futuras fases agregan más helpers DB, deben monkeypatchearlos también o el test cuelga 30s en Postgres timeout.

- **Test `tests/architecture/test_editable_fields_ssot.py::test_no_cross_domain_duplicates` flaquea con pytest-randomly.** Standalone PASS, dentro de la suite full FAIL. NO causado por F3 — orden de seed dep. Heredado, anotar en `docs/mejoras-proceso/to-do.md` (junto al flake F2 de `test_streaming_integration`). F4 que toque `editable_fields` debe correr aislado primero.

- **Modelos nuevos en conftest.py no son opcionales.** Confirmado de F2: si no agregás `BrandSummaryModel` a la lista de imports en `tests/conftest.py::db_engine`, el test del repo pasa standalone pero la suite full puede fallar por mappers config (`LeadModel→TenantModel` lazy fail). Agregué la fila — sin ella el bug es invisible hasta que un test posterior commitea.

- **Brand `save_settings` ya hacía `db.commit()` internamente.** El after-commit listener de EventBus se registra ANTES del commit y dispara una vez (`once=True`). Si una fase futura mueve la commit fuera del repo (UoW pattern), el listener tendrá que moverse con ella o nunca dispara.

---

## Recomendaciones accionables para F4

1. **Antes de empezar:** correr la suite F0-F3:
   ```bash
   cd backend && .venv/bin/pytest \
     tests/modules/copilot/golden/ \
     tests/architecture/test_copilot_provider_compliance.py \
     tests/architecture/test_no_new_copilot_module_imports.py \
     tests/architecture/test_copilot_anchors.py \
     tests/architecture/test_deep_agent_harness_invariants.py \
     tests/architecture/test_ddd_boundaries.py \
     tests/modules/copilot/test_deep_agent_harness.py \
     tests/modules/copilot/test_plan_card_emission.py \
     tests/modules/copilot/test_pinned_memory_repository.py \
     tests/modules/brand/test_brand_summary_repository.py \
     tests/modules/brand/test_brand_section_updated_event.py \
     tests/modules/brand/test_brand_context_injector.py \
     tests/shared/workers/test_brand_summary_regen.py \
     tests/shared/application/test_brand_summary_event_handlers.py \
     tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
     -q -o addopts="" --timeout=30
   ```
   Debe ser ~120 verde antes de tocar nada.

2. **F4 inserta inspirations al system prompt — inyectarlas como segundo `ContextInjector`, no rehacer el aggregator.** El hook `_collect_context_injectors_prefix` ya itera todos los providers descubiertos. Crear `landing/copilot_provider/context_inject.py` (o el módulo dueño) y devolver el bloque "Inspiraciones cargadas" desde `inject_for` cuando aplique. Aparece automáticamente en orden post-brand_lighthouse, sin tocar `graph.py`.

3. **`pin_to_memory` tool puede usar el repo F2 directo.** `CopilotPinnedMemoryRepository` está completo (CRUD + tenant isolation). F4 sólo construye el path final y llama `repo.upsert(tenant_id=..., user_id=..., path="/memories/...")`. Tenant_id/user_id de contextvars (igual que el resto de tools).

4. **El judge `judge_summary` es reusable.** Si F4 escribe una scratchpad note user-facing, el regex voseo + cap chars sirve igual. Importarlo desde `src.shared.workers.brand_summary_regen` o promover a `shared/domain/spanish_neutro_judge.py` cuando F5 también lo pida (no preemptivo).

5. **El `BrandContextInjector` tiene allowlist hardcoded** (`offer-studio/landing/campaign/sales/growth-studio`). F4 no necesita tocarlo, pero si una fase posterior agrega "campaign-studio" como ruta separada, sumar el segmento ahí — está como `INJECTION_SEGMENTS` constante de clase, fácil de extender.

6. **Si F4 introduce un nuevo `[COPILOT-*]` anchor**, agregarlo a `tests/architecture/test_copilot_anchors.py::ANCHOR_REGISTRY`. Límite 25; F3 dejó 22 con `COPILOT-BRAND-SUMMARY-F3`.

7. **No registrar el handler dos veces.** `register_brand_summary_event_handlers()` es idempotente, pero la API levanta los handlers en `main.py::register_event_handlers` Y los workers en `WorkerSettings.on_startup` Y `SchedulerSettings.on_startup`. Un proceso = una llamada. F4 que agregue handler nuevo: replicar el patrón "if handler in EventBus._handlers.get(...)" para evitar dispatch doble.

---

## Riesgos abiertos

- **Cache hit rate del system prompt no medido todavía.** El orden actual (lighthouse → snapshot/behavior/guided → deep-agent suffix) está pensado para que la prefix cacheable arranque con el lighthouse (estable mientras el tenant no edite brand) y la parte volátil (snapshot) venga después. Pero la confirmación con `cache_creation_input_tokens` vs `cache_read_input_tokens` queda para F8 cuando la routing/cost optim baseline esté en su lugar. Si F4 agrega más fragmentos volátiles ANTES del snapshot, el cache hit puede caer; medir ANTES de mergear F4.

- **`BrandContextInjector` inyecta también en `growth-studio`** (no estaba explícito en el plan F3 §5.4). Lo agregué porque `growth-studio` aloja "campaña" semánticamente — el plan menciona `campaign` pero no exists ese segmento como ruta primaria; las campañas viven dentro de growth-studio. Si F4 introduce una ruta `/campaigns/...` separada, evaluar si el lighthouse también debería entrar ahí (probablemente sí — agregar a `INJECTION_SEGMENTS`).

- **Ratchet `copilot → módulo` frozen en 22 entradas, F3 no shrunk.** Esperado, F3 no migró nada al provider pattern. F-pos que mueva offer's `offer_section_tools.py` (5 imports a brand/scheduling/social_proof) podría shrink a ~17. No urgente.

- **El test flaky `test_editable_fields_ssot::test_no_cross_domain_duplicates` se suma al `test_streaming_integration` heredado de F0.** Dos órdenes-dep que rompen `--randomly`. Si F4 toca `editable_fields` o streaming, correr aislado primero. Anotado en `docs/mejoras-proceso/to-do.md` para arreglo en una fase de housekeeping.

- **Backfill no corrió en prod.** El script `backend/scripts/backfill_brand_summaries.py` está listo pero requiere ventana de mantenimiento porque hace una llamada LLM por tenant (FAST tier, ~$0.0005 cada uno). Para Visionarias y los <50 tenants actuales no es problema, pero documentarlo: cualquier fase que cuente con `brand_summary` poblado debe verificar `SELECT COUNT(*) FROM brand_summary` antes de asumir presencia.

---

## Hooks listos para próximas fases

- `backend/src/modules/brand/copilot_provider/context_inject.py::BrandContextInjector` — patrón completo de allowlist + summary fetch + format prefix. F4 puede instanciar el suyo (`landing/copilot_provider/context_inject.py`) imitando.
- `backend/src/modules/copilot/application/orchestrator/graph.py::_collect_context_injectors_prefix` — aggregator que itera providers descubiertos. Cualquier nuevo `ContextInjector` aparece automáticamente sin tocar `graph.py`.
- `backend/src/modules/copilot/application/orchestrator/graph.py::_await_sync` — utility runner para correr awaitables desde sync con detección de loop activo. F-pos que necesite mismo patrón puede importar.
- `backend/src/shared/workers/brand_summary_regen.py::judge_summary` — validador puro Spanish-neutro reusable.
- `backend/src/shared/application/brand_summary_event_handlers.py::register_brand_summary_event_handlers` — patrón idempotente subscribe (handler in EventBus._handlers.get + check). F4 que agregue subscribers debe seguirlo.
- `backend/src/shared/workers/brand_summary_regen.py::regen_brand_summary_sync(db, tenant_id, ...)` — primitive sync invocable desde admin Streamlit + backfill + ARQ task. F4 que necesite forzar regen post-cambio externo (e.g. URL contextual modifica voice) puede llamarlo.
- `backend/src/admin/pages/brand-summaries.py` + `backend/src/admin/modules/brand_summaries.py` — surface con manual regen. F4 que agregue inspections puede crear admin similar.

---

## Fuentes research útiles

- [arq 0.28.0 PyPI](https://pypi.org/project/arq/) — confirmé que el feature `_job_id` (dedupe) + `_defer_by` (debounce) ya está en 0.27.0 instalado, sin breaking change a 0.28.0. Decidió seguir con 0.27 (no upgrade gratuito).
- [OpenAI Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs) — confirmé que `response_format={"type": "json_schema", ...}` no es necesario aquí (la salida es texto plano para system prompt, no JSON). Decidió NO usar structured output — agregaba parsing innecesario.
- [LLM brand voice consistency 2026 Lakera](https://www.lakera.ai/blog/prompt-engineering-guide) — confirmó el patrón "few-shot + judge" es el estándar 2026 para brand voice. Lo apliqué con regex en lugar de LLM-judge para el cap mínimo (length + voseo). LLM-judge semántico queda para F-pos si surge demanda.
- Inspección directa de F2 learnings — el patrón `index_elements` vs `constraint=` en `pg_insert.on_conflict_do_update` ya estaba documentado, solo lo apliqué literal.

Tessl tiles consultados: `tessl__fastapi`, `tessl__pytest-api-testing`. No instalé tile nuevo — `arq` no está en el registry y `pydantic-settings` ya está cubierto en otras dependencias.
