# Learnings · S11A · shared base lift

> Doc para S11B (orchestrator decomposition). El lift dejó dos handlers
> en 85 / 83 LOC + un base único de 634 LOC + un snapshot framework
> determinístico que protege la decomposition contra cambios de shape
> no intencionales. Sin esa red de seguridad, S11B sería refactor a
> ciegas.

---

## Resumen (3 líneas)

- **Entregado**: `BaseAgentCallbackHandler` shared (102 → 634 LOC)
  absorbe los 8 callbacks LangChain + helper extractors + el Template
  Method skeleton `_persist_llm_call` + `_safe_rollback` + dataclasses
  `_LLMSpan` / `_ToolSpan` / `_ChainSpan`. Sales subclass quedó en
  **85 LOC** (-87%), copilot subclass en **83 LOC** (-86%). Net delta
  cross-handlers: 1353 → 802 LOC. Snapshot framework determinístico
  (`tests/shared/agent_observability/test_callback_handler_snapshot.py`)
  con baselines JSON byte-equal. 5 commits revertibles, cada uno con
  quality gates verde. 3270 tests verde (637 arch + 2633 modules).
- **Decisión no obvia**: el plan original pedía "goldens del eval loop
  S10 estables 2 sem" — imposible (S10 cerró 2026-04-28). Pre-flight
  decidió **snapshot determinístico de pipeline outputs con LLM
  mockeado** en lugar de goldens LLM. Cubre el caso "refactor preserva
  shape" que es exactamente lo que validamos en S11A. Goldens S10
  siguen para drift detection del judge weekly.
- **Listo para S11B**: el snapshot framework cubre callback handler.
  Para Sub-sprint B agregar `tests/snapshots/orchestrator/` con
  fixtures que ejercen `process_chat_flow` con LLM + repos +
  channel_adapter mockeados. Cada commit Strangler Fig (extraer
  AuditEmitter / IdentityResolver / ConversationPipeline / split
  closer_studio_service / refactor semantic_router) debe re-correr
  los snapshots con diff = 0 byte-equal. Si diff > 0 → revertir.

---

## Decisiones clave

- **Snapshot determinístico de pipeline outputs vs goldens LLM**:
  - Tomada: snapshot byte-equal con LLM mockeado captura **shape** del
    pipeline (rows escritas a repos, args de cada call, eventos
    publicados). LLM mocked devuelve fixture fijo.
  - Razón: goldens LLM tienen variance natural (incluso con temp=0,
    multi-provider routing); el plan original asumía 2 sem de
    histórico para baseline de variance, físicamente imposible. El
    snapshot determinístico captura **exactamente** lo que el refactor
    debe preservar (shape de la pipeline) sin contaminarse por
    variance LLM.
  - Alternativa descartada: esperar 2 sem para acumular histórico
    semanal del cron `weekly_sales_agent_quality_eval`. Bloquea S11
    completa y no resuelve el problema central — el judge mide
    calidad LLM, no shape de pipeline.

- **Retrofit copilot mismo Sub-sprint A**:
  - Tomada: lift levantó AMBOS handlers (sales + copilot) en mismo
    set de commits. Copilot pasó de heredar `BaseCallbackHandler`
    (LangChain) a heredar `BaseAgentCallbackHandler` (shared) en
    commit 3.
  - Razón: el plan original asumía "coordinación con copilot redesign
    team" — no existe equipo separado. Postponer el retrofit para S12
    crearía deuda flotante que el plan se comprometió a evitar (S12
    DoD = cero DEFERRED). Mantenerlo en S11A satisface el principio
    DRY (`04-principles.md §1.2`): 2 consumers reales = threshold
    correcto para lift al base.
  - Alternativa descartada: postponer retrofit a S12 o crear S11.5.
    S12 ya tiene 4 cosas (tier pricing, Presidio, typing_simulation_cpm
    wiring, voseo scan); agregarle 500+ LOC retrofit cross-módulo
    rompe la fase final. Crear S11.5 contradice la decisión CTO
    2026-04-28 de mantener el plan autocontenido en S0..S12.

- **`_safe_rollback` en base con `getattr(self, "db_session", None)`**:
  - Tomada: el base lee `db_session` dinámicamente; sales lo declara
    como field, copilot no lo necesita.
  - Razón: copilot no maneja transacción explícita en el callback
    (su transacción vive en `chat.py`); sales sí (cada subscriber
    creates su propio `SessionLocal`). Hardcodear `db_session: Any`
    en el base como required force a copilot a inventar un stub.
    Usar `getattr` permite que el base sea agnóstico al modelo de
    transacción del consumer.
  - Alternativa descartada: declarar `db_session: Any | None = None`
    como field del base. Funcionaría pero ensucia la signature de
    todos los consumers; el `getattr` es estructuralmente más
    honesto al patrón Python (duck typing).

