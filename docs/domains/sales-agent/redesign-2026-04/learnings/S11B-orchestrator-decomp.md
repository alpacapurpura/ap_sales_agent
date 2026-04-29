# Learnings · S11B · orchestrator decomposition Strangler Fig

> Sub-sprint B cierra **S11 entera**. Sales orchestrator pasó de 1140 LOC en
> un solo archivo a 1393 LOC distribuidos en 5 archivos cohesivos
> (orchestrator/) + 5 archivos del split closer_studio (closer_studio/) + 3
> archivos del split semantic_router (domain/semantic_routes.py, overlay,
> singleton). El snapshot byte-equal validó comportamiento preservado
> commit-a-commit.

---

## Resumen (3 líneas)

- **Entregado**: 7 commits Strangler Fig (`f5bc583c` snapshot framework →
  `077ed6df` AuditEmitter → `48f3f2ef` IdentityResolver → `b14175cf`
  ConversationPipeline → `231d85a5` ChatOrchestrator thin facade →
  `ef972405` closer_studio Query/Command/Kpi split → `7367b5f8`
  semantic_router registry split). chat.py 1140 → 337 LOC (-70%, S11
  DoD §8 met). 3313 tests verde (638 arch + 2675 modules). Snapshot
  pipeline diff = 0 byte-equal validado tras CADA commit. §3 protected
  intacto (git diff = 0 cambios en BufferService / OutputManager /
  enrollment / agent_state_checkpoint / webhooks / follow_up_engine).
- **Decisión no obvia**: el snapshot helper monkeypatcha en **definition
  sites** (e.g., `src.shared.domain.events.EventBus.publish`,
  `src.modules.sales_agent.application.services.knowledge_builder.TenantKnowledgeBuilder`)
  **no** en `chat_mod.X`. El primer intento usaba `chat_mod.EventBus` y
  funcionaba mientras chat.py importaba EventBus. Cuando el ruff auto-fix
  borró el import muerto post-AuditEmitter, el patch falló con
  `AttributeError`. Lección: cualquier patch que tenga que sobrevivir
  Strangler Fig debe apuntar a la clase/función donde se DEFINE, no
  donde se USA.
- **Listo para S12**: snapshot framework cubre orchestrator (1 escenario:
  telegram new lead). 4 anchors reservados para extender a más
  escenarios cuando S12 audite el log de tech debt; por ahora es
  suficiente. 4 entradas DEFERRED-S12 documentadas en
  `05-tech-debt-log.md` (`_tool_dedup_tracker` typed, lazy imports
  brand/offer, SessionLocal-per-event, knowledge_builder factory). Cada
  una probable WONT-FIX al cierre S12 — el plan no debe forzar fixes
  artificiales si la deuda no es bloqueante.

---

## Decisiones clave

- **Snapshot diff = 0 después de CADA commit, no solo al final**:
  - Tomada: cada uno de los 7 commits corre el snapshot test antes de
    pushear. Si diff > 0 → revertir el commit + investigar.
  - Razón: el plan original ("Goldens diff = 0 al cierre del sprint")
    era ambiguo respecto al alcance. Ejecutar el snapshot por commit
    sirvió como ratchet local — atrapamos 3 patches frágiles antes de
    que se acumularan: (1) `chat_mod.EventBus.publish` rompió post-Commit 2
    al borrarse el import; (2) `chat_mod._update_customer_traits` patch
    inválido post-Commit 3 (call site movido a `IdentityResolver`); (3)
    `chat_mod.datetime` patch inválido post-Commit 5 (datetime ya no
    importado en chat.py). Los 3 los detectamos en el primer pytest del
    siguiente commit y los corregimos antes de mover.
  - Alternativa descartada: snapshot solo al cierre del sprint (Commit 7).
    Hubiese acumulado deuda — diff = ~5 buckets distintos al final, sin
    mapear a un commit específico. Imposible bisect.

- **Helpers compartidos en `closer_studio/lead_helpers.py` como módulo, NO
  en una clase**:
  - Tomada: `get_checkpoint`, `get_last_message_preview`,
    `resolve_display_name`, `resolve_avatar`, `resolve_lifecycle_stage`
    son **funciones libres** que reciben `db` + `lead_id` / `lead`.
  - Razón: ninguna requiere estado. Una clase `LeadRepoHelpers(db)` que
    instanciara las 3 services tendría que crear instancia 3 veces (una
    por servicio) o pasarse como dependencia — ambas peor que importar
    funciones libres. Research 2026 (CQRS lightweight FastAPI) confirmó
    que el split CQRS no requiere base classes — funciones puras + DTOs
    son suficientes.
  - Alternativa descartada: clase abstracta `BaseConversationService`
    con helpers como methods. Premature abstraction (3 consumers
    similares ≠ herencia justificada — `04-principles.md §1.2`).

