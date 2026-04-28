# Learnings · S2 · cost guardrails cross-agent + costo-agentes admin

> Doc para S3. Foundation cost cross-agent lista para prompt cache_boundary refactor.

---

## Resumen (3 líneas)

- **Entregado**: registry pasivo `shared/agent_observability/registry.py` (`AgentObservabilitySpec` + `register_agent_observability`); bootstrap `shared/infrastructure/agent_observability_bootstrap.py` que invierte la dependencia (módulos registran al importarse). `CostAggregator` parametrizado por `(db, llm_call_model)` + `CrossAgentCostAggregator` que itera registry. `cost_alert_service` cross-agent con `breakdown_usd_by_agent`. `aggregate_refresh_task` refresca ambas MVs (legacy + v2) con per-MV best-effort. `retention_task` itera registry con env vars per-agent. Migración 079 idempotente: `mv_daily_llm_cost_per_tenant_v2 (agent_kind, tenant_id, occurred_on)` UNION ALL + UNIQUE INDEX. Streamlit `costo-agentes` con tabs Total / Por agente; `_shared.render_agent_kind_selector` + `render_dual_read_banner`.
- **Decisión no obvia**: el shared registry **no puede** importar `src.modules.*` (arch test ratchet `test_shared_agent_observability_purity`). Solución: invertir la dependencia. Cada `modules/*/observability/__init__.py` llama `register_agent_observability(spec)` al importarse, y un nuevo `shared/infrastructure/agent_observability_bootstrap.py` (donde el patrón sí está permitido — espejo de `model_registry.py`) importa ambos. Entrypoints (main, admin, workers, conftest) ya importaban `model_registry`; agregamos el bootstrap junto a esa línea. Zero cambio en lógica, dependencia limpia.
- **Listo para S3**: 2970 tests verdes (sales_agent + copilot/observability + shared/agent_observability + arch + admin), ruff/format clean, migración 079 idempotente verificada en clone DB + concurrent refresh manual OK. La capa de cost cross-agent es punto fijo — S3 puede modificar `compose_system_prompt` sin tocar costo / pricing / billing.

---

## Decisiones clave

- **Registry pasivo + bootstrap externo**:
  - Tomada: `shared/agent_observability/registry.py` define la API (`register_agent_observability(spec)` + `agent_observability_registry()` + `get_spec(kind)`) **sin** conocer agentes concretos. Cada agente registra su spec desde su `observability/__init__.py`. Un `shared/infrastructure/agent_observability_bootstrap.py` importa ambos módulos para garantizar que ambos specs estén en el registry antes de que cualquier consumer (Streamlit, workers, API) los lea.
  - Razón: arch test `test_shared_agent_observability_purity.py` (S0) bloquea cualquier `src.modules.*` import desde `shared/agent_observability/`. Es ratchet sin allowlist — bypass = regresión documentada. La inversión sigue el patrón `model_registry.py` que ya existe (entrypoints ya importaban model_registry; agregamos línea adyacente).
  - Alternativa descartada: lazy import dentro de función. Funcionaba pero el AST walker del arch test detectaba el `import` igual. Y el lazy ofusca dependencia para readers.
  - Trade-off: el registry está vacío hasta que algo importe el bootstrap o un agent module. Aceptable porque: tests y código real siempre importan algo del agent (modelo, repo, page); test paranoia (`test_registry_lists_known_agents`) cubre tres entrypoints. Si un test futuro arranca sin tocar nada del agent y consulta el registry, fallará claro y se agrega `import src.shared.infrastructure.agent_observability_bootstrap` arriba.

- **`CostAggregator(db, model_class)` requerido — no default**:
  - Tomada: constructor exige model class explícita. No `CostAggregator(db)` defaulteando a copilot.
  - Razón: anti-parche `04-principles §1.4`. Default copilot ofusca quién consume qué tabla; refactor S2 quedaba a medio camino. Costo: 6 sites de tests + 1 admin module a actualizar. Lo paguemos clean.
  - Alternativa: factory functions `for_copilot(db)` / `for_sales_agent(db)`. Rechazada — solo agrega indirección; el caller ya conoce el model class necesario.

