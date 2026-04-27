# Phase 2 — Atomic Switch

**Objetivo:** en un solo commit, cablear el módulo nuevo en el hot path **y borrar** el código viejo. Cero paralelo, cero deprecation.

**Riesgo al copilot:** **alto**. Cambios en `chat.py`, `extraction_card_flow.py`, deletion de `trace_recorder.py` + `usage_tracking.py` + `node_trace.py`. Requiere ventana sin WIP paralelo en esos archivos.

**Duración estimada:** 1 día efectivo + 24-48h soak en dev antes de prod.

**Pre-condición:** Fase 1 cerrada (todos items de su `completion-checklist.md` ✓).

---

## Ventana de ejecución

**Antes de empezar:**
1. `git status --short` y `git stash list`. Si hay WIP en chat.py o archivos en scope → coordinar con sesión paralela. Si no se puede coordinar, **postergar fase**.
2. Confirmar con usuario que es buen momento (no hay deploys pendientes).
3. Reservar 4-6h sin interrupciones.

---

## Tasks

### T2.1 — Research checklist

Ejecutar `research-checklist.md` antes de tocar código. ~30 min.

---

### T2.2 — Bootstrap del event bus en copilot

**Acción:** confirmar/ajustar el event bus en `backend/src/shared/events/event_bus.py`.

- Si no existe pattern publish-subscribe sincrónico → crearlo. Pattern: in-process `dict[type[Event], list[Callable]]`, `publish(event)` invoca subscribers en orden, captura excepciones de subscribers (best-effort, no rompe publisher).
- Si ya existe → reutilizarlo.

**Tests primero:** `tests/shared/events/test_event_bus.py` — publish→subscribe, multiple subscribers, exception en subscriber no rompe a otros.

**Criterio aceptación:** event bus funcional, tests verdes.

---

### T2.3 — Definir domain events copilot

**Acción:** en `backend/src/modules/copilot/domain/events.py`:

```python
@dataclass(frozen=True)
class TurnStarted:
    tenant_id: UUID
    user_id: UUID | None
    conversation_id: UUID | None
    turn_id: UUID
    message_preview: str
    current_route: str | None
    guided_mode: bool
    attachment_count: int
    started_at: datetime

@dataclass(frozen=True)
class TurnEnded:
    tenant_id: UUID
    turn_id: UUID
    response_length: int
    message_count: int
    block_count: int
    duration_ms: int
    ended_at: datetime

@dataclass(frozen=True)
class CardEmitted:
    tenant_id: UUID
    turn_id: UUID
    card_kind: str
    source_tool: str
    payload_keys: list[str]
    emitted_at: datetime

@dataclass(frozen=True)
class RoutingDecided:
    tenant_id: UUID
    conversation_id: UUID
    message_id: UUID
    tier_selected: str
    classifier_used: str
    reason: str
    confidence: Decimal | None
    user_msg_length: int
    tools_available: int
    decided_at: datetime
```

**Tests primero:** `tests/modules/copilot/domain/test_events.py` — instancia + frozen + serialización (si JSONB).

**Criterio aceptación:** events definidos, tests verdes, no hay imports cruzados (events son puro dato).

---

### T2.4 — Registrar subscribers en boot

**Acción:** en `backend/src/modules/copilot/observability/__init__.py`:

```python
def register(event_bus) -> None:
    """Registra subscribers del módulo en el event bus.
    
    Llamar una sola vez en startup de FastAPI app (lifespan).
    """
    from .recording.domain_subscribers import register_subscribers
    register_subscribers(event_bus)
```

En `backend/src/main.py` (lifespan startup): `from src.modules.copilot.observability import register as register_obs; register_obs(event_bus)`.

**Tests primero:** `tests/modules/copilot/observability/test_register.py` — invocar register + publicar evento + verificar persistencia.

**Criterio aceptación:** test verde, startup app funciona.

---

### T2.5 — **EL switch atómico** (un solo commit)

> Este es **el** commit grande. Hacerlo todo o nada. Si algo falla, revert completo.

**Acciones en orden:**

#### 2.5.1 — `chat.py`: reemplazar setup obs

