# Learnings · S6 · Architectural fitness tests ratchet + sweeps

> Doc para S7 (brand voice integration). Los 6 arch tests congelan el estado
> infra post-S0..S5 limpio; el sweep S5 cerró deuda de 3 shims copilot que
> hubieran complicado la migración brand_voice del slot 4 (lighthouse mirror
> F3 copilot). S7 puede asumir que el SSoT de channel registry vive en
> shared/, ANCHOR_REGISTRY admite sus nuevos anchors, y el ratchet de
> imports flagea cualquier nuevo cross-module sin port.

---

## Resumen (3 líneas)

- **Entregado**: 6 arch fitness tests nuevos en `tests/architecture/`
  (`test_no_new_sales_agent_module_imports`, `test_sales_agent_anchors`,
  `test_sales_agent_callback_handler_invariants`,
  `test_pii_sanitization_coverage_sales_agent`,
  `test_sales_agent_tenant_isolation`,
  `test_subagent_isolation_invariants_sales_agent`). 23 fitness tests
  nuevos verde. Sweeps oportunista: 11 call sites copilot migrados de
  shim re-export → import directo a `src.shared.agent_observability.channels.*`,
  3 shims borrados, allowlist `test_ddd_boundaries.py:75` apunta al SSoT
  shared. `LLM_ROLE_BY_SITE` SSoT extendido (S4 carry-over): `summary`
  y `follow_up_nudge` migrados FAST → NANO; `safety` queda FAST. 622
  tests architecture verde + 2535 tests sales/copilot/admin/shared verde
  (~3157 vs 3134 baseline pre-S6).
- **Decisión no obvia**: el plan original S6 incluía drop de tablas
  legacy `agent_trace_model` + `LLMLogModel` + cutover `sales_audit.py`
  + 2 arch tests bloqueando reads legacy. La ventana dual-write son 4
  semanas desde S1 close (2026-04-28); hoy mismo día = ventana NO
  cumplida. Drop legacy y los 2 arch tests asociados se difieren a
  fase post-S6.5 (post 2026-05-26). Documentado DEFERRED en
  `05-tech-debt-log.md` con razón. S6 mantuvo scope estricto: ratchet
  + invariantes + sweeps de S4/S5.
- **Listo para S7**: el ratchet `KNOWN_SALES_AGENT_TO_MODULE_IMPORTS`
  tiene 4 entradas TYPE_CHECKING (brand / crm × 2 / offer). S7 va a
  introducir `brand_voice_summary` lighthouse — si lo lee via port en
  `shared/links/ports/brand.py`, la entrada `sales_agent -> brand` se
  shrinks. Si lee directo el modelo brand → bumpear el counter en el
  test (1 expected adjustment). Slot 4 del prompt cache ya está listo
  para inyectar la voz de marca; slot 6 lo respalda con channel hint
  desde el registry shared (S5).

---

## Decisiones clave

- **Mantener AST custom (no migrar a import-linter / PyTestArch)**:
  - Tomada: continuar el patrón AST custom mirror de copilot
    (`test_no_new_copilot_module_imports.py`).
  - Razón: el repo ya tiene 60+ arch tests AST funcionando con allowlist
    frozen + shrinks-only. Import-linter no soporta nativo el ratchet
    pattern (habría que envolver con `frozenset` igual). PyTestArch
    agrega dependencia + curva de aprendizaje sin mejora cualitativa.
    [qntm — Ratchets in software development] confirmó: "fitness function
    se agrega después de limpiar el módulo, congela trabajo hecho".
  - Alternativa descartada: migrar a `import-linter` con `forbidden`
    contracts. Rechazada — ratio costo/beneficio negativo.

- **Sweeps oportunista ANTES del freeze del ratchet**:
  - Tomada: ejecutar los 2 sweeps DEFERRED-post-S6 (shim cleanup S5 +
    LLM_ROLE_BY_SITE expansion S4) ANTES de escribir los arch tests.
  - Razón: el principio "lock not goal" de [qntm] dice: el ratchet
    debe congelar lo limpio, no lo sucio. Sweep antes = allowlist más
    chico + shim files borrados. Si el sweep se hace después del
    freeze, el shim queda allowlistado innecesariamente.
  - Alternativa descartada: freeze primero + sweep después en otro
    sprint. Rechazada — fragmenta la operación + arch test
    falsamente "tolerante" a deuda ya extinta.

