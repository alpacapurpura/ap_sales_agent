# Refactor Copilot Arquitectónico — PLAN

Owner: arquitectura copilot. Branch trabajo: `development`. Paralelo-safe: no toca `offer.py`/refactor field-contract-ssot en curso (módulos disjuntos).

Pre-requisito: leer `INVESTIGATION.md`.

## Objetivos

- Contrato único tool response tipado + arch test enforcement.
- Flujos extracción unificados (URL + DOC → worker pattern único).
- Focus mode E2E (BE state persistente + FE UX dedicada + nav lock).
- Registry dominios extensible (nuevo dominio = 1 PR: config + template + persister + test).
- Persister interface común enforced.
- Observabilidad estructurada (schema Pydantic + session_id focus).
- Retiro de `output_sanitizer` cuando contrato maduro.
- Strategy explícita context budget conversaciones largas.

## Principios no negociables

- DRY: 2 flujos hacen lo mismo → unificar antes de añadir 3ro (buyer_persona, landing, assets, crm enrichment).
- Alta cohesión / bajo acoplamiento: orchestrator no mezcla persistencia con streaming.
- Observabilidad primero: ningún flow nuevo sin `trace_event` + test que valide trace.
- TDD: arch tests primero. Implementación después. RED → GREEN.
- Backwards-compat durante rollout: `384ad265` fixes deben seguir pasando. Feature-flag dual-read 2 sprints donde corresponda.

---

## Fases — orden causal

Dependencias: F0 → F1 → {F2, F3, F4} paralelas → F5 continuo → F6 retiro → F7 independiente.

| # | Fase | Duración estimada | Depende | Arch tests nuevos |
|---|---|---|---|---|
| F0 | Workspace + contratos base | 1 sprint | — | 0 nuevos, todos existentes verdes |
| F1 | ToolResponse Pydantic + migración tools | 3 sprints | F0 | 3 |
| F2 | Unificar extracción (worker + persist-mode flag) | 2 sprints | F1 | 2 |
| F3 | Focus mode E2E (BE checkpointer + FE sidebar) | 3 sprints | F1 | 3 |
| F4 | Persister Protocol + homologación | 1 sprint | F0 | 1 |
| F5 | Observabilidad estructurada | 1 sprint (cross-fase) | F1 | 2 |
| F6 | Retiro sanitizer + contrato enforced | 1 sprint | F1 + F2 + F5 en verde | 1 |
| F7 | Context budget compaction | 1 sprint | F1 | 1 |

Total: ~10-13 sprints depende paralelismo F2/F3/F4.

---

## F0 — Workspace + contratos base

**Objetivo**: preparar terreno sin tocar código runtime. Alinear docs + tests + decisiones.

Entregables:
- `docs/refactors/copilot-architecture/DECISIONS.md` (ADRs), `STATE.md`, `INVARIANTS.md`, `TODO.md`. Precedente: `docs/refactors/field-contract-ssot/`.
- ADR-001: LangGraph checkpointer = `AsyncPostgresSaver` + RLS. thread_id convention.
- ADR-002: Unified worker pattern para extract URL+DOC con `commit_mode` flag.
- ADR-003: Focus mode BE-state SSoT, FE mirror.
- ADR-004: `ToolMessage.artifact` + `ToolResponse` Pydantic.
- ADR-005: Persister `Protocol` firma única.
- ADR-006: OTel GenAI naming (`gen_ai.*`) sobre `copilot_trace_event`.
- ADR-007: Sanitizer retirement criteria.

Salida F0: arch tests existentes verdes (baseline). Ningún cambio de comportamiento.

Exit criteria:
- ADRs mergeados en `development`.
- `.claude/rules/copilot-resilience.md` actualizado con referencia a estos ADRs.
- `/test-backend` + `/test-frontend` verdes baseline.

---

## F1 — ToolResponse Pydantic + migración tools

**Objetivo**: contrato único tipado para toda tool response. Eliminar raíz JSON-regurgitation.