ANTES (borrar):
```python
usage = UsageAccumulator(model=_settings.get_model(ModelRole.AGENT))
acc = _StreamAccumulator()
recorder = trace_recorder.start(tenant_id=..., user_id=..., conversation_id=...)
acc.recorder = recorder
recorder.record(event_type="turn_start", ...)
# ... ~10 sitios más con recorder.record(...)
recorder.record(event_type="turn_end", ...)
usage.log(...)
```

DESPUÉS:
```python
from src.modules.copilot.observability.recording.turn_envelope import ObservabilityContext

obs = ObservabilityContext.start(
    tenant_id=tenant_id,
    user_id=user_id,
    conversation_id=conv_uuid,
)
event_bus.publish(TurnStarted(
    tenant_id=tenant_id, user_id=user_id, conversation_id=conv_uuid,
    turn_id=obs.turn_id, message_preview=message[:200],
    current_route=state.get("client_context", {}).get("current_route"),
    guided_mode=bool(state.get("client_context", {}).get("guided_mode")),
    attachment_count=len(blocks or []),
    started_at=utc_now(),
))

# graph stream con callbacks via config:
async for event in graph.astream_events(state, version="v2", config=obs.langchain_config()):
    # ... no más usage.update_from_event(event)
    # ... no más recorder.record() en el loop
    # solo procesamiento de SSE events

event_bus.publish(TurnEnded(
    tenant_id=tenant_id, turn_id=obs.turn_id,
    response_length=len(acc.full_response),
    message_count=len(acc.messages),
    block_count=len(acc.emitted_blocks),
    duration_ms=int((time.monotonic() - turn_start_ts) * 1000),
    ended_at=utc_now(),
))
```

#### 2.5.2 — `extraction_card_flow.py`: reemplazar `recorder.record(event_type='card_emitted',...)` por `event_bus.publish(CardEmitted(...))`.

#### 2.5.3 — Routing decision (líneas chat.py:681 y :760): publish `RoutingDecided` event en vez de `recorder.record(event_type='routing_decision',...)`. El subscriber actualiza tanto `copilot_routing_log` como `copilot_trace_event`.

#### 2.5.4 — Borrar archivos:

```bash
git rm backend/src/modules/copilot/application/observability/trace_recorder.py
git rm backend/src/modules/copilot/application/observability/node_trace.py
git rm backend/src/modules/copilot/application/orchestrator/usage_tracking.py
```

#### 2.5.5 — Limpiar imports muertos:

`grep -r "from src.modules.copilot.application.observability.trace_recorder import" backend/src/` → ajustar/borrar imports.
`grep -r "from src.modules.copilot.application.orchestrator.usage_tracking import" backend/src/` → ajustar/borrar.
`grep -r "from src.modules.copilot.application.observability.node_trace import" backend/src/` → ajustar/borrar.

#### 2.5.6 — Limpiar tests viejos:

- `backend/tests/modules/copilot/test_trace_recorder.py` → reescribir como `test_event_store.py` apuntando al nuevo repo, o borrar si redundante con tests de Fase 1.
- Cualquier test que mockee `UsageAccumulator` → borrar mocks, reemplazar.

#### 2.5.7 — Mantener compat de `copilot_trace_event.event_type='turn_end'.data`:

Por compat con Streamlit existente (`/trazas`, `/copilot-routing`) que aún lee de ese JSONB hasta Fase 3, el subscriber de `TurnEnded` agrega summary al JSONB con shape similar al actual:

```json
{
  "model": "<model más usado en el turn>",
  "prompt_tokens": <SUM>,
  "completion_tokens": <SUM>,
  "total_tokens": <SUM>,
  "cached_input_tokens": <SUM>,
  "cache_hit_rate": <ratio>,
  "cost_usd": <SUM>,
  "response_length": ...,
  "message_count": ...,
  "block_count": ...
}
```

**Pero** la fuente de verdad ya es `copilot_llm_call`. Este JSONB es una **proyección denormalizada** para la UI vieja, no es donde se calcula. En Fase 3 cuando Streamlit migre a leer `copilot_llm_call` directo, este shape se simplifica.

**Tests primero (obligatorio):**

