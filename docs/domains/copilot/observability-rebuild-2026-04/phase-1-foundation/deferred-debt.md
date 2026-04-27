# Phase 1 — Deferred Debt

> Items de Fase 1 que NO se completaron + items descubiertos que pertenecen a fases siguientes.

Cerrada el **2026-04-26**. Todos los gates de `completion-checklist.md` pasaron salvo dos tests preexistentes que se confirmaron flakies antes de Fase 1 (ver "Descubrimientos fuera del alcance").

---

## Items de Fase 1 NO completados

Ninguno bloqueante. Todas las tasks T1.1–T1.13 cerraron con criterio de aceptación verificado.

Salvedades documentadas (no bloquean cierre):

- [ ] **`sync_pricing` produce ~1% de updates fantasma** — dos corridas consecutivas con la misma respuesta de GitHub mueven 22 filas (sobre 1972). Causa probable: pricing valores fuera del rango `NUMERIC(14,12)` (e.g. tasas Bedrock con 13 decimales) sufren rounding en DB y re-comparan distinto en la segunda pasada. Razón para diferir: cero impacto en costo per-call (la versión activa siempre es la última snapshot, así que cualquier cálculo posterior a la primer corrida usa el valor "redondeado" estable). Bloquea reportes Fase 3 con timeline-of-changes? Sí potencialmente — antes de Fase 3 evaluar (a) bumpear precisión a `NUMERIC(20,14)` vía migración aditiva, o (b) cuantizar `Decimal(...).quantize(Decimal("1E-12"))` en el sync antes de comparar.
- [ ] **Frankfurter no cubre PEN/COP** — `FXResolver` cae a `fx_unsupported` (rate=1.0) para esas dos monedas. Razón para diferir: Visionarias (tenant principal LATAM) tiene tarifa flat USD; ningún tenant productivo factura en PEN/COP hoy. Owner próximo (Fase 3): evaluar `exchangerate.host` como fallback secundario o compra de tier de `openexchangerates.org`.

---

## Descubrimientos que pertenecen a Fase 2

- [ ] **Wireup en chat.py es de 4 puntos, no 3.** El plan original dice "obs.start_turn / obs.end_turn / RunnableConfig". Faltó listar el cleanup del `_isolate_trace_recorder_db` autouse fixture en `tests/conftest.py:115-138` — cuando la atomic switch borre `trace_recorder.py`, ese autouse hace `monkeypatch.setattr(trace_recorder, "_session_factory", ...)` y se romperá. Plan: en Fase 2, junto con borrar `trace_recorder.py`, eliminar el autouse y dejar que la nueva `ObservabilityContext` se inyecte vía fixture explícita en los tests que la necesitan.
- [ ] **Domain events del copilot no tienen clases tipadas todavía.** `domain_subscribers.py` consume `DomainEvent` genérico con `payload` JSONB. Fase 2 debería agregar a `src/modules/copilot/domain/events.py` (no existe aún) las clases `CardEmitted`, `RoutingDecided`, `TurnStarted`, `TurnEnded` con `@classmethod create(...)`, mismo pattern que `SaleCompletedEvent` en `shared/domain/events.py`. Eso da type-safety end-to-end.
- [ ] **Cron de `sync_litellm_pricing` corre sin estado.** El task no persiste el último ETag en Redis ni en una tabla; la próxima corrida no usa `If-None-Match`. Bajo costo (GitHub raw es CDN-cached). Si Fase 3 quiere reducir tráfico saliente: agregar `tenant_billing_config`-style row global con `last_sync_etag`.
- [ ] **`copilot_llm_call` no captura `parent_span_id` real.** La columna existe pero el callback handler la deja en `NULL` porque `BaseCallbackHandler` recibe `parent_run_id` y no lo correlacionamos. Útil para construir el span tree completo en `/trazas`. Fase 2 agrega `_resolve_parent_span(run_id, parent_run_id)` que mapea `run_id`s a `span_id`s persistidos.

---

## Descubrimientos que pertenecen a Fase 3

- [ ] **`copilot_llm_call.cost_tenant_currency` precisión NUMERIC(16,8) limita FX para JPY (sin decimales).** Para tenants con monedas con escala distinta a 2 decimales, vale la pena convertir el almacenamiento a `NUMERIC(18,6)`. No bloquea Fase 1.
- [ ] **MV `mv_daily_llm_cost_per_tenant` (ARCHITECTURE.md §4.3) no está creada.** El skeleton de `aggregate_refresh_task.py` está en `workers/__init__.py` pero no su implementación. Es parte explícita de Fase 3.
- [ ] **PII redaction (Presidio + regex) en `recording/sanitization.py`.** Hoy es solo `truncate(value, 4000)`. Plan documentado en `PRINCIPLES.md` §8.
- [ ] **Retention policy en `copilot_trace_event`.** `retention_task.py` skeleton vacío.
- [ ] **Streamlit dashboard de costos por tenant.** Owner: Fase 3.
- [ ] **`PricingResolver` LRU no es thread-safe.** Single-process con uvicorn no es problema, pero si Fase 3 introduce multi-worker con cache compartido por Redis, este detalle aplica.

---

## Descubrimientos fuera del alcance de este rebuild

> Estos van a `docs/mejoras-proceso/to-do.md` (regla 12 de CLAUDE.md).

- [ ] **`tests/modules/copilot/test_ask_tenant_data_integration.py::test_conversation_count_question` y `::test_lead_count_question_returns_number` fallan en `development` independientemente de Fase 1.** Reproducido con `git checkout e7f6b248 -- backend && pytest <testname>` — falla idéntico. Síntoma: `result_count == 1` esperaba `3`. Causa probable: filtro "esta semana" del intent classifier resuelve un rango que no cubre la fecha en la que las fixtures fueron sembradas, dependiente de la fecha actual del sistema (2026-04-26). Reportado como "pre-existing flake" — agregar a `docs/mejoras-proceso/to-do.md` para que un agente futuro lo investigue.

---

## Cambios pendientes a este folder de docs

- [ ] **Actualizar `ARCHITECTURE.md` §3 Seam A.** El doc lista `on_chat_model_end` como hook del callback handler — la API real de `langchain_core.callbacks.BaseCallbackHandler` solo expone `on_llm_end` (que dispara para chat y no-chat). El nombre `on_chat_model_end` es del stream-event de `LangGraph.astream_events`. Cambio menor: reemplazar `on_chat_model_end` → `on_llm_end` en la tabla de Seam A. Documentado en `learnings.md` D1.2.
- [ ] **Actualizar `ARCHITECTURE.md` §4.2.** Cambiar el snippet del SQL para `occurred_year_month` — la versión actual usa `to_char(...)` (rechazado por Postgres por no ser IMMUTABLE). Reemplazar por la versión `EXTRACT(YEAR ...) || '-' || LPAD(EXTRACT(MONTH ...), 2, '0')` que sí compila.
- [ ] **Pequeña adición en `PRINCIPLES.md` §6.** Aclarar que `mode in {chat, completion}` es el filtro del sync — los image/audio entries de LiteLLM se saltan a propósito en Phase 1.

> Estos cambios son sin riesgo (solo docs) — pueden hacerse al inicio de Fase 2 junto con la lectura del ARCHITECTURE.md actualizado.
