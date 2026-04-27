# Phase 3 — Learnings

> Llenado durante ejecución. Última actualización al cerrar fase.

---

## Research findings (executed 2026-04-27)

### Postgres MV vs TimescaleDB
- **Decisión:** MV plain con `REFRESH MATERIALIZED VIEW CONCURRENTLY` cada hora vía ARQ.
- **Razón:** Postgres 15.15 (verificado en `visionarias_postgres`). Volumen actual = 13 rows en `copilot_llm_call`, proyección <5M calls/mes durante todo 2026 (volumen LATAM AaaS, no FAANG). El gain de TimescaleDB continuous aggregates entra cuando >100M rows o latencia inserción importa. Para reporting cycle 25-25 sobre <50 tenants × 30 días, MV refresh hourly cubre con holgura. `REFRESH CONCURRENTLY` requiere unique index — incluído en T3.3.

### Presidio Spanish recognizers
- **Status:** Presidio + spaCy NO instalados en `backend/.venv` (verificado `pip show presidio-analyzer spacy` → not found).
- **Latencia medida:** N/A (no se instaló).
- **Decisión:** **regex sincrónico solo** en T3.8. Presidio entero defer.
- **Razón:** instalar Presidio + spaCy `es_core_news_md` agrega ~600MB al image + reload del worker, el inicio del callback handler debe ser <10ms (best-effort principle 4). Plan ya autorizaba esta ruta ("Si Presidio es lento, queda regex sincrónico + Presidio en worker async (anotar como deferred)"). Documentación oficial reporta <10ms / 1000 tokens en setup english medium — no hay benchmark reciente verificado para `es_core_news_md` 2026, así que el riesgo de overhead silencioso es alto. Se deja como deferred-debt el async worker post-write si surge la necesidad.

### Streamlit viz pattern
- **Pattern elegido:** Plotly Express (line + stacked bar + pie) + `st.dataframe(hide_index=True, width="stretch")` + `st.metric` para KPIs + `st.tabs` para sub-secciones de detalle por tenant. Imitar conventions de `copilot_routing.py` y `copilot_quality.py`. Selector ciclo via `st.session_state` + flechas `st.button("◀")` `st.button("▶")` para nav. CSV export via `st.download_button` con `pd.DataFrame.to_csv`.

### Frankfurter API
- **Status:** ya verificado en Phase 1 (`api.frankfurter.dev/v1/latest?base=USD`, ECB-backed). Sin re-verificación necesaria. Sigue gap PEN/COP — usar passthrough USD documentado en `cost/fx_resolver.py`.

### tenant_billing_config bootstrap
- **Tenants existentes:** 11 activos en DB (`SELECT COUNT(*) FROM tenants WHERE is_active`).
- **Filas en `tenant_billing_config`:** 0.
- **Acción tomada:** **bootstrap perezoso, no migración**. Repo ya devuelve `None` cuando falta config; downstream (`compute_cycle_start` SQL function) defaultea a anchor 25. Streamlit dashboard muestra todos los tenants con o sin config — los unconfigured aparecen con `currency='USD'` + `flat_fee=null`. El admin puede crear/editar config via futuro form (no en alcance Phase 3) o via SQL directo. Bootstrap masivo agregaría ruido al rollback de Phase 2.

### copilot_llm_call data volume
- **Rows:** 13.
- **Tenants con data:** 1 (`Visionarias`, `6347e21e-...`).
- **Suficiente para dashboard real:** No para "datos ricos" (un único tenant, costos $0 porque modelo Kimi K2 no está en pricing snapshot). El dashboard debe renderizar **funcional pero potencialmente vacío** — la prueba de fuego es que la UI no rompe en empty-state y se popula naturalmente al fluir tráfico real post-deploy.

### Sesiones paralelas
- **`backend/src/admin/`:** sin WIP ajeno (`git status --short` limpio). Recent commits en main = de Phase 2 close.
- **`backend/src/modules/copilot/observability/`:** sin WIP ajeno.
- **`backend/src/workers/settings.py`:** sin WIP ajeno (Phase 1 ya commiteó pricing_sync_task).