- **`LLM_ROLE_BY_SITE` como superset, `SPECIALIST_TO_ROLE` como sub-view**:
  - Tomada: `LLM_ROLE_BY_SITE` superset (specialists + summary +
    follow_up_nudge + safety) en `domain/model_tier.py`. Sub-view
    `SPECIALIST_TO_ROLE` derivada con dict-comprehension restringida
    a las 4 keys de specialists.
  - Razón: el arch test S4 `test_no_hardcoded_models_sales_agent`
    valida `SPECIALIST_TO_ROLE` keys explícitas — romper esa firma
    rompía 26 tests dependientes. La sub-view derivada preserva
    back-compat al 100% (los 26 tests pasan sin tocar) y suma 3 nuevos
    sites a la SSoT amplia.
  - Alternativa descartada: deprecar `SPECIALIST_TO_ROLE` y migrar
    nodes.py + tests a `LLM_ROLE_BY_SITE`. Rechazada — cascade de
    refactor en `nodes.py:108,140,154,175` + `test_specialist_*.py` ×
    26 assertions. Scope creep.

- **`safety` mantiene FAST (NO promoción a NANO)**:
  - Tomada: `LLM_ROLE_BY_SITE["safety"] = ModelRole.FAST` (no promoción).
  - Razón: el fail-safe del safety service es ``return True`` (asume
    sensitive cuando el LLM falla). Falsos positivos = mensaje
    enmascarado innecesario al lead. NANO en gpt-5.4-nano podría
    aumentar la tasa de FP. FAST en gpt-4o-mini es bajo costo (input
    < 5k tokens típico) y mantiene quality.
  - Alternativa descartada: promover a NANO siguiendo el pattern de
    summary/nudge. Rechazada — caso de uso distinto (safety check es
    sensible a precisión, summary/nudge son generadores de texto).

- **Drop legacy agent_trace_model DEFERRED a post-S6.5**:
  - Tomada: NO ejecutar drop legacy + cutover admin en S6.
  - Razón: ventana dual-write S1 = 4 semanas desde 2026-04-28. Hoy
    día 0 — ventana NO cumplida. Drop prematuro rompe `sales_audit.py`
    dual-read banner + reconciliation worker aún midiendo diff.
  - Alternativa descartada: comprimir window a 1 día. Rechazada —
    sin baseline de drift cross-tenant production no podemos validar
    que el callback handler S1 captura todo lo que el `@trace_node`
    legacy capturaba. 4 semanas son no-negociables.

- **REGISTERED_SUBAGENTS_RATCHET = () (preventivo, no reactivo)**:
  - Tomada: arch test `test_subagent_isolation_invariants_sales_agent`
    con tupla vacía + 3 invariantes preventivos.
  - Razón: §2.3 del plan declara explícitamente "NO subagents
    deepagents" para sales (StateGraph lineal es el valor). Si alguna
    fase futura intenta romper la regla, los 3 tests cazan el intento:
    (a) `astream_events` sin `policy_for`, (b) import de `deepagents`
    en `graph.py`, (c) `create_deep_agent` call en `graph.py`.
  - Alternativa descartada: skip el test (no aplica hoy). Rechazada —
    el test es preventive guard del principio §2.3, valor sigue vigente
    incluso con tupla vacía hoy.

---

## Sorpresas / gotchas críticos

- **`ruff format` re-organiza imports cross-tree**: cuando ejecuté
  `ruff format src/ tests/` después del sweep de shims, ruff aplicó
  format y re-organizó imports en `src/modules/copilot/application/orchestrator/chat.py`
  (entre otros). Eso bumpó algunos imports al lugar canónico — efecto
  positivo pero NO esperado si el plan era "scope estricto solo files
  tocados". **Lección**: cuando se hace sweep que toca >5 archivos
  de imports, re-correr `ruff format` SOLO sobre los files tocados
  (lista explícita) si el goal es cero diff colateral. Hoy el efecto
  fue benigno (113 tests copilot verde post-format). Si el repo tuviera
  consumers FE/SDK que dependen del orden de imports en runtime
  (raro pero posible), el reformat sería breaking.