- **Sales y copilot dataclass fields ordering hack**:
  - Tomada: Sales subclass declara `lead_id: UUID = None` con
    `# type: ignore[assignment]`. Hack para no romper el dataclass
    inheritance ordering (los fields del padre con default no pueden
    ser seguidos por fields del hijo sin default).
  - Razón: alternativa "limpia" requiere refactor del callsite
    (`build_sales_agent_callback_handler` factory) para usar
    `@dataclass(kw_only=True)` o similar. Scope creep para el lift.
    El `# type: ignore` es localizado y documentado. Sub-sprint B
    NO lo toca.
  - Alternativa descartada: convertir todos los fields del base a
    `kw_only=True`. Cambia el constructor signature de ambos
    handlers (breaking en factory + tests). Diferido a S11B si
    alguna decomposition lo gatilla.

- **Snapshot helper monkeypatch path apunta al base**:
  - Tomada: `freeze_handler_clock` parchea `datetime` y `time` en
    `src.shared.agent_observability.recording.base_callback_handler`.
  - Razón: post-lift los callbacks viven en el base; el clock se
    invoca desde ahí. Parchar el subclass no funciona porque el
    subclass NO importa `datetime` ni `time` ya.
  - Alternativa descartada: parchar ambos paths simultáneamente. Es
    redundante post-lift. Para back-compat con callers viejos, la
    signature acepta el `module_path` arg pero lo ignora.

---

## Sorpresas / gotchas críticos

- **Copilot baseline JSON requirió regeneración intencional**: pre-lift
  copilot NO pasaba `data` ni `duration_ms` en `node_enter` /
  `node_exit` rows. Sales sí. El lift unifica el contract via abstract
  `_persist_trace_event_row(data, duration_ms, ...)` — copilot ahora
  pasa `data: {}` y `duration_ms: null` también (paridad). DB rows
  son idénticas (campos nullable), solo cambia la shape del kwargs
  capture. Documentado en commit `30ef49e7`. **Lección S11B**: cuando
  el snapshot diff aparezca, primero validar si es regresión
  (revertir) o paridad intencional (regenerar baseline + documentar).

- **`from __future__ import annotations` y dataclass abstracts**: el
  base es `@dataclass + ABC + abstractmethod`. Si el subclass tiene
  `from __future__ import annotations` (por defecto en este repo), el
  type checker puede confundirse con la herencia. Trabajó OK en este
  caso porque las concretas implementan los abstracts, pero
  watchpoint: si S11B agrega un nuevo abstract, verificar que las
  subclases lo implementen.

- **Ruff `TC004` cuando se importa runtime use desde
  `TYPE_CHECKING`**: el dataclass field `pricing_resolver:
  PricingResolver` requiere `PricingResolver` en runtime para
  introspección, NO solo para type hint. Tuve que mover `from
  src.shared.agent_observability.pricing.resolver import
  PricingResolver` fuera del bloque TYPE_CHECKING. Mismo para
  `FXResolver`. **Lección S11B**: cuando un Protocol / dataclass
  field tipa con clase shared, el import va al top-level, no al
  bloque condicional.

- **ANN401 en `**kwargs: Any` Template Method passthrough**: ruff
  flagea `**kwargs: Any` en signatures de override. El override pasa
  TODO el kwarg dict al repo subyacente; tipar cada uno individualmente
  duplicaría la signature del abstract base. `# noqa: ANN401 — Template
  Method passthrough` es la convención adoptada en el repo
  (consistente con sales/copilot anteriores).

- **`_safe_rollback` arch test escanea base post-lift**: el arch test
  S6 `test_rollback_invoked_on_persist_failures` originalmente
  escaneaba el sales handler. Post-lift, `_safe_rollback` se invoca
  en los callbacks del base. El arch test debe leer `BASE_HANDLER`
  en lugar de `CALLBACK_HANDLER`. Mismo para
  `test_callbacks_are_wrapped_in_try_except`. Estos cambios fueron
  fold-in al commit 4 (no separados a un commit 5 propio) porque
  rompía la regla "cada commit revertible solo" si se postponían.

---

## Recomendaciones accionables para S11B