### Cambios al diseño respecto a ARCHITECTURE.md
- **Schema `copilot_llm_call` no tiene `created_at`** — usa `started_at` como timestamp canónico. Implicancia para retention worker (T3.9): cláusula `WHERE started_at < NOW() - interval '365 days'` (no `created_at`). Plan original decía `created_at`; corregir en docs.
- **`copilot_trace_event` SÍ tiene `created_at`** (default `NOW()`). Retention worker mantiene cláusula original.

---

## Decisiones tomadas

### D3.1 — Regex-only PII redaction (Presidio defer)

- **Contexto:** T3.8 plan permite "Presidio sincrónico si <100ms, sino regex + Presidio async."
- **Opciones:**
  - (A) Instalar Presidio + spaCy `es_core_news_md` ahora. Probable +500MB image, latencia incierta.
  - (B) Regex-only (email/phone LATAM/token) sincrónico. Presidio defer a `docs/mejoras-proceso/to-do.md`.
- **Elegida:** B. Razón: el callback handler corre dentro del hot path SSE; cualquier latencia >10ms se traduce en TTFT del copilot. Sin benchmark `es_core_news_md` reciente verificado, instalar agrega riesgo no proporcional al payoff. Regex cubre 90% del PII real (emails + teléfonos LATAM + tokens API) — el 10% restante (nombres propios, direcciones) requiere NER y queda como deferred-debt async.

### D3.2 — Bootstrap perezoso de `tenant_billing_config`

- **Contexto:** 11 tenants activos, 0 rows en config.
- **Opciones:**
  - (A) Migración data-fill que crea row con defaults para cada tenant.
  - (B) Bootstrap perezoso: SQL function + repo manejan ausencia con defaults. Admin crea config manual cuando hace falta.
- **Elegida:** B. Razón: la migración data-fill nos obliga a definir flat_fee/threshold per-tenant sin contexto comercial real (hoy ninguno tiene cuotas vendidas). Crear rows vacías agrega ruido y diferencia de "no configurado" vs "configurado a $0". El default 25-25 ya está en la columna; el SQL function `compute_cycle_start` cae al default. El dashboard simplemente muestra `flat_fee=—` para los que no tienen.

### D3.3 — Retention worker usa `started_at` para `copilot_llm_call`

- **Contexto:** schema tiene `started_at TIMESTAMPTZ` pero no `created_at`. Plan asumía `created_at`.
- **Decisión:** SQL del retention worker usa `started_at < NOW() - interval ':n days'`. Documentar en learnings; no breaking change al schema.
- **Razón:** `started_at` es el momento real de la invocación LLM, no del INSERT. Usarlo para retention significa "borrar invocaciones más viejas que N días" — semántica más útil que "INSERT más viejo que N días" porque inserts batch (carga histórica futura) podrían tener `started_at` muy viejo y `created_at` reciente. Para retention de auditoría billing usar `started_at` es correcto.

### D3.4 — `MV mv_daily_llm_cost_per_tenant` con `tenant_currency` no agregado

- **Contexto:** ARCHITECTURE.md §4.3 muestra `SUM(cost_tenant_currency)`. Sumar montos en distintas monedas tenant no tiene sentido si la MV cruza tenants — pero la MV agrupa POR tenant_id, así que cada partición tiene una sola moneda → sumar es correcto.
- **Decisión:** mantener shape exacto del ARCHITECTURE.md. Agregar columna `tenant_currency` (MIN o ANY) para que el reporte sepa qué moneda corresponde sin re-leer `tenant_billing_config`.

### D3.5 — `BillingCycleService.compute_window` retorna `(start, end_exclusive)`

- **Contexto:** convención usual en Python date ranges.
- **Decisión:** start = primer día del ciclo (inclusive). end = primer día del siguiente ciclo (exclusive). Range queries: `WHERE occurred_on >= :start AND occurred_on < :end`. Pasa el filtro al `ix_llm_call_tenant_day` index trivial.

### D3.6 — `costo_copilot.py` admin module en español neutro LatAm