Scope BE:

1. **Nuevo tipo compartido** `backend/src/shared/domain/tool_response.py`:
   ```
   ToolResponse(
       text: str                     # para ToolMessage.content, visible al LLM
       llm_content: str | None       # opcional, texto condensado
       ui_action: UiAction | None    # discriminated union tipada
       error: ToolError | None       # code + message estructurado
       session_hint: SessionHint | None  # hints para focus mode (next_block, etc.)
   )
   UiAction: discriminated union kind in {preview_update, clarify_card, proposal, navigation, extraction_summary, interview_complete, guided_started/advanced/completed, procedure_progress, checkpoint, alternatives, multi_option, metric_summary, comparison, checklist}
   ```
2. **Tool decorator helper** `@copilot_tool(...)` wrap `@tool` + `response_format="content_and_artifact"`. Tool dev retorna `ToolResponse` → helper transforma en `(text, artifact_dict)`.
3. **Migrar tools** por oleadas (ratchet):
   - Wave A (core focus mode): `start_guided_setup`, `advance_guided_block`, `end_guided_setup`, `extract_structured`, `extract_document_to_fields`, `propose_field_updates`, `clarify`.
   - Wave B (extraction): `extract_from_url`, `extract_from_doc`.
   - Wave C (module/analytics): `module_tools`, `analytics_tools`, `landing_tools`, `connections_tools`, `crm_tools`, `sales_agent_tools`.
   - Wave D (misc): knowledge, web_research, assets, document, procedure, navigation, awareness, offer_ladder, offer_section_tools.
4. **Adaptar `graph.py`** `tool_executor_node` + `context_budget.py` `sanitize_tool_calls` para leer `ToolMessage.artifact` cuando exista.

Scope FE:

5. **Types shared** `frontend/src/features/copilot/types/tool-response.ts` — reflejar Pydantic discriminated union con zod si ya usamos.
6. **use-copilot-ui-action**: consumir `artifact.ui_action` en vez de string parsing.

Arch tests nuevos:

- `backend/tests/architecture/test_tool_response_contract.py` — toda tool decorada con `@copilot_tool` retorna `ToolResponse`. Ratchet allowlist legacy encogible.
- `backend/tests/architecture/test_no_tool_returns_json_string.py` — AST scan: ninguna tool retorna `json.dumps(...)` en top-level return.
- `backend/tests/architecture/test_ui_action_discriminated_union_total.py` — todo `kind` declarado en union tiene renderer FE (cross-check con registry TS).

Exit criteria:
- 100% tools Wave A + B migradas con tests unitarios propios.
- ≥60% Wave C + D migradas; resto allowlist con ticket asociado.
- `output_sanitizer` sigue activo (defensa en profundidad hasta F6).
- `copilot_trace_event.output_preview` sigue truncado 4KB; sin regresión.

Riesgos: context_budget depende de shape actual de `ToolMessage.content` string. Verificar que artifact no rompe sliding window. Spike 0.5 día.

---

## F2 — Unificar extracción URL + DOC bajo worker pattern

**Objetivo**: un solo flujo, un solo evento, un solo subscriber. Flag `commit_mode` distingue UX.

Scope BE:

1. **Nuevo tipo** `ExtractionJob` (ampliar enum existente `backend/src/shared/domain/extraction_jobs.py`):
   ```
   source: Literal["url", "document"]
   commit_mode: Literal["auto", "preview"]
   ```
   - url → `commit_mode="auto"` (worker escribe DB, user ve summary).
   - document → `commit_mode="preview"` (worker calcula delta, emite proposal card; user aprueba via `propose_field_updates`).