- [ ] **Capturar snapshot pipeline pre-decomposition** ANTES del primer
  refactor de `chat.py`. Path: `tests/snapshots/orchestrator/`. Cubrir
  5-10 escenarios canónicos: lead nuevo (telegram), lead existente
  con human_mode, lead con frozen_at, lead con resume_objective,
  reactivación, etc. Mockear LLMFactory + channel_adapter +
  SessionLocal + event_bus.
- [ ] **Cada commit Strangler Fig (AuditEmitter, IdentityResolver,
  ConversationPipeline) debe correr el snapshot** post-extraction y
  asertar diff = 0. Si diff > 0 → revertir el commit + investigar.
  Documentar en `learnings/S11B-*.md` cualquier diff intencional
  con razón.
- [ ] **Empezar por AuditEmitter** (extraer event publish + audit log).
  Es la pieza con menor blast radius — solo agrega un layer adelante
  del `event_bus.publish` actual. ChatOrchestrator NO se rompe si la
  extracción se aborta a medias (legacy paths siguen). Test de
  unit nuevo: `tests/modules/sales_agent/orchestrator/test_audit_emitter.py`.
- [ ] **`closer_studio_service.py` split usar repo helper compartido
  para `_get_checkpoint`**. Es el único método cross-Service (Query
  + Command lo usan). Subir a `application/services/_checkpoint_repo.py`
  o similar. NO duplicar.
- [ ] **`semantic_router.py` registry**: el Strategy pattern es claro —
  `domain/semantic_routes.py` con `SYSTEM_ROUTES` const, `application/
  services/semantic_router.py` con la clase singleton (cache + embed
  model), nuevo `application/services/tenant_route_overlay.py` con
  `register_tenant_routes`. Mantener back-compat de
  `SemanticRouter.detect_intent` y `detect_and_accumulate` —
  callers sales en `chat.py` y `nodes.py` no cambian.
- [ ] **NO tocar §3 protected**: `BufferService.smart_debounce`,
  `OutputManager.process_response`, `enrollment_*`,
  `agent_state_checkpoint_model`, webhook adapters,
  `follow_up_engine.py` — cualquiera de ellos requiere PARAR y
  preguntar al usuario. El plan original es claro.
- [ ] **`_tool_dedup_tracker` magic string** (DEFERRED-S11B desde
  S1): convertir a TypedDict update sólo si la `ConversationPipeline`
  extracción lo requiere — si no, dejar para una fase posterior.
- [ ] **Lazy imports brand + offer** (DEFERRED-S11B desde S00): si
  `IdentityResolver` o `ConversationPipeline` extraen el `_build_agent_identity`
  / `_build_brand_voice` flows, formalizar via port en
  `shared/links/ports/`. Si no, dejarlos como están (TYPE_CHECKING
  passes the arch test).

---

## Hooks listos

- `src/shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler`
  — Template Method completo. Nuevos agentes solo overriden
  `_persist_llm_call_row` + `_persist_trace_event_row` + agregan fields
  agent-specific.
- `src/modules/sales_agent/observability/recording/callback_handler.py::SalesAgentCallbackHandler`
  — referencia: 85 LOC, herencia limpia.
- `src/modules/copilot/observability/recording/callback_handler.py::ObservabilityCallbackHandler`
  — referencia: 83 LOC, idem.
- `tests/shared/agent_observability/_callback_snapshot_helpers.py` —
  helpers para snapshot determinístico: `freeze_handler_clock`,
  `replay_canonical_sequence`, `build_pricing_resolver_stub`,
  `build_fx_resolver_stub`, `build_capturing_repos`,
  `assert_matches_snapshot`. Reusable para Sub-sprint B (extender
  con replay para `process_chat_flow` end-to-end).
- `tests/shared/agent_observability/test_callback_handler_snapshot.py`
  — patrón a copiar para snapshots de orchestrator. Determinismo
  via monkeypatch de `datetime`, `time.monotonic`, `uuid4` en módulo
  base + del orchestrator.
- `tests/snapshots/callback_handler/{sales,copilot}_handler_baseline.json`
  — baselines byte-equal. Cualquier diff post-S11B = revertir o
  documentar como intencional.
- `tests/architecture/test_sales_agent_callback_handler_invariants.py`
  — patrón AST scan + LOC ratchet (`test_subclass_below_loc_target`).
  Reusable para arch tests de orchestrator decomposition (`chat.py
  < 400 LOC`).
- `tests/architecture/test_sales_agent_observability_invariants.py`
  — `_read_handler_chain()` helper: concat base + subclass. Útil
  para invariantes que viven cross-archivo post-lift.

---

## Riesgos abiertos