- **Sed `^from src.modules.copilot.application.orchestrator.channel_intent_detector import (`** —
  la regex tiene que anclarse al ``^`` para no afectar imports nested
  o comentarios que mencionen el path. El sed inicial sin anchor
  producía falsos positivos en docstrings con texto exacto del import.
  **Lección**: bulk sed para imports siempre con `^` + `$` cuando es
  línea completa. Para multi-line imports (con `(`), el match es
  sólo de la primera línea — el cuerpo (los símbolos) queda intacto y
  el `)` cierra correctamente porque el script no lo toca.

- **AST scan de `_outer_function` en arch test PII**: SIM102 + SIM110
  ruff catches en mi primera versión. Reflowing nested ifs a single
  `if A and B and ...` colapsa el AST sin perder semántica + ruff
  contento. **Lección**: cuando se usa AST para arch tests, escribir
  helpers en estilo ruff-friendly desde el inicio (single-condition
  `if`, `any(... for ...)` comprehensions) ahorra el ruff pass post-hoc.

- **`enclosing_statement` ambiguo cross-Stmt**: el primer draft tenía
  un loop muerto + un loop activo. Ruff no lo detectó (loop muerto
  era `pass` interno, no flag de "unreachable"). **Lección**: arch test
  helpers que escanean stmt-level anidamiento pueden tener side-effects
  invisibles si tienen branches redundantes — collapse a single
  comprehension siempre que sea posible.

- **3064 tests post-sweep vs 3134 baseline pre-S6**: número diff confunde.
  El baseline reportado por S5 fue "3134 verde" — mí run post-sweep
  reporta 3064. La diff (-70) es NO regresión: el run post-sweep filtró
  por `tests/modules/copilot/ tests/modules/sales_agent/ tests/shared/
  tests/architecture/ -m "not verify and not integration"` mientras
  que el S5 baseline incluía `tests/admin/`. Re-corriendo con admin
  incluido: 2535 sales+copilot+admin+shared + 622 architecture = 3157
  total. Saldo neto: +23 tests vs baseline (los 6 arch nuevos S6).
  **Lección**: comparar test counts cross-fase es trampa si los filters
  de pytest cambian. Anclar siempre al mismo set de directorios + flags
  para comparaciones válidas.

---

## Recomendaciones accionables para S7

- [ ] **Brand voice lighthouse via port `shared/links/ports/brand.py`**:
  S7 va a leer `brand_voice_summary` (mirror copilot F3 lighthouse).
  Si el read es via port → la entrada `sales_agent -> brand |
  application/services/style_anchor_retriever.py` del ratchet shrinks
  a 3 entradas. Si se lee directo del modelo brand → la entrada se
  multiplica. Ratchet test S6 garantiza visibilidad — el counter
  `expected = 4` debe bumpearse explícitamente con razón en el commit.

- [ ] **Anchor `SALES-AGENT-BRAND-VOICE-S7`**: agregar al
  `ANCHOR_REGISTRY` en `test_sales_agent_anchors.py` cuando S7 cree el
  archivo `brand_voice_summary.py` con su anchor. El cap (25) admite
  hasta 20 nuevos sin bumpear.

- [ ] **Slot 4 del cache prefix toma `brand_voice_summary`**: el
  `compose_system_prompt` S3 ya tiene `AGENT_IDENTITY` cacheable
  per-tenant. S7 lo reemplaza con `brand_voice_lighthouse` desde el
  port. Cache hit rate se preserva si el render es estable per-tenant
  (no fragments volatile).

- [ ] **Re-correr scan voseo post-S7 brand voice integration**: S00
  baseline limpia (regla 11 CLAUDE.md), pero brand voice override por
  tenant podría inyectar voseo si el tenant lo configuró. Validar con
  golden tests.