2. **BaseExtractionOrchestrator** (ya existe en `backend/src/shared/application/extraction/`) acepta `commit_mode`. Si `preview`, salta persistencia; delta queda en Redis progress key.
3. **Worker `run_buyer_persona_extraction`**: nuevo task ARQ analog a brand/offer. Elimina `extract_from_doc.py` inline path para buyer_persona → usa worker.
4. **Consolidar helpers duplicados**:
   - `_MODULE_LABELS`, `_BRAND_SECTION_LABELS`, `_OFFER_SECTION_LABELS` → `backend/src/modules/copilot/domain/extraction_labels.py`.
   - `_compose_target_label` + `_resolve_section_label` → mismo módulo.
   - `_err` envelope → usar `ToolResponse.error` (F1).
5. **Evento unificado**: mantener `ExtractionSectionCompletedEvent` + `ExtractionJobCompletedEvent` pero añadir `source` y `commit_mode` al payload.
6. **Subscriber único**: `extraction_card_flow.py` lee `source` + `commit_mode`:
   - `auto` → summary card + nav pills (como hoy URL).
   - `preview` → proposal card → `propose_field_updates` → commit.
7. **Concurrency control**: `_record_active_extraction_job` usa optimistic-lock con `xmin`/version column **o** row-level `SELECT ... FOR UPDATE` sobre `copilot_conversations` durante merge JSONB. Tests: 2 jobs paralelos → ambos tracked en `active_extraction_jobs: list`, no dict.
8. **Observabilidad**: `trace_event.source_tool` fiel al origen real (`extract_from_url` / `extract_from_doc`). Unhardcode subscriber.

Scope FE:

9. **Hook `use-copilot-extraction-jobs`**: suscribirse a events job_started / section_completed / job_completed; muestra toast o sidebar progreso.
10. **ProposalCard**: soporta `commit_mode="preview"` con botones aprobar/rechazar todo/parcial (ya parcialmente existe).

Arch tests nuevos:

- `test_extraction_single_contract.py` — un solo `ExtractionJob` descriptor por `(domain, source)`, sin duplicados.
- `test_extraction_card_flow_dispatches_by_commit_mode.py` — subscriber routeando por `commit_mode`.

Exit criteria:
- `extract_from_doc.py` inline → deprecated/eliminado, redirigido a worker.
- Tests end-to-end cubren: URL-brand, URL-offer, DOC-brand, DOC-offer, DOC-buyer_persona.
- 2 jobs paralelos simulados → ambos tracked sin pérdida.
- `source_tool` correcto en `copilot_trace_event`.

Riesgos: migration de `extract_document_to_fields` (guided inline) vs `extract_from_doc` — ¿mismo worker? Decisión F2.1: unificar, `extract_document_to_fields` se vuelve sugar sobre worker con `commit_mode="preview"`.

---

## F3 — Focus mode E2E

**Objetivo**: sesión de interview persistente, resumible, con UX dedicada.

Scope BE:

1. **LangGraph checkpointer**:
   - Añadir `AsyncPostgresSaver` en `graph.py` compile. Tabla `copilot_graph_checkpoints` (migración idempotente).
   - `thread_id = f"{tenant_id}:{user_id}:{conversation_id}"`.
   - RLS Postgres policies sobre checkpoint tables (enforced tenant).
   - Migration idempotente `063_copilot_graph_checkpoints.py`.
2. **FocusState** nuevo dataclass (`backend/src/modules/copilot/application/focus/state.py`):
   ```
   FocusState:
       active: bool
       domain: str
       entity_id: UUID | None
       mode: "conversational" | "document" | "url"
       visible_block_id: str
       completed_slots: list[str]
       pending_slots: list[str]
       last_user_input_summary: str
       started_at, updated_at
       session_id: UUID  # correlator para traces
   ```
   Sibling key en `procedure_state["focus"]` (coexiste con `"guided"` legacy durante migration).
3. **Interrupt-based slot filling**:
   - Bloques existentes promovidos a FSM formal (`block_generator.py` → `focus_flow.py` con transitions `answer_ready / needs_clarify / skip_allowed / complete`).
   - Nodo `ask_slot` usa `interrupt({"slot_id": ..., "prompt": ...})`.
   - FE POST chat con `Command(resume=<user answer>)` — SSE v2 adaptado.