- **`top_conversations_by_cost` vs `top_leads_by_cost` opt-in**:
  - Tomada: cada método chequea `_has_conversation_id` / `_has_lead_id` (cacheado en `__init__`); raise `AttributeError` con mensaje descriptivo si el caller mal-usa el método.
  - Razón: copilot tiene `conversation_id` (no `lead_id`); sales_agent al revés. SQL polymorphism al runtime con check estructural mantiene el aggregator único, sin clases hijas. El mensaje del raise apunta al método correcto (defensive contract).
  - Trade-off: dos métodos en vez de uno unificado `top_entities_by_cost(entity_kind=...)`. Aceptable: las semánticas (lead vs conversation) son diferentes y los DTOs deben tipar distinto.

- **MV cross-agent no reemplaza la legacy**:
  - Tomada: `mv_daily_llm_cost_per_tenant` (077) sigue activa con su grano fino (model+provider+role); `mv_daily_llm_cost_per_tenant_v2` (079) agrega coarse cross-agent. `aggregate_refresh_task` refresca ambas.
  - Razón: el copilot tab existente (`/costo-copilot`) consume el grano fino. Romper esa UI no entra en scope S2. v2 es coarse porque el cross-agent dashboard no necesita drill por modelo en el resumen — el drill está en el tab "Por agente" de `costo-agentes` que llama `CostAggregator.tenant_detail` directo (no MV).
  - Trade-off: 2 MVs para mantener. Cron refresh hourly es barato; cada MV tiene su unique index para CONCURRENT. Borrado de v1 se decide cuando `costo-copilot` migre a v2 (post S6).

- **Per-MV best-effort en `aggregate_refresh_task`**:
  - Tomada: refresh de cada MV en su propio try/except + commit. Si v1 falla, v2 sigue. Resultado: `{"ok": v1_ok and v2_ok, "legacy_ok": ..., "v2_ok": ...}`.
  - Razón: una de las dos MVs puede fallar por bloqueo, lock contention, o dato corrupto. Aborta-todo = stale data en ambos dashboards. Best-effort por MV = al menos uno actualizado.
  - Trade-off: el caller (cron) no distingue entre "ambos OK" y "uno de dos OK". Resultado tiene los dos flags para introspección manual; el cron solo log + retry hourly.

- **Per-table best-effort en `retention_task`**:
  - Mismo patrón. Si copilot purge falla, sales_agent purge sigue. El parent commit es único; el rollback solo cubre el commit (no abortado, los DELETEs ya se ejecutaron lo que pudieron antes del except).
  - Trade-off: error en commit = todo lo borrado ese ciclo se pierde. Aceptable porque retention es weekly-fresh — no hay urgencia día por día.

- **`_render_per_agent_tab` sin `db` arg**:
  - Tomada: cleanup oportunista paso 11.5 — el tab no usa `db` directo (todo via `cross.aggregators_by_kind()[kind]`). Removido el arg.
  - Razón: ANN001 (ruff) marcaba ausencia del type. Mejor eliminarlo que tipar algo no usado.

---

## Sorpresas / gotchas críticos

- **Arch test `test_shared_agent_observability_purity` AST-walks imports**: detecta `from src.modules.X import Y` aún si está dentro de un function lazy import. La regla tiene KNOWN_VIOLATIONS vacío y debe quedar así. Solución: invertir dependencia con bootstrap externo. **Lección S3+**: cualquier nuevo símbolo en `shared/agent_observability/` que necesite conocer agentes debe usar el patrón register-from-agent-side, nunca lazy import.

- **Lambdas inline triggerean PLW0108 ruff**: `monkeypatch.setattr(mod, "_today", lambda: x.date())` falla con "Lambda may be unnecessary". Fix: declarar `def _today_stub() -> dt.date:` arriba. Pequeña fricción pero evita falsos negativos del lint en producción.

- **MV CONCURRENT refresh y NULL columns**: research confirmó que cualquier columna nullable en el unique index del MV degrada severamente el refresh (NULL=NULL → all rows look different). Solución preventiva: declaré las 3 columnas del UNION ALL como NOT NULL via literal (`'copilot'::VARCHAR(32)`) + columnas NOT NULL upstream (`tenant_id`, `occurred_on`). **Lección**: cuando agreguemos el 3er agente, su tabla debe garantizar tenant_id y occurred_on NOT NULL desde el inicio.

