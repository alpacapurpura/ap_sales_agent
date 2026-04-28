# S11 · Shared base lift + orchestrator decomposition

## Objetivo

1. **Shared base lift**: levantar el plumbing común de los 6 LangChain
   callbacks (`on_chat_model_*`, `on_tool_*`, `on_chain_*` + helpers
   `_extract_usage`, `_from_openai_token_usage`,
   `_extract_provider_and_model`) al `BaseAgentCallbackHandler` del shared
   module. Sales y copilot dejan de duplicar ~250 LOC cada uno. Coordinado
   con copilot retrofit en el mismo sprint.

2. **Orchestrator decomposition** (Stranger Fig): refactorizar tres archivos
   sales overgrown:
   - `chat.py` 1082 LOC → < 400 LOC.
   - `closer_studio_service.py` 623 LOC → split en
     `ConversationQueryService` + `ConversationCommandService` + `KpiService`.
   - `semantic_router.py` 328 LOC → registry-based con tenant overrides
     desacoplados.

   §3 protected (`closer_studio.py` API + `ws.py` + `enrollment_*`
   end-to-end + `agent_state_checkpoint` schema + webhook adapters +
   `BufferService.smart_debounce` + `OutputManager.process_response` +
   `follow_up_engine` cadence) **NO se toca**.

## Dependencias

S10 cerrado (eval loop activo + goldens cubren features completas — sin
ese safety net, refactor de `chat.py` es ciego).

## Criterios de éxito

### Lift compartido

1. ✅ `BaseAgentCallbackHandler` declara concreto `on_chat_model_start`,
   `on_chat_model_end`, `on_chat_model_error`, `on_tool_start`,
   `on_tool_end`, `on_tool_error`, `on_chain_start`, `on_chain_end`.
2. ✅ Helpers `_extract_usage`, `_from_openai_token_usage`,
   `_extract_provider_and_model`, `_apply_sanitization`, `_resolve_pricing`
   en la base.
3. ✅ Subclases sólo overrides de `_persist_llm_call_row` +
   `_persist_trace_event_row` (sales adds `lead_id` + `channel_type` per
   call).
4. ✅ `SalesAgentCallbackHandler` < 200 LOC (de 575 actuales).
5. ✅ `ObservabilityCallbackHandler` (copilot) < 200 LOC (de ~580
   actuales).
6. ✅ Tests existentes 113 copilot + sales callback handler tests
   verdes sin cambio.
7. ✅ `tests/architecture/test_sales_agent_callback_handler_invariants.py`
   sigue verde — el invariante migra al base.

### Orchestrator decomposition

8. ✅ `chat.py` < 400 LOC. Responsabilidades extraídas en orden:
   - `ConversationPipeline` (parsing + state machine + dispatch).
   - `IdentityResolver` (lead identity resolution).
   - `AuditEmitter` (event publish + audit log).
9. ✅ `closer_studio_service.py` split:
   - `ConversationQueryService` (list/detail/get_kpis).
   - `ConversationCommandService` (stop/resume/send/nudge/reactivate/diagnose).
   - `KpiService` (dedicated, lazy aggregation).
10. ✅ `semantic_router.py` registry-based: routes domain en
    `domain/semantic_routes.py` con strategy pattern; tenant overrides en
    repo separado.
11. ✅ Goldens del eval loop S10 pasan idénticos pre/post-refactor (golden
    diff = 0 turn outputs). Si diff aparece → refactor introdujo cambio
    semántico, revertir.
12. ✅ `make arch-test` global verde. `tests/modules/sales_agent/` verde.
13. ✅ Cobertura tests sales_agent ≥ 70% (post-decomposition más fácil
    testear unidades).

## Research mandate

### Queries WebSearch

1. `Stranger Fig pattern Python service decomposition tests preserve behavior 2026`.
2. `LangChain BaseCallbackHandler Template Method pattern multi-agent inheritance 2026`.
3. `pytest snapshot testing golden output Python 2026 best practices`.

### Lectura obligatoria

- `learnings/S1-sales-agent-observability-parity.md` — sección "callback
  handler 6-callbacks duplica copilot".
- `audit/sales-agent-current-state.md §8` (cohesion heatmap top-5).
- `src/shared/agent_observability/recording/base_callback_handler.py`
  (estado actual base abstract).