4. **Tools nuevos**:
   - `enter_focus_mode(domain, entity_id, mode)` — inicializa FocusState.
   - `exit_focus_mode` — cleanup + emite trace.
   - Ambos retornan `ToolResponse` con `ui_action.kind="enter_focus"` / `"exit_focus"`.
5. **Dual-read feature flag**: `GuidedState` legacy coexiste 2 sprints; nuevo código lee FocusState, fallback a GuidedState si `active=false`.

Scope FE:

6. **sidebarState extendido**: `"collapsed" | "rail" | "full" | "focus"`. Zustand persist middleware en copilot-store para esta clave.
7. **FocusPanel** — nuevo componente:
   - Sidebar expandido con progress bar per-block.
   - ChatPanel lateral.
   - Badge "faltan X slots".
   - Botón "salir focus" (confirmación si hay pending).
8. **Nav lock**:
   - `useBeforeUnload` cuando `focus.active=true && focus.pending_slots.length > 0`.
   - Interceptor `router.events` Next.js — bloquea push/replace fuera de `routeFor(domain)`.
   - Sidebar collapse deshabilitado en focus.
9. **Session resumption**: al mount `CopilotChatPanel`, si backend reporta `focus.active=true`, FE auto-abre en `sidebarState="focus"` sin esperar input user.
10. **UI actions nuevos**: `enter_focus`, `exit_focus`, `focus_slot_update` (actualiza pending/completed).

Arch tests nuevos:

- `test_focus_state_single_writer.py` — solo servicios en `focus/` escriben `procedure_state["focus"]`.
- `test_checkpointer_thread_id_tenant_scoped.py` — thread_id siempre incluye tenant.
- FE: `test-focus-sidebar-state.test.tsx` — sidebarState "focus" persiste localStorage.

Exit criteria:
- Recargar navegador mid-interview → UI reanuda en mismo bloque sin perder completed_slots.
- 20-turn interview → checkpoint por turn, `thread_id` estable.
- RLS test: query cross-tenant de checkpoints rechazada.
- FE nav lock dispara modal al intentar salir con pending>0.

Riesgos:
- LangGraph `interrupt()` + SSE v2: verificar `chat.py` `_persist_messages` accumulator maneja resume sin duplicar state. **Spike 1-2 días antes de F3.1**.
- Migration 063 en prod con rows existentes: dual-read flag mitiga.

---

## F4 — Persister Protocol + homologación

**Objetivo**: agregar nuevo dominio = declarar 1 Persister con firma fija, test arch obliga.

Scope:

1. **Nuevo protocolo** `backend/src/modules/copilot/infrastructure/persisters/base.py`:
   ```
   class Persister(Protocol):
       domain: ClassVar[str]  # "brand" | "offer" | "buyer_persona" | ...
       async def persist(
           self,
           tenant_id: UUID,
           delta: Mapping[str, Any],          # rename mapa_global → delta
           fields_to_persist: Sequence[str],
           entity_id: UUID | None = None,
       ) -> PersistResult:  # dataclass con created_id / updated_fields / errors
           ...
   ```
2. **Homologar 3 existentes**:
   - `BrandPersister`: agregar `entity_id` (no usado hoy, ignora). Retornar `PersistResult`.
   - `OfferPersister`: retornar `PersistResult` con `updated_fields`.
   - `BuyerPersonaPersister`: retornar `PersistResult(created_id=entity_id)` en lugar de `UUID | None`.
3. **Registry** `persister_registry.py` indexa por `domain` → `Persister`.
4. **Rename `mapa_global` → `delta`** (Spanish code only — mejor consistencia con event payload).

Arch test nuevo:
- `test_persister_protocol_compliance.py` — import recursivo bajo `persisters/`, verifica cada clase con sufijo `Persister` implementa `Persister` Protocol.

Exit criteria:
- 3 persisters actuales pasan Protocol.
- Nuevo dominio (e.g. `landing`) = add `LandingPersister` + test → sin cambios en orchestrator.

