# Prompt — F6 Workflow unificado

> Copiar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F6 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: fusionar `guided` + `procedure` + `extraction_card_flow` en una sola clase declarativa `Workflow` registrada via provider, con estado en `copilot_conversations.workflow_state` (rename idempotente de `procedure_state`), discovery agregándolos automáticamente y UI sidebar mostrando progreso unificado.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§3 Workflow declarativo unificado)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F6-workflow-unification.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md
10. docs/domains/copilot/redesign-2026-04/learnings/F4-url-contextual-scratchpad.md
11. docs/domains/copilot/redesign-2026-04/learnings/F5-ask-tenant-data.md  ← APRENDIZAJES F5 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 2 queries del mandate F6):
    - "LangGraph workflow declarative state machine 2026 production patterns"
    - "guided workflow chatbot multi-step state persistence 2026"
  - Tessl tiles: `tessl__fastapi`, `tessl__langgraph`. Si surge tile workflow/state-machine relevante, evaluar instalar.
  - Confirmar versiones LangGraph 1.1.x interrupt + checkpointer patterns.

- **Foco — no scope creep.** F6 entrega UNA cosa: clase `Workflow` declarativa + migration rename `procedure_state → workflow_state` (idempotente) + provider port `WorkflowProvider.workflows()` poblado en al menos 2 módulos pilots (brand + offer) + UI sidebar mantiene compat. F7/F8 NO se mezclan.

- **Paso 4 — TDD obligatorio.**
  - Test por capa: dataclass `Workflow` + state machine engine + provider integration + migration idempotency + handler con state schema Pydantic.
  - Integration: workflow `design_offer_from_url` arranca → ejecuta nodos → guarda estado JSONB → reanuda en próximo turn.
  - Migration test: clone DB (Postgres) verificar `procedure_state → workflow_state` rename sin pérdida de datos.
  - Test invariante: provider sigue cumpliendo Protocol después de agregar `workflows()` real (no solo dummy).
  - Golden snapshots F1+F2+F3+F4+F5 verdes ANTES de empezar.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar cualquier cosa**: corré la baseline F0-F5 (~250+ tests). Debe ser verde (excepto los flaky heredados `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates`).
  - Después de cada bloque: ruff + golden + arch.
  - Si tocás streaming u orchestrator: correr `test_streaming_integration` aislado primero.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - Ratchet `copilot → módulo` sigue en 22 (o shrunk).
  - Anchor budget: 25/25 alcanzado en F5 — **F6 DEBE bumpear** `assert len(ANCHOR_REGISTRY) <= N` en `tests/architecture/test_copilot_anchors.py` si introduce anchors nuevos.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (state engine custom vs LangGraph subgraph; rename migration estrategia; cómo coexistir guided legacy con Workflow nuevo durante el cutover).
  - Gotchas reales: que apareció en la ejecución, no genéricos.
  - Hooks listos para F7 (channel formatter consume Workflow output) y F8 (routing puede meter Workflow tools en NANO/MINI).

- **Paso 8 — Generar `prompts/F7-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f6): workflow unification + provider integration`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F6-workflow-unification.md` y `prompts/F7-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F6 no aplica por aprendizajes F5 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3 + F4 + F5). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F6 (de aprendizajes F5)

### Aprendizajes F5 que F6 debe asumir

- **Pipeline determinístico dentro de un tool, NO subgrafo LangGraph LLM-driven.** F5 demostró que para flujos con dispatch por enum cerrado (intent kinds), el patrón "tool transversal con stages internos en Python + LLM calls puntuales en bordes" cuesta 2 LLM calls por turn vs 4-6 con subgrafo. F6 debe replicar para cada Workflow: 1 LLM call en planning + N stages Python + 1 LLM call en synthesis. Ver `application/tools/ask_tenant_data/tool.py` como referencia.
- **Patrón `DataAccessProvider` con `supports(kind)` + `execute(*, tenant_id, plan, context)`** — port estable, dispatch por kind. F6 puede modelar `WorkflowProvider.workflows()` con shape similar: cada Workflow declara `id` + `state_schema` + `handler(state, context)`. Discovery agrega via existing `_collect_*` aggregators.
- **`context: Mapping[str, Any]` con `db` opcional** evita el "provider abre/cierra session" de F4. Los Workflow handlers F6 deben recibir `context` con `db` ya abierto por el orchestrator.
- **Sub-port nuevo en `CopilotProvider` Protocol rompe `_StubProvider`.** F5 agregó `data_access()` y `tests/modules/copilot/domain/test_provider_ports.py::_StubProvider` rompió silencioso (assert isinstance False sin pista del método faltante). F6 que expanda `WorkflowProvider` o agregue cualquier sub-port nuevo DEBE actualizar `_StubProvider` con stub-method return None.
- **Anchor budget 25/25 alcanzado.** Bumpear el límite en `test_copilot_anchors.py:87` antes de agregar anchor F6. Documentar el bump en commit message.
- **Cross-module imports prohibidos.** Ratchet 22 frozen. F6 que necesite cross-module access (workflow lee/escribe en otro módulo) DEBE pasar via provider port — no import directo.