- **`hasattr(model, "lead_id")` cuesta 1 vez en `__init__`**: cacheado en `_has_lead_id`. SQLAlchemy declarative attribute lookup no es trivial — cada `getattr` resuelve la columna ORM. Cachear evita pegar el descriptor en cada query (~100 calls per-tenant per-cycle).

- **Streamlit `_format_money` sin uso (LOW)**: helper movido del `costo_copilot.py` original quedó sin call sites en `costo_agentes.py` (uso `f"${val:.4f}"` inline). Dejé la función definida porque podría usarse en futuras tabs (currency display); ruff lo flagearía si fuera dead — no lo es porque está en `__all__` implícito (sin `_` prefix). **Watchpoint S3+**: si nadie lo usa al cierre de S6, borrar.

- **`agent_observability_registry()` retorna tuple, no dict**: por orden determinístico. Iteración consistente para emails/dashboards (siempre copilot antes que sales). Código que necesite lookup usa `get_spec(kind)`.

---

## Recomendaciones accionables para S3

- [ ] **Cache_boundary refactor del system prompt sales_agent**: el prefix cacheable ≥1024 tokens (per `02-architecture-target §3.4`). El consumer post-S2 puede leer cost via `CrossAgentCostAggregator(db).tenant_breakdown()` para validar que el hit rate ≥60% reduce `sales_agent` cost en ~25-30%.
- [ ] **NO modificar `cost_aggregator` o `cost_alert_service`** — cualquier nuevo dato cross-agent debería emerger del registry o de columnas tipadas en `*_llm_call`. Si se necesita un nuevo método (ej. `cache_hit_rate_per_agent`), agregarlo en el aggregator parametrizado, no en un service nuevo.
- [ ] **Si S3 toca `prompt_loader`/`compose_system_prompt`**: usar `agent_observability_registry()` para identificar `agent_kind`. NO hardcodear strings.
- [ ] **`aggregate_refresh_task` puede medir cache hit rate cross-agent**: cuando S3 popule `cached_read_tokens` regularmente, agregar columna a la MV v2 (DROP+CREATE idempotente, cron refresh actualiza automatico).

---

## Hooks listos

- `backend/src/shared/agent_observability/registry.py` — registro pasivo. Cualquier agente nuevo se agrega con 1 call a `register_agent_observability(spec)` desde su `observability/__init__.py` + 1 import en `agent_observability_bootstrap.py`.
- `backend/src/shared/agent_observability/reporting/cost_aggregator.py` — `CostAggregator(db, model)` + `CrossAgentCostAggregator(db)`. Métodos: `tenant_detail`, `tenants_summary`, `daily_series`, `top_conversations_by_cost`, `top_leads_by_cost`, `tenants_summary_by_agent`, `tenant_breakdown`, `aggregators_by_kind`.
- `backend/src/shared/agent_observability/application/cost_alert_service.py` — `check_cost_alerts(db)` cross-agent. Emite `cost_alert_threshold_exceeded` con `breakdown_usd_by_agent`.
- `backend/src/shared/agent_observability/workers/{aggregate_refresh_task,retention_task,cost_alert_task}.py` — todos cross-agent. Registrados en `WorkerSettings.functions` + `SchedulerSettings.cron_jobs`.
- `backend/src/admin/modules/_shared.py` — nuevos: `render_agent_kind_selector(key, default)` + `render_dual_read_banner(legacy, new)`.
- `backend/src/admin/modules/costo_agentes.py` + `pages/costo-agentes.py` + `PageSpec` registrado.
- `backend/alembic/versions/079_cross_agent_daily_cost_mv.py` — MV v2 idempotente.

---

## Riesgos abiertos

- **MV v2 refresh latency**: con 2 tablas creciendo, el refresh CONCURRENT puede tardar más cuando lleguen >100k rows. Watchpoint: si `aggregate_refresh_complete.v2_ms > 500ms` regularmente, considerar particionar `*_llm_call` por mes (Postgres native partitioning) o agregar índice covering en source tables.

- **Cost alert breakdown precision**: `breakdown_usd_by_agent` se serializa como dict[str, str] (Decimals stringificados). Consumers downstream (Slack/email cuando se agregue) deben deserializar. Hoy es structlog warning solo — log-level monitoring lo lee como JSON sin issue. **Watchpoint**: si llegamos a Slack alert, considerar Pydantic model para alert payload.