- **`CloserStudioService` mantenido como facade post-split**:
  - Tomada: facade thin de 124 LOC delega a los 3 services.
  - Razón: la API en `api/closer_studio.py` instancia
    `CloserStudioService(db)` en 11 callsites + tests pre-existentes
    test_closer_studio_service.py usa la facade en 19 lugares. Migrar
    todos a los 3 services específicos = 30+ cambios cross-archivo. La
    facade satisface back-compat sin diluir el split — el comentario de
    docstring deja claro que "new code should depend on the dedicated
    service".
  - Alternativa descartada: borrar `CloserStudioService` y migrar todo.
    Scope creep para una sub-fase enfocada en split. La deprecación se
    hace de forma orgánica: cuando un endpoint nuevo se cree, llama
    directo al service correcto.

- **`smart_debounce_runner.py` como módulo separado, NO como método de
  ChatOrchestrator**:
  - Tomada: el cuerpo del `smart_debounce_task` se movió a una función
    libre `run_smart_debounce(*, buffer_service, buffer_key,
    channel_adapter, on_complete)`. La method en el orchestrator es un
    delegate de 6 líneas.
  - Razón: el test arch `test_chat_orchestrator_loc_ratchet.py` tiene
    ceiling 400 LOC. Sin esta extracción, chat.py quedaba en 427 LOC
    (sobre el ceiling). Strangler Fig dicta extraer, no adaptar el
    ceiling. Y la lógica de timing está protegida (§3) — moverla a un
    runner module mantiene la byte-equivalencia con la versión anterior.
  - Alternativa descartada: bumpear ceiling a 450 LOC. Contradice
    "shrink-only". Mejor extraer.

- **`UUID` movido a `TYPE_CHECKING` en `semantic_router.py`**:
  - Tomada: `from uuid import UUID` ahora está en
    `if TYPE_CHECKING:` bloque post-S11B.
  - Razón: ruff TC003 se activó porque `UUID` solo aparecía en
    annotations (post `from __future__ import annotations`). El test
    arquitectónico TC003 falla CI si no se mueve. Pre-S11B no tenía
    `from __future__ import annotations`, ahora sí. La diferencia: las
    annotations post-future-import son strings lazy-evaluadas.
  - Alternativa descartada: quitar `from __future__ import annotations`
    del archivo. Inconsistente con el resto del código (todos los
    nuevos archivos S11B lo tienen).

- **NO formalizar lazy imports brand/offer como ports**:
  - Tomada: dejar `style_anchor_retriever.py` y `business_repository.py`
    con sus lazy imports actuales. Ratchet
    `test_no_new_sales_agent_module_imports` mantiene baseline 4.
  - Razón: la decomposition de chat.py NO ejerció esos paths. La
    `IdentityResolver` no toca brand. La `ConversationPipeline` solo
    delega a `TenantKnowledgeBuilder` (un consumer de los lazy imports,
    pero no los expande). Crear ports nuevos sería scope creep:
    afectaría `shared/links/ports/`, requeriría tests cross-módulo, y
    la decomposition no lo demanda.
  - Alternativa descartada: portar a ports retroactivamente. Out of
    scope; mejor dejarlo para S7+ si una nueva feature lo gatilla.

---

## Sorpresas / gotchas críticos

- **`_init_repos` patched por nombre en snapshot helper**: el helper
  hace `monkeypatch.setattr(f"{chat_mod}.ChatOrchestrator._init_repos", ...)`.
  Eso solo funciona porque `_init_repos` siguió siendo método de
  ChatOrchestrator — si lo hubiéramos extraído, el patch fallaría. La
  decisión de mantenerlo como composición root (orchestrator dueño del
  SessionLocal lifecycle) es la correcta arquitectónicamente Y la que
  preserva el snapshot.

- **Ruff auto-fix `--fix` borra imports muertos agresivo**: cada commit
  Strangler Fig reduce los imports usados en chat.py. `ruff check --fix`
  borra los `F401` antes que yo me dé cuenta. El primer ciclo tras
  Commit 2, 4 imports muertos se borraron silenciosamente. **Lección
  S12**: revisar `git diff` post-`ruff --fix` — los imports borrados
  pueden romper monkeypatches. Patch sites siempre a definition site.