- `src/modules/copilot/observability/recording/observability_callback_handler.py`
  (referencia de duplicación).
- Docs copilot redesign 2026-04 — confirmar coordinación timing.

### Hallazgos research

- **Strangler Fig (microservices.io / AWS prescriptive guidance / 2026
  Medium articles)**: pattern key — dual-write/shadow comparing legacy vs
  new para preservar behavior. Decommission inmediato post-extract.
  Boundaries reflejan behavior real, no conceptual. Aplica a la
  orchestrator decomposition: cada extracción es un commit con dual-call
  pattern (legacy chat.py llama nueva clase, ambos producen mismos
  outputs) hasta que el legacy queda vacío y se borra.
- **LangChain BaseCallbackHandler Template Method**
  (python.langchain.com): pattern oficial. Hook methods optional override
  en derived classes. Subclassing es la forma idiomática para
  multi-agent. Sin breaking en 2026. Confirma que lift Template Method
  es API-idiomatic.
- **pytest snapshot testing (Syrupy / inline-snapshot March 2026 /
  pytest-golden)**: libs maduras. Best practice deterministic seeds +
  commit snapshots con tests. Confirma que el approach fixture-based con
  diff byte-equal es viable.

---

## Ajustes vs plan original (2026-04-28 — pre-flight S11A)

Decisiones tomadas en sesión pre-flight tras research + verificación
estado real del repo:

### Ajuste 1 — Snapshot determinístico de pipeline en lugar de goldens LLM

**Plan original**: "Goldens del eval loop S10 pasan idénticos
pre/post-refactor (golden diff = 0 turn outputs)" + "eval loop S10
corriendo + goldens estables (últimas 2 sem semanal sin diffs)".

**Realidad**: S10 cerró 2026-04-28 (commit `4b7258d1`). Cero corridas
semanales aún. La regla "2 semanas sin diffs" es físicamente
incumplible.

**Decisión**: en vez de goldens LLM (que tienen variance natural y
requieren histórico inalcanzable), capturamos **snapshot determinístico
de pipeline outputs** con LLM mockeado. Capture:
- `_resolve_customer` output dict.
- `_track_message_event` calls (props passed).
- `LeadCapturedEvent` published count.
- `_load_checkpoint` result.
- `_handle_human_mode` returns.
- `_determine_session_state` output dict.
- `_build_initial_state` output (initial_state dict completo).
- `semantic_router.detect_and_accumulate` returns.
- `agent_app.ainvoke` config (callbacks list).
- `_save_checkpoint` arguments.
- `audit_repo.log_message` calls.
- `OutputManager.process_response` call.
- `ws_manager.emit` events.
- `event_bus.publish` events.

Estas son funciones puras del input + state cuando el LLM se mockea.
Refactor preserva pipeline → diff = 0 byte-equal. Validation correcto
para refactor (cambios estructurales), NO para regresiones de modelo
(eso lo cubre el judge S10 cuando arranque corrida normal).

Tests viven en `tests/snapshots/sales_agent_pipeline/` con archivos
JSON commiteados. Refactor arch test:
`tests/architecture/test_pipeline_snapshot_diff.py` corre los snapshots
y falla si byte-diff > 0.

Goldens LLM S10 se mantienen intactos para su rol original (judge
weekly drift detection). NO se tocan.

### Ajuste 2 — Retrofit copilot mismo Sub-sprint A

**Plan original**: "Coordinar timing — copilot retrofit + sales lift en
mismo sprint. Si copilot no listo → diferir lift a S12 o crear S11.5."

**Realidad**: no hay equipo separado de copilot. El developer que toca
sales toca copilot. La condición "copilot no listo" = "developer no
disponible" = nunca aplica.

**Decisión**: retrofit copilot dentro de Sub-sprint A. Lift levanta
ambos handlers al base en el mismo set de commits. 113 tests copilot +
sales callback verde post-lift. Cierre simultáneo de la deuda en ambos
módulos. El base nace validado por 2 consumers reales (threshold DRY de
[04-principles.md §1.2](§1.2): "esperar al 3er consumer antes de extraer"
queda exactamente cumplido — 2 consumers reales → extract justificado).