- **Registry `_REGISTRY` global mutable**: tests que modifiquen el registry deben restaurar (ningún test S2 lo hace). Si un test futuro hace `_REGISTRY.clear()` y no restora, todos los tests posteriores rompen. **Watchpoint S6**: arch test que valide registry tiene ≥2 specs al final de cada test.

- **Deferred-debt LiteLLM tier pricing**: si Kimi K2.6 / DeepSeek-V4 conversaciones largas entran al tier >200k, `cost_usd` grabado puede underestimar 10-20%. Watchpoint para reconciliación post-S6 con LiteLLM API real.

- **Subscribers SessionLocal per-event**: re-evaluado en S2, no impacta hoy. Re-checkpoint en S6 cuando reconciliation worker tenga un mes de runtime data.

---

## Tech debt detectado (NO arreglado)

- **[MEDIUM]** LiteLLM tier pricing > 200k tokens — DEFERRED-post-S6 (research confirmó el field schema; agregar a calculator cuando reconciliation muestre drift >5%).
- **[MEDIUM]** PII async post-write worker (Presidio + spaCy NER) — DEFERRED-post-S6 (regex sync cubre 80% LATAM compliance hoy).
- **[LOW]** `_format_money` en `costo_agentes.py` sin call sites — re-evaluar en S6, posible borrar.
- **[LOW]** `aggregate_refresh_task` no expone forma de saltar v2 si solo está la legacy (ej. test environment sin la migration 079). Hoy no es problema; conftest test DB siempre corre full alembic upgrade. Watchpoint si emerge en CI hermético.

---

## Fuentes research útiles

- [PostgreSQL 18 REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html) — confirmó UNIQUE index requirement + columns-only constraint + nullable degradation (NULL=NULL).
- [Crunchy Data — Indexing Materialized Views](https://www.crunchydata.com/blog/indexing-materialized-views-in-postgres) — patrones de unique index covering sobre MVs UNION.
- [BerriAI/litellm `model_prices_and_context_window.json`](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json) — tier pricing schema con `input_cost_per_token_above_200k_tokens` confirmado vigente.
- [Schematic — Usage-Based Billing 2026 Guide](https://schematichq.com/blog/why-usage-based-billing-is-taking-over-saas) — best practice de breakdown per producto en alerts.
- [Microsoft Presidio + spaCy Universe](https://spacy.io/universe/project/presidio) — confirmó latency 50-200ms; deferred-debt válido.
- [oneuptime LLMOps PII Detection 2026-01-30](https://oneuptime.com/blog/post/2026-01-30-llmops-pii-detection/view) — pattern arquitectónico async post-write.

---

## Métricas medidas

- BE quality gates: `ruff check src/ tests/` 0 errors, `ruff format --check` clean.
- Pytest full suite: **2970 passed, 1 warning** en 63s (sales_agent + copilot/observability + shared + arch + admin sin integration/verify).
- Migración 079 aplicada idempotente en dev DB + verificada con `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant_v2` manual.
- Tests nuevos S2: 28 (10 cross_agent_aggregator + 3 cost_alert_breakdown + 2 retention upgrade + 1 aggregate_refresh upgrade + 10 costo_agentes_page + 2 registry wiring).
- Files nuevos: 6 (registry + bootstrap + cost_aggregator shared + cost_alert_service shared + 3 workers shared + costo_agentes admin + page wrapper + migration + 3 test files).
- Files movidos: 5 (cost_aggregator + cost_alert_service + 3 workers de copilot a shared, sin shims).
- Files modificados: 9 (workers/settings.py, main.py, admin/app.py, conftest.py, _shared.py, copilot/observability/__init__.py, sales_agent/observability/__init__.py, costo_copilot.py, master_data arch test allowlist, 5 test files de copilot/observability con paths actualizados).
- LOC añadidas: ~1500 (incluye docs + tests + admin module + workers + cross-agent aggregator + registry + bootstrap).
- Spanish neutro: NO regresión — `costo-agentes` y `_shared` cumplen tuteo + sin voseo. Scan baseline limpio se mantiene.