- **Arch test `test_folder_naming` rechaza `_lead_helpers.py`**: el regex
  `^[a-z][a-z0-9_]*\.py$` requiere primer caracter alfanumérico. El
  prefijo `_` (convención Python "private module") falla. Renombré a
  `lead_helpers.py` (sin underscore). El módulo sigue siendo
  package-private (no se exporta vía `closer_studio/__init__.py`).
  Convención Python vs convención Nicolify — gana Nicolify.

- **`from __future__ import annotations` propaga ruff TC**: todos los
  archivos S11B nuevos tienen `from __future__ import annotations`. Eso
  vuelve las annotations strings lazy-evaluadas, lo que activa
  TC001/TC003 ruff rules para mover types-only imports a TYPE_CHECKING
  blocks. Modelos como `AgentStateCheckpointModel` que solo aparecen
  como annotation deben ir en TYPE_CHECKING. No es bug — es enforcement
  estricto de "runtime imports vs type-only imports".

- **El snapshot helper grew 200+ LOC durante S11B**: cada extraction
  agregó 1-2 patches nuevos. Al cierre, el helper tiene ~440 LOC. No es
  ideal — pero el helper es código de test, no de prod, y su shape es
  deliberadamente exhaustiva (cada patch documenta CON qué external
  collaborator interactúa el orchestrator). Trade-off aceptable.

---

## Recomendaciones accionables para S12

- [ ] **Audit `05-tech-debt-log.md`** — buscar todas las entradas
  DEFERRED-S* y validar que apunten a S12. Si alguna apunta a S+1 o
  post-redesign, reabrir discusión CTO o convertir a WONT-FIX con
  razón documentada (Definition of Done del plan: cero DEFERRED al
  cierre S12).

- [ ] **Validar que las 4 deudas DEFERRED-S12 tienen target real**:
  `_tool_dedup_tracker` typed (TypedDict update), lazy imports
  brand/offer (probable WONT-FIX), SessionLocal-per-event (probable
  WONT-FIX), knowledge_builder factory (probable WONT-FIX). Si todos
  son WONT-FIX, S12 cierre es elemental — solo audit + scan + ratchet.

- [ ] **NO extender el snapshot framework a más escenarios** salvo que
  S12 detecte un bug específico que requiera un escenario nuevo. El
  snapshot actual cubre `telegram + new lead`. Escenarios adicionales
  (returning user, human_mode, frozen lead, IG enrichment) son
  candidatos válidos pero out-of-scope si no hay regresión visible.

- [ ] **Tier pricing >200k**: arch ratchet en S12 que falle si el
  calculator empieza a recibir tokens > 200k sin tier resolution. Hoy
  no aplica al volumen LATAM, pero la arch test bloquea regresión
  silenciosa.

- [ ] **Presidio WONT-FIX**: documentar en S12 la decisión + condición
  reapertura (>5% drift en reconciliation worker post-Phase 4
  observability rebuild de copilot, que ya cerró).

- [ ] **`typing_simulation_cpm` wiring**: validado por eval loop S10.
  S12 puede liberar el §3 fragment para que `OutputManager` consuma el
  `ChannelFormat.typing_simulation_cpm` del registry.

- [ ] **Voseo scan final**: `grep -E '(vos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|configurá|elegí)'`
  sobre `backend/src/modules/sales_agent/` + `frontend/src/features/closer-studio/`.
  Ya verificado en S00 (0 hits). Re-correr al cierre para confirmar
  que ningún commit S11A/S11B introdujo voseo (probable 0 hits).

- [ ] **NO tocar §3 protected**: `BufferService.smart_debounce`,
  `OutputManager.process_response`, `enrollment_*`,
  `agent_state_checkpoint_model`, webhook adapters, `follow_up_engine.py`
  — cualquier touch requiere PARAR y preguntar al usuario.

---

## Hooks listos

- `src/modules/sales_agent/application/orchestrator/audit_emitter.py::AuditEmitter`
  — 4 staticmethods (track_message_received, publish_lead_captured,
  emit_assistant_message, emit_human_mode_message). Pattern para
  futuros eventos: agregar staticmethod, opcional best-effort try/except.

- `src/modules/sales_agent/application/orchestrator/identity_resolver.py::IdentityResolver`
  — 5 staticmethods (resolve_customer, enrich_instagram_profile,
  update_customer_traits, resolve_lead, process_customer_lifecycle).
  Pattern para nuevas identidades: agregar staticmethod en este file.