- `tests/modules/copilot/observability/test_atomic_switch.py`:
  - Setup: copilot graph completo (no mock).
  - Mandar mensaje sintético.
  - Assert:
    - 1 row `turn_start` en `copilot_trace_event`.
    - 1 row `turn_end` en `copilot_trace_event` con `data.cost_usd > 0`.
    - ≥1 row en `copilot_llm_call` con cost coincidente con `turn_end.data.cost_usd` ±1%.
    - 0 imports a `trace_recorder` / `usage_tracking` / `node_trace` en backend/src/.

**Criterio aceptación:**
- Test atomic_switch verde.
- `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches.
- Smoke manual: copilot funciona.
- E2E Playwright (si Fase 1 no rompió E2E): smoke pasa.

---

### T2.6 — Feature flag temporal de rollback

**Acción:** Agregar env var `COPILOT_OBS_REBUILD_DISABLED=false` (default).

Si `=true`: `ObservabilityContext.start` retorna un noop context (no callbacks, no event bus, no rows). Para rollback de emergencia sin revert de código.

**Tests:** `test_disabled_flag.py` — flag activo no escribe ninguna row.

**Criterio aceptación:** flag funciona, `.env.example` actualizado, doc en `learnings.md` con plan de borrarlo en commit posterior.

> **Borrar el flag** en commit separado dentro de Fase 2 (o al inicio de Fase 3) tras 24-48h de soak en dev.

---

### T2.7 — Soak en dev environment

**Acción:** mergear el commit de switch atómico a development. **No tocar más en 24-48h.** Monitorear:

- `docker logs visionarias_brain_dev --tail 200 | grep -i "trace_event_write_failed\|llm_call_write_failed\|observability"`
- `SELECT COUNT(*), date_trunc('hour', created_at) FROM copilot_llm_call GROUP BY 2 ORDER BY 2 DESC LIMIT 24;`
- `SELECT COUNT(*) FROM copilot_trace_event WHERE created_at > NOW() - interval '24 hours' AND event_type = 'llm_call';` → > 0 después de algunos turns.
- Comparar `SUM(cost_usd)` desde `copilot_llm_call` vs `SUM((data->>'cost_usd')::numeric)` desde `copilot_trace_event` para mismo turn → diff < 5%.

**Criterio aceptación:**
- 24h sin warnings críticos.
- Volumen de rows en `copilot_llm_call` consistente con cantidad de turns.
- Diff de cost agregado < 5%.

---

### T2.8 — Borrar feature flag

**Acción:** un commit separado: `chore(copilot-obs): remove temporary rollback flag`.

- Borrar el branch del flag en `ObservabilityContext.start`.
- Borrar la env var de `.env.example`.
- Test del flag → borrar test.

**Criterio aceptación:** sin flag, todo verde.

---

### T2.9 — Quality gates finales

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q  # ≥43%
```

E2E smoke:
```bash
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

**Criterio aceptación:** todo verde.

---

### T2.10 — Cerrar fase

1. Llenar `learnings.md`.
2. Llenar `deferred-debt.md`.
3. Verificar `completion-checklist.md`.
4. Commit final docs.
5. Devolver al usuario el prompt de `handoff-prompts/start-phase-3.md`.

---

## Commits sugeridos

1. `feat(copilot-obs): add domain events module + register hook` (T2.2 + T2.3 + T2.4)
2. `feat(copilot-obs): atomic switch — wire callback handler, delete legacy paths` (T2.5) ← **el commit grande**
3. `chore(copilot-obs): add temporary rollback flag` (T2.6) — opcional, en mismo commit que T2.5 si querés todo junto
4. `chore(copilot-obs): remove temporary rollback flag` (T2.8) — tras soak
5. `docs(copilot-obs): close phase 2 — fill learnings + deferred-debt` (T2.10)

---

## Plan de rollback (si el switch rompe)

Orden:
1. **Flag rollback** (`COPILOT_OBS_REBUILD_DISABLED=true`) → 1 minuto, no requiere deploy de código si flag está activo en prod.
2. **Git revert** del commit `feat(copilot-obs): atomic switch ...` → restaura archivos borrados, vuelve `chat.py`/`extraction_card_flow.py` al estado pre-switch.
3. Investigar root cause con trazas existentes.
4. Re-intentar Fase 2 cuando bug fixed.

**Nunca** rollback con `git reset --hard` sobre `development` (puede borrar WIP de otras sesiones). Solo `git revert <hash>`.