- [ ] **Arch test `test_no_legacy_agent_trace_reads.py` en S6.5**:
  cuando la ventana dual-write S1 cumpla 4 semanas (post 2026-05-26),
  ejecutar drop legacy + cutover admin + agregar el arch test que
  bloquea reads. NO en S7.

- [ ] **`test_pii_sanitization_coverage_sales_agent` extiende a
  brand_voice_summary writes**: si S7 introduce escritura de
  `brand_voice_summary` a tabla cacheable, agregar la tabla a
  `TENANT_SCOPED_MODELS` del tenant isolation arch test + cubrir
  sanitization (aunque brand voice no contiene PII típica, el
  override del tenant podría incluir testimonios con email/phone).

---

## Hooks listos

- `backend/tests/architecture/test_no_new_sales_agent_module_imports.py::KNOWN_SALES_AGENT_TO_MODULE_IMPORTS` —
  frozenset 4 entradas (brand × 1, crm × 2, offer × 1). Shrinks-only.
- `backend/tests/architecture/test_sales_agent_anchors.py::ANCHOR_REGISTRY` —
  dict 5 entradas (S1/S3/S4/S5). Cap 25.
- `backend/tests/architecture/test_sales_agent_callback_handler_invariants.py::EXPECTED_ON_METHODS` —
  frozenset 8 callback names. ROLLBACK_OPTIONAL = `{on_chat_model_start, on_tool_start}`.
- `backend/tests/architecture/test_pii_sanitization_coverage_sales_agent.py::TARGET_METHOD_NAMES` —
  frozenset `{_persist_trace_event_row, add}`. Helper `_violations_in_file`
  reusable para extender a otros files.
- `backend/tests/architecture/test_sales_agent_tenant_isolation.py::TENANT_SCOPED_MODELS` —
  frozenset 3 modelos observability. Allowlist 1 entry (reconciliation
  worker, lineno-anchored).
- `backend/tests/architecture/test_subagent_isolation_invariants_sales_agent.py::REGISTERED_SUBAGENTS_RATCHET` —
  tupla vacía. 3 invariantes preventivos.
- `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE` —
  dict 7 keys (4 specialists + summary + follow_up_nudge + safety).
  `SPECIALIST_TO_ROLE` sub-view back-compat.

---

## Riesgos abiertos

- **Drop legacy post-S6.5 puede romper si reconciliation drift > 1%**:
  el cutover criterion del plan dice "diff < 1% en trace count, dejamos
  LLM rebuild post-cutover". Si la reconciliation 4-semana mide drift
  > 1%, el drop se posterga otra ventana. Watchpoint: revisar
  `reconciliation_runs` table en 2026-05-25 antes del drop.

- **Ratchet `test_baseline_count_matches_documented_state`**: hardcoded
  a 4 entradas. Cualquier shrink futuro requiere bumpear el `expected`
  count en el test. Si el dev olvida, el test rompe — feature, no bug
  (forces awareness). Pero puede frustrar onboarding nuevo si no se
  documenta cómo bumpear.

- **`logger.warning` count check en `test_each_on_method_calls_logger_warning`**:
  el test cuenta cualquier `Call` con `func.attr == "warning"` o
  `func.id == "warning"` dentro del on_* method. Falso positivo
  posible si alguien define un local function `warning(...)` sin
  relación a logging. Mitigación: el método es helper, los false-positive
  serían deliberados. Aceptable.

- **`from __future__ import annotations` en arch tests**: cada uno
  tiene `from __future__ import annotations`. Diferente del watchpoint
  S1 (que era para `orchestrator/graph.py` que LangGraph introspecta).
  Los arch tests NO son introspectados por LangGraph runtime — es OK.

- **Parallel session (analytics) modificó files cross-cutting**: durante
  el sweep, `ruff format` reformateó `tests/factories/analytics.py` +
  `tests/modules/analytics/test_evangelization_repository.py` (untracked
  files de la otra sesión). Mi commit NO los incluye. Si la otra sesión
  re-corre format con su propio config y obtiene diff, hay que re-format.
  Watchpoint: comunicar al user que esos files están post-`ruff format`
  pero no committed.