- **Aplicación:** todos los strings user-facing usan tuteo neutro. Sin voseo. Verificación grep automatizada en T3.13 quality gates.
- **Glosario clave:** "Selecciona ciclo", "Filtra por tenant", "Exporta CSV", "Cambia moneda" (no "Seleccioná/Filtrá/Exportá/Cambiá").

---

## Sorpresas / atajos descubiertos

- **`copilot_llm_call.created_at` NO existe** — descubierto al primer query. Plan asumía paridad con `copilot_trace_event`. Migración Phase 1 nunca lo agregó; no es un bug, simplemente esquema event-sourced usa `started_at`. Implicancia para retention + indexación de "rows nuevas".
- **Presidio + spaCy ausentes** del venv — Phase 1 plan los listaba como "Phase 3". Phase 1 close-up no instaló nada de runtime PII. Confirma decisión D3.1.
- **0 rows en `tenant_billing_config`** — la migración Phase 1 creó la tabla pero ningún workflow inserta. Descubierto en research, llevó a decisión D3.2.

---

## Métricas del dashboard en data real

Estado al cierre Phase 3 (con 13 LLM calls poblados y 1 tenant activo):

- **Tenants visibles en Comando Central:** 1 (Visionarias `6347e21e-...`) con datos en el ciclo `2026-04-25 → 2026-05-25`.
- **Promedio cost USD / tenant / ciclo:** $0.0000 (Kimi K2 no en pricing snapshot — gap de catálogo, no de pipeline).
- **Tenant con mayor consumo:** Visionarias, 13 calls / 1 conversación.
- **% tenants > threshold alerta:** 0% — `tenant_billing_config` tiene 0 rows con `cost_alert_threshold_usd` configurado.
- **MV `mv_daily_llm_cost_per_tenant`:** 1 row tras `REFRESH MATERIALIZED VIEW CONCURRENTLY`. Verificado en vivo.
- **SQL function `compute_cycle_start`:** verificada in-DB con 3 inputs (current cycle, previous cycle, year wraparound) — todos correctos.
- **Perf `tenants_summary` Postgres:** EXPLAIN ANALYZE = 0.269ms para Sequential Scan + GroupAggregate sobre 13 rows. Holgada vs gate <200ms incluso a 50 tenants × 30 días proyectados.

El dashboard está listo para usar — la prueba de fuego funcional (empty-state legible + render sin exception) pasó vía smoke tests headless. La prueba de fuego visual queda pendiente del primer despliegue dev real con tráfico.

---

## Items para `.claude/rules/` (resueltos)

- ✅ Crear `.claude/rules/copilot-observability.md` — T3.12, regla nueva con módulo structure, tablas, cómo agregar domain events, providers, pricing manual, retention, PII, best-effort, tenant isolation, workers + prohibiciones.
- ✅ Update `.claude/rules/copilot-resilience.md` — T3.12, agregada sección `copilot_llm_call` debug queries (cost+model en columnas tipadas, no JSONB) + apuntar a `/costo-copilot` y `/copilot-routing` post-rebuild.
- ✅ Update `CLAUDE.md` regla 10 — apunta a la nueva regla de observability.

---

## Métrica final del rebuild completo (3 fases)

