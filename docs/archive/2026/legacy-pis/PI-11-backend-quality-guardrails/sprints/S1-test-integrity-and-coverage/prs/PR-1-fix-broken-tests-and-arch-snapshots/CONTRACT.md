# CONTRACT — PR-1 Fix Broken Tests + Polluter Hunt + Singleton Fixture + EventBus Migration

> Architect: `nicolify-architect` (Opus 4.7[1M])
> Run: 2026-05-04
> Cross-link: [PR-3 CONTRACT.md](../PR-3-anti-default-flip-enforcement/CONTRACT.md) (compartido — singleton fixture + EventBus migration habilitan arch fitness PR-3)

---

## § 0 — Context Summary

| Item | Value |
|---|---|
| **PR** | PR-1-fix-broken-tests-and-arch-snapshots |
| **PI** | PI-11-backend-quality-guardrails |
| **Sprint** | S1-test-integrity-and-coverage |
| **Architect run** | 2026-05-04 |
| **Modules touched** | brand, copilot, sales_agent, shared (domain_events + infrastructure/llm), campaigns (allowlist), crm (allowlist), core (no code), tests/architecture, tests/conftest |
| **CONTEXT-BRIEF source** | Used § 7 (existing systems) + § 8 (EXTEND-vs-NEW) verbatim. All 5 surfaces = EXTEND, ZERO NEW. |
| **Decisions consumed** | D1, D2, D3, D4, D5, D6, D7 (PI.md § Decisión arquitectónica clave) |
| **pm-nico/current-state files affected (post-merge)** | None — puro test hardening + 1 real bug fix backend (litellm clamp). NO user-facing capability. |
| **Architecture gates that MUST keep passing** | `test_no_legacy_event_bus_publish.py` · `test_ddd_boundaries.py` · `test_folder_naming.py` · `test_sales_agent_anchors.py` · `test_sales_agent_system_prompt_order.py` · `test_budget_guard_pre_llm_call.py` · `test_extraction_orchestrator_inheritance.py` · `test_telegram_cache_prefix_meets_anthropic_threshold.py` (target 78/78 PASS) |

### Surface → builder → auditor mapping (PM uses to spawn correct agents)