- `src/modules/sales_agent/application/orchestrator/conversation_pipeline.py::ConversationPipeline`
  — 14 staticmethods (full state machine + dispatch). Si S+ agrega un
  paso (e.g., RAG retrieval pre-agent_app.ainvoke), va aquí.

- `src/modules/sales_agent/application/orchestrator/smart_debounce_runner.py::run_smart_debounce`
  — free function. §3 protected timing. NO tocar salvo instrucción
  explícita.

- `src/modules/sales_agent/application/services/closer_studio/{query,command,kpi}_service.py`
  — 3 services Query / Command / Kpi. New endpoints en `api/closer_studio.py`
  deberían depender directamente del service correcto, NO de la facade.

- `src/modules/sales_agent/application/services/closer_studio/lead_helpers.py`
  — `get_checkpoint`, `get_last_message_preview`,
  `resolve_display_name`/`resolve_avatar`/`resolve_lifecycle_stage`. Pure
  functions. Si un nuevo Closer Studio service necesita una de estas
  primitives, importa directo (no duplicar en la nueva clase).

- `src/modules/sales_agent/domain/semantic_routes.py::SYSTEM_ROUTES`
  — agregar route nueva = agregar entrada al dict + fixture in
  `test_semantic_router.py`.

- `src/modules/sales_agent/application/services/tenant_route_overlay.py::collect_tenant_anchors`
  — pure fn, fully testable. Si Offer agrega otra dimensión semántica
  (e.g., desire_phrases), extender aquí.

- `tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py`
  — `install_chat_module_patches(monkeypatch, capture)` patches todo
  collaborator del orchestrator. Reusable como fixture para escenarios
  adicionales (returning user, human_mode, frozen lead).

- `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py`
  — 1 escenario `telegram_new_lead_baseline.json`. Patrón a copiar para
  escenarios adicionales.

- `tests/architecture/test_chat_orchestrator_loc_ratchet.py`
  — ceiling 400 LOC, shrink-only. Lower si una refactor lo permite.

---

## Riesgos abiertos

- **Snapshot helper acoplado a paths internos**: si alguien renombra
  `src.shared.domain.events.EventBus` o
  `src.modules.sales_agent.application.services.knowledge_builder.TenantKnowledgeBuilder`,
  el snapshot rompe. Mitigación: el helper documenta cada patch site
  con un comentario inline explicando POR QUÉ usa el definition site.
  Refactor futuro debe re-mapear.

- **Closer Studio facade puede crecer**: si nuevos endpoints añaden
  métodos a `CloserStudioService` (back-compat hábito), el facade puede
  re-bloatar. Mitigación: agregar arch test `test_closer_studio_facade_loc_ratchet.py`
  con ceiling 150 LOC en S12 si vale el ratchet.

- **`CHAT_LOC_CEILING = 400`** es arbitrario. Si una feature legítima
  requiere subir a 420, hay que justificar. La regla `04-principles.md
  §1.3` (alta cohesión) dice que el archivo debe tener UNA
  responsabilidad — chat.py la tiene (composición root). LOC es proxy
  imperfecto.

- **`agent_app.ainvoke` patch en definition site funciona porque
  `agent_app` es singleton**. Si en algún momento el graph se construye
  per-request, el patch puede fallar (cada instancia tendría su propio
  `ainvoke`). Mitigación: `test_chat_orchestrator_snapshot.py` correrá
  rojo y forzará investigación.

---

## Tech debt detectado (NO arreglado, ya en log)

Las siguientes entradas viven en `05-tech-debt-log.md` sección "Detectados
durante S11B" + reabren a S12 (probables WONT-FIX al cierre):

- [LOW] `_tool_dedup_tracker` magic string (S1) → DEFERRED-S12.
- [LOW] Lazy imports brand+offer (S00) → DEFERRED-S12 (probable WONT-FIX).
- [LOW] Subscribers SessionLocal per-event (S1) → DEFERRED-S12 (probable
  WONT-FIX).
- [LOW] `knowledge_builder.py` factory amplio (S00) → DEFERRED-S12
  (probable WONT-FIX).

---

## Fuentes research útiles