Riesgos: bajos. Refactor mecánico + tipado.

---

## F5 — Observabilidad estructurada

**Objetivo**: trace_events tipados, session_id focus correlacional, alineación OTel GenAI.

Scope:

1. **Schema Pydantic** `trace_event.py`:
   - `TraceEventData` union por `event_type`: ToolCallData, LlmCallData, CardEmittedData, NodeData, ErrorData, FocusSessionData.
   - Validar antes de write.
2. **Nuevos campos**:
   - `focus_session_id: UUID | None` — correlaciona toda interview.
   - `source_tool_origin: str` — fix hardcoded `"extract_from_url"`.
   - `gen_ai.usage.input_tokens`, `output_tokens`, `gen_ai.response.id` en llm_call.
3. **Streamlit admin `/trazas`** (ya existe según `copilot-resilience.md`): filtros nuevos por `focus_session_id`, `source_tool`, `error_type`.
4. **Rule update**: `.claude/rules/copilot-resilience.md` — sección "focus session debugging" con queries sample.

Arch tests:
- `test_trace_event_schema.py` — todo `record()` call usa `TraceEventData` subclass.
- `test_no_hardcoded_source_tool.py` — AST grep: nadie hardcodea `source_tool=` con string literal fuera de `tool_executor_node`.

Exit criteria:
- Todo evento validado Pydantic.
- Una query SQL por `focus_session_id` reconstruye interview end-to-end.

---

## F6 — Retiro sanitizer + contrato enforced

**Objetivo**: eliminar `output_sanitizer.py` cuando contrato es SSoT.

Pre-requisito:
- F1 completa (100% tools Wave A+B, ≥80% C+D).
- F5 mostrando ≥2 sprints sin hit de sanitizer en prod (métrica: % AIMessages donde sanitizer modificó content).

Scope:
1. Eliminar `output_sanitizer.py` + imports en `graph.py`.
2. Reemplazar por arch test `test_no_json_regurgitation_at_boundary.py`: integration test que simula LLM response con JSON dump y valida `graph.py` no lo emite en SSE final — en vez de stripearlo, falla.
3. Métrica observabilidad: `trace_event` tipo `contract_violation` si detecta.

Exit criteria:
- 0 hits sanitizer 2 sprints.
- `output_sanitizer.py` borrado.
- Test integration en verde.

---

## F7 — Context budget compaction

**Objetivo**: interviews largas (20-30 turns) sin balloon de tokens.

Scope:
1. **Tool-result compaction**: nuevo helper `compact_tool_messages(messages, max_per_tool=1024)` — trunca `content` preservando `tool_call_id`.
2. **SummarizationNode**: promover `truncate_history` summary inline (80 chars) a nodo `pre_model_hook` tipo LangMem SummarizationNode con prompt "summarize 10 prior turns focusing on form slots filled".
3. **Budget dinámico**: ajustar `DEFAULT_BUDGET` por modo:
   - Focus mode: prioridad `interview_context` + `entity_snapshot` (más); historia (menos).
   - Free chat: balanceado.
4. **Opt-in Anthropic memory tool**: feature flag tenant-level. Si habilitado, usa `memory` server-side de Anthropic para compaction (beneficio -84% tokens en evals públicas).

Arch test:
- `test_context_budget_never_exceeds_model_limit.py` — simular conversación 50 turns, assert tokens ≤ 90% max_context.

Exit criteria:
- Benchmark: interview 25 turns → tokens estables alrededor de 8-12K (vs balloon actual a 30K+).
- Costo promedio por turn ≤ 15% vs pre-refactor.

---

## Paralelismo entre fases

- F2, F3, F4 pueden correr simultáneos post-F1 (diferentes owners OK).
- F5 es transversal: cada fase añade trace events usando schema F5.
- F7 independiente — se puede arrancar tras F1.

## Rollback strategy

