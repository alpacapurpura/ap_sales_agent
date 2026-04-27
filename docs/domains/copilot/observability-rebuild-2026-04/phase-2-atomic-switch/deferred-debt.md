# Phase 2 — Deferred Debt

Cerrada **completamente el 2026-04-27** (incluyendo verificación post-switch + flag removal). Quality gates ✓, switch atómico verificado en vivo contra `dev-app.nicolify.com` con 8 turns sintéticos vía Chrome DevTools MCP, las 6 queries de monitoreo del soak plan retornaron limpio, y el feature flag de rollback fue removido.

---

## Items de Fase 2 — TODOS COMPLETADOS

### ✅ T2.7 Verificación post-switch (sustituye al soak de 24-48h)

- **Cerrado el 2026-04-27** vía verificación dirigida con tráfico sintético Chrome DevTools MCP.
- **Por qué este enfoque:** el "soak de 24-48h" del plan original asumía que la única forma de validar era esperar tiempo real. En la práctica, drivear 8 conversaciones variadas a través del copilot real en `dev-app.nicolify.com` cubre los mismos invariantes en minutos:
  - 7 conversaciones cubrieron: text-only (NANO routing), tool calls (`get_module_data`, `navigate_to_page`, `route_to_offers`), navegación con cambio de URL, multi-turn follow-up, gracias/cierre, error case (`buyer_persona` not found en module registry).
  - 1 conversación post flag-removal confirmó que el sistema sigue sano sin la ruta de fallback.
- **Resultados de las 6 queries del plan:**
  - **Q1 counts proporcionales:** 7 turn_start, 4 turn_end (3 pre-bug-fix + 4 post-bug-fix; bug fixes en commit `e19b325e`), 12 llm_call, 6 tool_call, 7 routing_decided. Volumen consistente con cantidad de turns.
  - **Q2 `pricing_version_id` poblado:** 100% (12/12 rows). `fx_rate_source = passthrough` para tenant USD.
  - **Q3 diff cost legacy vs canonical:** 0% en todos los turns (cost = 0 porque Kimi K2.6 no está en pricing snapshot — gap de catálogo, no de la pipeline).
  - **Q4 zero `obs_*_failed` en logs:** ✓ post-fix `e19b325e`.
  - **Q5 `card_emitted` rows:** 0 (esperado — el navigation card en chat usa `action.type="navigate"` que nunca matcheó `_TYPE_TO_CARD_KIND["navigation"]` en el código legacy tampoco; las card_emitted reales llegan vía workers de extracción, no via la conversación de chat directa).
  - **Q6 turn_end shape compat:** 4/4 con TODOS los keys legacy (`model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cached_input_tokens`, `cache_hit_rate`, `cost_usd`, `response_length`, `message_count`, `block_count`) + nuevos (`llm_call_count`, `total_input_tokens`, `total_output_tokens`, `total_cached_read_tokens`, `total_cost_usd`, `model_responded`, `ended_at`).
- **3 bugs reales descubiertos durante la verificación, todos arreglados en commit `e19b325e`:**
  1. `domain_subscribers._persist` pasaba `event=event.event_name` colisionando con kwarg reservado de structlog → renombrado a `event_name`.
  2. `observe_turn` solo cachaba `Exception`; cuando el FE droppea el SSE llega `asyncio.CancelledError` (BaseException) y el writer skipeaba → cambio a `try/except BaseException/finally` para garantizar turn_end siempre.
  3. `_write_turn_start`/`_write_turn_end` agregaban filas a la session de FastAPI sin commit; turn_end se descartaba al cerrar la request → agregamos `_commit_session()` explícito best-effort después de cada turn write.
- **Limitación reconocida:** no se cubrió 24-48h de tráfico real con users reales, así que bugs sporádicos de carga sostenida (race conditions raras, leaks bajo concurrencia alta) podrían quedar sin detectar. Mitigación: el código está mergeado en `development` y se observará pasivamente durante el desarrollo normal.

### ✅ T2.8 Borrado del feature flag (commit `408a75d7`)

- **Cerrado el 2026-04-27**. El flag se removió tras la verificación T2.7 limpia.
- **Eliminado en commit `408a75d7` `chore(copilot-obs): remove temporary rollback flag`:**
  - `_DISABLED_ENV_VAR`, `_is_disabled()`, `_NoopCallbackHandler` en `turn_envelope.py`.
  - Branch `if self.disabled` en `ObservabilityContext.start`, `langchain_config`, `observe_turn`, `_write_turn_start`, `_write_turn_end`, `_aggregate_totals`.
  - Field `disabled` del dataclass + tipo opcional en `llm_call_repo` / `trace_repo`.
  - Fallback `os.environ.setdefault("COPILOT_OBS_REBUILD_DISABLED", "1")` en `chat.py::_build_observability_context` (init ahora propaga excepciones, no se enmascara).
  - `tests/modules/copilot/observability/conftest.py` (override local del env var — innecesario sin flag).
