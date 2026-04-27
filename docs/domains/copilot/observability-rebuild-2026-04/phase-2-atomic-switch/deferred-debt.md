# Phase 2 — Deferred Debt

Cerrada el **2026-04-26 (commit del switch atómico) + soak en curso**. Quality gates ✓; el soak de 24-48h y el borrado del feature flag NO se pueden completar dentro de la sesión del agente — quedan listados en "Items de Fase 2 NO completados" para que un humano los ejecute como follow-up explícito.

---

## Items de Fase 2 NO completados

### ⏳ Soak de 24-48h en `dev` environment (T2.7)

- **Estado:** pendiente. El switch atómico está mergeado a `development` con feature flag `COPILOT_OBS_REBUILD_DISABLED` apagado por default. Mantener mergeado y monitorear durante 24-48h antes de declarar la fase totalmente cerrada.
- **Por qué se difirió:** los gates de soak requieren tráfico real del copilot en dev environment + 24-48h wall-clock. No se puede satisfacer en una sesión sincrónica del agente.
- **Plan de remediación:**
  1. Mergeado en `development` (commit `3d5ff66f` `feat(copilot-obs): atomic switch ...`).
  2. Containers up: `docker compose up -d`.
  3. Llamadas reales al copilot durante 24-48h via dev-app.nicolify.com.
  4. Monitoreo:
     ```bash
     # Sin warnings críticos.
     docker logs visionarias_brain_dev --tail 500 \
         | grep -i "trace_event_write_failed\|llm_call_write_failed\|obs_"

     # Volumen consistente con turns.
     docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs \
       -c "SELECT COUNT(*), date_trunc('hour', created_at) AS h
           FROM copilot_llm_call WHERE created_at > NOW() - interval '24 hours'
           GROUP BY h ORDER BY h DESC LIMIT 24;"

     # turn_end mirror activo.
     docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs \
       -c "SELECT COUNT(*) FROM copilot_trace_event
           WHERE event_type='llm_call' AND created_at > NOW() - interval '24 hours';"

     # Diff cost agregado por turn_id (debe ser <5%).
     docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c "
       WITH per_turn AS (
         SELECT t.turn_id,
                (t.data->>'cost_usd')::numeric  AS legacy,
                (SELECT SUM(c.cost_usd)
                   FROM copilot_llm_call c
                   WHERE c.turn_id = t.turn_id
                     AND c.tenant_id = t.tenant_id) AS canonical
           FROM copilot_trace_event t
          WHERE t.event_type='turn_end'
            AND t.created_at > NOW() - interval '24 hours'
       )
       SELECT COUNT(*) FILTER (WHERE ABS(legacy - canonical) / NULLIF(canonical,0) > 0.05) AS over_5pct,
              COUNT(*) AS total
         FROM per_turn;
     "
     ```
- **Si el soak revela un bug:** activar el flag (`echo COPILOT_OBS_REBUILD_DISABLED=true >> .env; docker compose restart`). Si el flag no alcanza, `git revert 3d5ff66f` (NUNCA `git reset --hard` sobre development).

### ⏳ Borrado del feature flag tras soak (T2.8)

- **Estado:** pendiente, dependencia de T2.7.
- **Acción cuando el soak salga limpio:**
  1. Quitar las ramas `_is_disabled()` / `_NoopCallbackHandler` de `backend/src/modules/copilot/observability/recording/turn_envelope.py`.
  2. Quitar el fallback en `chat.py::_build_observability_context` (`os.environ.setdefault(...)`).
  3. Quitar la línea `monkeypatch.setenv("COPILOT_OBS_REBUILD_DISABLED", "1")` del autouse en `tests/conftest.py` (la observabilidad va a fallar en silencio sin DB Docker — agregar nota en el rule `.claude/rules/copilot-resilience.md` + en `tests/conftest.py` apuntando al fixture local de `tests/modules/copilot/observability/conftest.py` como referencia).
  4. Borrar la documentación del flag en `.env.example` (no se agregó porque el default es seguro).
  5. Commit: `chore(copilot-obs): remove temporary rollback flag`.
- **Riesgo si NO se borra:** el flag queda como deuda eterna y futuros agentes asumen que es soportado.

### ⏳ Smoke E2E Playwright `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke`

- **Estado:** no ejecutado. Requiere `docker compose up -d` activo y autenticación Clerk válida (no disponibles en la sesión del agente).
- **Acción cuando levantes containers:** correr el comando arriba antes de iniciar Phase 3.

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