Cada fase mergeada detrás de feature flag tenant-level (`copilot.use_focus_mode`, `copilot.use_checkpointer`, etc.) durante 1 sprint. Métricas + comparación A/B antes de hard-cutover.

## Tests a preservar (SIEMPRE verdes)

- `backend/tests/architecture/test_copilot_anchors.py`
- `backend/tests/architecture/test_editable_fields_ssot.py`
- `backend/tests/modules/copilot/test_extraction_domain_registry.py`
- `backend/tests/modules/copilot/test_field_paths_hint.py`
- `backend/tests/modules/copilot/test_tool_message_envelope.py`
- `backend/tests/modules/copilot/test_output_sanitizer.py` (hasta F6)

## Archivos nuevos propuestos

Backend:
- `backend/src/shared/domain/tool_response.py`
- `backend/src/modules/copilot/application/tools/decorators.py` (`@copilot_tool`)
- `backend/src/modules/copilot/application/focus/state.py`
- `backend/src/modules/copilot/application/focus/flow.py` (FSM)
- `backend/src/modules/copilot/application/focus/persistence.py`
- `backend/src/modules/copilot/application/observability/trace_event_schema.py`
- `backend/src/modules/copilot/infrastructure/persisters/base.py`
- `backend/src/modules/copilot/domain/extraction_labels.py`
- `backend/src/modules/{brand,offer,buyer_persona}/workers/tasks.py` — nuevos task `run_*_extraction_unified` (o modificar existentes con `commit_mode`).
- `backend/alembic/versions/063_copilot_graph_checkpoints.py`

Frontend:
- `frontend/src/features/copilot/types/tool-response.ts`
- `frontend/src/features/copilot/components/FocusPanel.tsx`
- `frontend/src/features/copilot/components/focus/ProgressBlockList.tsx`
- `frontend/src/features/copilot/components/focus/FocusNavLockGuard.tsx`
- `frontend/src/features/copilot/hooks/use-focus-state.ts`
- `frontend/src/features/copilot/hooks/use-copilot-extraction-jobs.ts`

Docs:
- `docs/refactors/copilot-architecture/DECISIONS.md`
- `docs/refactors/copilot-architecture/STATE.md`
- `docs/refactors/copilot-architecture/INVARIANTS.md`
- `docs/refactors/copilot-architecture/TODO.md`
- `docs/domains/copilot/focus-mode.md`
- `docs/domains/copilot/tool-response-contract.md`

## Métricas de éxito

| Métrica | Baseline actual | Target post-refactor |
|---|---|---|
| Tools con envelope compliant | 2/31 | 31/31 |
| JSON regurgitado en chat (sanitizer hits/día) | ~? (medir F5) | 0 (F6 gate) |
| Conversaciones resumibles post-reload | 0% (session pierde) | ≥95% |
| Tiempo dev para añadir nuevo dominio | 2-3 sprints (hoy) | 1 sprint |
| Tokens promedio por interview 25-turn | balloon >30K | ≤12K |
| Trazas con `focus_session_id` correlacional | 0% | 100% focus mode |
| Cross-tenant leak posible vía checkpointer | no existe hoy | 0 (RLS enforced) |

## Dependencias con otros refactors en curso

- **field-contract-ssot** (`docs/refactors/field-contract-ssot/`): toca `offer.py`, schemas. No overlap con copilot core. Si field paths cambian, `field_paths_hint.py` se actualiza automático (SSoT derivado). Coord sync al cerrar fase 01 field-contract.
- **offer migration 062** (`88383918`): independiente; solo afecta OfferPersister campos nuevos → F4 persister homologación debe leer el schema final.

## Out of scope (explícito)

- Reescribir personalidad agent / system prompt (hay refactor separado personality 3-pillars).
- Cambiar SSE protocol v2 a v3.
- Migrar FE a React 19 / Next 16 específicamente por este refactor (aprovechar si otro refactor lo hace).
- Reemplazar ARQ por Celery/Dramatiq.
- Rewrite copilot en agent framework alternativo (DSPy, CrewAI).