### Ajuste 3 — S11 ejecutado en 2 sesiones (S11A + S11B)

**Plan original**: S11 = 8-12 días en una fase única.

**Realidad**: una sesión Claude no sostiene 12 días sin context
degradation. El refactor Strangler Fig requiere precisión quirúrgica
incompatible con context window saturado.

**Decisión**: dividir ejecución en 2 sesiones consecutivas, cada una
con su propio learnings + handoff prompt:

| Sub-fase | Sesión | Scope | Esfuerzo |
|---|---|---|---|
| **S11A** | Esta | Shared base lift (sales + copilot retrofit) + snapshot pipeline framework | 5 días |
| **S11B** | Próxima | Orchestrator decomposition (chat.py + closer_studio_service.py + semantic_router.py) | 7 días |

S11A produce:
- `learnings/S11A-shared-base-lift.md`
- `prompts/S11B-start.md` (handoff con commit hash final S11A)

S11B produce:
- `learnings/S11B-orchestrator-decomp.md`
- `prompts/S12-start.md` actualizado (override del existente)

S11 entera está cerrada cuando S11B cierre — README muestra estado
✅ S11 al cierre conjunto. El **plan no fragmenta** — es la **ejecución**
la que se distribuye en sesiones para preservar calidad. La fase
sigue siendo una sola en términos de DoD del plan ([01-master-plan.md
Definition of Done](01-master-plan.md)).

---

## Diseño

### Lift Template Method

```python
# src/shared/agent_observability/recording/base_callback_handler.py
class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):

    # ── Concrete callbacks (lift desde sales + copilot) ─────────────
    async def on_chat_model_start(self, ...) -> None:
        try:
            self._open_chat_span(...)
        except Exception as exc:
            self._log_warning("on_chat_model_start_failed", exc)

    async def on_llm_end(self, ...) -> None:
        try:
            call = self._build_llm_call_event(response)
            call = self._apply_sanitization(call)
            call = self._resolve_pricing(call)
            await self._persist_llm_call_row(**call.fields, **self._agent_specific())
        except Exception as exc:
            self._log_warning("on_llm_end_failed", exc)
            self._safe_rollback()

    # ... 6 más

    # ── Helpers (lift) ──────────────────────────────────────────────
    def _extract_usage(self, response: LLMResult) -> dict[str, int]: ...
    def _from_openai_token_usage(self, raw: dict) -> dict[str, int]: ...
    def _extract_provider_and_model(self, response: LLMResult) -> tuple[str, str]: ...

    # ── Abstract (subclass overrides) ───────────────────────────────
    @abstractmethod
    def _agent_specific(self) -> dict[str, Any]: ...

    @abstractmethod
    async def _persist_llm_call_row(self, **kwargs: Any) -> None: ...

    @abstractmethod
    async def _persist_trace_event_row(self, **kwargs: Any) -> None: ...
```

```python
# src/modules/sales_agent/observability/recording/callback_handler.py
class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    def __init__(self, *, db_session, tenant_id, lead_id, channel_type, ...):
        super().__init__(db_session=db_session, tenant_id=tenant_id, ...)
        self.lead_id = lead_id
        self.channel_type = channel_type

    def _agent_specific(self) -> dict:
        return {"lead_id": self.lead_id, "channel_type": self.channel_type}

    async def _persist_llm_call_row(self, **kwargs):
        self.llm_call_repo.add(**kwargs)

    async def _persist_trace_event_row(self, **kwargs):
        self.trace_repo.add(**kwargs)
```

### Stranger Fig orchestrator

Extraer en orden inverso al data flow (más abajo primero, menos riesgo):

1. **`AuditEmitter`** (extracto de `chat.py`):
   - emit `LeadCapturedEvent`, `LeadQualifiedEvent`, etc.
   - publishes via `event_bus.publish`.
   - sin lectura/escritura DB; pure functions over state.
2. **`IdentityResolver`** (extracto de `chat.py`):
   - resolve lead identity vía port `shared/links/ports/crm_repos.py`.
   - sin acoplar a adapter.
3. **`ConversationPipeline`** (extracto de `chat.py`):
   - parsing entrada → state machine → dispatch al subgraph.
   - delegate a SmartBufferService (§3, sin tocar) + OutputManager (§3,
     sin tocar) + agent_app.ainvoke.