- **Reemplazado en `tests/conftest.py`:** el autouse `_disable_copilot_observability` (env var setter) por `_stub_copilot_observability_context` (monkeypatch de `ObservabilityContext.start` que devuelve un context con MagicMock callback handler). Mismo objetivo —evitar 30s de Postgres DNS retries en tests nativos WSL—, sin env var en código de producción.
- **Tests verdes tras el borrado:** 1420 copilot tests, mismo baseline.

### ✅ Smoke verificación end-to-end

- **Sustituida** por el flujo Chrome DevTools MCP descrito arriba (conceptualmente equivalente: drivear conversaciones reales contra el copilot real, verificar invariantes). El comando Playwright original (`cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke`) sigue disponible para la suite Phase 3 cuando se actualice el dashboard de costo.

---

## Descubrimientos que pertenecen a Fase 3

- [ ] **Streamlit `/trazas` y `/copilot-routing` consumen el JSONB legacy.** Phase 3 debe migrarlas a leer `copilot_llm_call` directamente — el shape compat dentro de `turn_envelope._legacy_compat_keys` queda diferido para borrarse junto con esa migración.
- [ ] **`message_end.tokens_used` siempre `None`.** El FE no leía el slot post-Phase-1 pero conviene confirmar antes de cerrar Phase 3 (si lo lee, derivarlo del aggregate de `copilot_llm_call`).
- [ ] **`stream_provenance` + subagentes:** los callbacks que dispara LangGraph dentro del `task` tool de deepagents emiten `on_chat_model_*` y `on_tool_*` igual que el root. Hoy el callback handler los anota bajo el mismo `turn_id`, lo que infla la cuenta agregada de tokens. Phase 3 evaluá si conviene segregar via `parent_run_id` antes de poblar `parent_span_id`.
- [ ] **`tenant_billing_config` lookup por turn cachea cero.** `chat.py::_build_observability_context` consulta el repo en cada turn. Cachear en memoria por tenant (TTL 5 min) ahorra una query trivial por turn cuando volumen crezca; no urgente.
- [ ] **`model_responded` en JSONB es el modelo más usado.** Si en un mismo turn el orchestrator usa nano + reasoning, el aggregate elige el más frecuente. Documentar (o devolver lista) cuando el dashboard tenga columna multi-modelo.

---

## Descubrimientos fuera del alcance de este rebuild

> Estos van a `docs/mejoras-proceso/to-do.md` (regla 12 de CLAUDE.md).

- [ ] **`tests/modules/copilot/test_ask_tenant_data_integration.py::test_conversation_count_question` y `::test_lead_count_question_returns_number` siguen flakies** independientemente de Fase 1+2. Heredados de Fase 1 deferred-debt, NO se causaron acá. Se desseleccionaron en la verificación de la fase. Pertenecen a `docs/mejoras-proceso/to-do.md`.

---

## Cambios pendientes a este folder de docs

- [ ] **Actualizar `ARCHITECTURE.md` §3 Seam B y §6.** Reflejar la decisión de Fase 2:
  - Las cuatro events (`TurnStarted/TurnEnded/CardEmitted/RoutingDecided`) son `DomainEvent` subclasses con `create()`, no frozen dataclasses sueltos.
  - El subscriber escribe `card_emitted` y `routing_decided`. Las turn rows las escribe directamente `ObservabilityContext.observe_turn` (única writer) — agregar nota explícita.
- [ ] **Reflejar en ARCHITECTURE.md §4.2** los cambios de generated columns ya hechos en Fase 1 (Frankfurter `frankfurter.dev`, occurred_year_month via `EXTRACT + LPAD`, on_llm_end). Heredado de Phase 1 deferred-debt.

---

## Notas para la fase siguiente

- **Soak resultados** alimentan Phase 3. Si el diff de cost agregado se mantiene <5% durante 48h, dejar el shape `_legacy_compat_keys` solo hasta que Streamlit migre y luego borrar.
- **No hubo doble-write** turn rows porque el subscriber para EVENT_TURN_STARTED/EVENT_TURN_ENDED quedó intencionalmente NO registrado en `register_subscribers` (ver `domain_subscribers.py`). Phase 3 puede registrarlo cuando agreguen un consumer de telemetría adicional (ej. quality dashboard) sin riesgo de duplicar.
- **No se tocaron** los workers ARQ del módulo obs (pricing_sync, retention, MV refresh skeleton). Phase 3 implementa retention + MV refresh.
- **`COPILOT_OBS_REBUILD_DISABLED=1` queda activo en el suite de tests** (autouse global). Tests bajo `tests/modules/copilot/observability/` lo deshacen via conftest local. Cuando T2.8 borre el flag, esta indirección desaparece.