- **Sales `lead_id: UUID = None  # type: ignore[assignment]`** es un
  hack de dataclass ordering. Si S11B introduce un nuevo dataclass
  child, el patrón se replica. Solución limpia: migrar todo el árbol
  a `@dataclass(kw_only=True)` en una pasada. Diferido a Sub-sprint B
  si gatilla problema; si no, S12 cleanup.
- **Snapshot baselines son frágiles a renames de campos en repos**: si
  alguien cambia `LlmCallRepository.add` signature (rename `model_responded`
  → `model_responded_id`, por ejemplo), el snapshot diff aparece.
  Watchpoint S11B: la decomposition NO debe tocar repos — solo el
  orchestrator. Si toca repos, regenerar baselines documentado.
- **`from __future__ import annotations` en sales subclass + dataclass
  abstracts**: cubierto por tests, pero si LangGraph cambia su
  introspection runtime, podría fallar. Watchpoint si `from
  __future__ import annotations` se borra del subclass S6.5 (legacy
  drop) — los abstract checks empiezan a tipar realmente.
- **Coverage del base 85% (vs 100% sales subclass)**: las líneas no
  cubiertas son edge cases del Template Method (rollback paths,
  span no encontrado). Sub-sprint B podría agregar tests si la
  decomposition altera esos paths; si no, dejar para S12.

---

## Tech debt detectado (NO arreglado)

- [MEDIUM] `chat.py` orchestrator overgrown 1140 LOC → `05-tech-debt-log.md`
  línea 36 (DEFERRED-S11B).
- [MEDIUM] `closer_studio_service.py` 8+ responsabilidades →
  `05-tech-debt-log.md` línea 38 (DEFERRED-S11B).
- [MEDIUM] `semantic_router.py` routes hardcoded → `05-tech-debt-log.md`
  línea 39 (DEFERRED-S11B).
- [LOW] `_tool_dedup_tracker` magic string → `05-tech-debt-log.md`
  línea 42 (DEFERRED-S11B).
- [LOW] Subscribers crean SessionLocal per-event → `05-tech-debt-log.md`
  línea 41 (DEFERRED-S11B).
- [LOW] Lazy imports brand+offer → `05-tech-debt-log.md` línea 40
  (DEFERRED-S11B).

---

## Fuentes research útiles

- [Strangler Fig Pattern (microservices.io / AWS prescriptive guidance /
  Geek Planets Feb 2026)](https://thegeekplanets.medium.com/strangler-fig-pattern-explained-the-safer-path-from-monolith-to-microservices-d97f0efa8619)
  — confirmó el patrón "dual-write/shadow comparing legacy vs new"
  para decomposition. Aplicado al callback handler: snapshot byte-equal
  pre/post como shadow validation. Decommission inmediato — sales
  handler quedó en 85 LOC sin código duplicado residual.
- [LangChain BaseCallbackHandler official docs](https://python.langchain.com/api_reference/core/callbacks/langchain_core.callbacks.base.BaseCallbackHandler.html)
  — confirmó que el Template Method via subclassing es la API
  idiomática. Sin breaking changes 2026.
- [pytest snapshot — Syrupy + inline-snapshot March 2026](https://github.com/syrupy-project/syrupy)
  — descartado como librería externa; el snapshot custom (JSON file +
  monkeypatch determinístico) es suficiente para 2 tests, no
  justifica nueva dependencia.

---

## Métricas medidas

- **LOC delta**:
  - Base: 102 → 634 (+532, absorbe plumbing).
  - Sales: 668 → 85 (-583, -87%).
  - Copilot: 583 → 83 (-500, -86%).
  - Net cross-handlers: 1353 → 802 (-551 duplicación eliminada).
- **Tests verde**: 3270 (637 architecture + 2633 sales/copilot/admin/
  shared modules).
- **Snapshot tests**: 2 verdes (sales + copilot byte-equal con
  baseline).
- **Coverage observability**: 91% (sales handler 100%, base 85%).
- **Commits**: 5 (`7c0b921a` snapshot framework + plan split,
  `6664263d` lift helpers, `30ef49e7` copilot retrofit + delegate,
  `8cc9ea2c` lift 8 callbacks + arch tests update, +1 docs final).
- **Quality gates nativos**: ruff check + format ✅, pytest arch ✅,
  pytest modules ✅, admin smoke ✅.
- **§3 protected intacto**: BufferService, OutputManager,
  agent_state_checkpoint, enrollment, webhooks, follow_up_engine —
  ninguno tocado en Sub-sprint A.