4. **`ChatOrchestrator` reducido**: thin facade que compone los 3.

Mismo pattern para `closer_studio_service.py` (Query/Command/Kpi split)
y `semantic_router.py` (registry + strategy).

## Plan TDD

1. **Pre-refactor: capture goldens del eval loop** S10 (turn outputs
   por canal × por tenant fixture). Estos son la verdad — refactor
   debe preservarlos byte-equal.
2. RED: tests del lift base — `BaseAgentCallbackHandler` instanciable
   con stubs, ejecuta callback flow sin SubclassImplementationError.
3. Implementar lift en base. Verificar copilot + sales tests verdes
   después de delegar al base.
4. RED: tests de cada nueva clase orchestrator (`AuditEmitter`,
   `IdentityResolver`, `ConversationPipeline`, `ConversationQueryService`,
   `ConversationCommandService`, `KpiService`).
5. Implementar Stranger Fig — extraer una clase por commit. Tests verdes
   tras cada commit.
6. Re-correr goldens — diff debe ser 0.
7. Si diff > 0 → revertir el commit que rompió + investigar.

## Implementación step-by-step

### Lift base (5 días)

1. RED: tests del shared base con stubs.
2. Lift `_extract_usage` + `_from_openai_token_usage` +
   `_extract_provider_and_model` desde sales handler.
3. Verificar copilot también puede consumirlos (via diff entre
   helpers).
4. Lift los 6 callbacks `on_*`. Sales + copilot conservan solo
   overrides de `_persist_*_row`.
5. Update sales handler (eliminar 6 callbacks + helpers, conservar
   constructor + overrides).
6. Update copilot handler (idem).
7. 113 + sales tests verdes.
8. Arch test S6 `test_sales_agent_callback_handler_invariants` ajustar
   si el AST scan ahora detecta los `on_*` en el base — el test
   debe inspeccionar el AST del **base** + del **subclass** y validar
   ambos (o validar sólo el base).

### Orchestrator decomposition (7 días)

9. Capture goldens pre-refactor.
10. Extract `AuditEmitter`. Tests + commit.
11. Extract `IdentityResolver`. Tests + commit.
12. Extract `ConversationPipeline`. Tests + commit.
13. Reduce `ChatOrchestrator` a facade. Tests + commit. Goldens diff = 0.
14. Split `closer_studio_service.py` (Query/Command/Kpi). Tests + commit.
15. Refactor `semantic_router.py` registry-based. Tests + commit.
16. Re-correr goldens completo.
17. Quality gates verdes.

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Refactor introduce diff semántico no detectable por unit tests | Goldens del eval loop S10 son la verdad. Si diff > 0 → revertir commit. |
| Lift base requiere coordinar con copilot redesign | Coordinar timing — copilot retrofit + sales lift en mismo sprint. Si copilot no listo → diferir lift a S12 o crear S11.5. |
| Stranger Fig deja stubs orfanos si extracción se aborta | Cada commit debe ser revertible solo (ratchet). NO commits parciales. |
| Tests existentes asumen `chat.py` shape monolítico | Re-write tests pre-refactor a shape de las clases nuevas (esperado, no shortcut). |

## Tech debt closure

Cierra estas entradas FIXED (con commit hash):

- `[MEDIUM] SalesAgentCallbackHandler duplica 6 LangChain callbacks` (S1) — lift.
- `[MEDIUM] chat.py orchestrator overgrown (1082 LOC)` (S00) — Stranger Fig.
- `[MEDIUM] closer_studio_service.py 8+ responsabilidades` (S00) — split.
- `[MEDIUM] semantic_router.py routes hardcoded (328 LOC)` (S00) — registry.
- `[LOW] _tool_dedup_tracker en state es magic string` (S1) — tipar como
  TypedDict update (parte de orchestrator decomposition).
- `[LOW] Lazy imports brand + offer en sales_agent services` (S00) —
  formalizar ports si la decomposition los requiere.
- `[LOW] Subscribers crean SessionLocal() per-event` (S1) — opportunity
  durante event_bus reshape post-decomposition.
- `[LOW] knowledge_builder.py factory amplio` (S00) — opportunity post-decomposition.