### Tests baseline que F6 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/golden/ \
  tests/architecture/ \
  tests/modules/copilot/test_deep_agent_harness.py \
  tests/modules/copilot/test_plan_card_emission.py \
  tests/modules/copilot/test_pinned_memory_repository.py \
  tests/modules/copilot/test_inspiration_repository.py \
  tests/modules/copilot/test_trafilatura_client.py \
  tests/modules/copilot/test_url_inspiration_analyzer.py \
  tests/modules/copilot/test_fetch_url_tool.py \
  tests/modules/copilot/test_pin_to_memory_tool.py \
  tests/modules/copilot/test_inspirations_layer.py \
  tests/modules/copilot/test_data_access_port.py \
  tests/modules/copilot/test_conversation_data_access_provider.py \
  tests/modules/copilot/test_ask_tenant_data_*.py \
  tests/modules/copilot/test_data_query_cache.py \
  tests/modules/copilot/test_conversation_repository_count_window.py \
  tests/modules/copilot/domain/test_provider_ports.py \
  tests/modules/offer/test_offer_repository_search.py \
  tests/modules/offer/test_offer_data_access_provider.py \
  tests/modules/crm/test_lead_repository_count_inbound.py \
  tests/modules/crm/test_crm_data_access_provider.py \
  tests/modules/brand/test_brand_summary_repository.py \
  tests/modules/brand/test_brand_section_updated_event.py \
  tests/modules/brand/test_brand_context_injector.py \
  tests/shared/workers/test_brand_summary_regen.py \
  tests/shared/application/test_brand_summary_event_handlers.py \
  tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
  -q -o addopts="" --timeout=60
```

Debe ser ~700+ verde. Los flaky heredados (`test_streaming_integration` + `test_editable_fields_ssot::test_no_cross_domain_duplicates`) se corren **aislados** post-cambios.

### Archivos clave que F6 modifica (a priori)

- `backend/src/modules/copilot/domain/workflow.py` — clase `Workflow` + `WorkflowNode` + `WorkflowState` + `WorkflowTrigger` enum (existe stub mínimo en `domain/ports.py::Workflow`, F6 lo expande).
- `backend/src/modules/copilot/application/workflows/engine.py` — state machine ejecutor.
- `backend/src/modules/copilot/application/workflows/registry.py` — agrega workflows descubiertos.
- `backend/src/modules/copilot/domain/ports.py::WorkflowProvider` — protocol existe (F1), F6 lo activa.
- Migration `071_rename_procedure_state_to_workflow_state.py` — idempotente PG (DROP COLUMN IF EXISTS + ADD COLUMN IF NOT EXISTS + UPDATE).
- `backend/src/modules/{brand,offer}/copilot_provider/workflows.py` — pilots.
- `backend/src/modules/copilot/application/guided/` — coexistencia / desuso planeado (NO hard-delete sin cutover).
- `backend/src/modules/copilot/application/procedures/` — coexistencia / desuso planeado.
- `backend/src/modules/copilot/application/extraction_card_flow.py` — coexistencia / desuso planeado.

### Riesgos que vigilar en F6

- **Coexistencia de 4 sistemas (legacy guided + procedure + extraction_card_flow + nuevo Workflow)** durante el cutover. Plan: feature flag `WORKFLOW_V2_ENABLED` por tenant + dual-write a workflow_state + fallback a procedure_state si falta. Backfill de conversaciones activas via worker dedicado.
- **Migration `procedure_state → workflow_state`**: PG NO permite RENAME en JSONB column durante write traffic. Estrategia idempotente: ADD COLUMN workflow_state JSONB, UPDATE workflow_state = procedure_state WHERE workflow_state IS NULL, NUEVO código lee workflow_state con fallback a procedure_state. NO DROP procedure_state hasta cutover confirmado en F-pos. Documentar en learnings.
- **`Workflow` con LLM calls embebidos** vs deterministic stages. F5 demostró que pipeline puro con 2 LLM calls cuesta poco; si F6 modela cada Workflow node como LLM call, el costo explota. Recomendación: workflows tienen 1 LLM call de "planning" (¿qué nodo sigue?) + nodos Python deterministic + 1 LLM call de synthesizer.
- **Sub-port `WorkflowProvider` ya existe en F1 stub**, pero F6 debe expandirlo (workflow_id, state_schema, handler). Cualquier modificación al Protocol va a romper `_StubProvider` igual que F5 — actualizar test stub al mismo commit.
- **Test flaky `test_streaming_integration`** heredado F0/F1/F2/F3/F4/F5. Si F6 toca el orchestrator (probable — workflows interactúan con SSE): correr aislado primero.
- **Test flaky `test_editable_fields_ssot::test_no_cross_domain_duplicates`** heredado F3. Mismo tratamiento si F6 toca editable_fields.
- **Guided deprecation**: `guided` engine tiene state propio (state.py + blocks.py). F6 debe migrar el state existente o documentar que guided sigue corriendo en paralelo. NO hard-delete hasta cutover.
- **Provider scan cargado en module-import time** (heredado F4) — cualquier provider nuevo debe diferir DB connections hasta `__call__` time. Workflows con `handler` que abre DB en el module-load corrompen unit tests. Ver patrón F4/F5 (DI de `db_factory` con default lazy).

### Hooks F5 disponibles para F6

- `backend/src/modules/copilot/domain/ports.py::DataAccessProvider` — patrón port limpio que F6 puede imitar para `WorkflowProvider`.
- `backend/src/modules/copilot/application/data_access/__init__.py` — directorio para accessors own-module no via discovery; F6 puede crear `application/workflows/__init__.py` con engine + registry similar.
- `backend/src/modules/copilot/application/tools/ask_tenant_data/tool.py::_default_accessors` — patrón aggregator que itera providers + propia infra. F6 puede reusar shape para `_collect_workflows`.
- `backend/src/modules/copilot/infrastructure/cache/data_query_cache.py` — wrapper Redis con fail-open. F6 puede reusar el pattern para cachear workflow_state si necesita.
- `backend/src/modules/copilot/application/orchestrator/subagents/data_query.py` — patrón "subagent con 1 tool sandbox". F6 puede crear subagents per-workflow.
- `backend/src/modules/copilot/application/tools/ask_tenant_data/synthesizer.py::SUPPORTED_OUTPUT_CHANNELS` — F7 lo va a expandir; F6 NO lo toca (canal-aware response es F7 territory).
