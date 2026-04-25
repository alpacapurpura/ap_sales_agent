# F12 — Cutover `procedure_state` → `workflow_state` (planeada, no ejecutada en F11)

> **Estado:** plan listo, ejecución diferida.
> **Antecedente:** F11.2 inicial. Esta fase fue separada por superficie y riesgo.
> **Pre-lectura obligatoria:** `learnings/F6-workflow-unification.md`, `learnings/F11-housekeeping.md`.

---

## Por qué fue separada de F11

F11 housekeeping cerró 4 de las 5 deudas heredadas:
- F11.4 — drop legacy KB residue.
- F11.1 — wire `build_default_router` al chat orchestrator.
- F11.5 — weekly RAG eval cron.
- F11.3 (parcial) — fix de `test_no_cross_domain_duplicates`. `test_streaming_integration` flaky queda activo.

La 5ta tarea (F11.2 cutover) toca **9+ archivos de application** que viven en 4 sistemas paralelos:
- `application/guided/` (state.py + persistence.py + __init__.py)
- `application/extraction/` (active_job_state.py + active_job_persistence.py + extraction_tools.py)
- `application/orchestrator/` (chat.py + state.py)
- `application/tools/guided/__init__.py`

Cada uno escribe/lee `copilot_conversations.procedure_state` JSONB con shape **libre** (heredado pre-F6). Migrar requiere garantizar paridad de comportamiento — cualquier divergencia rompe conversaciones live.

El propio prompt F11 reconoce el riesgo:

> **Nota:** alta superficie. Si scope creep — split en 2-3 fases F11a/b/c.

F12 es esa fase dedicada.

---

## Estado actual (post-F11)

- F6 dejó `workflow_state` JSONB column (migration 071 idempotente) + backfill desde `procedure_state` + dual-read fallback en repo (`get_workflow_state(..., fallback_to_procedure=True)`).
- Ningún consumer de application/ usa `workflow_state` aún. Todos siguen escribiendo a `procedure_state`.
- Tests F0-F10 (~3057 verdes en baseline F11) ejecutan sobre el path `procedure_state` original — ningún test cubre el dual-read fallback en escritura.

---

## Plan F12 (split en 3 sub-fases)

### F12a — Dual-write en escritores (guided + extraction)

1. **Tests primero (TDD)**:
   - Para cada escritor (`guided/persistence.py`, `extraction/active_job_persistence.py`), test que verifica `workflow_state["guided"]` y `workflow_state["active_extraction_job"]` quedan poblados sincrónicamente con `procedure_state` legacy.
2. **Implementación**: cada `update_procedure_state(...)` también llama `update_workflow_state(...)` con la misma shape.
3. **Quality gate**: arch test que enforza dual-write en escritores marcados.
4. **Verificación funcional**: arrancar dev, levantar conversación con guided activo, ver fila DB con AMBAS columnas pobladas.

Riesgo: bajo. Solo agrega escritura, no cambia lectura. Rollback = revertir el segundo update.

### F12b — Switch read path orchestrator + runners a `workflow_state`

1. **Tests primero**: por cada lector (`chat.py::_read_procedure_state`, `guided/state.py::load_guided_state`, `extraction/active_job_state.py::load_active_job`), test que verifica resolver desde `workflow_state` cuando ambos están poblados.
2. **Implementación**:
   - `_read_procedure_state` → `_read_conversation_state` que lee `workflow_state` primero, fallback a `procedure_state` (mantener fallback durante esta sub-fase).
   - `load_guided_state(state)` y `load_active_job(state)` aceptan workflow_state shape.
3. **Migration backfill**: script ARQ one-shot que pasa `procedure_state → workflow_state` para conversaciones donde solo procedure_state está poblado (rows pre-dual-write).
4. **Goldens F0-F10 verde**.
5. **Verificación**: stop dual-write desde código nuevo (escribe solo `workflow_state`). Comprobar conversación nueva no popula `procedure_state`.

Riesgo: medio. Tocar leer state pero con fallback explícito mantiene compat.

### F12c — Drop `procedure_state` column

1. **Confirmar zero-write**: arch test bloquea cualquier import nuevo de `update_procedure_state`. Grep manual de `procedure_state` en `src/modules/copilot/application/` debe retornar cero.
2. **Migration drop**:
   ```sql
   ALTER TABLE copilot_conversations DROP COLUMN IF EXISTS procedure_state;
   ```
3. **Cleanup código**:
   - Eliminar `procedure_state` column del modelo + repo `update_procedure_state` + `_read_procedure_state` + `fallback_to_procedure` flag.
   - `get_workflow_state(..., fallback_to_procedure=True)` → `get_workflow_state(...)` simple.
4. **Eliminar `ProcedureState` value object** (`domain/procedure_state.py`) + port `update_procedure_state` (`domain/ports.py:167`).
5. **Goldens F0-F10 verde post-drop**.

Riesgo: alto pero contenido. Drop + zero-fallback debe estar precedido por F12b en producción mínimo 1 semana para confirmar zero-write desde producción real. Backfill pre-drop garantiza no perder data.

---

## Hooks listos

- `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py::update_workflow_state` — ya existe (F6).
- `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py::get_workflow_state(..., fallback_to_procedure=True)` — dual-read activado.
- F6 migration 071 — backfill ya corrido en cada DB.

---

## Cuándo abordar F12

- Cuando el roadmap de UX no requiera tocar copilot un sprint completo (riesgo de regresión durante cutover bloquea otras features).
- Cuando se priorice eliminar el dual-read fallback (F6 dijo F-pos absorbe; F11 confirmó necesidad).
- Cuando se quiera reducir blast radius de cualquier mutation accidental al `procedure_state` JSONB de shape libre.

Estimación esfuerzo: 8-12 horas reparteadas en 3 sub-fases con quality gate por cada una.

---

## Referencias

- `learnings/F6-workflow-unification.md` (introdujo dual-read).
- `learnings/F11-housekeeping.md` (confirmó scope diferido).
- `.claude/rules/backend-migrations.md` (idempotencia obligatoria).
- `tests/architecture/test_workflow_compliance.py` (5 fitness tests existentes).