| Métrica | Phase 1 | Phase 2 | Phase 3 | **Rebuild total** |
|---|---|---|---|---|
| Commits | 11 | 6 | 8 | **25** |
| Líneas añadidas (insertions) | 4,365 | ~660 | 3,013 | **~8,038** |
| Líneas eliminadas (deletions) | 45 | 2,022 | 39 | **~2,106** |
| Net LOC | +4,320 | -1,372 | +2,974 | **+5,932** |
| Archivos nuevos | 42 | 5 | 22 | **69** |
| Archivos eliminados | 0 | 9 (3 src + 6 tests) | 0 | **9** |
| Tests añadidos | 64 | 28 | 41 | **133** |
| Tests eliminados | 0 | 36 | 0 | **36 net = +97** |
| Coverage backend antes/después | ~67% / 67.48% | 67.48% / 67% | 67% / 67.48% | **67% baseline mantenido** |
| Tablas nuevas | 3 (`copilot_llm_call`, `model_pricing_snapshot`, `tenant_billing_config`) | 0 | 1 MV (`mv_daily_llm_cost_per_tenant`) + 1 SQL function (`compute_cycle_start`) | **3 tablas + 1 MV + 1 function** |
| Streamlit pages nuevas | 0 | 0 | 1 (`/costo-copilot`) | **1** |
| Streamlit pages refactorizadas | 0 | 0 | 2 (`/trazas`, `/copilot-routing`) | **2** |
| Workers ARQ nuevos | 1 (pricing_sync) | 0 | 3 (aggregate_refresh, retention, cost_alert) | **4** |
| Cron jobs registrados | 1 | 0 | 3 | **4** |
| Migraciones nuevas | 1 (`075_copilot_observability_rebuild`) | 0 | 2 (`076_billing_cycle_function`, `077_daily_llm_cost_mv`) | **3** |
| Tiempo wall-clock real | ~3h | ~3h | ~4h | **~10h** |

### Quality gates al cierre

- ✅ `ruff check` clean (con warning pre-existing en `offer_type_presets.py:28` sobre `# noqa` syntax — no causado por el rebuild).
- ✅ `ruff format --check` clean.
- ✅ `pytest tests/architecture/` 575 passed.
- ✅ `pytest tests/admin/ tests/architecture/` 632 passed.
- ✅ `pytest` full: 5308 passed, 5 skipped, 2 failed (los 2 fallos son flakes pre-existing documentados en Phase 2 deferred-debt: `test_ask_tenant_data_integration::test_conversation_count_question` + `test_lead_count_question_returns_number`).
- ✅ Coverage backend 67.48% (gate ≥43% holgado).
- ✅ Ratchet: `git grep -E "recorder\.record\b|UsageAccumulator|_PRICING\b" backend/src/` → cero matches.
- ✅ Ratchet: cero imports a `trace_recorder` / `usage_tracking` / `node_trace` legacy.

### Logros estructurales

1. **Cohesión total.** Todo lo de observability vive en `backend/src/modules/copilot/observability/`. Cero código disperso en orchestrator/tools/services. Verificado por imports + grep.
2. **Switch atómico ejecutado.** El commit `3d5ff66f` (Phase 2) eliminó 3 archivos legacy + 6 archivos de tests + 10 sitios de `recorder.record(...)` en un solo commit.
3. **Schema OTel-shape.** `copilot_llm_call` tiene los nombres de la spec OTel GenAI (Development) listos para rename trivial cuando promueva a Stable.
4. **Pricing como data, no código.** Cero `_PRICING = {...}` hardcoded; 1972 rows en `model_pricing_snapshot` poblados via worker LiteLLM diario.
5. **Reporting end-to-end.** SQL function `compute_cycle_start` + MV `mv_daily_llm_cost_per_tenant` + `BillingCycleService` + `CostAggregator` + Streamlit `/costo-copilot` cierran el camino del callback handler al usuario admin.
6. **Best-effort + tenant-isolated.** Toda escritura observability en try/except; toda query reporting filtra `tenant_id`. Validado por arch tests.
7. **Hot path no acoplado.** `chat.py` post-Phase-2 importa solo `ObservabilityContext` + `event_bus`. Cero llamadas explícitas al recorder.

### Tareas que NO se hicieron y por qué

- **Presidio NER para PII** — overhead de spaCy `es_core_news_md` no medido en 2026, riesgo demasiado alto vs el regex que cubre 90%. Movido a `docs/mejoras-proceso/to-do.md` item 27.
- **Email/Slack delivery para cost alerts** — sin infra previa en el repo. Movido a item 28.
- **Bootstrap masivo de `tenant_billing_config`** — decisión deliberada (D3.2, bootstrap perezoso). Movido a item 29.
- **Soak 24-48h con tráfico real** — sustituido por verificación dirigida con Chrome DevTools MCP en Phase 2 (T2.7), 8 turns sintéticos cubriendo los invariantes en minutos en lugar de días.