- [Strangler Fig Pattern (microservices.io / AWS prescriptive guidance /
  Geek Planets Feb 2026)](https://thegeekplanets.medium.com/strangler-fig-pattern-explained-the-safer-path-from-monolith-to-microservices-d97f0efa8619)
  — confirmó "transform → coexist → eliminate" en 3 pasos. Aplicado:
  cada commit Strangler Fig **transforma** (crea nueva clase) +
  **coexiste** (chat.py wrappers delegan) + **elimina** (Commit 5
  borra los wrappers). Snapshot byte-equal = shadow validation.

- [Python dataclass `kw_only=True` inheritance (Python typing 2026,
  mypy PR #19018)](https://github.com/python/mypy/pull/19018) —
  consultado para evaluar el hack `lead_id: UUID = None # type: ignore`
  de S11A. Decisión S11B: NO migrar a `kw_only=True` retroactivamente
  porque no introdujimos nuevos dataclasses children. La deuda persiste
  pero no creció.

- [Lightweight CQRS for FastAPI 2026 (cosmicpython chapter 12, OneUptime
  blog Jan 2026)](https://oneuptime.com/blog/post/2026-01-30-cqrs-pattern-microservices/view)
  — confirmó "same DB, separate models for reads/writes en single
  service". Aplicado al `closer_studio_service.py` split. Read side
  (`ConversationQueryService`) talks to a thin query layer returning
  flat DTOs. Write side (`ConversationCommandService`) maintains rich
  domain interactions (resume_objective, frozen flags, etc).

---

## Métricas medidas

- **LOC delta** (sales_agent post-S11B vs S11A):
  - `application/orchestrator/chat.py`: 1140 → 337 (-803, -70%).
  - `application/orchestrator/audit_emitter.py`: 0 → 160 (new).
  - `application/orchestrator/identity_resolver.py`: 0 → 224 (new).
  - `application/orchestrator/conversation_pipeline.py`: 0 → 518 (new).
  - `application/orchestrator/smart_debounce_runner.py`: 0 → 154 (new).
  - `application/services/closer_studio_service.py`: 624 → 124 (-500, facade).
  - `application/services/closer_studio/__init__.py`: 0 → 25 (new).
  - `application/services/closer_studio/lead_helpers.py`: 0 → 96 (new).
  - `application/services/closer_studio/query_service.py`: 0 → 286 (new).
  - `application/services/closer_studio/command_service.py`: 0 → 272 (new).
  - `application/services/closer_studio/kpi_service.py`: 0 → 79 (new).
  - `application/services/semantic_router.py`: 329 → 220 (-109).
  - `application/services/tenant_route_overlay.py`: 0 → 42 (new).
  - `domain/semantic_routes.py`: 0 → 128 (new).
  - **Net cross-orchestrator + closer_studio + semantic_router**: 2093 → 2665
    (+572 LOC). Aumento esperado: docstrings nuevos + boilerplate de
    classes + back-compat facade. **El target real (cohesión, archivos
    < 600 LOC, single responsibility per file) está cumplido**: máximo
    archivo nuevo es 518 LOC (ConversationPipeline), promedio 234
    LOC/archivo.

- **Tests verde**: 3313 (638 architecture + 2675 modules). Pre-S11B:
  3270 (637 + 2633). Net +43 tests (8 audit_emitter + 10
  identity_resolver + 16 conversation_pipeline + 7 tenant_route_overlay
  + 1 chat_orchestrator_loc_ratchet + 1 chat_orchestrator_snapshot).

- **Snapshot tests**: 3 verdes (sales handler S11A + copilot handler
  S11A + chat orchestrator telegram new lead S11B). Diff = 0 byte-equal
  preservado a través de los 7 commits.

- **Coverage estimado**: cada nueva clase con 70%+ test coverage en su
  test file dedicado. Cobertura sales_agent global no medida en este
  sprint (los tests nuevos sumaron a la base existente sin medir
  delta).

- **Commits**: 7 (`f5bc583c`, `077ed6df`, `48f3f2ef`, `b14175cf`,
  `231d85a5`, `ef972405`, `7367b5f8`). Cada uno revertible solo. Cada
  uno con quality gates verde y snapshot diff = 0.

- **Quality gates nativos**: ruff check + format ✅, pytest arch ✅,
  pytest modules ✅, admin smoke ✅. CI parity nativo (no docker exec).

- **§3 protected intacto**: BufferService, OutputManager,
  agent_state_checkpoint, enrollment, webhooks, follow_up_engine — `git
  diff 8cc9ea2c..HEAD` sobre esos paths = 0 cambios.

- **Files de log** (informational):
  - `chat.py` 337 LOC bajo ceiling 400 ✓
  - 4 nuevos archivos en orchestrator/ con responsabilidades claras
  - 5 nuevos archivos en services/closer_studio/ con CQRS-lite split
  - 3 nuevos archivos para semantic_router refactor (domain split +
    application overlay + thin singleton).