| Surface | Owner builder | Auditor |
|---|---|---|
| `backend/tests/conftest.py` (singleton fixture exhaustivo) | `nicolify-backend` (Sonnet) — **business builder OWNS** (regla M3 lock prevention) | `nicolify-backend-auditor` (Opus) |
| `backend/tests/architecture/test_ddd_boundaries.py`, `test_folder_naming.py`, `test_no_legacy_event_bus_publish.py` (allowlist updates) | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/tests/architecture/test_sales_agent_anchors.py`, `test_sales_agent_system_prompt_order.py` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| `backend/tests/modules/brand/**` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/tests/modules/copilot/**` (incl. observability + voice 410) | `nicolify-agentic` | `nicolify-agentic-auditor` |
| `backend/tests/modules/sales_agent/**` (snapshot helpers + orchestrator + polluter hunt) | `nicolify-agentic` | `nicolify-agentic-auditor` |
| `backend/tests/shared/domain_events/test_event_bus_adapter.py` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/tests/integration/test_outbound_orchestrator_e2e.py` | `nicolify-agentic` | `nicolify-agentic-auditor` |
| `backend/src/shared/domain/events.py` (LegacyEventBus deprecation warning) | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/src/shared/infrastructure/llm/providers/litellm.py` (kimi clamp) | `nicolify-backend` | `nicolify-backend-auditor` |
| `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` (URL slug) | `nicolify-backend` (mecánico via stash apply — sin builder FE separado) | `nicolify-backend-auditor` (vitest run nativo) |

### Skills consulted

- **`backend-expert`**: SQLA 2.0 patterns, conftest fixture pattern, lint/test commands native venv. Decisión: extender autouse fixture en conftest.py respetando override pattern docs (`runtime-quality-checklist.md` § override fixture pattern).
- **`copilot-expert`**: 5 anti-patrones recurrentes consultados (singleton leaks, snapshot helpers domain_events siempre `[]`, observability recorder honesty). Decisión: reset ChatOrchestrator (+ build_deep_agent_graph cache si existe) en autouse fixture; mock target migration cubre `EventBus.publish` legacy → `adapter_bus.publish`.
- **`sales-agent-expert`**: §3 NO-tocar list verificada — snapshot helpers (`_chat_flow_snapshot_helpers.py`) NO está en §3 (es test infra). EXTEND outbox-aware OK. SemanticRouter + ChatOrchestrator singletons reset OK (no §3 violation). `agent_app = workflow.compile()` module-level en `application/orchestrator/graph.py` ES candidato singleton — fixture reset agent_app cache obligatorio.
- **`tessl__langgraph`**: StateGraph compilation pattern. `workflow.compile()` produce CompiledGraph cacheable. Reset entre tests via `agent_app.checkpointer.delete_thread()` NO aplica (sin checkpointer en sales_agent graph) — solución: re-importar módulo o monkeypatch atributo si polluter raíz.
- **`tessl__fastapi`**: N/A (no API change).
- **`tessl__graceful-degradation`**: Recorder writes (`copilot_trace_event`) son best-effort — pattern preservado en deprecation warning emit (`try/except + structlog warning + no raise`).

---

## § 1 — Singleton Inventory (lista mínima esperada — builder valida + extiende)

> Source: § 7 CONTEXT-BRIEF + grep `_instance = None\|cls\._instance` cross-codebase ejecutado 2026-05-04.

**Singletons class-level confirmados (5 detectados):**

| # | Class | Path:line | Reset reason | Cleanup específico antes reset |
|---|---|---|---|---|
| 1 | `LLMFactory._instance` | `backend/src/shared/infrastructure/llm/factory.py:31-33` | MultiRoleLLMRouter cacheado holding ChatOpenAI clients con base_url settings; settings monkeypatch en test posterior NO se refleja → router stale. | None (factory pura) |
| 2 | `ChatOrchestrator._instance` (sales_agent) | `backend/src/modules/sales_agent/application/orchestrator/chat.py:74-81` | `_initialized=True` flag persiste; `buffer_service: SmartBufferService` instanciado una vez con state interno. Cross-test → next test reusa mismo orchestrator → leak buffers + side-effects. | `if cls._instance and hasattr(cls._instance, 'buffer_service'): cls._instance.buffer_service = None` antes set `_instance = None` |
| 3 | `SemanticRouter._instance` (sales_agent) | `backend/src/modules/sales_agent/application/services/semantic_router.py:46-60` | Routing rules cacheadas + tenant config snapshot. Tests siguientes con tenant distinto reusan rules viejas. | None |
| 4 | `ChannelRouterRegistry._instance` (campaigns) | `backend/src/modules/campaigns/infrastructure/channels/registry.py:48-52` | **NO reset necesario** (per CONTEXT-BRIEF § 7 + skill verification). Singleton thread-safe robust con `get_instance()` factory + bootstrapped una sola vez en startup. Si reset → rompe tests campaigns que dependen del registry inicializado. | **EXCLUIR** del fixture |
| 5 | `MetaAPI._api_instance` (connections) | `backend/src/modules/connections/infrastructure/channels/meta.py:303` | Per-instance attribute (`self._api_instance`), NO class-level. NO requiere reset class-level (instance se crea/destruye con cada test que use Meta). | **EXCLUIR** del fixture (no class-level) |

**Caches módulo-level NO singleton pero requieren reset (candidatos polluter Fase 4):**

| # | Path:line | Reason | Reset hook |
|---|---|---|---|
| A | `backend/src/shared/domain_events/outbox/application/event_bus_adapter.py:54-96` (`_module_name_from_file` lru_cache + `_adapter_instance` module-level) | Module-load singleton; `_adapter_instance` cacheado. lru_cache puede retener stale module mappings cross-test. | `_reset_module_inference_cache()` ya existe (línea 90); fixture lo invoca pre+post test |
| B | `backend/src/modules/sales_agent/application/orchestrator/graph.py:52` (`agent_app = workflow.compile()` module-level) | LangGraph compiled graph cached at import; reusado cross-test; possible polluter raíz (Fase 4 sospechoso primario) | Re-import via `importlib.reload(graph_module)` en fixture cleanup OR monkeypatch reset si compile reactiva. **Builder valida si esto es polluter raíz.** |
| C | `backend/src/modules/sales_agent/application/agents/sales/graph.py::sales_app` (subgraph compilation) | Mismo patrón que B; compiled at module load | Same pattern as B |
| D | `backend/src/shared/domain/events.py::EventBus._handlers` (class-level dict) | Subscribers cacheados class-level; sin teardown leak handlers cross-test (root cause `TestDomainSubscribersRegistration` PI.md § Origen punto 2) | `EventBus.clear()` (existe línea 76 — usar en fixture) |

**Builder PR-1 obliga a producir lista exhaustiva validada:**

```bash
# Comando obligatorio Step 0 builder Phase 3
grep -rn "_instance = None\|_instance: Optional\|cls\._instance\|@cache\|@lru_cache" \
  /home/chris/AISALESHT/backend/src/ 2>/dev/null

# Resultado pre-validado architect: 5 class-level singletons + 4 module-level caches arriba
# Si grep encuentra más → builder agrega + documenta razón en IMPL-LOG
```

---

## § 2 — Singleton Fixture Design

**File:** `backend/tests/conftest.py`
**Fixture:** `_reset_singletons_between_tests` (autouse)
**Scope:** function (default — reset por cada test)
**Owner:** business builder (regla M3 — agentic NO modifica conftest.py)

### Pattern (extiende stash inicial)

```python
# (bloque conceptual — NO código de implementación; el builder escribe el real)

@pytest.fixture(autouse=True)
def _reset_singletons_between_tests():
    """Reset class-level singletons + module-level caches pre+post each test.
    
    Origen: PI-11 PR-1 Fase 3 (2026-05-04). Sin reset, ChatOrchestrator/SemanticRouter/LLMFactory
    leaks entre tests + EventBus._handlers persists (origen TestDomainSubscribersRegistration
    leak documentado PI.md § Origen punto 2).
    
    Lista exhaustiva validada architect CONTRACT.md PR-1 § 1.
    
    NO reseteamos:
    - ChannelRouterRegistry (thread-safe robust, bootstrap-once design)
    - MetaAPI._api_instance (per-instance, no class-level)
    """
    # Pre-test reset
    _reset_pre()
    yield
    # Post-test cleanup
    _reset_post()


def _reset_pre():
    # 1. LLMFactory — drop cached MultiRoleLLMRouter
    from src.shared.infrastructure.llm.factory import LLMFactory
    LLMFactory._instance = None
    
    # 2. ChatOrchestrator (sales_agent) — clean buffer_service first
    from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
    if ChatOrchestrator._instance is not None:
        if hasattr(ChatOrchestrator._instance, 'buffer_service'):
            ChatOrchestrator._instance.buffer_service = None
        ChatOrchestrator._instance = None
    
    # 3. SemanticRouter (sales_agent)
    from src.modules.sales_agent.application.services.semantic_router import SemanticRouter
    SemanticRouter._instance = None
    
    # 4. EventBus._handlers — drop subscribers (origen punto 2 PI.md)
    from src.shared.domain.events import EventBus
    EventBus.clear()
    
    # 5. EventBusAdapter module-inference lru_cache
    from src.shared.domain_events.outbox.application.event_bus_adapter import (
        _reset_module_inference_cache,
    )
    _reset_module_inference_cache()


def _reset_post():
    # Same set — guarantee no leak FROM this test TO next.
    _reset_pre()
```

### Comments per-singleton (mandatory en código real builder)

Cada bloque de reset DEBE incluir comment `# {ClassName}._instance — reset reason: {why}` referenciando línea CONTRACT.md § 1. Auditor agentic Cat 13 valida exhaustividad.

### Cleanup hooks

- **ChatOrchestrator**: `buffer_service = None` antes de drop instance (evita SmartBufferService background task leak si tiene timer activo).
- **EventBus._handlers**: `EventBus.clear()` ya existe (es `cls._handlers.clear()`, idempotente).
- **lru_cache**: helper `_reset_module_inference_cache()` ya existe línea 90 event_bus_adapter.py — usarlo (NO `lru_cache.cache_clear()` directo, hay encapsulación).

### NO incluir en fixture (justificado)

- `ChannelRouterRegistry._instance` — bootstrap-once design; reset rompe tests campaigns.
- `MetaAPI._api_instance` — per-instance attribute, no class-level.
- `LiteLLMService._models` cache — per-instance, garbage-collected al perder LLMFactory._instance.

### Polluter hunt extension (Fase 4 puede agregar)

Si Fase 4 identifica polluter raíz en LangGraph `agent_app` compilation cache → fixture extiende con re-import módulo:

```python
# (Fase 4 candidate — solo si polluter hunt lo valida)
import importlib
import src.modules.sales_agent.application.orchestrator.graph as _graph_module
importlib.reload(_graph_module)
```

**Builder business documenta lista final + reset hooks completos en IMPL-LOG § Singleton fixture inventory.**

---

## § 3 — EventBus Migration Strategy (D2)

**Decisión cementada (D2):** Tests legacy `EventBus.publish` mocks → migración OBLIGATORIA a `adapter_bus` mock OR outbox table query. NO `monkeypatch.setattr(USE_OUTBOX_PATTERN_*=False)` — esa táctica es band-aid del band-aid (decisión D1: outbox True permanente).

### Decisión per-test (matriz)

| Caso | Estrategia | Mock target | Probe pattern |
|---|---|---|---|
| **A. Test asserts EVENT FUE PUBLICADO** (event aparece después de service.save()) | Mockear adapter_bus directamente | `src.shared.domain_events.outbox.application.event_bus_adapter.adapter_bus.publish` | `mock_publish.assert_called_once_with(event_obj, session=mock_db, ...)` |
| **B. Test asserts EVENT FUE ENCOLADO en outbox table** (tests integración) | Probe outbox repository read | NO mock — real DB write | `select(DomainEventOutboxModel).where(tenant_id=...)` + assert row count |
| **C. Test asserts HANDLER FUE INVOCADO** (subscriber callback executes) | Subscribe + simular dispatcher | NO mock event_bus — usar real LegacyEventBus subscribe (pre-cutover compat path) | `EventBus.subscribe('event_name', handler_spy)` + `EventBus.publish(...)` (immediate dispatch session=None) |
| **D. Test prueba la capability del EventBus mismo** (test_event_bus.py) | NO migrar — capability test | `src.shared.domain.events.EventBus.publish` (legitimately) | Mismo (este test mide EventBus.publish, no es uso de producción) — bypass arch fitness PR-3 |
| **E. Test prueba EventBusAdapter routing logic** (test_event_bus_adapter.py + test_outbox_cutover_e2e.py) | NO migrar — meta-test del adapter | Tests pueden mockear `EventBus.publish` PARA verificar fall-through legacy path cuando flag False | bypass arch fitness PR-3 con magic comment `# arch-bypass: testing legacy capability` |

### Decision tree builder Step (Fase 2 audit)

```
Para cada test detectado en grep:
  ¿Test mockea "src.shared.domain.events.EventBus.publish"?
    └── SÍ:
        ¿File path en ["tests/shared/test_event_bus.py", "tests/shared/domain_events/test_event_bus_adapter.py", "tests/integration/test_outbox_cutover_e2e.py", "tests/modules/{brand,copilot,sales_agent}/integration/test_outbox_cutover.py"]?
          ├── SÍ → Caso D o E. Bypass PR-3 (magic comment).
          └── NO → Caso A o C:
              ¿Test asserts subscriber callback?
                ├── SÍ → Caso C. Mantener mock LegacyEventBus pero suscribir handler real.
                └── NO → Caso A. Migrar mock target a adapter_bus.
```

### Mock target migration patterns (por defecto, Caso A)

```python
# ANTES (legacy, romperá arch fitness PR-3 cuando outbox flag True default):
monkeypatch.setattr("src.shared.domain.events.EventBus.publish", mock_publish)

# DESPUÉS (canonical post-cutover):
from src.shared.domain_events.outbox.application import event_bus_adapter
monkeypatch.setattr(event_bus_adapter.adapter_bus, "publish", mock_publish)
# O patch as attribute:
monkeypatch.setattr("src.shared.domain_events.outbox.application.event_bus_adapter.adapter_bus.publish", mock_publish)
```

### Lista esperada tests a migrar (Builder valida vs grep cross-codebase)

Builder Step 0 Fase 2 ejecuta:
```bash
grep -rln "src.shared.domain.events.EventBus.publish" /home/chris/AISALESHT/backend/tests/ | grep -v __pycache__
```

Lista pre-validada architect (23 archivos identificados — sub-set de los que mockean específicamente):

**Caso A (migrar a adapter_bus mock):**
- `tests/modules/copilot/test_extraction_event_handlers.py`
- `tests/modules/copilot/observability/test_domain_subscribers.py`
- `tests/modules/copilot/observability/test_register.py`
- `tests/modules/copilot/api/test_suggestions_endpoint.py`
- `tests/modules/copilot/api/test_suggestions_accept_endpoint.py`
- `tests/modules/copilot/suggestions/test_suggestion_event_recorded.py`
- `tests/shared/application/test_brand_summary_event_handlers.py`
- `tests/modules/sales_agent/orchestrator/test_audit_emitter.py`
- `tests/modules/sales_agent/tools/payment/test_grant_access_idempotent.py`
- `tests/modules/crm/test_sale_lifecycle.py`

**Caso B (mantener — probe outbox table real DB):**
- `tests/integration/test_outbox_cutover_e2e.py`
- `tests/modules/copilot/integration/test_outbox_cutover.py`
- `tests/modules/brand/integration/test_outbox_cutover.py`
- `tests/modules/sales_agent/integration/test_outbox_cutover.py`

**Caso D/E (bypass PR-3 — magic comment):**
- `tests/shared/test_event_bus.py` ← capability test (mide EventBus mismo)
- `tests/shared/domain_events/test_event_bus_adapter.py` ← meta-test routing logic
- `tests/shared/domain_events/test_event_bus_adapter_infers_module.py` ← meta-test inference

**Stash apply (Fase 1 — REVISAR vs decisión D2):**
- `tests/modules/brand/test_brand_section_updated_event.py` — stash usa `monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False)` → **REVISAR + MIGRAR a Caso A** (band-aid prohibido por D2)
- `tests/modules/brand/test_outbox_adapter_integration.py` — stash usa `monkeypatch.setattr` settings con MagicMock → **REVISAR + MIGRAR**
- `tests/modules/copilot/test_outbox_adapter_integration.py` — stash USE_OUTBOX_PATTERN_COPILOT=False → **REVISAR + MIGRAR a Caso B (probe outbox table) o Caso E (bypass como meta-test)**
- `tests/shared/domain_events/test_event_bus_adapter.py` — stash USE_OUTBOX_PATTERN_SALES_AGENT=False → **REVISAR + MIGRAR a Caso E (meta-test bypass)**

**Snapshot helper crítico (Fase 5 — ver § 4):**
- `tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` línea 215-227 — `_capture_publish` mockea `src.shared.domain.events.EventBus.publish` → **MIGRAR a Caso A (probe adapter_bus) o Caso B (probe outbox table — recomendado)**

### Audit coverage requirement

IMPL-LOG.md § "EventBus migration audit" debe contener tabla con TODOS los archivos de la lista grep + estrategia aplicada (Caso A/B/C/D/E) + mock target nuevo. Auditor (backend + agentic Cat 12/13) valida 0 omisiones.

---

## § 4 — Snapshot Helpers Outbox-Aware Design

**File:** `backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` (existente, EXTEND)
**Estado actual:** línea 215-227 `_capture_publish` mockea `EventBus.publish` legacy → captura `domain_events=[]` siempre cuando flag True (publicación va por outbox no interceptado).

### Decisión: Caso B PRIMARIO (probe outbox table real) + Caso A FALLBACK

Justificación:
- Outbox table query refleja realidad post-cutover (lo que producción hace).
- adapter_bus mock funciona pero NO valida que outbox INSERT actualmente ocurre — solo que adapter recibió la llamada.
- Tests snapshot orchestrator son end-to-end → real path = outbox table query.

### API extension (helpers nuevos)

**Builder agentic owns. Modifica `_chat_flow_snapshot_helpers.py`:**

```python
# (bloque conceptual — NO código de implementación; builder escribe el real)

async def _capture_outbox_events(
    capture: FlowCapture,
    session: AsyncSession,
    tenant_id: UUID = TENANT_ID,
) -> None:
    """Query outbox table after orchestrator turn completes.
    
    Replaces legacy `_capture_publish` mock pattern (line 215-227).
    Reflects real post-cutover path: events INSERT to domain_event_outbox table.
    
    Calls AT END of test setup (post `await orchestrator.process_chat_flow(...)`).
    """
    from src.shared.domain_events.outbox.infrastructure.repository import (
        DomainEventOutboxRepository,
    )
    repo = DomainEventOutboxRepository(session)
    rows = await repo.list_for_tenant_after(tenant_id, FROZEN_NOW)
    for row in rows:
        capture.domain_events.append({
            "event_name": row.event_name,
            "tenant_id": str(row.tenant_id),
            "payload": row.payload,
            "occurred_at": row.occurred_at.isoformat(),
        })


def _build_capture_publish_legacy(capture: FlowCapture):
    """LEGACY — kept for backward-compat tests that explicitly probe legacy path.
    
    DEPRECATED: new tests should call _capture_outbox_events post-orchestrator.
    """
    def _capture_publish(event: Any, session: Any = None) -> None:
        capture.domain_events.append({
            "event_name": event.event_name,
            "tenant_id": str(event.tenant_id),
            "payload": event.payload,
        })
    return _capture_publish
```

### Migration of consumer tests

**Files using helper that need update (builder agentic Step 0 grep):**

```bash
grep -rln "_capture_publish\|_chat_flow_snapshot_helpers" /home/chris/AISALESHT/backend/tests/modules/sales_agent/ 2>/dev/null
```

Pre-validated:
- `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` — usar `_capture_outbox_events` POST `process_chat_flow` invocation.

### Snapshot baseline diff

Después de la migración:
1. Run snapshot test isolation → captura nueva baseline (incluye eventos reales).
2. Diff vs baseline anterior (`domain_events=[]`).
3. **EXPECTED:** baseline diff NO empty → snapshot file `tests/modules/sales_agent/snapshots/orchestrator/*.json` debe regenerarse con eventos reales.
4. Builder agentic commitea snapshot updated + documenta diff en IMPL-LOG § "Snapshot baseline diff".

### Asserciones que cambian

Tests que asserts `len(capture.domain_events) == 0` ahora deben asserts `len(capture.domain_events) == N` donde N = eventos reales emitidos por el orchestrator. Builder identifica N via run + commit baseline + audit valida snapshot determinístico (FROZEN_NOW + deterministic UUID).

---

## § 5 — LegacyEventBus Deprecation Runtime Warning (D3)

**File:** `backend/src/shared/domain/events.py` — `EventBus.publish` classmethod
**Owner:** business builder (`nicolify-backend`)

### Pattern

```python
# (bloque conceptual — NO código de implementación; builder escribe el real)

import warnings
import structlog

logger = structlog.get_logger(__name__)

class EventBus:
    # ... existing code ...
    
    @classmethod
    def publish(cls, event: DomainEvent, session: Any | None = None) -> None:
        """Publish an event. (Original docstring preserved.)
        
        DEPRECATED PATH: Since outbox cutover (PR-6 PI-2), production
        emitters route via EventBusAdapter. Direct calls to EventBus.publish
        outside test capability suites + EventBusAdapter fall-through path
        emit a runtime warning when ANY USE_OUTBOX_PATTERN_* flag is True.
        
        Origen: PI-11 PR-1 § 5 D3 (2026-05-04).
        Eliminación final post PI-12 (capability removal evaluation).
        """
        # Best-effort warning emit (try/except para preservar best-effort contract)
        try:
            from src.core.config import settings
            outbox_flags_on = (
                settings.USE_OUTBOX_PATTERN_SALES_AGENT
                or settings.USE_OUTBOX_PATTERN_COPILOT
                or settings.USE_OUTBOX_PATTERN_BRAND
            )
            if outbox_flags_on:
                # NOTE: stack-walk skips internal frames. Only emits warning
                # when caller is OUTSIDE shared/domain_events/* and outside
                # tests/* (best-effort detection).
                if not _is_internal_caller_or_test():
                    warnings.warn(
                        "EventBus.publish called when outbox cutover active. "
                        "Migrate emitter to EventBusAdapter or wrap with "
                        "magic comment '# arch-bypass: testing legacy capability'.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    logger.warning(
                        "legacy_event_bus_called_outside_test_context",
                        event_name=event.event_name,
                        tenant_id=str(event.tenant_id),
                    )
        except Exception:  # noqa: BLE001 — best-effort, must not break caller
            pass
        # Original implementation continues unchanged...
        # (rest of method body preserved byte-equal)
```

### Detection helper `_is_internal_caller_or_test`

```python
def _is_internal_caller_or_test() -> bool:
    """Returns True if caller is inside shared/domain_events/* OR tests/*.
    
    Used to suppress deprecation warning during fall-through (adapter calls
    EventBus.publish when flag False) and during test capability runs.
    """
    import sys
    try:
        frame = sys._getframe(2)  # Skip publish() + this helper
        depth = 0
        while frame is not None and depth < 10:
            filename = frame.f_code.co_filename
            if (
                "shared/domain_events/" in filename
                or "shared/domain/events.py" in filename
                or "/tests/" in filename
            ):
                return True
            frame = frame.f_back
            depth += 1
    except Exception:  # noqa: BLE001
        return True  # On error, suppress warning (best-effort)
    return False
```

### Test coverage (Fase 6)

Test nuevo:
- `tests/shared/test_legacy_event_bus_deprecation_warning.py`:
  - Test 1: external caller (simulated via `tmp_path` script) + outbox flag True → `DeprecationWarning` emitted
  - Test 2: caller inside `shared/domain_events/` → NO warning (fall-through path quiet)
  - Test 3: caller inside `tests/*` → NO warning (test capability quiet)
  - Test 4: outbox flag all False → NO warning (legacy compat path active)

### Suppression in production

Production tenant code que aún llama `EventBus.publish` directo (debería ser cero post-PR-6) recibe warning visible en logs. Alerta Chris para identificar emisores residuales pre-eliminación final.

### Out of scope

- Eliminación final `EventBus.publish` capability (post PI-12 evaluación)
- Removal de `EventBus._handlers` + subscribe/clear (capability legacy compat preserved)

---

## § 6 — Polluter Hunt Methodology (Fase 4 — D4 D5)

**Target:** `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot`
**Estado actual stash:** `@pytest.mark.flaky(reruns=2)` band-aid (REMOVER pre-ship).
**Owner:** **agentic builder** (Opus — sin budget cap per Chris D4).

### Methodology (mandatory steps en orden estricto)

#### Step 1 — Snapshot baseline isolation
```bash
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot \
  -v --tb=long > /tmp/baseline_isolation.txt 2>&1
```
Resultado esperado: PASS. Captura output snapshot real.

#### Step 2 — Reproduce in suite
```bash
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/modules/sales_agent/ -v --tb=long > /tmp/suite_run.txt 2>&1
```
Confirma FAIL determinístico.

#### Step 3 — Use `detect-test-pollution` tool (state-of-the-art per WebSearch)
```bash
# Install (native venv)
cd /home/chris/AISALESHT/backend && .venv/bin/pip install detect-test-pollution

# Run bisection
cd /home/chris/AISALESHT/backend && \
  .venv/bin/python -m detect_test_pollution \
    --failing-test "tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot" \
    --tests "tests/modules/sales_agent/" \
    > /tmp/polluter_bisection.txt 2>&1
```
Output: identifica test causal exacto que muta estado leak.

#### Step 4 — JSON diff exhaustivo baseline vs polluted
```bash
# Capturar snapshot polluted
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/modules/sales_agent/ -v -s \
    -k "test_chat_flow_telegram_new_lead_snapshot or {polluter_test_id}" \
    > /tmp/polluted_run.txt 2>&1

# Diff JSONs (snapshots si existen baseline files)
diff -u tests/modules/sales_agent/snapshots/orchestrator/baseline.json /tmp/polluted_snapshot.json
```

#### Step 5 — Setup-only suite check
```bash
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/modules/sales_agent/ --setup-only --tb=short \
    > /tmp/setup_only.txt 2>&1
# Identifica fixtures cargadas + orden
```

#### Step 6 — Hipótesis + experimento (sospechosos primarios)

| Sospechoso | Razón | Experimento |
|---|---|---|
| **`agent_app = workflow.compile()` module-level** (graph.py:52) | LangGraph compiled graph cached at import; reusable cross-test con state acumulado en `state` dict references | Re-import módulo via `importlib.reload(...)` antes test target → si pasa = polluter raíz |
| **`sales_app` subgraph (sales/graph.py)** | Mismo patrón compilation cache | Re-import + recompile |
| **`ChatOrchestrator._instance` + `buffer_service` SmartBufferService** | Buffer state persistente entre tests; threads/timers leak | Singleton fixture (§ 1-2) DEBE resetear; Fase 4 valida fixture cubre |
| **Module-level uuid patches en tests previos** | Tests previos patchean `uuid.uuid4` module-wide → leaks via `monkeypatch.setattr` no restore | `MonkeyPatch` scope check; Fase 4 verifica `uuid` reset entre tests |
| **`langgraph.checkpoint` shared state** | Si checkpointer compartido; mensajes persisten | Sales_agent NO usa checkpointer (graph.py:52 compile() sin arg). Descartado. |
| **`httpx.AsyncClient` mocks persisten cross-test** | Mocks no escapados de fixture scope | Fixture scope check |
| **Settings cached, monkeypatch restore falla** | `Settings` Pydantic v2 instance cacheado; monkeypatch.setattr no escapa | Fixture reset settings cache (no canonical reset method — re-import módulo o reload setting) |
| **EventBus._handlers leak (TestDomainSubscribersRegistration)** | Test calls `LegacyEventBus.clear()` SIN teardown → handlers leak (PI.md § Origen punto 2) | Singleton fixture incluye `EventBus.clear()` post-test (§ 2 punto 4) |

#### Step 7 — Fix at source (D4)

Si polluter raíz identificado → fix at source:
- Si `agent_app` compilation cache → re-importar el módulo en singleton fixture (§ 1 candidato B)
- Si test previo no restaura uuid patch → fix ese test con proper monkeypatch scope OR move patch to autouse fixture
- Si EventBus._handlers leak → singleton fixture (§ 2) cubre con `EventBus.clear()`

#### Step 8 — Pre-ship REMOVE band-aid

```bash
# Remover @pytest.mark.flaky del stash
sed -i '/@pytest.mark.flaky/d' tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py

# Verificar test pasa 1.0 sin reruns
cd /home/chris/AISALESHT/backend && \
  .venv/bin/pytest tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py::test_chat_flow_telegram_new_lead_snapshot \
  -v -p no:randomly --count=20  # 20 runs sequential, 0 fails
```

### Documentación obligatoria IMPL-LOG.md § "Polluter hunt log"

Tabla:
| Step | Comando | Resultado | Hipótesis | Conclusión |
|---|---|---|---|---|
| 1 | `pytest ... isolation` | PASS | Test funciona aislado | Confirmado: polluter externo |
| 2 | `pytest tests/sales_agent/` | FAIL | Polluter en ese dir | Estrechar bisection |
| 3 | `detect-test-pollution` | Identifica `tests/X::test_Y` | `test_Y` muta estado | Read `test_Y` source |
| ... | ... | ... | ... | ... |
| N | Fix applied | PASS suite-wide | Root cause: `<X>` leak en `<Y>` cross-test | Singleton fixture cubre o fix at source `<Y>` |

**SIN budget cap explícito (D4). Si supera 6h Opus → escalate Chris budget extra. NO ship con `@pytest.mark.flaky` permanente.**

---

## § 7 — litellm.py Kimi Clamp Design

**Stash incluye fix initial.** Architect REVISA: stash debe mirror del clamp adapter legacy (`kimi.py:79-92`) en `litellm.py` `_get_chat_model`.

### Pattern obligatorio (mirror kimi.py)

**File:** `backend/src/shared/infrastructure/llm/providers/litellm.py`
**Method:** `LiteLLMService._get_chat_model` (línea 84)

```python
# (bloque conceptual — REVISAR stash vs este spec; builder valida + ajusta)

_K2_REQUIRED_TEMPERATURE = 0.6
"""Mirror del kimi.py:30 — K2.6 con thinking disabled requiere temp=0.6 exact."""


def _get_chat_model(
    self,
    role: ModelRole,
    temperature: float | None = None,
) -> BaseChatModel:
    """Build (or reuse cached) ChatOpenAI instance targeting LiteLLM Proxy."""
    spec = self.CHAT_MODEL_SPEC
    litellm_model = self._litellm_model_name(role)
    
    # NEW: Kimi K2.6 temperature clamp (mirror kimi.py:79-92).
    # Origen: PR-1 PI-11 § 7 (2026-05-04) — production bug fix.
    # Cuando litellm proxy dispatchea a kimi/k2.6 + thinking disabled,
    # el endpoint server-enforced rechaza temp != 0.6 con HTTP 400 silent.
    is_k2 = "kimi/k2" in litellm_model.lower() or "kimi-k2" in litellm_model.lower()
    if is_k2 and temperature is not None and temperature != _K2_REQUIRED_TEMPERATURE:
        logger.warning(
            "litellm_kimi_k2_temperature_clamped",
            litellm_model=litellm_model,
            requested=temperature,
            effective=_K2_REQUIRED_TEMPERATURE,
            role=role.value,
        )
        temperature = _K2_REQUIRED_TEMPERATURE
    # END NEW
    
    effective_temp = self._DEFAULT_TEMPERATURE if temperature is None else temperature
    cache_key = (litellm_model, effective_temp)
    if cache_key not in self._models:
        ctx = ChatBuildContext(
            api_key=self.api_key,
            base_url=self.base_url,
            model=litellm_model,
            temperature=effective_temp,
        )
        self._models[cache_key] = _build_chat_from_spec(spec, ctx)
    return self._models[cache_key]
```

### Test coverage (regression)

**File nuevo:** `backend/tests/shared/infrastructure/llm/providers/test_litellm_kimi_clamp.py`

Tests:
1. `test_kimi_k2_temp_explicit_clamped_to_0_6` — pasar temp=1.0 + role=AGENT (resolves to kimi/k2.6 modelo) → assert effective_temp == 0.6
2. `test_kimi_k2_temp_already_0_6_no_clamp_log` — pasar temp=0.6 → no warning logged
3. `test_non_kimi_model_temp_passthrough` — pasar temp=1.0 + role=NANO (resolves to gpt-4o-mini) → effective_temp == 1.0 (sin clamp)
4. `test_kimi_k2_temp_none_uses_default` — pasar temp=None → effective_temp == _DEFAULT_TEMPERATURE (0.7) → NO clamp triggered (None case)

### Stash relevance audit

Builder business Phase 1 valida que stash fix:
- ✓ Aplica clamp en `_get_chat_model` (no en otro método)
- ✓ Detection `is_k2` cubre formato `kimi/k2.6` (LiteLLM convention) NO solo `k2` substring (litellm puede usar `kimi/kimi-k2.6` o `kimi/k2.6`)
- ✓ Logger via structlog (no print)
- ✓ Mirror semántico del kimi.py:79-92 pattern

Si stash difiere → builder ajusta + documenta diff en IMPL-LOG § "litellm kimi clamp stash vs spec".

### NO incluido (out of scope PR-1)

- Extensión a otros modelos con temp constraints (Qwen, Gemini) — diferido si surge
- Refactor para extraer clamp logic a helper compartido — postergar
- `extra_body={"thinking": {"type": "disabled"}}` para K2 via LiteLLM (kimi.py:97-101) — verify si LiteLLM proxy ya inyecta vía `litellm_config.yaml` (gestión proxy-side, NO adapter-side). **Open question § 10**.

---

## § 8 — Tests EventBus Mock Migration List

**Ver § 3** — completo con matriz Caso A/B/C/D/E + lista pre-validada de 23 archivos.

**Builder Phase 2 produce IMPL-LOG.md tabla:**

```markdown
## EventBus migration audit

| File | Caso | Mock target ANTES | Mock target DESPUÉS | Notes |
|---|---|---|---|---|
| `tests/modules/copilot/test_extraction_event_handlers.py` | A | `src.shared.domain.events.EventBus.publish` | `event_bus_adapter.adapter_bus.publish` | Standard migration |
| `tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py:215` | B | `src.shared.domain.events.EventBus.publish` (mock) | `_capture_outbox_events(session, tenant_id)` post-call | Outbox table query (§ 4) |
| `tests/shared/test_event_bus.py` | D | `src.shared.domain.events.EventBus.publish` (test target) | UNCHANGED | Capability test bypass — magic comment added |
| ... (TODOS los archivos del grep) | ... | ... | ... | ... |
```

**Auditor Cat 12 valida:**
- 0 omisiones (todos los archivos del grep aparecen en tabla)
- 0 archivos con `monkeypatch.setattr(USE_OUTBOX_PATTERN_*=False)` post-merge (D2 enforcement)
- Todos archivos Caso D/E tienen magic comment `# arch-bypass: testing legacy capability` exacto

---

## § 9 — Stash Apply Checklist

**Owner:** business builder (Phase 1 Step 1)

### Pre-pop checklist

```bash
cd /home/chris/AISALESHT
git status --short              # Verificar tree clean
git stash list                   # Confirma stash@{0} = "WIP PI-11 PR-1 partial — 16 tests/source fixes ..."
git branch --show-current        # Confirma development
```

### Pop + review

```bash
cd /home/chris/AISALESHT
git stash pop                    # Apply stash@{0}
git status                       # Lista 16 archivos modificados
```

### Per-archivo review (16 archivos)

| # | Archivo | Stash fix | Acción Phase 1 (REVISAR vs scope nuevo) |
|---|---|---|---|
| 1 | `tests/architecture/test_ddd_boundaries.py` | 3 entries `KNOWN_CROSS_MODULE_IMPORTS` (campaigns→sales_agent, crm→campaigns x2) | KEEP — alineado scope |
| 2 | `tests/architecture/test_folder_naming.py` | `copilot/api/_dependencies.py` exception | KEEP |
| 3 | `tests/architecture/test_sales_agent_anchors.py` | `SALES-AGENT-OUTBOUND-PR7` | KEEP — owns agentic builder |
| 4 | `tests/architecture/test_sales_agent_system_prompt_order.py` | `CAMPAIGN_CONTEXT` | KEEP — owns agentic builder |
| 5 | `tests/conftest.py` | Singleton fixture initial (LLMFactory + ChatOrchestrator + SemanticRouter) | **EXTEND** a exhaustivo § 1-2 (5 singletons + 4 module caches) |
| 6 | `tests/integration/test_outbound_orchestrator_e2e.py` | Mock target rename (`build_sales_agent_callback_handler` → `build_sales_agent_observability_context`) | KEEP — owns agentic builder |
| 7 | `tests/modules/brand/test_brand_section_updated_event.py` | `monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False)` autouse | **REVISAR + MIGRAR** a Caso A (adapter_bus mock) — D2 prohíbe band-aid |
| 8 | `tests/modules/brand/test_outbox_adapter_integration.py` | `monkeypatch.setattr` settings con MagicMock USE_OUTBOX_PATTERN_BRAND=False | **REVISAR + MIGRAR** a Caso B/E (probe outbox o bypass meta-test) |
| 9 | `tests/modules/copilot/test_offer_section_tools.py` | `next_step_hint` contract | KEEP — owns agentic builder |
| 10 | `tests/modules/copilot/test_outbox_adapter_integration.py` | `monkeypatch.setattr` USE_OUTBOX_PATTERN_COPILOT=False | **REVISAR + MIGRAR** a Caso B/E |
| 11 | `tests/modules/copilot/test_voice_api.py` | 410 Gone | KEEP — owns agentic builder |
| 12 | `tests/modules/copilot/test_voice_combined.py` | 410 Gone | KEEP — owns agentic builder |
| 13 | `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` | `@pytest.mark.flaky(reruns=2)` band-aid + comment | **REMOVE** band-aid pre-ship (Fase 4 polluter fix) |
| 14 | `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | `CAMPAIGN_CONTEXT` | KEEP — owns agentic builder |
| 15 | `tests/shared/domain_events/test_event_bus_adapter.py` | `monkeypatch.setattr` USE_OUTBOX_PATTERN_SALES_AGENT=False | **REVISAR + MIGRAR** a Caso E (meta-test bypass — magic comment) |
| 16 | `src/shared/infrastructure/llm/providers/litellm.py` | Kimi clamp logic | **REVISAR vs § 7 spec** — aplica `_get_chat_model`, formato `kimi/k2`, structlog |
| 17 | `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` | URL `/campañas/` → `/campanas/` | KEEP — fix mecánico |

### Conflict handling

Si `git stash pop` reporta conflict → **NO descartar stash**. Resolución manual file-by-file:
```bash
git status                                    # Ver archivos en conflict
# Para cada archivo conflict:
vim <file>                                    # Resolver markers <<<<<<<
git add <file>                                # Stage manual (NO -A/-u)
# Una vez resueltos todos:
git stash drop                                # Limpiar stash@{0}
```

### Post-pop validation

```bash
cd /home/chris/AISALESHT/backend && \
  .venv/bin/ruff check src/ tests/ --no-cache && \
  .venv/bin/ruff format --check src/ tests/
# Confirma stash apply no rompe lint
```

---

## § 10 — Open Questions for PM

1. **LiteLLM proxy `extra_body={"thinking": {"type": "disabled"}}`** — kimi.py adapter línea 97-101 inyecta este field a `model_kwargs` para forzar thinking disabled (requirement K2.6). litellm.py NO inyecta. ¿Se gestiona via `litellm_config.yaml` proxy-side (overrideando o agregando body en el server)? O ¿necesitamos mirror también en litellm.py?
   - **Decision needed pre-builder Phase 1**: si proxy NO inyecta → litellm.py necesita extender clamp para incluir extra_body manipulation también. Riesgo: producción HTTP 400 silent en otro frente si solo clampamos temp.
   - **Recomendación architect**: verificar `litellm_config.yaml` ANTES de stash apply. Si proxy ya inyecta → spec § 7 OK. Si NO → expandir scope § 7 a incluir extra_body inject.

2. **Polluter Fase 4 budget** — Chris D4 dice "sin budget cap". Architect propone: si supera **6h Opus consecutivas sin avance medible** (no progress in detect-test-pollution output) → escalate Chris para decisión continuar/pivote. ¿OK este threshold operativo?

3. **`agent_app = workflow.compile()` module-level** — Sales_agent graph.py:52 compila al import. Si polluter Fase 4 lo identifica como root cause → singleton fixture necesita `importlib.reload()` (§ 1 candidato B). ¿Aceptable? O ¿prefiere PM refactor `agent_app` a factory pattern (más invasivo, scope expansión)?

4. **`tests/shared/domain_events/test_event_bus_adapter_infers_module.py`** — capability test del adapter; tiene mocks. Stash NO lo modifica. ¿Confirma que va Caso E (bypass arch fitness PR-3 con magic comment) y NO Caso D (que sería test de EventBus mismo)?

5. **Snapshot baseline diff Fase 5** — al migrar `_chat_flow_snapshot_helpers.py` a outbox-aware, snapshot file `tests/modules/sales_agent/snapshots/orchestrator/*.json` debe regenerarse con eventos reales. ¿PM acepta commit del snapshot diff dentro PR-1 (no requiere PR separado)?

6. **frontend test (slug `/campañas/` → `/campanas/`)** — vitest run nativo confirma fix. ¿Necesita auditor frontend o auditor backend cubre via auto-spawn vitest? Decisión PR.md actual: `nicolify-backend-auditor` cubre vitest run. **Confirmar** OK.

---

## § 11 — Surface Mapping (business vs agentic file ownership EXCLUSIVO)

> Regla M3 parallel-safety: paths exclusivos por surface, conftest solo business builder, tests secuencial.

### Business builder owns (`nicolify-backend` Sonnet)

```
backend/tests/conftest.py                                                  # SINGLETON FIXTURE (§ 1-2)
backend/tests/architecture/test_ddd_boundaries.py                         # Allowlist 3 entries
backend/tests/architecture/test_folder_naming.py                          # Exception _dependencies.py
backend/tests/modules/brand/test_brand_section_updated_event.py           # MIGRAR a Caso A
backend/tests/modules/brand/test_outbox_adapter_integration.py            # MIGRAR a Caso B/E
backend/tests/shared/domain_events/test_event_bus_adapter.py              # MIGRAR a Caso E
backend/src/shared/domain/events.py                                       # DEPRECATION WARNING (§ 5)
backend/src/shared/infrastructure/llm/providers/litellm.py                # KIMI CLAMP (§ 7)
backend/tests/shared/infrastructure/llm/providers/test_litellm_kimi_clamp.py  # NEW REGRESSION TEST
backend/tests/shared/test_legacy_event_bus_deprecation_warning.py         # NEW DEPRECATION TEST (§ 5)
frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx  # SLUG FIX (mecánico stash)
```

### Agentic builder owns (`nicolify-agentic` Opus)

```
backend/tests/architecture/test_sales_agent_anchors.py                    # SALES-AGENT-OUTBOUND-PR7
backend/tests/architecture/test_sales_agent_system_prompt_order.py        # CAMPAIGN_CONTEXT
backend/tests/integration/test_outbound_orchestrator_e2e.py               # Mock target rename
backend/tests/modules/copilot/test_offer_section_tools.py                 # next_step_hint
backend/tests/modules/copilot/test_outbox_adapter_integration.py          # MIGRAR a Caso B/E
backend/tests/modules/copilot/test_voice_api.py                           # 410 Gone
backend/tests/modules/copilot/test_voice_combined.py                      # 410 Gone
backend/tests/modules/copilot/test_extraction_event_handlers.py           # MIGRAR a Caso A
backend/tests/modules/copilot/observability/test_domain_subscribers.py    # MIGRAR a Caso A
backend/tests/modules/copilot/observability/test_register.py              # MIGRAR a Caso A
backend/tests/modules/copilot/api/test_suggestions_endpoint.py            # MIGRAR a Caso A
backend/tests/modules/copilot/api/test_suggestions_accept_endpoint.py     # MIGRAR a Caso A
backend/tests/modules/copilot/suggestions/test_suggestion_event_recorded.py  # MIGRAR a Caso A
backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py  # OUTBOX-AWARE (§ 4)
backend/tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py  # POLLUTER FIX + REMOVE FLAKY (§ 6)
backend/tests/modules/sales_agent/orchestrator/test_audit_emitter.py      # MIGRAR a Caso A
backend/tests/modules/sales_agent/tools/payment/test_grant_access_idempotent.py  # MIGRAR a Caso A
backend/tests/modules/sales_agent/prompts/test_compose_system_prompt.py   # CAMPAIGN_CONTEXT
backend/tests/modules/crm/test_sale_lifecycle.py                          # MIGRAR a Caso A
backend/tests/shared/application/test_brand_summary_event_handlers.py     # MIGRAR a Caso A
```

### Shared (NO touch — bypass arch fitness PR-3 con magic comment)

```
backend/tests/shared/test_event_bus.py                                    # Capability test — magic comment + UNCHANGED
backend/tests/shared/domain_events/test_event_bus_adapter.py              # (Business owns ABOVE — magic comment + MIGRATE F=False to bypass)
backend/tests/shared/domain_events/test_event_bus_adapter_infers_module.py  # (NEEDS DECISION § 10 q4)
backend/tests/integration/test_outbox_cutover_e2e.py                      # Caso B/E — probably already correct, ARCHITECT does NOT modify
backend/tests/modules/{brand,copilot,sales_agent}/integration/test_outbox_cutover.py  # Caso B real DB integration
```

### Lock prevention

- `tests/conftest.py` SOLO business builder modifica. Agentic builder NO touches.
- `backend/tests/architecture/test_no_legacy_event_bus_publish.py` SOLO modifica si nuevo `KNOWN_DIRECT_LEGACY_EMITTERS` allowlist entry needed (post audit Fase 2 — solo business builder). Initial: empty allowlist preserved.
- Si business + agentic colisionan editando mismo file → escalate Chris.

---

## § 12 — Research Notes (DATE-AWARE)

| Source | URL | accessed | Knowledge cutoff disclosure | Key takeaway | Why over alternatives |
|---|---|---|---|---|---|
| `detect-test-pollution` GitHub | https://github.com/asottile/detect-test-pollution | 2026-05-04 | Pre-cutoff (tool stable since 2024); WebSearch confirmed canonical 2026-05 | Bisection tool by Anthony Sottile — automatically identifies pair of tests where one pollutes another. Native pytest support. | Manual binary search (Step 1-7 PR.md Phase 4) is 80min spend; tool reduces to ~10min. Validated WebSearch live 2026-05-04. |
| `pytest-bisect-tests` | https://github.com/maciej-gol/pytest-bisect-tests | 2026-05-04 | Same | Alternative bisection tool with auto-discovery — minimal input needed | Backup if `detect-test-pollution` doesn't catch (different bisection strategy) |
| pytest fixture autouse docs | https://docs.pytest.org/en/stable/how-to/fixtures.html#autouse-fixtures-fixtures-you-don-t-have-to-request | 2026-05-04 | Pre-cutoff (pytest stable API) | autouse=True fixtures applied implicitly to all tests in scope; default scope=function (per-test) | Standard for cross-test cleanup; avoids opt-in per-test boilerplate |
| LangGraph state isolation | https://docs.langchain.com/oss/python/langgraph/persistence | 2026-05-04 | Topic researched live (post-Jan 2026 cutoff for LangGraph features) | StateGraph `.compile()` produces CompiledGraph — module-level compilation cache survives unless module re-imported | Confirms § 1 candidate B: `agent_app = workflow.compile()` module-level is polluter risk; reset via `importlib.reload()` if Fase 4 confirms |
| Anthropic prompt caching (LegacyEventBus context) | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-05-04 | N/A (informational reference) | Cache invalidation rules; not directly applied PR-1 but consulted for sales-agent cache prefix invariants (§ 3 D context) | Confirms slot architecture untouched by PR-1 |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. PR-1 patterns (pytest fixtures, SQLA 2.0, deprecation warnings) all pre-cutoff stable APIs — no risk of model confabulation. `detect-test-pollution` tool researched live 2026-05-04 via WebSearch to confirm 2026-current canonical methodology.

---

## § 13 — Cross-link to PR-3 CONTRACT

PR-3 builds on PR-1 outcome:
- **PR-3 § 2 arch fitness test** (`test_no_legacy_eventbus_mock_when_outbox_on.py`) requires PR-1 § 3 EventBus migration COMPLETE (else baseline allowlist needed).
- **PR-3 § 1 rule** (`anti-default-flip-audit.md`) references PR-1 § 5 LegacyEventBus deprecation warning as enforcement layer 1.
- **PR-3 ship POST PR-1 PASS** (recomendación CONTEXT-BRIEF § 9) para evitar deadlock arch fitness baseline.

**Coordination signal:** Builder PR-1 termina Phase 5 → emite señal commit `feat(test): PR-1 PI-11 EventBus migration complete (Fase 5)` → Builder PR-3 puede commitear arch fitness test sin allowlist temporal.

Si PR-3 builder lanza paralelo (sin esperar PR-1 PASS): arch fitness test usa `KNOWN_LEGACY_MOCK_FILES` allowlist temporal con TODOS los files identificados § 3 Caso A pre-migration. Allowlist shrinks conforme PR-1 progress. Final state post-PR-1: allowlist size = 0 (solo Caso D/E con magic comments).

Ver detalle: `../PR-3-anti-default-flip-enforcement/CONTRACT.md`

---

## § 14 — Aceptación CONTRACT-driven (mirror PR.md § Aceptación)

Builder marca cada checkbox cumplido en IMPL-LOG:

- [ ] Stash pop completo + 16 archivos revisados per-archivo (§ 9 checklist)
- [ ] Singleton fixture exhaustive (§ 1-2): 5 singletons + 4 module caches con comments + cleanup hooks
- [ ] EventBus migration audit completo (§ 3): tabla IMPL-LOG con TODOS los archivos del grep + estrategia Caso A/B/C/D/E
- [ ] Snapshot helpers outbox-aware (§ 4): `_capture_outbox_events` implementado + snapshot baseline diff committed
- [ ] LegacyEventBus runtime warning (§ 5): test 4 cases pasa
- [ ] Polluter hunt completo (§ 6): root cause documentado + `@pytest.mark.flaky` REMOVED + 20 sequential runs PASS
- [ ] litellm.py kimi clamp (§ 7): mirror kimi.py + 4 regression tests pasan
- [ ] Arch fitness 78/78 PASS
- [ ] `pytest` 0 failed, 0 deselected, 0 `flaky` permanentes
- [ ] `vitest run` 0 failed (frontend slug fix)
- [ ] Surface mapping respetado (§ 11): builders no colisionan
- [ ] Open questions (§ 10) resueltas pre-merge
- [ ] Cross-link PR-3 (§ 13) coordinación efectiva (señal commit Fase 5 emitida)