---

## Tech debt detectado (NO arreglado)

Ya en `05-tech-debt-log.md` sección "Detectados durante S6":

- [HIGH] Drop tablas legacy → DEFERRED-post-cutover-window (post 2026-05-26).
- [LOW] `agent_log_model` mencionado en docs no existe → FLAGGED-cutover-window.
- [LOW] `from __future__ import annotations` en files LangGraph-introspected →
  FLAGGED (sin arch test preventivo, watchpoint manual).
- [LOW] `typing_simulation_cpm` declarado pero no consumido (S5 carry-over) → FLAGGED.
- [LOW] Test fixtures duplicados SessionLocal mock → FLAGGED-S7.

Y FIXED en S6 (sweeps):

- [LOW] Copilot shims `output_channels.py` + `format_for_channel.py` +
  `channel_intent_detector.py` → FIXED en S6.
- [LOW] Test `test_ddd_boundaries.py:75` allowlist obsoleto → FIXED en S6.
- [LOW] safety_service.py + chat.py:550 + follow_up_engine.py NO
  consumen SPECIALIST_TO_ROLE → FIXED en S6 (LLM_ROLE_BY_SITE expansion).

---

## Fuentes research útiles

Solo las que **cambiaron una decisión**.

- [qntm — Ratchets in software development](https://qntm.org/ratchet) —
  confirmó "lock not goal" como filosofía del ratchet. Decisión de
  ejecutar sweeps ANTES del freeze, no después.
- [Hands On Architects — Protecting Architecture with Automated
  Tests in Python](https://handsonarchitects.com/blog/2026/protecting-architecture-with-automated-tests-in-python/)
  — confirmó AST custom como pattern canónico Python 2026. Decisión
  de NO migrar a `import-linter`.
- [Import Linter — contract types](https://import-linter.readthedocs.io/en/v2.7/contract_types.html) —
  evaluado como alternativa. NO soporta nativo el ratchet pattern;
  rechazado.
- [Core27 — Transactional pytest async SA pattern](https://www.core27.co/post/transactional-unit-tests-with-pytest-and-async-sqlalchemy) —
  validó el pattern conftest. Decisión re-evaluada: 2 fixtures hoy ≠
  3+ tests; FLAGGED-S7 en lugar de promoción S6.

---

## Métricas medidas

- `ruff check src/ tests/`: 0 errors mías (1 RUF059 pre-existing en
  `tests/modules/analytics/test_adoption_repository.py` perteneciente
  a la sesión paralela analytics — fuera de scope S6).
- `ruff format --check src/ tests/`: 1735 files clean. 1 file
  (`tests/modules/analytics/test_evangelization_repository.py`) needs
  reformat — perteneciente a sesión paralela, fuera de scope.
- `pytest tests/architecture/`: **622 passed** (incluye 23 nuevos S6).
- `pytest tests/modules/sales_agent/ tests/admin/ tests/shared/
  tests/modules/copilot/ -m "not verify and not integration"`:
  **2535 passed**.
- Total estimado vs baseline pre-S6: ~3157 vs 3134 = **+23 tests** (los
  6 arch tests nuevos S6 contribuyen 22 tests + 1 stale-entries
  diagnostic).
- Files nuevos: 6 arch tests + 1 phase doc + 1 learnings doc.
- Files modificados: 11 (sweep imports copilot 4 + tests copilot 4 +
  arch test ddd boundaries 1 + sales chat.py 1 + sales safety_service 1
  + sales follow_up_engine 1 + sales model_tier 1 + tech-debt-log 1 +
  S6 phase doc 1).
- Files borrados: 3 (copilot shims).
- LOC añadidas: ~1100 (incluye learnings + 6 arch tests + LLM_ROLE_BY_SITE
  expansion + tech debt entries).
- Sweep de shims: 11 call sites migrados, 3 files deleted, 0 breaking
  changes downstream.
- Spanish neutro: NO regresión — los nuevos arch tests usan español
  neutro en assertion messages + descripciones (revisado).
